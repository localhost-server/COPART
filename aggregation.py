import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

# Create a MongoClient
client = pymongo.MongoClient(os.getenv("MONGO_URI"))

# Select the database
db = client["Copart"]

# Run the aggregation pipeline
pipeline = [
    {
        "$lookup": {
            "from": "Cars",
            "localField": "carLink",
            "foreignField": "carLink",
            "as": "Integrated"
        }
    },
    {
        "$unwind": "$Integrated"
    },
    {
        "$project": {
            "_id": 0,
            "carLink": 1,
            "prices": 1,
            "Info": "$Integrated.Info"
        }
    },
    {
        "$out": "IntegratedData"
    }
]

db["CarsPrice"].aggregate(pipeline)
