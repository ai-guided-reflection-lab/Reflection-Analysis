import os
import json
import pandas as pd
import datetime

__all__ = ['JSONViewer', 'JSONSaver']

class JSONViewer:
    def __init__(self, file_path=None):
        """
        Initializes JSONViewer with an optional file path.
        Loads JSON data if a file path is provided.
        """
        self.json_data = None
        if file_path:
            self.file_path = file_path
            self.json_data = self.load_json()

    def load_json(self):
        """Load JSON data from the specified file path."""
        with open(self.file_path) as file:
            return json.load(file)

    def format_json(self, data, indent_level=0, is_top_level=True):
        """Recursively format JSON data into a string."""
        indent = "    " * indent_level  # Create indentation
        formatted_string = ""

        if isinstance(data, dict):
            for key, value in data.items():
                # Add a separator for top-level sections
                if is_top_level:
                    formatted_string += f"{indent}-------\n"
                    
                formatted_string += f"{indent}{key}:\n"
                formatted_string += self.format_json(value, indent_level + 1, is_top_level=False)  # Recur for value

            # Add a separator after the entire dictionary
            if is_top_level:
                formatted_string += f"{indent}-------\n"

        elif isinstance(data, list):
            for index, item in enumerate(data):
                # Add a separator for top-level sections
                if is_top_level:
                    formatted_string += f"{indent}-------\n"

                formatted_string += f"{indent}Item {index}:\n"
                formatted_string += self.format_json(item, indent_level + 1, is_top_level=False)  # Recur for item

            # Add a separator after the entire list
            if is_top_level:
                formatted_string += f"{indent}-------\n"

        else:
            formatted_string += f"{indent}{data}\n"  # Base case for non-iterable types

        return formatted_string

    def display_json(self):
        """Display the JSON data as a formatted string."""
        formatted_string = self.format_json(self.json_data)
        return(formatted_string)

class JSONSaver:
    def __init__(self, timestamp, prompt_file_name, ref_path):
        self.timestamp = timestamp
        self.prompt_file_name = prompt_file_name
        self.ref_path = ref_path
    def save_json_to_csv(self, json_list, file_name, directory):
        """
        Converts a list of string-formatted JSON objects to CSV format and saves it to the specified directory.
        """
        # Check if the input is a non-empty list
        if not isinstance(json_list, list) or not json_list:
            print("The provided JSON list is empty or not a list.")
            return

        # Parse each JSON string into a dictionary
        parsed_json_list = []
        for json_str in json_list:
            try:
                parsed_json = json.loads(json_str)  # Convert string to dictionary
                parsed_json_list.append(parsed_json)
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {json_str}")
                return

        # Convert the list of dictionaries to a DataFrame
        output_df = pd.DataFrame(parsed_json_list)
        
        # Using the ref_path, create a DataFrame from the original reflections csv
        ref_df = pd.read_csv(self.ref_path)
        print("Original CSV columns and data:")
        print(ref_df.head())
        
        # Create a Reflection object from the first row to get questions
        first_reflection = Reflection(ref_df.iloc[0])
        questions = first_reflection.questions
        
        print("Original columns:", ref_df.columns.tolist())
        print("Questions from reflection:", questions)
        
        # Rename the reflection columns with actual questions
        reflection_columns = [col for col in ref_df.columns if col.startswith('reflection_')]
        # Map each reflection_X column to its corresponding question
        rename_dict = {}
        for i, col in enumerate(reflection_columns):
            if i < len(questions):
                rename_dict[col] = questions[i]
        
        print("Rename mapping:", rename_dict)
        ref_df = ref_df.rename(columns=rename_dict)
        
        print("Columns after rename:", ref_df.columns.tolist())
        
        # Combine the reflections and the final output
        final_df = ref_df.merge(output_df, left_on='ID', right_on='id', how='inner')
        
        # Ensure the renamed columns are preserved after merge
        for old_col, new_col in rename_dict.items():
            if old_col in final_df.columns:
                final_df = final_df.rename(columns={old_col: new_col})
        
        # Drop the redundant id column if it exists
        if 'id' in final_df.columns:
            final_df = final_df.drop('id', axis=1)

        # Create the output directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        # Define the full path for the CSV file
        csv_file_path = os.path.join(directory, f"{file_name}_{self.prompt_file_name}_{self.timestamp}.csv")

        # Save DataFrame to CSV
        final_df.to_csv(csv_file_path, index=False)

        print(f"CSV file saved at: {csv_file_path}")
# Example usage
if __name__ == "__main__":
    json_file_path = "prompts/topic_prompt.json"  # Replace with your JSON file path
    viewer = JSONViewer(json_file_path)
    viewer.display_json()
