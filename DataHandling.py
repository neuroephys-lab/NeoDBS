import json
import numpy as np
from datetime import datetime, timedelta
import utils as utl # type: ignore
import re


'''

file_path1 = 'C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162023.json'

file_path2 = 'C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json'

file_path1 = 'C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162023.json'
file1 = open(file_path,'r',encoding='utf-8')
json1 = json.load(file)

file_path2 = 'C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json'
file1 = open(file_path,'r',encoding='utf-8')
json2 = json.load(file)
'''

def info_electrodes(data):
    '''
    Inês Pereira - up202107421@edu.fe.up.pt

    Return information of the active electrodes from TIMELINE mode
    
    '''
    GroupHistory=data['Device']['GroupHistory']
    days_hemisphere_right = list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())
    for dic in GroupHistory:
        if dic['SessionDate'][0:10]==days_hemisphere_right[0][0:10]:
                Groups=dic["Groups"]
                #print(Groups[1])
                for di in Groups:
                    if di.get("ActiveGroup")==True:
                        Group_id=di["GroupId"][-1]
                        ProgramSettings=di["ProgramSettings"]
                        Rate_in_hertz=ProgramSettings["RateInHertz"]
                        SensingChannel=ProgramSettings['SensingChannel']
                        Pulse_width_in_microseconds=SensingChannel[0]["PulseWidthInMicroSecond"]
                        Suspend_amplitude_in_miliamps=SensingChannel[0]["SuspendAmplitudeInMilliAmps"]
                        Stimulation_electrodes_1=SensingChannel[0]["ElectrodeState"]
                        Stimulation_electrodes=[]

                        for d in Stimulation_electrodes_1:
                            Stimulation_electrodes.append(re.split('\.|_',d['Electrode'])[-1]+'-'+d["ElectrodeStateResult"].split('.')[-1])
                        Sensing_electrodes=SensingChannel[0]["Channel"]
                        Sensing_electrodes=Sensing_electrodes.split('.')[-1]
    return Group_id, Rate_in_hertz, Pulse_width_in_microseconds, Suspend_amplitude_in_miliamps, Stimulation_electrodes, Sensing_electrodes

def getData(file_path):

    file = open(file_path,'r',encoding='utf-8')
    raw_data = json.load(file)

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

    def add_mode(Data):
        for key, value in Data.items():
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

    return modes

def getStimStatus(Data):
    initial = utl.after_point(Data['Device']['Stimulation']['InitialStimStatus'])
    final = utl.after_point(Data['Device']['Stimulation']['FinalStimStatus'])
    return (initial,final)

def getTimeTicksMs(TickInS,GlobalPacketSizes,Fs):
    return np.round(np.arange(start=TickInS[0],stop=TickInS[-1]+ (GlobalPacketSizes[-1]-1)/Fs ,step=1/Fs),3)

def getSessionDate(Data): 
    if Data['Device']['SessionDate']:
        return utl.parse_datetime(Data['Device']['SessionDate'])
    else: return "No date stored!"

def getSessionDuration(Data):
    
    if Data['Device']['SessionEndDate'] and Data['Device']['SessionDate']:
        end = utl.parse_datetime(Data['Device']['SessionEndDate'])
        beginning = utl.parse_datetime(Data['Device']['SessionDate'])

        print(beginning , '-->', end)
        return end - beginning
    else: return "No dates stored!"

'''
def getRecordingDuration(dictionary):
    
    Calculate duration of recording, not the whole session (1 session, can have several Recordings)    
    #Survey -> SenseChannelTests -> [:6] -> TicksInMses --- supostamente tem 90s de duração
    #Survey -> CalibrationTest -> [:4] -> TicksInMses
    #Streaming -> BrainSenseLfp -> LfpData -> [:26] -> TicksInMs
    #Indefinite -> IndefiniteStreaming -> [:9] -> TicksInMses
    #Timeline: Device -> DiagnosticData -> LFPTrendLogs -> [:2] (hemisfério) -> são dias portanto Datetime
    
    
    Time = []
    modes = getModes(dictionary)

    for m in modes:
        print(m)
        match m:

            case 'Survey':
                keys = getModes(dictionary[m])
                for k in keys:
                    recording = dictionary[m][k][-1]
                    if 'TicksInMses' in recording.keys():
                        Ticks = string2numbers(recording['TicksInMses'])
                        Fs = recording['SampleRateInHz']
                        if len(Ticks)==0:
                            GlobalPacketSizes = string2numbers(recording['GlobalPacketSizes'][1:-1])
                            temp_time = sum(GlobalPacketSizes)/Fs
                        else:
                            Ticks = (Ticks - Ticks[0])/1000
                            temp_time = np.abs(Ticks[-1])
                        print(temp_time)
                        Time.append([m,k,temp_time])

            case 'Streaming': 
                recording = dictionary[m]['BrainSenseLfp'][-1]['LfpData']
                TickI = recording[0]['TicksInMs']
                TickF = recording[-1]['TicksInMs']
                temp_time = np.round(np.abs((TickF - TickI)/1000),1)
                Time.append([m,temp_time])

            case 'Timeline': 
                if 'LFPTrendLogs' in dictionary['Device']['DiagnosticData'].keys(): #verificar se fez gravou em casa
                    recording = dictionary['Device']['DiagnosticData']['LFPTrendLogs']['HemisphereLocationDef.Right']
                    days = recording.keys()
                    for day in days:
                        TickI = parse_datetime(recording[day][0]['DateTime']).timestamp()   
                        TickF = parse_datetime(recording[day][-1]['DateTime']).timestamp()  
                        temp_time = np.abs(np.round((TickF - TickI)/1000,1))
                        Time.append([m,day,temp_time])

                else: pass

            case 'Indefinite': 
                recording = dictionary[m]['IndefiniteStreaming']        
                Ticks = string2numbers(recording[-1]['TicksInMses'])
                Fs = recording[-1]['SampleRateInHz']
                if len(Ticks)==0:
                    GlobalPacketSizes = string2numbers(recording[-1]['GlobalPacketSizes'][1:-1])
                    temp_time = sum(GlobalPacketSizes)/Fs
                else:
                    Ticks = (Ticks - Ticks[0])/1000
                    temp_time = Ticks[-1]
                Time.append([m,temp_time])
            
    return Time
'''

def getLogDuration(log):
    TickI = utl.parse_datetime(log[-1]['DateTime']).timestamp()   
    TickF = utl.parse_datetime(log[0]['DateTime']).timestamp()  
    temp_time = (TickF - TickI)/1000

    return temp_time

def getRecordingDuration(mode, recording):

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

    return np.abs(np.round(temp_time,1))

def getAllRecordingDuration(dictionary):
    '''
    Calculate duration of recording, not the whole session (1 session, can have several Recordings)    
    #Survey -> SenseChannelTests -> [:6] -> TicksInMses --- supostamente tem 90s de duração
    #Survey -> CalibrationTest -> [:4] -> TicksInMses
    #Streaming -> BrainSenseLfp -> LfpData -> [:26] -> TicksInMs
    #Indefinite -> IndefiniteStreaming -> [:9] -> TicksInMses
    #Timeline: Device -> DiagnosticData -> LFPTrendLogs -> [:2] (hemisfério) -> são dias portanto Datetime
    '''
    
    Time = []
    modes = getModes(dictionary)

    for m in modes:
        print(m)
        match m:

            case 'Survey':
                keys = getModes(dictionary[m])
                for k in keys:
                    recording = dictionary[m][k][-1]
                    if 'TicksInMses' in recording.keys():
                        temp_time = getRecordingDuration(m,recording)
                        Time.append([m,k,temp_time])

            case 'Streaming': 
                recording = dictionary[m]['BrainSenseLfp'][-1]['LfpData']
                temp_time = getRecordingDuration(m,recording)

            case 'Timeline': 
                if 'LFPTrendLogs' in dictionary[m].keys(): #verificar se fez gravou em casa
                    recording = dictionary[m]['LFPTrendLogs']['HemisphereLocationDef.Right']
                    days = recording.keys()
                    for day in days:
                        recording = recording[day]  
                        temp_time = getRecordingDuration(m,temp_time)
                        Time.append([m,day,temp_time])

                else: pass

            case 'Indefinite': 
                recording = dictionary[m]['IndefiniteStreaming']        
                temp_time = getRecordingDuration(m,recording)
                Time.append([m,temp_time])
            
    return Time

def getElectrodes(list):
    '''
    list: stim['SensingChannel'][0]['ElectrodeState']
    '''
    Electrodes = []

    for row in list:
        Electrode = utl.after_point(row['Electrode'])
        ElectrodeState = utl.after_point(row['ElectrodeStateResult'])
        if Electrode == 'Case' and ElectrodeState == 'Positive':
            Electrodes.append([Electrode, ElectrodeState])
        else:
            ElectrodeAmplitude = row['ElectrodeAmplitudeInMilliAmps']
            ElectrodeFraction = row['ElectrodeFractionOf64']
            Electrodes.append([Electrode, ElectrodeState,ElectrodeAmplitude,ElectrodeFraction])
    return Electrodes

def getEventsElectrodes(data):
    if 'Events' not in getModes(data):
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

def getStimulationParameters(dictionary, group_name, time = 'Initial'):

    group_name = 'GroupIdDef.GROUP_' + group_name
    #left = 0
    #right = 1
    if time == 'Final':
        time_ = 'FinalStimStatus'
    else:
        time_ = 'InitialStimStatus'
    
    stim = next((group for group in dictionary['Device']['Groups'][time] if group['GroupId'] == group_name), None)
    stim = stim['ProgramSettings']
    StimStatus = dictionary['Device']['Stimulation'][time_]
    StimFreq = stim['RateInHertz']
    StimCurr = stim['SensingChannel'][0]['SuspendAmplitudeInMilliAmps' ]
    AmplitudeType = utl.after_point(stim['AmplitudeControl'])
    BrainSenseStatus = stim['SensingChannel'][0]['BrainSensingStatus']
    Channel = utl.after_point(stim['SensingChannel'][0]['Channel'])
    Electrodes = getElectrodes(stim['SensingChannel'][0]['ElectrodeState'])
    PulseWidth = stim['SensingChannel'][0]['PulseWidthInMicroSecond']

    Left = {
        'StimStatus': StimStatus,
        'StimFreq': StimFreq,
        'StimCurr': StimCurr,
        'PulseWidth': PulseWidth,
        'AmplitudeType': AmplitudeType,
        'BrainSenseStatus': BrainSenseStatus,
        'Channel': Channel,
        'Electrodes': Electrodes
    }
    

    StimCurr = stim['SensingChannel'][1]['SuspendAmplitudeInMilliAmps' ]
    BrainSenseStatus = stim['SensingChannel'][1]['BrainSensingStatus']
    Channel = utl.after_point(stim['SensingChannel'][1]['Channel'])
    Electrodes = getElectrodes(stim['SensingChannel'][1]['ElectrodeState'])
    PulseWidth = stim['SensingChannel'][1]['PulseWidthInMicroSecond']

    Right = {
        'StimStatus': StimStatus,
        'StimFreq': StimFreq,
        'StimCurr': StimCurr,
        'PulseWidth': PulseWidth,
        'AmplitudeType': AmplitudeType,
        'BrainSenseStatus': BrainSenseStatus,
        'Channel': Channel,
        'Electrodes': Electrodes
    }

    Stimulation = [Left, Right]

    return Stimulation

def getSetupInfo(dictionary,group_name):

    '''
    Receives dictionary and group of interest and outputs the setup information by hemisphere
    '''

    group_name = 'GroupIdDef.GROUP_' + group_name
    left = 0
    right = 1
    
    stim = next((group for group in dictionary['Device']['Groups']['Final'] if group['GroupId'] == group_name), None)
    LeftSetup = stim['ProgramSettings']['SensingChannel'][left]['SensingSetup']
    RightSetup = stim['ProgramSettings']['SensingChannel'][right]['SensingSetup']

    return [LeftSetup, RightSetup]

def correctMissingData(dictionary,path):

    '''
    NaN where there is missing data, path: path of previously identified missing data, by checkingMissingData
    '''
    print(path)
    path_parts = utl.parse_path(path)[:-1] #until the key before
    #signal = access_by_path(dictionary,path_parts)
    new_path = ""
    for part in path_parts:
        new_path = new_path + f"[{part}]"
    print('\n' , new_path)
    mode = path_parts[0]

    match mode:
        case 'Indefinite':
            recording = f"[{mode}]['IndefiniteStreaming'][{path_parts[2]}]"
            

        case 'Streaming': 
            recording = f"[{mode}]['BrainSenseTimeDomain'][{path_parts[2]}]"
            stimulation = "FALTA AQUI O PATH PARA VERIFICAR"
        
        case 'Survey':
            recording = f"[{mode}][{path_parts[1]}][{path_parts[2]}]"

        case 'Timeline':
            LFP_path = new_path + f"['LFP']"

        case 'Events':
            LFP_path = new_path + f"['LfpFrequencySnapshotEvents']['LfpFrequencySnapshotEvents'])"

    if mode == 'Indefinite' or mode == 'Streaming' or mode == 'Survey':
        LFP_path = recording + "['TimeDomainData']"
        Ticks_path = recording + "['TicksInMses']"
        PacketsSizes_path = recording + "['GlobalPacketSizes']"
    

    print(LFP_path)

    LFP = utl.access_by_path(dictionary,utl.parse_path(LFP_path))
            
    '''
    else:
        if path_parts[2]=='LFPTrendLogs': #Timeline - 10 em 10 minutos
            LFP_path = new_path + f"['LFP']"
        if path_parts[2]=='LfpFrequencySnapshotEvents' : #Events - registo de TD por 40s?
            LFP_path = new_path + f"['LfpFrequencySnapshotEvents'])"
    
    LFP = access_by_path(dictionary,parse_path(LFP_path))

    if 'TicksInMses' in signal.keys() and 'GlobalPacketSizes' in signal.keys() and 'SampleRateInHz' in signal.keys():
        TickInS = string2numbers(signal['TicksInMses'])
        GlobalPacketSizes = string2numbers(signal['GlobalPacketSizes'][1:-1]) #take out [ ]
        Fs = signal['SampleRateInHz']

        if len(TickInS) != 0:
            Time = getTimeTicksMs(TickInS,GlobalPacketSizes, Fs)

            isReceived = np.zeros(len(Time), dtype=bool)
            nPackets = len(GlobalPacketSizes)
            print(nPackets)

            for packetId in range(nPackets):
                # Calculate the distance between each time tick and the theoretical time points
                timeTicksDistance = np.abs(Time - TickInS[packetId])             
                packetIdx = np.argmin(timeTicksDistance)
                
                if isReceived[packetIdx]:
                    packetIdx += 1

                isReceived[packetIdx:packetIdx + GlobalPacketSizes[packetId]] = True

           
            plt.figure()
            plt.plot(isReceived, '.')
            plt.yticks([0, 1], ['not received', 'received'])
            plt.ylim([-1, 2])
            plt.show()
            

            isReceived[packetIdx:packetIdx + GlobalPacketSizes[packetId]] = True
            print('Loading...')

            # Plot the received data
            plt.figure()
            plt.plot(isReceived, '.')
            plt.yticks([0, 1], ['not received', 'received'])
            plt.ylim([-1, 2])
            plt.show()'''

def sortJSONs(json_list):
    """Sort a list of JSON objects by 'SessionEndDate' in ascending order."""
    try:
        json_list.sort(key=lambda x: datetime.strptime(x['SessionEndDate'], "%Y-%m-%dT%H:%M:%SZ"))
    except KeyError:
        print("One or more JSON objects are missing 'SessionEndDate'")
    except ValueError:
        print("Invalid date format in one or more JSON objects")
    
    return json_list

def getRealTime(mode, recording):
    
    Times = []
    if mode == 'Timeline' or mode == 'Events':
        return recording['DateTime']
    else:
        first_time = recording['FirstPacketDateTime']
        if len(recording['TicksInMses']) != 0:
            Ticks = utl.string2numbers(recording['TicksInMses'])
            for tick in Ticks:
                real = utl.parse_datetime(first_time) + timedelta(milliseconds=int(tick))  # Use milliseconds
                Times.append(real)
        else: Warning('Unable to convert for lack of data!')
        return Times

def chooseRecordingDates(dictionary, mode):
    dates = []
    types = None
    keys = {}

    match mode:
        case 'Streaming': #ver se quero plottar estimulação - é à parte
            recs  = dictionary[mode]['BrainSenseTimeDomain']
            for rec in recs: dates.append(rec['FirstPacketDateTime'])
            dates = np.unique(dates)
            keys = {'Dates': dates}

        case 'Timeline': #dont need to check date, only hemisphere
            recs = dictionary[mode]['LFPTrendLogs']['HemisphereLocationDef.Left']
            for rec in recs: dates.append(rec)
            dates = np.unique(dates)
            keys = {'Dates': dates}
            
        case 'Events': #ver isto
            recs = dictionary[mode]['LfpFrequencySnapshotEvents']
            events_paths = utl.find_key_path(recs, 'LfpFrequencySnapshotEvents')
            for path in events_paths:
                event = utl.access_by_path(recs, utl.parse_path(path))
                first = event['DateTime']
                '''event = event['LfpFrequencySnapshotEvents']
                date = event['HemisphereLocationDef.Left']['DateTime']
                print(first,' | ', date)'''
                dates.append(first)
            dates = np.unique(dates)    
            keys = {'Dates': dates}
                           

        case 'Indefinite': 
            recs  = dictionary[mode]['IndefiniteStreaming']
            for rec in recs: dates.append(rec['FirstPacketDateTime'])
            dates = np.unique(dates)
            keys = {'Dates': dates}

        case _: #SenseChannelTests or CalibrationTests
            recs = dictionary['Survey']
            types = list(recs.keys())
            paths = utl.find_key_path(recs,'FirstPacketDateTime')
            for path in paths:
                path = utl.parse_path(path)
                rec = utl.access_by_path(recs,path)
                date = rec['FirstPacketDateTime']
                dates.append(date)
            #vai ser necessário se as datas pertencem ao modo-type
            keys = {'Dates': dates,
                    'Types': types}
            
    return keys

def getModeSignals(dictionary, mode):
    match mode:
        case 'Streaming': #✅
            recs  = dictionary[mode]['BrainSenseTimeDomain']

        case 'Timeline': #✅dont need to check date, only hemisphere
            recs = dictionary[mode]['LFPTrendLogs']
            
        case 'Events': #✅
            recs = []
            temp = dictionary[mode]['LfpFrequencySnapshotEvents']
            paths = utl.find_key_path(temp,'LfpFrequencySnapshotEvents')
            for path in paths:
                path = utl.parse_path(path)
                event = utl.access_by_path(temp,path)
                recs.append(event)
            '''
            Usage:
            recs = DH.getModeSignals(Data,'Events')
            for rec in recs: print(rec['EventName'],':',rec['LfpFrequencySnapshotEvents']['HemisphereLocationDef.Right']['DateTime'])
            '''

        case 'Indefinite': #✅
            recs  = dictionary[mode]['IndefiniteStreaming']
            
        case 'Setup':
            recs = [dictionary[mode]['SenseChannelTests'], 
            dictionary[mode]['CalibrationTests'],
            dictionary[mode]['MostRecentInSessionSignalCheck']]

        case 'Survey': #✅ #só falta o LFPMontage
            recs = dictionary[mode]['LfpMontageTimeDomain']

    return recs

def getSignals(Data, mode):
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

    elif mode=='Timeline': #falta adicionar canal
        signal = {}
        for side in recs:
            for day, logs in recs[side].items():
                if day not in signal:
                    signal[day] = {'Left': {'X': [], 'Y': [], 'Stim': []}, 'Right': {'X': [], 'Y': [], 'Stim': []}}

                LFP = [log['LFP'] for log in logs]
                #time = [utl.convert_to_timestamp(log['DateTime']) for log in logs]
                time = [log['DateTime'] for log in logs]
                stim = [log['AmplitudeInMilliAmps'] for log in logs]

                hemisphere = 'Left' if utl.after_point(side) == 'Left' else 'Right'
                signal[day][hemisphere]['X'].extend(time)
                signal[day][hemisphere]['Y'].extend(LFP)
                signal[day][hemisphere]['Stim'].extend(stim)

        signals = [{'Date': day, 'Left': data['Left'], 'Right': data['Right']} for day, data in signal.items()]


    return signals

def getEventSummary(Data):
    return Data['Events']['EventSummary'] 

def cutSignal(signal, initial=0, end=-1):
    # Ensure 'X' and 'Y' exist and have the same length
    if 'X' not in signal or 'Y' not in signal:
        raise ValueError("Signal must contain both 'X' and 'Y' keys.")

    length = len(signal['X'])  # Assuming 'X' and 'Y' have the same length

    # Check if the given bounds exist in the original signal
    if end ==-1 or end>length: end=length

    if initial < 0 or initial >= length:
        raise IndexError(f"Bounds out of range: initial={initial}, end={end}, signal length={length}")

    # Ensure valid slicing
    initial = max(0, min(initial, length))
    end = max(0, min(end, length))

    if initial >= end:
        return {'X': [], 'Y': []}  # Return empty signal if range is invalid

    # Create new signal with sliced values
    new = {
        'X': signal['X'][initial:end],
        'Y': signal['Y'][initial:end],
    }

    # Add 'Stim' only if it exists in the original signal
    if 'Stim' in signal and isinstance(signal['Stim'], list) and len(signal['Stim']) == length:
        new['Stim'] = signal['Stim'][initial:end]

    return new

def getSignal(dictionary,mode):
    '''
    Checkar primeiro data e depois ir buscar canal, porque canais repetem-se e datas não
    '''
    flag = 0
    match mode:
        case 'Streaming': #ver se quero plottar estimulação - é à parte
            recs  = dictionary[mode]['BrainSenseTimeDomain']
            flag = 1

        case 'Timeline': #dont need to check date, only hemisphere
            recs = dictionary[mode]['LFPTrendLogs']
            keys = list(recs.keys())
            for i in range(len(keys)): print(i,' - ', utl.after_point(keys[i]))
            hemisphere = input('What HEMISPHERE you want to analyze?')
            rec = recs[keys[int(hemisphere)]]
            total_duration = getRecordingDuration(mode,rec)
            print(total_duration)
            Fs = 1/600
            time_array = np.arange(0,total_duration,Fs)

        case 'Events': 
            print(mode) 


        case 'Indefinite': 
            recs  = dictionary[mode]['IndefiniteStreaming']
            flag = 1

        case _: #SenseChannelTests or CalibrationTests
            recs = dictionary['Survey']
            flag = 2

            types = list(recs.keys())
            for i in range(len(types)): print(i,' - ', types[i])
            type = int(input('Which RECORDING would you like to analyze? (number)'))
            type = types[type]
            recs= recs[type]

            dates = []
            channels = []

            for rec in recs: dates.append(rec['FirstPacketDateTime'])
            dates = np.unique(dates)
                            
            for i in range(len(dates)): print(i,' - ', dates[i])
            d = int(input('Which RECORDING would you like to analyze? (number)'))

            for rec in recs:
                if rec['FirstPacketDateTime'] == dates[d]:
                    channels.append(rec['Channel'])

            for i in range(len(channels)): print(i,' - ', channels[i])
            c = int(input('Which CHANNEL would you like to analyze? (number)'))

    if flag ==1: #Streaming (TD) + Indefinite + Survey: SenseChannelTests or CalibrationTests
        dates = []
        channels = []
        for rec in recs: 
            dates.append(rec['FirstPacketDateTime'])
            channels.append(rec['Channel'])
        dates = np.unique(dates)
        channels = np.unique(channels)
            
        for i in range(len(dates)): print(i,' - ', dates[i])
        d = int(input('Which RECORDING would you like to analyze? (number)'))

        for i in range(len(channels)): print(i,' - ', channels[i])
        c = int(input('Which CHANNEL would you like to analyze? (number)'))
        
    if flag!=0:
        for rec in recs:
            if rec['FirstPacketDateTime'] == dates[d] and rec['Channel']==channels[c]:
                Fs = rec['SampleRateInHz']
                raw = rec['TimeDomainData']
                total_duration = getRecordingDuration(mode,rec)
                time_array = np.arange(0,total_duration,1/Fs)
                date = utl.parse_datetime(rec['FirstPacketDateTime'])
                
        
        if len(time_array)<len(raw): #while there is no correct missing data function complete
            raw = raw[:len(time_array)]
        else:
            time_array = time_array[:len(raw)]
        
    
    signal = [time_array,raw,date, total_duration]

    return signal

def mergeJSONs(data1, data2):
    """Merge two JSON structures.""" 
    merged = {} 
    for key in data1.keys() | data2.keys(): # Union of all keys 
        if key in data1 and key in data2: 
            if isinstance(data1[key], dict) and isinstance(data2[key], dict): 
                merged[key] = mergeJSONs(data1[key], data2[key]) # Recursively merge diction 
            elif isinstance(data1[key], list) and isinstance(data2[key], list): 
                merged[key] = data1[key] + data2[key] # Concatenate Lists 
            else: 
                merged[key] = data2[key] # Overwrite with the latest data 
        else: 
            merged[key] = data1.get(key, data2.get(key)) 
    return merged

def removeDuplicates(lst):
    """Remove duplicate entries from a list while maintaining order."""
    seen = set()
    return [x for x in lst if not (tuple(x.items()) if isinstance(x, dict) else x) in seen and not seen.add(tuple(x.items()) if isinstance(x, dict) else x)]

def concatenateLists(JSONs, keys):
    """Concatenate lists from multiple JSONs based on the keys path."""
    concatenated = []
    for JSON in JSONs:
        data = JSON
        for key in keys:
            if key in data:
                data = data[key]
            else:
                data = None
                break
        if isinstance(data, list):
            concatenated.extend(data)
        elif isinstance(data, dict):  # If it's a dictionary, convert to a list
            concatenated.append(data)
    return concatenated

def listSort(lst, indices):
    """Sort a list based on given indices."""
    return [lst[i] for i in indices]

def concatenateJSONs(JSONs):
    """Merge multiple JSONs according to the adapted data structure."""
    CompiledJSON = {
        'Device': {},
        'Survey': {},
        'Streaming': {},
        'Indefinite': {},
        'Events': {},
        'Timeline': {}
    }

    for JSON in JSONs:

       # Merge Device-related fields
        
        for key in ['AbnormalEnd', 'FullyReadForSession', 'FeatureInformationCode', 'SessionDate', 
                    'SessionEndDate', 'ProgrammerTimezone', 'ProgrammerUtcOffset', 'ProgrammerLocale', 
                    'ProgrammerVersion', 'PatientInformation', 'DeviceInformation', 'BatteryInformation', 
                    'RechargeCount', 'NonRechargeBatteryStatus', 'GroupUsagePercentage', 'LeadConfiguration', 
                    'Stimulation', 'Groups', 'BatteryReminder', 'MostRecentInSessionSignalCheck', 
                    'Impedance', 'GroupHistory', 'PatientEvents']:
            if key in JSON['Device']:
                CompiledJSON['Device'][key] = JSON['Device'][key]


        # Merge Survey-related fields
        for key in ['SenseChannelTests', 'CalibrationTests', 'LFPMontage', 'LfpMontageTimeDomain']:
            if key in JSON['Survey']:
                CompiledJSON['Survey'][key] = JSON['Survey'][key]

        # Merge Streaming-related fields
        for key in ['BrainSenseTimeDomain', 'BrainSenseLfp']:
            if key in JSON['Streaming']:
                CompiledJSON['Streaming'][key] = JSON['Streaming'][key]

        # Merge Indefinite Streaming
        if 'IndefiniteStreaming' in JSON['Indefinite'].keys():
            CompiledJSON['Indefinite'] = JSON['Indefinite']

        # Merge Timeline (LFPTrendLogs)
        if 'DiagnosticData' in JSON and 'LFPTrendLogs' in JSON['DiagnosticData']:
            for hemisphere, data in JSON['DiagnosticData']['LFPTrendLogs'].items():
                if hemisphere not in CompiledJSON['Timeline']:
                    CompiledJSON['Timeline'][hemisphere] = {}
                for date, logs in data.items():
                    if date not in CompiledJSON['Timeline'][hemisphere]:
                        CompiledJSON['Timeline'][hemisphere][date] = logs
                    else:
                        CompiledJSON['Timeline'][hemisphere][date].extend(logs)
                        CompiledJSON['Timeline'][hemisphere][date] = removeDuplicates(CompiledJSON['Timeline'][hemisphere][date])

        # Merge Events-related fields
        for key in ['EventLogs', 'LfpFrequencySnapshotEvents', 'EventSummary']:
            if key in JSON.get('DiagnosticData', {}):
                if key not in CompiledJSON['Events']:
                    CompiledJSON['Events'][key] = []
                CompiledJSON['Events'][key].extend(JSON['DiagnosticData'][key])
                CompiledJSON['Events'][key] = removeDuplicates(CompiledJSON['Events'][key])

    # Sorting Timeline logs by timestamp
    for hemisphere, logs in CompiledJSON['Timeline'].items():
        for date, entries in logs.items():
            timestamps = [datetime.fromisoformat(entry["DateTime"][:-1] + "+00:00").timestamp() for entry in entries]
            CompiledJSON['Timeline'][hemisphere][date] = listSort(entries, np.argsort(timestamps))

    # Sorting EventLogs by timestamp
    if 'EventLogs' in CompiledJSON['Events']:
        timestamps = [datetime.fromisoformat(entry["DateTime"][:-1] + "+00:00").timestamp() for entry in CompiledJSON['Events']['EventLogs']]
        CompiledJSON['Events']['EventLogs'] = listSort(CompiledJSON['Events']['EventLogs'], np.argsort(timestamps))

    return CompiledJSON

def getImpedance(Data):

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

def getEventsInTimeline(Data):
    events = getSignals(Data,'Events')
    timeline = getSignals(Data,'Timeline')
    events_in_timeline = []
    evt_time = [e['DateInitial'] for e in events]

    for t in timeline:
        beg = utl.parse_datetime(t['Right']['X'][-1])
        end = utl.parse_datetime(t['Right']['X'][0])

        for idx, e in enumerate(evt_time):
            e = utl.parse_datetime(e)
            if beg<=e<=end:
                events_in_timeline.append(events[idx])

    return events_in_timeline

def interpolateTimelineStream(signal):

    missing = []
    time = [utl.parse_datetime(s) for s in signal['X']]
    for i in range(len(time)-1):
        diff= (time[i+1]-time[i]).minutes()
        if diff > 10:
            n_extra = diff//10
            dic = {
                'idx': i,
                'n_extra': n_extra
            }
            missing.append(dic)

    return missing

def MissingTimeline(data,side):
    '''
    Inês Pereira (up202107421)

    This function is for the right hemisphere of the brain
    This function recieves the information in dictionary data and also the days that will appear in the graphic
    This function returns a dictionary, the dictionary have x - time, Y - LFP, 
    X_missing - points in x-axis that will be added due to missing information, 
    Y_missing - points in y-axis that will be added due to missing information
    '''
    if side == 'Right': side = 'HemisphereLocationDef.Right'
    else: side = 'HemisphereLocationDef.Left'
    
    days_hemisphere_right=list(data['Timeline']['LFPTrendLogs'][side].keys())
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

            info_chosen_day= data['Timeline']['LFPTrendLogs'][side][key_chosen_day]

            size_chosen_day = len(info_chosen_day)
            time_format=[0]*size_chosen_day
            LFP=[0]*size_chosen_day
            i=size_chosen_day

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

    '''elif isinstance(days_of_search, str):
        for s in days_hemisphere_right: #in case of a single day
            if days_of_search in s:
                key_chosen_day = s
                break 
        
        info_chosen_day= data['Timeline']['LFPTrendLogs'][side][key_chosen_day]
        
            

        size_chosen_day = len(info_chosen_day)
        time_format=[0]*size_chosen_day
        LFP=[0]*size_chosen_day
        i=size_chosen_day

        for t in info_chosen_day:
            LFP[i-1]=int(t['LFP'])
            # time_format[i-1]=datetime.fromisoformat(t['DateTime'].rstrip('Z'))
            time_format[i-1] = t['DateTime']
            i=i-1

        #adding the missing points
        index_n_pontos_extra=[]
        for s in range(len(time_format)-1):
            dif=time_format[s+1]-time_format[s]
            dif=dif.seconds
            if dif > 660: #why 660?
                n_pontos_extra=(dif//600) - 1
                index_n_pontos_extra.append(s)
                index_n_pontos_extra.append(n_pontos_extra)

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
        
        time_format_somado = [utl.parse_datetime(t) for t in time_format_somado]'''

    new_dic = {'X': time_format_somado, 'Y':LFP_somado,'X_missing':red_time,'Y_missing':red_LFP}
            
    return new_dic

def correctMissingTimeline(Data, Timeline, axis='X'):

    other_axis = 'Y'
    added_timeline = {'Right':[],'Left':[]}
    added_lfp = {'Right':[],'Left':[]}

    missing = utl.after_underscore(axis)
    if missing == 'missing': 
        other_axis = other_axis +'_' + missing
    
    for side in ['Left','Right']:

        added = MissingTimeline(Data, side)
        added_timeline[side] = added[axis]
        added_lfp[side] = added[other_axis]


        days_added = [utl.date2str(ad) for ad in added[axis]]
        days_added = np.unique(days_added)

        new_timeline = {d:[] for d in days_added}
        new_lfp = {d:[] for d in days_added}

        for idx, at in enumerate(added_timeline[side]):
            key = utl.date2str(at)
            new_timeline[key].append(at)
            new_lfp[key].append(added_lfp[side][idx])

        if isinstance(Timeline,dict): Timeline = [Timeline]
        
        for i,day in enumerate(Timeline):
            date = utl.parse_datetime(day['Date'])
            date = utl.date2str(date)
            if axis not in Timeline[i][side].keys(): 
                Timeline[i][side][axis] = []
                Timeline[i][side][other_axis] = []
            if date in new_timeline.keys():
                Timeline[i][side][axis] = new_timeline[date]
                Timeline[i][side][other_axis] = new_lfp[date]

    return Timeline