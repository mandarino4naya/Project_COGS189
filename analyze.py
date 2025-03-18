#### Imports ####

import numpy as np
import pandas as pd
import mne

# from mne import Annotations
# from mne.time_frequency import psd_array_welch

#### Load CSV into pd df ####
path = 'results/4/' # change to use other recordings
data = pd.read_csv(path + 'eeg_data_cleaned.csv', 
                   skiprows=0)
sfreq = 250. # Sampling frequency

#### Stimulus log to events processing ####
t0_eeg = data['Timestamp'].iloc[0] # Save t0 before dropping
data = data.drop('Timestamp', axis=1) # drop timestamp
stim_log = pd.read_csv(path + 'stimulus_log_cleaned.csv')

#### Event markers ####
events_list = []
for i, row in stim_log.iterrows():
    stim_time = row['Timestamp']  # absolute time of stimulus
    marker    = row['Marker']     # e.g. 1, 2, 3...

    # Convert to 'seconds since EEG start'
    onset_sec = stim_time - t0_eeg  
    # Convert to sample index
    onset_samp = int(onset_sec * sfreq)

    # MNE event array = [onset_sample, 0, event_id]
    events_list.append([onset_samp, 0, marker])

events = np.array(events_list, dtype=int)

# #### Annotations ####
# annots_list = []
# for i, row in stim_log.iterrows():
#     stim_time = row['Timestamp']
#     onset_sec = stim_time - t0_eeg
#     duration  = 4.0  # each word shown for 4 s
#     desc      = f"{row['Word']} ({row['Color']})"
#     annots_list.append((onset_sec, duration, desc))

#### EEG Channels processing ####
ch_names = ['Fp1', 'Fp2', 'O1', 'O2', 'T5', 'T6', 'P3', 'P4'] # def channel names used in exp
ch_types = ['eeg'] * len(ch_names) # convert all channels to eeg
montage = mne.channels.make_standard_montage('standard_1020') # Create 10-20 international standard
info = mne.create_info(ch_names = ch_names, sfreq = sfreq, ch_types=ch_types)
raw = mne.io.RawArray(data.transpose(), info)
raw.set_montage(montage) # forgot to set it befo

#TODO: Simple preprocessing
original_raw = raw.copy() # save original file

raw.notch_filter(freqs=[60, 120]) # notch filter freq for US powerline
raw.filter(l_freq=1., h_freq=45.) # high pass & low pass


# fig = raw.plot_sensors(show_names=True) # doesnt work
# montage.plot(show=True)  # 2D # doesnt work

#TODO: Power plot --> doesnt work
# raw.compute_psd(fmax=50).plot(picks="data", exclude="bads", amplitude=False)
# raw.plot(duration=5, n_channels=8)

# # Plot annotations + eeg
# annotations = Annotations(onset   =[a[0] for a in annots_list],
#                           duration=[a[1] for a in annots_list],
#                           description=[a[2] for a in annots_list],
#                           orig_time=raw.info['meas_date'])  # or None if purely relative
# raw.set_annotations(annotations)
# raw.plot(
#     n_channels=8,
#     scalings='auto',
#     start=0, 
#     duration=10.0, 
#     block=True
# )

# Plot event markers + eeg
# raw.plot(
#     events=events,        # provide your event array
#     n_channels=8,         # number of channels to display at once
#     scalings='auto',      # automatically scale the signals
#     start=0,              # start time (in seconds) for the plot
#     duration=10.0,        # how many seconds of data to show
#     block=True            # pause execution until the plot window is closed
# )

#TODO: Epoching ADD BASELINE REF
# epochs = mne.Epochs(raw, events, tmin=-0.25, tmax=4)
# print(epochs)
# epochs.plot(
#     n_epochs=10, 
#     events=events,
#     n_channels=8,         # number of channels to display at once
#     scalings='auto',      # automatically scale the signals
#     block=True   
# )

#TODO: # Welch

# # Define parameters
# fmin, fmax = 13., 30.  # Beta range
# n_fft = 256       # FFT length
# n_overlap = 128   # Number of samples to overlap
# window_type = 'hamming'  # Window function used on each segment

# processed = raw.get_data()
# # Calculate PSD in the beta band
# psds, freqs = psd_array_welch(
#     processed,             # Your data array
#     sfreq=sfreq,           # Sampling frequency
#     fmin=fmin,             # Min frequency of interest
#     fmax=fmax,             # Max frequency of interest
#     n_fft=n_fft,           # FFT length (>= n_per_seg)
#     n_overlap=n_overlap,   # Overlap between segments
#     n_per_seg=None,        # Defaults to n_fft if None
#     average='mean',        # Average type ('mean', 'median', or None for un-aggregated)
#     window=window_type,    # Which window function to use
#     remove_dc=True,        # Subtract mean before segmenting
#     output='power',        # Return power or complex values
#     verbose=True           # Control logging verbosity
# )

# # 'psds' shape: (n_channels, n_freqs) unless average=None
# # 'freqs' shape: (n_freqs,)

# # Plot the PSD for each channel (log scale)
# plt.figure(figsize=(8, 4))
# for ch_idx in range(psds.shape[0]):
#     plt.semilogy(freqs, psds[ch_idx], label=f'Chan {ch_idx+1}')
# plt.xlabel('Frequency (Hz)')
# plt.ylabel('PSD (Power)')
# plt.title('Beta Band (13-30 Hz) Power Spectral Density')
# plt.legend(loc='best')
# plt.show()

# Some functionality we might need below for artifacts (?)

# Artifact removal
# ica = mne.preprocessing.ICA(n_components=10, method='fastica', random_state=97)
# ica.fit(raw)