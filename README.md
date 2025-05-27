# NumList - Number List Manager

A CLI tool for managing lists of unique positive integers with SQLite persistence and multi-format export capabilities.
Disclaimer: This is a toy project vibe coded in no time for personal requirements.

## Features

- ✅ Add/remove positive integers with duplicate checking
- 📊 Statistics and list display
- 💾 Persistent SQLite storage with timestamps
- 📤 Export to multiple formats (CSV, JSON, Excel, TSV, Pickle, Parquet)
- 🖥️ Both CLI commands and interactive REPL mode
- 🎨 Rich, colorful output using Rich library
- ⚡ Fast SQLite operations with proper error handling
- 📅 Timestamp tracking for all additions
- 🗂️ Follows Linux XDG Base Directory Specification

## Storage Location

Data is stored in `~/.local/share/numlist/numbers.db` following Linux conventions (XDG Base Directory Specification). You can also specify custom database files using the `--db` option.

## Installation

### Using uv (recommended)

```bash
# Clone or create the project
git clone https://github.com/ragul-kachiappan/NumList
cd NumList

# Install dependencies and the package
uv sync
uv pip install -e .

# Or install as a tool globally
uv tool install .
```

### Using pip

```bash
pip install -e .
```

### Using pipx (for global installation)

```bash
pipx install .
```

## Usage

### CLI Commands

```bash
# Add numbers to the list
numlist add 1 2 3 42 100

# Remove numbers from the list
numlist remove 2 3

# List all numbers
numlist list

# Show statistics
numlist stats

# Show recent additions with timestamps
numlist history

# Check if numbers exist
numlist check 1 42 999

# Clear all numbers
numlist clear

# Clear all numbers without confirmation
numlist clear --force

# Show database information
numlist info

# Export to various formats
numlist export output.csv --format csv
numlist export data.json --format json --timestamps
numlist export report.xlsx --format excel --timestamps
numlist export data.tsv --format tsv
numlist export backup.pkl --format pickle
numlist export analysis.parquet --format parquet

# Start interactive REPL mode
numlist repl

# Use a custom database file
numlist add 1 2 3 --db my_numbers.db
numlist export output.csv --db my_numbers.db
```

### Export Formats

- **CSV**: Comma-separated values (`.csv`)
- **JSON**: JSON format with metadata (`.json`)
- **Excel**: Excel workbook with multiple sheets (`.xlsx`)
- **TSV**: Tab-separated values (`.tsv`)
- **Pickle**: Python pickle format (`.pkl`)
- **Parquet**: Columnar storage format (`.parquet`)

All formats except Pickle support the `--timestamps` option to include when numbers were added.

### Interactive REPL Mode

```bash
# Start REPL (default behavior)
numlist

# Or explicitly
numlist repl
```

In REPL mode, you can:
- Enter positive integers to add them
- Use commands: `stats`, `list`, `history`, `remove [number]`, `clear`, `help`, `quit`

### REPL Example Session

```
📊 Number List REPL
Type "help" for commands or enter positive integers to add them to your list.
Data is persisted in: /home/user/.local/share/numlist/numbers.db

number> 42
✅ Successfully added 42 to the list!

number> 100
✅ Successfully added 100 to the list!

number> stats
📈 Statistics:
• Count: 2
• Min: 42
• Max: 100
• Sum: 142
• Average: 71.00

number> history
📅 Recent Numbers (last 10):
   100 - 2024-01-15 14:32:10
    42 - 2024-01-15 14:31:55

number> quit
Goodbye! 👋
```

## Export Examples

```bash
# Export all numbers to CSV
numlist export my_numbers.csv

# Export with timestamps to JSON
numlist export data.json --format json --timestamps

# Export to Excel with multiple sheets
numlist export report.xlsx --format excel --timestamps

# Export for data science (Parquet format)
numlist export analysis.parquet --format parquet --timestamps
```

## File Structure

The tool automatically creates and manages a SQLite database file in `~/.local/share/numlist/numbers.db` following Linux XDG Base Directory Specification. You can specify a custom database file using the `--db` option.

## Error Handling

- Only positive integers are accepted (> 0)
- Duplicate numbers are rejected with appropriate messages
- Invalid input (decimals, negative numbers, text) is handled gracefully
- File I/O errors are caught and reported

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd numlist

# Install in development mode with dev dependencies
uv sync --all-extras

# Install pre-commit hooks (optional)
pre-commit install
```

### Code Quality

```bash
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Type checking
uv run mypy src/

# Run tests
uv run pytest
```

### Building and Distribution

```bash
# Build the package
uv build

# Install from wheel
pip install dist/numlist-*.whl
```

## Requirements

- Python 3.8+
- typer >= 0.9.0
- prompt-toolkit >= 3.0.0
- pandas >= 1.5.0 (for Excel/Parquet export)
- openpyxl >= 3.0.0 (for Excel export)
- pyarrow >= 10.0.0 (for Parquet export)
- rich (automatically installed with typer)

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run code quality checks
6. Submit a pull request
