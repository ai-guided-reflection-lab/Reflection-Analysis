import streamlit as st
import pandas as pd
import os
from pathlib import Path
from application.controller.utilities.id_column_fixer import IDColumnFixer

def run_id_fixer_ui():
    """
    Streamlit UI for fixing ID column issues in reflection files.
    """
    st.title("🔧 ID Column Fixer")
    st.markdown("""
    This tool helps fix ID column issues in reflection CSV files where students' ID choices 
    (email, 4-digit number, anonymous) are spread across multiple columns instead of being 
    consolidated into a single ID column.
    """)
    
    # Initialize the fixer
    fixer = IDColumnFixer()
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📁 Analyze File", "🔧 Fix Single File", "📂 Batch Fix Directory"])
    
    with tab1:
        st.header("Analyze ID Structure")
        st.markdown("Upload a CSV file to analyze its current ID column structure.")
        
        uploaded_file = st.file_uploader(
            "Upload CSV file for analysis", 
            type="csv",
            help="Upload a reflection CSV file to analyze its ID structure"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Show basic file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", len(df))
                with col2:
                    st.metric("Total Columns", len(df.columns))
                with col3:
                    st.metric("File Size", f"{uploaded_file.size} bytes")
                
                # Analyze ID structure
                analysis = fixer.analyze_id_structure(df)
                
                # Display analysis results
                st.subheader("📊 Analysis Results")
                
                if analysis['has_single_id_column']:
                    st.success("✅ File has a single ID column")
                    
                    # Show ID format breakdown
                    if analysis['id_formats_found']:
                        st.markdown("**ID Format Distribution:**")
                        format_df = pd.DataFrame(
                            list(analysis['id_formats_found'].items()),
                            columns=['Format', 'Count']
                        )
                        st.dataframe(format_df)
                        
                        # Sample IDs
                        if 'existing_id' in analysis['sample_data']:
                            st.markdown("**Sample IDs:**")
                            for i, sample_id in enumerate(analysis['sample_data']['existing_id']):
                                st.write(f"{i+1}. `{sample_id}`")
                else:
                    st.warning("⚠️ No single ID column found")
                
                # Show detected columns
                detected = analysis['detected_columns']
                st.subheader("🔍 Detected ID-Related Columns")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    choice_col = detected['choice']
                    if choice_col:
                        st.success(f"**Choice Column:** `{choice_col}`")
                        if 'choice' in analysis['sample_data']:
                            st.write("Sample values:")
                            for val in analysis['sample_data']['choice'][:3]:
                                st.write(f"• `{val}`")
                    else:
                        st.error("**Choice Column:** Not found")
                
                with col2:
                    email_col = detected['email']
                    if email_col:
                        st.success(f"**Email Column:** `{email_col}`")
                        if 'email' in analysis['sample_data']:
                            st.write("Sample values:")
                            for val in analysis['sample_data']['email'][:3]:
                                st.write(f"• `{val}`")
                    else:
                        st.error("**Email Column:** Not found")
                
                with col3:
                    id4_col = detected['id4']
                    if id4_col:
                        st.success(f"**4-Digit ID Column:** `{id4_col}`")
                        if 'id4' in analysis['sample_data']:
                            st.write("Sample values:")
                            for val in analysis['sample_data']['id4'][:3]:
                                st.write(f"• `{val}`")
                    else:
                        st.error("**4-Digit ID Column:** Not found")
                
                # Recommendations
                if analysis['needs_consolidation']:
                    st.subheader("💡 Recommendations")
                    st.warning("🔧 This file needs ID consolidation!")
                    st.info("This file has separate ID columns that should be consolidated into a single ID column based on student preferences.")
                    
                    # Show preview of what would happen
                    if st.button("🔍 Preview Consolidation", key="preview_consolidation"):
                        with st.spinner("Generating preview..."):
                            try:
                                preview_df = fixer.consolidate_id_columns(df)
                                
                                st.subheader("📋 Preview of Consolidated Data")
                                st.markdown("**First 10 rows after consolidation:**")
                                st.dataframe(preview_df.head(10))
                                
                                # Show ID format breakdown
                                id_formats = {}
                                for id_val in preview_df['ID']:
                                    id_str = str(id_val).strip()
                                    if '@' in id_str:
                                        id_formats['email'] = id_formats.get('email', 0) + 1
                                    elif id_str.isdigit() and len(id_str) == 4:
                                        id_formats['four_digit'] = id_formats.get('four_digit', 0) + 1
                                    elif id_str.startswith('ID-'):
                                        id_formats['generated'] = id_formats.get('generated', 0) + 1
                                    else:
                                        id_formats['other'] = id_formats.get('other', 0) + 1
                                
                                st.markdown("**Resulting ID Format Distribution:**")
                                format_df = pd.DataFrame(
                                    list(id_formats.items()),
                                    columns=['Format', 'Count']
                                )
                                st.dataframe(format_df)
                                
                            except Exception as e:
                                st.error(f"Error generating preview: {str(e)}")
                else:
                    st.success("✅ This file already has proper ID structure!")
                
            except Exception as e:
                st.error(f"Error analyzing file: {str(e)}")
    
    with tab2:
        st.header("Fix Single File")
        st.markdown("Fix ID columns in a single CSV file.")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload CSV file to fix", 
            type="csv",
            key="fix_single_file",
            help="Upload a reflection CSV file with ID column issues"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Auto-detect columns
                detected = fixer.detect_id_columns(df)
                
                st.subheader("🔧 Fix Configuration")
                
                col1, col2, col3 = st.columns(3)
                
                # Column selection with auto-detected defaults
                with col1:
                    choice_options = ['Auto-detect'] + list(df.columns)
                    choice_default = 0 if detected['choice'] is None else choice_options.index(detected['choice']) if detected['choice'] in choice_options else 0
                    
                    choice_col = st.selectbox(
                        "Choice Column",
                        choice_options,
                        index=choice_default,
                        help="Column indicating ID preference (1=email, 2=4-digit, 3=anonymous)"
                    )
                    if choice_col == 'Auto-detect':
                        choice_col = detected['choice']
                
                with col2:
                    email_options = ['Auto-detect'] + list(df.columns)
                    email_default = 0 if detected['email'] is None else email_options.index(detected['email']) if detected['email'] in email_options else 0
                    
                    email_col = st.selectbox(
                        "Email Column", 
                        email_options,
                        index=email_default,
                        help="Column containing email addresses"
                    )
                    if email_col == 'Auto-detect':
                        email_col = detected['email']
                
                with col3:
                    id4_options = ['Auto-detect'] + list(df.columns)
                    id4_default = 0 if detected['id4'] is None else id4_options.index(detected['id4']) if detected['id4'] in id4_options else 0
                    
                    id4_col = st.selectbox(
                        "4-Digit ID Column",
                        id4_options, 
                        index=id4_default,
                        help="Column containing 4-digit student IDs"
                    )
                    if id4_col == 'Auto-detect':
                        id4_col = detected['id4']
                
                # Show selected columns
                st.info(f"Selected columns: Choice=`{choice_col}`, Email=`{email_col}`, 4-Digit=`{id4_col}`")
                
                # Validate selection
                missing_cols = []
                for name, col in [("Choice", choice_col), ("Email", email_col), ("4-Digit", id4_col)]:
                    if not col or col not in df.columns:
                        missing_cols.append(name)
                
                if missing_cols:
                    st.error(f"Missing or invalid columns: {', '.join(missing_cols)}")
                else:
                    # Processing options
                    create_backup = st.checkbox("Create backup before processing", value=True)
                    
                    # Fix button
                    if st.button("🔧 Fix ID Columns", type="primary", key="fix_single"):
                        with st.spinner("Processing file..."):
                            try:
                                # Process the data
                                fixed_df = fixer.consolidate_id_columns(
                                    df, 
                                    choice_col=choice_col,
                                    email_col=email_col,
                                    id4_col=id4_col
                                )
                                
                                # Validate the results
                                validation = fixer.validate_id_consolidation(
                                    df, fixed_df, choice_col, email_col, id4_col
                                )
                                
                                st.success("✅ ID consolidation completed!")
                                
                                # Show validation results
                                st.subheader("📋 Validation Results")
                                if validation['is_valid']:
                                    st.success("✅ Validation passed!")
                                else:
                                    st.warning("⚠️ Validation issues found:")
                                    for issue in validation['issues']:
                                        st.write(f"• {issue}")
                                
                                # Show statistics
                                stats = validation['statistics']
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Rows", stats.get('total_rows', 0))
                                with col2:
                                    st.metric("Null IDs", stats.get('null_ids', 0))
                                with col3:
                                    st.metric("Format Mismatches", stats.get('format_mismatches', 0))
                                
                                # Show preview
                                st.subheader("📄 Fixed Data Preview")
                                st.dataframe(fixed_df.head(10))
                                
                                # Download option
                                csv_data = fixed_df.to_csv(index=False)
                                original_filename = uploaded_file.name.rsplit('.', 1)[0]
                                
                                st.download_button(
                                    label="📥 Download Fixed CSV",
                                    data=csv_data,
                                    file_name=f"{original_filename}_fixed.csv",
                                    mime="text/csv",
                                    help="Download the file with consolidated ID column"
                                )
                                
                            except Exception as e:
                                st.error(f"Error fixing file: {str(e)}")
                                st.exception(e)
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with tab3:
        st.header("Batch Fix Directory")
        st.markdown("Fix ID columns in all reflection CSV files within a directory.")
        
        # Directory path input
        directory_path = st.text_input(
            "Directory Path",
            value="application/model/reflections",
            help="Path to directory containing reflection CSV files"
        )
        
        # File pattern
        file_pattern = st.text_input(
            "File Pattern",
            value="*ref*.csv",
            help="Pattern to match CSV files (supports wildcards)"
        )
        
        # Processing options
        col1, col2 = st.columns(2)
        with col1:
            create_backups = st.checkbox("Create backups", value=True)
        
        with col2:
            dry_run = st.checkbox("Dry run (preview only)", value=True)
        
        # Scan directory button
        if st.button("🔍 Scan Directory", key="scan_directory"):
            if not os.path.exists(directory_path):
                st.error(f"Directory not found: {directory_path}")
            else:
                with st.spinner("Scanning directory..."):
                    try:
                        # Find matching files
                        directory = Path(directory_path)
                        csv_files = list(directory.rglob(file_pattern))
                        
                        st.info(f"Found {len(csv_files)} files matching pattern `{file_pattern}`")
                        
                        if csv_files:
                            # Analyze each file
                            analysis_results = []
                            for file_path in csv_files[:10]:  # Limit to first 10 for preview
                                try:
                                    df = pd.read_csv(file_path)
                                    analysis = fixer.analyze_id_structure(df)
                                    
                                    analysis_results.append({
                                        'file': str(file_path.name),
                                        'path': str(file_path),
                                        'rows': len(df),
                                        'has_id_column': analysis['has_single_id_column'],
                                        'needs_fix': analysis['needs_consolidation'],
                                        'choice_col': analysis['detected_columns']['choice'],
                                        'email_col': analysis['detected_columns']['email'],
                                        'id4_col': analysis['detected_columns']['id4']
                                    })
                                except Exception as e:
                                    analysis_results.append({
                                        'file': str(file_path.name),
                                        'path': str(file_path),
                                        'rows': 0,
                                        'has_id_column': False,
                                        'needs_fix': False,
                                        'error': str(e)
                                    })
                            
                            # Display results table
                            st.subheader("📊 File Analysis Results")
                            
                            # Convert to DataFrame for display
                            results_df = pd.DataFrame(analysis_results)
                            
                            # Style the dataframe
                            def style_analysis_results(val):
                                if val == True:
                                    return 'background-color: #90EE90'  # Light green
                                elif val == False:
                                    return 'background-color: #FFB6C1'  # Light red
                                return ''
                            
                            # Display with styling
                            styled_df = results_df.style.applymap(style_analysis_results, subset=['has_id_column', 'needs_fix'])
                            st.dataframe(styled_df)
                            
                            # Summary
                            needs_fixing = sum(1 for r in analysis_results if r.get('needs_fix', False))
                            st.info(f"Summary: {needs_fixing} files need ID consolidation out of {len(analysis_results)} analyzed")
                            
                            # Batch fix button
                            if not dry_run and needs_fixing > 0:
                                if st.button("🔧 Fix All Files", type="primary", key="batch_fix"):
                                    with st.spinner("Fixing files..."):
                                        results = fixer.scan_and_fix_directory(
                                            directory_path, 
                                            pattern=file_pattern,
                                            backup=create_backups
                                        )
                                        
                                        # Display results
                                        st.subheader("🎯 Batch Fix Results")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Fixed", len(results['fixed']))
                                        with col2:
                                            st.metric("Skipped", len(results['skipped']))
                                        with col3:
                                            st.metric("Failed", len(results['failed']))
                                        
                                        # Show details
                                        if results['fixed']:
                                            with st.expander("✅ Fixed Files"):
                                                for item in results['fixed']:
                                                    st.write(f"• {item}")
                                        
                                        if results['skipped']:
                                            with st.expander("⏭️ Skipped Files"):
                                                for item in results['skipped']:
                                                    st.write(f"• {item}")
                                        
                                        if results['failed']:
                                            with st.expander("❌ Failed Files"):
                                                for item in results['failed']:
                                                    st.write(f"• {item}")
                        else:
                            st.warning("No files found matching the pattern.")
                    
                    except Exception as e:
                        st.error(f"Error scanning directory: {str(e)}")
    
    # Help section
    with st.expander("ℹ️ Help & Documentation"):
        st.markdown("""
        ### How This Tool Works
        
        This tool fixes reflection CSV files where student ID preferences are stored in separate columns instead of a single consolidated ID column.
        
        ### Expected Column Structure
        
        **Before fixing:**
        - **Choice Column**: Contains student preference (1=email, 2=4-digit, 3=anonymous)
        - **Email Column**: Contains email addresses (for students who chose option 1)
        - **4-Digit Column**: Contains 4-digit IDs (for students who chose option 2)
        
        **After fixing:**
        - **ID Column**: Single column with appropriate ID based on student choice
        
        ### ID Format Types
        
        - 📧 **Email**: `student@charlotte.edu` (choice = 1)
        - 🔢 **4-Digit**: `1234` (choice = 2)  
        - 🏷️ **Generated**: `ID-15` (choice = 3 or fallback)
        
        ### Common Column Names
        
        The tool automatically detects columns with these patterns:
        - **Choice**: `Q9`, `id_choice`, `preference`
        - **Email**: `Q9_1_TEXT`, `email`, `email_address`
        - **4-Digit**: `Q9_2_TEXT`, `4_digit`, `four_digit`
        
        ### Tips
        
        1. Always create backups before fixing files
        2. Use "Analyze File" first to understand the current structure
        3. Preview consolidation results before applying changes
        4. Use batch processing for multiple files in a directory
        """)

if __name__ == "__main__":
    run_id_fixer_ui() 