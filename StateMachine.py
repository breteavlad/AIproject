from datetime import datetime
from AppointmentManager import *
from patternFinder import *
from AIBot import ai_bot_interaction


class StateMachine:

    def __init__(self, appointment_manager):
        # Define your states
        self.appointment_manager = appointment_manager
        self.is_scheduling = False
        self.is_rescheduling = False
        self.is_first_message = True
        self.appointment_date = None
        self.client_email = None
        self.client_name = None
        self.chosen_slot = None
        self.STATE_EXTRACT_STATE = "extract_state"
        self.STATE_ASK_DATE = "ask_date"
        self.STATE_ASK_HOUR = "ask_hour"
        self.STATE_ASK_NAME= "ask_name"
        self.STATE_ASK_EMAIL= "ask_email"
        self.STATE_CREATE_APPOINTMENT = "create_appointment"
        self.STATE_DELETE_APPOINTMENT = "detete_appointment"
        self.STATE_ASK_EMAIL_FOR_DELETE = "ask_email_for_delete"

        # Map states to functions
        self.state_functions = {
            self.STATE_EXTRACT_STATE: self.extract_state,
            self.STATE_ASK_DATE: self.ask_date,
            self.STATE_ASK_HOUR: self.ask_hour,
            self.STATE_ASK_NAME: self.ask_name,
            self.STATE_ASK_EMAIL: self.ask_email,
            self.STATE_CREATE_APPOINTMENT: self.create_appointment,
            self.STATE_DELETE_APPOINTMENT: self.delete_appointment,
            self.STATE_ASK_EMAIL_FOR_DELETE: self.ask_email_for_delete
        }

        # Initialize state
        self.state = self.STATE_ASK_DATE
        self.data = None
    def ask_date(self,message_body,service):
            message = ai_bot_interaction("Tell the user that I work from 8:00 to 17:00. Please provide the date you want to schedule the appointment (DD.MM.YYYY).")
            return message, self.STATE_EXTRACT_STATE
    

    def extract_state(self,message_body,service):
        print("Hello from extract_date")
        self.appointment_date = extract_date(message_body)
        if not self.appointment_date:
            message = "I work from 8:00 to 17:00. Please provide the date you want to schedule the appointment (DD.MM.YYYY)."
            return message, self.STATE_ASK_DATE
        else:
             # Call ai_bot_interaction with the appropriate prompt
            message = ai_bot_interaction("Tell the user that the date has been successfully set and has him to give you an hour in the interval 8:00 to 17:00.")
            return message, self.STATE_ASK_HOUR

    def ask_hour(self, message_body, service, calendar_id, request):
        print("Hello from ask_hour")
        
        self.appointment_manager = AppointmentManager(calendar_id)
        available_slots = self.appointment_manager.check_available_slots(self.appointment_date, service)
        available_slots_str = [slot.strftime('%Y-%m-%d %H:%M:%S') for slot in available_slots]
        message = "Available slots are: " + ", ".join(available_slots_str) + ". Please choose a slot."
        chosen_slot_str = self.appointment_manager.get_chosen_time_slot(request)
        chosen_slot_start_str = chosen_slot_str.split(' to ')[0]  # Extract the start time
        chosen_slot_date_str = datetime.strptime(self.appointment_date, '%d.%m.%Y').strftime('%Y-%m-%d')  # Parse and format the date
        chosen_slot_datetime_str = f'{chosen_slot_date_str} {chosen_slot_start_str}:00'  # Combine date and start time
        chosen_slot = datetime.strptime(chosen_slot_datetime_str, '%Y-%m-%d %H:%M:%S')
        chosen_slot_str = chosen_slot.strftime('%Y-%m-%d %H:%M:%S')
        print("Chosen slot after datetime modification:", chosen_slot)
        available_slots_str = [slot.strftime('%Y-%m-%d %H:%M:%S') for slot in available_slots]
        print("Available slots:", available_slots_str)  
        chosen_slot = chosen_slot.replace(tzinfo=None)
        available_slots = [slot.replace(tzinfo=None) for slot in available_slots]
        print("Chosen slot after tzinfo modification:", chosen_slot_str)
        self.chosen_slot = chosen_slot_str
        if chosen_slot_str not in available_slots_str:
            message = "Invalid slot. Please choose a valid slot."
            return message, None, self.STATE_ASK_HOUR  # Return to asking hour state if slot is invalid
        else:
            message=ai_bot_interaction("Tell the user that the hour has been successfully set and ask him to provide his full name.")
            return message,chosen_slot_str, self.STATE_ASK_NAME

    def ask_name(self, message_body, request):
        self.client_name = request.form.get('Body')
        if self.client_name is None:
            message=ai_bot_interaction("Tell the user that he needs to provide his full name.")
            return message, self.STATE_ASK_NAME
        else:
            return f"Your name is :  {self.client_name}   . Please type your email. Use a valid email address (e.g., example@gmail.com or example@yahoo.com)", self.STATE_ASK_EMAIL

    def ask_email(self, message_body, request):
        self.client_email = request.form.get('Body')
        if not is_valid_email(self.client_email):
            return "Please input a valid email address (e.g., example@gmail.com or example@yahoo.com).", self.STATE_ASK_EMAIL
        else:
            return f"Your email is: {self.client_email}", self.STATE_CREATE_APPOINTMENT

    def create_appointment(self,service,calendar_id):
        # Logic for creating appointment
        schedule_successful = self.appointment_manager.schedule_appointment_for_chosen_slot(self.chosen_slot, self.appointment_date, self.client_name, self.client_email,service,calendar_id)
        if schedule_successful:
            message = ai_bot_interaction("Tell the user that the appointment has been scheduled successfully.")
            return message, self.STATE_ASK_DATE
        else:
            message= ai_bot_interaction("Tell the user that there was an error scheduling the appointment and ask him to try again.")
            return message, self.STATE_ASK_DATE
    
    def ask_email_for_delete(self, message_body, service):
        message = "Please provide the email address associated with the appointment you want to delete."
        return message, self.STATE_DELETE_APPOINTMENT

    def delete_appointment(self,service,calendar_id,request):
        # Logic for deleting appointment
        self.client_email = request.form.get('Body')
        if not is_valid_email(self.client_email):
            return "Please input a valid email address (e.g., example@gmail.com or example@yahoo.com).", self.STATE_DELETE_APPOINTMENT
        else:
            print(f"self.appointment_manager before delete_appointment_by_email: {self.appointment_manager}")
            response = self.appointment_manager.delete_appointment_by_email(self.client_email,service)
            return response, self.STATE_ASK_DATE



    