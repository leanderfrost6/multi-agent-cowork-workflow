"""Offline planner/worker/reviewer handoff coordinator."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import PurePosixPath
from typing import Any

MODELS = {
    "gpt-6-sol": {"input": 0.6, "output": 3.0, "efforts": ["low", "medium", "high", "xhigh", "max"]},
    "gpt-5.4-mini": {"input": 0.225, "output": 1.35, "efforts": ["low", "medium", "high", "xhigh"]},
}
ROLE_POLICY = {
    "planner": {"model": "gpt-6-sol", "effort": "high", "input_tokens": 12000, "output_tokens": 4000, "instruction": "decompose the task, name files and invariants, and state acceptance tests"},
    "worker": {"model": "gpt-5.4-mini", "effort": "medium", "input_tokens": 30000, "output_tokens": 12000, "instruction": "implement only approved changes and report the patch and checks"},
    "reviewer": {"model": "gpt-6-sol", "effort": "high", "input_tokens": 30000, "output_tokens": 6000, "instruction": "inspect the actual diff and tests; approve or request one specific correction"},
}
REVIEW_STATUSES = {"pending", "approved", "changes_requested", "rejected"}


def _path(value: str) -> str:
    parsed = PurePosixPath(value)
    if not value or parsed.is_absolute() or ".." in parsed.parts:
        raise ValueError(f"path must be relative and stay in the workspace: {value}")
    return str(parsed)


def _cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    model = MODELS[model_id]
    return input_tokens / 1_000_000 * model["input"] + output_tokens / 1_000_000 * model["output"]


def plan_cost() -> float:
    return sum(_cost(row["model"], row["input_tokens"], row["output_tokens"]) for row in ROLE_POLICY.values())


def plan_digest(plan: dict[str, Any]) -> str:
    canonical = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run(task: str, allowed_paths: list[str] | None = None, acceptance_tests: list[str] | None = None, budget_usd: float | None = None) -> dict[str, Any]:
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task must be non-empty")
    paths = [_path(value) for value in (allowed_paths or [])]
    tests = [value.strip() for value in (acceptance_tests or []) if value.strip()]
    if not tests:
        raise ValueError("at least one acceptance test is required")
    estimate = plan_cost()
    if budget_usd is not None and (not isinstance(budget_usd, (int, float)) or not math.isfinite(float(budget_usd)) or budget_usd < estimate):
        raise ValueError(f"three-role estimate ${estimate:.4f} exceeds the budget")
    plan = {"task": task, "allowed_paths": paths, "acceptance_tests": tests}
    return {
        "plan": plan,
        "plan_digest": plan_digest(plan),
        "roles": {
            role: {key: value for key, value in policy.items() if key not in {"input_tokens", "output_tokens"}}
            for role, policy in ROLE_POLICY.items()
        },
        "estimated_usd": round(estimate, 8),
        "budget_usd": budget_usd,
        "handoff": {"worker_patch": None, "test_command": None, "reviewer_status": "pending", "response_ids": []},
    }


def record_handoff(document: dict[str, Any], worker_files: list[str], test_command: str, reviewer_status: str, response_ids: list[str] | None = None) -> dict[str, Any]:
    if reviewer_status not in REVIEW_STATUSES:
        raise ValueError("invalid reviewer status")
    allowed = set(document["plan"]["allowed_paths"])
    files = [_path(value) for value in worker_files]
    outside = sorted(set(files) - allowed)
    if outside:
        raise ValueError(f"worker patch leaves approved scope: {', '.join(outside)}")
    if not test_command.strip():
        raise ValueError("test_command is required")
    updated = dict(document)
    updated["handoff"] = {"worker_patch": files, "test_command": test_command, "reviewer_status": reviewer_status, "response_ids": response_ids or []}
    return updated


def approve(document: dict[str, Any]) -> None:
    handoff = document.get("handoff", {})
    if handoff.get("reviewer_status") != "approved":
        raise ValueError("reviewer approval is required before applying a patch")
    if not handoff.get("worker_patch") or not handoff.get("test_command"):
        raise ValueError("worker patch and test command must be recorded")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an offline planner/worker/reviewer handoff")
    parser.add_argument("task")
    parser.add_argument("--allowed-path", action="append", default=[])
    parser.add_argument("--acceptance-test", action="append", required=True)
    parser.add_argument("--budget", type=float)
    args = parser.parse_args()
    print(json.dumps(run(args.task, args.allowed_path, args.acceptance_test, args.budget), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
