import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import utils as utl # type: ignore


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
            'BatteryReminder', 'MostRecentInSessionSignalCheck', 
            'Impedance', 'GroupHistory', 'PatientEvents']

    survey_keys = ['SenseChannelTests', 'CalibrationTests','LFPMontage', 'LfpMontageTimeDomain']
    streaming_keys = ['BrainSenseTimeDomain', 'BrainSenseLfp']
    indefinite_keys = ['IndefiniteStreaming']
    timeline_keys= ['LFPTrendLogs']
    

    Device = {key: raw_data[key] for key in device_keys if key in raw_data} #dict com info só DEVICE
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
        'Streaming': Streaming,
        'Indefinite': Indefinite, 
        'Events': Events,
        'Timeline': Timeline
    }

    return Data

def getModes(Data):
    modes = []
    if 'Device' not in Data.keys() or Data['Device']['AbnormalEnd'] == False: #check if recording was successfully terminated
        for key in list(Data.keys()):
            if Data[key]!={} and key!='Device':
                modes.append(key)
    else: 
        modes.append('None. Recording is Damaged!')
    print(f"Modes present in Recording: {modes}")

    return modes

def checkMissingData(dictionary):

    '''
    Check missing data in the whole of dictionary, either full json file or just a recording or mode
    Return boolean matrix of missing data and the paths
    '''
    
    GlobalPacketSizes = 0
    Fs = 250

    check = []

    modes = getModes(dictionary)

    for mode in modes:
        if mode== 'Streaming' or mode== 'Indefinite' or mode == 'Survey': #Streaming, Survey
                key_paths = utl.find_key_path(dictionary[mode], 'TicksInMses')

                for path in key_paths:
                    path_parts = utl.parse_path(path)
                    signal = utl.access_by_path(dictionary[mode],path_parts)
                    if 'TicksInMses' in signal.keys() and 'GlobalPacketSizes' in signal.keys() and 'SampleRateInHz' in signal.keys():
                        TickInS = utl.string2numbers(signal['TicksInMses'])
                        GlobalPacketSizes = utl.string2numbers(signal['GlobalPacketSizes'][1:-1]) #take out [ ]
                        Fs = signal['SampleRateInHz']

                        if len(TickInS)!=0:
                            TickInS = (TickInS - TickInS[0])/1000 #convert from ms to s, and start from 0
                            if TickInS[-1]>sum(GlobalPacketSizes)/Fs:
                                #print('WARNING: MISSING PACKETS IN Path: ' + path)
                                check.append(path)
                                Warning(f"Missing packets in {mode}")
                            else: pass                    
                        else: 
                            #print('WARNING: No required keys or data in Path: ' + path)
                            check.append(path)
                            Warning(f"Missing keys or data in {mode}")

                    else: 
                        #print("ERROR: No required keys or data.")
                        check.append(path)
                        Warning(f"Missing keys or data in {mode}")
        
        if mode == 'Timeline':

            key_paths = utl.find_key_path(dictionary[mode],'DateTime')
            new_paths = []
            for path in key_paths: new_paths.append(f"['{mode}']" + path + "['DateTime']")
            
            for i in  range(len(new_paths)-1):
                path1 = utl.parse_path(new_paths[i+1])
                path2 = utl.parse_path(new_paths[i])

                time1 = utl.parse_datetime(utl.access_by_path(dictionary,path1))
                time2 = utl.parse_datetime(utl.access_by_path(dictionary,path2))
                delta = time2-time1
                minutes = np.round(delta.seconds/60,3)
                remainder = minutes%10
                if minutes >10 and remainder==0: #check if difference in time is bigger than 10 and multiple of ten, meaning lost a packet
                    print(new_paths[i])
                    check.append(new_paths[i])
                    Warning(f"Missing packets in {mode}")
                    

    return check

def getTimeTicksMs(TickInS,GlobalPacketSizes,Fs):
    return np.round(np.arange(start=TickInS[0],stop=TickInS[-1]+ (GlobalPacketSizes[-1]-1)/Fs ,step=1/Fs),3)

def getSessionDuration(Data):
    return utl.parse_datetime(Data['Device']['SessionEndDate'])-utl.parse_datetime(Data['Device']['SessionDate'])

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

def getRecordingDuration(mode, recording):

    match mode:
        case 'Survey':
            if 'TicksInMses' in recording.keys():
                Ticks = utl.string2numbers(recording['TicksInMses'])
                Fs = recording['SampleRateInHz']
                if len(Ticks)==0:
                    GlobalPacketSizes = utl.string2numbers(recording['GlobalPacketSizes'][1:-1])
                    temp_time = sum(GlobalPacketSizes)/Fs
                else:
                    Ticks = (Ticks - Ticks[0])/1000
                    temp_time = Ticks[-1]

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

def getStimulationParameters(dictionary, group_name, time = 'Final'):

    group_name = 'GroupIdDef.GROUP_' + group_name
    left = 0
    right = 1
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

    Left = [StimStatus,StimFreq,StimCurr,PulseWidth,AmplitudeType,BrainSenseStatus,Channel,Electrodes]

    StimCurr = stim['SensingChannel'][1]['SuspendAmplitudeInMilliAmps' ]
    BrainSenseStatus = stim['SensingChannel'][1]['BrainSensingStatus']
    Channel = utl.after_point(stim['SensingChannel'][1]['Channel'])
    Electrodes = getElectrodes(stim['SensingChannel'][1]['ElectrodeState'])
    PulseWidth = stim['SensingChannel'][1]['PulseWidthInMicroSecond']

    Right = [StimStatus,StimFreq,StimCurr,PulseWidth,AmplitudeType,BrainSenseStatus,Channel,Electrodes]

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
            recs = dictionary['Device']['DiagnosticData']['LFPTrendLogs']
            keys = list(recs.keys())
            for i in range(len(keys)): print(i,' - ', utl.after_point(keys[i]))
            hemisphere = input('What HEMISPHERE you want to analyze?')
            rec = recs[keys[int(hemisphere)]]
            total_duration = getRecordingDuration(mode,rec)
            '''
            raw = []
            for sample in rec:
                print(sample)
                raw.append(sample['LFP'])'''
            Fs = 1/600
            time_array = np.arange(0,total_duration,Fs)

        case 'Events': print(mode) 

        case 'Indefinite': 
            recs  = dictionary[mode]['IndefiniteStreaming']
            flag = 1

        case _: #SenseChannelTests or CalibrationTests
            recs = dictionary['Survey'][mode]
            flag = 1

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
        
        for rec in recs:
            if rec['FirstPacketDateTime'] == dates[d] and rec['Channel']==channels[c]:
                Fs = rec['SampleRateInHz']
                raw = rec['TimeDomainData']
                total_duration = getRecordingDuration(mode,rec)
                time_array = np.arange(0,total_duration,1/Fs)
                print('DATE: ',rec['FirstPacketDateTime'])

    signal = [time_array,raw[:len(time_array)]]

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


'''
data2 = getData(file_path1)

data1 = getData(file_path2)

print(data1['Device']['SessionDate'])
print(data2['Device']['SessionDate'])
merged = mergeJSONs(*sortJSONs([data1, data2]))
print(merged['Device']['SessionDate'])

rec = Data['Streaming']['BrainSenseTimeDomain'][0]
print(getRealTime('Streaming',rec)[0], ' : ', getRealTime('Streaming',rec)[-1] )
seconds = getRecordingDuration('Streaming',rec)
print(timedelta(seconds=seconds))
'''
