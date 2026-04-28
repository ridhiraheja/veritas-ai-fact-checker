from pymongo import MongoClient

client = MongoClient("mongodb+srv://ridhiraheja:ridhi24@cluster0.xtijuvx.mongodb.net/")
db = client["chatbot"]
collection = db["history"]

all_chats = list(collection.find({}, {"_id": 0}))
print(f"Total records in DB: {len(all_chats)}")
for i, chat in enumerate(all_chats[-5:]):  # print last 5
    print(f"Record {i}: {chat}")
