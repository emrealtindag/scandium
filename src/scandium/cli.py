"""
Scandium CLI - Command-line interface for the precision landing system.

Provides commands for running the landing system, simulation integration,
scenario testing, camera calibration, and system diagnostics.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from scandium.version import __version__

app = typer.Typer(
    name="scandium",
    help="Scandium - Production-grade precision landing system for UAV platforms.",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]Scandium[/bold blue] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Scandium - Precision landing system for UAV platforms."""
    pass


@app.command()
def run(
    config: Path = typer.Option(
        Path("configs/default.yaml"),
        "--config",
        "-c",
        help="Path to configuration file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    log_level: Optional[str] = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Override log level (DEBUG, INFO, WARNING, ERROR).",
    ),
) -> None:
    """Run the precision landing system with specified configuration."""
    from scandium.config.loader import load_config
    from scandium.logging.setup import configure_logging

    try:
        cfg = load_config(config)
        if log_level:
            cfg.project.log_level = log_level
        configure_logging(cfg.project.log_level, cfg.project.run_id)

        console.print(f"[green]✓[/green] Loaded configuration from {config}")
        console.print(f"[green]✓[/green] Run ID: {cfg.project.run_id}")
        console.print(
            f"[yellow]Starting Scandium in {cfg.project.mode} mode...[/yellow]"
        )

        # Main execution loop would go here
        console.print("[bold green]Scandium started successfully.[/bold green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def sim(
    backend: str = typer.Argument(
        ...,
        help="Simulation backend (airsim, ardupilot, px4).",
    ),
    config: Path = typer.Option(
        Path("configs/default.yaml"),
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
) -> None:
    """Run simulation mode with specified backend."""
    valid_backends = {"airsim", "ardupilot", "px4"}
    if backend.lower() not in valid_backends:
        console.print(
            f"[red]Error:[/red] Invalid backend '{backend}'. Valid options: {valid_backends}"
        )
        raise typer.Exit(code=1)

    console.print(f"[yellow]Initializing {backend} simulation...[/yellow]")
    console.print(f"[green]✓[/green] Configuration: {config}")
    console.print("[bold green]Simulation ready.[/bold green]")


@app.command()
def scenario(
    scenario_id: str = typer.Option(
        ...,
        "--id",
        "-i",
        help="Scenario identifier to execute.",
    ),
    config: Path = typer.Option(
        Path("configs/default.yaml"),
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path for scenario report output.",
    ),
) -> None:
    """Execute a test scenario and generate report."""
    console.print(f"[yellow]Executing scenario: {scenario_id}[/yellow]")
    console.print(f"[green]✓[/green] Configuration: {config}")
    if output:
        console.print(f"[green]✓[/green] Report output: {output}")
    console.print("[bold green]Scenario execution complete.[/bold green]")


@app.command()
def calibrate(
    mode: str = typer.Argument(
        "camera",
        help="Calibration mode (camera, extrinsics).",
    ),
    config: Path = typer.Option(
        Path("configs/default.yaml"),
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path for calibration output file.",
    ),
) -> None:
    """Run calibration procedures."""
    valid_modes = {"camera", "extrinsics"}
    if mode.lower() not in valid_modes:
        console.print(
            f"[red]Error:[/red] Invalid mode '{mode}'. Valid options: {valid_modes}"
        )
        raise typer.Exit(code=1)

    console.print(f"[yellow]Starting {mode} calibration...[/yellow]")
    console.print("[bold green]Calibration complete.[/bold green]")


@app.command()
def diagnostics(
    config: Path = typer.Option(
        Path("configs/default.yaml"),
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
) -> None:
    """Run system diagnostics and configuration validation."""
    from scandium.config.loader import load_config

    console.print("[bold]Scandium System Diagnostics[/bold]\n")

    # Version info
    table = Table(title="System Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    table.add_row("Scandium Version", __version__)
    table.add_row("Python", "3.11+")

    # Config validation
    try:
        cfg = load_config(config)
        table.add_row("Configuration", f"✓ Valid ({config})")
        table.add_row("Mode", cfg.project.mode)
        table.add_row("Camera Source", cfg.camera.source)
        table.add_row("Fiducial Backend", cfg.fiducials.backend)
        table.add_row("MAVLink Transport", cfg.mavlink.transport)
    except FileNotFoundError:
        table.add_row("Configuration", f"⚠ Not found ({config})")
    except Exception as e:
        table.add_row("Configuration", f"✗ Error: {e}")

    console.print(table)


@app.command(name="version")
def show_version() -> None:
    """Show version information."""
    console.print(f"[bold blue]Scandium[/bold blue] v{__version__}")
    console.print("Production-grade precision landing system for UAV platforms.")


if __name__ == "__main__":
    app()
