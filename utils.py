import numpy as np
from datetime import datetime
import re

def find_in_string(string, expression):
    if expression in string:
        return True
    else:
        return False

def find_key_path(dictionary, target_key, path=""):
    """Recursively finds and prints the path of a key in a nested dictionary (including lists)."""
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
    return np.array([int(num) for num in string.split(',') if num.strip()!=' ' and num.strip()!=''])

def parse_path(path):
    """Convert the string path into a list of keys and indices."""
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
    if isinstance(date_input, datetime):
        return date_input.timestamp()
    elif isinstance(date_input, str):
        try:
            return datetime.fromisoformat(date_input.replace("Z", "")).timestamp()
        except ValueError:
            print(f"Invalid date format: {date_input}")
            return None
    else:
        print(f"Unsupported type for date input: {type(date_input)}")
        return None

def access_by_path(dictionary, path_parts):
    """Access the dictionary by the provided list of keys/indices."""
    value = dictionary
    for part in path_parts[:-1]:
        value = value[part]
    return value

def after_point(s):
    start_index = s.find('.')
    if start_index != -1:
        return s[start_index + 1:]
    else:
        return ''
    
def after_underscore(s):
    start_index = s.find('_')
    if start_index != -1:
        return s[start_index + 1:]
    else:
        return s

def parse_datetime(string):
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(string, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {string}")

def parse_time(string):
     return datetime.strptime(string, "%H:%M:%S")

def find_closest_index(new_time, target_hour, target_minute, target_second = 0):
    """Finds the index of the sample in new_time closest to the given hour and minute.
       Returns None if the target time is out of bounds.
    """
    # Convert target hour and minute to a datetime object (same date as new_time[0])
    target_time = datetime(new_time[0].year, new_time[0].month, new_time[0].day, target_hour, target_minute, target_second)

    # Check if the target time is within bounds
    if target_time < new_time[0] or target_time > new_time[-1]:
        return None  # Return None if the target time is out of range

    # Compute absolute time differences
    time_diffs = [abs((t - target_time).total_seconds()) for t in new_time]

    # Get the index of the smallest difference
    closest_idx = np.argmin(time_diffs)
    
    return closest_idx

def read_lines(filename):
    info = {}
    name = ""
    with open(filename, 'r', encoding='utf-8') as file:
        for idx,line in enumerate(file):
            line = line.strip()
            if idx==0: 
                info[line] = []
                name=line
            else:
                info[name].append(line)
    return info

def read_event_file(filename):
    """Reads a text file and returns a list of (hour, minute, second, event) tuples.
    If seconds are not provided, they default to 0."""
    events = []
    
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            
            try:
                time_part, event = line.split(", ")
                time_components = list(map(int, time_part.split(":")))
                
                if len(time_components) == 2:
                    hour, minute = time_components
                    second = 0
                elif len(time_components) == 3:
                    hour, minute, second = time_components
                else:
                    raise ValueError("Invalid time format")

                events.append((hour, minute, second, event))
            except ValueError:
                print(f"Skipping invalid line: {line}")
    
    return events

def date2str(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def extract_time_from_datetime_string(dt_string):
    """Parses a datetime string and returns a timestamp of the time portion."""
    try:
        dt = datetime.strptime(dt_string, "%H:%M:%S")
    except Exception:
        dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%SZ")
    t = dt.time()
    # Convert time to timestamp (seconds since midnight)
    return t.hour * 3600 + t.minute * 60 + t.second


def extract_time(dt):
    """
    Extracts and returns the time portion from a datetime object as a string (HH:MM:SS).
    """
    return dt.time().strftime("%H:%M:%S")

def full_date2str(d: datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")