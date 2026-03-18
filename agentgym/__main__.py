"""Allow running as `python -m agentgym`."""

from dotenv import load_dotenv

load_dotenv()

from agentgym.cli import run  # noqa: E402

run()
