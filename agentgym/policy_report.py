"""Terminal output for policy-gate preflight results."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_preflight(results: list[dict], summary: dict[str, int]):
    table = Table(
        title="Policy-Gate Preflight (Go sidecar)",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Attack", style="bold", width=34)
    table.add_column("Category", width=16)
    table.add_column("Decision", width=18)
    table.add_column("Rule", width=10)
    table.add_column("Reason", width=36)

    color = {
        "DENY": "red",
        "REQUIRE_APPROVAL": "yellow",
        "ALLOW": "green",
    }

    for row in results:
        decision = row["decision"]
        table.add_row(
            row["attack"],
            row["category"],
            f"[{color.get(decision, 'white')}]{decision}[/{color.get(decision, 'white')}]",
            row.get("rule_id", "?"),
            (row.get("reason") or "")[:36],
        )

    console.print(table)
    console.print(
        Panel(
            f"DENY: {summary.get('DENY', 0)} | "
            f"REQUIRE_APPROVAL: {summary.get('REQUIRE_APPROVAL', 0)} | "
            f"ALLOW: {summary.get('ALLOW', 0)}",
            title="Preventive Coverage",
            border_style="cyan",
        )
    )
