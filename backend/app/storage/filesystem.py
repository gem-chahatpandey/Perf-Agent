import json
import aiofiles
import aiofiles.os
from pathlib import Path
from app.storage.interface import Storage
from app.core.config import settings


class FilesystemStorage(Storage):
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or settings.data_dir

    def _resolve(self, key: str) -> Path:
        resolved = (self.base_dir / key).resolve()
        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise ValueError("Path traversal detected")
        return resolved

    async def save(self, key: str, data: dict) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2, default=str))

    async def load(self, key: str) -> dict:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"Key not found: {key}")
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
        return json.loads(content)

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    async def list(self, prefix: str) -> list[str]:
        base = self._resolve(prefix)
        if not base.exists():
            return []
        results = []
        resolved_base = self.base_dir.resolve()
        for item in base.iterdir():
            rel = item.relative_to(resolved_base)
            results.append(str(rel).replace("\\", "/"))
        return sorted(results)

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            import shutil
            shutil.rmtree(path)

    async def save_file(self, key: str, content: bytes) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)

    async def load_file(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        async with aiofiles.open(path, "rb") as f:
            return await f.read()


storage = FilesystemStorage()
