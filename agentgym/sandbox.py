"""Provision a Blaxel sandbox with OpenClaw + opik-openclaw plugin installed."""

import asyncio
import json
import os

from blaxel.core import SandboxInstance

SANDBOX_NAME = "agentgym-openclaw"
GATEWAY_TOKEN = os.getenv("OPENCLAW_GATEWAY_TOKEN", "agentgym-secret-token-12345")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPIK_API_KEY = os.getenv("OPIK_API_KEY")
OPIK_WORKSPACE = os.getenv("OPIK_WORKSPACE", "default")

OPENCLAW_HOME = "/blaxel/.openclaw"


async def create_sandbox() -> SandboxInstance:
    """Create a Blaxel sandbox with OpenClaw installed."""
    sandbox = await SandboxInstance.create_if_not_exists(
        {
            "name": SANDBOX_NAME,
            "image": "blaxel/node:latest",
            "memory": 4096,
            "ports": [{"target": 18789, "protocol": "HTTP"}],
            "region": "us-pdx-1",
        }
    )
    return sandbox


async def install_openclaw(sandbox: SandboxInstance):
    """Install OpenClaw inside the sandbox."""
    proc = await sandbox.process.exec(
        {
            "command": "npm install -g openclaw@latest",
            "waitForCompletion": True,
            "timeout": 120,
        }
    )
    print(f"[sandbox] OpenClaw installed: exit={proc.exit_code}")


async def configure_openclaw(sandbox: SandboxInstance):
    """Write openclaw.json config with correct model."""
    config = {
        "gateway": {
            "mode": "local",
            "bind": "lan",
        },
        "agents": {
            "defaults": {
                "model": "anthropic/claude-sonnet-4-20250514",
            }
        },
    }

    await sandbox.process.exec(
        {
            "command": f"mkdir -p {OPENCLAW_HOME}",
            "waitForCompletion": True,
            "timeout": 10,
        }
    )

    await sandbox.fs.write(
        f"{OPENCLAW_HOME}/openclaw.json", json.dumps(config, indent=2)
    )

    env_content = f"ANTHROPIC_API_KEY={ANTHROPIC_API_KEY}\n"
    await sandbox.fs.write(f"{OPENCLAW_HOME}/.env", env_content)

    print("[sandbox] OpenClaw configured")


async def provision() -> tuple[SandboxInstance, str]:
    """Full provisioning flow. Returns (sandbox, gateway_url)."""
    print("[agentgym] Provisioning sandbox...")
    sandbox = await create_sandbox()
    await install_openclaw(sandbox)
    await configure_openclaw(sandbox)
    print("[agentgym] OpenClaw ready (agent --local mode)")
    return sandbox, "local"


async def read_config(sandbox: SandboxInstance) -> dict:
    """Read current openclaw.json from the sandbox."""
    content = await sandbox.fs.read(f"{OPENCLAW_HOME}/openclaw.json")
    return json.loads(content)


async def write_config(sandbox: SandboxInstance, config: dict):
    """Write updated openclaw.json to the sandbox."""
    await sandbox.fs.write(
        f"{OPENCLAW_HOME}/openclaw.json",
        json.dumps(config, indent=2),
    )


async def restart_gateway(sandbox: SandboxInstance):
    """No-op in local agent mode — config is read on each agent invocation."""
    print("[sandbox] Config updated (takes effect on next agent call)")
