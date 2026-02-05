import pandas as pd
import re
from typing import Dict, Optional, Tuple, List

class ReflectionConverter:
    """
    Handles cleaning and preprocessing of reflection survey data from CSV files.
    Converts raw survey exports into clean, analysis-ready format.
    
    Features:
    - Column filtering based on regex patterns
    - Header row application from any row in the data
    - Metadata row removal (NEW): Skip metadata rows that appear after headers
    - Section and emotion code mapping with multiple emotion support
    - ID column consolidation
    - Data validation and quality checks
    - Emotion usage analysis and statistics
    
    Multiple Emotion Support:
    The system now handles comma-separated multiple emotion selections:
    - Single emotions: "1" → "Excited"
    - Multiple emotions: "2,3" → "Satisfied, Frustrated"
    - Handles spaces and edge cases automatically
    - Provides usage statistics and patterns analysis
    
    Metadata Row Handling:
    Survey exports often contain metadata rows immediately after the header row.
    These typically include:
    - Import/Export IDs
    - Response IDs  
    - Question metadata
    - Other system-generated information
    
    The metadata_rows_to_skip parameter allows you to automatically remove these
    rows during processing, with a default of 3 rows which covers most common cases.
    """
    
    def __init__(self, section_mapping: Optional[Dict[str, str]] = None, 
                 emotion_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize with custom mappings or defaults.
        
        Args:
            section_mapping: Custom mapping for section codes to names
            emotion_mapping: Custom mapping for emotion codes to names
        """
        self.section_mapping = section_mapping or {
            '1': '001 In-person MW 2:30-3:45PM',
            '2': '051 Online TR 11:30-12:45PM'
        }
        
        self.emotion_mapping = emotion_mapping or {
            '1': 'Excited',
            '2': 'Satisfied', 
            '3': 'Frustrated',
            '4': 'Confused',
            '5': 'Neutral'
        }
    
    def update_section_mapping(self, section_mapping: Dict[str, str]):
        """Update the section mapping with new values."""
        self.section_mapping = section_mapping
    
    def update_emotion_mapping(self, emotion_mapping: Dict[str, str]):
        """Update the emotion mapping with new values."""
        self.emotion_mapping = emotion_mapping
    
    def filter_valid_columns(self, df: pd.DataFrame, pattern: str = r'^Q\d+(?:_\d+_TEXT)?$') -> List[str]:
        """
        Filter DataFrame columns based on a regex pattern.
        
        Args:
            df: Input DataFrame
            pattern: Regex pattern to match valid columns
            
        Returns:
            List of column names that match the pattern
        """
        return [col for col in df.columns if re.match(pattern, col)]
    
    def apply_new_headers(self, df: pd.DataFrame, valid_columns: List[str], 
                         header_row_index: int = 0, metadata_rows_to_skip: int = 0) -> pd.DataFrame:
        """
        Apply new headers from a specific row in the DataFrame and optionally skip metadata rows.
        
        Args:
            df: Input DataFrame
            valid_columns: List of valid column names to keep
            header_row_index: Row index to use as headers
            metadata_rows_to_skip: Number of metadata rows to skip after the header row
            
        Returns:
            DataFrame with new headers applied and metadata rows removed
        """
        # Filter to valid columns first
        filtered_df = df[valid_columns].copy()
        
        # Apply new headers from the specified row
        if header_row_index < len(filtered_df):
            new_headers = filtered_df.iloc[header_row_index].astype(str).tolist()
            filtered_df.columns = new_headers
            
            # Remove the header row, any rows before it, and metadata rows after it
            start_row = header_row_index + 1 + metadata_rows_to_skip
            filtered_df = filtered_df.iloc[start_row:].reset_index(drop=True)
        
        return filtered_df
    
    def apply_section_mapping(self, df: pd.DataFrame, section_column: str) -> pd.DataFrame:
        """
        Apply section mapping to convert numeric codes to descriptive names.
        
        Args:
            df: Input DataFrame
            section_column: Name of the section column to map
            
        Returns:
            DataFrame with mapped section values
        """
        if section_column not in df.columns:
            return df
        
        df_copy = df.copy()
        df_copy[section_column] = df_copy[section_column].astype(str).map(
            lambda x: self.section_mapping.get(x.strip(), x)
        )
        return df_copy
    
    def apply_emotion_mapping_and_combine(self, df: pd.DataFrame, emotion_column: str, 
                                        text_column: Optional[str] = None) -> pd.DataFrame:
        """
        Apply emotion mapping and optionally combine with text responses.
        Handles both single emotions and comma-separated multiple emotions.
        
        Args:
            df: Input DataFrame
            emotion_column: Name of the emotion column to map
            text_column: Optional text column to combine with emotions
            
        Returns:
            DataFrame with mapped emotion values
        """
        if emotion_column not in df.columns:
            return df
        
        df_copy = df.copy()
        
        # Map emotion codes to readable text, handling multiple values
        def map_emotions(emotion_value):
            """Map single or multiple emotion codes to readable text."""
            if pd.isna(emotion_value) or emotion_value == '':
                return ''
            
            emotion_str = str(emotion_value).strip()
            
            # Handle empty or whitespace-only strings
            if not emotion_str or emotion_str.lower() in ['nan', 'none', 'null']:
                return ''
            
            # Check if it contains comma-separated values
            if ',' in emotion_str:
                # Split by comma, map each emotion, and join back
                emotion_codes = [code.strip() for code in emotion_str.split(',')]
                mapped_emotions = []
                
                for code in emotion_codes:
                    if code:  # Skip empty strings
                        mapped_emotion = self.emotion_mapping.get(code, code)
                        mapped_emotions.append(mapped_emotion)
                
                return ', '.join(mapped_emotions)
            else:
                # Single emotion code
                return self.emotion_mapping.get(emotion_str, emotion_str)
        
        df_copy[emotion_column] = df_copy[emotion_column].apply(map_emotions)
        
        # Combine with text column if specified
        if text_column and text_column in df_copy.columns:
            def combine_emotion_text(row):
                emotion = str(row[emotion_column]) if pd.notna(row[emotion_column]) else ''
                text = str(row[text_column]) if pd.notna(row[text_column]) else ''
                
                if emotion and text:
                    return f"{emotion}, {text}"
                elif emotion:
                    return emotion
                elif text:
                    return text
                else:
                    return ''
            
            df_copy[emotion_column] = df_copy.apply(combine_emotion_text, axis=1)
            # Remove the separate text column since it's now combined
            df_copy = df_copy.drop(columns=[text_column])
        
        return df_copy
    
    def create_id_column(self, df: pd.DataFrame, id_choice_col: str, 
                        email_col: str, id4_col: str) -> pd.DataFrame:
        """
        Create a unified ID column based on student choice.
        
        Args:
            df: Input DataFrame
            id_choice_col: Column indicating ID preference (1=email, 2=4-digit, 3=anonymous)
            email_col: Column containing email addresses
            id4_col: Column containing 4-digit IDs
            
        Returns:
            DataFrame with new ID column and original ID columns removed
        """
        df_copy = df.copy()
        
        # print(f"\n=== ID COLUMN CONSOLIDATION ===")
        # print(f"Choice column: {id_choice_col}")
        # print(f"Email column: {email_col}")
        # print(f"4-digit ID column: {id4_col}")
        # print(f"Total rows to process: {len(df_copy)}")
        
        # Validate that required columns exist
        missing_cols = []
        for col_name, col in [("Choice", id_choice_col), ("Email", email_col), ("4-digit", id4_col)]:
            if col not in df_copy.columns:
                missing_cols.append(f"{col_name} ({col})")
        
        if missing_cols:
            raise ValueError(f"Missing columns: {', '.join(missing_cols)}")
        
        # Statistics tracking
        choice_stats = {'1': 0, '2': 0, '3': 0, 'invalid': 0}
        id_format_stats = {'email': 0, 'four_digit': 0, 'generated': 0, 'other': 0}
        
        def create_id(row):
            choice = str(row[id_choice_col]).strip()
            row_num = row.name + 1
            
            # Count choice distribution
            if choice in ['1', '1.0']:
                choice_stats['1'] += 1
                # Student chose email
                email_val = row[email_col]
                if pd.notna(email_val) and str(email_val).strip() and str(email_val).strip().lower() not in ['nan', '', 'none']:
                    result_id = str(email_val).strip()
                    id_format_stats['email'] += 1
                    # print(f"Row {row_num}: Choice=Email, Result='{result_id}'")
                    return result_id
                else:
                    result_id = f"ID-{row_num}"
                    id_format_stats['generated'] += 1
                    # print(f"Row {row_num}: Choice=Email but no email provided, Result='{result_id}'")
                    return result_id
                    
            elif choice in ['2', '2.0']:
                choice_stats['2'] += 1
                # Student chose 4-digit ID
                id4_val = row[id4_col]
                if pd.notna(id4_val) and str(id4_val).strip() and str(id4_val).strip().lower() not in ['nan', '', 'none']:
                    result_id = str(id4_val).strip()
                    # Validate it's actually numeric
                    if result_id.isdigit():
                        id_format_stats['four_digit'] += 1
                    else:
                        id_format_stats['other'] += 1
                    # print(f"Row {row_num}: Choice=4-digit, Result='{result_id}'")
                    return result_id
                else:
                    result_id = f"ID-{row_num}"
                    id_format_stats['generated'] += 1
                    # print(f"Row {row_num}: Choice=4-digit but no ID provided, Result='{result_id}'")
                    return result_id
                    
            elif choice in ['3', '3.0']:
                choice_stats['3'] += 1
                # Student chose anonymous
                result_id = f"ID-{row_num}"
                id_format_stats['generated'] += 1
                # print(f"Row {row_num}: Choice=Anonymous, Result='{result_id}'")
                return result_id
            else:
                choice_stats['invalid'] += 1
                # Invalid or missing choice - default to anonymous
                result_id = f"ID-{row_num}"
                id_format_stats['generated'] += 1
                # print(f"Row {row_num}: Choice=Invalid ('{choice}'), Result='{result_id}'")
                return result_id
        
        # Create new ID column
        df_copy['ID'] = df_copy.apply(create_id, axis=1)
        
        # Print summary statistics
        # print(f"\n=== CONSOLIDATION SUMMARY ===")
        # print(f"Choice distribution:")
        # print(f"  1 (Email): {choice_stats['1']} students")
        # print(f"  2 (4-digit): {choice_stats['2']} students") 
        # print(f"  3 (Anonymous): {choice_stats['3']} students")
        # print(f"  Invalid: {choice_stats['invalid']} students")
        
        # print(f"\nID format results:")
        # print(f"  Email addresses: {id_format_stats['email']}")
        # print(f"  4-digit numbers: {id_format_stats['four_digit']}")
        # print(f"  Generated IDs: {id_format_stats['generated']}")
        # print(f"  Other formats: {id_format_stats['other']}")
        
        # Validate results
        total_processed = sum(choice_stats.values())
        total_ids = len(df_copy['ID'].dropna())
        if total_processed != total_ids:
            print(f"WARNING: Processed {total_processed} choices but got {total_ids} IDs")
        
        # Sample validation - check first few IDs
        # print(f"\nSample IDs created:")
        # for i, (idx, row) in enumerate(df_copy.head(3).iterrows()):
        #     original_choice = row[id_choice_col]
        #     final_id = row['ID']
        #     print(f"  Row {idx+1}: Choice='{original_choice}' → ID='{final_id}'")
        
        # Remove original ID columns to avoid confusion
        id_cols_to_remove = [id_choice_col, email_col, id4_col]
        df_copy = df_copy.drop(columns=[col for col in id_cols_to_remove if col in df_copy.columns])
        
        # print(f"Removed original ID columns: {id_cols_to_remove}")
        # print(f"=== ID CONSOLIDATION COMPLETE ===\n")
        
        return df_copy
    
    def validate_id_consolidation(self, original_df: pd.DataFrame, processed_df: pd.DataFrame,
                                id_choice_col: str, email_col: str, id4_col: str) -> Dict[str, any]:
        """
        Validate that ID consolidation worked correctly.
        
        Args:
            original_df: Original DataFrame before processing
            processed_df: DataFrame after ID consolidation
            id_choice_col: Name of the choice column
            email_col: Name of the email column  
            id4_col: Name of the 4-digit ID column
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'statistics': {},
            'sample_mismatches': []
        }
        
        try:
            # Basic checks
            if 'ID' not in processed_df.columns:
                validation['issues'].append("No ID column found in processed data")
                validation['is_valid'] = False
                return validation
            
            if len(original_df) != len(processed_df):
                validation['issues'].append(f"Row count mismatch: {len(original_df)} → {len(processed_df)}")
                validation['is_valid'] = False
            
            # Check for missing IDs
            null_ids = processed_df['ID'].isnull().sum()
            if null_ids > 0:
                validation['issues'].append(f"{null_ids} rows have null IDs")
                validation['is_valid'] = False
            
            # Validate ID formats match choices
            mismatches = 0
            for idx, (orig_row, proc_row) in enumerate(zip(original_df.itertuples(), processed_df.itertuples())):
                choice = str(getattr(orig_row, id_choice_col, '')).strip()
                final_id = str(getattr(proc_row, 'ID', '')).strip()
                
                expected_format = None
                if choice in ['1', '1.0']:
                    expected_format = 'email'
                elif choice in ['2', '2.0']:
                    expected_format = 'four_digit'  
                elif choice in ['3', '3.0']:
                    expected_format = 'generated'
                
                actual_format = None
                if '@' in final_id:
                    actual_format = 'email'
                elif final_id.isdigit() and len(final_id) == 4:
                    actual_format = 'four_digit'
                elif final_id.startswith('ID-'):
                    actual_format = 'generated'
                else:
                    actual_format = 'other'
                
                if expected_format and expected_format != actual_format:
                    mismatches += 1
                    if len(validation['sample_mismatches']) < 5:  # Keep first 5 examples
                        validation['sample_mismatches'].append({
                            'row': idx + 1,
                            'choice': choice,
                            'expected': expected_format,
                            'actual': actual_format,
                            'id': final_id
                        })
            
            validation['statistics'] = {
                'total_rows': len(processed_df),
                'null_ids': null_ids,
                'format_mismatches': mismatches,
                'mismatch_rate': mismatches / len(processed_df) if len(processed_df) > 0 else 0
            }
            
            if mismatches > 0:
                validation['issues'].append(f"{mismatches} ID format mismatches found")
                if mismatches / len(processed_df) > 0.1:  # More than 10% mismatches
                    validation['is_valid'] = False
                    
        except Exception as e:
            validation['issues'].append(f"Validation error: {str(e)}")
            validation['is_valid'] = False
        
        return validation
    
    def reorder_columns_with_id(self, df: pd.DataFrame, id_position: int = 0) -> pd.DataFrame:
        """
        Reorder columns to place ID at specified position.
        
        Args:
            df: Input DataFrame
            id_position: Position for ID column (0-based index)
            
        Returns:
            DataFrame with reordered columns
        """
        cols = list(df.columns)
        if 'ID' in cols:
            cols.remove('ID')
            cols.insert(id_position, 'ID')
            return df[cols]
        return df
    
    def filter_by_section(self, df: pd.DataFrame, section_column: str, 
                         selected_section: str) -> pd.DataFrame:
        """
        Filter DataFrame by selected section.
        
        Args:
            df: Input DataFrame
            section_column: Name of the section column
            selected_section: Section to filter by ('All Sections' for no filter)
            
        Returns:
            Filtered DataFrame
        """
        if selected_section == 'All Sections':
            return df
        return df[df[section_column] == selected_section]
    
    def process_reflection_data(self, df: pd.DataFrame, 
                              column_pattern: str = r'^Q\d+(?:_\d+_TEXT)?$',
                              header_row_index: int = 0,
                              metadata_rows_to_skip: int = 3,
                              section_column_index: Optional[int] = 0,
                              emotion_column_index: Optional[int] = 1,
                              text_column_index: Optional[int] = 2,
                              id_choice_col: Optional[str] = None,
                              email_col: Optional[str] = None,
                              id4_col: Optional[str] = None) -> Tuple[pd.DataFrame, List[str]]:
        """
        Complete processing pipeline for reflection survey data.
        
        Args:
            df: Input DataFrame
            column_pattern: Regex pattern for valid columns
            header_row_index: Row to use as headers
            metadata_rows_to_skip: Number of metadata rows to skip after the header row (default: 3)
            section_column_index: Index of section column (None to skip)
            emotion_column_index: Index of emotion column (None to skip)
            text_column_index: Index of text column to combine with emotions (None to skip)
            id_choice_col: Column name for ID choice
            email_col: Column name for email
            id4_col: Column name for 4-digit ID
            
        Returns:
            Tuple of (processed_dataframe, list_of_removed_columns)
        """
        # Filter valid columns
        valid_columns = self.filter_valid_columns(df, column_pattern)
        removed_columns = list(set(df.columns) - set(valid_columns))
        
        # Apply new headers and filter columns, skipping metadata rows
        cleaned_df = self.apply_new_headers(df, valid_columns, header_row_index, metadata_rows_to_skip)
        
        # Get column names after header application
        column_names = list(cleaned_df.columns)
        
        # Apply section mapping if specified
        if section_column_index is not None and section_column_index < len(column_names):
            section_col = column_names[section_column_index]
            cleaned_df = self.apply_section_mapping(cleaned_df, section_col)
        
        # Apply emotion mapping and combine with text if specified
        if emotion_column_index is not None and emotion_column_index < len(column_names):
            emotion_col = column_names[emotion_column_index]
            text_col = None
            if text_column_index is not None and text_column_index < len(column_names):
                text_col = column_names[text_column_index]
            cleaned_df = self.apply_emotion_mapping_and_combine(cleaned_df, emotion_col, text_col)
        
        # Create ID column if ID columns are specified
        if all([id_choice_col, email_col, id4_col]):
            print(f"\n🔧 DEBUG: Adding ID columns")
            print(f"Cleaned DF shape before ID processing: {cleaned_df.shape}")
            print(f"Header row index: {header_row_index}")
            print(f"Metadata rows to skip: {metadata_rows_to_skip}")
            
            # Ensure ID columns are present (add from original df if needed)
            for col in [id_choice_col, email_col, id4_col]:
                if col not in cleaned_df.columns and col in df.columns:
                    # CRITICAL: Account for header row and metadata rows removal
                    start_row = header_row_index + 1 + metadata_rows_to_skip
                    original_col_data = df[col].iloc[start_row:].reset_index(drop=True)
                    # Only take as many rows as we have in cleaned_df to ensure alignment
                    if len(original_col_data) >= len(cleaned_df):
                        cleaned_df[col] = original_col_data.iloc[:len(cleaned_df)]
                    else:
                        cleaned_df[col] = original_col_data
                    print(f"Added {col}: {len(original_col_data)} values, used first {len(cleaned_df)}")
            
            # Show sample data before ID processing
            print(f"\n📊 Sample data before ID processing:")
            sample_cols = [id_choice_col, email_col, id4_col]
            for i in range(min(3, len(cleaned_df))):
                row_data = []
                for col in sample_cols:
                    if col in cleaned_df.columns:
                        val = cleaned_df.iloc[i][col]
                        row_data.append(f"{col}='{val}'")
                print(f"  Row {i+1}: {', '.join(row_data)}")
            
            cleaned_df = self.create_id_column(cleaned_df, id_choice_col, email_col, id4_col)
            cleaned_df = self.reorder_columns_with_id(cleaned_df)
            
            # Show sample data after ID processing
            print(f"\n✅ Sample data after ID processing:")
            for i in range(min(3, len(cleaned_df))):
                final_id = cleaned_df.iloc[i]['ID']
                print(f"  Row {i+1}: ID='{final_id}'")
            print(f"🔧 DEBUG: ID processing complete\n")
        
        return cleaned_df, removed_columns
    
    def get_section_options(self, df: pd.DataFrame, section_column_index: int = 0) -> List[str]:
        """
        Get unique section values for filtering options.
        
        Args:
            df: Processed DataFrame
            section_column_index: Index of section column
            
        Returns:
            List of unique section values
        """
        if section_column_index < len(df.columns):
            section_col = df.columns[section_column_index]
            unique_sections = list(df[section_col].unique())
            return ['All Sections'] + unique_sections
        return ['All Sections'] 

    def analyze_metadata_rows(self, df: pd.DataFrame, header_row_index: int = 0, max_check_rows: int = 10) -> dict:
        """
        Analyze the DataFrame to suggest metadata row removal.
        
        Args:
            df: Input DataFrame
            header_row_index: Row index to use as headers
            max_check_rows: Maximum number of rows to check for metadata patterns
            
        Returns:
            Dictionary with analysis results and suggestions
        """
        analysis = {
            'suggested_skip_rows': 0,
            'confidence': 'low',
            'reasons': [],
            'preview_rows': []
        }
        
        if header_row_index >= len(df) - 1:
            return analysis
        
        # Check rows after header for metadata patterns
        start_row = header_row_index + 1
        end_row = min(start_row + max_check_rows, len(df))
        
        for i in range(start_row, end_row):
            row = df.iloc[i]
            row_analysis = {
                'row_index': i,
                'likely_metadata': False,
                'reasons': []
            }
            
            # Check for common metadata patterns
            non_null_values = row.dropna()
            if len(non_null_values) > 0:
                # Check if row contains import/export metadata
                text_values = [str(v).lower() for v in non_null_values if pd.notna(v)]
                metadata_keywords = ['import', 'export', 'generated', 'qualtrics', 'survey', 'response']
                
                for keyword in metadata_keywords:
                    if any(keyword in text for text in text_values):
                        row_analysis['likely_metadata'] = True
                        row_analysis['reasons'].append(f"Contains '{keyword}' keyword")
                
                # Check if row has very few non-null values compared to total columns
                if len(non_null_values) < len(df.columns) * 0.1:
                    row_analysis['likely_metadata'] = True
                    row_analysis['reasons'].append("Very sparse data (likely metadata)")
                
                # Check if row contains only numeric codes or short text
                if all(len(str(v)) <= 5 for v in non_null_values):
                    row_analysis['likely_metadata'] = True
                    row_analysis['reasons'].append("Contains only short values (likely codes)")
            
            analysis['preview_rows'].append(row_analysis)
            
            # Update suggestion based on analysis
            if row_analysis['likely_metadata']:
                analysis['suggested_skip_rows'] = max(analysis['suggested_skip_rows'], i - start_row + 1)
                analysis['reasons'].extend(row_analysis['reasons'])
        
        # Set confidence based on findings
        if analysis['suggested_skip_rows'] > 0:
            analysis['confidence'] = 'high' if len(analysis['reasons']) > 2 else 'medium'
        
        return analysis 

    def analyze_emotion_usage(self, df: pd.DataFrame, emotion_column: str) -> dict:
        """
        Analyze emotion usage patterns in the data.
        
        Args:
            df: Input DataFrame
            emotion_column: Name of the emotion column
            
        Returns:
            Dictionary with emotion usage statistics
        """
        analysis = {
            'total_responses': 0,
            'single_emotions': 0,
            'multiple_emotions': 0,
            'empty_responses': 0,
            'emotion_frequency': {},
            'multiple_emotion_patterns': {},
            'max_emotions_per_response': 0
        }
        
        if emotion_column not in df.columns:
            return analysis
        
        for _, value in df[emotion_column].items():
            if pd.isna(value) or str(value).strip() == '':
                analysis['empty_responses'] += 1
                continue
            
            analysis['total_responses'] += 1
            emotion_str = str(value).strip()
            
            if ',' in emotion_str:
                # Multiple emotions
                analysis['multiple_emotions'] += 1
                emotion_codes = [code.strip() for code in emotion_str.split(',') if code.strip()]
                analysis['max_emotions_per_response'] = max(
                    analysis['max_emotions_per_response'], 
                    len(emotion_codes)
                )
                
                # Track multiple emotion patterns
                pattern = ', '.join(sorted(emotion_codes))
                analysis['multiple_emotion_patterns'][pattern] = analysis['multiple_emotion_patterns'].get(pattern, 0) + 1
                
                # Count individual emotions
                for code in emotion_codes:
                    analysis['emotion_frequency'][code] = analysis['emotion_frequency'].get(code, 0) + 1
            else:
                # Single emotion
                analysis['single_emotions'] += 1
                analysis['max_emotions_per_response'] = max(analysis['max_emotions_per_response'], 1)
                analysis['emotion_frequency'][emotion_str] = analysis['emotion_frequency'].get(emotion_str, 0) + 1 