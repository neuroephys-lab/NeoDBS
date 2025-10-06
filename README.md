# NeoDBS

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

