"""Number list management with SQLite persistence and export capabilities."""

import sqlite3
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, Optional, Union, List
import os

try:
    import pandas as pd
except ImportError:
    pd = None


class NumberListManager:
    """Manages a persistent list of unique positive integers using SQLite."""
    
    def __init__(self, db_file: Optional[Union[str, Path]] = None):
        if db_file is None:
            # Use XDG Base Directory Specification for Linux
            data_dir = Path.home() / ".local" / "share" / "numlist"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_file = data_dir / "numbers.db"
        else:
            self.db_file = Path(db_file)
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database and create tables if they don't exist."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS numbers (
                    number INTEGER PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster lookups (though not needed for small datasets)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_added_at ON numbers(added_at)
            """)
            
            conn.commit()
    
    def add_number(self, number: int) -> bool:
        """Add a number to the list.
        
        Args:
            number: The positive integer to add.
            
        Returns:
            bool: True if added successfully, False if duplicate.
            
        Raises:
            ValueError: If number is not a positive integer.
        """
        if not isinstance(number, int) or number <= 0:
            raise ValueError("Number must be a positive integer")
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO numbers (number) VALUES (?)",
                    (number,)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Duplicate key violation
            return False
    
    def remove_number(self, number: int) -> bool:
        """Remove a number from the list.
        
        Args:
            number: The number to remove.
            
        Returns:
            bool: True if removed successfully, False if not found.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM numbers WHERE number = ?", (number,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_all(self) -> bool:
        """Clear all numbers from the list.
        
        Returns:
            bool: True if cleared successfully, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM numbers")
                conn.commit()
                return True
        except Exception:
            return False
    
    def has_number(self, number: int) -> bool:
        """Check if a number exists in the list.
        
        Args:
            number: The number to check.
            
        Returns:
            bool: True if the number exists, False otherwise.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM numbers WHERE number = ?", (number,))
            return cursor.fetchone() is not None
    
    def get_all_numbers(self) -> List[int]:
        """Get all numbers in sorted order.
        
        Returns:
            List[int]: Sorted list of all numbers.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT number FROM numbers ORDER BY number")
            return [row[0] for row in cursor.fetchall()]
    
    def get_numbers_with_timestamps(self) -> List[Dict[str, Union[int, str]]]:
        """Get all numbers with their timestamps.
        
        Returns:
            List[Dict]: List of dictionaries with 'number' and 'added_at' keys.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT number, added_at FROM numbers ORDER BY number")
            return [
                {"number": row[0], "added_at": row[1]}
                for row in cursor.fetchall()
            ]
    
    def get_stats(self) -> Dict[str, Optional[Union[int, float]]]:
        """Get statistics about the current number list.
        
        Returns:
            dict: Statistics including count, min, max, sum, and average.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as count,
                    MIN(number) as min_val,
                    MAX(number) as max_val,
                    SUM(number) as sum_val,
                    AVG(number) as avg_val
                FROM numbers
            """)
            row = cursor.fetchone()
            
            if row[0] == 0:  # count is 0
                return {
                    "count": 0,
                    "min": None,
                    "max": None,
                    "sum": None,
                    "average": None
                }
            
            return {
                "count": row[0],
                "min": row[1],
                "max": row[2],
                "sum": row[3],
                "average": row[4]
            }
    
    def is_empty(self) -> bool:
        """Check if the list is empty.
        
        Returns:
            bool: True if empty, False otherwise.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM numbers")
            return cursor.fetchone()[0] == 0
    
    def get_db_path(self) -> Path:
        """Get the path to the SQLite database file.
        
        Returns:
            Path: Path to the database file.
        """
        return self.db_file.absolute()
    
    def get_db_info(self) -> Dict[str, Union[str, int, bool]]:
        """Get information about the database file.
        
        Returns:
            Dict: Database file information.
        """
        info = {
            "path": str(self.get_db_path()),
            "exists": self.db_file.exists(),
            "size_bytes": 0,
            "count": 0
        }
        
        if self.db_file.exists():
            info["size_bytes"] = self.db_file.stat().st_size
            info["count"] = self.get_stats()["count"]
        
        return info
    
    # Export Methods
    
    def export_to_csv(self, output_file: Union[str, Path], include_timestamps: bool = False) -> bool:
        """Export numbers to CSV format.
        
        Args:
            output_file: Path to output CSV file.
            include_timestamps: Whether to include timestamp column.
            
        Returns:
            bool: True if export successful, False otherwise.
        """
        try:
            if pd is None:
                # Fallback to basic CSV writing
                import csv
                with open(output_file, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    if include_timestamps:
                        writer.writerow(['number', 'added_at'])
                        data = self.get_numbers_with_timestamps()
                        for item in data:
                            writer.writerow([item['number'], item['added_at']])
                    else:
                        writer.writerow(['number'])
                        numbers = self.get_all_numbers()
                        for number in numbers:
                            writer.writerow([number])
                return True
            
            # Use pandas for better handling
            if include_timestamps:
                data = self.get_numbers_with_timestamps()
                df = pd.DataFrame(data)
            else:
                numbers = self.get_all_numbers()
                df = pd.DataFrame({'number': numbers})
            
            df.to_csv(output_file, index=False)
            return True
        except Exception:
            return False
    
    def export_to_json(self, output_file: Union[str, Path], include_timestamps: bool = False) -> bool:
        """Export numbers to JSON format.
        
        Args:
            output_file: Path to output JSON file.
            include_timestamps: Whether to include timestamps.
            
        Returns:
            bool: True if export successful, False otherwise.
        """
        try:
            if include_timestamps:
                data = {
                    "numbers": self.get_numbers_with_timestamps(),
                    "exported_at": datetime.now().isoformat(),
                    "stats": self.get_stats()
                }
            else:
                data = {
                    "numbers": self.get_all_numbers(),
                    "exported_at": datetime.now().isoformat(),
                    "stats": self.get_stats()
                }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False
    
    def export_to_excel(self, output_file: Union[str, Path], include_timestamps: bool = False) -> bool:
        """Export numbers to Excel format.
        
        Args:
            output_file: Path to output Excel file.
            include_timestamps: Whether to include timestamps.
            
        Returns:
            bool: True if export successful, False otherwise.
        """
        if pd is None:
            return False
            
        try:
            if include_timestamps:
                data = self.get_numbers_with_timestamps()
                df = pd.DataFrame(data)
            else:
                numbers = self.get_all_numbers()
                df = pd.DataFrame({'number': numbers})
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Numbers', index=False)
                
                # Add stats sheet
                stats_df = pd.DataFrame([self.get_stats()])
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            return True
        except Exception:
            return False
    
    def export_to_tsv(self, output_file: Union[str, Path], include_timestamps: bool = False) -> bool:
        """Export numbers to TSV (Tab-Separated Values) format.
        
        Args:
            output_file: Path to output TSV file.
            include_timestamps: Whether to include timestamps.
            
        Returns:
            bool: True if export successful, False otherwise.
        """
        try:
            if pd is None:
                # Fallback to basic TSV writing
                with open(output_file, 'w') as f:
                    if include_timestamps:
                        f.write("number\tadded_at\n")
                        data = self.get_numbers_with_timestamps()
                        for item in data:
                            f.write(f"{item['number']}\t{item['added_at']}\n")
                    else:
                        f.write("number\n")
                        numbers = self.get_all_numbers()
                        for number in numbers:
                            f.write(f"{number}\n")
                return True
            
            # Use pandas
            if include_timestamps:
                data = self.get_numbers_with_timestamps()
                df = pd.DataFrame(data)
            else:
                numbers = self.get_all_numbers()
                df = pd.DataFrame({'number': numbers})
            
            df.to_csv(output_file, sep='\t', index=False)
            return True
        except Exception:
            return False
    
    def export_to_pickle(self, output_file: Union[str, Path]) -> bool:
        """Export numbers to Python pickle format.
        
        Args:
            output_file: Path to output pickle file.
            
        Returns:
            bool: True if export successful, False otherwise.
        """
        try:
            data = {
                "numbers": self.get_all_numbers(),
                "numbers_with_timestamps": self.get_numbers_with_timestamps(),
                "stats": self.get_stats(),
                "exported_at": datetime.now().isoformat()
            }
            
            with open(output_file, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception:
            return False
    
    def export_to_parquet(self, output_file: Union[str, Path], include_timestamps: bool = False) -> bool:
        """Export numbers to Parquet format (for data science).
        
        Args:
            output_file: Path to output Parquet file.
            include_timestamps: Whether to include timestamps.
            
        Returns:
            bool: True if export successful, False otherwise.
        """
        if pd is None:
            return False
            
        try:
            if include_timestamps:
                data = self.get_numbers_with_timestamps()
                df = pd.DataFrame(data)
                # Convert timestamp to proper datetime
                df['added_at'] = pd.to_datetime(df['added_at'])
            else:
                numbers = self.get_all_numbers()
                df = pd.DataFrame({'number': numbers})
            
            df.to_parquet(output_file, index=False)
            return True
        except Exception:
            return False