import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set!")

client = MongoClient(MONGO_URI)
db = client["chatbot"]
collection = db["history"]

all_chats = list(collection.find({}, {"_id": 0}))
print(f"Total records in DB: {len(all_chats)}")
for i, chat in enumerate(all_chats[-5:]):  # print last 5
    print(f"Record {i}: {chat}")
