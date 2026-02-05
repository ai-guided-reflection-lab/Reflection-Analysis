import os
import streamlit as st
from typing import Optional, Tuple
import pandas as pd
from application.model.services.file_system import FileSystemService
from application.model.services.data_processing import DataProcessingService
from application.model.services.state_management import StateManager
from application.model.models.course import Course
from application.model.models.student import Student
from application.model.models.reflection import Reflection
from application.html_builder.builder import HTMLBuilder
import base64
from pathlib import Path
from application.controller.utilities.file_validator import FileValidator, validate_reflection_files

class ReflectionView:
    """Handle reflection-related UI components"""
    def __init__(self, fs_service: FileSystemService, 
                 data_processor: DataProcessingService,
                 state_manager: StateManager):
        self.fs_service = fs_service
        self.data_processor = data_processor
        self.state_manager = state_manager
        self.file_validator = FileValidator()  # Add file validator
        
    def show_reflection_selection(self, course_name: str) -> None:
        """Display reflection selection UI"""
        reflection_action = st.radio(
            "Choose action:",
            ["Select Existing Reflection", "Import Reflection from CSV"],
            key="workflow_reflection_action"
        )
        
        if reflection_action == "Import Reflection from CSV":
            self.handle_reflection_import(course_name)
        else:
            self.handle_existing_reflection(course_name)
            
    def handle_existing_reflection(self, course_name: str) -> None:
        """Handle existing reflection selection"""
        course_path = os.path.join(self.fs_service.base_path, course_name)
        reflections = self.fs_service.get_reflection_folders(course_path)
        
        if reflections:
            selected_folder = st.selectbox(
                "Select reflection:",
                reflections,
                key="workflow_reflection_select"
            )
            
            if selected_folder:
                folder_path = os.path.join(course_path, selected_folder)
                files = self.fs_service.get_reflection_files(folder_path, course_name)
                
                self.state_manager.set_reflection(selected_folder, files)
                
                self.show_reflection_files(files)
                
                # Add mode selection BEFORE the Load Reflection Data button
                # Report mode is now always instructor mode (simplified)
                report_mode = "instructor"

                # Determine whether topic analysis has been run for the selected reflection
                results_dir = os.path.join(folder_path, "results")
                analysis_files = []
                if os.path.exists(results_dir):
                    try:
                        analysis_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]
                    except Exception:
                        analysis_files = []

                # Heuristic: presence of any results CSV implies analysis ran
                has_topic_analysis = len(analysis_files) > 0

                if not has_topic_analysis:
                    st.info("ℹ️ No topic analysis results detected for this reflection. Please open the Analysis tab and run Topic Analysis first, then return here to generate the report.")
                else:
                    st.success("✅ Topic analysis results found. You can generate the instructor report below.")
                
                # Add anonymization option
                anonymized = st.checkbox(
                    "🔒 Anonymize Report",
                    value=False,
                    help="Anonymize student names, emails, and sections for privacy. Useful for sharing reports or research purposes.",
                    key="reflection_view_anonymized"
                )
                
                if st.button("Load Reflection Data", disabled=not has_topic_analysis):
                    self.show_reflection_data(course_name, report_mode, anonymized)
        else:
            st.warning("No existing reflections found.")
            
    def show_reflection_files(self, files: dict) -> None:
        """Display available reflection files"""
        st.write("Available files:")
        if 'reflection' in files:
            st.write(f"- Reflection file: {files['reflection']}")
        if 'grades' in files:
            st.write(f"- Grades file: {files['grades']}")
            
    def show_reflection_data(self, course_name: str, report_mode: str, anonymized: bool) -> None:
        """Display reflection data and objects"""
        try:
            # 1. First scan all reflection folders for this course
            course_path = os.path.join(self.fs_service.base_path, course_name)
            reflection_folders = self.fs_service.get_reflection_folders(course_path)
            
            if not reflection_folders:
                st.error("No reflection folders found")
                return
            
            # 2. Create course and build complete student objects
            course = Course(course_name)
            
            # Process all reflection folders
            for folder in reflection_folders:
                ref_num = int(folder.replace('ref', ''))
                course.add_reflection_number(ref_num)
                
                folder_path = os.path.join(course_path, folder)
                files = self.fs_service.get_reflection_files(folder_path, course_name)
                
                if 'grades' in files:
                    grades_path = os.path.join(folder_path, files['grades'])
                    grades_data = pd.read_csv(grades_path)
                    
                    # Create/update students from grades
                    for _, grade_row in grades_data.iloc[2:].iterrows():
                        sis_id = grade_row.get('SIS Login ID')
                        if sis_id and pd.notna(sis_id):
                            email = f"{sis_id}@charlotte.edu"
                            student = course.get_student_by_email(email)
                            if not student:
                                student = Student(
                                    name=grade_row.get('Student', 'Unknown'),
                                    email=email,
                                    course=course_name
                                )
                                course.add_student(student)
                            student.add_reflection_data(
                                ref_num=ref_num,
                                grades=grade_row.to_dict()
                            )
                
                if 'reflection' in files:
                    reflection_path = os.path.join(folder_path, files['reflection'])
                    reflection_data = pd.read_csv(reflection_path)
                    
                    for _, ref_row in reflection_data.iterrows():
                        email = ref_row.get('ID', '')
                        if '@' in email:
                            student = course.get_student_by_email(email)
                            if student:
                                ref_row_dict = ref_row.to_dict()
                                ref_row_dict['reflection_number'] = ref_num
                                reflection = Reflection(ref_row_dict)
                                student.add_reflection_data(
                                    ref_num=ref_num,
                                    reflection=reflection
                                )

            # Add download button for HTML report
            if course.students:
                st.write("### Download Student Profiles")
                
                builder = HTMLBuilder()
                html_content = builder.build_student_profiles(course, mode=report_mode, anonymized=anonymized)
                
                # Create filename for instructor report
                anonymized_suffix = "_anonymized" if anonymized else ""
                filename = f"student_profiles_instructor{anonymized_suffix}.html"
                
                # Create download button
                b64 = base64.b64encode(html_content.encode()).decode()
                anonymized_text = " (Anonymized)" if anonymized else ""
                href = f'<a href="data:text/html;base64,{b64}" download="{filename}" class="button">Download Instructor Report{anonymized_text}</a>'
                st.markdown(href, unsafe_allow_html=True)
                
                # Add debugging information
                st.write("### 🔍 Debugging Information")
                st.write("This section shows all email IDs from reflection files and SIS Login IDs from grade files to help debug matching issues.")
                
                self._show_matching_debug_info(course_path, reflection_folders, course_name)

        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            
    def _show_matching_debug_info(self, course_path: str, reflection_folders: list, course_name: str) -> None:
        """Display debugging information for email ID and SIS Login ID matching"""
        try:
            # Find the most recent reflection folder
            if not reflection_folders:
                st.warning("No reflection folders found for debugging.")
                return
                
            # Sort folders by reflection number to get the most recent
            sorted_folders = sorted(reflection_folders, key=lambda x: int(x.replace('ref', '')))
            most_recent_folder = sorted_folders[-1]
            most_recent_ref_num = int(most_recent_folder.replace('ref', ''))
            
            st.write(f"**Debugging data for most recent reflection: {most_recent_folder}**")
            
            # Get files for the most recent reflection
            folder_path = os.path.join(course_path, most_recent_folder)
            files = self.fs_service.get_reflection_files(folder_path, course_name)
            
            # Collect email IDs from reflection file
            email_ids = []
            if 'reflection' in files:
                reflection_path = os.path.join(folder_path, files['reflection'])
                if os.path.exists(reflection_path):
                    reflection_df = pd.read_csv(reflection_path)
                    if 'ID' in reflection_df.columns:
                        for _, row in reflection_df.iterrows():
                            student_id = row.get('ID', '')
                            if pd.notna(student_id) and '@' in str(student_id):
                                email_ids.append(str(student_id).strip())
            
            # Collect SIS Login IDs from grade file
            sis_login_ids = []
            sis_students_with_grades = {}  # Track which have valid grades
            if 'grades' in files:
                grades_path = os.path.join(folder_path, files['grades'])
                if os.path.exists(grades_path):
                    grades_df = pd.read_csv(grades_path)
                    if 'SIS Login ID' in grades_df.columns:
                        for _, row in grades_df.iterrows():
                            sis_id = row.get('SIS Login ID', '')
                            current_score = row.get('Current Score', '')
                            if pd.notna(sis_id) and str(sis_id).strip():
                                sis_login = str(sis_id).strip()
                                sis_login_ids.append(sis_login)
                                
                                # Check if they have a valid grade
                                has_valid_grade = False
                                if pd.notna(current_score) and str(current_score).strip() not in ['-', '', 'N/A', 'n/a', '(read only)']:
                                    try:
                                        float(current_score)
                                        has_valid_grade = True
                                    except (ValueError, TypeError):
                                        pass
                                sis_students_with_grades[sis_login] = {
                                    'grade': current_score,
                                    'has_valid_grade': has_valid_grade
                                }
            
            # Remove duplicates and sort
            email_ids = sorted(list(set(email_ids)))
            sis_login_ids = sorted(list(set(sis_login_ids)))
            
            # Create DataFrames for display
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### Email IDs from Reflection File")
                if email_ids:
                    # Create matching status for each email
                    email_data = []
                    for email in email_ids:
                        username = email.split('@')[0].lower()
                        has_match = username in [sis.lower() for sis in sis_login_ids]
                        
                        # Find the matching SIS Login ID and check if they have valid grades
                        matched_sis = None
                        has_valid_grade = False
                        for sis in sis_login_ids:
                            if sis.lower() == username:
                                matched_sis = sis
                                has_valid_grade = sis_students_with_grades.get(sis, {}).get('has_valid_grade', False)
                                break
                        
                        email_data.append({
                            'Email ID': email,
                            'Username': username,
                            'Has SIS Match': '✅' if has_match else '❌',
                            'Matched SIS ID': matched_sis if has_match else '',
                            'Has Valid Grade': '✅' if has_valid_grade else '❌'
                        })
                    
                    email_df = pd.DataFrame(email_data)
                    st.dataframe(email_df, use_container_width=True)
                    
                    # Summary stats
                    total_emails = len(email_ids)
                    matched_emails = len([e for e in email_data if e['Has SIS Match'] == '✅'])
                    with_valid_grades = len([e for e in email_data if e['Has Valid Grade'] == '✅'])
                    
                    st.write(f"**Summary:**")
                    st.write(f"- Total email IDs: {total_emails}")
                    st.write(f"- With SIS matches: {matched_emails} ({matched_emails/total_emails*100:.1f}%)")
                    st.write(f"- With valid grades: {with_valid_grades} ({with_valid_grades/total_emails*100:.1f}%)")
                else:
                    st.write("No email IDs found in reflection file.")
            
            with col2:
                st.write("#### SIS Login IDs from Grade File")
                if sis_login_ids:
                    # Create matching status for each SIS Login ID
                    sis_data = []
                    for sis_id in sis_login_ids:
                        has_reflection_match = any(email.split('@')[0].lower() == sis_id.lower() for email in email_ids)
                        grade_info = sis_students_with_grades.get(sis_id, {})
                        
                        sis_data.append({
                            'SIS Login ID': sis_id,
                            'Has Reflection Match': '✅' if has_reflection_match else '❌',
                            'Current Score': grade_info.get('grade', ''),
                            'Has Valid Grade': '✅' if grade_info.get('has_valid_grade', False) else '❌'
                        })
                    
                    sis_df = pd.DataFrame(sis_data)
                    st.dataframe(sis_df, use_container_width=True)
                    
                    # Summary stats
                    total_sis = len(sis_login_ids)
                    matched_sis = len([s for s in sis_data if s['Has Reflection Match'] == '✅'])
                    valid_grades_sis = len([s for s in sis_data if s['Has Valid Grade'] == '✅'])
                    
                    st.write(f"**Summary:**")
                    st.write(f"- Total SIS Login IDs: {total_sis}")
                    st.write(f"- With reflection matches: {matched_sis} ({matched_sis/total_sis*100:.1f}%)")
                    st.write(f"- With valid grades: {valid_grades_sis} ({valid_grades_sis/total_sis*100:.1f}%)")
                else:
                    st.write("No SIS Login IDs found in grade file.")
            
            # Overall matching summary
            if email_ids and sis_login_ids:
                st.write("#### 🎯 Overall Matching Summary")
                
                # Calculate final matching count (students who submitted reflection AND have valid grades)
                final_matches = 0
                for email in email_ids:
                    username = email.split('@')[0].lower()
                    for sis in sis_login_ids:
                        if sis.lower() == username:
                            if sis_students_with_grades.get(sis, {}).get('has_valid_grade', False):
                                final_matches += 1
                            break
                
                st.write(f"**Students with BOTH recent reflection AND valid grade data: {final_matches}**")
                st.write("This is the number that should appear as 'Students with Recent Data' in the HTML report.")
                
        except Exception as e:
            st.error(f"Error displaying debug information: {str(e)}")

    def handle_reflection_import(self, course_name: str) -> None:
        """Handle reflection import from CSV"""
        st.write("Upload Reflection Files:")
        
        reflection_file = st.file_uploader("Choose reflection CSV file", type='csv', key="reflection_csv")
        grades_file = st.file_uploader("Choose grades CSV file", type='csv', key="grades_csv")
        
        if reflection_file or grades_file:
            if st.button("Import Files"):
                try:
                    course_path = os.path.join(self.fs_service.base_path, course_name)
                    existing_refs = self.fs_service.get_reflection_folders(course_path)
                    next_ref_num = len(existing_refs) + 1
                    
                    folder_name = f"ref{next_ref_num}"
                    folder_path = os.path.join(course_path, folder_name)
                    self.fs_service.ensure_directory(folder_path)
                    
                    if reflection_file:
                        new_name = f"{course_name}_ref{next_ref_num}.csv"
                        self.fs_service.save_csv_file(
                            os.path.join(folder_path, new_name),
                            reflection_file.getvalue()
                        )
                        
                    if grades_file:
                        new_name = f"{course_name}_grades_ref{next_ref_num}.csv"
                        self.fs_service.save_csv_file(
                            os.path.join(folder_path, new_name),
                            grades_file.getvalue()
                        )
                        
                    st.success(f"Created new reflection folder: {folder_name}")
                    
                except Exception as e:
                    st.error(f"Error importing files: {str(e)}") 

    def display_reflection_management(self):
        st.title("Reflection Management")
        
        # Course selection
        course_names = self.fs_service.get_courses()
        if not course_names:
            st.warning("No courses found. Please create a course first.")
            return
        
        selected_course = st.selectbox("Select Course:", course_names)
        
        if not selected_course:
            return
        
        # Action selection
        action = st.radio(
            "Choose action:",
            ["Select Existing Reflection", "Import Reflection from CSV"]
        )
        
        if action == "Select Existing Reflection":
            self._display_existing_reflections(selected_course)
        else:
            self._display_import_interface(selected_course)
    
    def _display_existing_reflections(self, course_name):
        reflections = self.fs_service.get_reflections(course_name)
        
        if not reflections:
            st.info("No reflections found for this course.")
            return
        
        selected_reflection = st.selectbox("Select reflection:", reflections)
        
        if selected_reflection:
            st.session_state['current_course_folder'] = course_name
            st.session_state['current_reflection_folder'] = selected_reflection
            
            # File validation section
            st.subheader("📋 File Validation")
            
            # Run validation
            with st.spinner("Validating files..."):
                validation_report = validate_reflection_files(course_name, selected_reflection)
            
            # Display validation results in an expandable section
            with st.expander("🔍 View Validation Report", expanded=False):
                st.text(validation_report)
            
            # Check if files are valid for processing
            validator = FileValidator()
            directory_path = os.path.join("application", "model", "reflections", course_name, selected_reflection)
            results = validator.validate_reflection_directory(directory_path)
            
            all_valid = all(result.is_valid for result in results.values())
            critical_issues = any("CRITICAL" in issue for result in results.values() for issue in result.issues)
            
            if critical_issues:
                st.error("🔥 Critical file issues detected! Please fix before proceeding with analysis.")
                st.warning("Common fixes:")
                st.write("• Check if reflection and grades files are swapped")
                st.write("• Ensure files contain the correct data types")
                st.write("• Verify CSV files are not corrupted")
            elif not all_valid:
                st.warning("⚠️ Some file issues detected. Review the validation report above.")
            else:
                st.success("✅ All files are valid and ready for analysis!")
            
            # Display file information
            self._display_reflection_info(course_name, selected_reflection)
    
    def _display_import_interface(self, course_name):
        st.subheader("Import Reflection from CSV")
        
        # Reflection number input
        reflection_num = st.number_input(
            "Reflection number:",
            min_value=1,
            value=1,
            step=1
        )
        
        reflection_folder = f"ref{reflection_num}"
        
        # File upload section
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Reflection Data (CSV)**")
            reflection_file = st.file_uploader(
                "Upload reflection responses:",
                type=['csv'],
                key="reflection_upload"
            )
            
        with col2:
            st.write("**Grades Data (CSV)**")
            grades_file = st.file_uploader(
                "Upload grades data:",
                type=['csv'],
                key="grades_upload"
            )
        
        # Validate uploaded files before saving
        if reflection_file and grades_file:
            st.subheader("📋 File Validation")
            
            # Read uploaded files for validation
            try:
                reflection_df = pd.read_csv(reflection_file)
                grades_df = pd.read_csv(grades_file)
                
                # Validate reflection file
                reflection_temp_path = f"temp_reflection_{reflection_num}.csv"
                reflection_df.to_csv(reflection_temp_path, index=False)
                reflection_result = self.file_validator.validate_file(
                    reflection_temp_path, 
                    self.file_validator.FileType.REFLECTION
                )
                
                # Validate grades file  
                grades_temp_path = f"temp_grades_{reflection_num}.csv"
                grades_df.to_csv(grades_temp_path, index=False)
                grades_result = self.file_validator.validate_file(
                    grades_temp_path,
                    self.file_validator.FileType.GRADES
                )
                
                # Clean up temp files
                for temp_file in [reflection_temp_path, grades_temp_path]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
                # Display validation results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Reflection File Validation:**")
                    if reflection_result.is_valid:
                        st.success("✅ Valid reflection data")
                    else:
                        st.error("❌ Invalid reflection data")
                        for issue in reflection_result.issues:
                            st.write(f"• {issue}")
                
                with col2:
                    st.write("**Grades File Validation:**")
                    if grades_result.is_valid:
                        st.success("✅ Valid grades data")  
                    else:
                        st.error("❌ Invalid grades data")
                        for issue in grades_result.issues:
                            st.write(f"• {issue}")
                
                # Check for file swapping
                if (reflection_result.actual_type == self.file_validator.FileType.GRADES and 
                    grades_result.actual_type == self.file_validator.FileType.REFLECTION):
                    st.error("🔄 **Files appear to be SWAPPED!**")
                    st.warning("The reflection file contains grades data and the grades file contains reflection data.")
                    st.info("💡 **Solution:** Switch the files in the upload boxes above.")
                
                # Only show save button if files are valid
                both_valid = reflection_result.is_valid and grades_result.is_valid
                has_critical = any("CRITICAL" in issue for issue in reflection_result.issues + grades_result.issues)
                
                if both_valid and not has_critical:
                    if st.button("💾 Save Files", type="primary"):
                        self._save_reflection_files(
                            course_name, 
                            reflection_folder, 
                            reflection_df, 
                            grades_df
                        )
                        st.success(f"✅ Reflection {reflection_num} imported successfully!")
                        st.session_state['current_course_folder'] = course_name
                        st.session_state['current_reflection_folder'] = reflection_folder
                        st.rerun()
                else:
                    st.error("🔥 Cannot save files due to validation issues. Please fix the problems above.")
                
            except Exception as e:
                st.error(f"Error validating files: {str(e)}")
    
    def _save_reflection_files(self, course_name, reflection_folder, reflection_df, grades_df):
        """Save reflection and grades files to the appropriate directory"""
        # Create directory
        reflection_path = os.path.join(
            "application", "model", "reflections", 
            course_name, reflection_folder
        )
        os.makedirs(reflection_path, exist_ok=True)
        
        # Save files with correct naming convention
        reflection_filename = f"{course_name}_{reflection_folder}.csv"
        grades_filename = f"{course_name}_grades_{reflection_folder}.csv"
        
        reflection_df.to_csv(
            os.path.join(reflection_path, reflection_filename), 
            index=False
        )
        grades_df.to_csv(
            os.path.join(reflection_path, grades_filename), 
            index=False
        )
    
    def _display_reflection_info(self, course_name, reflection_folder):
        """Display information about the selected reflection"""
        
        st.subheader("Available files:")
        
        reflection_path = os.path.join(
            "application", "model", "reflections", 
            course_name, reflection_folder
        )
        
        files_info = []
        
        # Check for reflection file
        reflection_file = f"{course_name}_{reflection_folder}.csv"
        reflection_file_path = os.path.join(reflection_path, reflection_file)
        if os.path.exists(reflection_file_path):
            try:
                df = pd.read_csv(reflection_file_path)
                files_info.append(f"• **Reflection file:** {reflection_file}")
                files_info.append(f"  - Shape: {df.shape}")
                files_info.append(f"  - Columns: {len(df.columns)}")
            except Exception as e:
                files_info.append(f"• **Reflection file:** {reflection_file} (Error: {e})")
        else:
            files_info.append(f"• **Reflection file:** {reflection_file} ❌ Not found")
        
        # Check for grades file
        grades_file = f"{course_name}_grades_{reflection_folder}.csv"
        grades_file_path = os.path.join(reflection_path, grades_file)
        if os.path.exists(grades_file_path):
            try:
                df = pd.read_csv(grades_file_path)
                files_info.append(f"• **Grades file:** {grades_file}")
                files_info.append(f"  - Shape: {df.shape}")
                files_info.append(f"  - Columns: {len(df.columns)}")
            except Exception as e:
                files_info.append(f"• **Grades file:** {grades_file} (Error: {e})")
        else:
            files_info.append(f"• **Grades file:** {grades_file} ❌ Not found")
        
        # Check for results directory
        results_path = os.path.join(reflection_path, "results")
        if os.path.exists(results_path):
            result_files = [f for f in os.listdir(results_path) if f.endswith('.csv')]
            if result_files:
                files_info.append(f"• **Analysis results:** {len(result_files)} files")
                for file in result_files:
                    files_info.append(f"  - {file}")
            else:
                files_info.append("• **Analysis results:** No analysis files found")
        else:
            files_info.append("• **Analysis results:** No results directory")
        
        for info in files_info:
            st.write(info)
        
        # Add file quality indicators
        self._display_file_quality_indicators(course_name, reflection_folder) 