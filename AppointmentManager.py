from CalendarService import create_calendar_event
import googleapiclient
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import pytz
from twilio.twiml.messaging_response import MessagingResponse
from AIBot import ai_bot_interaction
from patternFinder import extract_date, extract_time_range, is_valid_email, format_slot

class AppointmentManager:
    def __init__(self, calendar_id):
        self.calendar_id = calendar_id

    def twilio_response(self,message):
        return message

    # Function to check for available time slots on a given day
    def check_available_slots(self,day, service):
        global calendar_id
        
        events_result = None
        try:
            start_datetime = datetime.strptime(day, "%d.%m.%Y").replace(hour=8, minute=0, tzinfo=pytz.timezone('Europe/Bucharest'))
            end_datetime = start_datetime + timedelta(hours=9)
            events_result = service.events().list(calendarId=self.calendar_id, timeMin=start_datetime.isoformat(), timeMax=end_datetime.isoformat(), singleEvents=True, orderBy='startTime').execute()
            events = events_result.get('items', [])
        except ValueError:
            print(f"The provided day {day} does not match the format 'DD.MM.YYYY'")
        except googleapiclient.errors.HttpError:
            print("An error occurred while making the request to the Google Calendar API.")

        if not events_result:
            return []
        
        events = events_result.get('items', [])

        occupied_slots = set()
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            start_time = datetime.fromisoformat(start).replace(tzinfo=None)
            end_time = datetime.fromisoformat(end).replace(tzinfo=None)
            while start_time < end_time:
                occupied_slots.add(start_time)
                start_time += timedelta(hours=1)
        print("occupied_slots:", occupied_slots)

        available_slots = []
        current_time = start_datetime
        while current_time < end_datetime:

            current_time_naive = current_time.replace(tzinfo=None)

            # Check if the current_time_naive is not in the occupied_slots
            if current_time_naive not in occupied_slots:
            # If it's not occupied, append it to the available_slots
                
            #if current_time not in occupied_slots:
                print("current_time:", current_time)
                available_slots.append(current_time)
            current_time += timedelta(hours=1)
        print("available_slots:", available_slots)

        return available_slots
    #generates the message with the available time slots
    def generate_options_message(self,available_slots, appointment_date):
        options_message = "Available time slots on {}: ".format(appointment_date)
        twilio_response(options_message)
        for slot in available_slots:
            options_message += "\n- {} to {}".format(slot.strftime("%H:%M"), (slot + timedelta(hours=1)).strftime("%H:%M"))
        return options_message
    #gets the chosen time slot
    def get_chosen_time_slot(self,request):
        ai_response = ai_bot_interaction("Please choose a preferred time slot (e.g., '08:00 to 09:00').")
        print("AI:", ai_response)
        self.twilio_response("Please choose a preferred time slot (e.g., '08:00 to 09:00').")
        chosen_slot = request.form.get('Body') 
        chosen_slot = extract_time_range(chosen_slot)
        print("Chosen slot inside get_chosen_time_slot:", chosen_slot)
        return chosen_slot
    #checks if the chosen slot is valid
    def validate_chosen_time_slot(self,chosen_slot, available_slots):
        available_slots_formatted = [f"{slot.strftime('%H:%M')} to {(slot + timedelta(hours=1)).strftime('%H:%M')}" for slot in available_slots]
        return chosen_slot in available_slots_formatted
    #gets the information of the client
    def get_client_info(self):
        client_name = None
        while client_name is None:
            ai_response = "Please input your full name."
            client_name = request.form.get('Body')
            if client_name is None:
                ai_response = "Please input a name."
            else:
                ai_response = "Please input a valid email address (e.g., example@gmail.com or example@yahoo.com)."
                client_email = request.form.get('Body')
                while not is_valid_email(client_email):
                    ai_response += "Please input a valid email address (e.g., example@gmail.com or example@yahoo.com)."
                    client_email = request.form.get('Body')
        return client_name, client_email
    #schedule an appointment for the chosen slot
    def schedule_appointment_for_chosen_slot(self,chosen_slot, appointment_date, client_name, client_email,service,calendar_id):
        print("Scheduling appointment...")  # Add print statement here
        print("chosen_slot:", chosen_slot)  # Add print statement here
        print("appointment_date:", appointment_date)  # Add print statement here
        print("client_name:", client_name)  # Add print statement here
        print("client_email:", client_email)  # Add print statement here
        print("service:", service)  # Add print statement here
        print("calendar_id:", calendar_id)  # Add print statement here
        summary = "Appointment with:" + client_name
        location = "Your office"  # Update with your location
        description = "Meeting with client"
        chosen_slot=format_slot(chosen_slot)
        start_time_str, end_time_str = chosen_slot.split(" to ")
        start_time = datetime.strptime(appointment_date + " " + start_time_str, "%d.%m.%Y %H:%M")
        end_time = datetime.strptime(appointment_date + " " + end_time_str, "%d.%m.%Y %H:%M")
        attendees = [{"name": client_name, "email": client_email}]
         # Logic for scheduling appointment
        try:
            create_calendar_event(calendar_id, service, summary, location, description, start_time, end_time, "Europe/Bucharest", attendees)
            return True
        except Exception as e:
            print("Error:", e)  # Print any error that occurs
            return False
        #return create_calendar_event(calendar_id,service,summary, location, description, start_time, end_time, "Europe/Bucharest", attendees)
    #asks the user for the date of the appointment
    def get_appointment_date(self):
        message = "I work from 8:00 to 17:00. Please provide the date you want to schedule the appointment (DD.MM.YYYY)."
        response = self.twilio_response(message)
        if response:
            return response
        # Initialize appointment_date
        appointment_date = None

        # Loop until appointment date is provided
        while not appointment_date:
            message_body = request.form.get('Body')
            if message_body:
                appointment_date = extract_date(message_body)
                if not appointment_date:
                    self.twilio_response("Invalid date format. Please provide the date in the format DD.MM.YYYY.")
        return appointment_date
    #asks the user for the date of the appointment
    def get_time_slot(self,available_slots):
        options_message = generate_options_message(available_slots, appointment_date)
        ai_response = ai_bot_interaction(options_message)
        
        while True:
            chosen_slot = get_chosen_time_slot()
            if chosen_slot is None:
                continue
            if validate_chosen_time_slot(chosen_slot, available_slots):
                return chosen_slot
            else:
                twilio_response("Invalid time slot. Please choose from the available options.")
    #schedules an appointment for the chosen slot
    def process_appointment(self,appointment_date):
        available_slots = check_available_slots(appointment_date)
        if available_slots:
            chosen_slot = get_time_slot(available_slots)
            client_name, client_email = get_client_info()
            schedule_successful = schedule_appointment_for_chosen_slot(chosen_slot, appointment_date, client_name, client_email)
            if schedule_successful:
                return twilio_response("Appointment scheduled successfully!")
            else:
                return twilio_response("Error scheduling appointment. Please try again.")
        else:
            return twilio_response("I'm sorry, but I'm fully booked on {}. Please choose another date.".format(appointment_date))
    #the main function to schedule an appointment
    def schedule_appointment(self):
        appointment_date = get_appointment_date()
        return process_appointment(appointment_date)

    def delete_appointment_by_email(self,client_email,service):
        try:
            # Retrieve the list of events from the calendar
            events = service.events().list(calendarId='primary', q=client_email).execute()
            
            # Check if there are any events associated with the client's email
            if 'items' in events:
                for event in events['items']:
                    # Get the event ID
                    event_id = event['id']
                    
                    # Delete the event using the event ID
                    service.events().delete(calendarId='primary', eventId=event_id).execute()
                    print("Appointment deleted successfully!")
            else:
                #print("No appointments found for the specified email address.")
                return "No appointments found for the specified email address."
        except Exception as e:
            print("An error occurred:", str(e))
            return "An error occurred while deleting the appointment."
        return "Appointment deleted successfully!"