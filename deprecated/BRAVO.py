from datetime import datetime, timezone
import numpy as np
import DataHandling as DH # type: ignore

def arrayCompare(first, second):
    return np.array_equal(first, second)

def concatenateLists(array, args):
    if len(args) > 1:
        newArray = [subArray[args[0]] for subArray in array if args[0] in subArray.keys()]
        return concatenateLists(newArray, args[1:])
    
    newList = list()
    for i in range(len(array)):
        if args[0] in array[i].keys(): 
            if type(array[i][args[0]]) == list:
                newList.extend(array[i][args[0]])
            else:
                newList.append(array[i][args[0]])
    return newList

def removeDuplicates(originalList, type="all"):
    finalList = []
    for item in originalList:
        notFound = True
        for finalItem in finalList:
            if type == "Data":
                if "Data" in item.keys() and "Data" in finalItem.keys():
                    if arrayCompare(item["Data"], finalItem["Data"]):
                        notFound = False
                        break
                if "Power" in item.keys() and "Power" in finalItem.keys():
                    if arrayCompare(item["Power"], finalItem["Power"]):
                        notFound = False
                        break
            else:
                if dictionaryCompare(item, finalItem):
                    notFound = False
                    break
        if notFound:
            finalList.append(item)
    return finalList

def listSort(oldList, newIndexes):
    return [oldList[i] for i in newIndexes]

def concatenateJSONs(JSONs):
    # Get the list of fields in all JSONs
    allJsonFields = list()
    for JSON in JSONs:
        allJsonFields.extend(JSON.keys())
    allJsonFields = removeDuplicates(allJsonFields)
    
    CompiledJSON = dict()
    for field in allJsonFields:
        if field == "DiagnosticData":
            CompiledJSON[field] = dict()
            subFields = list()
            for JSON in JSONs:
                if field in JSON.keys():
                    subFields.extend(JSON[field].keys())
            subFields = removeDuplicates(subFields)
            
            for subfield in subFields:
                if subfield == "LFPTrendLogs":
                    CompiledJSON[field][subfield] = dict()
                    
                    for JSON in JSONs:
                        if field in JSON.keys():
                            if subfield in JSON[field].keys():
                                hemisphereDefinitions = list(JSON[field][subfield].keys())
                    
                    for hemisphere in hemisphereDefinitions:
                        CompiledJSON[field][subfield][hemisphere] = dict()
                        
                        dates = list()
                        for JSON in JSONs:
                            if field in JSON.keys():
                                if subfield in JSON[field].keys():
                                    # No check for hemisphere, assuming that hemisphere always exist..... can we?
                                    dates.extend(JSON[field][subfield][hemisphere].keys())
                        dates = removeDuplicates(dates)
                        
                        # Quick Note: Dates here are very confusing. I do not think the Hour/Minutes/Seconds actually matter. 
                        # It is best to concatenate everything and store in one single dictionary in the combined JSON.
                        allLFPTrends = list()
                        for date in dates:
                            allLFPTrends.extend(concatenateLists(JSONs, [field, subfield, hemisphere, date]))
                        allLFPTrends = removeDuplicates(allLFPTrends)
                        Timestamp = [datetime.fromisoformat(allLFPTrends[i]["DateTime"][:-1]+"+00:00").timestamp() for i in range(len(allLFPTrends))]
                        allLFPTrends = listSort(allLFPTrends, np.argsort(Timestamp))
                        CompiledJSON[field][subfield][hemisphere][allLFPTrends[0]["DateTime"]] = allLFPTrends
                
                elif subfield == "EventLogs":
                    CompiledJSON[field][subfield] = concatenateLists(JSONs, [field, subfield])
                    CompiledJSON[field][subfield] = removeDuplicates(CompiledJSON[field][subfield])
                    Timestamp = [datetime.fromisoformat(CompiledJSON[field][subfield][i]["DateTime"][:-1]+"+00:00").timestamp() for i in range(len(CompiledJSON[field][subfield]))]
                    CompiledJSON[field][subfield] = listSort(CompiledJSON[field][subfield], np.argsort(Timestamp))
                    
                # Skipping PSD Logs for now. Test dataset do not contain them.
        
        # Critical Check: Are we looking at the JSONs of the same patient?
        elif field == "PatientInformation" or field == "LeadConfiguration":
            CompiledJSON[field] = concatenateLists(JSONs, [field])
            CompiledJSON[field] = removeDuplicates(CompiledJSON[field])
            if len(CompiledJSON[field]) > 1:
                print(f"Multiple {field}. Are you sure this is the same patient?")
                raise(TypeError)
            CompiledJSON[field] = CompiledJSON[field][0]
        
        # Minor Check. It is possible they are different, we will take only the first occurance
        elif field == "BatteryInformation" or field == "DeviceInformation" or field == "GroupUsagePercentage" or field == "Stimulation" or field == "BatteryReminder":
            CompiledJSON[field] = concatenateLists(JSONs, [field])
            CompiledJSON[field] = removeDuplicates(CompiledJSON[field])
            if len(CompiledJSON[field]) > 1:
                Warning(f"Multiple {field}. Are you sure this is the same patient?")
            CompiledJSON[field] = CompiledJSON[field][0]
        
        # They are list without time. Concat and remove duplicate.
        # Event Summary is a fun one. We should make that into an array even though originally was a dictionary.
        elif field == "Impedance" or field == "MostRecentInSessionSignalCheck" or field == "EventSummary":
            CompiledJSON[field] = concatenateLists(JSONs, [field])
            CompiledJSON[field] = removeDuplicates(CompiledJSON[field])
        
        # GroupHistory is an interesting case. If a setting is changed then the later GroupHistory will be influenced.
        #   This is a very troublesome condition, the initial true history will not be stored for future JSONs. 
        #   Need to consult Medtronic for more information
        elif field == "GroupHistory":
            CompiledJSON[field] = concatenateLists(JSONs, [field])
            CompiledJSON[field] = removeDuplicates(CompiledJSON[field])
            Timestamp = [datetime.fromisoformat(CompiledJSON[field][i]["SessionDate"][:-1]+"+00:00").timestamp() for i in range(len(CompiledJSON[field]))]
            CompiledJSON[field] = listSort(CompiledJSON[field], np.flip(np.argsort(Timestamp)))
        
        # Groups is as confusing as GroupHistry. This is also modifiable in the middle of the recording.
        # Do we care about the change? What do we really need in this structure? If we get all that we want from GroupHistory
        elif field == "Groups":
            CompiledJSON[field] = concatenateLists(JSONs, [field])
            CompiledJSON[field] = removeDuplicates(CompiledJSON[field])
            if len(CompiledJSON[field]) > 1:
                Warning(f"Multiple {field}. Therapy Changed, but only the last JSON is taken")
            CompiledJSON[field] = CompiledJSON[field][-1]

        elif field == "SenseChannelTests" or field == "CalibrationTests" or field == "LfpMontageTimeDomain" or field == "LFPMontage": 
            CompiledJSON[field] = concatenateLists(JSONs, [field])
            CompiledJSON[field] = removeDuplicates(CompiledJSON[field])
            
        elif field == "BrainSenseTimeDomain" or field == "BrainSenseLfp" or field == "IndefiniteStreaming": 
            CompiledJSON[field] = concatenateLists(JSONs, [field])
            CompiledJSON[field] = removeDuplicates(CompiledJSON[field])
        
        else: 
            CompiledJSON[field] = concatenateLists(JSONs, [field])
            CompiledJSON[field] = removeDuplicates(CompiledJSON[field])
            if len(CompiledJSON[field]) > 1:
                Warning(f"Multiple {field}. Are you sure this is the same patient?")
            CompiledJSON[field] = CompiledJSON[field][0]
            
    return CompiledJSON

def dictionaryCompare(first, second):
    if type(first) == list:
        if not len(first) == len(second):
            return False
        
        for i in range(len(first)):
            if not dictionaryCompare(first[i], second[i]):
                return False
    else:
        try:
            return first == second
        except:
            if not second.keys() == first.keys():
                return False
            
            for key in first.keys():
                if not type(first[key]) == type(second[key]):
                    return False
                
                if type(first[key]) == dict:
                    if not dictionaryCompare(first[key], second[key]):
                        return False
                
                elif type(first[key]) == np.ndarray:
                    if not np.all(first[key] == second[key]):
                        return False
                    
                elif type(first[key]) == list:
                    return False
                
                else:
                    if not first[key] == second[key]:
                        return False
    return True

'''file_path1 = 'C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162023.json'
file_path2 = 'C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json'

data1 = DH.getData(file_path1)
data2 = DH.getData(file_path2)
merged = concatenateJSONs([data2,data1])

print(data1['Device']['SessionEndDate'])
print(data2['Device']['SessionEndDate'])
print(merged['Device']['SessionEndDate'])

print(DH.getSessionDuration(data1))
print(DH.getSessionDuration(data2))
print(DH.getSessionDuration(merged))'''