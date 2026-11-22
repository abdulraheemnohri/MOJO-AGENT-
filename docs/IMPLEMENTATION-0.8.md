# Implementation update — 0.8

## Workflow scheduler
- Persistent SQLite schedules linked to existing validated workflows.
- Intervals are bounded from 60 seconds to 30 days; at most 100 schedules.
- A scheduler tick claims due items transactionally and runs at most 10 workflows per request.
- Schedules can be paused, resumed and deleted. Last run status and next run time persist.
- The scheduler is intentionally pull-driven: call POST /api/v1/scheduler/tick from an OS scheduler or manually. The API does not create hidden daemon threads or execute workflows in the background by default.

## Interfaces
- Dashboard: create a schedule from each workflow, view next run and last status, pause/resume/remove, trigger due work.
- Android: create schedule by workflow ID, list schedules, tick due work, pause/resume/remove through API controls.

## Safety
- Only the existing allowlisted workflow step types can execute.
- Each tick runs at most 10 schedules; schedule count and intervals are capped.
- No shell, arbitrary code execution, remote worker or unbounded background process was added.
