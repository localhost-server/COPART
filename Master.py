from datetime import datetime, timedelta
import subprocess
import time
import pytz

# Define the weekdays on which to run the scripts
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Setting CDT timezone
cdt = pytz.timezone('America/Chicago')

# Set the specific time to start the process (08:20 AM)
target_time = "08:20"

while True:
    # Get the current time and day of the week
    now = datetime.now(cdt)
    day_of_week = now.strftime("%A")
    now_time = now.strftime("%H:%M")

    # Check if the current day is in the list of weekdays
    if day_of_week in weekdays:
        print(f'Today is {day_of_week}, checking time...')

        # Wait until the specific time (08:20 AM)
        if now_time >= target_time:
            print(f'Time is {now_time}. Running scripts for {day_of_week}...')
            
            # Run the processes
            subprocess.Popen(["python3", "AuctionLinkScraping.py"])
            time.sleep(300)
            
            # Wait until the next day
            next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            time_to_wait = (next_day - now).total_seconds()
            print(f'Scripts completed. Waiting for the next day...')
            time.sleep(time_to_wait)
        
        else:
            # If it's not yet the target time, wait for a short while before checking again
            print(f'It\'s still {now_time}. Waiting for {target_time}...')
            time.sleep(60)  # Check again in 1 minute

    else:
        # If today is not a weekday, wait until the next day
        next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_to_wait = (next_day - now).total_seconds()
        print(f'Today is {day_of_week}. Waiting for the next day...')
        time.sleep(time_to_wait)
