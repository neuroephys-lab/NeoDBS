import numpy as np
from datetime import datetime
import re

def find_key_path(dictionary, target_key, path=""):
    '''
    Recursively finds and prints the path of a key in a nested dictionary (including lists).

    :param dictionary: dict, list
    :param target_key: int/str
    :param path: str, optional. Looks for target_key in dictionary[path] ex.: path = '[key1][key2]'

    :return: list, names of all paths that lead to target_key

    '''

    key_paths = []  # Collect key paths in a list
    
    if isinstance(dictionary, dict):  # If it's a dictionary, iterate through keys
        for key, value in dictionary.items():
            new_path = f"{path}['{key}']" if path else f"['{key}']"  # Build path
            if key == target_key:
                key_paths.append(new_path)  # Add the found path
            key_paths.extend(find_key_path(value, target_key, new_path))  # Collect results from recursion

    elif isinstance(dictionary, list):  # If it's a list, iterate through elements
        for index, item in enumerate(dictionary):
            new_path = f"{path}[{index}]"  # Append list index to path
            key_paths.extend(find_key_path(item, target_key, new_path))  # Collect results from recursion

    return key_paths

def string2numbers(string):
    '''
    Converts string with numbers separated by ',' (TicksInMs) into a np.array. Example: '1,2,3,,4,6,7' --> np.array([1,2,3,4,6,7])
    
    :param string: str

    :return: np.ndarray

    '''
    return np.array([int(num) for num in string.split(',') if num.strip()!=' ' and num.strip()!=''])

def parse_path(path):
    '''
    Convert the string path into a list of keys and indices. Example: '[key1][key2]' --> [key1,key2]

    :param path: str

    :return: list

    '''
    path_parts = []
    
    # Match keys, indices, and quoted keys
    parts = re.findall(r"\['(.*?)'\]|\[(\d+)\]", path)
    
    for key, index in parts:
        if index:  # If it's an index (a number inside brackets)
            path_parts.append(int(index))  # Convert to integer
        else:
            path_parts.append(key)  # Keep it as a string key
    
    return path_parts

def convert_to_timestamp(date_input):
    '''
    Converts date_input into timestamp.

    :param date_input: datetime, str

    :return: float

    '''
    if isinstance(date_input, datetime):
        return date_input.timestamp()
    elif isinstance(date_input, str):
        try:
            return datetime.fromisoformat(date_input.replace("Z", "")).timestamp()
        except ValueError:
            print(f"Invalid date format: {date_input}")
            return None
    elif isinstance(date_input, (int,float)):
        return date_input
    else:
        print(f"Unsupported type for date input: {type(date_input)}")
        return None

def access_by_path(dictionary, path_parts):
    '''
    Access the dictionary by the provided list of keys/indices.

    :param dictionary: dict, list
    :param path_parts: list

    '''
    value = dictionary
    for part in path_parts[:-1]:
        value = value[part]
    return value

def after_point(s):
    '''
    Extracts string after finding '.'
    
    :param s: str

    :return: str

    '''
    start_index = s.find('.')
    if start_index != -1:
        return s[start_index + 1:]
    else:
        return ''
    
def after_underscore(s):
    '''
    Extracts string after finding '_'
    
    :param s: str

    :return: str

    '''
    start_index = s.find('_')
    if start_index != -1:
        return s[start_index + 1:]
    else:
        return s

def parse_datetime(string):
    '''
    Converts string into datetime.datetime object.

    :param string: str, "%Y-%m-%dT%H:%M:%S.%fZ" OR "%Y-%m-%dT%H:%M:%SZ" OR "%Y-%m-%d %H:%M:%S"

    :return: datetime.datetime object

    '''
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(string, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {string}")

def parse_time(string):
     '''
     Converts time string into datetime.datetime object.

     :param string: str, "%H:%M:%S"

     :return: datetime.datetime object

     '''
     return datetime.strptime(string, "%H:%M:%S")

def find_closest_index(new_time, target_hour, target_minute, target_second = 0):
    '''
    Finds the index of the sample in new_time closest to the given hour and minute.
    
    :param new_time: datetime.datetime, target date
    :param target_hour: int/float
    :param target_minute: int/float
    :param target_second: int/float

    :return: int, if the target time is out of bounds return None.

    '''
    target_time = datetime(new_time[0].year, new_time[0].month, new_time[0].day, target_hour, target_minute, target_second)

    big, small = max(new_time), min(new_time)
    if target_time > big or target_time < small:
        return None  # Return None if the target time is out of range

    time_diffs = [abs((t - target_time).total_seconds()) for t in new_time]
    closest_idx = np.argmin(time_diffs)
    
    return closest_idx

def read_lines(filename):
    '''
    Converts txt file into dictionary, with firts line being key.

    :param filename: str, must be path/file.txt

    :return: dict 

    '''
    info = {}
    name = ""
    with open(filename, 'r', encoding='utf-8') as file:
        for idx,line in enumerate(file):
            line = line.strip()
            if line == '': line = np.nan
            if idx==0: 
                info[line] = []
                name=line
            else:
                info[name].append(line)
    return info

def read_event_file(filename):
    '''
    Reads a text file and returns a list of (hour, minute, second, event) tuples.
    If seconds are not provided, they default to 0.

    :param filename: str, must be path/file.txt

    :return: list

    '''
    events = []
    day, month, year, hour, minute, second = 1,1,1970,0,0,0

    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            
            try:
                time_part, event = line.split(", ")
                date = time_part.find(" ") #in here, date is the index, if -1 its because there is no space --> therefore no date part
                if date != -1: #there's a date
                    date, time_part = time_part.split(" ")
                    slash = next(c for c in date if not c.isdigit())
                    day,month,year = list(map(int, date.split(slash)))
                
                time_components = list(map(int, time_part.split(":")))
                
                if len(time_components) == 2:
                    hour, minute = time_components

                elif len(time_components) == 3:
                    hour, minute, second = time_components
                else:
                    raise ValueError("Invalid time format")
                
                dtt = datetime(day=day,month=month,year=year,hour=hour,minute=minute,second=second)

                # events.append((hour, minute, second, event))
                events.append((dtt, event))
            except Exception as e:
                print(f"{e}: {line}")
    
    return events

def get_timestamp_from_dt(dt_string):
    '''
    Parses a datetime string and returns a timestamp of the time portion.

    :param dt_string: str
    
    :return: float
    '''
    try:
        dt = datetime.strptime(dt_string, "%H:%M:%S")
    except Exception:
        dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%SZ")
    t = dt.time()
    # Convert time to timestamp (seconds since midnight)
    return t.hour * 3600 + t.minute * 60 + t.second

def extract_date(d):
    '''
    Returns only date-part in string, from datetime object.
    
    :param d: datetime

    :return: str

    '''
    return d.strftime("%Y-%m-%d")

def extract_time(dt):
    '''
    Extracts and returns the time portion from a datetime object as a string (HH:MM:SS).

    :param d: datetime

    :return: str

    '''
    return dt.time().strftime("%H:%M:%S")

def full_date2str(d):
    '''
    Converts datetime object to full date string
    
    :param d: datetime.datetime

    :return: str
    '''
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")