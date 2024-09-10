import pymongo
import subprocess
import time
import pytz
import os
import psutil
from dotenv import load_dotenv
load_dotenv()

# Create a new client
client = pymongo.MongoClient(os.getenv("MONGO_URI"))

# Get a reference to the database
db = client['Copart']

# Get a reference to the collection
collection = db['Cars']

from datetime import datetime

weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
cdt=pytz.timezone('America/Chicago')

process=None

# Function to get current system memory usage
def get_system_memory_usage():
    memory = psutil.virtual_memory()
    return memory.percent  # return memory usage in percentage
    
while True:
    if datetime.now(cdt).strftime("%H:%M")<="16:00":
        continue
        
    if get_system_memory_usage() > 30:
        time.sleep(3600) 

    # print("Current Time =", time_string)
    # print("Day of the Week =", day_of_week)
    
    # Checking the count of Cars with None Info
    elif collection.count_documents({"Info": "None"}) or collection.count_documents({"Info":"processing"}):

        print("Time to run the script")
        # if not process:
        process = subprocess.Popen(["python3", "ProductScraping.py"])
        # time.sleep(30)
        # process1 = subprocess.Popen(["python3", "ProductScraping.py"])
        # time.sleep(30)
        # process2 = subprocess.Popen(["python3", "ProductScraping.py"])
        process.wait()
        # process1.wait()
        # process2.wait()
        process.terminate()      
        # process1.terminate()     
        # process2.terminate()     
        process.communicate()    
        # process1.communicate()   
        # process2.communicate()   

        del process
        # del process1
        # del process2

        # Aggregation
        aggregation_process = subprocess.Popen(["python3", "aggregation.py"])
        aggregation_process.wait()
        aggregation_process.terminate()
        aggregation_process.communicate()
        del aggregation_process

        # DB Merging
        # merging_process = subprocess.Popen(["python3", "mergedDB.py"])
        # merging_process.wait()
        # merging_process.terminate()
        # merging_process.communicate()
        # del merging_process

        # break
    else:
        time.sleep(3600)
    # time.sleep(3600)  # Sleep for an hour before checking again
