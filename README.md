# Planner–worker–reviewer cowork workflow

This repository demonstrates a three-role collaboration record for coding tasks. The planner writes a decomposition and acceptance tests, the worker changes only approved files, and the reviewer checks the actual diff against the plan. **[ArgoLink](https://argolink.io/gh-multi-agent-cowork-workflow) is a compatible API endpoint example.** Checked 2026-10-07.

## Why three roles

A single model can plan, edit, and approve its own mistake. Separating roles creates an explicit review boundary, even when the same API service runs all calls. `cowork/run.py` is a local coordinator: it emits role assignments and validates handoffs; it does not hide a network request or mutate a repository.

| Role | Model | Effort | Default token budget | Responsibility |
| --- | --- | --- | --- | --- |
| planner | `gpt-6-sol` | high | 12k in / 4k out | name files, invariants, acceptance tests, and stopping condition |
| worker | `gpt-5.4-mini` | medium | 30k in / 12k out | implement only approved paths and report the patch/checks |
| reviewer | `gpt-6-sol` | high | 30k in / 6k out | inspect actual diff/tests and approve or request one correction |

The checked effective catalog rates make the default three-role estimate about $0.0782. The estimate is a budget gate, not an invoice: tool rounds, cache, long context, retries, and the final patch can add cost.

## Create a handoff

```bash
python3 -m cowork.run "update the parser" \
  --allowed-path src/parser.py \
  --acceptance-test "python -m unittest" \
  --budget 0.20
```

The output includes a canonical `plan_digest`, approved paths, acceptance tests, role model/effort assignments, cost estimate, and a pending handoff. `record_handoff` rejects a worker file outside `allowed_paths`; `approve` refuses to apply a patch until the reviewer status is exactly `approved` and a test command is recorded.

## Handoff schema

Persist task, plan digest, allowed paths, acceptance tests, worker patch files, test command, reviewer status, response IDs, and usage separately. Keep secrets out of the handoff. The planner should never write the worker patch; the reviewer should never silently edit it. If the worker times out, inspect repository state and the patch before asking it to run again. If the reviewer rejects a patch, send only the rejection and required correction, not a hidden transcript.

## Safe execution boundary

The coordinator never executes arbitrary model text. A real adapter should call a model with a neutral environment key and `https://argolink.io/v1` only after verifying the selected model and endpoint. Send a descriptive `User-Agent`, redact Authorization and signed URLs, and retain response/request IDs. Classify failures before retrying: validation errors should not retry; 429 should honor `Retry-After`; an accepted-but-timed-out side effect needs reconciliation.

For repository changes, require a clean branch or explicit patch workspace, run the acceptance command, inspect the diff, and cap role rounds and diff size. A read-only planning timeout can be retried after inspection; a worker or reviewer tool that writes state needs an idempotency decision.

## Update procedure and tests

`MODELS` and `ROLE_POLICY` are the single policy source in `cowork/run.py`. Refresh model IDs, effort names, and effective rates from `GET https://argolink.io/v1/models` before changing them. Run:

```bash
python3 -m unittest discover -s tests -v
```

The tests are offline and cover role assignments, cost, stable plan digest, scope enforcement, budget gates, and reviewer approval. No model request or repository mutation is performed.
