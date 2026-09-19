import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from application.model.services.file_system import FileSystemService
from application.model.services.data_processing import DataProcessingService
from application.model.services.state_management import StateManager
from application.model.models.reflection import Reflection
from application.controller.gpt_api import DEFAULT_GROQ_MODEL

class TopicAnalysisManager:
    """Manages topic analysis functionality"""
    def __init__(self, fs_service, data_processor, state_manager):
        self.fs_service = fs_service
        self.data_processor = data_processor
        self.state_manager = state_manager
        
    def process_analysis_results(self, results, reflections):
        """Process GPT analysis results into DataFrames"""
        processed_data = []
        
        for reflection, result in zip(reflections, results):
            try:
                # Ensure result is a dictionary
                if isinstance(result, str):
                    try:
                        import json
                        result = json.loads(result)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error for reflection {reflection.id}: {e}")
                        print(f"Raw result: {result}")
                        raise ValueError("The model returned invalid JSON. Please rerun the analysis.") from e
                
                # Base data with reflection ID - preserve original ID format
                original_id = reflection.id
                print(f"DEBUG: Processing reflection with original ID: '{original_id}' (type: {type(original_id)})")
                
                # Ensure ID is preserved as string to maintain format (email, 2-digit, 4-digit)
                base_data = {'ID': str(original_id).strip() if original_id else ''}
                
                # Add reflection data
                for q, r in zip(reflection.questions, reflection.reflections):
                    base_data[q] = r
                
                # Process result data
                if isinstance(result, dict):
                    # Get arrays of labels
                    primary_labels = result.get('primary_labels_selected', [])
                    resolution_labels = result.get('resolution_primary_labels', [])
                    
                    # Ensure we have lists
                    if not isinstance(primary_labels, list):
                        primary_labels = [primary_labels]
                    if not isinstance(resolution_labels, list):
                        resolution_labels = [resolution_labels]
                    if not primary_labels or not all(
                        isinstance(label, str) and label.strip() for label in primary_labels
                    ):
                        raise ValueError("The model response is missing valid primary_labels_selected.")
                    
                    # Create a row for each label pair
                    for i in range(max(len(primary_labels), len(resolution_labels))):
                        row_data = base_data.copy()
                        row_data.update({
                            'primary_labels_selected': primary_labels[i] if i < len(primary_labels) else 'Unknown',
                            'resolution_primary_labels': resolution_labels[i] if i < len(resolution_labels) else 'Unspecified',
                            'urgency': result.get('urgency', 'medium'),
                            'reflection_summary': result.get('reflection_summary', ''),
                            'instructor_suggestions': result.get('instructor_suggestions', '')
                        })
                        processed_data.append(row_data)
                        print(f"DEBUG: Added row with ID: '{row_data['ID']}'")
                else:
                    print(f"Unexpected result format for reflection {reflection.id}: {type(result)}")
                    raise ValueError("The model response must be a JSON object.")
                
            except Exception as e:
                print(f"Error processing reflection {reflection.id}: {e}")
                raise
        
        # Create DataFrames
        if not processed_data:
            print("No data was processed successfully")
            # Return empty DataFrames with correct columns
            empty_df = pd.DataFrame(columns=[
                'ID', 'primary_labels_selected', 'resolution_primary_labels', 
                'urgency', 'reflection_summary', 'instructor_suggestions'
            ])
            return empty_df, empty_df, empty_df
        
        # Create main DataFrame
        combined_df = pd.DataFrame(processed_data).fillna('')
        
        # Create counts DataFrame
        counts_df = pd.DataFrame({
            'Topic': combined_df['primary_labels_selected'].astype(str),
            'Resolution Status': combined_df['resolution_primary_labels'].astype(str),
            'Count': 1
        }).groupby(['Topic', 'Resolution Status'], as_index=False).sum()
        
        # Create plot DataFrame
        plot_df = counts_df.copy()
        
        print(f"Processed {len(processed_data)} reflections successfully")
        return combined_df, counts_df, plot_df
    
    def display_analysis(self, course_name, reflection_folder):
        """Display topic analysis results"""
        try:
            # Load analysis results
            results_path = os.path.join(self.fs_service.base_path, course_name, reflection_folder, "results")
            if not os.path.exists(results_path):
                st.warning("No analysis results found. Please run the analysis first.")
                return
            
            file_prefix = f"{course_name}_{reflection_folder}"
            exploded_path = os.path.join(results_path, f"{file_prefix}_exploded.csv")
            plot_data_path = os.path.join(results_path, f"{file_prefix}_plot_data.csv")
            
            if not os.path.exists(exploded_path):
                st.warning(f"Analysis data not found at: {exploded_path}")
                return
            
            # Load and display results
            combined_df = pd.read_csv(exploded_path)
            
            if combined_df.empty:
                st.warning("No analysis data available.")
                return
            
            # Display detailed analysis first
            st.subheader("Detailed Analysis")
            
            # Add filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                topics = ['All Topics'] + sorted(combined_df['primary_labels_selected'].unique().tolist())
                selected_topic = st.selectbox('Topic:', topics)
            
            with col2:
                resolutions = ['All Resolutions'] + sorted(combined_df['resolution_primary_labels'].unique().tolist())
                selected_resolution = st.selectbox('Resolution Status:', resolutions)
            
            with col3:
                urgencies = ['All Urgency Levels'] + sorted(combined_df['urgency'].unique().tolist())
                selected_urgency = st.selectbox('Urgency:', urgencies)
            
            # Filter the dataframe
            filtered_df = combined_df.copy()
            if selected_topic != 'All Topics':
                filtered_df = filtered_df[filtered_df['primary_labels_selected'] == selected_topic]
            if selected_resolution != 'All Resolutions':
                filtered_df = filtered_df[filtered_df['resolution_primary_labels'] == selected_resolution]
            if selected_urgency != 'All Urgency Levels':
                filtered_df = filtered_df[filtered_df['urgency'] == selected_urgency]
            
            # Display filtered data
            st.dataframe(filtered_df)
            
            # Create and display visualization
            if os.path.exists(plot_data_path):
                plot_df = pd.read_csv(plot_data_path)
                
                # Create visualization
                fig = px.bar(
                    plot_df,
                    x='Topic',
                    y='Count',
                    color='Resolution Status',
                    title=f'Topic Distribution in {len(combined_df["ID"].unique())} Reflections'
                )
                
                st.subheader("Topic Distribution")
                st.plotly_chart(fig)
            
        except Exception as e:
            st.error(f"Error displaying analysis: {str(e)}")
            print(f"Error details: {e}")

    def run_analysis(self, course_name, reflection_folder, selected_prompt=None, num_reflections=None, provider="openai", model=None):
        """Run the topic analysis on selected reflection data"""
        try:
            print(f"\nStarting analysis for {course_name}/{reflection_folder}")
            
            # Get reflection data
            reflection_path = os.path.join(
                self.fs_service.base_path, 
                course_name, 
                reflection_folder
            )
            print(f"Loading reflections from: {reflection_path}")
            
            # Process reflection data
            reflection_data = self.data_processor.load_reflection_data(reflection_path)
            if not reflection_data:
                st.error("No reflection data found.")
                return False
            print(f"Loaded {len(reflection_data)} reflections")
            
            # Run new analysis
            print(f"Running GPT analysis with prompt: {selected_prompt}")
            results = self.data_processor.analyze_topics(
                reflection_data,
                selected_prompt=selected_prompt,
                num_reflections=num_reflections,
                provider=provider,
                model=model
            )
            print(f"Got {len(results)} analysis results")
            expected_count = len(reflection_data[:num_reflections] if num_reflections else reflection_data)
            if len(results) != expected_count:
                raise ValueError(
                    f"Analysis returned {len(results)} results for {expected_count} reflections. "
                    "No results were saved. Check the analysis service and retry."
                )
            
            # Process results into dataframes
            print("Processing analysis results...")
            combined_df, counts_df, plot_df = self.process_analysis_results(
                results, 
                reflection_data[:num_reflections] if num_reflections else reflection_data
            )
            print(f"Processed into dataframes: {len(combined_df)} rows")
            if combined_df.empty:
                raise ValueError(
                    "Analysis produced no usable topic results. Check the selected prompt "
                    "and reflection data, then retry."
                )
            
            # Create results directory only after validating the new analysis.
            results_path = os.path.join(
                self.fs_service.base_path,
                course_name,
                reflection_folder,
                "results"
            )
            os.makedirs(results_path, exist_ok=True)
            
            # Save new analysis results
            self.save_analysis_results(
                course_name,
                reflection_folder,
                combined_df,
                counts_df,
                plot_df
            )
            
            # Update student objects with analysis results
            if hasattr(st.session_state, 'current_course'):
                print("Updating student objects with analysis results...")
                for _, row in combined_df.iterrows():
                    student_id = row['ID']
                    student = st.session_state.current_course.get_student_by_email(student_id)
                    if student:
                        ref_num = int(reflection_folder.replace('ref', ''))
                        # Add topic analysis to student's reflection data
                        if ref_num in student.reflection_data:
                            student.reflection_data[ref_num].update({
                                'topic_analysis': [{
                                    'primary_labels_selected': row['primary_labels_selected'],
                                    'resolution_primary_labels': row['resolution_primary_labels'],
                                    'urgency': row['urgency'],
                                }],
                                'reflection_summary': row.get('reflection_summary', ''),
                                'instructor_suggestions': row.get('instructor_suggestions', '')
                            })
                            print(f"Updated analysis for student: {student_id}")
            
            return True
            
        except Exception as e:
            st.error(f"Error running analysis: {str(e)}")
            print(f"Detailed error in run_analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def save_analysis_results(self, course_name, reflection_folder, combined_df, counts_df, plot_df):
        """Save analysis results to files"""
        try:
            results_path = os.path.join(
                self.fs_service.base_path,
                course_name,
                reflection_folder,
                "results"
            )
            os.makedirs(results_path, exist_ok=True)
            
            # Save DataFrames
            file_prefix = f"{course_name}_{reflection_folder}"
            
            # Format the exploded data for HTML display
            if not combined_df.empty:
                # Ensure all required columns are present
                required_columns = [
                    'ID', 
                    'primary_labels_selected',
                    'resolution_primary_labels',
                    'urgency',
                    'reflection_summary',
                    'instructor_suggestions'
                ]
                
                # Add any missing columns with default values
                for col in required_columns:
                    if col not in combined_df.columns:
                        combined_df[col] = ''
                
                # Validate ID consistency before saving
                self._validate_id_consistency(combined_df, course_name, reflection_folder)
                
                # Save the exploded data
                exploded_path = os.path.join(results_path, f"{file_prefix}_exploded.csv")
                combined_df.to_csv(exploded_path, index=False)
                print(f"Saved combined data: {len(combined_df)} rows to {exploded_path}")
                
                # Additional validation after saving
                self._validate_saved_file(exploded_path)
                
            else:
                print("No combined data to save")
                
            # Save counts and plot data
            if not counts_df.empty:
                counts_df.to_csv(os.path.join(results_path, f"{file_prefix}_counts.csv"), index=False)
                print(f"Saved counts data: {len(counts_df)} rows")
                
            if not plot_df.empty:
                plot_df.to_csv(os.path.join(results_path, f"{file_prefix}_plot_data.csv"), index=False)
                print(f"Saved plot data: {len(plot_df)} rows")
                
        except Exception as e:
            print(f"Error saving analysis results: {e}")
            raise

    def _validate_id_consistency(self, df, course_name, reflection_folder):
        """Validate that IDs in the DataFrame match expected formats and are consistent"""
        if 'ID' not in df.columns:
            print("WARNING: No ID column found in DataFrame")
            return
            
        print(f"VALIDATION: Checking ID consistency for {course_name}_{reflection_folder}")
        id_formats = {
            'email': 0,
            'four_digit': 0,
            'two_digit': 0,
            'other': 0
        }
        
        for idx, row in df.iterrows():
            id_value = str(row['ID']).strip()
            if '@' in id_value:
                id_formats['email'] += 1
            elif id_value.isdigit() and len(id_value) == 4:
                id_formats['four_digit'] += 1
            elif id_value.isdigit() and len(id_value) == 2:
                id_formats['two_digit'] += 1
            else:
                id_formats['other'] += 1
                print(f"VALIDATION WARNING: Unexpected ID format '{id_value}' at row {idx}")
        
        print(f"VALIDATION SUMMARY: {id_formats}")
        
        # Check if all IDs are the same format (which might indicate a transformation issue)
        non_zero_formats = [k for k, v in id_formats.items() if v > 0]
        if len(non_zero_formats) == 1 and non_zero_formats[0] == 'four_digit' and id_formats['four_digit'] > 10:
            print("VALIDATION WARNING: All IDs are 4-digit numbers - this might indicate ID transformation during processing")

    def _validate_saved_file(self, file_path):
        """Validate the saved exploded CSV file"""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            print(f"VALIDATION: Saved file {file_path} contains {len(df)} rows")
            if 'ID' in df.columns:
                unique_ids = df['ID'].nunique()
                total_rows = len(df)
                print(f"VALIDATION: {unique_ids} unique IDs in {total_rows} total rows")
                
                # Sample a few IDs for verification
                sample_ids = df['ID'].head(3).tolist()
                print(f"VALIDATION: Sample IDs from saved file: {sample_ids}")
            
        except Exception as e:
            print(f"Error validating saved file: {e}")

def get_categorized_prompts(prompts_dir):
    """
    Categorize prompts and get modification times for sorting.
    
    Returns:
        dict: {category: [(filename, display_name, mod_time), ...]}
    """
    import os
    
    if not os.path.exists(prompts_dir):
        return {}
    
    categories = {
        'Topic Classification': []
    }
    
    try:
        for filename in os.listdir(prompts_dir):
            if filename.endswith('.json') and not filename.startswith('.'):
                file_path = os.path.join(prompts_dir, filename)
                mod_time = os.path.getmtime(file_path)
                display_name = filename.replace('.json', '').replace('_', ' ').title()
                
                # Categorize based on filename
                if 'topic' in filename.lower() and 'classification' in filename.lower():
                    categories['Topic Classification'].append((filename, display_name, mod_time))
                else:
                    # Default to Topic Classification for other topic-related prompts
                    categories['Topic Classification'].append((filename, display_name, mod_time))
        
        # Sort each category by modification time (most recent first)
        for category in categories:
            categories[category].sort(key=lambda x: x[2], reverse=True)
    
    except Exception as e:
        print(f"Error processing prompts: {e}")
    
    return categories

def get_most_recent_prompt_by_category(categorized_prompts):
    """
    Get the most recently edited prompt from each category.
    
    Returns:
        dict: {category: (filename, display_name, mod_time)} or None if empty
    """
    most_recent = {}
    for category, prompts in categorized_prompts.items():
        if prompts:  # If category has prompts
            most_recent[category] = prompts[0]  # First item is most recent due to sorting
    return most_recent

def run_topic_analysis_tab(is_workflow=False):
    """Main entry point for topic analysis"""
    # Initialize services with proper base path
    base_path = os.path.join("application", "model", "reflections")
    fs_service = FileSystemService(base_path=base_path)
    data_processor = DataProcessingService()
    state_manager = StateManager()
    
    # Create topic analysis manager
    topic_manager = TopicAnalysisManager(fs_service, data_processor, state_manager)
    
    # Get current course and reflection
    course_name = st.session_state.get('current_course_folder')
    reflection_folder = st.session_state.get('current_reflection_folder')
    
    if not course_name or not reflection_folder:
        st.warning("Please select a course and reflection first.")
        return
    
    # Add analysis controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Topic Analysis for {course_name} - {reflection_folder}")
        providers = ["openai", "groq"]
        default_provider = "groq" if os.getenv("GROQ_API_KEY") and not os.getenv("OPENAI_API_KEY") else "openai"
        provider = st.selectbox(
            "AI provider", providers, index=providers.index(default_provider),
            format_func=lambda value: "Groq" if value == "groq" else "OpenAI",
            key="topic_analysis_provider"
        )
        model = st.text_input(
            "Model", value=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL) if provider == "groq" else "gpt-4o",
            key=f"topic_analysis_model_{provider}",
            help="Enter a chat model ID supported by your selected provider."
        ).strip()
        key_name = "GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"
        has_api_key = bool(os.getenv(key_name, "").strip())
        if not has_api_key:
            st.warning(f"Set {key_name} in your server environment to use this provider.")
        
        # Enhanced prompt selection with categorization
        prompts_dir = os.path.join("application", "model", "prompts")
        categorized_prompts = get_categorized_prompts(prompts_dir)
        most_recent_by_category = get_most_recent_prompt_by_category(categorized_prompts)
        
        # Analysis type selection (SSM Analysis removed)
        analysis_type = "Topic Classification"
        
        # Get prompts for selected category
        available_prompts_in_category = categorized_prompts.get(analysis_type, [])
        
        if available_prompts_in_category:
            # Create list of filenames and display names for the selectbox
            prompt_filenames = [prompt[0] for prompt in available_prompts_in_category]
            prompt_display_names = [prompt[1] for prompt in available_prompts_in_category]
            
            # Find the default index (most recent)
            default_prompt = most_recent_by_category.get(analysis_type)
            default_index = 0  # Default to first (most recent) if available
            if default_prompt:
                try:
                    default_index = prompt_filenames.index(default_prompt[0])
                except ValueError:
                    default_index = 0
            
            # Show modification time of current default
            if default_prompt:
                from datetime import datetime
                mod_time_str = datetime.fromtimestamp(default_prompt[2]).strftime("%Y-%m-%d %H:%M")
                st.info(f"📅 Most recent {analysis_type.lower()} prompt: **{default_prompt[1]}** (edited: {mod_time_str})")
            
            selected_prompt = st.selectbox(
                f"Select {analysis_type} Prompt:",
                prompt_filenames,
                format_func=lambda x: next(name for filename, name, _ in available_prompts_in_category if filename == x),
                index=default_index,
                help=f"Choose from available {analysis_type.lower()} prompts. The most recently edited prompt is selected by default."
            )
        else:
            st.warning(f"No {analysis_type.lower()} prompts found in the prompts directory.")
            selected_prompt = None
        
        # Add reflection count selection
        num_reflections = st.number_input(
            "Number of reflections to analyze (0 for all):",
            min_value=0,
            value=0,
            help="Select how many reflections to analyze. Use 0 to analyze all reflections."
        )
        
    with col2:
        if st.button("Run New Analysis", key="run_new_analysis", disabled=not has_api_key or not model):
            with st.spinner("Running topic analysis..."):
                # Convert num_reflections=0 to None for analyzing all reflections
                analysis_count = None if num_reflections == 0 else num_reflections
                
                if topic_manager.run_analysis(
                    course_name, 
                    reflection_folder,
                    selected_prompt=selected_prompt,
                    num_reflections=analysis_count,
                    provider=provider,
                    model=model
                ):
                    st.success("Analysis complete!")
                    
    # Add tabs for analysis and class aggregates
    tabs = st.tabs(["Topic Analysis", "Class Aggregates"])
    
    with tabs[0]:
        topic_manager.display_analysis(course_name, reflection_folder)
    
    with tabs[1]:
        st.header("Class Aggregates: Emotions Bar Chart and Table")
        # Load the reflection CSV
        reflection_path = os.path.join(
            base_path, course_name, reflection_folder, f"{course_name}_{reflection_folder}.csv"
        )
        if not os.path.exists(reflection_path):
            st.warning(f"Reflection CSV not found at: {reflection_path}")
            return
        df = pd.read_csv(reflection_path)
        # Find the column for emotions (case-insensitive match)
        emotion_col = None
        for col in df.columns:
            if isinstance(col, str) and col.strip().lower().startswith("how do you feel about the course so far?"):
                emotion_col = col
                break
        if not emotion_col:
            st.warning("Could not find the emotions column in the reflection data.")
            return
        # Extract and count emotions
        emotion_counts = {}
        student_emotions = []
        for idx, row in df.iterrows():
            student_id = row.get('ID', f'Row {idx+1}')
            emotions_raw = row.get(emotion_col, '')
            if pd.isna(emotions_raw):
                continue
            emotions = [e.strip() for e in str(emotions_raw).split(',') if e.strip()]
            for emotion in emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            student_emotions.append({'Student': student_id, 'Emotions': ', '.join(emotions)})
        # Bar chart
        if emotion_counts:
            emotion_df = pd.DataFrame(list(emotion_counts.items()), columns=['Emotion', 'Count'])
            fig = px.bar(emotion_df, x='Emotion', y='Count', title='Emotions Reported by Students')
            st.plotly_chart(fig)
        else:
            st.info("No emotions data found to display.")
        # Table of student emotions
        if student_emotions:
            st.subheader("Student-Reported Emotions Table")
            st.dataframe(pd.DataFrame(student_emotions))
        else:
            st.info("No student emotions data found.")
