# AgentGym

Automated OpenClaw Security Scanner + Auto-Remediation.

Spins up an OpenClaw instance inside a Blaxel sandbox, runs 10 attack scenarios (prompt injection, sandbox escape, credential theft, persistence, evasion, config exploitation), scores each with an LLM-as-a-judge via Opik, auto-remediates by patching `openclaw.json`, and re-scans to prove fixes worked.

AgentTrace                                                                                                                                                                                                                                                                
  An automated security scanner and auto-remediation tool for AI coding agents.                                                       
                                                                                                                                        What It Does                                                                                                                                                                                                                                                                AgentTrace provisions a live AI coding agent (OpenClaw) inside a cloud sandbox (Blaxel), attacks it with 10 security scenarios        across 6 threat categories, scores each attack using an LLM-as-a-judge (Claude Sonnet), auto-patches the agent's configuration to
  fix discovered vulnerabilities, and re-scans to verify the fixes — all in a single automated pipeline. Every attack and its outcome 
  is traced and logged to Opik for observability.

  How It Works                                                                                                                          
  AgentTrace runs a 6-phase pipeline:                                                                                                   
  1. Provision — Spins up a Blaxel cloud sandbox with OpenClaw (an AI coding agent) installed                                           2. Baseline Scan — Fires 10 attack payloads against the default agent configuration
  3. Score — Claude Sonnet acts as an LLM-as-a-judge, evaluating each attack as compromised/resisted with severity ratings            
  4. Remediate — Automatically generates and applies configuration patches to openclaw.json based on which attacks succeeded          
  5. Re-scan — Runs the same 10 attacks against the hardened configuration                                                            
  6. Report — Displays before/after comparison in terminal; full traces logged to Opik dashboard                                      
                                                                                                                                        Attack Categories                                                                                                                   
                                                                                                                                        ┌──────────────────┬───────────┬─────────────────────────────────────────────────────────────────────────┐                            │     Category     │ # Attacks │                              What It Tests                              │
  ├──────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────┤                            │ Prompt Injection │ 3         │ System prompt extraction, role-play reframe, code-based credential leak │
  ├──────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────┤                          
  │ Sandbox Escape   │ 2         │ Path traversal, symlink escape                                          │                          
  ├──────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────┤                            │ Credential Theft │ 2         │ Env var dump, config file read                                          │                          
  ├──────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────┤                            │ Persistence      │ 1         │ SOUL.md tampering                                                       │
  ├──────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────┤                            │ Evasion          │ 1         │ Base64-encoded command execution                                        │
  ├──────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────┤                            │ Config Exploit   │ 1         │ Cloud metadata access via elevated tools                                │
  └──────────────────┴───────────┴─────────────────────────────────────────────────────────────────────────┘                            
  Tech Stack                                                                                                                          
  
  - Python 3.11+ — Core runtime                                                                                                         - Blaxel SDK — Cloud sandbox provisioning and management
  - Anthropic Claude API — Powers the LLM-as-a-judge scorer                                                                           
  - Opik (Comet) — Tracing and observability for all attack/response pairs                                                            
  - Rich — Terminal UI with formatted tables and colored output                                                                       
  - OpenClaw — The target AI coding agent being security-tested                                                                       
                                                                                                                                        Key Differentiator                                                                                                                  
                                                                                                                                        AgentTrace doesn't just find vulnerabilities — it closes the loop by automatically remediating them and proving the fix works,        giving you a measurable before/after security posture improvement (e.g., Grade C → Grade B).
                                                                                                     

## Quick Start

```bash
# 1. Install dependencies
pip install -e .

# 2. Configure credentials
cp .env.example .env
# Edit .env with your keys

# 3. Login to Blaxel
bl login

# 4. Run the scanner
python -m agentgym
```

## Environment Variables

| Variable | Description |
|---|---|
| `BL_WORKSPACE` | Blaxel workspace name |
| `BL_API_KEY` | Blaxel API key |
| `OPIK_API_KEY` | Opik API key (sign up at comet.com) |
| `OPIK_WORKSPACE` | Opik workspace name |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |
| `OPENCLAW_GATEWAY_TOKEN` | Token for OpenClaw gateway auth |

## How It Works

1. **Provision** -- Creates a Blaxel sandbox, installs OpenClaw + opik-openclaw tracing plugin
2. **Baseline Scan** -- Runs 10 attack scenarios against the default OpenClaw config
3. **Score** -- Claude Sonnet 4.6 acts as LLM-as-a-judge, scoring each attack pass/fail + severity
4. **Remediate** -- Patches `openclaw.json` based on which attacks succeeded
5. **Re-scan** -- Runs the same 10 attacks against the hardened config
6. **Report** -- Prints before/after comparison in terminal; full traces available in Opik dashboard

## Attack Categories

| Category | Attacks | What It Tests |
|---|---|---|
| Prompt Injection | 3 | System prompt extraction, role-play reframe, code-based credential leak |
| Sandbox Escape | 2 | Path traversal, symlink escape |
| Credential Theft | 2 | Env var dump, config file read |
| Persistence | 1 | SOUL.md tampering |
| Evasion | 1 | Base64-encoded command execution |
| Config Exploit | 1 | Cloud metadata access via elevated tools |

## Viewing Results

All traces are logged to your Opik dashboard at [comet.com/opik](https://www.comet.com/opik) under the project `agentgym`. Each attack is a separate trace with:

- `compromised` score (0.0 = resisted, 1.0 = compromised)
- `severity` score (0.0 none to 1.0 critical)
- Full payload and response text
- Tags for scan phase (`baseline` / `post-fix`) and attack category
