from google_auth_oauthlib.flow import InstalledAppFlow
from flask import Flask, request, redirect, session
import pickle
from googleapiclient.discovery import build
from AppointmentManager import AppointmentManager
from twilio.twiml.messaging_response import MessagingResponse
from patternFinder import contains_schedule, contains_cancel
from AIBot import ai_bot_interaction
from StateMachine import StateMachine
import os

class OAuthService:

    def __init__(self, app):
        
        self.app = app
        self.service = None
        self.calendar_id = None
        self.state = None
        self.data = None
        self.app.add_url_rule('/callback', 'callback', self.callback)
        self.app.add_url_rule('/sms', 'handle_sms', self.handle_sms, methods=['POST', 'GET'])
        self.appointment_manager = AppointmentManager(self.calendar_id)
        self.state_machine = StateMachine(self.appointment_manager)  # Create an instance of StateMachine



    #@app.route("/callback")
    def callback(self):
        print("Callback function called.")
        global calendar_id
        print("Request URL: ", request.url)  # Print the request URL for debugging
        authorization_code = request.args.get('code')
        if 'DYNO' in os.environ:
            redirect_uri = 'https://arcane-forest-88129-c9ea7937c5e9.herokuapp.com/callback'
        else:
            redirect_uri = 'http://localhost:8080/callback'

        if authorization_code:
            try:
                # Reconstruct the flow from the saved authorization URL
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_web_1.json',
                    ['https://www.googleapis.com/auth/calendar'],
                    redirect_uri=redirect_uri
                )

                flow.fetch_token(authorization_response=request.url)

                # Get the credentials
                credentials = flow.credentials
                pickle.dump(credentials, open("token.pkl", "wb"))
                credentials = pickle.load(open("token.pkl", "rb"))
                self.service = build("calendar", "v3", credentials=credentials)
                result = self.service.calendarList().list().execute()
                calendar_id = result['items'][0]['id']
                self.appointment_manager = AppointmentManager(calendar_id)

                # Redirect the user to the SMS handling route
                return redirect("/sms")
            except Exception as e:
                return f"Error during callback function: {e}"
        else:
            return "Authorization failed. Missing authorization code."
    # SMS handling route

    def initiate_oauth_flow(self):
        print("Initiating OAuth2 flow...")

        if 'DYNO' in os.environ:
            redirect_uri = 'https://arcane-forest-88129-c9ea7937c5e9.herokuapp.com/callback'
        else:
            redirect_uri = 'http://localhost:8080/callback'

        try:
            # Set up the OAuth2 flow
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_web_1.json',
                ['https://www.googleapis.com/auth/calendar'],
                redirect_uri=redirect_uri
            )

            # Start the OAuth2 flow
            authorization_url, _ = flow.authorization_url(access_type='offline', prompt='consent')

            # Save the authorization URL to the session for later use
            session['authorization_url'] = authorization_url

            # Redirect to the authorization URL
            return redirect(authorization_url)
        except Exception as e:
            return f"Error during OAuth2 initiation: {e}"

    
    #@app.route("/sms", methods=['POST', 'GET'])
    def handle_sms(self):
        
        global state,data

        # Check if service is initialized
        if self.service is None:
            return "Error: Service is not initialized. Please authorize first."

        # Extract the message body from the request
        message_body = request.form.get('Body')

        # Create an instance of AppointmentManager
        # print(f"calendar_id before initialization: {calendar_id}")
        # self.appointment_manager = AppointmentManager(calendar_id)
        # print(f"self.appointment_manager after initialization: {self.appointment_manager}")
        # Create a Twilio response object
        self.appointment_manager.twilio_response = MessagingResponse()

        if message_body is None:
            return "Invalid request. Message body is missing."

        # Handle different types of messages
        if self.state_machine.is_scheduling or contains_schedule(message_body):
            self.state_machine.is_scheduling = True
            # If the message contains a request to schedule an appointment
            print(f"Current state before handling SMS: {self.state_machine.state}")
            if self.state_machine.state in self.state_machine.state_functions:
                #response, next_state = self.state_machine.state_functions[self.state_machine.state](message_body,service,calendar_id)
                if self.state_machine.state == self.state_machine.STATE_ASK_HOUR:
                    response, chosen_slot_str,next_state = self.state_machine.state_functions[self.state_machine.state](message_body, self.service, calendar_id, request)
                elif self.state_machine.state == self.state_machine.STATE_ASK_NAME :
                    response, next_state = self.state_machine.state_functions[self.state_machine.state](message_body, request)
                elif self.state_machine.state == self.state_machine.STATE_ASK_EMAIL:
                    response, next_state = self.state_machine.state_functions[self.state_machine.state](message_body, request)
                    self.state_machine.state = next_state
                    if self.state_machine.state == self.state_machine.STATE_CREATE_APPOINTMENT:
                        response, next_state = self.state_machine.state_functions[self.state_machine.state](self.service, calendar_id)
                elif self.state_machine.state == self.state_machine.STATE_CREATE_APPOINTMENT:
                    response, next_state = self.state_machine.state_functions[self.state_machine.state](self.service,calendar_id)
                else:
                    response, next_state = self.state_machine.state_functions[self.state_machine.state](message_body, self.service)
                self.state_machine.state = next_state
                self.state_machine.data = response
                print(f"Current state after handling SMS: {self.state_machine.state}")
            #response = schedule_appointment()
            self.appointment_manager.twilio_response.message(response)
            #twilio_response.message(response)
        elif self.state_machine.is_rescheduling or contains_cancel(message_body):
            print(f"message_body: {message_body}")  # Print the message body
            self.state_machine.is_rescheduling = True
            # If the message contains a request to reschedule an appointment
            # Extract the email address from the user
            # You might want to replace this with actual logic to obtain the email address
            #print(f"Current state before first message in rescheduling: {self.state_machine.state}")
            if self.state_machine.is_first_message:
                self.state_machine.is_first_message = False
                self.state_machine.state = self.state_machine.STATE_ASK_EMAIL_FOR_DELETE
                response, next_state = self.state_machine.state_functions[self.state_machine.state](message_body, self.service)
                print(f"Current state after first message in rescheduling: {self.state_machine.state}")
                print("response: ", response)
                # self.state_machine.state = next_state
                # self.state_machine.data = response
                # appointment_manager.twilio_response.message(response)  # Return the Twilio response
            elif self.state_machine.state == self.state_machine.STATE_DELETE_APPOINTMENT:
                response, next_state = self.state_machine.state_functions[self.state_machine.state](self.service, calendar_id, request)
            self.state_machine.state = next_state
            self.state_machine.data = response
            print(f"Current state after first message in rescheduling: {self.state_machine.state}")
            self.appointment_manager.twilio_response.message(response)
        else:
            # For other prompts, interact with the AI bot
            response = ai_bot_interaction("I want you to behave like an assistant .Please be concise and polite in your response. Inform the user that I work from 8-17. Also be sure to tell him to use the word: schedule , if he wants to schedule an appointment and the word: cancel ,if he wants to delete his appointment. Don't answer this prompt.")
            # Add the AI bot response to the Twilio response
            self.appointment_manager.twilio_response.message(response)

        # Return the Twilio response as XML
        return str(self.appointment_manager.twilio_response)