import pandas as pd
from application_v2.model.models.course import Course
from application_v2.model.models.student import Student
from application_v2.model.models.reflection import Reflection

class CourseHandler:
    @staticmethod
    def process_csv(file_path: str, skip_rows: int = 2) -> Course:
        """Process a CSV file and create a Course object with Students.
        
        Expected CSV format:
        [header row]
        [skip row 1]
        [skip row 2]
        ID,SIS User ID,Section,Student,SIS Login ID,assignment1,assignment2,...
        309502,1265875,ITSC-3155-051,John Doe,jdoe1,85,90,...
        """
        try:
            # First read CSV file, skipping specified rows after header
            df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1))
            
            # Replace 'ID' column with 'QID12_1_TEXT' if it exists
            if 'QID12_1_TEXT' in df.columns:
                df['ID'] = df['QID12_1_TEXT']
            
            # Validate required columns
            required_cols = {'Student', 'SIS Login ID'}
            if not required_cols.issubset(df.columns):
                raise ValueError(f"CSV must contain columns: {required_cols}")
            
            # Skip rows with NaN or empty values in required columns
            df = df.dropna(subset=['Student', 'SIS Login ID'])
            df = df.dropna(axis=1, how='all')
            
            # Get assignment columns (any column not in the skip list)
            columns_to_skip = {'ID', 'SIS User ID', 'Section', 'Student', 'SIS Login ID'}
            grade_cols = [col for col in df.columns if col not in columns_to_skip]
            
            # Convert grade columns to numeric
            for col in grade_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(axis=1, how='all')
            grade_cols = [col for col in df.columns if col not in columns_to_skip]
            
            # Create Course object
            course_name = df['Section'].iloc[0] if 'Section' in df.columns else file_path.split('/')[-1].replace('.csv', '')
            course = Course(course_name)
            
            # Process each row into a Student object
            for _, row in df.iterrows():
                email = f"{row['SIS Login ID']}@charlotte.edu"
                grades = {col: row[col] for col in grade_cols if pd.notna(row[col])}
                
                student = Student(
                    name=row['Student'],
                    email=email,
                    course=course_name,
                    grades=grades
                )
                course.add_student(student)
            
            if 'Section' in df.columns and 'SIS Login ID' in df.columns:
                print(f"All SIS Login IDs from CSV: {[str(x).strip().lower() for x in df['SIS Login ID'].tolist()]}")
                for student in course.get_all_students():
                    sis_id = student.email.split('@')[0].strip().lower()
                    print(f"Current student SIS Login ID (email prefix): {sis_id}")
                    # Make sure to strip and lowercase the SIS Login ID from the CSV as well
                    sis_login_ids = df['SIS Login ID'].astype(str).str.strip().str.lower()
                    match = sis_login_ids == sis_id
                    row = df[match]
                    if not row.empty:
                        student.section = row.iloc[0]['Section']
                    print(f"Student email: {student.email}, SIS Login ID (student): {sis_id}, SIS Login ID (csv): {row.iloc[0]['SIS Login ID'] if not row.empty else 'N/A'}, Section: {student.section}")
            
            return course
            
        except Exception as e:
            raise Exception(f"Error processing CSV: {str(e)}")

    @staticmethod
    def add_reflections_to_course(course: Course, reflection_file_path: str) -> tuple[Course, dict]:
        """Add reflections to students in a course."""
        try:
            ref_df = pd.read_csv(reflection_file_path)
            
            # Replace 'ID' column with 'QID12_1_TEXT' if it exists
            if 'QID12_1_TEXT' in ref_df.columns:
                ref_df['ID'] = ref_df['QID12_1_TEXT']
            
            stats = {
                'total_reflections': 0,
                'matched_reflections': 0,
                'invalid_ids': 0
            }
            
            for _, row in ref_df.iterrows():
                stats['total_reflections'] += 1
                
                if not CourseHandler.is_valid_email(row['ID']):
                    stats['invalid_ids'] += 1
                    continue
                
                reflection = Reflection(row)
                reflection_username = row['ID'].split('@')[0].lower().strip()
                
                student = next(
                    (s for s in course.get_all_students() 
                     if s.email.split('@')[0].lower().strip() == reflection_username),
                    None
                )
                
                if student:
                    if not hasattr(student, 'reflections'):
                        student.reflections = []
                    student.reflections.append(reflection)
                    stats['matched_reflections'] += 1
            
            return course, stats
            
        except Exception as e:
            raise Exception(f"Error processing reflections: {str(e)}")

    @staticmethod
    def is_valid_email(id_str: str) -> bool:
        """Check if string is in valid email format."""
        return isinstance(id_str, str) and '@' in id_str
