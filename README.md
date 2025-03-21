# Project_COGS189

## How to setup env
For running on lab windows computer:

### Environment setup for UCSD Windows Lab machine:
1) `& C:/Users/apecherskaya/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m pip install virtualenv`
2) `& C:/Users/apecherskaya/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m virtualenv pyenv --python=3.11.9`
3) `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
4) `pyenv\Scripts\activate`

If you use the same computer you would only need to run `pyenv\Scripts\activate`

### Environment setup for MacOS (Apple Silicon compatible): (Experimental)
NB: Miniconda use for Apple Silicon ARM64 built Macs recommended
Full env setup will be updated in the next release.

## Recommended libraries and versions
- Python 3.9, 3.10 or 3.11 recommended
- Requires MNE-Python with qt for GUI backend if you want to have nice visuals of your raw EEG and annotate for artifacts manually, NOT matplotlib
- Should be compatible even with the newest PsychoPy version

### How to run experiment
1) Run `python COGS189V2Updated.py` for colored background version. 
2) Record your data with a real or virtual board.
3) Run `python clean_data.py` and `python stim_cleanup.py` to clean stimulus log and eeg data.
4) Run `python analyze.py` to do analysis, generate all plots and perform t-test.

## Color change (currently used: yellow VS blue)
Use this link to access various #HEX for colors from image `glasses_color.jpg` of glasses: https://redketchup.io/color-picker