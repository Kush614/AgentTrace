# policy-gate

Production Go sidecar for **deterministic agent tool-call policy enforcement**. Sits in front of agent runtimes (OpenClaw / Mission Control / AgentTrace) and returns fast `ALLOW`, `DENY`, or `REQUIRE_APPROVAL` decisions with audit-friendly rule IDs.

Built as the enforcement layer for [AgentTrace](https://github.com/Kush614/AgentTrace) — the scanner finds vulnerabilities; policy-gate blocks them at ingress.

## Why AgentTrace (not Mission Control)

| Project | Role | Why not lead with it |
|---------|------|----------------------|
| **AgentTrace** | Red-team scanner + auto-remediation | ✅ Best fit — completes scan → enforce loop; rules mirror remediation playbook |
| Mission Control | TS approval UI | Already has approval queue; Go sidecar would duplicate UI logic |
| Carapace | Python action-layer policy | Different stack; K8s-focused |

Mission Control can call the same `/v1/evaluate` webhook later — one sidecar, two consumers.

## Architecture

```
Agent tool call / user message
        │
        ▼
  policy-gate (Go)  ──► ALLOW / DENY / REQUIRE_APPROVAL
        │                    │
        │                    └── rule_id + reason (audit)
        ▼
  Agent runtime (OpenClaw)
```

AgentTrace pipeline with sidecar:

```
Provision → Policy Preflight (Go) → Baseline Scan → Score → Remediate → Re-scan
```

## API

### `POST /v1/evaluate`

```json
{
  "agent_id": "openclaw-default",
  "session_id": "agentgym",
  "tool": "exec",
  "arguments": {"command": "printenv ANTHROPIC_API_KEY"},
  "content": "",
  "policy_profile": "hardened",
  "category_hint": "credential_theft"
}
```

Response:

```json
{
  "decision": "DENY",
  "rule_id": "R-CRED-01",
  "reason": "Environment or secret exfiltration command",
  "category": "credential_theft",
  "latency_ms": 0.08,
  "profile": "hardened"
}
```

### `GET /v1/metrics`

Returns request totals, decision breakdown, and latency percentiles (`p50`, `p95`, `p99`).

### `GET /health`

## Run locally

```bash
cd policy-gate
go run .
# listens on :8091
```

With AgentTrace:

```bash
# terminal 1
cd policy-gate && go run .

# terminal 2
cd .. && python -m agentgym
```

Set `POLICY_GATE_URL=http://127.0.0.1:8091` if not using default.

## Benchmark

```bash
cd policy-gate
chmod +x scripts/bench.sh
./scripts/bench.sh
```

Example output (Apple M-series, local):

```
completed=10000 elapsed=0.42s rps=23809 p50=0.06ms p99=0.31ms
```

## Rules (aligned with AgentTrace remediation)

| Rule | Category | Trigger |
|------|----------|---------|
| R-INJ-01..03 | prompt_injection | Injection patterns in content |
| R-SBX-01 | sandbox_escape | Path traversal, `/etc/passwd` |
| R-CRED-01..02 | credential_theft | `printenv`, `/etc/*`, `~/.openclaw/` |
| R-PERS-01 | persistence | `SOUL.md` / identity file writes |
| R-EVA-01 | evasion | Base64 decode execution |
| R-CFG-01 | config_exploit | Cloud metadata, elevated tools |
| R-APP-01 | approval_rail | Risky tools (`exec`, `write_file`, `send_email`, …) |

## Tests

```bash
cd policy-gate
go test ./...
```

## Docker

```bash
docker build -t policy-gate .
docker run -p 8091:8091 policy-gate
```
