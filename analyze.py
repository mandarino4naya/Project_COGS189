#### Imports ####
import numpy as np
import pandas as pd
import mne
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt

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
    stim_time = row['Timestamp']  # absolute time
    onset_sec = stim_time - t0_eeg  # seconds since start of EEG
    onset_samp = int(onset_sec * sfreq)  # convert to sample index

    # Assign color code: e.g. 1 = yellow, 2 = blue
    if row['Color'] == 'yellow':
        color_code = 1
    elif row['Color'] == 'blue':
        color_code = 2

    events_list.append([onset_samp, 0, color_code])
events = np.array(events_list, dtype=int)

#### EEG Channels processing ####
ch_names = ['Fp1', 'Fp2', 'O1', 'O2', 'T5', 'T6', 'P3', 'P4'] # def channel names used in exp
ch_types = ['eeg'] * len(ch_names) # convert all channels to eeg
montage = mne.channels.make_standard_montage('standard_1020') # Create 10-20 international standard
info = mne.create_info(ch_names = ch_names, sfreq = sfreq, ch_types=ch_types)
raw = mne.io.RawArray(data.transpose(), info)
raw.set_montage(montage)

#### Simple preprocessing ####
raw.notch_filter(freqs=[60, 120]) # notch filter freq for US powerline
raw.filter(l_freq=1., h_freq=45.) # high pass & low pass

# Plot event markers + filtered eeg
raw.plot(
    events=events,        # provide your event array
    n_channels=8,         # number of channels to display at once
    scalings='auto',      
    start=0,              # start time (in seconds) for the plot
    duration=10.0,        # how many seconds of data to show
    block=True            # pause execution until the plot window is closed
)

#### Epoching ####
event_id = {'yellow': 1, 'blue': 2}
epochs = mne.Epochs(
    raw, 
    events,
    event_id=event_id, 
    tmin=-0.3, 
    tmax=4.,
    baseline=(-0.3, 0), 
    reject_by_annotation=True
)
epochs_yellow = epochs['yellow']  # all epochs with code=1
epochs_blue   = epochs['blue']    # all epochs with code=2

print(epochs_yellow)
print(epochs_blue)

#### Welch ####

# Welch PSD
psd_yellow_obj = epochs_yellow.compute_psd(
    method='welch',
    fmin=1,
    fmax=45,
    n_fft=512,
    n_overlap=256
)
# Access the PSD data and frequencies from the returned object
psd_yellow = psd_yellow_obj.data
freqs = psd_yellow_obj.freqs

psd_blue_obj = epochs_blue.compute_psd(
    method='welch',
    fmin=1,
    fmax=45,
    n_fft=512,
    n_overlap=256
)
psd_blue = psd_blue_obj.data

# psds_yellow.shape => (n_epochs, n_channels, n_freqs)
beta_mask = (freqs >= 13) & (freqs <= 30)

# Average the beta power for each epoch and channel:
beta_power_yellow = psd_yellow[:, :, beta_mask].mean(axis=-1)
beta_power_blue   = psd_blue[:, :, beta_mask].mean(axis=-1)

# Optionally, average across channels:
avg_beta_yellow = beta_power_yellow.mean(axis=1)  # per-epoch average
avg_beta_blue   = beta_power_blue.mean(axis=1)

# Compare with a t-test
t_stat, p_val = ttest_ind(avg_beta_yellow, avg_beta_blue)
print(f"T-test (yellow vs. blue), t={t_stat:.3f}, p={p_val:.5f}")

#### Wavelets ####
freqs = np.arange(2, 45, 1)
n_cycles = freqs / 2.  # or a fixed number like 7

tfr_yellow = epochs_yellow.compute_tfr(method='morlet', freqs=freqs, n_cycles=n_cycles, return_itc=False)
tfr_blue = epochs_blue.compute_tfr(method='morlet', freqs=freqs, n_cycles=n_cycles, return_itc=False)

# tfr_yellow.data.shape => (n_epochs, n_channels, n_freqs, n_times)
beta_mask = (freqs >= 13) & (freqs <= 30)
time_mask = (tfr_yellow.times >= 0) & (tfr_yellow.times <= 4.0)

# Average in freq/time
beta_yellow = tfr_yellow.data[:, :, beta_mask, :][:, :, :, time_mask].mean(axis=(2,3))
beta_blue   = tfr_blue.data[:, :, beta_mask, :][:, :, :, time_mask].mean(axis=(2,3))

# Optionally average across channels => shape (n_epochs,)
avg_beta_yellow = beta_yellow.mean(axis=1)
avg_beta_blue   = beta_blue.mean(axis=1)

# Stats
t_stat, p_val = ttest_ind(avg_beta_yellow, avg_beta_blue)
print(f"TFR-based beta comparison: t={t_stat:.3f}, p={p_val:.5f}")

#### VISUALS ####

## Evoked ##
evoked_yellow = epochs_yellow.average()
evoked_blue = epochs_blue.average()
evoked_yellow.plot()
evoked_blue.plot()

## Topomap ##
diff_evoked = mne.combine_evoked([evoked_yellow, -evoked_blue], weights='equal')

# Choose a time point (in seconds) at which to plot the topomap: 0.3, 2, 4
time_point = 4

# Find the index corresponding to this time point
idx = np.argmin(np.abs(diff_evoked.times - time_point))

# Extract the data for each channel at that time
data_at_time = diff_evoked.data[:, idx]

# Create a figure and axis for the topomap
fig, ax = plt.subplots(1, 1)

im, cn = mne.viz.plot_topomap(
    data_at_time,            
    diff_evoked.info,        
    ch_type='eeg',           
    sensors=True,            
    names=diff_evoked.info['ch_names'],  # sensor names to show
    mask=None,               # no masking
    mask_params=dict(marker='o', markerfacecolor='w', markeredgecolor='k',
                     linewidth=0, markersize=4),
    contours=6,              
    outlines='head',         
    sphere='auto',           
    image_interp='cubic',    # interpolation method for image
    extrapolate='auto',      
    border='mean',           # border extrapolation value
    res=64,                  # resolution of the image (64x64 pixels)
    size=1,                  # size of the subplot in inches
    cmap='RdBu_r',           # colormap; you can change this as needed
    vlim=(None, None),       
    cnorm=None,              
    axes=ax,                 
    show=True                
)
plt.show()