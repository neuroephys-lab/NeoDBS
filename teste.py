'''import DataHandling as DH
import matplotlib.pyplot as plt
import utils as utl
import numpy as np
import Preprocessing as pre'''
import matplotlib.pyplot as plt
import DataHandling as DH
import Preprocessing as pre
import utils as utl
from datetime import datetime
import os

# Set the base directory where JSON files are located
base_directory = "C:\\Users\\OCD\\Desktop\\DATA\\RN"  # Change this to your folder path

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

def run_json_files(directory):
    """Recursively find and execute JSON files."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        
                        Data = DH.getData(json_path)
                        print("--------------")                     
                        if 'Impedance' in Data['Device'].keys() and Data['Device']['Impedance']:
                            print(json_path)
                            print(Data['Device']['SessionDate'])
                            print(Data['Device']['Impedance'][0].keys())

                        elif Data['Device']['Impedance'] == []:
                            print(json_path) 
                            print('NOOOO:', Data['Device']['SessionDate'])
                             
                except Exception as e:
                    print(f"Error processing {json_path}: {e}")

def show_cut_signals(signals):
    i=0
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 6))
    axes = [ax1,ax2,ax3]

    for stream in signals:
        if i <3:
            channel = stream['Channel']
            date = stream['Date']

            new = DH.cutSignal(stream)
            x = new['X']
            y = new['Y']

            print(len(x),' : ',len(y))

            axes[i].plot(x, y, label=f"{channel}_raw")
            axes[i].set_title(f"{channel} - Raw Signal")
            axes[i].set_xlabel("Time (s)")
            axes[i].set_ylabel("LFP (µV)")
            axes[i].legend()

            i+=1

    plt.tight_layout()
    plt.show()

Data = DH.getData(file_path)
timeline = DH.getSignals(Data, 'Timeline')

arrays = []
for time in timeline:
    date = time['Left']['X'][-1]
    x = []

    for val in time['Left']['X']:
        date = utl.parse_datetime(val)
        new_date = datetime(year=1900, month=1, day=1, hour=date.hour, minute=date.minute)
        x.append(new_date)

    arrays.append(x)

max = -1
flag = -1
for i, xx in enumerate(arrays):
    if len(xx)>max: 
        max == len(xx)
        flag = i

x = arrays[flag]
plt.figure()
for time in timeline:
    for side in ['Left', 'Right']:
        sign = time[side]
        y = [float(val) for val in sign['Y']]
        '''if len(y)<len(x): 
            x = x[:len(y)]
        else: y = y[:len(x)]'''
        print(x)
        plt.plot(x,y,label = f"{time['Date']}-{side}")
plt.legend()
plt.show()

'''left = [utl.convert_to_timestamp(val) for val in time['Left']['X']]
right = [utl.convert_to_timestamp(val) for val in time['Right']['X']]

raw_left = time['Left']['X']
raw_right = time['Right']['X']

print(left[0],'|',raw_left[0],'------>',left[-1],'|',raw_left[-1])
print(right[0],'|',raw_right[0],'------>',right[-1],'|',raw_right[-1])'''

        
    

'''

for recent in Data['Setup']['MostRecentInSessionSignalCheck']:
    print(recent['Channel'])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))  # 1 row, 2 columns

# Plot raw signal in the first subplot
ax1.plot(x, y, label=f"{channel}_raw")
ax1.set_title(f"{channel} - Raw Signal")
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("LFP (µV)")
ax1.legend()

# Plot cleaned signal in the second subplot
ax2.plot(new_x, new_y, label=f"{channel}_cleaned", color='orange')
ax2.set_title(f"{channel} - Cleaned Signal")
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("LFP (µV)")
ax2.legend()

# Adjust layout
plt.tight_layout()
plt.show()


file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-12-19\\Report_Json_Session_Report_20250212T121933.json"

#Setup: Impedance + MostRecentInSessionSignalCheck
#Survey: Impedance only

Data = DH.getData(file_path)

print(Data['Device']['Impedance' ][-1]['Hemisphere'][1]['SessionImpedance'].keys())


#plt.show()

plt.figure()
for rec in recs:
    print(rec)
    x = rec['X']
    y = rec['Y']
    plt.plot(x,y,label = rec['Channel'])

plt.legend()

recent = Data['Device']['MostRecentInSessionSignalCheck'] #PSD - Survey da sessão 
if recent:
    plt.figure()
    for stream in recent:
        channel = stream['Channel']
        x = stream['SignalFrequencies']
        y = stream['SignalPsdValues']
        peak_x = stream['PeakFrequencies']
        peak_y = stream['PeakValues']
        plt.plot(x,y,label=utl.after_point(channel))
        plt.scatter(peak_x,peak_y)

    plt.legend()

survey = DH.getSignals(Data,'LFPTimeDomain')

if survey:
    plt.figure()
    for stream in survey:
        channel = stream['Channel']
        x = stream['SignalFrequencies']
        y = stream['SignalPsdValues']
        peak_x = stream['PeakFrequencies']
        peak_y = stream['PeakValues']
        plt.plot(x,y,label=utl.after_point(channel))
        plt.scatter(peak_x,peak_y)

    plt.legend()
    
plt.show()'''

#space
print()
'''
recs = DH.getSignals(Data,'Setup')

plt.figure()

i = 0
for rec in recs:
    sense, calibration = recs
    for c in sense:
        x = c['X']
        y = c['Y']
        plt.plot(x,y,label=f"sense {c['Channel']} - {c['Date']}")
        i+=1
    for c in calibration:
        x = c['X']
        y = c['Y']
        plt.plot(x,y,label=f"Calibration {c['Channel']} - {c['Date']}")
        i+=1

print(i)
plt.legend()
plt.show()

signals = DH.getSignals(Data,'CalibrationTests')

plt.figure('Calibration')
for signal in signals:
    x = signal['X']
    y = signal['Y']
    plt.plot(x,y,label=f"{signal['Channel']}")
plt.legend()

signals = DH.getSignals(Data,'SenseChannelTests')

plt.figure('SenseChannelTests')
for signal in signals:
    x = signal['X']
    y = signal['Y']
    plt.plot(x,y,label=f"{signal['Channel']}")

signals = DH.getSignals(Data,'Indefinite')
plt.legend()

plt.figure('Indefinite')
for signal in signals:
    x = signal['X']
    y = signal['Y']
    plt.plot(x,y,label=f"{signal['Channel']}")

plt.legend()


plt.show()
'''


#2025-01-23T11:14:07.000Z
#dict_keys(['Pass', 'GlobalSequences', 'GlobalPacketSizes', 'TicksInMses', 
# 'Channel', 'Gain', 'FirstPacketDateTime', 'SampleRateInHz', 'TimeDomainData'])

'''
mine = DH.checkMissingData(Data)

print('----------MINE--------------')
for m in mine: print(m)

plt.figure()
plt.plot(time,signal)
plt.show()

missing = DH.checkMissingData(Data)

def unwrap(x, cap=None):
    if cap is None:
        cap = np.max(x) + 1
    
    unwrappedX = np.array(range(len(x)))
    unwrappedX[0] = x[0]
    currentRolls = 0
    for n in range(1,len(x)):
        if x[n] < x[n-1]:
            currentRolls += cap
        unwrappedX[n] = x[n] + currentRolls
    
    return unwrappedX

def checkMissingPackage(Data):
    if "IndefiniteStreaming" in Data['Indefinite'].keys():
        Data = Data['Indefinite']
        for nStream in range(len(Data["IndefiniteStreaming"])):
            TDSequences = unwrap(utl.string2numbers(Data["IndefiniteStreaming"][nStream]["GlobalSequences"][1:-1]), cap=256) #unwrap?
            raw_len = len(Data["IndefiniteStreaming"][nStream]["TimeDomainData"])
            print(f"{nStream} | TD: {raw_len} | GS: {TDSequences[-1]} ")
            missingSequence = list()
            for n in range(1,len(TDSequences)):
                jumppedSequence = TDSequences[n]-TDSequences[n-1]
                if jumppedSequence > 1:
                    print(nStream, ':', TDSequences[n-1], '-->', TDSequences[n])
                    print(TDSequences[n-1:])
                    missingIndexes = np.array(range(1, jumppedSequence)) + TDSequences[n-1]
                    missingSequence.extend(missingIndexes)
                    #print(f"Sequence {n}: {missingIndexes}")
                    
            Data["IndefiniteStreaming"][nStream]["Missing"] = np.zeros(len(Data["IndefiniteStreaming"][nStream]['TimeDomainData']))
            PacketSize = int(np.mean(utl.string2numbers(Data["IndefiniteStreaming"][nStream]["GlobalSequences"][1:-1])))
            if len(missingSequence) > 0:
            #for nMissing in missingSequence:
            #    insertionIndex = np.where(TDSequences < nMissing)[0][-1] + 1
                startIndex = int(np.sum(utl.string2numbers(Data["IndefiniteStreaming"][nStream]["GlobalSequences"][1:-1])))
            #    TDSequences = np.concatenate((TDSequences[:insertionIndex], [nMissing], TDSequences[insertionIndex:]))
            #    Data["IndefiniteStreaming"][nStream]["GlobalPacketSizes"] = np.concatenate((utl.string2numbers(Data["IndefiniteStreaming"][nStream]["GlobalSequences"][1:-1])[:insertionIndex], [PacketSize], TDSequences[insertionIndex:]))
            #    Data["IndefiniteStreaming"][nStream]["Data"] = np.concatenate((Data["IndefiniteStreaming"][nStream]["TimeDomainData"][:startIndex],np.zeros((PacketSize)),Data["IndefiniteStreaming"][nStream]["TimeDomainData"][startIndex:]))
                Data["IndefiniteStreaming"][nStream]["Missing"] = np.concatenate((Data["IndefiniteStreaming"][nStream]["Missing"][:startIndex],np.ones((PacketSize)),Data["IndefiniteStreaming"][nStream]["Missing"][startIndex:]))
                #Data["IndefiniteStreaming"][nStream]["Time"] = np.array(range(len(Data["IndefiniteStreaming"][nStream]["TimeDomainData"]))) / Data["IndefiniteStreaming"][nStream]["SamplingRateinHz"]
                #print(f"Warning: Missing sequence occured for Stream #{nStream}, Data insertion complete. Check ['Missing'] field.")
    ###       
    if "StreamingTD" in Data.keys() and "StreamingPower" in Data.keys():
        if len(Data["StreamingTD"]) != len(Data["StreamingPower"]):
            raise Warning("Number of stream in Time-domain does not match number of stream in Power channel")
            
        for nStream in range(len(Data["StreamingTD"])):
            Data["StreamingTD"][nStream]["Missing"] = np.zeros(Data["StreamingTD"][nStream]["Data"].shape)
            Data["StreamingPower"][nStream]["Missing"] = np.zeros((Data["StreamingPower"][nStream]["Power"].shape[0]))
            
            # TicksInMs
            ChangesInMs = np.diff(Data["StreamingTD"][nStream]["Ticks"])
            TimePerPackage = np.median(ChangesInMs)
            if len(np.where(ChangesInMs < 0)[0]) > 0:
                print("TicksInMs Revamped")
                raise Exception("Bad Format in TicksInMs")
            
            TimePerPacket = np.median(ChangesInMs)
            MissingPacket = np.where(ChangesInMs > TimePerPacket)[0] + 1
            TDSequences = np.arange(len(Data["StreamingTD"][nStream]["Ticks"]))
            
            # is all missing sequence accounted for?
            PacketSize = int(np.mean(Data["StreamingTD"][nStream]["GlobalPacketSizes"]))
            if len(MissingPacket) > 0:
                for missingIndex in MissingPacket:
                    if not ChangesInMs[missingIndex-1] % TimePerPacket == 0:
                        print(f"TicksInMs Reversed for {nStream}")
                        #raise Exception("Time Skip is not full package drop")
                        
                    numMissingPacket = int(ChangesInMs[missingIndex-1] / TimePerPacket - 1)
                    insertionIndex = np.where(TDSequences < missingIndex)[0][-1] + 1
                    startIndex = int(np.sum(Data["StreamingTD"][nStream]["GlobalPacketSizes"][:insertionIndex]))
                    TDSequences = np.concatenate((TDSequences[:insertionIndex], np.zeros(numMissingPacket), TDSequences[insertionIndex:]))
                    Data["StreamingTD"][nStream]["GlobalPacketSizes"] = np.concatenate((Data["StreamingTD"][nStream]["GlobalPacketSizes"][:insertionIndex], PacketSize*np.ones(numMissingPacket), Data["StreamingTD"][nStream]["GlobalPacketSizes"][insertionIndex:]))
                    Data["StreamingTD"][nStream]["Data"] = np.concatenate((Data["StreamingTD"][nStream]["Data"][:startIndex],np.zeros((PacketSize*numMissingPacket)),Data["StreamingTD"][nStream]["Data"][startIndex:]))
                    Data["StreamingTD"][nStream]["Missing"] = np.concatenate((Data["StreamingTD"][nStream]["Missing"][:startIndex],np.ones((PacketSize*numMissingPacket)),Data["StreamingTD"][nStream]["Missing"][startIndex:]))
                Data["StreamingTD"][nStream]["Time"] = np.array(range(len(Data["StreamingTD"][nStream]["Data"]))) / Data["StreamingTD"][nStream]["SamplingRate"]
                #print(f"Warning: Missing sequence occured for Stream #{nStream}, Data insertion complete. Check ['Missing'] field.")
            
            # Check Power Channel Now
            ChangesInMs = np.around(np.diff(Data["StreamingPower"][nStream]["Time"]),3)
            if len(np.where(ChangesInMs < 0)[0]) > 0:
                print("TicksInMs Reversed")
                raise Exception("Bad Format in TicksInMs for Power Channel")
            
            TimePerPacket = np.percentile(ChangesInMs,5)
            MissingPacket = np.where(ChangesInMs > TimePerPacket)[0] + 1
            
            if len(MissingPacket) > 0:
                newTimestamp = np.arange(Data["StreamingPower"][nStream]["Time"][0], Data["StreamingPower"][nStream]["Time"][-1]+TimePerPacket, TimePerPacket)
                processedPower = np.zeros((len(newTimestamp),2))
                processedStimulation = np.zeros((len(newTimestamp),2))
                Data["StreamingPower"][nStream]["Missing"] = np.zeros((len(newTimestamp)))
                for i in range(2):
                    processedPower[:,i] = np.interp(newTimestamp, Data["StreamingPower"][nStream]["Time"], Data["StreamingPower"][nStream]["Power"][:,i])
                    processedStimulation[:,i] = np.interp(newTimestamp, Data["StreamingPower"][nStream]["Time"], Data["StreamingPower"][nStream]["Stimulation"][:,i])
                
                for t in range(len(newTimestamp)):
                    if not newTimestamp[t] in Data["StreamingPower"][nStream]["Time"]:
                        Data["StreamingPower"][nStream]["Missing"][t] = 1
                        
                Data["StreamingPower"][nStream]["Power"] = processedPower
                Data["StreamingPower"][nStream]["Stimulation"] = processedStimulation
                Data["StreamingPower"][nStream]["Time"] = newTimestamp
                
            # Compensate for shifting less than 500ms, which will be indicated by the TickInMs
            TimeShift = Data["StreamingPower"][nStream]["InitialTickInMs"] - Data["StreamingTD"][nStream]["Ticks"][0] / 1000
            if TimeShift < -1000:
                TimeShift = np.round(TimeShift+3276.8,2)
            elif TimeShift > 1000:
                TimeShift = np.round(TimeShift-3276.8,2)
            else:
                TimeShift = np.round(TimeShift,2)
            Data["StreamingPower"][nStream]["Time"] += TimeShift
            #print(f"Warning: Missing sequence occured for Stream #{nStream}, Data insertion complete. Check ['Missing'] field.")
            ###
    

#bravo = checkMissingPackage(Data)

plt.figure()
for i in range(len(Data['Indefinite']['IndefiniteStreaming'])):
    seq = utl.string2numbers(Data['Indefinite']['IndefiniteStreaming'][i]['GlobalSequences'][1:-1])
    plt.plot(seq,'o')
    plt.legend()

plt.show()

'''