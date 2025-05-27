"""Command line interface for numlist."""

from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .manager import NumberListManager
from .repl import run_repl


app = typer.Typer(
    name="numlist",
    help="Manage lists of unique positive integers with CSV persistence.",
    add_completion=False
)
console = Console()


def get_manager(db_file: Optional[Path] = None) -> NumberListManager:
    """Get a NumberListManager instance."""
    return NumberListManager(db_file)


@app.command()
def add(
    numbers: List[int] = typer.Argument(..., help="Positive integers to add to the list"),
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use")
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
        console.print(f"[yellow]{len(duplicates)} duplicate(s) skipped: {duplicates}[/yellow]")
    if invalid:
        console.print(f"[red]{len(invalid)} invalid number(s): {invalid}[/red]")


@app.command()
def remove(
    numbers: List[int] = typer.Argument(..., help="Numbers to remove from the list"),
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use")
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
        console.print(f"\n[green]Successfully removed {removed_count} number(s)[/green]")
    if not_found:
        console.print(f"[yellow]{len(not_found)} number(s) not found: {not_found}[/yellow]")


@app.command("list")
def list_numbers(
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use")
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
        row = numbers[i:i+10]
        numbers_str = "  ".join(f"{n:>6}" for n in row)
        table.add_row(numbers_str)
    
    console.print(table)
    console.print(f"\n[green]Total: {len(numbers)} numbers[/green]")


@app.command()
def stats(
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use")
) -> None:
    """Show statistics about the numbers in the list."""
    manager = get_manager(db_file)
    
    stats_data = manager.get_stats()
    
    if stats_data['count'] == 0:
        console.print("[yellow]No numbers in the list yet.[/yellow]")
        return
    
    # Create a nice stats panel
    stats_table = Table(show_header=False, box=None, padding=(0, 1))
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Count", str(stats_data['count']))
    stats_table.add_row("Minimum", str(stats_data['min']))
    stats_table.add_row("Maximum", str(stats_data['max']))
    stats_table.add_row("Sum", str(stats_data['sum']))
    stats_table.add_row("Average", f"{stats_data['average']:.2f}")
    
    console.print(Panel(stats_table, title="📈 Statistics", border_style="blue"))


@app.command()
def clear(
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt")
) -> None:
    """Clear all numbers from the list."""
    manager = get_manager(db_file)
    
    if manager.is_empty():
        console.print("[yellow]List is already empty.[/yellow]")
        return
    
    # Confirmation unless --force is used
    if not force:
        count = len(manager.get_all_numbers())
        confirm = typer.confirm(f"⚠️  Are you sure you want to clear all {count} numbers?")
        if not confirm:
            console.print("[yellow]Clear cancelled.[/yellow]")
            return
    
    if manager.clear_all():
        console.print("[green]✅ All numbers cleared![/green]")
    else:
        console.print("[red]❌ Error clearing numbers![/red]")


@app.command()
def check(
    numbers: List[int] = typer.Argument(..., help="Numbers to check if they exist"),
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use")
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
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use")
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
    
    console.print(Panel(info_table, title="ℹ️  Database Information", border_style="blue"))


@app.command()
def export(
    output_file: Path = typer.Argument(..., help="Output file path"),
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv, json, excel, tsv, pickle, parquet"),
    timestamps: bool = typer.Option(False, "--timestamps", "-t", help="Include timestamps in export"),
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use")
) -> None:
    """Export numbers to various formats."""
    manager = get_manager(db_file)
    
    if manager.is_empty():
        console.print("[yellow]No numbers to export.[/yellow]")
        return
    
    format = format.lower()
    success = False
    
    # Map format to method
    export_methods = {
        "csv": manager.export_to_csv,
        "json": manager.export_to_json,
        "excel": manager.export_to_excel,
        "xlsx": manager.export_to_excel,
        "tsv": manager.export_to_tsv,
        "pickle": manager.export_to_pickle,
        "pkl": manager.export_to_pickle,
        "parquet": manager.export_to_parquet,
    }
    
    if format not in export_methods:
        console.print(f"[red]❌ Unsupported format: {format}[/red]")
        console.print("[yellow]Supported formats: csv, json, excel, tsv, pickle, parquet[/yellow]")
        return
    
    try:
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Special handling for pickle format (doesn't support timestamps option)
        if format in ["pickle", "pkl"]:
            success = export_methods[format](output_file)
        else:
            success = export_methods[format](output_file, timestamps)
        
        if success:
            stats = manager.get_stats()
            console.print(f"[green]✅ Successfully exported {stats['count']} numbers to {output_file}[/green]")
            console.print(f"[cyan]Format: {format.upper()}{' (with timestamps)' if timestamps and format != 'pickle' else ''}[/cyan]")
        else:
            console.print(f"[red]❌ Failed to export to {output_file}[/red]")
            
            # Provide specific error messages for common issues
            if format in ["excel", "xlsx", "parquet"]:
                console.print("[yellow]💡 Make sure you have the required dependencies:[/yellow]")
                console.print("[yellow]   pip install pandas openpyxl pyarrow[/yellow]")
    
    except Exception as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")


@app.command()
def history(
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent entries to show")
) -> None:
    """Show recently added numbers with timestamps."""
    manager = get_manager(db_file)
    
    if manager.is_empty():
        console.print("[yellow]No numbers in the list yet.[/yellow]")
        return
    
    numbers_with_timestamps = manager.get_numbers_with_timestamps()
    
    # Sort by timestamp (most recent first) and limit
    # Note: SQLite timestamps are strings, so we sort them as strings (works for ISO format)
    sorted_numbers = sorted(numbers_with_timestamps, key=lambda x: x['added_at'], reverse=True)
    recent_numbers = sorted_numbers[:limit]
    
    table = Table(title=f"📅 Recent Numbers (last {len(recent_numbers)})", show_header=True)
    table.add_column("Number", style="green", justify="right")
    table.add_column("Added At", style="cyan")
    
    for item in recent_numbers:
        # Format timestamp for better readability
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(item['added_at'].replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = item['added_at']
        
        table.add_row(str(item['number']), formatted_time)
    
    console.print(table)


@app.command()
def repl(
    db_file: Optional[Path] = typer.Option(None, "--db", "-d", help="SQLite database file to use")
) -> None:
    """Start the interactive REPL mode.""" 
    db_file_str = str(db_file) if db_file else None
    
    try:
        run_repl(db_file_str)
    except ImportError:
        console.print("[red]❌ REPL mode requires prompt-toolkit. Install with: pip install prompt-toolkit[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version information")
) -> None:
    """Number List CLI - Manage lists of unique positive integers.
    
    If no command is provided, starts the interactive REPL mode.
    """
    if version:
        console.print("numlist version 1.0.0")
        return
    
    if ctx.invoked_subcommand is None:
        # No subcommand provided, start REPL
        try:
            run_repl()
        except ImportError:
            console.print("[red]❌ REPL mode requires prompt-toolkit. Install with: pip install prompt-toolkit[/red]")
            console.print("\n[yellow]Available CLI commands:[/yellow]")
            console.print("  numlist add 1 2 3     # Add numbers")
            console.print("  numlist list          # Show all numbers")
            console.print("  numlist stats         # Show statistics")
            console.print("  numlist --help        # Show all commands")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
