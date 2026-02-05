import pandas as pd
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class IDColumnFixer:
    """
    Utility to fix ID column issues in reflection CSV files.
    Consolidates student ID choices (email, 4-digit, anonymous) into a single ID column.
    """
    
    def __init__(self):
        self.id_patterns = {
            'choice_column': [
                'id choice', 'id_choice', 'identity choice', 'identity_choice',
                'preference', 'id preference', 'id_preference',
                # Qualtrics patterns
                r'Q\d+$',  # e.g., Q9
                # Text patterns that might indicate choice
                r'.*comfortable.*share.*email.*',
                r'.*share.*uncc.*email.*',
                r'.*email.*four.*digits.*anonymous.*'
            ],
            'email_column': [
                'email', 'email address', 'email_address', 'uncc email', 'uncc_email',
                # Qualtrics patterns
                r'Q\d+_1_TEXT$',  # e.g., Q9_1_TEXT
                r'.*TEXT.*email.*',
                r'.*email.*TEXT.*'
            ],
            'id4_column': [
                '4 digit', '4_digit', 'four digit', 'four_digit', 'phone digits', 'phone_digits',
                'last four', 'last_four', 'id4', 'four digits', 'four_digits',
                # Qualtrics patterns  
                r'Q\d+_2_TEXT$',  # e.g., Q9_2_TEXT
                r'.*TEXT.*four.*digit.*',
                r'.*four.*digit.*TEXT.*'
            ]
        }
    
    def detect_id_columns(self, df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """
        Detect which columns contain ID choice, email, and 4-digit ID data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with detected column names for 'choice', 'email', 'id4'
        """
        detected = {'choice': None, 'email': None, 'id4': None}
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Check for choice column
            if detected['choice'] is None:
                for pattern in self.id_patterns['choice_column']:
                    if pattern.startswith(r'Q\d+') or pattern.startswith(r'.*'):
                        if re.match(pattern, str(col), re.IGNORECASE):
                            detected['choice'] = col
                            break
                    else:
                        if pattern in col_lower:
                            detected['choice'] = col
                            break
            
            # Check for email column  
            if detected['email'] is None:
                for pattern in self.id_patterns['email_column']:
                    if pattern.startswith(r'Q\d+') or pattern.startswith(r'.*'):
                        if re.match(pattern, str(col), re.IGNORECASE):
                            detected['email'] = col
                            break
                    else:
                        if pattern in col_lower:
                            detected['email'] = col
                            break
            
            # Check for 4-digit ID column
            if detected['id4'] is None:
                for pattern in self.id_patterns['id4_column']:
                    if pattern.startswith(r'Q\d+') or pattern.startswith(r'.*'):
                        if re.match(pattern, str(col), re.IGNORECASE):
                            detected['id4'] = col
                            break
                    else:
                        if pattern in col_lower:
                            detected['id4'] = col
                            break
        
        return detected
    
    def analyze_id_structure(self, df: pd.DataFrame) -> Dict:
        """
        Analyze the current ID structure in the DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'has_single_id_column': 'ID' in df.columns,
            'detected_columns': self.detect_id_columns(df),
            'needs_consolidation': False,
            'sample_data': {},
            'id_formats_found': {},
            'recommendations': []
        }
        
        # If there's already an ID column, analyze its content
        if analysis['has_single_id_column']:
            id_col_data = df['ID'].dropna().astype(str)
            analysis['sample_data']['existing_id'] = id_col_data.head(5).tolist()
            
            # Analyze ID formats in existing column
            for id_val in id_col_data:
                id_str = str(id_val).strip()
                if '@' in id_str:
                    analysis['id_formats_found']['email'] = analysis['id_formats_found'].get('email', 0) + 1
                elif id_str.isdigit() and len(id_str) == 4:
                    analysis['id_formats_found']['four_digit'] = analysis['id_formats_found'].get('four_digit', 0) + 1
                elif id_str.isdigit() and len(id_str) <= 3:
                    analysis['id_formats_found']['short_digit'] = analysis['id_formats_found'].get('short_digit', 0) + 1
                elif id_str.startswith('ID-'):
                    analysis['id_formats_found']['generated'] = analysis['id_formats_found'].get('generated', 0) + 1
                else:
                    analysis['id_formats_found']['other'] = analysis['id_formats_found'].get('other', 0) + 1
        
        # Check if we have separate ID columns that need consolidation
        detected = analysis['detected_columns']
        if detected['choice'] and (detected['email'] or detected['id4']):
            analysis['needs_consolidation'] = True
            
            # Sample the separate columns
            for key, col_name in detected.items():
                if col_name and col_name in df.columns:
                    sample_data = df[col_name].dropna().head(5).tolist()
                    analysis['sample_data'][key] = sample_data
            
            analysis['recommendations'].append(
                f"Found separate ID columns: {[col for col in detected.values() if col]}. "
                "Consider consolidating into single ID column."
            )
        
        return analysis
    
    def consolidate_id_columns(self, df: pd.DataFrame, 
                             choice_col: str = None,
                             email_col: str = None, 
                             id4_col: str = None,
                             auto_detect: bool = True) -> pd.DataFrame:
        """
        Consolidate separate ID columns into a single ID column.
        
        Args:
            df: Input DataFrame
            choice_col: Column indicating ID preference (1=email, 2=4-digit, 3=anonymous)
            email_col: Column containing email addresses
            id4_col: Column containing 4-digit IDs
            auto_detect: Whether to auto-detect columns if not specified
            
        Returns:
            DataFrame with consolidated ID column
        """
        df_copy = df.copy()
        
        # Auto-detect columns if not provided
        if auto_detect and not all([choice_col, email_col, id4_col]):
            detected = self.detect_id_columns(df_copy)
            choice_col = choice_col or detected['choice']
            email_col = email_col or detected['email']
            id4_col = id4_col or detected['id4']
        
        if not choice_col:
            raise ValueError("Choice column not found or specified")
        
        print(f"Consolidating ID columns:")
        print(f"  Choice column: {choice_col}")
        print(f"  Email column: {email_col}")
        print(f"  4-digit ID column: {id4_col}")
        
        def create_consolidated_id(row):
            """Create consolidated ID based on student choice"""
            choice = str(row.get(choice_col, '')).strip()
            
            # Handle different choice representations
            if choice in ['1', '1.0', 'email', 'Email']:
                # Student chose email
                email_val = row.get(email_col, '') if email_col else ''
                if pd.notna(email_val) and str(email_val).strip() and str(email_val).strip() != 'nan':
                    return str(email_val).strip()
                else:
                    return f"ID-{row.name + 1}"  # Fallback to generated ID
                    
            elif choice in ['2', '2.0', '4-digit', '4digit', 'phone']:
                # Student chose 4-digit ID
                id4_val = row.get(id4_col, '') if id4_col else ''
                if pd.notna(id4_val) and str(id4_val).strip() and str(id4_val).strip() != 'nan':
                    return str(id4_val).strip()
                else:
                    return f"ID-{row.name + 1}"  # Fallback to generated ID
                    
            else:
                # Student chose anonymous or invalid choice
                return f"ID-{row.name + 1}"
        
        # Create the consolidated ID column
        df_copy['ID'] = df_copy.apply(create_consolidated_id, axis=1)
        
        # Remove the original ID columns to avoid confusion
        columns_to_remove = [col for col in [choice_col, email_col, id4_col] 
                           if col and col in df_copy.columns]
        
        if columns_to_remove:
            print(f"Removing original ID columns: {columns_to_remove}")
            df_copy = df_copy.drop(columns=columns_to_remove)
        
        # Reorder columns to put ID first
        cols = list(df_copy.columns)
        if 'ID' in cols:
            cols.remove('ID')
            cols.insert(0, 'ID')
            df_copy = df_copy[cols]
        
        return df_copy
    
    def fix_reflection_file(self, file_path: str, 
                          backup: bool = True,
                          choice_col: str = None,
                          email_col: str = None,
                          id4_col: str = None) -> Tuple[bool, str]:
        """
        Fix ID columns in a specific reflection CSV file.
        
        Args:
            file_path: Path to the CSV file
            backup: Whether to create a backup before modifying
            choice_col: Override column name for choice
            email_col: Override column name for email
            id4_col: Override column name for 4-digit ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            # Load the CSV
            df = pd.read_csv(file_path)
            
            # Analyze current structure
            analysis = self.analyze_id_structure(df)
            
            if not analysis['needs_consolidation']:
                return True, "File already has proper ID structure"
            
            # Create backup if requested
            if backup:
                backup_path = file_path.replace('.csv', '_backup.csv')
                df.to_csv(backup_path, index=False)
                print(f"Created backup: {backup_path}")
            
            # Consolidate ID columns
            fixed_df = self.consolidate_id_columns(
                df, 
                choice_col=choice_col,
                email_col=email_col, 
                id4_col=id4_col
            )
            
            # Save the fixed file
            fixed_df.to_csv(file_path, index=False)
            
            return True, f"Successfully fixed ID columns in {file_path}"
            
        except Exception as e:
            return False, f"Error fixing file {file_path}: {str(e)}"
    
    def scan_and_fix_directory(self, directory_path: str, 
                             pattern: str = "*ref*.csv",
                             backup: bool = True) -> Dict[str, List]:
        """
        Scan a directory for reflection files and fix ID columns.
        
        Args:
            directory_path: Directory to scan
            pattern: File pattern to match
            backup: Whether to create backups
            
        Returns:
            Dictionary with lists of fixed, skipped, and failed files
        """
        results = {
            'fixed': [],
            'skipped': [],
            'failed': []
        }
        
        directory = Path(directory_path)
        if not directory.exists():
            results['failed'].append(f"Directory not found: {directory_path}")
            return results
        
        # Find matching files
        csv_files = list(directory.rglob(pattern))
        
        for file_path in csv_files:
            try:
                success, message = self.fix_reflection_file(
                    str(file_path), 
                    backup=backup
                )
                
                if success:
                    if "already has proper" in message:
                        results['skipped'].append(f"{file_path}: {message}")
                    else:
                        results['fixed'].append(f"{file_path}: {message}")
                else:
                    results['failed'].append(f"{file_path}: {message}")
                    
            except Exception as e:
                results['failed'].append(f"{file_path}: Error - {str(e)}")
        
        return results

# Convenience function for command-line usage
def fix_reflection_ids(file_or_directory: str, 
                      choice_col: str = None,
                      email_col: str = None,
                      id4_col: str = None,
                      backup: bool = True) -> None:
    """
    Fix ID columns in reflection files.
    
    Args:
        file_or_directory: Path to a single file or directory to process
        choice_col: Override column name for choice
        email_col: Override column name for email  
        id4_col: Override column name for 4-digit ID
        backup: Whether to create backups
    """
    fixer = IDColumnFixer()
    
    if os.path.isfile(file_or_directory):
        # Single file
        success, message = fixer.fix_reflection_file(
            file_or_directory, backup, choice_col, email_col, id4_col
        )
        print(f"Result: {message}")
        
    elif os.path.isdir(file_or_directory):
        # Directory
        results = fixer.scan_and_fix_directory(file_or_directory, backup=backup)
        
        print(f"\nProcessing complete!")
        print(f"Fixed: {len(results['fixed'])} files")
        print(f"Skipped: {len(results['skipped'])} files") 
        print(f"Failed: {len(results['failed'])} files")
        
        if results['fixed']:
            print("\nFixed files:")
            for item in results['fixed']:
                print(f"  ✅ {item}")
        
        if results['skipped']:
            print("\nSkipped files:")
            for item in results['skipped']:
                print(f"  ⏭️ {item}")
                
        if results['failed']:
            print("\nFailed files:")
            for item in results['failed']:
                print(f"  ❌ {item}")
    else:
        print(f"Path not found: {file_or_directory}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python id_column_fixer.py <file_or_directory> [choice_col] [email_col] [id4_col]")
        print("Example: python id_column_fixer.py /path/to/reflections")
        print("Example: python id_column_fixer.py /path/to/file.csv Q9 Q9_1_TEXT Q9_2_TEXT")
        sys.exit(1)
    
    path = sys.argv[1]
    choice_col = sys.argv[2] if len(sys.argv) > 2 else None
    email_col = sys.argv[3] if len(sys.argv) > 3 else None  
    id4_col = sys.argv[4] if len(sys.argv) > 4 else None
    
    fix_reflection_ids(path, choice_col, email_col, id4_col) 