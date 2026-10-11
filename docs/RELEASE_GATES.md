# Research and deployment gates

**This repository begins at DEMONSTRATION_ONLY.** Passing CI checks code and synthetic outputs, not authorization to make scientific claims or deploy an app.

| Gate | Required evidence | Default | Block response |
| --- | --- | --- | --- |
| G0 scaffold | Protocol, source register, data dictionary, environment, question | PASS as examples; study-specific completion PENDING | Complete study intake |
| G1 code | Unit/integration/negative tests, lint, isolated environment | Testable in CI | Fix errors and rerun |
| G2 data | Valid sources/permissions, schema, units, joins and missingness | BLOCKED for real data | Quarantine input |
| G3 methods | Hypotheses/estimand or target, baselines, leakage isolation and review | BLOCKED for real claims | Return for methods review |
| G4 outputs | Figure interpretation, n, citations, uncertainty, artifact manifest, independent reviewer | BLOCKED | Withhold unsupported figures or claims |
| G5 deployment | Approved reviewed SHA, scoped credentials, smoke test, monitoring and rollback | BLOCKED | No external release |

For every gate, log disposition `PASS`, `BLOCKED` or `NOT_APPLICABLE`, evidence path, reviewer and date. `NOT_APPLICABLE` requires explanation. A passing `research-template audit` verifies the presence of scaffold files only. `--require-release` correctly exits nonzero for this starter. Publication readiness must be determined for an actual study and may require ethics/IRB, DUA, security, regulatory or journal approvals.

CI deliberately has **read-only permissions and no production deploy step**. Any release workflow should be separate, narrowly permissioned, reviewed, and pinned to an approved revision.
