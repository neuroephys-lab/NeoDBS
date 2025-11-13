# NeoDBS

## 13.11.2025

Electrode tab/Group History for now deprecated while waiting for medtronic response

### New Functionalities:
- Event Summary tab finished
- Change window name

### Design:
- Setup artifacts tab: child window + mean + std.dev/95th percentile


## 12.11.2025

### New Functionalities:
- Event Summary tab 

### Design:
- Horizontal scrollbars on information windows

### Bug fixes:
- Circadian Rhhythm accepting correctly values (mean still to be corrected)
- Modes only appear with data between sessions (Events and Timeline)
- Verification if data is previous to the last session
- Survey get Signal corrected
- Coherence: get labels and channels correctly


## 10.11.2025

## To Add:
- Event Summary tab (/being developed in temp)


### Bug fixes:
- Toggle buttons (setup artifacts tab)
- Session duration
- Stimulation window always appears with correct info
- Survey tab

## 07.11.2025
### New functionalities:
- Sensing PSD
    - toggle correct
- Export 2D and 3D signals

## 05.11.2025
### New functionalities:
- Sensing PSD new tab (when events or timeline pressed)

### Bug fixes:
- Custom parameters finalized
- Custom coherence
- Custom PAC


## 04.11.2025
### New functionalities:
- Closing (recording mode) tab --> reset to original raw signals

### Bug fixes:
- Data Handling: info electrode string handling
- Custom dpss: receiving parameters
- Custom multitaper coherence: receiving parameters, range of colormap
- Custom coherence
- Custom PAC
- Custom/Default Cross-correlation: 
    - correct peaks
    - per band
    - toggle

### GUI design:
- Survey PSD: organized and grouped

## 31.10.2025
### Bug fixes:
- Python versions below 3.12.00 dont allow encapsulated f-strings with the same type of "" (they need to be different) --> updated to allow versions below 3.12
- Circadian rhythm combined: corrected (values received in float, adn if only considered ints)
- Circadian rhythm values: 
    - nan resistant
    - Added sensing information
- DH module: info_electrodes updated to retrieve info from *Initial* (default) and Final configurations

## 27.10.2025
### Bug fixes:
- Get signals on combined with different types of recordings
- Circadian Rhythm: get signals corrected --> values still = nan

## 24.10.2025
### Bug fixes:
- Wavelet: 
    - repeated alias
    - added colormap range selector
- Joined spectrogram and wavelet
- Get correct signal/event (mode was missing)

### New functionalities:
- Reset frequency bands

### GUI design:
- Individual Events: organized and grouped


## 22.10.2025
### Bug fixes:
- Choosing signals for methods from different files 

## 20.10.2025
### Bug fixes:
- PAC 

## 17.10.2025
### Bug fixes:
- Combined multitaper: BvA working w/ dB
- Tables change value correctly (correction of % mean power and AUC - absolute)

### New functionalities:
- Spectrogram: Change colormap scale
- Events (Individual and Combined): 
    - Std. deviation e 95% IC
    - dB working with mean and std.dev 

## 16.10.2025
### Bug fixes:
- dB working correctly in PSD and events
- Std. deviation e 95% IC working correctly (add in events)

## 15.10.2025
### Bug Fixes:
- Toggle buttons for segments (in PSD estimation) correct
- Segment spectrogram with correct title
- Filter segments not mixed

## 14.10.2025
Events in text files for easier combined analysis

### New functionalities:
- Mean Spectrogram

## 10.10.2025
Tables into respective folders.

### Bug fixes:
1. Combined segmentation of streaming events
2. Filtering segments of multiple files


## 07.10.2025

### Bug fixes:
1. Normalized mean power

### GUI design:
- Feature extraction in PSD (combined/individual): streams are grouped by hemisphere and channel, but also individually presented

### Code structure:
- New folder: deprecated - old docs

## 06.10.2025
### Bug fixes:
1. Hide/toggle button in timeline events
    - if hide=True and toggle active --> hide=False and unselected streams active
2. PAC: exception for signals w/ different length
3. Coherence: restrictions for feature extraction

### GUI design:
- Timeline combined: header shows sensing information

### Code structure:
- removal of duplicates


## Before 06.10.2025
Debugs to address:
- Timeline: display of sensing band and electrodes, checkboxes
- Coherence: restrictions for feature extraction
- DPSS (custom): error
- Cross-Correlation (custom): 
    - per band: to add
    - no normalization
- Cross-Correlation (default):
    - change feature header
    - verify and validate peaks
    - exception for new bands: if f0 = 0, change to 0.1 Hz
- PAC: exception for signals w/ different length

