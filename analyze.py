#### Imports ####
import numpy as np
import pandas as pd
import mne
from scipy.stats import ttest_ind
import seaborn as sns
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

# Plot event markers + eeg
raw.plot(
    events=events,        # provide your event array
    n_channels=8,         # number of channels to display at once
    scalings='auto',      # automatically scale the signals
    start=0,              # start time (in seconds) for the plot
    duration=10.0,        # how many seconds of data to show
    block=True            # pause execution until the plot window is closed
)

#### Epoching ADD BASELINE REF ####
event_id = {'yellow': 1, 'blue': 2}
epochs = mne.Epochs(
    raw, 
    events,
    event_id=event_id, 
    tmin=-0.25, 
    tmax=4.,
    baseline=(None, 0), 
    reject_by_annotation=True
)
epochs_yellow = epochs['yellow']  # all epochs with code=1
epochs_blue   = epochs['blue']    # all epochs with code=2

#### Welch ####

# Welch PSD
psd_yellow_obj = epochs_yellow.compute_psd(
    method='welch',  # or 'multitaper'
    fmin=1,
    fmax=45,
    n_fft=512,
    n_overlap=256
)
# Access the PSD data and frequencies from the returned object:
psd_yellow = psd_yellow_obj.data  # shape: (n_epochs, n_channels, n_freqs)
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
beta_power_yellow = psd_yellow[:, :, beta_mask].mean(axis=-1)  # shape: (n_epochs, n_channels)
beta_power_blue   = psd_blue[:, :, beta_mask].mean(axis=-1)    # shape: (n_epochs, n_channels)

# Optionally, average across channels:
avg_beta_yellow = beta_power_yellow.mean(axis=1)  # per-epoch average
avg_beta_blue   = beta_power_blue.mean(axis=1)

# Compare with a t-test
t_stat, p_val = ttest_ind(avg_beta_yellow, avg_beta_blue)

print(f"T-test (yellow vs. blue), t={t_stat:.3f}, p={p_val:.5f}")

plt.figure(figsize=(8, 6))

# Plot histograms for both groups
sns.histplot(avg_beta_yellow, color='red', kde=True, label='Yellow', stat='density', linewidth=0)
sns.histplot(avg_beta_blue, color='blue', kde=True, label='Blue', stat='density', linewidth=0)


# Labels and title
plt.xlabel('Beta Value')
plt.ylabel('Density')
plt.title('Distribution of Beta Values for Yellow and Blue')

legend = plt.legend()

# Show plot
plt.show()


# For alpha waves(switch beta mask to to 8 and 12): 
# outlier_threshold = 100
# avg_beta_blue_clean = avg_beta_blue[avg_beta_blue <= outlier_threshold]

# # Compare with a t-test
# t_stat, p_val = ttest_ind(avg_beta_yellow, avg_beta_blue)

# print(f"T-test (yellow vs. blue), t={t_stat:.3f}, p={p_val:.5f}")

# plt.figure(figsize=(8, 6))

# # Plot histograms for both groups
# sns.histplot(avg_beta_yellow, color='red', kde=True, label='Yellow', stat='density', linewidth=0)
# sns.histplot(avg_beta_blue_clean, color='blue', kde=True, label='Blue', stat='density', linewidth=0,)  # Adjusting KDE bandwidth

# # Labels and title
# plt.xlabel('Alpha Value')
# plt.ylabel('Density')
# plt.title('Distribution of Alpha Values for Yellow and Blue')

# # Set x-axis limits
# plt.xlim(0, 30)

# # Show the legend
# plt.legend()

# #Show plot

# plt.show()

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

# Choose a time point (in seconds) at which to plot the topomap
time_point = 0.3

# Find the index corresponding to this time point
idx = np.argmin(np.abs(diff_evoked.times - time_point))

# Extract the data for each channel at that time
data_at_time = diff_evoked.data[:, idx]  # shape (n_channels,)

# Create a figure and axis for the topomap
fig, ax = plt.subplots(1, 1)

im, cn = mne.viz.plot_topomap(
    data_at_time,            # data values for each channel (1D array)
    diff_evoked.info,        # info object from which x,y sensor positions are inferred
    ch_type='eeg',           # channel type to plot
    sensors=True,            # display sensor markers (default: black circles)
    names=diff_evoked.info['ch_names'],  # sensor names to show; optional
    mask=None,               # no masking (set to a boolean array of length n_channels to highlight channels)
    mask_params=dict(marker='o', markerfacecolor='w', markeredgecolor='k',
                     linewidth=0, markersize=4),
    contours=6,              # draw 6 contour lines
    outlines='head',         # use the default head outline
    sphere='auto',           # automatically determine sphere parameters from digitization
    image_interp='cubic',    # interpolation method for image
    extrapolate='auto',      # automatically extrapolate outside sensor locations
    border='mean',           # border extrapolation value
    res=64,                  # resolution of the image (64x64 pixels)
    size=1,                  # size of the subplot in inches
    cmap='RdBu_r',           # colormap; you can change this as needed
    vlim=(None, None),       # let the function set the color limits automatically
    cnorm=None,              # use standard normalization (unless you want to customize)
    axes=ax,                 # plot into the provided axes
    show=True                # show the figure immediately
)
plt.show()

## TFRs ## --> #TODO fix plotting this does smth weird... (multiple frames, can it be a GIF?)
# tfr_yellow_avg = tfr_yellow.average()
# tfr_yellow_avg.plot(baseline=(None, 0), mode='logratio',
#                       title='Time-Frequency Representation (yellow)')

# tfr_blue_avg = tfr_blue.average()
# tfr_blue_avg.plot(baseline=(None, 0), mode='logratio',
#                       title='Time-Frequency Representation (blue)')