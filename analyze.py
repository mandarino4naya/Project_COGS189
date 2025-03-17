# Imports
import matplotlib.pyplot as plt
import pandas as pd 
import mne
from mne.time_frequency import psd_array_welch

# Load CSV and read into raw object
path = 'results/4/' # change to use other recordings
data = pd.read_csv(path + 'eeg_data.csv', 
                   skiprows=0, usecols=[*range(0, 24)]) 
ch_names = ['CH 1', 'CH 2', 'CH 3', 'CH 4', 'CH 5', 'CH 6', 'CH 7', 'CH 8', 'CH 9',
            'CH 10', 'CH 11', 'CH 12', 'CH 13', 'CH 14', 'CH 15', 'CH 16', 'CH 17',
            'CH 18', 'CH 19', 'CH 20', 'CH 21', 'CH 22', 'CH 23', 'CH 24']

sfreq = 250. # Sampling frequency
info = mne.create_info(ch_names = ch_names, sfreq = sfreq)
raw = mne.io.RawArray(data.transpose(), info)

#TODO: figure out which channels we using from 10/20 and our setup

# Create 24 channel montage 10-20 international standard
# montage = mne.channels.make_standard_montage('standard_1020')

# Pick only channels that are used in Cyton OpenBCI
            
# ch_names = ['FP1', 'Fp2', 'F7', 'F3', 'F4', 'F8', 'T7', 'C3', 'C4', 'T8', 'P7', 'P3', 'P4', 'P8', 'O1', 'O2']
# ch_types = ['eeg'] * 16
# info = mne.create_info(
# ch_names=ch_names,
# sfreq=250,
# ch_types=ch_types)
# info.set_montage('standard_1020', match_case=False)

# Plotting raw signal
montage = mne.channels.make_standard_montage('standard_1020')
raw.set_channel_types({ch: 'eeg' for ch in raw.ch_names})
raw.crop(tmax=60).load_data()

#TODO: Simple preprocessing
original_raw = raw.copy() # save original file

raw.notch_filter(freqs=[60, 120]) # notch filter freq for US powerline
raw.filter(l_freq=1., h_freq=45.) # high pass & low pass
raw.set_eeg_reference('average') #TODO: set ref (prob spec channel for us)

# See result
# raw.plot_psd(fmin=13., fmax=30.) # see how much beta power we have in raw
# raw.plot(duration=10.) # see just 10s of signal
# plt.show()

# Welch

# Define parameters
fmin, fmax = 13., 30.  # Beta range
n_fft = 256       # FFT length
n_overlap = 128   # Number of samples to overlap
window_type = 'hamming'  # Window function used on each segment

processed = raw.get_data()
# Calculate PSD in the beta band
psds, freqs = psd_array_welch(
    processed,             # Your data array
    sfreq=sfreq,           # Sampling frequency
    fmin=fmin,             # Min frequency of interest
    fmax=fmax,             # Max frequency of interest
    n_fft=n_fft,           # FFT length (>= n_per_seg)
    n_overlap=n_overlap,   # Overlap between segments
    n_per_seg=None,        # Defaults to n_fft if None
    average='mean',        # Average type ('mean', 'median', or None for un-aggregated)
    window=window_type,    # Which window function to use
    remove_dc=True,        # Subtract mean before segmenting
    output='power',        # Return power or complex values
    verbose=True           # Control logging verbosity
)

# 'psds' shape: (n_channels, n_freqs) unless average=None
# 'freqs' shape: (n_freqs,)

# Plot the PSD for each channel (log scale)
plt.figure(figsize=(8, 4))
for ch_idx in range(psds.shape[0]):
    plt.semilogy(freqs, psds[ch_idx], label=f'Chan {ch_idx+1}')
plt.xlabel('Frequency (Hz)')
plt.ylabel('PSD (Power)')
plt.title('Beta Band (13-30 Hz) Power Spectral Density')
plt.legend(loc='best')
plt.show()

# Some functionality we might need below for artifacts (?)

# Artifact removal
# ica = mne.preprocessing.ICA(n_components=10, method='fastica', random_state=97)
# ica.fit(raw)