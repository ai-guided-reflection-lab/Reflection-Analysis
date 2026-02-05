import streamlit as st
import os
import json
import pandas as pd
from application.model.models.student import Student
from application.model.models.course import Course
from application.model.models.reflection import Reflection
from app.logic.course_handler import CourseHandler  # Import the existing handler
from application.model.services.file_system import FileSystemService
from application.model.services.data_processing import DataProcessingService
from application.model.services.state_management import StateManager
from application.view.components.course_view import CourseView
from application.view.components.reflection_view import ReflectionView
from application.html_builder.builder import HTMLBuilder
import base64

class CourseManager:
    """
    Manages course directories and operations.
    Handles creation, retrieval, and path management for course data.
    """
    def __init__(self, base_path=None):
        """Initialize CourseManager with configurable base path"""
        self.base_path = base_path or os.path.join("application", "model", "reflections")  # Updated path
        os.makedirs(self.base_path, exist_ok=True)
        
    def get_existing_courses(self):
        """Get list of existing course directories"""
        return [d for d in os.listdir(self.base_path) 
                if os.path.isdir(os.path.join(self.base_path, d))]
    
    def create_course(self, course_name):
        """Create a new course directory"""
        course_path = os.path.join(self.base_path, course_name)
        if not os.path.exists(course_path):
            os.makedirs(course_path)
            return True
        return False
    
    def get_course_path(self, course_name):
        """Get full path for a course"""
        return os.path.join(self.base_path, course_name)

class ReflectionManager:
    """
    Manages reflection data within courses.
    Handles reflection folders, CSV files for both reflection data and grades.
    Follows specific naming conventions: coursename_ref#.csv for reflections
    and coursename_grades_ref#.csv for grades.
    """
    def __init__(self, course_path):
        self.course_path = course_path
        
    def get_existing_reflections(self):
        """Get list of existing reflection folders and their CSV files"""
        reflections = []
        # Look for ref# folders
        for folder in sorted([d for d in os.listdir(self.course_path) 
                            if d.startswith('ref') and os.path.isdir(os.path.join(self.course_path, d))]):
            folder_path = os.path.join(self.course_path, folder)
            
            # Get reflection and grades CSV files
            ref_files = {}
            for f in os.listdir(folder_path):
                if not f.endswith('.csv'):
                    continue
                    
                course_name = os.path.basename(self.course_path)
                ref_num = folder.replace('ref', '')
                
                # Match exact file patterns
                if f == f"{course_name}_ref{ref_num}.csv":
                    ref_files['reflection'] = f
                elif f == f"{course_name}_grades_ref{ref_num}.csv":
                    ref_files['grades'] = f
                    
            if ref_files:
                reflections.append((folder, ref_files))
        return reflections
    
    def create_reflection(self, ref_num, course_name):
        """Create a new reflection folder with proper naming"""
        folder_name = f"ref{ref_num}"
        folder_path = os.path.join(self.course_path, folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return True
        return False
    
    def process_reflection_files(self, ref_folder, ref_files):
        """Process reflection and grades CSV files"""
        folder_path = os.path.join(self.course_path, ref_folder)
        
        # Load reflection data
        reflection_data = None
        if 'reflection' in ref_files:
            reflection_path = os.path.join(folder_path, ref_files['reflection'])
            reflection_data = pd.read_csv(reflection_path)
            
        # Load grades data
        grades_data = None
        if 'grades' in ref_files:
            grades_path = os.path.join(folder_path, ref_files['grades'])
            grades_data = pd.read_csv(grades_path)
            
        return reflection_data, grades_data

class DataDisplayManager:
    """
    Handles data visualization and object creation.
    Converts raw data into Student objects and provides formatted display methods.
    """
    @staticmethod
    def create_student_objects(student_data_list, current_course):
        """Create list of Student objects from raw data"""
        students = []
        for student_data in student_data_list:
            student = Student(
                name=student_data.get('name', 'Not Set'),
                email=student_data.get('id', 'Not Set'),
                course=current_course,
                reflections=student_data.get('reflections', [])
            )
            students.append(student)
        return students
    
    @staticmethod
    def display_student_data(student):
        """Display formatted student data"""
        st.write(f"Student Name: {student.name}")
        st.write(f"Student Email: {student.email}")
        st.write(f"Course: {student.course}")
        
        if student.reflections:
            st.write("Reflections:")
            for ref_data in student.reflections:
                reflection = Reflection(ref_data)
                st.write(reflection.console_output())
                if reflection.grades:
                    st.write("Grades:", reflection.get_grades())
        st.write("---")

def run_workflow_tab():
    """
    Main entry point for the workflow UI.
    Sets up services and components, manages the overall workflow:
    1. Course selection/creation
    2. Reflection management
    3. Report generation
    4. Topic analysis
    """
    # Initialize services
    fs_service = FileSystemService()
    data_processor = DataProcessingService()
    state_manager = StateManager()
    
    # Initialize UI components
    course_view = CourseView(fs_service, data_processor, state_manager)
    reflection_view = ReflectionView(fs_service, data_processor, state_manager)
    
    # Create main sections
    st.header("Course Management")
    course_name = course_view.show_course_selection()
    
    if course_name:
        st.header("Reflection Management")
        reflection_view.show_reflection_selection(course_name)
        
        # Add Topic Analysis section
        st.header("Topic Analysis")
        if st.button("Run Topic Analysis", key="run_topic_analysis"):
            try:
                from application.view.analysis_UI.topic_analysis import run_topic_analysis_tab
                run_topic_analysis_tab(is_workflow=True)
            except Exception as e:
                st.error(f"Error running topic analysis: {str(e)}")
        
        # Add HTML Report Generation section
        st.header("Generate Report")
        
        # Report mode is now always instructor mode (simplified)
        report_mode = "instructor"
        
        if st.button("Generate HTML Report"):
            try:
                # Build course object with all data
                course_path = os.path.join(fs_service.base_path, course_name)
                reflection_folders = fs_service.get_reflection_folders(course_path)
                
                if reflection_folders:
                    course = Course(course_name)
                    
                    # Process all reflection folders
                    for folder in reflection_folders:
                        ref_num = int(folder.replace('ref', ''))
                        course.add_reflection_number(ref_num)
                        
                        folder_path = os.path.join(course_path, folder)
                        files = fs_service.get_reflection_files(folder_path, course_name)
                        
                        if 'grades' in files:
                            grades_path = os.path.join(folder_path, files['grades'])
                            grades_data = pd.read_csv(grades_path)
                            
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
                    
                    # Generate and offer download of HTML report with selected mode
                    builder = HTMLBuilder()
                    html_content = builder.build_student_profiles(course, mode=report_mode)
                    
                    # Create filename for instructor report
                    filename = f"{course_name}_student_profiles_instructor.html"
                    
                    b64 = base64.b64encode(html_content.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="{filename}" class="button">Download Instructor Report</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # Show success message
                    st.success("✅ Instructor report generated! This simplified version focuses on student insights without statistical complexity.")
                    
                else:
                    st.warning("No reflection data found for this course")
                    
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

def handle_course_selection(course_manager):
    """
    Provides UI for course management with three options:
    1. Select existing course
    2. Create new course
    3. Import course from CSV
    Returns selected/created course name or None
    """
    course_action = st.radio(
        "Choose an action:",
        ["Select Existing Course", "Create New Course", "Import Course from CSV"],  # Added option
        key="workflow_course_action"
    )
    
    if course_action == "Import Course from CSV":
        return handle_course_import(course_manager)
    elif course_action == "Select Existing Course":
        return handle_existing_course(course_manager)
    else:
        return handle_new_course(course_manager)

def handle_course_import(course_manager):
    """
    Handles CSV import functionality for courses.
    - Accepts CSV upload
    - Processes course data
    - Creates course directory
    - Saves course metadata as JSON
    """
    uploaded_file = st.file_uploader("Choose a course CSV file", type='csv')
    if uploaded_file:
        try:
            # Save uploaded file temporarily
            with open("temp_course.csv", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Process CSV
            course = CourseHandler.process_csv("temp_course.csv")
            
            # Create course folder
            if course_manager.create_course(course.course_name):
                st.success(f"Created course: {course.course_name}")
                
                # Save course data as JSON
                course_data = {
                    "course_name": course.course_name,
                    "students": [{
                        "name": student.name,
                        "email": student.email,
                        "grades": student.grades
                    } for student in course.get_all_students()]
                }
                
                with open(os.path.join(course_manager.get_course_path(course.course_name), 
                                     "course_data.json"), "w") as f:
                    json.dump(course_data, f, indent=4)
                
                return course.course_name
            
        except Exception as e:
            st.error(f"Error importing course: {str(e)}")
        finally:
            if os.path.exists("temp_course.csv"):
                os.remove("temp_course.csv")
    
    return None

def handle_existing_course(course_manager):
    """
    Manages selection of existing courses.
    Displays dropdown of available courses and updates session state.
    """
    existing_courses = course_manager.get_existing_courses()
    if existing_courses:
        selected_course = st.selectbox(
            "Select course:",
            existing_courses,
            key="workflow_course_select"
        )
        if selected_course:
            st.session_state.current_course_folder = selected_course
            return selected_course
    else:
        st.warning("No existing courses found.")
    return None

def handle_new_course(course_manager):
    """
    Handles creation of new courses.
    Provides input field for course name and creates course directory.
    """
    new_course = st.text_input("Enter new course name:")
    if new_course and st.button("Create Course"):
        if course_manager.create_course(new_course):
            st.success(f"Created new course: {new_course}")
            st.session_state.current_course_folder = new_course
            return new_course
        else:
            st.error("Course already exists!")
    return None

def handle_reflection_management(reflection_manager, current_course):
    """
    Main reflection management interface.
    Provides options for:
    1. Selecting existing reflections
    2. Creating new reflections
    3. Importing reflection data from CSV
    """
    st.header("Reflection Management")
    
    reflection_action = st.radio(
        "Choose action:",
        ["Select Existing Reflection", "Create New Reflection", "Import Reflection from CSV"],  # Added option
        key="workflow_reflection_action"
    )
    
    if reflection_action == "Import Reflection from CSV":
        handle_reflection_import(reflection_manager, current_course)
    elif reflection_action == "Select Existing Reflection":
        handle_existing_reflection(reflection_manager, current_course)
    else:
        handle_new_reflection(reflection_manager, current_course)

def handle_existing_reflection(reflection_manager, current_course):
    """
    Manages selection and display of existing reflections.
    Shows available reflection files and provides data preview functionality.
    """
    reflections = reflection_manager.get_existing_reflections()
    
    if reflections:
        # Create display names for the selectbox
        reflection_options = [f"{ref_folder}" for ref_folder, _ in reflections]
        selected_folder = st.selectbox(
            "Select reflection:",
            reflection_options,
            key="workflow_reflection_select"
        )
        
        if selected_folder:
            # Find the files for the selected folder
            selected_files = next(files for folder, files in reflections if folder == selected_folder)
            
            st.session_state.current_reflection_folder = selected_folder
            st.session_state.reflection_files = selected_files
            
            # Display available files
            st.write("Available files:")
            if 'reflection' in selected_files:
                st.write(f"- Reflection file: {selected_files['reflection']}")
            if 'grades' in selected_files:
                st.write(f"- Grades file: {selected_files['grades']}")
                
            # Process the files if requested
            if st.button("Load Reflection Data"):
                reflection_data, grades_data = reflection_manager.process_reflection_files(
                    selected_folder, selected_files
                )
                
                if reflection_data is not None:
                    st.write("Reflection Data Preview:")
                    st.dataframe(reflection_data.head())
                    
                if grades_data is not None:
                    st.write("Grades Data Preview:")
                    st.dataframe(grades_data.head())
    else:
        st.warning("No existing reflections found.")

def handle_new_reflection(reflection_manager, current_course):
    """
    Handles creation of new reflection entries.
    Creates properly named reflection folders within course directory.
    """
    new_reflection = st.text_input("Enter new reflection name (without .json):")
    if new_reflection and st.button("Create Reflection"):
        if reflection_manager.create_reflection(new_reflection, current_course):
            st.success(f"Created new reflection: {new_reflection}")
        else:
            st.error("Reflection already exists!")

def handle_reflection_import(reflection_manager, current_course):
    """
    Manages CSV import for reflection and grades data.
    - Handles both reflection and grades file uploads
    - Maintains proper file naming convention
    - Creates new reflection folder with sequential numbering
    """
    st.write("Upload Reflection Files:")
    
    reflection_file = st.file_uploader("Choose reflection CSV file", type='csv', key="reflection_csv")
    grades_file = st.file_uploader("Choose grades CSV file", type='csv', key="grades_csv")
    
    if reflection_file or grades_file:
        if st.button("Import Files"):
            try:
                # Get next ref number
                existing_refs = [d for d in os.listdir(reflection_manager.course_path) 
                               if d.startswith('ref') and os.path.isdir(os.path.join(reflection_manager.course_path, d))]
                next_ref_num = len(existing_refs) + 1
                
                # Create new reflection folder
                if reflection_manager.create_reflection(next_ref_num, current_course):
                    folder_name = f"ref{next_ref_num}"
                    folder_path = os.path.join(reflection_manager.course_path, folder_name)
                    
                    # Save reflection file with correct naming
                    if reflection_file:
                        new_reflection_name = f"{current_course}_ref{next_ref_num}.csv"
                        with open(os.path.join(folder_path, new_reflection_name), "wb") as f:
                            f.write(reflection_file.getvalue())
                            
                    # Save grades file with correct naming
                    if grades_file:
                        new_grades_name = f"{current_course}_grades_ref{next_ref_num}.csv"
                        with open(os.path.join(folder_path, new_grades_name), "wb") as f:
                            f.write(grades_file.getvalue())
                            
                    st.success(f"Created new reflection folder: {folder_name}")
                else:
                    st.error("Failed to create reflection folder")
                    
            except Exception as e:
                st.error(f"Error importing files: {str(e)}")

def display_course_data(reflection_manager, current_course):
    """
    Displays processed course and student data.
    Shows:
    - Course object details
    - Individual student information
    - Reflection and grades data previews
    """
    st.header("Course and Student Data")
    try:
        folder_name = st.session_state.get('current_reflection_folder')
        reflection_files = st.session_state.get('reflection_files')
        if not folder_name or not reflection_files:
            st.warning("Please select a reflection folder and files.")
            return
            
        reflection_data, grades_data = reflection_manager.process_reflection_files(folder_name, reflection_files)
        display_manager = DataDisplayManager()
        
        # Create and display objects
        students = display_manager.create_student_objects(reflection_data.to_dict(orient='records'), current_course)
        course = Course(course_name=current_course, students=students)
        
        with st.expander("View Course Object", expanded=True):
            st.json(course.to_dict())
        
        with st.expander("View Individual Students", expanded=True):
            for student in students:
                display_manager.display_student_data(student)
                
    except Exception as e:
        st.error(f"Error loading reflection data: {str(e)}")