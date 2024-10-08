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
    await asyncio.sleep(60)
    while True :#and (datetime.now(cdt).strftime("%H:%M") <= "23:59"):
        if (collection.count_documents({'Info': "None"}) > 0):
            document = collection.find_one({'Info': "None"},sort=[("creation_time", ASCENDING)])
            if document is not None:
                # Check system memory usage
                while get_system_memory_usage() > 70:
                    await asyncio.sleep(600)  # Wait for 10 minutes before checking again
    
                subprocess.Popen(["python3","StartNAuction.py"])
    
                await asyncio.sleep(300)  # Wait for 2 minutes before checking again
        else:
            await asyncio.sleep(600)
                # break

# Run the asynchronous function
asyncio.run(open_auctions())
