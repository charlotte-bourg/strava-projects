# from https://www.strava.com/settings/api
export CLIENT_ID=<>
export CLIENT_SECRET=<>

# route in server.py to which the user will be redirected after authentication 
# must be within the callback domain specified by the application
export REDIRECT_URI="http://localhost:5000/callback"

# secret key for securely signing session cookie
export FLASK_KEY=<>

# for client security: send with webhook subscription request to validate response
export STRAVA_VERIFY_TOKEN=<>

# email address for reminder emails to be sent from 
export SENDING_ADDRESS=<>

# password for sender email specified above 
export EMAIL_PASS=<>

# address where webhook events will be sent
# needs to be within authorization callback domain https://www.strava.com/settings/api
export CALLBACK_URL=<ngrok url/webhook>