"""Client + attack mapping for the Go policy-gate sidecar."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_GATE_URL = os.getenv("POLICY_GATE_URL", "http://127.0.0.1:8091")


def gate_available(base_url: str = DEFAULT_GATE_URL) -> bool:
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/health", timeout=1.0)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


def evaluate(
    *,
    tool: str,
    arguments: dict[str, str] | None = None,
    content: str = "",
    policy_profile: str = "default",
    category_hint: str = "",
    agent_id: str = "openclaw-default",
    session_id: str = "agentgym",
    base_url: str = DEFAULT_GATE_URL,
) -> dict[str, Any]:
    payload = {
        "agent_id": agent_id,
        "session_id": session_id,
        "tool": tool,
        "arguments": arguments or {},
        "content": content,
        "policy_profile": policy_profile,
        "category_hint": category_hint,
    }
    resp = httpx.post(
        f"{base_url.rstrip('/')}/v1/evaluate",
        json=payload,
        timeout=5.0,
    )
    resp.raise_for_status()
    return resp.json()


def attack_to_tool_call(attack: dict) -> dict[str, Any]:
    """Map an AgentTrace attack scenario to a synthetic tool invocation."""
    category = attack.get("category", "")
    payload = attack.get("payload", "")
    name = attack.get("name", "")

    if category == "prompt_injection":
        return {
            "tool": "agent_message",
            "content": payload,
            "category_hint": category,
        }

    if category == "sandbox_escape":
        if "symlink" in name:
            return {
                "tool": "exec",
                "arguments": {"command": payload[:500]},
                "category_hint": category,
            }
        return {
            "tool": "read_file",
            "arguments": {"path": payload[:500]},
            "category_hint": category,
        }

    if category == "credential_theft":
        return {
            "tool": "exec",
            "arguments": {"command": payload[:500]},
            "category_hint": category,
        }

    if category == "persistence":
        return {
            "tool": "write_file",
            "arguments": {"path": "SOUL.md", "body": payload[:500]},
            "category_hint": category,
        }

    if category == "evasion":
        return {
            "tool": "exec",
            "arguments": {"command": payload[:500]},
            "category_hint": category,
        }

    if category == "config_exploit":
        return {
            "tool": "http_request",
            "arguments": {"url": payload[:500]},
            "category_hint": category,
        }

    return {
        "tool": "agent_message",
        "content": payload,
        "category_hint": category,
    }


def preflight_attacks(
    attacks: list[dict],
    *,
    policy_profile: str = "default",
    base_url: str = DEFAULT_GATE_URL,
) -> list[dict]:
    """Evaluate each attack against policy-gate before the live agent scan."""
    results: list[dict] = []
    for attack in attacks:
        call = attack_to_tool_call(attack)
        decision = evaluate(
            tool=call["tool"],
            arguments=call.get("arguments"),
            content=call.get("content", ""),
            policy_profile=policy_profile,
            category_hint=call.get("category_hint", ""),
            base_url=base_url,
        )
        results.append(
            {
                "attack": attack["name"],
                "category": attack.get("category", ""),
                "decision": decision["decision"],
                "rule_id": decision.get("rule_id"),
                "reason": decision.get("reason"),
                "latency_ms": decision.get("latency_ms"),
            }
        )
    return results


def summarize_preflight(results: list[dict]) -> dict[str, int]:
    summary = {"DENY": 0, "REQUIRE_APPROVAL": 0, "ALLOW": 0}
    for row in results:
        summary[row["decision"]] = summary.get(row["decision"], 0) + 1
    return summary
