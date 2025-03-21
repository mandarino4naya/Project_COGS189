# Imports
import os
import pandas as pd

# Define the parent "results" folder
root_folder = 'results'

# Subfolders to process
subfolders = [1, 2, 3, 4]

# Files to process in each subfolder
filename = 'stimulus_log.csv'

for subfolder in subfolders:
    # Build the full path to the CSV
        file_path = os.path.join(root_folder, str(subfolder), filename)
        
        # Read the CSV
        stim_log = pd.read_csv(file_path)

        # --- Begin cleaning steps ---

        # Define hex-->color
        color_map = {
            '#F1E05C': 'yellow',
            '#A6D5FF': 'blue'
        }
        # Replace
        stim_log['Color'] = stim_log['Color'].map(color_map)

        # --- End cleaning steps ---

        # Save the cleaned DataFrame to a new file
        cleaned_filename = os.path.splitext(filename)[0] + '_cleaned.csv'
        cleaned_file_path = os.path.join(root_folder, str(subfolder), cleaned_filename)
        stim_log.to_csv(cleaned_file_path, index=False)
        
        print(f'Cleaned file saved to: {cleaned_file_path}')