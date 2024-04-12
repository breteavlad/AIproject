# Function to create a calendar event
def create_calendar_event(calendar_id,service,summary, location, description, start_time, end_time, timezone, attendees):
    print("Creating calendar event...")  # Add print statement here
    print("start_time in create_calendar:", start_time)  # Add print statement here
    print("end_time in create_calendar:", end_time)  # Add print statement here
    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'attendees': attendees,
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    service.events().insert(calendarId=calendar_id, body=event).execute()