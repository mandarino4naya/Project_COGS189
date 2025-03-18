# Imports
import os
import pandas as pd

# Define the parent "results" folder
root_folder = 'results'

# Subfolders to process
subfolders = [1, 2, 3, 4]

# Files to process in each subfolder
files_to_clean = ['baseline_eeg_data.csv', 'eeg_data.csv']

for subfolder in subfolders:
    for filename in files_to_clean:
        # Build the full path to the CSV
        file_path = os.path.join(root_folder, str(subfolder), filename)
        
        # Read the CSV
        data = pd.read_csv(file_path)

        # --- Begin cleaning steps ---
            # Drop channels 8-20, timestamp and 22-23
            # new timestamp = channel 21
            # new channels 1-8 are 0-7
        
        channels_to_drop = [f'Channel_{i}' for i in range(8, 21)]
        data_clean = data.drop(channels_to_drop, axis=1)

        more_to_drop = [f'Channel_{i}' for i in range(22, 24)]
        data_clean = data_clean.drop(more_to_drop, axis=1)

        data_clean = data_clean.drop('Timestamp', axis=1)

        # Renaming and rearranging

        data_clean = data_clean.rename(columns={'Channel_21': 'Timestamp'})
        rename_map = {
            f'Channel_{i}': f'Channel_{i+1}' 
            for i in range(8)
        }
        data_clean = data_clean.rename(columns=rename_map)

        new_order = ['Timestamp'] + [f'Channel_{i}' for i in range(1, 9)]
        data_clean = data_clean[new_order]

        # --- End cleaning steps ---

        # Save the cleaned DataFrame to a new file
        cleaned_filename = os.path.splitext(filename)[0] + '_cleaned.csv'
        cleaned_file_path = os.path.join(root_folder, str(subfolder), cleaned_filename)
        data_clean.to_csv(cleaned_file_path, index=False)
        
        print(f'Cleaned file saved to: {cleaned_file_path}')
