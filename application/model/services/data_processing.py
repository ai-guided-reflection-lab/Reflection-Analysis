import pandas as pd
from typing import Tuple, Dict, Any, List, Optional
from application.model.utilities.course_handler import CourseHandler
from application.model.models.course import Course
from application.model.models.student import Student
from application.model.models.reflection import Reflection
from application.controller.gpt_api import PromptConfig, Model
from application.controller.utilities.output_compiler import LabelCounter
import os

class DataProcessingService:
    """Handle all data processing operations"""
    def __init__(self):
        self.course_handler = CourseHandler()
        
    def process_course_csv(self, file_path: str) -> Course:
        """Process course CSV file and create Course object"""
        return self.course_handler.process_csv(file_path)
        
    def process_reflection_files(self, reflection_path: str, grades_path: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Process reflection and grades CSV files"""
        reflection_data = pd.read_csv(reflection_path) if reflection_path else None
        grades_data = pd.read_csv(grades_path) if grades_path else None
        return reflection_data, grades_data
        
    def create_student_objects(self, data: Dict[str, Any], course_name: str) -> List[Student]:
        """Create student objects from data"""
        students = []
        for student_data in data:
            student = Student(
                name=student_data.get('name', 'Not Set'),
                email=student_data.get('id', 'Not Set'),
                course=course_name,
                reflections=student_data.get('reflections', [])
            )
            students.append(student)
        return students 

    def load_reflection_data(self, reflection_path: str) -> Optional[List[Reflection]]:
        """Load reflection data from CSV files in the reflection folder"""
        try:
            # Get the course name and ref number from the path
            path_parts = reflection_path.split(os.sep)
            course_name = path_parts[-2]
            ref_num = path_parts[-1].replace('ref', '')
            
            # Look for reflection CSV file
            reflection_file = f"{course_name}_ref{ref_num}.csv"
            reflection_csv_path = os.path.join(reflection_path, reflection_file)
            
            if not os.path.exists(reflection_csv_path):
                return None
                
            # Read reflection data and create Reflection objects
            df = pd.read_csv(reflection_csv_path)
            reflections = []
            for _, row in df.iterrows():
                reflection_data = row.to_dict()
                reflection_data['reflection_number'] = int(ref_num)
                reflection = Reflection(reflection_data)
                reflections.append(reflection)
                
            return reflections
            
        except Exception as e:
            print(f"Error loading reflection data: {e}")
            return None

    def analyze_topics(self, reflections: List[Reflection], selected_prompt: str = None, num_reflections: int = None, provider: str = "openai", model: str = None) -> List[Dict]:
        """Run GPT analysis on reflections"""
        try:
            print("\nStarting GPT analysis")
            # Limit number of reflections if specified
            if num_reflections is not None and num_reflections > 0:
                reflections = reflections[:num_reflections]
                print(f"Limited to {num_reflections} reflections")
            
            # Get prompt path
            prompts_dir = os.path.join("application", "model", "prompts")
            if not selected_prompt:
                prompt_path = os.path.join(prompts_dir, "topic_analysis.json")
            else:
                prompt_path = os.path.join(prompts_dir, selected_prompt)
            print(f"Using prompt from: {prompt_path}")
            
            prompt_config = PromptConfig(prompt_path)
            
            # Run GPT analysis
            print("Running GPT analysis on reflections...")
            results = prompt_config.run_prompt_on_individual_refs(
                refs=reflections,
                model=model or ("gpt-4o" if provider == "openai" else None),
                provider=provider,
                temp=0.7,
                max_tokens=4096 if provider == "groq" else 500
            )
            print(f"Got {len(results)} results from GPT")
            
            return results
            
        except Exception as e:
            print(f"Error in analyze_topics: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
