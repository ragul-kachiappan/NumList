"""numlist - A CLI tool for managing lists of unique positive integers."""

from .cli import app
from .manager import NumberListManager

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = ["NumberListManager", "app"]
