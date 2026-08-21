from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
ROUTE_PATTERNS = (
    re.compile(r"@(?:Get|Post|Put|Patch|Delete|Request)Mapping\s*\(\s*[\\{\"]([^\"}]+)", re.I),
    re.compile(r"@(?:app|router)\.(?:get|post|put|patch|delete)\s*\(\s*[\"']([^\"']+)", re.I),
    re.compile(r"(?:router|app)\.(?:route)\s*\(\s*[\"']([^\"']+)", re.I),
)


@dataclass
class Endpoint:
    operation_id: str
    method: str
    path: str
    service: str = ""
    source_files: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    sla: dict[str, Any] = field(default_factory=dict)


@dataclass
class Impact:
    operation_id: str
    method: str
    path: str
    service: str
    impact: str
    confidence: float
    reason: str
    evidence: list[str] = field(default_factory=list)


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return result.stdout


def changed_files(base: str, head: str) -> list[dict[str, str]]:
    output = run_git("diff", "--name-status", base, head)
    files = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            files.append({"status": parts[0], "filename": parts[-1]})
    return files


def diff_text(base: str, head: str) -> str:
    return run_git("diff", "--unified=80", base, head)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_spec_data(path: Path) -> Any:
    if path.suffix == ".json":
        return load_json(path)
    if yaml is None:
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None


def load_specs(root: Path) -> list[Endpoint]:
    endpoints: list[Endpoint] = []
    candidates = [
        path for pattern in ("**/openapi*.json", "**/swagger*.json", "**/openapi*.yaml", "**/openapi*.yml")
        for path in root.glob(pattern)
        if ".git" not in path.parts and "node_modules" not in path.parts
    ]
    for path in candidates:
        data = load_spec_data(path)
        if not isinstance(data, dict):
            continue
        for route, methods in data.get("paths", {}).items():
            if not isinstance(methods, dict):
                continue
            for method, operation in methods.items():
                if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                    continue
                operation_id = operation.get("operationId") or f"{method.upper()}_{route}"
                extensions = operation.get("x-source-paths", [])
                source_files = [str(item) for item in extensions] if isinstance(extensions, list) else []
                tags = operation.get("tags", [])
                service = operation.get("x-service") or (tags[0] if tags else "")
                endpoints.append(Endpoint(
                    operation_id=operation_id,
                    method=method.upper(),
                    path=route,
                    service=service,
                    source_files=source_files,
                    dependencies=[str(item) for item in operation.get("x-dependencies", [])],
                    sla=operation.get("x-sla", {}) if isinstance(operation.get("x-sla", {}), dict) else {},
                ))
    return endpoints


def discover_routes(root: Path, files: list[dict[str, str]]) -> list[Endpoint]:
    endpoints: list[Endpoint] = []
    for item in files:
        path = root / item["filename"]
        if not path.is_file() or path.suffix.lower() not in {".py", ".java", ".kt", ".ts", ".tsx", ".js"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for index, line in enumerate(text.splitlines(), start=1):
            for pattern in ROUTE_PATTERNS:
                match = pattern.search(line)
                if match:
                    route = match.group(1)
                    method_match = re.search(r"\.(get|post|put|patch|delete)\s*\(", line, re.I)
                    method = method_match.group(1).upper() if method_match else "UNKNOWN"
                    operation_id = f"{method}_{route}".replace("/", "_").replace("{", "").replace("}", "")
                    endpoints.append(Endpoint(
                        operation_id=operation_id,
                        method=method,
                        path=route,
                        service=path.parts[0] if len(path.parts) > 1 else "",
                        source_files=[item["filename"]],
                    ))
                    break
    return endpoints


def load_dependency_graph(root: Path, explicit: str | None) -> tuple[dict[str, set[str]], list[str]]:
    path = Path(explicit) if explicit else root / "sample-data/architecture/dependency-graph.json"
    data = load_json(path) if path.is_file() else None
    graph: dict[str, set[str]] = {}
    warnings: list[str] = []
    if not isinstance(data, dict):
        warnings.append("Dependency graph unavailable; indirect impact is incomplete.")
        return graph, warnings
    for edge in data.get("edges", []):
        if isinstance(edge, dict) and edge.get("from") and edge.get("to"):
            graph.setdefault(str(edge["from"]), set()).add(str(edge["to"]))
    return graph, warnings


def changed_services(files: list[dict[str, str]], endpoints: list[Endpoint]) -> set[str]:
    services = set()
    for item in files:
        filename = item["filename"]
        for endpoint in endpoints:
            if any(source and (source in filename or filename in source) for source in endpoint.source_files):
                if endpoint.service:
                    services.add(endpoint.service)
        parts = Path(filename).parts
        if parts:
            services.add(parts[0])
    return services


def reverse_callers(graph: dict[str, set[str]], targets: set[str]) -> set[str]:
    callers = set()
    changed = True
    while changed:
        changed = False
        for caller, dependencies in graph.items():
            if caller not in callers and dependencies & (targets | callers):
                callers.add(caller)
                changed = True
    return callers


def route_impacts(diff: str, endpoints: list[Endpoint], files: list[dict[str, str]]) -> tuple[list[Impact], list[str]]:
    impacts: list[Impact] = []
    unresolved: list[str] = []
    changed_names = {item["filename"] for item in files}
    for endpoint in endpoints:
        matching_files = [source for source in endpoint.source_files if source in changed_names or source in diff]
        route_in_diff = endpoint.path in diff and endpoint.method in diff
        if matching_files or route_in_diff:
            reason = "Endpoint source or route declaration changed"
            evidence = matching_files or [f"{endpoint.method} {endpoint.path} appears in the PR diff"]
            impacts.append(Impact(endpoint.operation_id, endpoint.method, endpoint.path, endpoint.service, "direct", 0.98, reason, evidence))
    added_routes = re.findall(r"^\+.*(?:@(?:Get|Post|Put|Patch|Delete)Mapping|(?:router|app)\.(?:get|post|put|patch|delete))[^\n]*", diff, re.M | re.I)
    if added_routes and not any(item.impact == "direct" for item in impacts):
        for line in added_routes:
            unresolved.append(f"New route requires OpenAPI/source mapping: {line.strip()[:200]}")
    return impacts, unresolved


def removed_routes(diff: str) -> list[Impact]:
    impacts: list[Impact] = []
    for line in diff.splitlines():
        if not line.startswith("-") or line.startswith("---"):
            continue
        for pattern in ROUTE_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            route = match.group(1)
            method_match = re.search(r"\.(get|post|put|patch|delete)\s*\(", line, re.I)
            method = method_match.group(1).upper() if method_match else "UNKNOWN"
            operation_id = f"{method}_{route}".replace("/", "_").replace("{", "").replace("}", "")
            impacts.append(Impact(operation_id, method, route, "", "removed", 0.95, "Route declaration was removed in the PR", [line.strip()]))
            break
    return impacts


def markdown(report: dict[str, Any]) -> str:
    lines = [f"## Endpoint Impact Analysis ({report['status']})", ""]
    lines.append(f"**Changed files:** {len(report['changed_files'])}  **Full regression:** `{report['run_full_regression']}`")
    for title, key in (("New endpoints", "new_endpoints"), ("Removed endpoints", "removed_endpoints"), ("Directly affected", "directly_affected_endpoints"), ("Indirectly affected", "indirectly_affected_endpoints"), ("Potentially affected", "potentially_affected_endpoints")):
        lines.extend([f"### {title}", ""])
        items = report[key]
        if not items:
            lines.append("None detected.")
        for item in items:
            lines.append(f"- `{item['method']} {item['path']}` (`{item['operation_id']}`) - {item['reason']} (confidence {item['confidence']:.2f})")
        lines.append("")
    if report["unresolved_changes"]:
        lines.extend(["### Unresolved changes", "", *[f"- {item}" for item in report["unresolved_changes"]]])
    return "\n".join(lines)

def analyze(root: Path, base: str, head: str, dependency_path: str | None) -> dict[str, Any]:
    files = changed_files(base, head)
    diff = diff_text(base, head)
    specs = load_specs(root)
    discovered = discover_routes(root, files)
    endpoints = specs + discovered
    unique: dict[tuple[str, str, str], Endpoint] = {(e.operation_id, e.method, e.path): e for e in endpoints}
    endpoints = list(unique.values())
    graph, warnings = load_dependency_graph(root, dependency_path)
    direct, unresolved = route_impacts(diff, endpoints, files)
    removed = removed_routes(diff)
    direct_keys = {(item.operation_id, item.method, item.path) for item in direct}
    services = changed_services(files, endpoints)
    indirect_services = reverse_callers(graph, services)
    indirect: list[Impact] = []
    for endpoint in endpoints:
        key = (endpoint.operation_id, endpoint.method, endpoint.path)
        if key in direct_keys or not endpoint.service or endpoint.service not in indirect_services:
            continue
        indirect.append(Impact(endpoint.operation_id, endpoint.method, endpoint.path, endpoint.service, "indirect", 0.82, "Owning service depends on a changed service", [f"Changed services: {', '.join(sorted(services))}"]))
    changed_names = {item["filename"] for item in files}
    new_endpoints = [item for item in direct if any(item.path in line for line in diff.splitlines() if line.startswith("+"))]
    potential: list[Impact] = []
    if any(Path(name).name.lower() in {"dockerfile", "pyproject.toml", "package.json", "settings.py", "config.py"} or "migration" in name.lower() for name in changed_names):
        potential = [Impact(endpoint.operation_id, endpoint.method, endpoint.path, endpoint.service, "potential", 0.55, "Shared configuration, build, or database change may affect runtime behavior", []) for endpoint in endpoints if (endpoint.operation_id, endpoint.method, endpoint.path) not in direct_keys and endpoint not in indirect]
    unresolved.extend(warnings)
    full_regression = bool(unresolved) or any(item["filename"].lower().endswith((".lock", ".yaml", ".yml")) for item in files)
    report = {
        "status": "completed",
        "base": base,
        "head": head,
        "changed_files": files,
        "new_endpoints": [asdict(item) for item in new_endpoints],
        "removed_endpoints": [asdict(item) for item in removed],
        "directly_affected_endpoints": [asdict(item) for item in direct if item not in new_endpoints],
        "indirectly_affected_endpoints": [asdict(item) for item in indirect],
        "potentially_affected_endpoints": [asdict(item) for item in potential],
        "unresolved_changes": unresolved,
        "run_full_regression": full_regression,
    }
    report["markdown_summary"] = markdown(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve direct and indirect endpoint impact for a GitHub PR")
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--dependency-graph")
    parser.add_argument("--output", default="endpoint-impact.json")
    args = parser.parse_args()
    report = analyze(Path.cwd(), args.base, args.head, args.dependency_graph)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(report["markdown_summary"])


if __name__ == "__main__":
    main()