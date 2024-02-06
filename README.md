LOCAL TESTING SETUP NOTES (TODO readme)
# start ngrok 
ngrok http 5000
# update forwarding url in https://www.strava.com/settings/api and secrets.sh 
# run server
source secrets.sh 
python3 server.py
# set up webhook subscription 
python3 -i webhook_subscription.py 
# then use methods view, create, or delete webhook subscription
# start redis
sudo service redis-server start
# run celery worker
celery -A server.celery worker --loglevel=info