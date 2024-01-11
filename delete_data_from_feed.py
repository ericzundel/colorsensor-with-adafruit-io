'''Removes all data from the Adafruit IO colorsensor feed. Intended to be run from desktop python.'''

import requests
import sys


print("*** WARNING: This script will delete all data collected to date.")

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there and don't commit them to git!")
    raise


# Pull in Adafruit IO credentials from our secrets file
username = secrets['aio_username']
io_key = secrets['aio_key']
feed_key = secrets['aio-colorsensor-feed-id']

# Adafruit IO API endpoint for getting feed data
api_url = f"https://io.adafruit.com/api/v2/{username}/feeds/{feed_key}/data"

# Call the function to delete all data from the specified feed
def delete_all_data():
    # Get the data IDs from the feed
    response = requests.get(api_url, headers={"X-AIO-Key": io_key})
    data_ids = [entry['id'] for entry in response.json()]

    # Delete each data point
    for data_id in data_ids:
        delete_url = f"{api_url}/{data_id}"
        response = requests.delete(delete_url, headers={"X-AIO-Key": io_key})
        print(f"Deleted data point {data_id}. Status code: {response.status_code}")

def yes_no_prompt():
    while True:
        print("Do you want to proceed? (yes/no): ")
        sys.stdout.flush()
        raw_input = sys.stdin.readline()
        user_input = str(raw_input).lower().rstrip()

        if user_input == 'yes':
            print("You chose to proceed.")
            return True
        else user_input == 'no':
            print("You chose not to proceed.")
            return False

proceed = yes_no_prompt()

# Now you can use 'user_decision' in your code to determine the course of action
if proceed:
    delete_all_data()
else:
    # Handle the case where the user decided not to proceed
    print("Aborted.")
