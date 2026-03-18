"""
AgentGym CLI -- Automated OpenClaw Security Scanner + Auto-Remediation.

Usage: python -m agentgym.cli
"""

import asyncio

from dotenv import load_dotenv

load_dotenv()

from rich.console import Console  # noqa: E402

from agentgym.remediator import apply_patches, generate_patches  # noqa: E402
from agentgym.report import (  # noqa: E402
    print_comparison,
    print_patches,
    print_scan_results,
    print_score,
)
from agentgym.sandbox import (  # noqa: E402
    provision,
    read_config,
    restart_gateway,
    write_config,
)
from agentgym.scanner import run_scan  # noqa: E402
from agentgym.scorer import compute_score, log_to_opik, score_results  # noqa: E402

console = Console()


async def main():
    console.print(
        "[bold cyan]AgentGym -- OpenClaw Security Scanner "
        "+ Auto-Remediation[/bold cyan]\n"
    )

    # Phase 1: Provision
    console.print(
        "[bold]Phase 1: Provisioning OpenClaw on Blaxel sandbox...[/bold]"
    )
    sandbox, gateway_url = await provision()
    console.print(f"[green]>[/green] OpenClaw ready on sandbox\n")

    # Phase 2: Baseline scan
    console.print(
        "[bold]Phase 2: Running baseline security scan (10 attacks)...[/bold]"
    )
    baseline_results = await run_scan(sandbox)
    console.print(
        f"[green]>[/green] {len(baseline_results)} attacks completed\n"
    )

    # Phase 3: Score
    console.print("[bold]Phase 3: Scoring with LLM-as-a-judge...[/bold]")
    baseline_scored = score_results(baseline_results)
    baseline_score = compute_score(baseline_scored)
    print_scan_results(baseline_scored, label="BASELINE SCAN")
    print_score(baseline_score, label="(Before)")
    log_to_opik(baseline_scored, scan_label="baseline")
    console.print()

    # Phase 4: Remediate
    console.print("[bold]Phase 4: Auto-remediating vulnerabilities...[/bold]")
    patches = generate_patches(baseline_scored)
    print_patches(patches)

    if patches:
        config = await read_config(sandbox)
        patched_config = apply_patches(config, patches)
        await write_config(sandbox, patched_config)
        await restart_gateway(sandbox)
        console.print(
            "[green]>[/green] Config patched and gateway restarted\n"
        )

        # Phase 5: Rescan
        console.print(
            "[bold]Phase 5: Re-scanning after remediation...[/bold]"
        )
        rescan_results = await run_scan(sandbox)
        rescan_scored = score_results(rescan_results)
        rescan_score = compute_score(rescan_scored)
        print_scan_results(rescan_scored, label="POST-FIX SCAN")
        print_score(rescan_score, label="(After)")
        log_to_opik(rescan_scored, scan_label="post-fix")

        # Phase 6: Comparison
        console.print("\n[bold]Phase 6: Before vs After[/bold]")
        print_comparison(baseline_score, rescan_score)
    else:
        console.print(
            "[green]Instance already secure -- nothing to fix![/green]"
        )

    console.print(
        "\n[bold cyan]Done! View full traces at: "
        "https://www.comet.com/opik[/bold cyan]"
    )
    console.print(
        "[dim]Open your Opik dashboard -> project 'agentgym' "
        "to see all traced attacks[/dim]"
    )


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
