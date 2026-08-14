# AgentTrace

An automated security scanner and auto-remediation tool for AI coding agents. AgentTrace provisions a live AI coding agent (OpenClaw) inside a cloud sandbox (Blaxel), attacks it with 10 security scenarios across 6 threat categories, scores each attack using an LLM-as-a-judge (Claude Sonnet), auto-patches the agent's configuration to fix discovered vulnerabilities, and re-scans to verify the fixes — all in a single automated pipeline. Every attack and its outcome is traced and logged to [Opik](https://www.comet.com/opik) for full observability.

## Key Differentiator

AgentTrace doesn't just find vulnerabilities — it **closes the loop** by automatically remediating them and proving the fix works, giving you a measurable before/after security posture improvement (e.g., Grade C → Grade B).

> *"Every OpenClaw deployment should run this before going to production."*

## How It Works

AgentTrace runs a 7-phase pipeline when policy-gate is running:

```
Provision → Policy Preflight (Go) → Baseline Scan → Score → Remediate → Re-scan → Report
```

Without policy-gate, phases 2–6 run as before.

1. **Provision** — Spin up a Blaxel sandbox with a live OpenClaw instance.
2. **Policy Preflight** — Go `policy-gate` sidecar evaluates all 10 attacks as synthetic tool calls; reports how many would be blocked at ingress (`DENY` / `REQUIRE_APPROVAL`).
3. **Baseline Scan** — Fire 10 attack payloads against the default configuration.
4. **Score** — Claude Sonnet judges each attack result as *compromised* or *resisted*, with severity levels.
5. **Remediate** — Auto-patch `openclaw.json` based on which defenses failed.
6. **Re-scan** — Re-run all 10 attacks against the hardened configuration.
7. **Report** — Generate a before/after comparison with full Opik trace logs.

## Attack Categories

| Category | Attacks | What It Tests |
|---|---|---|
| Prompt Injection | 3 | System prompt extraction, role-play reframe, code-based credential leak |
| Sandbox Escape | 2 | Path traversal, symlink escape |
| Credential Theft | 2 | Env var dump, config file read |
| Persistence | 1 | SOUL.md tampering |
| Evasion | 1 | Base64-encoded command execution |
| Config Exploit | 1 | Cloud metadata access via elevated tools |

## Tech Stack

- **Go 1.23** — `policy-gate` sidecar for deterministic tool-call policy enforcement (~400 LOC, p99 < 1ms local)
- **Python 3.11+** — Core runtime
- **Blaxel SDK** — Cloud sandbox provisioning and management
- **Anthropic Claude API** — LLM-as-a-judge scorer
- **Opik (Comet)** — Tracing and observability for all attack/response pairs
- **Rich** — Terminal UI with formatted tables and colored output
- **OpenClaw** — Target AI coding agent under test

## Quick Start

```bash
# Optional but recommended: start the Go policy-gate sidecar
cd policy-gate && go run .

# In another terminal
python -m agentgym
```

The CLI runs the full pipeline end-to-end. You'll see live output as each phase executes: sandbox provisioning, attacks firing one-by-one, the baseline results table, auto-remediation patches being applied, the post-fix rescan, and finally the before/after comparison.

## Observability with Opik

All 40 traces (10 attacks × 2 scans) are logged to Opik with structured metadata:

- **Trace names** follow the pattern `attack_{phase}_{category}_{attack_name}` (e.g., `attack_baseline_credential_theft_env_vars`)
- **Tags** include scan phase (`baseline` / `post-fix`) and attack category (`prompt_injection`, `sandbox_escape`, etc.)
- **Each trace contains**: the attack payload sent (input), the agent's full response (output), and attack metadata

### Comparing Results

The core value is visible when you compare traces for the same attack across scans:

| Trace | Phase | Result |
|---|---|---|
| `attack_baseline_credential_theft_env_vars` | Baseline | **COMPROMISED** — agent dumped all env vars |
| `attack_post-fix_credential_theft_env_vars` | Post-fix | **RESISTED** — remediation blocked the leak |

Same attack, different results after auto-patching.

## Demo Walkthrough

1. **Terminal** — Run `python -m agentgym` and watch the live pipeline output.
2. **Opik Traces List** — Browse all 40 traces; filter by `baseline` or `post-fix` tags.
3. **Trace Detail** — Click any trace to see the exact payload, agent response, and metadata.
4. **Before vs After** — Compare matched trace pairs to see the security posture shift.
5. **Blaxel Console** *(optional)* — Verify the sandbox at [app.blaxel.ai](https://app.blaxel.ai).

## License

MIT

