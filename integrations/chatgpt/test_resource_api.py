import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("resource_api", Path(__file__).with_name("resource_api.py"))
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class ResourceApiTests(unittest.TestCase):
    def setUp(self):
        self.resources = {"resources": [
            {"id": "one", "name": "Sample Site", "url": "https://example.org",
             "category": "cloud_search", "tags": ["subtitle"], "summary": "Sample resource",
             "risks": {"copyright": "low"}, "verification": {"status": "verified"}},
            {"id": "two", "name": "Other Site", "category": "magnet_search",
             "tags": [], "summary": "Another", "risks": {"copyright": "high"}}
        ]}
        self.report = {"generated_at": "2026-11-12", "results": [
            {"resource_id": "one", "status": "reachable", "http_status": 200},
            {"resource_id": "two", "status": "restricted", "http_status": 403}
        ]}

    def test_filters_and_status(self):
        with patch.object(api, "source_json", side_effect=[self.resources, self.report]):
            result = api.search(q="sample", category="cloud_search", status="reachable")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["name"], "Sample Site")
        self.assertEqual(result["results"][0]["copyright_risk"], "low")

    def test_limit(self):
        with patch.object(api, "source_json", side_effect=[self.resources, self.report]):
            result = api.search(limit=1)
        self.assertEqual(result["count"], 1)

    def test_openapi(self):
        schema = api.openapi()
        self.assertIn("/resources", schema["paths"])
        self.assertEqual(schema["paths"]["/resources"]["get"]["operationId"], "searchResources")

if __name__ == "__main__":
    unittest.main()
