# Imports
import numpy as np
import pandas as pd
from brainflow.data_filter import DataFilter

# Try reading saved data
restored_data = DataFilter.read_file('results/1/eeg_data.csv')
restored_df = pd.DataFrame(np.transpose(restored_data))
print('Data From the File')
print(restored_df.head(10))

# in read_file
# raise BrainFlowError('unable to read file', res)
# brainflow.exit_codes.BrainFlowError: INVALID_ARGUMENTS_ERROR:13 unable to read file