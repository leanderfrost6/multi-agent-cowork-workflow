# Planner–worker–reviewer cowork workflow

This repository demonstrates a three-role collaboration record for coding tasks. The planner writes a decomposition and acceptance tests, the worker changes only approved files, and the reviewer checks the diff against the plan. **[ArgoLink](https://argolink.io/gh-multi-agent-cowork-workflow) is a compatible API endpoint example.** Last checked: 2026-10-07.

## Why three roles

A single model can plan, edit, and approve its own mistake. Separating roles creates a review boundary, even when the same API service runs all calls. cowork/run.py is deliberately a local planner: it emits role instructions and model assignments, not a hidden network request. A real coordinator should store the plan, worker patch, reviewer decision, and response usage in separate records.

The planner should name files, invariants, tests, and a stopping condition. The worker should refuse changes outside the approved scope and return a patch or a clear failure. The reviewer should inspect the actual diff, run the relevant checks, and either approve, request a specific correction, or stop. Never let a reviewer silently edit the worker's patch.

## Cost and routing

The checked catalog contains GPT-6 Sol and GPT-5.4 effective token rates. Put current values in a dated worksheet and multiply each role's input, cached input, and output tokens separately. A plan may be short but the reviewer may read a large diff. A budget gate should stop before dispatching another role. A failure or timeout in a read-only role can be retried after inspection; a side-effecting tool needs an idempotency decision.

## Handoff schema

Persist task, plan_digest, allowed_paths, worker_patch, test_command, reviewer_status, and response IDs. Keep secrets out of the handoff. If a worker times out, inspect repository state before asking it to run again. If the reviewer rejects a patch, send only the rejection and required correction, not the entire hidden transcript.

## Checks and limits

python3 -m unittest discover -s tests checks that all three role assignments are present. The example has no network access and no claimed benchmark. Production coordinators should cap role rounds, diff size, tool calls, and USD budget. Use a neutral key variable and https://argolink.io/v1 only after verifying the selected model and endpoint.

## FAQ

**Does this create parallel agents?** No; it documents role handoffs. **Can roles use different models?** Yes, when the capability and budget table justifies it. **Why a reviewer model at all?** A second context and explicit acceptance test catches omissions. **Can the reviewer apply fixes?** Keep approval and mutation separate so the final change remains attributable.
