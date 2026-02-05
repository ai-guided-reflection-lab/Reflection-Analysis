import streamlit as st
from typing import Optional
from application.model.services.file_system import FileSystemService
from application.model.services.data_processing import DataProcessingService
from application.model.services.state_management import StateManager
import os

class CourseView:
    """Handle course-related UI components"""
    def __init__(self, fs_service: FileSystemService, 
                 data_processor: DataProcessingService,
                 state_manager: StateManager):
        self.fs_service = fs_service
        self.data_processor = data_processor
        self.state_manager = state_manager

    def show_course_selection(self) -> Optional[str]:
        """Display course selection UI"""
        course_action = st.radio(
            "Choose an action:",
            ["Select Existing Course", "Create New Course", "Import Course from CSV"],
            key="workflow_course_action"
        )
        
        if course_action == "Import Course from CSV":
            return self.handle_course_import()
        elif course_action == "Select Existing Course":
            return self.handle_existing_course()
        else:
            return self.handle_new_course()
            
    def handle_existing_course(self) -> Optional[str]:
        """Handle existing course selection"""
        existing_courses = self.fs_service.get_course_directories()
        if existing_courses:
            selected_course = st.selectbox(
                "Select course:",
                existing_courses,
                key="workflow_course_select"
            )
            if selected_course:
                self.state_manager.set_course(selected_course)
                return selected_course
        else:
            st.warning("No existing courses found.")
        return None
        
    def handle_new_course(self) -> Optional[str]:
        """Handle new course creation"""
        new_course = st.text_input("Enter new course name:")
        if new_course and st.button("Create Course"):
            course_path = os.path.join(self.fs_service.base_path, new_course)
            if not os.path.exists(course_path):
                self.fs_service.ensure_directory(course_path)
                st.success(f"Created new course: {new_course}")
                self.state_manager.set_course(new_course)
                return new_course
            else:
                st.error("Course already exists!")
        return None
        
    def handle_course_import(self) -> Optional[str]:
        """Handle course import from CSV"""
        uploaded_file = st.file_uploader("Choose a course CSV file", type='csv')
        if uploaded_file:
            try:
                # Save uploaded file temporarily
                temp_path = "temp_course.csv"
                self.fs_service.save_csv_file(temp_path, uploaded_file.getvalue())
                
                # Process CSV
                course = self.data_processor.process_course_csv(temp_path)
                
                # Create course folder and save data
                if not os.path.exists(os.path.join(self.fs_service.base_path, course.course_name)):
                    self.fs_service.ensure_directory(
                        os.path.join(self.fs_service.base_path, course.course_name)
                    )
                    
                    course_data = {
                        "course_name": course.course_name,
                        "students": [{
                            "name": student.name,
                            "email": student.email,
                            "grades": student.grades
                        } for student in course.get_all_students()]
                    }
                    
                    self.fs_service.save_json_file(
                        os.path.join(self.fs_service.base_path, course.course_name, "course_data.json"),
                        course_data
                    )
                    
                    st.success(f"Created course: {course.course_name}")
                    return course.course_name
                    
            except Exception as e:
                st.error(f"Error importing course: {str(e)}")
            finally:
                if os.path.exists("temp_course.csv"):
                    os.remove("temp_course.csv")
        
        return None 