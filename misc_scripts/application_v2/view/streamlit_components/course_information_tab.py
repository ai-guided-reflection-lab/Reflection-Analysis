"""
Course Information Tab Component
================================

Shows detailed information about the current course and reflection data structures.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any, Optional


def render_course_information_tab() -> None:
    """
    Render the course information tab.
    
    Displays:
    - Current course and reflection folder information
    - Data structure analysis
    - File contents preview
    - Schema information
    """
    st.header("📚 Course Information")
    
    # Get current session state
    course_folder = st.session_state.get('current_course_folder')
    reflection_folder = st.session_state.get('current_reflection_folder')
    reflection_files = st.session_state.get('reflection_files')
    
    if not course_folder:
        st.warning("⚠️ No course selected. Please go to the Workflow tab to select a course.")
        if st.button("🚀 Go to Workflow"):
            st.session_state.active_tab = 0
            st.rerun()
        return
    
    # Display course information
    _render_course_overview(course_folder, reflection_folder)
    
    # Display reflection data information
    if reflection_folder and reflection_files:
        _render_reflection_data_info(reflection_folder, reflection_files)
    else:
        st.info("💡 Select reflection data in the Workflow tab to see detailed information.")
    
    # Display available course exploration
    _render_course_exploration(course_folder)


def _render_course_overview(course_folder: str, reflection_folder: Optional[str]) -> None:
    """Render overview of current course selection."""
    st.subheader("📁 Current Selection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Course Folder", course_folder if course_folder else "None")
        if course_folder:
            st.success("✅ Course Selected")
        
    with col2:
        st.metric("Reflection Folder", reflection_folder if reflection_folder else "None")
        if reflection_folder:
            st.success("✅ Reflection Data Selected")
        elif course_folder:
            st.warning("⚠️ No Reflection Data")


def _render_reflection_data_info(reflection_folder: str, reflection_files: Any) -> None:
    """Render detailed information about reflection data."""
    st.subheader("📊 Reflection Data Analysis")
    
    try:
        # Convert reflection_files to a more readable format
        if hasattr(reflection_files, 'columns'):
            # It's a DataFrame
            _display_dataframe_info(reflection_files)
        elif isinstance(reflection_files, (list, tuple)):
            # It's a list of files
            _display_file_list_info(reflection_files)
        elif isinstance(reflection_files, dict):
            # It's a dictionary
            _display_dict_info(reflection_files)
        else:
            # Unknown format
            st.info(f"Reflection files type: {type(reflection_files)}")
            st.code(str(reflection_files))
            
    except Exception as e:
        st.error(f"Error analyzing reflection data: {str(e)}")
        st.code(f"Type: {type(reflection_files)}\nContent: {str(reflection_files)[:500]}...")


def _display_dataframe_info(df: pd.DataFrame) -> None:
    """Display information about a pandas DataFrame."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rows", len(df))
    with col2:
        st.metric("Total Columns", len(df.columns))
    with col3:
        st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    
    # Column information
    st.markdown("### 📋 Column Information")
    column_info = []
    for col in df.columns:
        col_type = str(df[col].dtype)
        null_count = df[col].isnull().sum()
        unique_count = df[col].nunique()
        column_info.append({
            "Column": col,
            "Type": col_type,
            "Null Count": null_count,
            "Unique Values": unique_count,
            "Sample Value": str(df[col].iloc[0]) if len(df) > 0 else "N/A"
        })
    
    st.dataframe(pd.DataFrame(column_info), use_container_width=True)
    
    # Data preview
    st.markdown("### 👀 Data Preview")
    st.dataframe(df.head(10), use_container_width=True)
    
    # Data summary
    with st.expander("📈 Statistical Summary"):
        st.dataframe(df.describe(include='all'), use_container_width=True)


def _display_file_list_info(file_list: list) -> None:
    """Display information about a list of files."""
    st.metric("Number of Files", len(file_list))
    
    st.markdown("### 📄 File List")
    for i, file_item in enumerate(file_list[:20]):  # Show first 20 files
        st.write(f"{i+1}. {file_item}")
    
    if len(file_list) > 20:
        st.info(f"... and {len(file_list) - 20} more files")


def _display_dict_info(data_dict: dict) -> None:
    """Display information about a dictionary."""
    st.metric("Number of Keys", len(data_dict.keys()))
    
    st.markdown("### 🔑 Dictionary Structure")
    for key, value in list(data_dict.items())[:10]:  # Show first 10 items
        value_type = type(value).__name__
        value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
        st.write(f"**{key}** ({value_type}): {value_preview}")
    
    if len(data_dict) > 10:
        st.info(f"... and {len(data_dict) - 10} more items")


def _render_course_exploration(course_folder: str) -> None:
    """Render course folder exploration tools."""
    st.subheader("🔍 Course Exploration")
    
    # Show model analysis automatically
    _analyze_course_reflections(course_folder)
    
    st.markdown("### Available Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 List Course Contents", use_container_width=True):
            _explore_course_contents(course_folder)
        
        if st.button("🎓 List Student Contents", use_container_width=True):
            _explore_student_contents(course_folder)
    
    with col2:
        if st.button("🔬 Create Test Instances", use_container_width=True):
            _create_test_instances(course_folder)
        
        if st.button("📄 Create Sample CSV Files", use_container_width=True):
            _create_sample_csv_files(course_folder)


def _explore_course_contents(course_folder: str) -> None:
    """Explore the contents of the course folder."""
    st.markdown("#### 📁 Course Folder Contents")
    
    try:
        # Try to import course-related modules to see what's available
        import os
        
        # This is a placeholder - you'll need to adapt based on your actual course structure
        st.info(f"Exploring course: {course_folder}")
        
        # Look for common course-related files or data
        course_info = {
            "Course Name": course_folder,
            "Type": "Course Selection",
            "Status": "Active" if course_folder else "None"
        }
        
        st.json(course_info)
        
    except Exception as e:
        st.error(f"Error exploring course contents: {str(e)}")


def _explore_student_contents(course_folder: str) -> None:
    """Explore student model contents and capabilities."""
    st.markdown("#### 🎓 Student Contents Analysis")
    
    try:
        from application_v2.model.models.student import Student
        from application_v2.model.models.reflection import Reflection
        from application_v2.model.utilities.course_handler import CourseHandler
        import os
        
        st.success("✅ Successfully imported Student model")
        
        # Check for actual student data first
        st.markdown("##### 🔍 Current Student Data Status")
        
        # Look for student data in session state
        course_obj = st.session_state.get('course_object')
        if course_obj and hasattr(course_obj, 'get_all_students'):
            students = course_obj.get_all_students()
            if students:
                st.success(f"✅ Found {len(students)} students in current course!")
                
                # Show some student info
                st.markdown("**Current Students:**")
                for i, student in enumerate(students[:5]):  # Show first 5
                    st.write(f"{i+1}. {student.name} ({student.email})")
                if len(students) > 5:
                    st.info(f"... and {len(students) - 5} more students")
            else:
                st.warning("⚠️ Course object exists but contains no students")
        else:
            st.info("ℹ️ No course object with students found in session")
        
        # Explain how students are created
        st.markdown("##### 📋 When Are Students Created?")
        st.info("""
        **Students are created when you process CSV files containing course data:**
        
        1. **Course CSV files** (roster with grades) - Creates students with basic info
        2. **Reflection CSV files** - Adds reflection data to existing students
        3. **Manual creation** - Can create individual students programmatically
        """)
        
        # Look for CSV files in the current course folder
        if course_folder:
            st.markdown("##### 📁 CSV Files in Course Folder")
            try:
                # Check if there are CSV files we could process
                csv_files = []
                
                # Updated paths to check application_v2/model structure
                possible_paths = [
                    f"application_v2/model/{course_folder}",  # Direct path in application_v2
                    f"model/{course_folder}",                 # From application_v2/
                    f"../model/{course_folder}",              # From view/streamlit_components/
                ]
                
                course_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        course_path = path
                        break
                
                # Debug information
                st.code(f"Course folder from session: {course_folder}")
                st.code(f"Found working path: {course_path}")
                
                if course_path:
                    st.success(f"✅ Path exists: {course_path}")
                    # Look in all subdirectories (ref1, ref2, etc.)
                    try:
                        subdirs = os.listdir(course_path)
                        st.write(f"**Found subdirectories:** {subdirs}")
                        
                        for subdir in subdirs:
                            subdir_path = os.path.join(course_path, subdir)
                            if os.path.isdir(subdir_path):
                                try:
                                    files_in_subdir = os.listdir(subdir_path)
                                    st.write(f"**Files in {subdir}:** {files_in_subdir}")
                                    for file in files_in_subdir:
                                        if file.endswith('.csv'):
                                            csv_files.append(f"{subdir}/{file}")
                                except PermissionError:
                                    st.warning(f"⚠️ Permission denied accessing {subdir}")
                                except Exception as e:
                                    st.warning(f"⚠️ Error accessing {subdir}: {str(e)}")
                    except Exception as e:
                        st.error(f"Error listing directory contents: {str(e)}")
                else:
                    st.error(f"❌ Could not find course path for: {course_folder}")
                    
                    # Let's also check what paths DO exist
                    st.write("**Checking possible locations:**")
                    for i, path in enumerate(possible_paths):
                        exists = os.path.exists(path)
                        st.write(f"{i+1}. {path} - {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
                    
                    # Check current working directory
                    import os
                    cwd = os.getcwd()
                    st.write(f"**Current working directory:** {cwd}")
                    
                    # List what's in current directory
                    current_dir_contents = os.listdir(".")
                    st.write(f"**Contents of current directory:** {current_dir_contents}")
                    
                    # Check if application_v2/model exists
                    if os.path.exists("application_v2/model"):
                        model_contents = os.listdir("application_v2/model")
                        st.write(f"**Contents of application_v2/model:** {model_contents}")
                
                if csv_files:
                    st.write("**Found CSV files:**")
                    for csv_file in csv_files:
                        st.write(f"- {csv_file}")
                    
                    # Add button to process CSV files
                    if st.button("🔄 Load Students from CSV Files", use_container_width=True):
                        _load_students_from_csv(course_folder, csv_files, course_path)
                else:
                    st.warning("⚠️ No CSV files found in course folder")
                    st.info("💡 **To create students:** Upload CSV files with course roster data")
                    
                    # Show what would be needed
                    st.markdown("##### 📋 Expected File Structure")
                    st.code(f"""
{course_folder}/
├── ref1/
│   ├── {course_folder}_ref1.csv (reflection data)
│   └── {course_folder}_grades_ref1.csv (grades data)
├── ref2/
│   ├── {course_folder}_ref2.csv
│   └── {course_folder}_grades_ref2.csv
└── ... (more reflection folders)
                    """)
                    
            except Exception as e:
                st.warning(f"Could not check course folder: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        
        # Show Student class details
        st.markdown("##### 📋 Student Class Information")
        
        # Show class attributes and their types
        st.markdown("**Class Attributes:**")
        student_attrs = {
            "VALID_DOMAINS": "List of valid email domains",
            "name": "Student's full name",
            "email": "Student's email address", 
            "course": "Course the student is enrolled in",
            "section": "Course section",
            "reflection_data": "Dictionary of reflection data by number",
            "grades": "Dictionary of grades"
        }
        
        for attr, description in student_attrs.items():
            st.write(f"- **{attr}**: {description}")
        
        # Show validation capabilities
        st.markdown("##### ✅ Validation Features")
        st.write("- Email domain validation (charlotte.edu, uncc.edu)")
        st.write("- Automatic email formatting")
        st.write("- Reflection data management")
        st.write("- Grade tracking by reflection number")
        
        # Show data management capabilities
        st.markdown("##### 📊 Data Management")
        st.write("- Add reflection data with grades")
        st.write("- Check reflection submission status")
        st.write("- Check grade availability")
        st.write("- Export to dictionary format")
        
        # Show example usage
        st.markdown("##### 💡 Example Usage")
        example_code = '''
# Create a student manually
student = Student(
    name="John Doe",
    email="jdoe1@charlotte.edu",
    course="ITSC-3155-051"
)

# Or load students from CSV file
course_handler = CourseHandler()
course = course_handler.process_csv("course_roster.csv")
students = course.get_all_students()  # List of Student objects

# Add reflection data
reflection = Reflection(reflection_data)
student.add_reflection_data(1, reflection=reflection, grades={"score": 85})

# Check if student has submitted reflection
has_reflection = student.has_reflection(1)  # True/False
has_grades = student.has_grades(1)  # True/False
'''
        st.code(example_code, language='python')
            
    except ImportError as e:
        st.error("⚠️ Could not import Student model")
        st.code(f"Import Error: {e}")
    except Exception as e:
        st.error(f"Error exploring student contents: {str(e)}")


def _load_students_from_csv(course_folder: str, csv_files: list, base_path: Optional[str] = None) -> None:
    """Load students from CSV files in the course folder."""
    try:
        from application_v2.model.utilities.course_handler import CourseHandler
        
        st.markdown("#### 🔄 Loading Students from CSV")
        
        if not base_path:
            st.error("No valid path provided for loading CSV files")
            return
        
        # Look for a course roster file (typically has grades or student data)
        roster_file = None
        for csv_file in csv_files:
            if any(keyword in csv_file.lower() for keyword in ['grade', 'roster', 'student', course_folder.lower()]):
                roster_file = csv_file
                break
        
        if not roster_file:
            # Look for grades files first, then any CSV
            grades_files = [f for f in csv_files if 'grades' in f.lower()]
            if grades_files:
                roster_file = grades_files[0]
            else:
                roster_file = csv_files[0]
        
        csv_path = os.path.join(base_path, roster_file)
        st.info(f"Processing: {roster_file}")
        st.code(f"Full path: {csv_path}")
        
        # Process the CSV file
        course_handler = CourseHandler()
        course = course_handler.process_csv(csv_path)
        
        # Store in session state
        st.session_state['course_object'] = course
        
        students = course.get_all_students()
        st.success(f"✅ Successfully loaded {len(students)} students!")
        
        # Show some details
        if students:
            st.markdown("**Loaded Students:**")
            for i, student in enumerate(students[:10]):  # Show first 10
                st.write(f"{i+1}. {student.name} ({student.email}) - {student.course}")
            if len(students) > 10:
                st.info(f"... and {len(students) - 10} more students")
                
    except Exception as e:
        st.error(f"Error loading students from CSV: {str(e)}")
        st.code(f"Make sure the CSV file has the expected format with 'Student' and 'SIS Login ID' columns")
        import traceback
        st.code(traceback.format_exc())


def _analyze_course_reflections(course_folder: str) -> None:
    """Analyze course and reflection data structures."""
    st.markdown("#### 🔧 Course & Reflection Data Analysis")
    
    try:
        # Try to import and analyze the course and reflection classes
        from application_v2.model.models.course import Course
        from application_v2.model.models.student import Student
        from application_v2.model.models.reflection import Reflection
        
        st.success("✅ Successfully imported Course, Student, and Reflection models")
        
        # Analyze Course class
        st.markdown("##### 📚 Course Model")
        course_methods = [method for method in dir(Course) if not method.startswith('_')]
        st.write("**Available Methods:**")
        for method in course_methods:
            st.write(f"- `{method}`")
        
        # Analyze Student class
        st.markdown("##### 🎓 Student Model")
        student_methods = [method for method in dir(Student) if not method.startswith('_')]
        st.write("**Available Methods:**")
        for method in student_methods:
            st.write(f"- `{method}`")
        
        # Analyze Reflection class
        st.markdown("##### 💭 Reflection Model")
        reflection_methods = [method for method in dir(Reflection) if not method.startswith('_')]
        st.write("**Available Methods:**")
        for method in reflection_methods:
            st.write(f"- `{method}`")
            
    except ImportError as e:
        st.error("⚠️ Could not import Course/Student/Reflection models")
        st.code(f"Import Error: {e}")
        
        # Show alternative exploration
        st.info("💡 **Alternative Exploration**: Use the original application modules")
        _explore_session_state()


def _create_test_instances(course_folder: str) -> None:
    """Create test instances of Course and Reflection models."""
    try:
        from application_v2.model.models.course import Course
        from application_v2.model.models.student import Student
        from application_v2.model.models.reflection import Reflection
        
        st.markdown("#### 🧪 Test Instance Creation")
        
        # Try to create a Course instance
        course = Course(course_folder)
        st.success(f"✅ Created Course instance for: {course_folder}")
        
        # Show course properties
        course_props = {}
        for attr in dir(course):
            if not attr.startswith('_') and not callable(getattr(course, attr)):
                try:
                    value = getattr(course, attr)
                    course_props[attr] = str(value)[:100]  # Truncate long values
                except:
                    course_props[attr] = "Unable to access"
        
        if course_props:
            st.markdown("**Course Properties:**")
            st.json(course_props)
        
        # Try to create a Student instance
        try:
            student = Student(
                name="Test Student",
                email="teststudent@charlotte.edu", 
                course=course_folder
            )
            st.success("✅ Created Student instance")
            
            # Show student properties
            student_props = {}
            for attr in dir(student):
                if not attr.startswith('_') and not callable(getattr(student, attr)):
                    try:
                        value = getattr(student, attr)
                        student_props[attr] = str(value)[:100]  # Truncate long values
                    except:
                        student_props[attr] = "Unable to access"
            
            if student_props:
                st.markdown("**Student Properties:**")
                st.json(student_props)
                
        except Exception as e:
            st.error(f"Could not create Student instance: {str(e)}")
        
    except Exception as e:
        st.error(f"Error creating test instances: {str(e)}")


def _create_sample_csv_files(course_folder: str) -> None:
    """Create sample CSV files for testing purposes."""
    st.markdown("#### 📄 Sample CSV File Creation")
    
    try:
        import pandas as pd
        import os
        
        # Create the course directory structure if it doesn't exist
        course_path = f"application_v2/model/{course_folder}"
        os.makedirs(course_path, exist_ok=True)
        
        # Create ref1 directory
        ref1_path = os.path.join(course_path, "ref1")
        os.makedirs(ref1_path, exist_ok=True)
        
        # Create sample reflection data
        reflection_data = pd.DataFrame({
            'Student': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'SIS Login ID': ['jdoe1@charlotte.edu', 'jsmith2@charlotte.edu', 'bjohnson3@charlotte.edu', 'abrown4@charlotte.edu'],
            'Reflection Text': [
                'This week I learned about software engineering principles...',
                'The most challenging part was understanding design patterns...',
                'I found the team project very insightful because...',
                'My biggest takeaway from this assignment was...'
            ],
            'Submission Date': ['2024-01-15', '2024-01-16', '2024-01-15', '2024-01-17'],
            'Word Count': [150, 200, 175, 180]
        })
        
        # Create sample grades data
        grades_data = pd.DataFrame({
            'ID': ['jdoe1@charlotte.edu', 'jsmith2@charlotte.edu', 'bjohnson3@charlotte.edu', 'abrown4@charlotte.edu'],
            'Current Score': [85, 92, 78, 88],
            'Possible Points': [100, 100, 100, 100],
            'Grade': ['B', 'A-', 'C+', 'B+']
        })
        
        # Save the files
        reflection_file = os.path.join(ref1_path, f"{course_folder}_ref1.csv")
        grades_file = os.path.join(ref1_path, f"{course_folder}_grades_ref1.csv")
        
        reflection_data.to_csv(reflection_file, index=False)
        grades_data.to_csv(grades_file, index=False)
        
        st.success(f"✅ Created sample CSV files in {ref1_path}")
        st.write(f"**Files created:**")
        st.write(f"- {reflection_file}")
        st.write(f"- {grades_file}")
        
        # Show preview of created files
        st.markdown("##### 📊 Reflection Data Preview")
        st.dataframe(reflection_data, use_container_width=True)
        
        st.markdown("##### 📈 Grades Data Preview")
        st.dataframe(grades_data, use_container_width=True)
        
        # Add button to load the created data
        if st.button("🔄 Load Created Sample Data", use_container_width=True):
            _load_students_from_csv(course_folder, ["ref1/" + f"{course_folder}_ref1.csv"], course_path)
        
    except Exception as e:
        st.error(f"Error creating sample CSV files: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def _explore_session_state() -> None:
    """Explore the current session state for course/reflection data."""
    st.markdown("#### 💾 Session State Analysis")
    
    relevant_keys = [key for key in st.session_state.keys() 
                    if 'course' in key.lower() or 'reflection' in key.lower()]
    
    if relevant_keys:
        st.write("**Course/Reflection Related Session State:**")
        for key in relevant_keys:
            value = st.session_state[key]
            value_type = type(value).__name__
            value_preview = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
            
            st.markdown(f"**🔑 {key}** ({value_type}):")
            st.code(value_preview)
    else:
        st.info("No course/reflection related data found in session state") 