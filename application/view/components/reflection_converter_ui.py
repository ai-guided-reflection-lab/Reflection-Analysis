import streamlit as st
import pandas as pd
from application.controller.utilities.reflection_converter import ReflectionConverter

def create_mapping_interface(mapping_type: str, default_mapping: dict) -> dict:
    """
    Create a dynamic interface for editing mappings.
    
    Args:
        mapping_type: Type of mapping (e.g., "Section", "Emotion")
        default_mapping: Default mapping values
        
    Returns:
        Dictionary with the configured mapping
    """
    st.markdown(f"**{mapping_type} Mapping Configuration:**")
    
    # Initialize mapping in session state if not exists
    session_key = f"{mapping_type.lower()}_mapping"
    if session_key not in st.session_state:
        st.session_state[session_key] = default_mapping.copy()
    
    mapping = st.session_state[session_key]
    
    # Create input fields for each mapping entry
    cols = st.columns([1, 2, 1])
    
    with cols[0]:
        st.markdown("**Code**")
    with cols[1]:
        st.markdown("**Description**")
    with cols[2]:
        st.markdown("**Action**")
    
    # Display existing mappings
    keys_to_remove = []
    for code, description in mapping.items():
        cols = st.columns([1, 2, 1])
        with cols[0]:
            st.text_input("Code", value=code, disabled=True, key=f"{session_key}_code_{code}")
        with cols[1]:
            new_desc = st.text_input("Description", value=description, key=f"{session_key}_desc_{code}")
            mapping[code] = new_desc
        with cols[2]:
            if st.button("🗑️", key=f"{session_key}_remove_{code}", help="Remove this mapping"):
                keys_to_remove.append(code)
    
    # Remove marked keys
    for key in keys_to_remove:
        del mapping[key]
        st.rerun()
    
    # Add new mapping interface - removed expander to avoid nesting
    st.markdown(f"**➕ Add New {mapping_type} Mapping:**")
    cols = st.columns([1, 2, 1])
    with cols[0]:
        new_code = st.text_input("New Code", key=f"{session_key}_new_code")
    with cols[1]:
        new_desc = st.text_input("New Description", key=f"{session_key}_new_desc")
    with cols[2]:
        if st.button("Add", key=f"{session_key}_add_button"):
            if new_code and new_desc:
                mapping[new_code] = new_desc
                # Clear the input fields by rerunning
                st.rerun()
            else:
                st.error("Please provide both code and description")
    
    return mapping

def run_reflection_converter_ui():
    """
    Streamlit UI for reflection data cleaning and conversion.
    """
    st.title("Reflection Data Cleaning")
    st.markdown("Convert raw survey exports into clean, analysis-ready reflection data.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload CSV file", 
        type="csv",
        help="Upload a CSV file exported from survey platforms (Qualtrics, etc.)"
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            # Show original data info
            st.subheader("📊 Original Data Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                st.metric("File Size", f"{uploaded_file.size} bytes")
            
            # Show original data preview
            with st.expander("View Original Data (First 5 rows)", expanded=False):
                st.dataframe(df.head())
            
            # Configuration section
            st.subheader("🔧 Cleaning Configuration")
            
            # Column pattern configuration
            col1, col2 = st.columns(2)
            with col1:
                column_pattern = st.text_input(
                    "Column Pattern (Regex)",
                    value=r'^Q\d+(?:_\d+_TEXT)?$',
                    help="Regex pattern to filter valid columns (e.g., Q1, Q2_1_TEXT)"
                )
            
            with col2:
                header_row_index = st.number_input(
                    "Header Row Index",
                    min_value=0,
                    max_value=min(5, len(df)-1),
                    value=0,
                    help="Row index to use as column headers (usually 0 or 1)"
                )
            
            # Metadata rows configuration
            st.markdown("**📋 Metadata Rows Configuration**")
            
            # Add intelligent analysis
            if st.button("🔍 Analyze Metadata Rows", help="Automatically analyze and suggest metadata rows to skip"):
                with st.spinner("Analyzing data structure..."):
                    temp_converter = ReflectionConverter()
                    analysis = temp_converter.analyze_metadata_rows(df, header_row_index)
                    
                    if analysis['suggested_skip_rows'] > 0:
                        st.success(f"✅ Analysis suggests skipping {analysis['suggested_skip_rows']} metadata rows")
                        st.info(f"Confidence: {analysis['confidence'].title()}")
                        if analysis['reasons']:
                            st.write("**Reasons:**")
                            for reason in set(analysis['reasons']):  # Remove duplicates
                                st.write(f"• {reason}")
                    else:
                        st.info("ℹ️ No obvious metadata rows detected")
            
            col1, col2 = st.columns(2)
            with col1:
                metadata_rows_to_skip = st.number_input(
                    "Metadata Rows to Skip",
                    min_value=0,
                    max_value=min(10, len(df)-1),
                    value=3,
                    help="Number of metadata rows to skip after the header row (default: 3)"
                )
            
            with col2:
                # Show preview of what will be skipped
                if header_row_index < len(df):
                    st.markdown("**Preview of rows to be skipped:**")
                    start_skip = header_row_index + 1
                    end_skip = min(start_skip + metadata_rows_to_skip, len(df))
                    if start_skip < len(df) and metadata_rows_to_skip > 0:
                        skip_preview = df.iloc[start_skip:end_skip]
                        st.dataframe(skip_preview, height=150)
                    else:
                        st.info("No metadata rows to skip")
            
            # Preview valid columns
            valid_columns = []
            try:
                # Create a temporary converter to test the pattern
                temp_converter = ReflectionConverter()
                valid_columns = temp_converter.filter_valid_columns(df, column_pattern)
                st.info(f"Found {len(valid_columns)} columns matching pattern: {', '.join(valid_columns[:10])}{' ...' if len(valid_columns) > 10 else ''}")
            except Exception as e:
                st.error(f"Invalid regex pattern: {str(e)}")
            
            if valid_columns:
                # Processing options
                st.subheader("🎛️ Processing Options")
                
                # Section and emotion mapping
                col1, col2, col3 = st.columns(3)
                with col1:
                    enable_section_mapping = st.checkbox("Enable Section Mapping", value=True)
                    section_column_index = st.number_input(
                        "Section Column Index",
                        min_value=0,
                        max_value=len(valid_columns)-1,
                        value=0,
                        disabled=not enable_section_mapping,
                        help="Index of column containing section codes (1, 2, etc.)"
                    ) if enable_section_mapping else None
                
                with col2:
                    enable_emotion_mapping = st.checkbox("Enable Emotion Mapping", value=True)
                    emotion_column_index = st.number_input(
                        "Emotion Column Index",
                        min_value=0,
                        max_value=len(valid_columns)-1,
                        value=1,
                        disabled=not enable_emotion_mapping,
                        help="Index of column containing emotion codes (1-5)"
                    ) if enable_emotion_mapping else None
                
                with col3:
                    enable_text_combine = st.checkbox("Combine with Text Column", value=True)
                    text_column_index = st.number_input(
                        "Text Column Index",
                        min_value=0,
                        max_value=len(valid_columns)-1,
                        value=2,
                        disabled=not enable_text_combine,
                        help="Index of text column to combine with emotions"
                    ) if enable_text_combine else None
                
                # Mapping configuration
                st.subheader("🗂️ Mapping Configuration")
                
                # Section mapping configuration
                section_mapping = {}
                if enable_section_mapping:
                    with st.expander("Configure Section Mapping", expanded=False):
                        default_section_mapping = {
                            '1': '081 Asychronous Online',
                            '2': '080 Synchronous Online'
                        }
                        section_mapping = create_mapping_interface("Section", default_section_mapping)
                
                # Emotion mapping configuration
                emotion_mapping = {}
                if enable_emotion_mapping:
                    with st.expander("Configure Emotion Mapping", expanded=False):
                        default_emotion_mapping = {
                            '1': 'Excited',
                            '2': 'Satisfied', 
                            '3': 'Frustrated',
                            '4': 'Confused',
                            '5': 'Neutral'
                        }
                        emotion_mapping = create_mapping_interface("Emotion", default_emotion_mapping)
                
                # ID column configuration
                st.subheader("🆔 ID Column Configuration")
                enable_id_processing = st.checkbox("Enable ID Processing", value=True)
                
                id_choice_col = None
                email_col = None
                id4_col = None
                
                if enable_id_processing:
                    st.markdown("Select columns for ID processing from **ALL** columns in your uploaded file:")
                    col1, col2, col3 = st.columns(3)
                    
                    # Set default values if available
                    id_choice_default = "Q9" if "Q9" in df.columns else df.columns[0]
                    email_default = "Q9_1_TEXT" if "Q9_1_TEXT" in df.columns else df.columns[0]
                    id4_default = "Q9_2_TEXT" if "Q9_2_TEXT" in df.columns else df.columns[0]
                    
                    with col1:
                        id_choice_col = st.selectbox(
                            "ID Choice Column",
                            df.columns,
                            index=list(df.columns).index(id_choice_default),
                            help="Column indicating ID preference (1=email, 2=4-digit ID, 3=anonymous)"
                        )
                    
                    with col2:
                        email_col = st.selectbox(
                            "Email Column",
                            df.columns,
                            index=list(df.columns).index(email_default),
                            help="Column containing email addresses"
                        )
                    
                    with col3:
                        id4_col = st.selectbox(
                            "4-Digit ID Column",
                            df.columns,
                            index=list(df.columns).index(id4_default),
                            help="Column containing 4-digit student IDs"
                        )
                
                # Process button
                if st.button("🔄 Clean Data", type="primary"):
                    with st.spinner("Processing data..."):
                        try:
                            # Initialize converter with custom mappings
                            converter = ReflectionConverter(
                                section_mapping=section_mapping if enable_section_mapping else None,
                                emotion_mapping=emotion_mapping if enable_emotion_mapping else None
                            )
                            
                            # Store original data for validation
                            original_df = df.copy()
                            
                            # Process the data
                            cleaned_df, removed_columns = converter.process_reflection_data(
                                df=df,
                                column_pattern=column_pattern,
                                header_row_index=header_row_index,
                                metadata_rows_to_skip=metadata_rows_to_skip,
                                section_column_index=section_column_index if enable_section_mapping else None,
                                emotion_column_index=emotion_column_index if enable_emotion_mapping else None,
                                text_column_index=text_column_index if enable_text_combine else None,
                                id_choice_col=id_choice_col if enable_id_processing else None,
                                email_col=email_col if enable_id_processing else None,
                                id4_col=id4_col if enable_id_processing else None
                            )
                            
                            # Validate ID consolidation if enabled
                            if enable_id_processing and all([id_choice_col, email_col, id4_col]):
                                st.subheader("🔍 ID Consolidation Validation")
                                
                                # Create a simple validation by checking the original data directly
                                # Get the data after header application but before ID processing
                                valid_columns = converter.filter_valid_columns(df, column_pattern)
                                pre_id_df = converter.apply_new_headers(df, valid_columns, header_row_index, metadata_rows_to_skip)
                                
                                # Add the original ID columns to this DataFrame
                                for col in [id_choice_col, email_col, id4_col]:
                                    if col in df.columns:
                                        # Get the data starting from the row after headers and metadata rows
                                        start_row = header_row_index + 1 + metadata_rows_to_skip
                                        col_data = df[col].iloc[start_row:].reset_index(drop=True)
                                        # Only take as many rows as we have in the processed data
                                        if len(col_data) >= len(pre_id_df):
                                            pre_id_df[col] = col_data.iloc[:len(pre_id_df)]
                                        else:
                                            pre_id_df[col] = col_data
                                
                                validation = converter.validate_id_consolidation(
                                    pre_id_df, cleaned_df, id_choice_col, email_col, id4_col
                                )
                                
                                if validation['is_valid']:
                                    st.success("✅ ID consolidation validation passed!")
                                else:
                                    st.warning("⚠️ ID consolidation validation issues:")
                                    for issue in validation['issues']:
                                        st.write(f"• {issue}")
                                
                                # Show validation statistics
                                stats = validation['statistics']
                                if stats:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Rows", stats.get('total_rows', 0))
                                    with col2:
                                        st.metric("Null IDs", stats.get('null_ids', 0))
                                    with col3:
                                        st.metric("Format Mismatches", stats.get('format_mismatches', 0))
                                
                                # Show sample mismatches if any
                                if validation['sample_mismatches']:
                                    with st.expander("🔍 Sample ID Mismatches"):
                                        for mismatch in validation['sample_mismatches']:
                                            st.write(f"Row {mismatch['row']}: Choice='{mismatch['choice']}' → Expected={mismatch['expected']}, Got={mismatch['actual']} (ID: '{mismatch['id']}')")
                            
                            # Store in session state
                            st.session_state.cleaned_df = cleaned_df
                            st.session_state.removed_columns = removed_columns
                            st.session_state.original_filename = uploaded_file.name
                            st.session_state.converter = converter  # Store converter for filtering
                            
                            st.success("✅ Data cleaning completed!")
                            
                        except Exception as e:
                            st.error(f"❌ Error processing data: {str(e)}")
                            st.exception(e)
                
                # Display results if available
                if 'cleaned_df' in st.session_state:
                    cleaned_df = st.session_state.cleaned_df
                    removed_columns = st.session_state.removed_columns
                    converter = st.session_state.get('converter', ReflectionConverter())
                    
                    # Results summary
                    st.subheader("✨ Cleaning Results")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Cleaned Rows", len(cleaned_df))
                    with col2:
                        st.metric("Cleaned Columns", len(cleaned_df.columns))
                    with col3:
                        st.metric("Removed Columns", len(removed_columns))
                    with col4:
                        st.metric("Metadata Rows Skipped", metadata_rows_to_skip)
                    
                    # Show metadata row removal info
                    if metadata_rows_to_skip > 0:
                        st.info(f"ℹ️ Skipped {metadata_rows_to_skip} metadata rows after the header row (row {header_row_index})")
                    
                    # Show emotion analysis if emotion mapping was enabled
                    if enable_emotion_mapping and emotion_column_index is not None:
                        with st.expander("📊 Emotion Usage Analysis", expanded=False):
                            try:
                                # Analyze emotion usage in the original data before mapping
                                original_valid_columns = temp_converter.filter_valid_columns(df, column_pattern)
                                if emotion_column_index < len(original_valid_columns):
                                    # Get the emotion column from the original data after header application
                                    emotion_analysis_df = temp_converter.apply_new_headers(df, original_valid_columns, header_row_index, metadata_rows_to_skip)
                                    
                                    # Validate that the emotion column index is valid
                                    if emotion_column_index < len(emotion_analysis_df.columns):
                                        emotion_col_name = emotion_analysis_df.columns[emotion_column_index]
                                        
                                        emotion_stats = converter.analyze_emotion_usage(emotion_analysis_df, emotion_col_name)
                                        
                                        # Validate that emotion_stats is not None and has required keys
                                        if emotion_stats and isinstance(emotion_stats, dict):
                                            # Display statistics
                                            col1, col2, col3, col4 = st.columns(4)
                                            with col1:
                                                st.metric("Total Responses", emotion_stats.get('total_responses', 0))
                                            with col2:
                                                st.metric("Single Emotions", emotion_stats.get('single_emotions', 0))
                                            with col3:
                                                st.metric("Multiple Emotions", emotion_stats.get('multiple_emotions', 0))
                                            with col4:
                                                st.metric("Empty Responses", emotion_stats.get('empty_responses', 0))
                                            
                                            # Show emotion frequency
                                            if emotion_stats.get('emotion_frequency'):
                                                st.markdown("**Emotion Code Frequency:**")
                                                freq_cols = st.columns(min(5, len(emotion_stats['emotion_frequency'])))
                                                for i, (code, count) in enumerate(emotion_stats['emotion_frequency'].items()):
                                                    with freq_cols[i % len(freq_cols)]:
                                                        mapped_emotion = converter.emotion_mapping.get(code, code)
                                                        st.metric(f"Code {code}", count, help=f"Mapped to: {mapped_emotion}")
                                            
                                            # Show multiple emotion patterns if any
                                            if emotion_stats.get('multiple_emotion_patterns'):
                                                st.markdown("**Common Multiple Emotion Patterns:**")
                                                for pattern, count in sorted(emotion_stats['multiple_emotion_patterns'].items(), key=lambda x: x[1], reverse=True)[:5]:
                                                    st.write(f"• `{pattern}` - {count} responses")
                                            
                                            # Show insights
                                            total_with_emotions = emotion_stats.get('total_responses', 0)
                                            if total_with_emotions > 0:
                                                multiple_pct = (emotion_stats.get('multiple_emotions', 0) / total_with_emotions) * 100
                                                st.info(f"💡 **Insight:** {multiple_pct:.1f}% of responses contain multiple emotions, indicating complex emotional states.")
                                        else:
                                            st.error("❌ Failed to analyze emotion usage - invalid analysis result")
                                    else:
                                        st.error(f"❌ Emotion column index {emotion_column_index} is out of range. Available columns: {len(emotion_analysis_df.columns)}")
                                else:
                                    st.error(f"❌ Emotion column index {emotion_column_index} is out of range. Available valid columns: {len(original_valid_columns)}")
                            except Exception as e:
                                st.error(f"❌ Error analyzing emotion usage: {str(e)}")
                                st.write("**Debug Info:**")
                                st.write(f"- Enable emotion mapping: {enable_emotion_mapping}")
                                st.write(f"- Emotion column index: {emotion_column_index}")
                                st.write(f"- Valid columns count: {len(original_valid_columns) if 'original_valid_columns' in locals() else 'N/A'}")
                                if 'emotion_analysis_df' in locals():
                                    st.write(f"- Analysis DataFrame columns: {list(emotion_analysis_df.columns)}")
                    
                    # Show removed columns
                    if removed_columns:
                        with st.expander("Removed Columns", expanded=False):
                            st.write(", ".join(removed_columns))
                    
                    # Section filter
                    st.subheader("🔍 Filter by Section")
                    if enable_section_mapping and section_column_index is not None:
                        # Calculate the actual section column index after ID processing
                        actual_section_index = section_column_index
                        if enable_id_processing and all([id_choice_col, email_col, id4_col]):
                            # ID column is added at position 0, so all other columns shift right by 1
                            actual_section_index = section_column_index + 1
                        
                        section_options = converter.get_section_options(cleaned_df, actual_section_index)
                        selected_section = st.selectbox("Select Section:", section_options)
                        
                        # Apply filter
                        if selected_section != 'All Sections':
                            section_col = cleaned_df.columns[actual_section_index]
                            filtered_df = converter.filter_by_section(cleaned_df, section_col, selected_section)
                        else:
                            filtered_df = cleaned_df
                    else:
                        selected_section = 'All Sections'
                        filtered_df = cleaned_df
                    
                    # Display cleaned data
                    st.subheader("📋 Cleaned Data Preview")
                    st.dataframe(filtered_df.head(10))
                    
                    # Download options
                    st.subheader("💾 Download Options")
                    
                    # Get original filename without extension
                    original_filename = st.session_state.original_filename.rsplit('.', 1)[0]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Download all data
                        csv_all = cleaned_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download All Cleaned Data",
                            data=csv_all,
                            file_name=f"cleaned_{original_filename}.csv",
                            mime="text/csv",
                            help="Download the complete cleaned dataset"
                        )
                    
                    with col2:
                        # Download filtered data
                        if selected_section != 'All Sections':
                            csv_filtered = filtered_df.to_csv(index=False)
                            section_safe = selected_section.split()[0]  # Get first word for filename
                            st.download_button(
                                label=f"📥 Download {selected_section.split()[0]} Data",
                                data=csv_filtered,
                                file_name=f"cleaned_{original_filename}_{section_safe}.csv",
                                mime="text/csv",
                                help=f"Download data filtered for {selected_section}"
                            )
                    
                    # Cleaning summary
                    with st.expander("📊 Detailed Cleaning Summary", expanded=False):
                        st.markdown(f"""
                        **Processing Summary:**
                        - **Original columns:** {len(df.columns)}
                        - **Valid columns found:** {len(valid_columns)}
                        - **Final columns:** {len(cleaned_df.columns)}
                        - **Rows processed:** {len(df)} → {len(cleaned_df)}
                        
                        **Applied Transformations:**
                        - Column filtering: {'✅' if valid_columns else '❌'}
                        - Header application: ✅
                        - Section mapping: {'✅' if enable_section_mapping else '❌'}
                        - Emotion mapping: {'✅' if enable_emotion_mapping else '❌'}
                        - ID processing: {'✅' if enable_id_processing else '❌'}
                        """)
                        
                        if removed_columns:
                            st.markdown("**Removed columns:**")
                            st.write(removed_columns)
                            
                        # Show applied mappings
                        if enable_section_mapping and section_mapping:
                            st.markdown("**Section Mapping:**")
                            for code, desc in section_mapping.items():
                                st.write(f"- `{code}` → {desc}")
                        
                        if enable_emotion_mapping and emotion_mapping:
                            st.markdown("**Emotion Mapping:**")
                            for code, desc in emotion_mapping.items():
                                st.write(f"- `{code}` → {desc}")
            
            else:
                st.warning("⚠️ No columns found matching the specified pattern. Please adjust the column pattern.")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.exception(e)
    
    else:
        # Usage instructions when no file is uploaded
        st.info("👆 Please upload a CSV file to begin cleaning")
        
        with st.expander("📚 Usage Instructions", expanded=True):
            st.markdown("""
            ### How to Use the Reflection Data Cleaner
            
            1. **Upload CSV File**: Upload your survey export (Qualtrics, etc.)
            2. **Configure Pattern**: Adjust the regex pattern to match your column naming
            3. **Set Processing Options**: Enable/disable specific cleaning features
            4. **Configure Mappings**: Customize section and emotion mappings for your course
            5. **Configure ID Columns**: Select columns for ID processing
            6. **Clean Data**: Click the "Clean Data" button to process
            7. **Filter & Download**: Filter by section and download the results
            
            #### 🔧 Configuration Options:
            
            **Column Pattern**: Regex to identify valid survey columns
            - Default: `^Q\d+(?:_\d+_TEXT)?$` (matches Q1, Q2_1_TEXT, etc.)
            
            **Section Mapping**: Configurable mapping of numeric codes to section names
            - Customize based on your course sections
            - Add/remove mappings as needed
            
            **Emotion Mapping**: Configurable mapping of emotion codes to readable text
            - Default: `1` → `Excited`, `2` → `Satisfied`, etc.
            - Modify to match your survey's emotion scale
            - **NEW**: Supports multiple emotions (e.g., `2,3` → `Satisfied, Frustrated`)
            - Handles comma-separated values automatically
            
            **ID Processing**: Creates unified ID column based on student preference
            - Choice `1` = Use email address
            - Choice `2` = Use 4-digit ID  
            - Choice `3` = Anonymous (auto-generated ID)
            - Default columns: Q9, Q9_1_TEXT, Q9_2_TEXT
            
            #### 📁 Output Format:
            The cleaned CSV will have:
            - Filtered columns matching your pattern
            - Proper headers from the specified row
            - Mapped section and emotion values (using your custom mappings)
            - Unified ID column (if enabled)
            - Clean, analysis-ready format
            """)

if __name__ == "__main__":
    run_reflection_converter_ui()