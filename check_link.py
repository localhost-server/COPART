import pymongo
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv

load_dotenv()

def process_link(link):
    if collection.find_one({"carLink": link}):
        # print(f"Car {link} already in the database")
        pass
    else:
        collection.insert_one({"carLink": link, "Info": "None"})
        # print(f"Car {link} added to the database with NONE")

# Create a new client
client = pymongo.MongoClient(os.getenv("MONGO_URI"))

# Get a reference to the database
db = client['Copart']

# Get a reference to the collection
collection = db['Cars']

def process_links(carlinks, num_threads=100):
    # Create a ThreadPoolExecutor with the specified number of threads
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit tasks for each link to be processed in parallel
        executor.map(process_link, carlinks)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Process some car links.')
parser.add_argument('carlinks', type=str, help='a space-separated string of car links')
args = parser.parse_args()

# Split the string back into a list
carlinks = args.carlinks.split(" ")

# Process the links
process_links(carlinks)
