# NeoDBS

## 27.02.2026

* try of constructing mac binary files
* Timeline uses missing points in **circadian rhythm** and **analyze timeline events** if "Missing points" is checked

## 20.02.2026

### Debug

* Before vs After PSD toggle buttons corrected

### New

- .exe is only for windows
- build.yml will use GitHub Actions to create proper executable files for linux and mac
- .icns file for icon in mac

## 16 e 18.02.2026

### Debug

* Timeline stimulation: plot both hemispheres w/ information about sensing band
* Checked: fuso horario
  * Correção de adicionar recs aos dias corretos nos sinais (dict) do timeline
* Tooltip in change to dB button only when hide is activated
* Impedance table with units
* **update_plot_td**: uses x axis plotted, not the in memory saved in app_state
* export_plot: multiple spectrograms (>2 ou >1 linha) was nesting lists of axes, not flattened and correctly exporting

## 13.02.2026

### Debug

* Circadian rhythm was getting confused
* getSignals on Timeline, sets the timestamp to the correct day
* added scale colormap in coherogram
* Timeline added sensing band
* Timeline stimulation: both hemispheres
* Streaming ready to plot stimulation, still to decide best option (maybe when click show stimulation change from time(s) to time(utc))

## 10.02.2026

### Debug

* Correction of timeline time axis
* correction of empty mean in toggling buttons (circaidan rhythm, analyze timeline events and hide)
* update of event name and electrodes in combined tabs

### Documentation

* Explanation of multiple tabs in survey and setup

## 05.02.2026

### Documentation

* added the explanation of right click plot tools

### Debug

- event-locked segmentation time axis with correct label
- indication of "no events present" correctly updated
- custom filters parameters and documentation organized under tree node
- after event-locked analysis --> x axis is set to the correct constraints

## 28.01.2026

- Themes --> classic wasnt applying the correct FULL theme, because it was checkin internal tag instead of label of sender

## 26.01.2026

- Git with version (tag @ v0.1.0)
- Default filter: if 0 --> 0.5 (5th order)
- Documentation: removed collaborators name and added version
- tags in github (v0.1.0)

## 23.01.2026v1

- Directories all corrected ('save' was not working)
- Font corrected

## 23.01.2026

### New:

- Start page
- License md (CC BY-NC-SA)
- Installation explained
- Documentation ready + collaborators
- .exe updated

## 22.01.2026

- Git e Gitea finalmente organizados, neste momento syncd

## 21.01.2026

- .exe creation (file and path organization)
  - fazer a partir do spec (1º pyinstaller NeoDBS.spec; para refazer: pyinstaller --clean NeoDBS.spec)
  - finalmente dá imagem e fontes (externos a módulos)
  - requirements not needed in .exe pois as bibliotecas sao previamente preparadas

## 20.01.2026

### Debugs:

- Show mean only hides: toggle 2 db disabled when show mean only is enabled
- CC: band cc is only computed after pressing the "plot" button, not on clicked checkbox
- Toggle2dB corrected (is only enabled when smo is disabled)
- wavelet: downsampled

### Documentation:

- Toggle2dB:
  - metrics are also changed in the table
  - Disabled if plot only shows mean

## 19.01.2026

### Documentation:

- Correction of small things
- Grammar and ortograph corrections

### Debugs:

- Combined stimulation
- Reset bands its ok
- date format present in x axis
- CC:
  - After changing type of plot plot didnt save (y_axis was identified by internal_tag and y_axis is deleted when type of plot changes. Now tag is str hard coded - always goes back to same tag)
  - Big signals crashed --> calculated norm (**2) with np.linalg cause it prevented overwflow
  - Delta was too steep to filter with 5th order: changed to 3 if b1<1Hz
- Delta estava de 0.01 a 4
- Hide days: calculates a mean per day into the table --> corrected by altering user_data when sended by 'Hide Days'. doesnt create table with user_data != None
- Event summary + CC: colormap 0
- DPI mentioned

### New:

- Toast: dizer que as metricas tambem sao convertidas em dB e apesar de teoricamente nao existir std. dev negativos, o sinal mantêm-se para a conversao para as unidades originais ser  correta
- Toast: shows current bands and is updated with inserting and reset
- When item is saved, button changes to green

## 15.01.2026

### New:

- Insert/Align (external) events: txt file also accepts date
  - confirms that theres a real date, not buffer, and checks with the string to minimize verify idx if its not correspondant to the session
  - accepts both with or withou date (day/month/year)

### Debug:

- remove outlier timeline: was trying to extract features from marked events. tags are verified for being str (tag format of add line series)

## 14.01.2026

### New:

- Menu for directories:
  - select directories for recordings, events and save into --> easier and more organized workflow

### Debugs:

- Event-locked analysis: (Toggle display) events nome diferente stream
- Toggle display: tamanho janela
- toggle: mean handle for zero signals
- save signals: save as the name indicated by the user
- Analyze timeline events:
  - dont know why, but y is coming with []
  - mean metrics were strange

## 09.01.2026

### Warnings:

- warning mean spectrogram quando tem tamanhos diferentes: nao permite calcular mean

### New:

- file example json from dbscope (metadata reformatted as in medtronic)

## 08.01.2026

### New:

- tags.xlsx: start organizing tags
- colormap buttons, scale and reset --> in spectrogram and wavelet (individual and joined)

### Debugs:

- Mean spectrogram:
  - colormap atualiza --> estava a espera de uma lista de tags, mas só há 1 mean
  - handling multiple presses
- Joined spectrogram/wavelet: shows interval and events
- Cross-correlation:
  - larger signals have cc values towards inf, before normalization --> crashing mean and max. Inf removed from normalization
  - peak normalization --> L2-norm/energy normalizaton
- Setup CT toggle —> “CT_A” : error was because all series had the word "artifaCT"

## 07.01.2026

### Documentation:

- better explaining of recordings and types of windows
- wavelet
- event summary
- table figure
- wasnt getting to the modules because now i have src folder before neodbs --> conf.py: sys.path.insert(0, os.path.abspath('../src/neodbs'))

### Debug:

- event toggling in timeline tabs
- Timeline: "signal analysis" --> closable tabs and properly deleted/reopened
- Survey combined working (psd wasnt opening because it wasnt with the right ident)

### GUI:

- Individual and combined: modes alphabetically sorted
- Custom parameters under tree node to hide
- Coherence doesnt change places with export plot if multiple employments (welch and multitaper)

## 06.01.2026

- Dummy test Andreia --> big to do list
- File example (DBScope)
- License: Creative Commons
- EEG Protocol
- Coherence features corrected: double mask was happening

### Documentation

- recording mode table in FU

## 05.01.2026

- Gitea sync

## 02.01.2026

### Structure:

- src/neodbs --> good for executables and pip installs

### Documentation

- Extra

### Debug:

- resize font: shows the actual font size

## 30.12.2025

### Documentation

- Signal Analysis done
- Extra tbd

### GUI

- filename window: modal true

### New

- Save all per window: saves exportations into folder with name of window
- Coherence over time: added export buttons
- CC debuged

## 24.12.2025

### Documentation:

- FU
- Individual vs Combined table added
- Recording mode table added
- PSD
- Coherence (tbf)

### GUI

- Main buttons colored - both
- "Features" --> "Signal Analysis" - Timeline
- Resizing window only one time - when file is opened

### Debug:

- Custom Features were not parsing the signals (i had them removed so they wouldnt appears as parameters, but wasnt addind them properly to the dict of signals)
- Removed deprecated functions
- Show mean power over time --> tags were being masked 2 times for the same visibility!

## 23.12.2025

### Documentation:

- At-home data

### GUI

- Add horizontal scrollbar: it keeps growing, so it can be activated or deactivated
- Remove random segment button lost in indefinite
- Stimulation information changed into table + export table (so it goes with electrode information per dat)
- Main buttons colored
- "Features" --> "Signal Analysis"

## 22.12.2025

### Documentation:

- At-home: timeline

### Debugs:

- **Export signals timeline after outlier removal:** signals were empty due to incorrect indexing. (After outlier removal signals are in correct order, and beg and end were switched cause they were forced to reverse signal - because of first time plotting)
- Open both change electrode names and event names at the same time, they had the same tag
- Timeline combined:
  - if multiple files from the same day headers label includes hour
  - remove outlier debugged: when from the same day, it was receiving x as float and it was expecting datetime. utils updated to handle float and int.
  - Analyze Timeline Events: metrics organized by moment, side and event

### New:

- Segmentation: removed "only visible signals" checkbox as it is unnecessary
- Outlier removal: threshold and replacement are RMS based, not MAD based. Check what is the best option with prof.
- Circadian Rhythm:
  - remove metrics as they are the same as the timeline. Maintain only the mean.
  - when toggle: mean metrics extracted and label adapted to "mean wo/ {checkbox}"
- Filename window: only put dpi when export plot

## 17.12.2025

### New:

- Tutorials:
  - In-Clinic Data (Preprocessing + Segmentation + Event-locked Analysis)

## 16.12.2025

### New:

- Documentation:
  - general workflow --> with images
  - Quick Start
  - Organized sections, numbered (sometimes doctree in build need to be deleted and created again)

### Updated:

- Documentation html pages!

### Debug:

- Timeline analyze events:
  - mean peak power wrong
  - mean appears 2x
  - add export plot/signals
- Mean spectrogram + power over time --> added buttons for export
- update table nan corrected (it was converting the same table multiple times)

### Checked:

- RMS outlier removal: threshold IS calculated per day! --> future versions see better outlier removal
- Check: Save all... window level
- Stimulation combined

## 15.12.2025

### New:

- Combined Timeline: add recalculate features
- User can define image quality on exportation

### Debug:

- Timeline combined with selected files WITH and WITHOUT Timeline mode
- Timeline combined shows events!

### Checked:

- Events: recalculate mean metrics
- Timezone correction
- CR: Mean peak time --> it calculates the peak of the mean, not the mean of the peaks!

## 12.12.2025

### Functionalities:

- Multitaper from mne removed, only dpss (from scipy signals)
- Timeline recalculate metrics for removal outliers!s

### Debug:

- spectrogram:
  - event marking correct for joined and individual
  - colors correct!
- wavelet:
  - event marking correct for joined and individual
  - colors correct!
  - parameters updated for less computational cost

## 11.12.2025

### Debug:

- Export Plot:
  - '2D' corrected
  - Event summary
  - Timeline with missing points
- Survey toggle display corrected to send correct colors for export plot
- Debug select all - toggle visibility
- Event marking on spectrogram:
  - with no cuts: correct event marking

## 10.12.2025

### Debug:

- Events identified by HH:MM
- Toggle Visibility acounts user-defined deviation
- Survey PSD with mean features and correct psd buttons
- Survey PSD is correclty inserted in app_state dictionary
- Default Filter min value --> cannot be below 0.5 Hz or else!!!!!!!!!
- Export plot:
  - impedance/empty label: handled

## 09.12.2025

### New functionalities:

- user chooses name of file for plot/signals/table
- TFD signals saved into respective files, separately
- Save all: (workspace/per window)
  - plots
  - tables
  - signals

### Debug:

- export plot: show mean power over time --> correct colors, thickness and documentation
- Volt2dB: calculates standard deviation according to user choice in deviation
- Mean Only and Mean Visibility: properly synchronized

## 08.12.2025

### Debug:

- export plot: show mean power over time

## 05.12.2025

- Finished documentation
- Uniform design:
  - tables under collapsing header
  - add std.dev buttons
  - remove segmentation from fd plots
  - add mean and std. dev in setup artifacts
  - Update table to power units: corrected so it wont calculate db of frequency (hz)

## 04.12.2025

- Documentation: finish DataHandling! and GUI (?)
- solve some random debugs
- Update table to power units: corrected so it wont calculate db of %

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

### To Add:

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
