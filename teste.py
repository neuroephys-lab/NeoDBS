import DataHandling as DH
import matplotlib.pyplot as plt
import utils as utl

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

Data = DH.getData(file_path)

signals = DH.getSignals(Data,'Timeline')

plt.figure()
for signal in signals:
    plt.title('Timeline')
    for side in ['Left','Right']:   
        sign = signal[side]
        date = utl.parse_datetime(signal['Date'])
        label = f"{side} - day {date.day}/{date.month}"
        x = sign['X']
        y = sign['Y']
        plt.plot(sign['X'],sign['Y'],label=label)


plt.legend()
plt.show()


'''
plt.legend()
plt.grid(True)
plt.show()

signals = []
for side in recs:
    print(side)
    for day in recs[side].keys():
        print(day)
        LFP = []
        time = []
        logs = recs[side][day]
        for log in logs:
            LFP.append(log['LFP'])
            time.append(log['DateTime']) 
        if utl.after_point(side) == 'Left':
            left= {
                'X': time,
                'Y': LFP
            }
        else:
            right= {
                'X': time,
                'Y': LFP
            }
    signal = {
        'Date': day,
        'Left': left,
        'Right': right
    }

    signals.append(signal)

signals = DH.getSignals(Data,'Events')

plt.figure()
for signal in signals:
    x = signal['Raw']['X']
    y = signal['Raw']['Y']
    plt.plot(x,y,label=f"Signal {signals.index(signal) +1}")
plt.legend()
plt.grid(True)
plt.show()'''


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