import unittest

from main import Endpoint, analyze, markdown, reverse_callers, route_impacts


class ImpactAgentTests(unittest.TestCase):
    def test_detects_direct_endpoint_change(self):
        endpoint = Endpoint(
            operation_id="createOrder",
            method="POST",
            path="/agent-test/orders",
            service="order-service",
            source_files=["backend/app/api/routes/agent_test.py"],
        )
        impacts, unresolved = route_impacts(
            '+@router.post("/agent-test/orders")',
            [endpoint],
            [{"status": "M", "filename": "backend/app/api/routes/agent_test.py"}],
        )
        self.assertEqual(unresolved, [])
        self.assertEqual(impacts[0].impact, "direct")
        self.assertEqual(impacts[0].operation_id, "createOrder")

    def test_detects_new_route_without_openapi_mapping_as_unresolved(self):
        impacts, unresolved = route_impacts(
            '+@router.get("/agent-test/new")',
            [],
            [{"status": "M", "filename": "backend/app/api/routes/agent_test.py"}],
        )
        self.assertEqual(impacts, [])
        self.assertEqual(len(unresolved), 1)

    def test_expands_indirect_callers(self):
        graph = {
            "order-service": {"payment-service"},
            "checkout-service": {"order-service"},
        }
        self.assertEqual(
            reverse_callers(graph, {"payment-service"}),
            {"order-service", "checkout-service"},
        )

    def test_markdown_contains_all_impact_sections(self):
        report = {
            "status": "completed",
            "changed_files": [],
            "run_full_regression": True,
            "new_endpoints": [],
            "removed_endpoints": [],
            "directly_affected_endpoints": [],
            "indirectly_affected_endpoints": [],
            "potentially_affected_endpoints": [],
            "unresolved_changes": ["Dependency graph unavailable"],
        }
        output = markdown(report)
        self.assertIn("New endpoints", output)
        self.assertIn("Removed endpoints", output)
        self.assertIn("Unresolved changes", output)


if __name__ == "__main__":
    unittest.main()