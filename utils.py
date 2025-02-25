import numpy as np
from datetime import datetime
import re

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

def convert_to_timestamp(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "")).timestamp()
    except ValueError:
        print(f"Invalid date format: {date_str}")
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

def parse_datetime(string):
    try:
        # Handle cases with milliseconds
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        # Fallback for cases without milliseconds
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")
