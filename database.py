import discord
import motor.motor_asyncio

# MongoDB connection setup
mongo_uri = "mongodb+srv://<username>:<password>@<app_name>.mongodb.net/Telecord?retryWrites=true&w=majority"
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
db = client.Telecord

# Function to insert data into MongoDB
async def insert_data(collection_name, data):
    collection = db[collection_name]
    await collection.insert_one(data)

# Function to update data in MongoDB
async def update_data(collection_name, query, new_data):
    collection = db[collection_name]
    await collection.update_one(query, {"$set": new_data})

# Function to delete data from MongoDB
async def delete_data(collection_name, query):
    collection = db[collection_name]
    await collection.delete_one(query)
