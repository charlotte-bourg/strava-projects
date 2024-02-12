# Running Helper
A web app for runners. V1 is an app for Strava users to sign up for email notifications when they log a new activity using their default shoes for that activity type to remind them to verify what gear was used and update as needed. 

## Table of Contents
- [Use Case Background](#use-case-background)
- [Installation](#installation)
- [Features](#features)
- [License](#license)
- [Contact Information](#contact-information)

## Use Case Background
Background:
- Strava says they're the world's #1 fitness app, used by hobbyists to elite athletes for tracking and sharing workout data
- Strava can help users track mileage on their shoes by associating shoes worn with an activity
- Tracking mileage helps runners know when to replace a pair of shoes, which can prevent injuries
- Strava allows setting a pair of shoes as a default for a given activity type (e.g. hike, run, or trail run)

Challenge: 
- Many athletes keep multiple pairs of shoes in rotation for a given activity type, as rotating shoes has been shown to be associated with lower injury risk 
- Many athletes don't record activities directly on Strava but rather use smart watches to track their runs and set up an automatic sync from their wearable to Strava
- When data syncs to Strava it can be easy to ignore it altogether and leave the default gear or to review detailed workout stats in accordance with a training plan or goals and then forget to update the gear 

Solution:
- Use this web app to sign up for alerts to keep your gear mileage accurate! 

## Installation
This app isn't deployed yet. To run it locally, follow the installation instructions below: 

### Prerequisites

- Python installed on your local machine. You can download Python from [python.org](https://www.python.org/downloads/).
- Git installed on your local machine. You can download Git from [git-scm.com](https://git-scm.com/downloads).

### Running Locally

1. **Clone the Repository:**
   ```bash
   $ git clone https://github.com/charlotte-bourg/running-helper/
   ```
2. **Navigate to the Project Directory:**
   ```bash
   $ cd running-helper
   ```
4. **Create and Activate a Virtual Environment:**
   ```bash
   $ python venv env
   ```
   Activate on Windows:
   ```bash
   env\Scripts\activate
   ```
   Activate on macOS and Linux:
   ```bash
   source env/bin/activate
   ```
6. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
   This command installs all the required dependencies listed in the requirements.txt file 
8. **Set Up Email Address to Serve as Sender:**
   Create an gmail address to serve as the sender for your email reminders. 
10. **Set Up Strava API Details:**
11. **Create secrets.sh file:**
    Use the template in secrets_example.sh to update the secrets you'll need to run the app. 
13. **Start ngrok:**
    ```bash
    ngrok http 5000
    ```
15. **Update callback url in secrets.sh:** 
16. **Set Up Webhook Subscription:**
    ```bash
    source secrets.sh
    python3 -i webhook_subscription.py
    >>> create_webhook_subscription()
    ```
17. **Create Database:**
    ```bash
    source secrets.sh
    python3 seed_database.py
    ```
18. **Install redis as needed, and start it:**
    ```bash
    sudo apt install redis-server
    sudo service redis-server start
    ```
20. **Start Celery worker:**
    ```bash
    celery -A server.celery worker --loglevel=info
    ```
21. **Start the Application:**
    ```bash
    source secrets.sh
    python3 server.py
    ```
22. **Access the Application:**
    Navigate to localhost:5000

## Features
TODO
- [Feature 1]: [Brief description]
- [Feature 2]: [Brief description]
- [Feature 3]: [Brief description]
- ...

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Contact Information
Developer: Charlotte Bourg (she/her)

[Email](mailto:charlotte.bourg@gmail.com), [LinkedIn](https://www.linkedin.com/in/charlottebourg/), [GitHub](https://github.com/charlotte-bourg), [Strava](https://www.strava.com/athletes/100636324)
