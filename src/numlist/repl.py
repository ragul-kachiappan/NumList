"""Interactive REPL for number list management."""

from datetime import datetime

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style

from .manager import NumberListManager


def create_style() -> Style:
    """Create custom style for the prompt."""
    return Style.from_dict(
        {
            "prompt": "#ansiblue bold",
            "success": "#ansigreen",
            "error": "#ansired",
            "info": "#ansiyellow",
        }
    )


def print_help() -> None:
    """Print help information."""
    help_text = """
<ansiblue><b>Number List REPL Commands:</b></ansiblue>

• <ansigreen>Enter a positive integer</ansigreen> - Add number to the list
• <ansigreen>stats</ansigreen> - Show statistics about current numbers
• <ansigreen>list</ansigreen> - Show all numbers in the list
• <ansigreen>history</ansigreen> - Show recently added numbers with timestamps
• <ansigreen>remove [number]</ansigreen> - Remove a specific number
• <ansigreen>clear</ansigreen> - Clear all numbers (with confirmation)
• <ansigreen>help</ansigreen> - Show this help message
• <ansigreen>quit</ansigreen> or <ansigreen>exit</ansigreen> - Exit the program

Only positive integers are allowed (e.g., 1, 2, 42, 100)
Negative numbers and decimals are not permitted.
All numbers are automatically saved to SQLite database.
Use CLI commands for export: numlist export output.csv --format csv
    """
    print_formatted_text(HTML(help_text))


def print_stats(manager: NumberListManager) -> None:
    """Print statistics about the number list."""
    stats = manager.get_stats()
    if stats["count"] == 0:
        print_formatted_text(
            HTML("<ansiyellow>No numbers in the list yet.</ansiyellow>")
        )
    else:
        print_formatted_text(
            HTML(
                f"""
<ansigreen><b>📈 Statistics:</b></ansigreen>
• Count: {stats['count']}
• Min: {stats['min']}
• Max: {stats['max']}
• Sum: {stats['sum']}
• Average: {stats['average']:.2f}
        """.strip()
            )
        )


def print_list(manager: NumberListManager) -> None:
    """Print all numbers in the list."""
    if manager.is_empty():
        print_formatted_text(
            HTML("<ansiyellow>No numbers in the list yet.</ansiyellow>")
        )
    else:
        numbers = manager.get_all_numbers()
        print_formatted_text(HTML("<ansigreen><b>📋 Current Numbers:</b></ansigreen>"))
        # Display in rows of 10
        for i in range(0, len(numbers), 10):
            row = numbers[i : i + 10]
            numbers_str = ", ".join(str(n) for n in row)
            print_formatted_text(HTML(f"<ansiwhite>{numbers_str}</ansiwhite>"))


def print_history(manager: NumberListManager) -> None:
    """Print recently added numbers with timestamps."""
    if manager.is_empty():
        print_formatted_text(
            HTML("<ansiyellow>No numbers in the list yet.</ansiyellow>")
        )
        return

    numbers_with_timestamps = manager.get_numbers_with_timestamps()

    # Sort by timestamp (most recent first) and limit to 10
    sorted_numbers = sorted(
        numbers_with_timestamps, key=lambda x: x["added_at"], reverse=True
    )
    recent_numbers = sorted_numbers[:10]

    print_formatted_text(
        HTML("<ansigreen><b>📅 Recent Numbers (last 10):</b></ansigreen>")
    )

    for item in recent_numbers:
        # Format timestamp for better readability
        try:
            dt = datetime.fromisoformat(item["added_at"].replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_time = item["added_at"]

        print_formatted_text(
            HTML(f'<ansiwhite>{item["number"]:>6} - ' f'{formatted_time}</ansiwhite>')
        )


def handle_remove_command(manager: NumberListManager, user_input: str) -> None:
    """Handle the remove command."""
    parts = user_input.split()
    if len(parts) != 2:
        print_formatted_text(HTML("<ansired>❌ Usage: remove [number]</ansired>"))
        return

    try:
        number = int(parts[1])
        if number <= 0:
            print_formatted_text(
                HTML("<ansired>❌ Error: Only positive integers are allowed.</ansired>")
            )
            return

        if manager.remove_number(number):
            print_formatted_text(
                HTML(
                    f"<ansigreen>✅ Successfully removed {number} "
                    "from the list!</ansigreen>"
                )
            )
        else:
            print_formatted_text(
                HTML(f"<ansired>❌ Error: {number} is not in the list!</ansired>")
            )
    except ValueError:
        print_formatted_text(
            HTML(f'<ansired>❌ Invalid number: "{parts[1]}"</ansired>')
        )


def handle_clear_command(manager: NumberListManager) -> None:
    """Handle the clear command with confirmation."""
    if manager.is_empty():
        print_formatted_text(HTML("<ansiyellow>List is already empty.</ansiyellow>"))
        return

    confirm = prompt(
        HTML("<ansired><b>⚠️  Clear all numbers? (yes/no): </b></ansired>")
    ).lower()
    if confirm in ["yes", "y"]:
        if manager.clear_all():
            print_formatted_text(HTML("<ansigreen>✅ All numbers cleared!</ansigreen>"))
        else:
            print_formatted_text(HTML("<ansired>❌ Error clearing numbers!</ansired>"))
    else:
        print_formatted_text(HTML("<ansiyellow>Clear cancelled.</ansiyellow>"))


def validate_and_add_number(manager: NumberListManager, user_input: str) -> None:
    """Validate and add a number to the list."""
    # Check if it contains decimal point
    if "." in user_input:
        print_formatted_text(
            HTML(
                f'<ansired>❌ Error: "{user_input}" is not a valid positive integer. '
                "Decimals are not allowed.</ansired>"
            )
        )
        return

    try:
        number = int(user_input)

        if number <= 0:
            print_formatted_text(
                HTML(
                    f"<ansired>❌ Error: {number} is not positive. "
                    "Only positive integers (> 0) are allowed.</ansired>"
                )
            )
            return

        if manager.add_number(number):
            print_formatted_text(
                HTML(
                    f"<ansigreen>✅ Successfully added {number} to the list!</ansigreen>"  # noqa
                )
            )
        else:
            print_formatted_text(
                HTML(f"<ansired>❌ Error: {number} is already in the list!</ansired>")
            )

    except ValueError:
        print_formatted_text(
            HTML(
                f'<ansired>❌ Invalid input: "{user_input}" is not a valid positive '
                "integer.</ansired>"
            )
        )
        print_formatted_text(
            HTML('<ansiyellow>Type "help" for available commands.</ansiyellow>')
        )


def run_repl(db_file: str | None = None) -> None:
    """Run the interactive REPL."""
    style = create_style()
    history = InMemoryHistory()

    # Initialize number manager
    manager = NumberListManager(db_file)

    # Welcome message
    print_formatted_text(HTML("<ansiblue><b>📊 Number List REPL</b></ansiblue>"))
    print_formatted_text(
        HTML(
            '<ansiyellow>Type "help" for commands or enter positive integers to add '
            "them to your list.</ansiyellow>"
        )
    )
    print_formatted_text(
        HTML(f"<ansiyellow>Data is persisted in: {manager.get_db_path()}</ansiyellow>")
    )

    # Show initial stats
    stats = manager.get_stats()
    if stats["count"] > 0:
        print_formatted_text(
            HTML(
                f'<ansigreen>Loaded {stats["count"]} numbers from database.</ansigreen>'
            )
        )
    print()

    # Command completer
    commands = ["help", "stats", "list", "history", "remove", "clear", "quit", "exit"]
    completer = WordCompleter(commands, ignore_case=True)

    while True:
        try:
            # Get user input
            user_input = prompt(
                HTML("<ansiblue><b>number> </b></ansiblue>"),
                history=history,
                completer=completer,
                style=style,
            ).strip()

            if not user_input:
                continue

            # Handle commands
            command = user_input.lower()

            if command in ["quit", "exit"]:
                print_formatted_text(HTML("<ansigreen>Goodbye! 👋</ansigreen>"))
                break

            elif command == "help":
                print_help()

            elif command == "stats":
                print_stats(manager)

            elif command == "list":
                print_list(manager)

            elif command == "history":
                print_history(manager)

            elif command.startswith("remove "):
                handle_remove_command(manager, user_input)

            elif command == "clear":
                handle_clear_command(manager)

            else:
                # Try to parse as a positive integer
                validate_and_add_number(manager, user_input)

        except KeyboardInterrupt:
            print_formatted_text(
                HTML(
                    '\n<ansiyellow>Use "quit" or "exit" to leave gracefully.</ansiyellow>'  # noqa
                )
            )
        except EOFError:
            print_formatted_text(HTML("\n<ansigreen>Goodbye! 👋</ansigreen>"))
            break
        except Exception as e:
            print_formatted_text(HTML(f"<ansired>❌ Unexpected error: {e!s}</ansired>"))
