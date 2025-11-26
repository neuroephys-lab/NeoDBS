from DataHandling import *
import json

def getSignal(dictionary,mode): #unused
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
            # for i in range(len(keys)): print(i,' - ', utl.after_point(keys[i]))
            hemisphere = input('What HEMISPHERE you want to analyze?')
            rec = recs[keys[int(hemisphere)]]
            total_duration = getRecordingDuration(mode,rec)
            print(total_duration)
            Fs = 1/600
            time_array = np.arange(0,total_duration,Fs)

        # case 'Events': 
        #     print(mode) 


        case 'Indefinite': 
            recs  = dictionary[mode]['IndefiniteStreaming']
            flag = 1

        case _: #SenseChannelTests or CalibrationTests
            recs = dictionary['Survey']
            flag = 2

            types = list(recs.keys())
            type = int(input('Which RECORDING would you like to analyze? (number)'))
            type = types[type]
            recs= recs[type]

            dates = []
            channels = []

            for rec in recs: dates.append(rec['FirstPacketDateTime'])
            dates = np.unique(dates)
                            
            d = int(input('Which RECORDING would you like to analyze? (number)'))

            for rec in recs:
                if rec['FirstPacketDateTime'] == dates[d]:
                    channels.append(rec['Channel'])

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

def mergeJSONs(data1, data2): #unused
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

def interpolateTimelineStream(signal):#unused

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

def getStimulationParameters(dictionary, group_name, time = 'Initial'): #unused

    group_name = 'GroupIdDef.GROUP_' + group_name
    #left = 0
    #right = 1
    if time == 'Final':
        time_ = 'FinalStimStatus'
    else:
        time_ = 'InitialStimStatus'
    
    stim = next((group for group in dictionary['Device']['Groups'][time] if group['GroupId'] == group_name), None)
    # print(stim)
    # stim = dictionary['Device']['GroupHistory'][0]['Groups'][0]
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

def getSetupInfo(dictionary,group_name): #unused

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

def correctMissingData(dictionary,path): #unused

    '''
    NaN where there is missing data, path: path of previously identified missing data, by checkingMissingData
    '''
    path_parts = utl.parse_path(path)[:-1] #until the key before
    #signal = access_by_path(dictionary,path_parts)
    new_path = ""
    for part in path_parts:
        new_path = new_path + f"[{part}]"
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

def sortJSONs(json_list): #unused
    """Sort a list of JSON objects by 'SessionEndDate' in ascending order."""
    try:
        json_list.sort(key=lambda x: datetime.strptime(x['SessionEndDate'], "%Y-%m-%dT%H:%M:%SZ"))
    except KeyError:
        print("One or more JSON objects are missing 'SessionEndDate'")
    except ValueError:
        print("Invalid date format in one or more JSON objects")
    
    return json_list

def getRealTime(mode, recording): #unused
    
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

def cutSignal(signal, initial=0, end=-1): #unused
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

def removeDuplicates(lst): #unused
    """Remove duplicate entries from a list while maintaining order."""
    seen = set()
    return [x for x in lst if not (tuple(x.items()) if isinstance(x, dict) else x) in seen and not seen.add(tuple(x.items()) if isinstance(x, dict) else x)]

def concatenateLists(JSONs, keys): #unused
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

def listSort(lst, indices):#unused
    """Sort a list based on given indices."""
    return [lst[i] for i in indices]

def concatenateJSONs(JSONs):#unused
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

def getAllRecordingDuration(dictionary): #unused
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

def getLogDuration(log): #unused
    TickI = utl.parse_datetime(log[-1]['DateTime']).timestamp()   
    TickF = utl.parse_datetime(log[0]['DateTime']).timestamp()  
    temp_time = (TickF - TickI)/1000

    return temp_time

def getTimelineBand(Data): #unused
    # return Data['Device']['GroupHistory'][0]['Groups'][0]
    central = Data['Device']['Groups']['Final'][0]['ProgramSettings']['SensingChannel'][0]['SensingSetup']['FrequencyInHertz']
    band_values = [np.round(central-2.5,2), np.round(central+2.5,2)]
    band = {
        str(band_values): band_values
    }
    return band

def getTimeTicksMs(TickInS,GlobalPacketSizes,Fs): #unused
    return np.round(np.arange(start=TickInS[0],stop=TickInS[-1]+ (GlobalPacketSizes[-1]-1)/Fs ,step=1/Fs),3)

def segmentTimelineEvent2(timeline, indexes):
    segments = {}
    flags = []
    for edx, idxs in indexes.items():
        if isinstance(idxs,str):
            print(idxs)
        else:
            x, signal = idxs
            segments[edx] = {}
            for side in ['Left', 'Right']:

                stream = timeline[signal][side]

                if x<6: 
                    mini,maxi = 0, 12
                    flags.append(True)
                elif x+6 > len(stream['X']):
                    maxi = len(stream['X'])-1
                    mini = maxi-6
                    flags.append(True)
                else: 
                    mini,maxi =  x-6, x+6
                    flags.append(False)

                #for dpg
                xx = stream['X'][mini:maxi]
                # temp = [utl.parse_datetime(x) for x in xx]
                temp = xx
                # print(abs(temp[0]-temp[-1]))
                # if abs(temp[0]-temp[1])<timedelta(hours=2, minutes=20):
                #     yy = stream['Y'][mini:maxi]
                #     segment = {'X': xx, 'Y': yy}
                #     segments[edx][side] =  segment


                if isinstance(temp[0], datetime) and isinstance(temp[-1], datetime):
                    duration = abs(temp[-1] - temp[0])
                    if duration < timedelta(hours=2, minutes=20):
                        if f'Filtered_{side}' in timeline[signal].keys():
                            yy = timeline[signal][f'Filtered_{side}']
                        else: yy = stream['Y'][mini:maxi]
                        segment = {'X': xx, 'Y': yy}
                        segments[edx][side] = segment
                    elif edx in segments.keys(): segments.pop(edx)

    return segments, flags

def segmentTimelineEvent(timeline, indexes, step_minutes=10):
    segments = {}
    flags = []

    for edx, idxs in indexes.items():
        if isinstance(idxs, str):
            print(idxs)
            continue

        x, signal = idxs  # x is an index into the X/Y arrays (int)
        segments[edx] = {}

        for side in ['Left', 'Right']:
            X_raw = timeline[signal][side]['X']
            if f'Filtered_{side}' in timeline[signal].keys():
                Y_raw = timeline[signal][f'Filtered_{side}']
            else:
                Y_raw = timeline[signal][side]['Y']

            # Convert string timestamps to datetime objects
            X_dt = [utl.parse_datetime(t) for t in X_raw]

            half_window = 6
            window_size = 13
            padded = False

            # Determine padding
            pad_left = max(0, half_window - x)
            pad_right = max(0, x + half_window + 1 - len(X_dt))

            min_idx = max(0, x - half_window)
            max_idx = min(len(X_dt), x + half_window + 1)

            # Slice available data
            segment_x_dt = X_dt[min_idx:max_idx]
            segment_y = Y_raw[min_idx:max_idx]

            # Pad left if needed
            if pad_left > 0:
                first_time = X_dt[min_idx]
                left_fill = [first_time - timedelta(minutes=step_minutes * i) for i in range(pad_left, 0, -1)]
                segment_x_dt = left_fill + segment_x_dt
                segment_y = [np.nan] * pad_left + segment_y
                padded = True

            # Pad right if needed
            if pad_right > 0:
                last_time = X_dt[max_idx - 1]
                right_fill = [last_time + timedelta(minutes=step_minutes * i) for i in range(1, pad_right + 1)]
                segment_x_dt = segment_x_dt + right_fill
                segment_y = segment_y + [np.nan] * pad_right
                padded = True

            # Final sanity check
            segment_x_dt = segment_x_dt[:window_size]
            segment_y = segment_y[:window_size]

            segment_x = [utl.full_date2str(dt) for dt in segment_x_dt]

            segments[edx][side] = {'X': segment_x, 'Y': segment_y}
            flags.append(padded)

    return segments, flags

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

def getTimelineIndexofEventRaw(timeline, events):
    #Retrieving timeline RAW
    index = {}
    flag = False

    for idx,e in enumerate(events):
        xe = utl.parse_datetime(e['DateInitial'])
        key = str(idx) + f"_{e['EventName']}"
        for j,t in enumerate(timeline):
            xt = t['Left']['X']
            xt = [utl.parse_datetime(x) for x in xt]
            # Loop with enumerate to get index
            for i, x in enumerate(xt):
                if abs(x - xe) < timedelta(minutes=10):
                    
                    index[key] = [i,j]
                    flag = True
                    break
        if flag==False:
            index[key] = f'{xe}: Event not present in any Timeline Stream'

    return index

def getTimelineIndexofEvent(timeline, events):
    #Retrieving timeline RAW
    index = {}
    flag = False

    for idx,e in enumerate(events):
        xe = utl.parse_datetime(e['DateInitial'])
        key = str(idx) + f"_{e['EventName']}"
        for j,t in enumerate(timeline):
            xt = t['Left']['X']
            # Loop with enumerate to get index
            for i, x in enumerate(xt):
                if abs(x - xe) < timedelta(minutes=10):
                    index[key] = [i,j]
                    flag = True
                    break
        if flag==False:
            index[key] = f'{xe}: Event not present in any Timeline Stream'

    return index


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
