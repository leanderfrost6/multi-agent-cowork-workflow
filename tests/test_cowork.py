import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
from cowork.run import approve, plan_cost, plan_digest, record_handoff, run


class CoworkTests(unittest.TestCase):
    def setUp(self):
        self.document = run("update the parser", ["src/parser.py"], ["python -m unittest"])

    def test_roles_and_cost_are_explicit(self):
        self.assertEqual([self.document["roles"][name]["model"] for name in ("planner", "worker", "reviewer")], ["gpt-6-sol", "gpt-5.4-mini", "gpt-6-sol"])
        self.assertGreater(plan_cost(), 0)
        self.assertEqual(len(self.document["plan_digest"]), 64)

    def test_digest_is_stable(self):
        self.assertEqual(plan_digest(self.document["plan"]), self.document["plan_digest"])

    def test_worker_scope_and_review_gate(self):
        with self.assertRaises(ValueError):
            record_handoff(self.document, ["README.md"], "python -m unittest", "pending")
        updated = record_handoff(self.document, ["src/parser.py"], "python -m unittest", "approved", ["resp-plan", "resp-review"])
        approve(updated)
        self.assertEqual(updated["handoff"]["worker_patch"], ["src/parser.py"])

    def test_rejected_review_cannot_approve(self):
        updated = record_handoff(self.document, ["src/parser.py"], "python -m unittest", "changes_requested")
        with self.assertRaises(ValueError):
            approve(updated)

    def test_budget_gate(self):
        with self.assertRaises(ValueError):
            run("update the parser", ["src/parser.py"], ["python -m unittest"], budget_usd=0.001)


if __name__ == "__main__":
    unittest.main()
