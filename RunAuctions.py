import subprocess
import pymongo
from pymongo import ASCENDING
import asyncio
import psutil
from datetime import datetime
import pytz

import os
from dotenv import load_dotenv
load_dotenv()

# Create a new client
client = pymongo.MongoClient(os.getenv("MONGO_URI"))
# Setting CDT timezone
cdt=pytz.timezone('America/Chicago')

# Get a reference to the database
db = client['Copart']

# Get a reference to the collection
collection = db['AuctionLinks']

# Function to get current system memory usage
def get_system_memory_usage():
    memory = psutil.virtual_memory()
    return memory.percent  # return memory usage in percentage

# Iterate over the documents in the MongoDB collection where 'Info' is sNone
async def open_auctions():
    # while datetime.now(cdt).strftime("%H:%M") >= "08:05" and datetime.now(cdt).strftime("%H:%M") <= "15:00":
    # while datetime.now(cdt).strftime("%H:%M") <= "23:00":
    while (collection.count_documents({'Info': "None"}) > 0) and (datetime.now(cdt).strftime("%H:%M") <= "23:59"):
        document = collection.find_one({'Info': "None"},sort=[("creation_time", ASCENDING)])
        if document is not None:
            # Check system memory usage
            while get_system_memory_usage() > 60:
                await asyncio.sleep(600)  # Wait for 10 minutes before checking again

            # link = document['link']
            # Open the link
            subprocess.Popen(["python3","StartNAuction.py"])

            # Update the 'Info' field in the MongoDB collection
            # collection.update_one({'link': link}, {'$set': {'Info': 'processing'}})

            await asyncio.sleep(240)  # Wait for 2 minutes before checking again
        else:
            await asyncio.sleep(600)
            # break

# Run the asynchronous function
asyncio.run(open_auctions())
