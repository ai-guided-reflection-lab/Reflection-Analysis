import pandas as pd
import os


class LabelCounter:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        
        # Dynamically find relevant columns
        self.labels_col = next((col for col in self.df.columns 
                              if any(term in col.lower() for term in ['label', 'topic']) 
                              and 'explain' not in col.lower()), None)
        
        self.resolved_labels_col = next((col for col in self.df.columns 
                                       if 'resolution' in col.lower() 
                                       and 'explain' not in col.lower()), None)
        
        if not self.labels_col or not self.resolved_labels_col:
            raise ValueError("Required columns not found in the CSV file")
    
    def process_columns(self):
        """Clean and process the columns"""
        if self.labels_col in self.df.columns:
            self.df[self.labels_col] = self.df[self.labels_col].astype(str).str.strip()
        
        if self.resolved_labels_col in self.df.columns:
            self.df[self.resolved_labels_col] = self.df[self.resolved_labels_col].astype(str).str.strip()
    
    def calculate_counts(self):
        """Calculate the counts for each combination"""
        if not all(col in self.df.columns for col in [self.labels_col, self.resolved_labels_col]):
            self.counts_df = pd.DataFrame(columns=['Label', 'Resolution', 'Count'])
            return
            
        # Group by both columns and count occurrences
        grouped = self.df.groupby([self.labels_col, self.resolved_labels_col]).size().reset_index()
        grouped.columns = ['Label', 'Resolution', 'Count']
        self.counts_df = grouped
    
    def save_counts_to_csv(self, output_path):
        """Save the counts to a CSV file"""
        if hasattr(self, 'counts_df'):
            self.counts_df.to_csv(output_path, index=False)


# Function to process a label file and calculate counts
def process_label_file(file_name):
    file_path = os.path.join('data', 'reflections', 'results', file_name)
    counter = LabelCounter(file_path)

    # Process the columns (ensure strings are stripped)
    counter.process_columns()

    # Calculate counts
    df_counts = counter.calculate_counts()

    # Save the counts DataFrame to CSV
    counts_output_path = os.path.join('data', 'reflections', 'results', f'counts_{file_name}')
    counter.save_counts_to_csv(counts_output_path)
