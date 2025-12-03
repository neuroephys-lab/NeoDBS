# NeoDBS

## 03.12.2025

- Documentation can be done semi-automatically.
- NeoDBS more organized so it has access to documentation

### TBF:
- Finish documenting all functions of NeoDBS (start at extract_cc_features)

### Debug:
 - extract_psd_features:
    - moved to features
    - also calculates for coherence
    - %Mean Power in extract_psd_features corrected
 - extract_timeline_features moved to features

## 02.12.2025

### TBF:
- First, try creating documentation from functions docs
- Finish documenting all functions of NeoDBS (start at extract_idx_from_series_tag)

### Debug/Finish:
- Export plot and signals, in all plots/tabs
- Deleted unused functions
- Deleted unused parameters
- Organized functions into proper modules, and replaced callbacks

## 28.11.2025

### TBF:
- Export Timeline Signals: 'X' is different for every day. See min of all and max of all --> create x array that encapsulates all streams

### Debug/Finish:
- Export plot and signals:
    - Impedance
    - PAC
    - Spectrogram (individual/joined)
    - Wavelet (individual/joined)
    - Coherogram
    - Timeline
    
- Features | export_plot:
    - 'Bar' completed with colors, figsize and ticks

## 27.11.2025

### Debug:
- Export plot:
    - Cross-correlatoin
    - Spectrogram (individual/joined)
    - Coherogram
    - Wavelet (individual/joined)
- Export signals:
    - Impedance table
- Features | export_plot 
    - '3D': 
        - matplotlib had smoothin ON making it seem like it had different time resolutions. Smoothing is now OFF
        - correct figsize
        
## 26.11.2025

### Organization:
- Started to remove unused functions and save them in deprecated-specific files

### Design:
- Plot coherence button colored

### Debugs:
- Export plot and signals in:
    - Circadian Rhythm
    - Stimulation
- Features | export_plot:
    - Get correct colors and plot size
    - '3D' (TBC: Correct resolution, make design as close as possible, make it handle coherogram) is almost complete, but matplotlib and dpg show different spectrograms to same signal :/


## 25.11.2025
### New functionalities:
- Fonts (available in https://github.com/sahibjotsaggu/San-Francisco-Pro-Fonts/tree/master)

### Debugs:
- Font resizer --> not scale, but actual resize (better quality)
- Features:
    - export_plot :
        - includes 'peaks' from Survey PSD
        - mean thickness corrected
    - export_signals:
        - Std. Dev is the actual difference, not y1 and y2
        - handles label empty (peaks in survey)
- Survey opens all corresponding tabs 
- Export plot and signals in:
    - Individual:
        - Setup Artifacts
        - Survey PSD
        - Timeline
    - Combined:
        - Setup Artifacts
        - Survey PSD
        - Timeline
    

## 24.11.2025
### New functionalities:
- Font resizer
- Design binded to classic theme (themes given by dpg cannot be edited)


## 21.11.2025

### New functionalities:
- Save signals and buttons
    - 2D
    - Stimulation (only saves the moments of amplitude change)
- Save workspace (in construction --> cannot be without json)

## 19.11.2025

Start function to apply export_plot from features

### Debugs:
- Change show mean power to simple index and axis legend on the side (its not possible to rotate ticks)
- Finish updating electrode and group/events names
- Others
- Close on handle submit

## 17.11.2025

### New functionalities:
- Event Summary Tab on Combined
- Show mean power 
    - save values into txt file ready to plot in graphpad
    - toggle buttons
    - Add extra values --> for example Y-BOCS/VAS to the plot, in a new axis
    - 2nd X and Y axis --> so the user can drag and visually inspect the best correlation between mean power and the added events/values

### Debugs:
- Circadian rhythm
- Band Mean power channel
- Correção: aceder aos modos de cada ficheiro e não falhar ao alinhar eventos

## 14.11.2025

### GUI Design
- Setup tab, Timeline tab 

### New functionalities:
- Show mean power

## 13.11.2025

### GUI Desing
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

