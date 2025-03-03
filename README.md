# Project_COGS189
Scripts for COGS 189 Project with EEG data collection

## How to setup env
For running on lab windows computer:

### Environment setup for Windows Lab machine:
1) `& C:/Users/apecherskaya/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m pip install virtualenv`
2) `& C:/Users/apecherskaya/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m virtualenv pyenv --python=3.11.9`
3) `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
4) `pyenv\Scripts\activate`

If you use the same computer you would only need to run `pyenv\Scripts\activate` (i think)

### Environment setup for MacOS (Apple Silicon compatible):
1) Run this in terminal before running the scripts: `conda env create -f environment.yml`.
2) Run `conda list | grep -E "^(psychopy|python|liblsl|brainflow)"` to ensure you have the required packages.

## How to run experiment
Run `python COGS189V2Updated.py` for colored background version.
#TODO (need to fix script first) Run `python COGS189V1Updated.py` for colored words version

### Color stuff
Use this link to access #HEX for colors from image `glasses_color.jpg` of glasses: https://redketchup.io/color-picker 

Can iterate color combinations later.