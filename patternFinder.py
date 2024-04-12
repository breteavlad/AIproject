import re
from datetime import datetime, timedelta

# Function to extract the appointment date from the user input
def extract_date(prompt):
    # Define the regex pattern to match the date in the format DD.MM.YYYY
    pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'
    match = re.search(pattern, prompt)
    if match:
        return match.group()
    else:
        return None

def extract_time_range(prompt):
    # Regular expression pattern to match the hour:minutes to hour:minutes format
    pattern = r'(\b\d{1,2}:\d{2}\b\s+to\s+\b\d{1,2}:\d{2}\b)'

    # Find the time range match in the prompt
    match = re.search(pattern, prompt)

    if match:
        return match.group(0)  # Return the matched substring
    else:
        print("Error: Please provide a time range in the format 'hour:minutes to hour:minutes'.")
        return None

def is_valid_email(email):
    # Regex pattern for validating email addresses
    pattern = r'^[a-zA-Z0-9._%+-]+@(?:gmail\.|yahoo\.)[a-zA-Z]{2,}$'
    return re.match(pattern, email) 

# Function to check if the prompt contains the word "schedule" in any context
def contains_schedule(prompt):
    # Define the regex pattern to match the word "schedule" in any context
    pattern = r'\bschedule\b'
    return re.search(pattern, prompt.lower()) is not None

# Function to check if the prompt contains the word "schedule" in any context
def contains_cancel(prompt):
    # Define the regex pattern to match the word "schedule" in any context
    pattern = r'\bcancel\b'
    return re.search(pattern, prompt.lower()) is not None
def format_slot(chosen_slot_str):
    # Parse the datetime string
    chosen_slot = datetime.strptime(chosen_slot_str, '%Y-%m-%d %H:%M:%S')
    
    # Extract the start time
    start_time = chosen_slot.time().strftime('%H:%M')
    
    # Calculate the end time
    end_time = (chosen_slot + timedelta(hours=1)).time().strftime('%H:%M')
    
    # Return the formatted string
    return f'{start_time} to {end_time}'
