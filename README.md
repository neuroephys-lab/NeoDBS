# NeoDBS

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

