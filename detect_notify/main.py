from dotenv import load_dotenv
load_dotenv()

from tools import logger
from google_auth_wrapper import GoogleConnection
import os
import datetime
import pytz
import requests
import time

GOOGLE_MASTER_TOKEN = os.getenv("GOOGLE_MASTER_TOKEN")
GOOGLE_USERNAME = os.getenv("GOOGLE_USERNAME")
NEST_DEVICE_ID = os.getenv("NEST_DEVICE_ID")
NEST_DEVICE_NAME = os.getenv("NEST_DEVICE_NAME")
REFRESH_INTERVAL_MINS = float(os.getenv("REFRESH_INTERVAL_MINS"))
NTFY_ENDPOINT = os.getenv("NTFY_ENDPOINT")
MAX_RECONNECT_ATTEMPTS = 3

assert GOOGLE_MASTER_TOKEN and GOOGLE_USERNAME and NEST_DEVICE_ID and NEST_DEVICE_NAME and REFRESH_INTERVAL_MINS and NTFY_ENDPOINT

def main():
    def connect():
        google_connection = GoogleConnection(GOOGLE_MASTER_TOKEN, GOOGLE_USERNAME)
        device = google_connection.get_nest_camera(NEST_DEVICE_ID, NEST_DEVICE_NAME)
        return google_connection, device

    reconnect_attempts = 0
    google_connection, device = connect()

    logger.info(f"Connected to device ID: {NEST_DEVICE_ID}")

    # Initialize the last checked time to now minus the refresh interval
    last_checked_time = pytz.timezone("Europe/London").localize(datetime.datetime.now() - datetime.timedelta(minutes=REFRESH_INTERVAL_MINS))

    notification_text = f"🐱 Cat detector initialised at {pytz.timezone('Europe/London').localize(datetime.datetime.now()).strftime('%d/%m/%Y %H:%M:%S')}."
    requests.post(NTFY_ENDPOINT, data=notification_text.encode(encoding='utf-8'))

    while True:
        loop_start_time = time.time()
        
        current_time = pytz.timezone("Europe/London").localize(datetime.datetime.now())
        
        try:
            events = device.get_events(
                start_time=last_checked_time,
                end_time=current_time
            )
            
            logger.info(f"Found {len(events)} events for {device.device_name}")
            for event in events:
                logger.info(f"Event: Start Time: {event.start_time}, End Time: {event.end_time}")
                # Send notification for each event
                notification_text = f"🐱 Cat spotted at {event.start_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %H:%M:%S')}!"
                requests.post(NTFY_ENDPOINT, data=notification_text.encode(encoding='utf-8'))
            
            # Reset reconnect attempts on successful operation
            reconnect_attempts = 0
        
        except Exception as e:
            logger.error(f"An error occurred while fetching or processing events: {e}")
            
            if reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
                logger.info(f"Attempting to reconnect. Attempt {reconnect_attempts + 1} of {MAX_RECONNECT_ATTEMPTS}")
                try:
                    google_connection, device = connect()
                    reconnect_attempts += 1
                    continue  # Skip to the next iteration of the loop
                except Exception as reconnect_error:
                    logger.error(f"Failed to reconnect: {reconnect_error}")
            else:
                logger.error("Maximum reconnection attempts reached. Exiting.")
                return
        
        # Update the last checked time for the next iteration
        last_checked_time = current_time
        
        # Calculate how long the operations took
        processing_time = time.time() - loop_start_time
        
        # Calculate the remaining time to sleep
        sleep_time = max(0, (REFRESH_INTERVAL_MINS * 60) - processing_time)
        
        logger.info(f"Processing took {processing_time:.2f} seconds. Sleeping for {sleep_time:.2f} seconds.")
        
        # Sleep for the remaining time
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()