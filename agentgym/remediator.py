"""Auto-remediate OpenClaw vulnerabilities by patching openclaw.json."""

import copy
import json

REMEDIATION_PLAYBOOK: dict[str, dict] = {
    "prompt_injection": {
        "description": "Enable approval flow for tool calls + tighten exec security",
        "patches": [
            ("agents.defaults.tools.exec.ask", True),
            ("agents.defaults.tools.exec.security", "standard"),
        ],
    },
    "sandbox_escape": {
        "description": "Enable sandbox mode + restrict workspace boundary",
        "patches": [
            ("agents.defaults.sandbox.enabled", True),
            ("agents.defaults.sandbox.writePaths", ["/workspace"]),
            ("agents.defaults.sandbox.readPaths", ["/workspace", "/tmp"]),
        ],
    },
    "credential_theft": {
        "description": "Deny credential-reading tools + restrict env access",
        "patches": [
            (
                "agents.defaults.tools.deny",
                [
                    "read_file:/etc/*",
                    "read_file:~/.openclaw/*",
                    "exec:env",
                    "exec:printenv",
                    "exec:cat /etc/*",
                ],
            ),
        ],
    },
    "persistence": {
        "description": "Lock identity files from agent modification",
        "patches": [
            (
                "agents.defaults.tools.deny_write",
                ["SOUL.md", "IDENTITY.md", "USER.md"],
            ),
        ],
    },
    "evasion": {
        "description": "Add content filtering + disable base64 decode execution",
        "patches": [
            ("agents.defaults.tools.exec.security", "strict"),
        ],
    },
    "config_exploit": {
        "description": "Disable tools.elevated + restrict network access",
        "patches": [
            ("agents.defaults.tools.elevated.enabled", False),
            ("gateway.bind", "loopback"),
            ("gateway.auth.mode", "token"),
        ],
    },
}


def _set_nested(d: dict, key_path: str, value):
    """Set a nested dict value using dot-separated key path."""
    keys = key_path.split(".")
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def generate_patches(scored_results: list[dict]) -> list[dict]:
    """Generate config patches based on which attacks succeeded."""
    patches_to_apply = []
    compromised_categories: set[str] = set()

    for result in scored_results:
        if result.get("verdict", {}).get("compromised"):
            compromised_categories.add(result["category"])

    for category in compromised_categories:
        if category in REMEDIATION_PLAYBOOK:
            patches_to_apply.append(
                {"category": category, **REMEDIATION_PLAYBOOK[category]}
            )

    return patches_to_apply


def apply_patches(config: dict, patches: list[dict]) -> dict:
    """Apply remediation patches to openclaw.json config."""
    patched = copy.deepcopy(config)

    for patch_group in patches:
        for key_path, value in patch_group["patches"]:
            _set_nested(patched, key_path, value)
            print(f"  [fix] {key_path} = {json.dumps(value)[:80]}")

    return patched


def diff_configs(before: dict, after: dict) -> list[str]:
    """Generate human-readable diff of config changes."""
    diffs: list[str] = []
    _diff_recursive(before, after, "", diffs)
    return diffs


def _diff_recursive(before, after, path: str, diffs: list[str]):
    if isinstance(after, dict):
        for key in after:
            new_path = f"{path}.{key}" if path else key
            if key not in (before or {}):
                diffs.append(f"  + {new_path} = {json.dumps(after[key])[:80]}")
            else:
                _diff_recursive(
                    (before or {}).get(key), after[key], new_path, diffs
                )
    elif before != after:
        diffs.append(
            f"  ~ {path}: {json.dumps(before)[:40]} -> {json.dumps(after)[:40]}"
        )
