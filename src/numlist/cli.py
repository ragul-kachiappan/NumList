"""Command line interface for numlist."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .manager import NumberListManager
from .repl import run_repl

app = typer.Typer(
    name="numlist",
    help="Manage lists of unique positive integers with CSV persistence.",
    add_completion=False,
)
console = Console()


def get_manager(db_file: Path | None = None) -> NumberListManager:
    """Get a NumberListManager instance."""
    return NumberListManager(db_file)


@app.command()
def add(
    numbers: list[int] = typer.Argument(
        ..., help="Positive integers to add to the list"
    ),
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
) -> None:
    """Add one or more positive integers to the list."""
    manager = get_manager(db_file)

    added_count = 0
    duplicates = []
    invalid = []

    for number in numbers:
        if number <= 0:
            invalid.append(number)
            continue

        try:
            if manager.add_number(number):
                added_count += 1
                console.print(f"✅ Added {number}", style="green")
            else:
                duplicates.append(number)
                console.print(f"⚠️  {number} already exists", style="yellow")
        except ValueError as e:
            invalid.append(number)
            console.print(f"❌ {number}: {e}", style="red")

    # Summary
    if added_count > 0:
        console.print(f"\n[green]Successfully added {added_count} number(s)[/green]")
    if duplicates:
        console.print(
            f"[yellow]{len(duplicates)} duplicate(s) skipped: {duplicates}[/yellow]"
        )
    if invalid:
        console.print(f"[red]{len(invalid)} invalid number(s): {invalid}[/red]")


@app.command()
def remove(
    numbers: list[int] = typer.Argument(..., help="Numbers to remove from the list"),
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
) -> None:
    """Remove one or more numbers from the list."""
    manager = get_manager(db_file)

    removed_count = 0
    not_found = []

    for number in numbers:
        if manager.remove_number(number):
            removed_count += 1
            console.print(f"✅ Removed {number}", style="green")
        else:
            not_found.append(number)
            console.print(f"⚠️  {number} not found", style="yellow")

    # Summary
    if removed_count > 0:
        console.print(
            f"\n[green]Successfully removed {removed_count} number(s)[/green]"
        )
    if not_found:
        console.print(
            f"[yellow]{len(not_found)} number(s) not found: {not_found}[/yellow]"
        )


@app.command("list")
def list_numbers(
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
) -> None:
    """Display all numbers in the list."""
    manager = get_manager(db_file)

    if manager.is_empty():
        console.print("[yellow]No numbers in the list yet.[/yellow]")
        return

    numbers = manager.get_all_numbers()

    # Create a table for better display
    table = Table(title="📋 Number List", show_header=False, box=None)

    # Display numbers in rows of 10
    for i in range(0, len(numbers), 10):
        row = numbers[i : i + 10]
        numbers_str = "  ".join(f"{n:>6}" for n in row)
        table.add_row(numbers_str)

    console.print(table)
    console.print(f"\n[green]Total: {len(numbers)} numbers[/green]")


@app.command()
def stats(
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
) -> None:
    """Show statistics about the numbers in the list."""
    manager = get_manager(db_file)

    stats_data = manager.get_stats()

    if stats_data["count"] == 0:
        console.print("[yellow]No numbers in the list yet.[/yellow]")
        return

    # Create a nice stats panel
    stats_table = Table(show_header=False, box=None, padding=(0, 1))
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Count", str(stats_data["count"]))
    stats_table.add_row("Minimum", str(stats_data["min"]))
    stats_table.add_row("Maximum", str(stats_data["max"]))
    stats_table.add_row("Sum", str(stats_data["sum"]))
    stats_table.add_row("Average", f"{stats_data['average']:.2f}")

    console.print(Panel(stats_table, title="📈 Statistics", border_style="blue"))


@app.command()
def clear(
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Clear all numbers from the list."""
    manager = get_manager(db_file)

    if manager.is_empty():
        console.print("[yellow]List is already empty.[/yellow]")
        return

    # Confirmation unless --force is used
    if not force:
        count = len(manager.get_all_numbers())
        confirm = typer.confirm(
            f"⚠️  Are you sure you want to clear all {count} numbers?"
        )
        if not confirm:
            console.print("[yellow]Clear cancelled.[/yellow]")
            return

    if manager.clear_all():
        console.print("[green]✅ All numbers cleared![/green]")
    else:
        console.print("[red]❌ Error clearing numbers![/red]")


@app.command()
def check(
    numbers: list[int] = typer.Argument(..., help="Numbers to check if they exist"),
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
) -> None:
    """Check if numbers exist in the list."""
    manager = get_manager(db_file)

    for number in numbers:
        if manager.has_number(number):
            console.print(f"✅ {number} exists", style="green")
        else:
            console.print(f"❌ {number} does not exist", style="red")


@app.command()
def info(
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
) -> None:
    """Show information about the database file and current state."""
    manager = get_manager(db_file)
    db_info = manager.get_db_info()

    info_table = Table(show_header=False, box=None, padding=(0, 1))
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Database File", db_info["path"])
    info_table.add_row("File Exists", "✅ Yes" if db_info["exists"] else "❌ No")

    if db_info["exists"]:
        info_table.add_row("File Size", f"{db_info['size_bytes']} bytes")

    info_table.add_row("Numbers Count", str(db_info["count"]))

    console.print(
        Panel(info_table, title="i Database Information", border_style="blue")
    )


@app.command()
def export(
    output_file: Path = typer.Argument(..., help="Output file path"),
    format: str = typer.Option(
        "csv",
        "--format",
        "-f",
        help="Export format: csv, json, excel, tsv, pickle, parquet",
    ),
    timestamps: bool = typer.Option(
        False, "--timestamps", "-t", help="Include timestamps in export"
    ),
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
) -> None:
    """Export numbers to various formats."""
    manager = get_manager(db_file)

    try:
        manager.export_numbers(output_file, format, timestamps)
        console.print(f"[green]✅ Successfully exported to {output_file}[/green]")
    except ValueError as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error during export: {e}[/red]")


@app.command()
def history(
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
    limit: int = typer.Option(
        10, "--limit", "-n", help="Number of recent entries to show"
    ),
) -> None:
    """Show recent history of operations."""
    manager = get_manager(db_file)

    try:
        history_data = manager.get_history(limit)
        if not history_data:
            console.print("[yellow]No history available.[/yellow]")
            return

        history_table = Table(show_header=True, box=None)
        history_table.add_column("Timestamp", style="cyan")
        history_table.add_column("Operation", style="green")
        history_table.add_column("Details", style="white")

        for entry in history_data:
            history_table.add_row(
                entry["timestamp"],
                entry["operation"],
                entry["details"],
            )

        console.print(
            Panel(
                history_table,
                title="📜 Operation History",
                border_style="blue",
            )
        )
    except Exception as e:
        console.print(f"[red]❌ Error retrieving history: {e}[/red]")


@app.command()
def repl(
    db_file: Path | None = typer.Option(
        None, "--db", "-d", help="SQLite database file to use"
    ),
) -> None:
    """Start an interactive REPL session."""
    manager = get_manager(db_file)
    try:
        run_repl(manager)
    except KeyboardInterrupt:
        console.print("\n[yellow]REPL session ended.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error in REPL: {e}[/red]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version information"),
) -> None:
    """Manage lists of unique positive integers with SQLite persistence."""
    if version:
        from importlib.metadata import version

        console.print(f"numlist version {version('numlist')}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
