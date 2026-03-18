"""Rich terminal output for scan results."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

GRADE_COLORS = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}


def print_scan_results(scored_results: list[dict], label: str = "SCAN"):
    """Print a formatted table of scan results."""
    table = Table(
        title=f"AgentGym {label} Results",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Attack", style="bold", width=35)
    table.add_column("Category", width=18)
    table.add_column("Result", width=12)
    table.add_column("Severity", width=10)
    table.add_column("Reasoning", width=40)

    for r in scored_results:
        v = r.get("verdict", {})
        compromised = v.get("compromised")
        severity = v.get("severity", "?")
        reasoning = v.get("reasoning", "")[:40]

        if compromised:
            result_str = "[red]COMPROMISED[/red]"
            sev_str = f"[red]{severity}[/red]"
        elif compromised is False:
            result_str = "[green]RESISTED[/green]"
            sev_str = f"[green]{severity}[/green]"
        else:
            result_str = "[yellow]UNKNOWN[/yellow]"
            sev_str = severity

        table.add_row(r["name"], r["category"], result_str, sev_str, reasoning)

    console.print(table)


def print_score(score: dict, label: str = ""):
    """Print the overall security score."""
    grade = score["grade"]
    color = GRADE_COLORS.get(grade, "white")

    panel = Panel(
        f"[bold {color}]Grade: {grade}[/bold {color}]\n"
        f"Score: {score['score']}\n"
        f"Compromised: {score['compromised']} | Resisted: {score['resisted']}",
        title=f"Security Score {label}",
        border_style=color,
    )
    console.print(panel)


def print_patches(patches: list[dict]):
    """Print remediation actions."""
    if not patches:
        console.print("[green]No vulnerabilities found - no patches needed![/green]")
        return

    console.print(
        f"\n[bold yellow]Applying {len(patches)} remediation(s):[/bold yellow]"
    )
    for p in patches:
        console.print(
            f"  [yellow]*[/yellow] [{p['category']}] {p['description']}"
        )


def print_comparison(before_score: dict, after_score: dict):
    """Print before/after comparison."""
    table = Table(title="Before vs After", box=box.ROUNDED)
    table.add_column("Metric", style="bold")
    table.add_column("Before", justify="center")
    table.add_column("After", justify="center")

    b_ratio = before_score["resisted"] / before_score["total_attacks"]
    a_ratio = after_score["resisted"] / after_score["total_attacks"]

    table.add_row("Score", before_score["score"], after_score["score"])
    table.add_row(
        "Grade",
        f"[red]{before_score['grade']}[/red]",
        f"[green]{after_score['grade']}[/green]",
    )
    table.add_row(
        "Defense Rate",
        f"[red]{b_ratio:.0%}[/red]",
        f"[green]{a_ratio:.0%}[/green]",
    )

    console.print(table)
