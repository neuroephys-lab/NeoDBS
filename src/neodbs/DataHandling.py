import json
import numpy as np
from datetime import datetime, timedelta
import utils as utl # type: ignore
import re


def info_electrodes(data,version='Initial',side=0):
    '''
    Return information of the active electrodes from TIMELINE mode
    side 0 - Left;
    side 1 - Right

    :param Data: dict, from DataHandling.getData(), reorganized using DataHandling.getData()
    :param version: str, default to 'Initial'. Access to version configuration
    :param side: int, default to 0 ('Left')

    :return: dict

    '''
    GroupHistory=data['Device']['Groups']


    di = GroupHistory[version][0]
    # di = data['Device']['GroupHistory'][0]

    Group_id=di["GroupId"]
    ProgramSettings=di["ProgramSettings"]
    GroupSettings = di["GroupSettings"]
    try:
        Rate_in_hertz=ProgramSettings["RateInHertz"]
    except KeyError as e:
        if e.args[0] == "RateInHertz":
            if isinstance(ProgramSettings['SensingChannel'],dict):
                Rate_in_hertz=ProgramSettings['SensingChannel']["RateInHertz"]
            elif isinstance(ProgramSettings['SensingChannel'],list): 
                Rate_in_hertz=0
            else: 
                return None
    try:
        SensingChannel=ProgramSettings['SensingChannel']
        Sensing_electrodes=SensingChannel[side]["Channel"]
        Sensing_electrodes=Sensing_electrodes.split('.')[-1]
        Suspend_amplitude_in_miliamps = SensingChannel[side]['SuspendAmplitudeInMilliAmps']
        Sensing_freq = SensingChannel[side]['SensingSetup']['FrequencyInHertz']
        # ChannelPSD = SensingChannel[side]['SensingSetup']['ChannelSignalResult']
    
    except Exception as e: #when electrodes dont allow sensing
        SensingChannel = ProgramSettings['LeftHemisphere']['Programs']
        Suspend_amplitude_in_miliamps=SensingChannel[0]["AmplitudeInMilliAmps"]
        Sensing_electrodes = 'Sensing Disabled'
        Sensing_freq = ''
    
    Pulse_width_in_microseconds=SensingChannel[side]["PulseWidthInMicroSecond"]
    
    left_e=SensingChannel[side]["ElectrodeState"]
    right_e=SensingChannel[side]["ElectrodeState"]
    Left,Right=[], []
    for d in left_e:
        Left.append(re.split(r'\.|_', d['Electrode'])[-1] + '-' + d["ElectrodeStateResult"].split('.')[-1])

    # for d in right_e:
    #     Right.append(re.split('\.|_',d['Electrode'])[-1]+'-'+d["ElectrodeStateResult"].split('.')[-1])
    type_stimulation = GroupSettings['Cycling']['Enabled']
    if type_stimulation == False:
        type_stimulation = 'Continuous'
    else: type_stimulation = 'Cycling'
    
    a = {
        'Group_id': utl.after_point(Group_id),
        'Frequency': Rate_in_hertz,
        'Pulse': Pulse_width_in_microseconds,
        'Amplitude': Suspend_amplitude_in_miliamps,
        'Stim_electrodes': Left, 
        'Type': type_stimulation,
    }

    if not isinstance(Sensing_freq,str):
        for g in range(4):
            try:
                ChannelPSD = data['Device']['GroupHistory'][0]['Groups'][g]['ProgramSettings']['SensingChannel'][side]['SensingSetup']['ChannelSignalResult']
                break
            except Exception as e: continue
        date = utl.parse_datetime(data['Device']['GroupHistory'][0]['SessionDate']).date()
        if ChannelPSD == {}:
            ChannelPSD = SensingChannel[side]['SensingSetup']['ChannelSignalResult']
            date = 'Most Recent Signal'
        temp = {
            'PSD': ChannelPSD,
            'Sense_electrodes': Sensing_electrodes,
            'Sense_frequency': Sensing_freq,
            'PSDdate': date
        }
        a = a | temp


    return a

def add_utc_conversion_to_dates(data, offset):
    '''
    Recursively convert all 'Date'-related fields to UTC with offset (time-shifted).
    Assumes naive datetimes are in the specified local timezone.

    :param Data: dict, from DataHandling.getData(), from DataHandling.getData()
    :param offset: 
    '''
   
    if isinstance(data, dict):
        for key, value in data.items():
            if 'DateTime' in key and isinstance(value, str):
                try:
                    new = utl.full_date2str(utl.parse_datetime(data[key]) - offset)
                    data[key] = new
                except Exception:
                    pass
            elif isinstance(value, (dict, list)):
                add_utc_conversion_to_dates(value, offset)

    elif isinstance(data, list):
        for item in data:
            add_utc_conversion_to_dates(item, offset)

    return data

def extract_time_offset(Data,string=False):
    '''
    Get time offset, from organized Data dictionary.

    :param Data: dict, from DataHandling.getData()
    :param string: boolean, default to False. If true returns string of the time offset, else returns timedelta object of time offset.

    :return: timedelta/string

    '''
    try:
        offset = Data['ProgrammerUtcOffset']
    except Exception:
        offset = Data['Device']['ProgrammerUtcOffset']
    sign = offset[0]
    hours = int(offset[1:].split(':')[0])
    if sign=='-':
        hours =  int(-hours)
    else: hours= hours
    if string: return offset
    return timedelta(hours=hours)

def getData(file_path):
    '''
    Creates organized dictionary with information in JSON file. Dictionary has 7 main keys, organized by the recording modes and device information.
    Data = {
        'Device': all information relative to device, stimulation, programming, session metadata, battery and electrode status,
        'Survey': recording data from BrainSense Survey (TD and PSD),
        'Setup': recording data from BrainSense Setup (Stimulation ON/OFF and PSD artifact checking),
        'Streaming': recording data from BrainSense Streaming (Stimulation ON/OFF),
        'Indefinite': recording data from BrainSense Indefinite Streaming, 
        'Events': at-home marked events, recorded 30s PSD,
        'Timeline': at-home LFP recordings,
    }

    :param file_path: str, path to JSON file.

    :return: dict

    '''

    file = open(file_path,'r',encoding='utf-8')
    try:
        raw = json.load(file)
    except Exception:
        return 'JSON corrupted.'
    offset = extract_time_offset(raw)
    raw_data = add_utc_conversion_to_dates(raw,offset)

    device_keys = ['AbnormalEnd', 'FullyReadForSession', 
            'FeatureInformationCode', 'SessionDate', 
            'SessionEndDate', 'ProgrammerTimezone', 
            'ProgrammerUtcOffset', 'ProgrammerLocale', 
            'ProgrammerVersion', 'PatientInformation', 
            'DeviceInformation', 'BatteryInformation', 
            'RechargeCount', 'NonRechargeBatteryStatus', 
            'GroupUsagePercentage', 'LeadConfiguration', 
            'Stimulation', 'Groups', 
            'BatteryReminder', 'Impedance', 
            'GroupHistory', 'PatientEvents']

    setup_keys = ['SenseChannelTests', 'CalibrationTests', 'MostRecentInSessionSignalCheck'] #
    survey_keys = ['LFPMontage', 'LfpMontageTimeDomain']
    streaming_keys = ['BrainSenseTimeDomain', 'BrainSenseLfp']
    indefinite_keys = ['IndefiniteStreaming']
    timeline_keys= ['LFPTrendLogs']
    

    Device = {key: raw_data[key] for key in device_keys if key in raw_data} #dict com info só DEVICE
    Setup = {key: raw_data[key] for key in setup_keys if key in raw_data} #dict com info só SETUP
    Survey = {key: raw_data[key] for key in survey_keys if key in raw_data} #dict com info só SURVEY
    Streaming = {key: raw_data[key] for key in streaming_keys if key in raw_data} #dict com info só STREAMING
    Indefinite = {key: raw_data[key] for key in indefinite_keys if key in raw_data} #dict com info só INDEFINITE
    #Timeline = {key: raw_data[key] for key in timeline_keys if key in raw_data} #dict com info só TIMELINE - chronic

    #dict com info só EVENTOS
    
    event_diagnotic_keys = ['EventLogs','LfpFrequencySnapshotEvents']
    event_keys = ['EventSummary']
    Events = {}
    Timeline = {}

    if 'DiagnosticData' in raw_data:
        for key in event_diagnotic_keys:
            if key in raw_data['DiagnosticData']:
                Events[key] = raw_data['DiagnosticData'][key]
        for key in timeline_keys:
            if key in raw_data['DiagnosticData']:
                Timeline[key] = raw_data['DiagnosticData'][key]

    for key in event_keys:
        if key in raw_data:
            Events[key] = raw_data[key]

    Data = {
        'Device': Device,
        'Survey': Survey,
        'Setup': Setup,
        'Streaming': Streaming,
        'Indefinite': Indefinite, 
        'Events': Events,
        'Timeline': Timeline
    }

    return Data

def getModes(Data):
    '''
    Gets recording modes present in Data dictionary. Verifies if Data is empty or damaged (with recordings available).

    Modes:
        - Survey
        - Setup
        - Indefinite (Streaming)
        - Streaming
        - Timeline
        - Events

    :param Data: dict, from DataHandling.getData()

    :return: list
    '''

    past = getLastSessionDate(Data)
    def add_mode(Data):
        for key, value in Data.items():
            if key == 'Events':
                if 'LfpFrequencySnapshotEvents' not in Data[key].keys(): #sensing capacities not yet setup
                    continue
                # elif not isinstance (Data[key]['LfpFrequencySnapshotEvents'], dict): #sensing capacities off
                #     continue
            if key == 'Timeline':
                if 'LFPTrendLogs' not in Data['Timeline'].keys(): continue
                first = list(Data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Left'].keys())[0]
                last_time = Data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Left'][first][0]['DateTime']
                if past>last_time: continue

            if key != 'Device' and value:  # Ensure it's not empty
                if (
                    key == 'Setup'
                    and set(value.keys()) == {'MostRecentInSessionSignalCheck'}  # Ensure it's the only key
                    and (not value['MostRecentInSessionSignalCheck'] or isinstance(value['MostRecentInSessionSignalCheck'], list) and len(value['MostRecentInSessionSignalCheck']) == 0)
                ):
                    continue  # Skip appending 'Setup'
                modes.append(key)

    modes = []
    if 'Device' not in Data or Data['Device'].get('AbnormalEnd') is False:  # Check if recording was successfully terminated
        add_mode(Data)
       
    else: 
        if 'Device' in Data.keys():
            Warning(f"Damaged with recordings!")
            modes.append('Damaged')
            add_mode(Data)
    if modes == ['Damaged']:
        modes = []
        modes.append('None. Recording is Damaged!')
    modes = sorted(modes)
    return modes

def getStimStatus(Data):
    '''
    Gets status (ON/OFF) of stimulation, from beginning and end of recording session. 

    :param Data: dict, from DataHandling.getData()

    :return: tuple, (initial,final)

    '''
    initial = utl.after_point(Data['Device']['Stimulation']['InitialStimStatus'])
    final = utl.after_point(Data['Device']['Stimulation']['FinalStimStatus'])
    return (initial,final)

def getSessionDate(Data): 
    '''
    Returns string of session date.

    :param Data: dict, from DataHandling.getData()
    '''
    if Data['Device']['SessionDate']:
        return utl.parse_datetime(Data['Device']['SessionDate'])
    else: return "No date stored!"

def getSessionDuration(Data):
    '''
    Gets session duration.

    :param Data: dict, from DataHandling.getData()
    :return: int

    '''
    
    if Data['Device']['SessionEndDate'] and Data['Device']['SessionDate']:
        end = utl.parse_datetime(Data['Device']['SessionEndDate'])
        beginning = utl.parse_datetime(Data['Device']['SessionDate'])

        return abs(end - beginning)
    else: return "No dates stored!"

def getPatientInfo(Data):
    '''
    Returns patient information.

    :param Data: dict, from DataHandling.getData().
    '''
    return Data['Device']['PatientInformation']['Initial']

def getDeviceInfo(Data):
    '''
    Returns device information.

    :param Data: dict, from DataHandling.getData()
    '''
    return Data['Device']['DeviceInformation']['Final']

def getLastSessionDate(Data):
    '''
    Returns date of previous session.

    :param Data: dict, from DataHandling.getData()
    '''
    if 'GroupHistory' not in Data['Device'].keys(): 
        return 'This is First Session.'
    return Data['Device']['GroupHistory'][1]['SessionDate']

def getBatteryInfo(Data):
    '''
    Returns battery information.

    :param Data: dict, from DataHandling.getData()
    '''
    return Data['Device']['BatteryInformation']

def getRecordingDuration(mode, recording):
    '''
    Returns recording duration.

    :param mode: str
    :param recording: dict

    :return: float

    '''
    match mode:
        case 'Streaming': 
            Ticks = utl.string2numbers(recording['TicksInMses'])
            temp_time = (Ticks[0] - Ticks[-1])/1000

        case 'Timeline': 
            days = recording.keys()
            for day in days:
                TickI = utl.parse_datetime(recording[day][-1]['DateTime']).timestamp()   
                TickF = utl.parse_datetime(recording[day][0]['DateTime']).timestamp()  
                temp_time = (TickF - TickI)/1000
                
            else: pass

        case 'Indefinite':      
            Ticks = utl.string2numbers(recording['TicksInMses'])
            Fs = recording['SampleRateInHz']
            if len(Ticks)==0:
                GlobalPacketSizes = utl.string2numbers(recording['GlobalPacketSizes'][1:-1])
                temp_time = sum(GlobalPacketSizes)/Fs
            else:
                Ticks = (Ticks - Ticks[0])/1000
                temp_time = Ticks[-1]

        case _: #Survey - SenseChannel OR CalibrationTest
            if 'TicksInMses' in recording.keys():
                Ticks = utl.string2numbers(recording['TicksInMses'])
                Fs = recording['SampleRateInHz']
                if len(Ticks)==0:
                    GlobalPacketSizes = utl.string2numbers(recording['GlobalPacketSizes'][1:-1])
                    temp_time = sum(GlobalPacketSizes)/Fs
                else:
                    Ticks = (Ticks - Ticks[0])/1000
                    temp_time = Ticks[-1]

    return np.abs(np.round(temp_time,4))

def getEventsElectrodes(data):
    '''
    Returns active electrodes at beginning and end, for at-home recordings.

    :param Data: dict, from DataHandling.getData()

    :return: list, [initial, final]
    '''
    if ('Events' or 'Timeline') not in getModes(data):
        return None

    if 'SensingChannel' not in data['Device']['Groups']['Initial'][0]['ProgramSettings'].keys():
        initial = 'At-home sensing disabled!'
    else:
        initial = data['Device']['Groups']['Initial'][0]['ProgramSettings']['SensingChannel']
        left = utl.after_point(initial[0]['Channel'])
        right = utl.after_point(initial[1]['Channel'])
        initial = left, right

    if 'SensingChannel' not in data['Device']['Groups']['Final'][0]['ProgramSettings'].keys():
        final = 'At-home sensing disabled!'
    else:
        final = data['Device']['Groups']['Final'][0]['ProgramSettings']['SensingChannel']
        left = utl.after_point(final[0]['Channel'])
        right = utl.after_point(final[1]['Channel'])
        final = left, right

    return initial, final

def getEventLog(Data):
    '''
    Returns log of marked events.

    :param Data: dict, from DataHandling.getData()
    '''
    data = Data['Events']['LfpFrequencySnapshotEvents']
    return [event for event in data if 'LfpFrequencySnapshotEvents' not in event.keys()]
    
def getModeSignals(Data, mode):
    '''
    Returns signals of respective mode, from Data dictionary.

    :param Data: dict, from DataHandling.getData()
    :param mode: str

    :return: list
    '''
    
    previous_session = utl.parse_datetime(getLastSessionDate(Data))
    match mode:
        case 'Streaming': #✅
            recs  = Data[mode]['BrainSenseTimeDomain']
            stim = Data[mode]['BrainSenseLfp']

        case 'Timeline': #✅dont need to check date, only hemisphere
            recs = Data[mode]['LFPTrendLogs']
            
        case 'Events': #✅
            recs = []
            
            temp = Data[mode]['LfpFrequencySnapshotEvents']
            paths = utl.find_key_path(temp,'LfpFrequencySnapshotEvents') #events snapshots have this key 2x, rest is only event timestamp
            for path in paths:
                path = utl.parse_path(path)
                event = utl.access_by_path(temp,path)
                if previous_session>utl.parse_datetime(event['DateTime']): continue
                recs.append(event)
            '''
            Usage:
            recs = DH.getModeSignals(Data,'Events')
            for rec in recs: print(rec['EventName'],':',rec['LfpFrequencySnapshotEvents']['HemisphereLocationDef.Right']['DateTime'])
            '''

        case 'Indefinite': #✅
            recs  = Data[mode]['IndefiniteStreaming']
            
        case 'Setup':
            recs = [Data[mode]['SenseChannelTests'], 
            Data[mode]['CalibrationTests'],
            Data[mode]['MostRecentInSessionSignalCheck']]

        case 'Survey': #✅ #só falta o LFPMontage
            recs = Data[mode]['LfpMontageTimeDomain']

    return recs

def getSignals(Data, mode):
    '''
    Returns signals in respective mode, properly handled into a clean dictionary.

    dict = {
            'Date': utl.parse_datetime(rec['FirstPacketDateTime']),
            'Channel': rec['Channel'],
            'Y' : raw,
            'X': time_array
        }
        
    
    :param Data: dict, from DataHandling.getData()
    :param mode: str

    :return: list, list of signal's dictionaries.
    '''
    recs = getModeSignals(Data, mode)
    signals = []

    def get(rec):
        Fs = rec['SampleRateInHz']
        total_duration = getRecordingDuration(mode,rec)
        time_array = np.arange(0,total_duration,1/Fs) #in seconds
        raw = rec['TimeDomainData']
        if len(time_array)<len(raw): #while there is no correct missing data function complete
            raw = raw[:len(time_array)]
        else:
            time_array = time_array[:len(raw)]

        dict = {
            'Date': utl.parse_datetime(rec['FirstPacketDateTime']),
            'Channel': rec['Channel'],
            'Y' : raw,
            'X': time_array
        }
        
        return dict
    
    if mode=='Setup':

        #Stimulation OFF = Sense
        #Stimulation ON = Calibration
        sense = []
        calibration = []
        artifacts = []

        for rec in recs[0]: sense.append(get(rec))
        for rec in recs[1]: calibration.append(get(rec))
        for rec in recs[2]:
            dict = {
                'Channel': utl.after_point(rec['Channel']),
                'Artifact': utl.after_point(rec['ArtifactStatus']),
                'X': rec['SignalFrequencies'],
                'Y': rec['SignalPsdValues']
            }
            artifacts.append(dict)
        


        signals = sense, calibration, artifacts

    if mode in ['Streaming','Indefinite','Survey']:
        for rec in recs: signals.append(get(rec))

    elif mode=='Events':
        signals = []
        # if (recs is None) or (recs== []): return None
        # if 'HemisphereLocationDef.Left' not in recs[0]: return None
        for rec in recs: 

            left_side = rec['LfpFrequencySnapshotEvents']['HemisphereLocationDef.Left']
            right_side = rec['LfpFrequencySnapshotEvents']['HemisphereLocationDef.Right']
            
            left = {
                'Channel': left_side['SenseID'],
                'X': left_side['Frequency'],
                'Y': left_side['FFTBinData']
            }

            right = {
                'Channel': right_side['SenseID'],
                'X': right_side['Frequency'],
                'Y': right_side['FFTBinData']
            }

            dict = {
                'EventName': rec['EventName'],
                'EventID': rec['EventID'],
                'DateInitial': rec['DateTime'],
                'DateFinal': rec['LfpFrequencySnapshotEvents']['HemisphereLocationDef.Left']['DateTime'],
                'Left': left,
                'Right': right
            }

            signals.append(dict)
        if recs == [] and 'LfpFrequencySnapshotEvents' in Data[mode].keys():
            signals = {'Marked': Data[mode]['LfpFrequencySnapshotEvents']}

    elif mode=='Timeline': #falta adicionar canal
        signal = {}
        for side in recs:
            for day, logs in recs[side].items():
                day = str(utl.parse_datetime(day).date())

                if day not in signal:
                    signal[day] = {'Left': {'X': [], 'Y': [], 'Stim': []}, 'Right': {'X': [], 'Y': [], 'Stim': []}}

                LFP = [log['LFP'] for log in logs[::-1]]
                #time = [utl.convert_to_timestamp(log['DateTime']) for log in logs]
                time = [log['DateTime'] for log in logs[::-1]]
                stim = [log['AmplitudeInMilliAmps'] for log in logs[::-1]]

                hemisphere = 'Left' if utl.after_point(side) == 'Left' else 'Right'
                for idx,t in enumerate(time):
                    current_day = str(utl.parse_datetime(t).date())
                    if current_day not in signal:
                        signal[current_day] = {'Left': {'X': [], 'Y': [], 'Stim': []}, 'Right': {'X': [], 'Y': [], 'Stim': []}}
                    signal[current_day][hemisphere]['X'].append(t)
                    signal[current_day][hemisphere]['Y'].append(LFP[idx])
                    signal[current_day][hemisphere]['Stim'].append(stim[idx])

        signals = [{'Date': day, 'Left': data['Left'], 'Right': data['Right']} for day, data in signal.items()]


    return signals

def getStreamingStimulationValues(data):
    '''
    Returns streaming stimulation amplitude.
    
    :param Data: dict, from DataHandling.getData()

    :return: str (status), dict (right amplitude), dict (left amplitude)
    '''
    if 'Streaming' not in data.keys():
        return
    
    stimulation = data['Streaming']['BrainSenseLfp']
    right, left, time = {}, {}, {}
    for s in stimulation:
        date = str(utl.parse_datetime(s['FirstPacketDateTime']))
        right[date], left[date], time[date] = [], [], []
        for side in s['LfpData']:
            time[date].append(side['TicksInMs'])
            right[date].append(side['Right']['mA'])
            left[date].append(side['Left']['mA'])

    for date, timeline in time.items():
        new_timeline = [(t - timeline[0])/1000 for t in timeline]#from ms to s, starting at 0
        time[date] = new_timeline

    return right, left, time

def getStreamingStimulation(Data,date):
    '''
    Returns active stimulation group.
    
    :param Data: dict, from DataHandling.getData()
    :param date: str

    :return: str
    '''
    dictionary = Data['Streaming']['BrainSenseLfp']
    group = None
    date = utl.extract_date(date)
    for rec in dictionary:
        rec_date = utl.extract_date(utl.parse_datetime(rec['FirstPacketDateTime']))
        if rec_date == date: 
            group = rec['TherapySnapshot']['ActiveGroup']
            group = utl.after_underscore(utl.after_point(group))
    
    if group == None: return ['Stimulation OFF']
    else: 
        right, left, time = getStreamingStimulationValues(Data)
        return [f'Stimulation ON: Group {group}',right,left, time]

def getStimulation(Data,side='Right'):
    '''
    Returns at-home stimulation amplitude.

    :param Data: dict, from DataHandling.getData()

    :return: dict

    '''
    timeline = getModeSignals(Data,'Timeline')[f'HemisphereLocationDef.{side}']
    info = info_electrodes(Data,version='Final')
    electrodes = info['Stim_electrodes']
    stimulation = {'X': [], 'Y': [], 'Info': []}
    final_date = getSessionDate(Data)

    for _, stream in timeline.items():
        x = list(reversed([s['DateTime'] for s in stream]))
        y = list(reversed([s['AmplitudeInMilliAmps'] for s in stream]))
        for xx in x: stimulation['X'].append(xx)
        for yy in y: stimulation['Y'].append(yy)
        # text = f"{_[:10]} | Initial: {y[0]} mA | Final: {y[-1]} mA \n Electrodes: {electrodes}"
        new = ""
        for e in electrodes: new = new + str(e) + ", "
        new = new.replace('-Positive','(+)')
        new = new.replace('-Negative','(-)')
        text = {'Date': _[:10], 'Initial (mA)': y[0], 'Final (mA)':y[-1], 'Electrodes': new}
        stimulation['Info'].append(text)
    
    if final_date.date() > utl.parse_datetime(x[-1]).date():
        if getStimStatus(Data)[1] == 'ON':
            stimulation['X'].append(utl.full_date2str(final_date))
            stimulation['Y'].append(info['Amplitude'])
            # text = f"{_[:10]} | Initial: {y[-1]} mA | Final: {info['Amplitude']} mA \n Electrodes: {electrodes}"
            text = {'Date': _[:10], 'Initial (mA)': y[0], 'Final (mA)':y[-1], 'Electrodes': electrodes}
            stimulation['Info'].append(text)

    return stimulation

def getEventSummary(Data):
    '''
    Returns event summary (number of occurences of each event).
    
    :param Data: dict, from DataHandling.getData()

    :return: dict

    '''
    if 'EventSummary' in Data['Events'].keys():
        return Data['Events']['EventSummary'] 
    else: return {}

def getImpedance(Data): 
    '''
    Returns monopolar and bipolar impedance test results, per hemisphere.
    
    :param Data: dict, from DataHandling.getData()

    :return: list, [status (str), Left (dict), Right (dict)]
    '''

    Left, Right = {}, {}
    if len(Data['Device']['Impedance']) == 0:
        return 'No Impedance data in file!'
    else:
        info = Data['Device']['Impedance'][0]
        status = utl.after_point(info['ImpedanceStatus'])
        tests = info['Hemisphere'][0]['SessionImpedance'].keys()
        for type in tests:
            Left[type] = info['Hemisphere'][0]['SessionImpedance'][type]
            Right[type] = info['Hemisphere'][1]['SessionImpedance'][type]
    return status, Left, Right

def MissingTimeline(data,side,days=None,filtered=None):
    '''
    Checks missing points in timeline (missing point: when difference between points is >= than 11 minutes) and returns a new corrected timeline dict, correcting missing LFP values through mean interpolation.
    
    new_dic = {
        'X': corrected timeline, 
        'Y': corrected LFP,
        'X_missing': missing timeline points,
        'Y_missing': missing LFP values}

    :param Data: dict, from DataHandling.getData()
    :paam side: str
    :return: dict
    '''
    if side == 'Right': side = 'HemisphereLocationDef.Right'
    else: side = 'HemisphereLocationDef.Left'

    if days: days_hemisphere_right=np.array(days).flatten().tolist()
    else: days_hemisphere_right=list(data['Timeline']['LFPTrendLogs'][side].keys())
    days_of_search=days_hemisphere_right
    
    time_format_somado=[]
    LFP_somado=[]
    red_LFP=[]
    red_time=[]

    if isinstance(days_of_search, list): #this for cycle needs to be changed so it is a search for key
        for chosen_day in days_of_search:
            for s in days_hemisphere_right:
                if chosen_day in s:
                    key_chosen_day = s
                    break 

            if filtered: info_chosen_day=filtered[utl.after_point(side)]
            else: info_chosen_day= data['Timeline']['LFPTrendLogs'][side][key_chosen_day]

            size_chosen_day = len(info_chosen_day)
            time_format=[0]*size_chosen_day
            LFP=[0]*size_chosen_day
            i=size_chosen_day

            if filtered:
                LFP = info_chosen_day['Y']
                time_format = info_chosen_day['X']
            else:
                for t in info_chosen_day:
                    LFP[i-1]=int(t['LFP'])
                    time_format[i-1]=datetime.fromisoformat(t['DateTime'].rstrip('Z'))
                    i=i-1

            #adding the missing points
            index_n_pontos_extra=[]
            for s in range(len(time_format)-1):
                dif=time_format[s+1]-time_format[s]
                dif=dif.seconds
                if dif > 660:
                    
                    n_pontos_extra=(dif//600) - 1
                    index_n_pontos_extra.append(s)
                    index_n_pontos_extra.append(n_pontos_extra)
                    #change this to a dictionary so it is [{'pos':s, 'n_extra': n_pontos_extra}]

            n_saltos=[]
            n_saltos=len(index_n_pontos_extra)//2
            LFP_acrescentar=[]

            for i in range(n_saltos):
                index_ponto_acrescentar=index_n_pontos_extra[i*2]
                numero_pontos_acrescentar=index_n_pontos_extra[i*2+1]
                #adding points in y-axis
                min_ponto_acrescentar=LFP[index_ponto_acrescentar]
                max_ponto_acrescentar=LFP[index_ponto_acrescentar+1]
                media_ponto_acrescentar=(min_ponto_acrescentar+max_ponto_acrescentar)/2
                LFP_acrescentar=[media_ponto_acrescentar]*numero_pontos_acrescentar
                LFP[index_ponto_acrescentar+1:index_ponto_acrescentar+1]=LFP_acrescentar
                red_LFP.extend(LFP_acrescentar)
                #adding points in x-axis
                tempo=time_format[index_ponto_acrescentar]
                for j in range(0,numero_pontos_acrescentar+1):
                    tempo=tempo + timedelta(minutes=10)
                    next_t = time_format[index_ponto_acrescentar+j+1]
                    diff = next_t-tempo
                    if diff>timedelta(minutes=10): 
                        time_format.insert(index_ponto_acrescentar+j+1,tempo)
                        red_time.append(tempo)

            time_format_somado.extend(time_format)
            LFP_somado.extend(LFP)

    new_dic = {'X': time_format_somado, 'Y':LFP_somado,'X_missing':red_time,'Y_missing':red_LFP}
            
    return new_dic

def correctMissingTimeline(Data, Timeline, axis='X',days=None,filtered=None):
    '''
    Corrects timeline recordings for both hemispheres.
    
    :param Data: dict, from DataHandling.getData()
    :param Timeline: dict
    :param axis: str

    :return: dict, corrected Timeline dict
    '''

    other_axis = 'Y'
    added_timeline = {'Right':[],'Left':[]}
    added_lfp = {'Right':[],'Left':[]}

    missing = utl.after_underscore(axis)
    if missing == 'missing': 
        other_axis = other_axis +'_' + missing
    
    for side in ['Left','Right']:

        if isinstance(Timeline,dict): Timeline = [Timeline]
        if side not in Timeline[0].keys(): continue

        added = MissingTimeline(Data, side,days=days,filtered=filtered)
        added_timeline[side] = added[axis]
        added_lfp[side] = added[other_axis]


        days_added = [utl.extract_date(ad) for ad in added[axis]]
        days_added = np.unique(days_added)

        new_timeline = {d:[] for d in days_added}
        new_lfp = {d:[] for d in days_added}

        for idx, at in enumerate(added_timeline[side]):
            key = utl.extract_date(at)
            new_timeline[key].append(at)
            new_lfp[key].append(added_lfp[side][idx])

        
        
        for i,day in enumerate(Timeline):
            date = day['Date']
            if isinstance(date,str):
                try:
                    date = utl.parse_datetime(date)
                    date = utl.extract_date(date)
                except Exception:
                    pass
            if axis not in Timeline[i][side].keys(): 
                Timeline[i][side][axis] = []
                Timeline[i][side][other_axis] = []
            if date in new_timeline.keys():
                Timeline[i][side][axis] = new_timeline[date]
                Timeline[i][side][other_axis] = new_lfp[date]
                
    return Timeline