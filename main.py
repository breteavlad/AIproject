import pickle
import re
from flask import Flask, request, redirect, session
from dotenv import load_dotenv
import os
import json
from twilio.twiml.messaging_response import MessagingResponse
from OAuthService import OAuthService

# Load environment variables from .env file
load_dotenv('s.env')
load_dotenv('secret_bot.env')

app = Flask(__name__)

app.secret_key = os.getenv('FLASK_SECRET_KEY')
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

oauth_service = OAuthService(app)
os.getenv('OPENAI_API_KEY')

# Main route to redirect to the OAuth2 flow initiation
@app.route("/")
def index():
    return oauth_service.initiate_oauth_flow()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Use PORT if it's there
    app.run(debug=True, host='0.0.0.0', port=port)