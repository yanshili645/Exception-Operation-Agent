import json
import unittest
from datetime import date
from pathlib import Path

from powerwash_report.connectors import DeputyClient, load_file_bundle
from powerwash_report.engine import evaluate, load_staff_mapping, summarize


ROOT = Path(__file__).resolve().parents[1]


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.rules = json.loads((ROOT / "config/rules.json").read_text())
        self.bundle = load_file_bundle(ROOT / "data/demo")
        self.mapping = load_staff_mapping(ROOT / "config/staff_mapping.csv")
        self.rows = evaluate(self.bundle, date(2026, 9, 13), self.rules, self.mapping)

    def test_critical_incomplete_job_is_detected(self):
        self.assertTrue(any(x["code"] == "JOB-01" and x["job_number"] == "31413" for x in self.rows))

    def test_priority_lateness_is_high(self):
        matches = [x for x in self.rows if x["code"] == "JOB-03" and x["job_number"] == "31411"]
        self.assertEqual(matches[0]["severity"], "High")

    def test_no_show_is_critical(self):
        self.assertTrue(any(x["code"] == "DEP-01" and "Bob" in x["employee"] for x in self.rows))

    def test_same_site_split(self):
        self.assertEqual(sum(1 for x in self.rows if x["code"] == "JOB-07"), 2)

    def test_summary_reconciles(self):
        summary = summarize(self.rows, self.bundle, date(2026, 9, 13))
        self.assertEqual(summary["total_exceptions"], len(self.rows))
        self.assertEqual(sum(summary["exception_counts"].values()), len(self.rows))


class ConnectorTest(unittest.TestCase):
    def test_deputy_employee_info_list_is_supported(self):
        client = DeputyClient(
            "https://example.au.deputy.com", "token", "Pacific/Auckland"
        )
        roster = client._normalize_roster({
            "Id": 10,
            "Employee": 101,
            "_DPMetaData": {
                "EmployeeInfo": [{"DisplayName": "Alice Example"}]
            },
        })
        self.assertEqual(roster["employee_name"], "Alice Example")


if __name__ == "__main__":
    unittest.main()

