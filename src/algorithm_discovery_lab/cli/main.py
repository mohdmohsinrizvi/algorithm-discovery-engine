"""CLI entry point."""

from __future__ import annotations

import json
import os
import sys

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from algorithm_discovery_lab.config.experiment import ExperimentConfig, SearchConfig
from algorithm_discovery_lab.core.candidate import CandidateState
from algorithm_discovery_lab.problems.sorting_network import SortingNetworkProblem
from algorithm_discovery_lab.storage.db import Storage

console = Console()

DB_PATH = os.environ.get("ADL_DB", "adl.db")


def get_storage() -> Storage:
    return Storage(DB_PATH)


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Algorithm Discovery Lab - Search, Verify, Benchmark, Discover."""


@cli.command()
@click.option("--n", default=8, help="Input size (number of wires)")
@click.option("--search", default="evolutionary", type=click.Choice(["random", "evolutionary", "map_elites"]))
@click.option("--population", default=200, help="Population size")
@click.option("--generations", default=500, help="Number of generations")
@click.option("--mutation-rate", default=0.15, help="Mutation rate")
@click.option("--crossover-rate", default=0.7, help="Crossover rate")
@click.option("--elitism-rate", default=0.05, help="Elitism rate")
@click.option("--seed", default=42, help="Random seed")
@click.option("--benchmark-reps", default=1000, help="Benchmark repetitions")
@click.option("--output", "-o", default=None, help="Output JSON file")
def discover(
    n: int,
    search: str,
    population: int,
    generations: int,
    mutation_rate: float,
    crossover_rate: float,
    elitism_rate: float,
    seed: int,
    benchmark_reps: int,
    output: str | None,
) -> None:
    """Run a discovery experiment on sorting networks."""
    config = ExperimentConfig(
        problem_type="sorting_network",
        n=n,
        search=SearchConfig(
            algorithm=search,
            population_size=population,
            generations=generations,
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
            elitism_rate=elitism_rate,
        ),
        seed=seed,
        benchmark_repetitions=benchmark_reps,
    )

    storage = get_storage()

    def on_event(event):
        if event.event_type.value == "generation_completed" and event.generation % 25 == 0:
            console.print(
                f"  [dim]Gen {event.generation:4d}[/dim] | "
                f"Verified: {event.data.get('total_verified', event.data.get('archive_size', 0))}"
            )
        elif event.event_type.value == "new_best_found":
            console.print(
                f"  [bold green]NEW BEST[/bold green] gen={event.generation} "
                f"comparators={int(event.data.get('comparator_count', 0))} depth={int(event.data.get('depth', 0))}"
            )
        elif event.event_type.value == "archive_updated":
            console.print(
                f"  [bold cyan]ARCHIVE[/bold cyan] gen={event.generation} "
                f"coverage={event.data.get('coverage', 0):.1%} "
                f"size={event.data.get('archive_size', 0)}"
            )

    console.print(Panel(
        f"[bold]Sorting Network Discovery[/bold]\n"
        f"n={n} | search={search} | pop={population} | gen={generations} | seed={seed}",
        title="Algorithm Discovery Lab",
    ))

    from algorithm_discovery_lab.experiments.runner import ExperimentRunner
    runner = ExperimentRunner(config, storage)

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Running search...", total=None)
        result = runner.run(callback=on_event)
        progress.update(task, completed=True)

    # Print results
    console.print()
    if result["discovery"]:
        d = result["discovery"]
        console.print(Panel(
            f"[bold green]{d['id']}[/bold green]\n"
            f"Problem: {d['problem']}\n"
            f"Verification: {d['verification_method']} ({d['verification_result'].get('inputs_tested', 0)} inputs)\n"
            f"Comparators: {d['cost_metrics'].get('comparator_count', '?')}\n"
            f"Depth: {d['cost_metrics'].get('depth', '?')}\n"
            f"Benchmark median: {d['benchmark_result'].get('median_ns', '?')} ns\n"
            f"Elapsed: {result['elapsed_seconds']:.1f}s",
            title="Discovery",
        ))
    else:
        console.print("[yellow]No verified candidate found.[/yellow]")

    # Save output
    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        console.print(f"\nResults saved to {output}")


@cli.command()
@click.argument("candidate_file")
def verify(candidate_file: str) -> None:
    """Verify a candidate from a JSON file."""
    with open(candidate_file) as f:
        data = json.load(f)

    problem = SortingNetworkProblem(data.get("n", 8))
    network = problem.deserialize(data)
    verifier = __import__("algorithm_discovery_lab.verification.verifier", fromlist=["get_verifier"])
    v = verifier.get_verifier("exhaustive", data.get("n", 8))

    console.print(Panel(f"Verifying sorting network n={data.get('n', 8)}", title="Verification"))

    result = v.verify(network)
    if result.verified:
        console.print(f"[bold green]VERIFIED[/bold green] - {result.inputs_tested} inputs tested in {result.duration_ms:.2f}ms")
    else:
        console.print(f"[bold red]FAILED[/bold red] - counterexample: {result.counterexample}")
        console.print(f"Tested {result.inputs_tested} inputs, found {len(result.failures)} failures")


@cli.command()
@click.argument("candidate_file")
@click.option("--reps", default=1000, help="Benchmark repetitions")
def benchmark(candidate_file: str, reps: int) -> None:
    """Benchmark a candidate from a JSON file."""
    from algorithm_discovery_lab.benchmarking.engine import benchmark_sorting_network
    from algorithm_discovery_lab.problems.sorting_network import SortingNetworkProblem

    with open(candidate_file) as f:
        data = json.load(f)

    problem = SortingNetworkProblem(data.get("n", 8))
    network = problem.deserialize(data)

    console.print(Panel(f"Benchmarking sorting network n={data.get('n', 8)}", title="Benchmark"))

    br = benchmark_sorting_network(network, "cli-candidate", repetitions=reps)
    table = Table(title="Benchmark Results")
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Runs", str(br.runs))
    table.add_row("Median", f"{br.median_ns:.1f} ns")
    table.add_row("Mean", f"{br.mean_ns:.1f} ns")
    table.add_row("StdDev", f"{br.stddev_ns:.1f} ns")
    table.add_row("Min", f"{br.min_ns:.1f} ns")
    table.add_row("Max", f"{br.max_ns:.1f} ns")
    table.add_row("Comparators", str(br.comparator_count))
    table.add_row("Depth", str(br.depth))
    console.print(table)


@cli.command()
def museum() -> None:
    """List discoveries in the museum."""
    storage = get_storage()
    discoveries = storage.list_discoveries()

    if not discoveries:
        console.print("[dim]No discoveries yet. Run `adl discover` first.[/dim]")
        return

    table = Table(title="Discovery Museum")
    table.add_column("ID", style="bold")
    table.add_column("Problem")
    table.add_column("Comparators")
    table.add_column("Depth")
    table.add_column("Verified")
    table.add_column("Timestamp")

    import datetime
    for d in discoveries:
        metrics = json.loads(d.get("cost_metrics", "{}"))
        vr = json.loads(d.get("verification_result", "{}"))
        ts = datetime.datetime.fromtimestamp(d.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M")
        table.add_row(
            d["id"],
            d.get("problem", ""),
            str(metrics.get("comparator_count", "?")),
            str(metrics.get("depth", "?")),
            "Yes" if vr.get("verified") else "No",
            ts,
        )
    console.print(table)


@cli.command()
@click.argument("experiment_config")
def run(experiment_config: str) -> None:
    """Run experiment from YAML config."""
    config = ExperimentConfig.from_yaml(experiment_config)
    storage = get_storage()

    from algorithm_discovery_lab.experiments.runner import ExperimentRunner
    runner = ExperimentRunner(config, storage)

    console.print(Panel(f"Running experiment from {experiment_config}", title="Experiment"))

    result = runner.run()
    console.print(f"\nExperiment {result['experiment_id']} completed in {result['elapsed_seconds']:.1f}s")
    if result["discovery"]:
        console.print(f"Discovery: {result['discovery']['id']}")


@cli.command()
def demo() -> None:
    """Run a quick demo discovery."""
    console.print(Panel(
        "[bold]Algorithm Discovery Lab - Demo[/bold]\n"
        "Running a quick sorting network discovery for n=5",
        title="Demo",
    ))

    config = ExperimentConfig(
        n=5,
        search=SearchConfig(
            algorithm="evolutionary",
            population_size=50,
            generations=100,
        ),
        seed=42,
        benchmark_repetitions=100,
    )

    storage = get_storage()

    def on_event(event):
        if event.event_type.value == "new_best_found":
            console.print(
                f"  [bold green]NEW BEST[/bold green] gen={event.generation} "
                f"comparators={int(event.data.get('comparator_count', 0))} depth={int(event.data.get('depth', 0))}"
            )
        elif event.event_type.value == "generation_completed" and event.generation % 20 == 0:
            console.print(f"  [dim]Gen {event.generation}[/dim] verified={event.data.get('total_verified', 0)}")

    from algorithm_discovery_lab.experiments.runner import ExperimentRunner
    runner = ExperimentRunner(config, storage)
    result = runner.run(callback=on_event)

    if result["discovery"]:
        d = result["discovery"]
        console.print(f"\n[bold green]Demo Discovery: {d['id']}[/bold green]")
        console.print(f"  Comparators: {d['cost_metrics'].get('comparator_count')}")
        console.print(f"  Depth: {d['cost_metrics'].get('depth')}")
        console.print(f"  Verified: {d['verification_result'].get('inputs_tested')} inputs")
    else:
        console.print("\n[yellow]Demo did not find a verified candidate. Try increasing generations.[/yellow]")


@cli.command()
def status() -> None:
    """Show system status."""
    storage = get_storage()
    exps = storage.list_experiments()
    discs = storage.list_discoveries()

    table = Table(title="System Status")
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Experiments", str(len(exps)))
    table.add_row("Discoveries", str(len(discs)))
    table.add_row("Database", DB_PATH)
    console.print(table)


if __name__ == "__main__":
    cli()
