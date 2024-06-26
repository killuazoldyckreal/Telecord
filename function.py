import os, json
from typing import Dict, List, Any
from addons import Settings, TOKENS
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(os.path.join(ROOT_DIR, "jsonfiles/settings.json")):
    raise Exception("Settings file not set!")
    
def openJson(path: str) -> dict:
    try:
        with open(os.path.join(ROOT_DIR, path), encoding="utf8") as json_file:
            return json.load(json_file)
    except:
        return {}
#--------------- Cache Var ---------------
sdict = openJson("jsonfiles/settings.json")
tokens: TOKENS = TOKENS()
settings = Settings(sdict)

MONGO_DB: AsyncIOMotorClient
telecorddata: AsyncIOMotorCollection
telegramdata: AsyncIOMotorCollection

# Convert integers to Int64
def convert_to_int64(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, int):
                data[key] = int(value)
            elif isinstance(value, dict):
                convert_to_int64(value)
            elif isinstance(value, list):
                data[key] = [int(item) if isinstance(item, int) else item for item in value]
    return data

# Update function
async def update_db(collection:AsyncIOMotorCollection, filter: Dict, update_data: Dict) -> bool:
    update_data = convert_to_int64(update_data)
    result = await collection.update_one(filter, update_data)
    return result.modified_count > 0

# Insert function
async def insert_db(collection:AsyncIOMotorCollection, document: Dict) -> bool:
    document = convert_to_int64(document)
    result = await collection.insert_one(document)
    return result.acknowledged

# Delete function
async def delete_db(collection:AsyncIOMotorCollection, filter: Dict) -> bool:
    result = await collection.delete_one(filter)
    return result.deleted_count > 0

# Get a row with unique value
async def get_db(collection, filter: Dict):
    filter = convert_to_int64(filter)
    result = await collection.find_one(filter)
    return result

# Get all rows that contain specific values
async def get_any(collection, query: Dict):
    cursor = collection.find(query)
    result = await cursor.to_list(length=None)
    return result

# Get all rows
async def get_all_db(collection: AsyncIOMotorCollection) -> List[Dict[str, Any]]:
    cursor = collection.find()
    result = await cursor.to_list(length=None)  # Fetch all documents
    return result


# Function for reference purpose
async def update_telegramdata(entries):    
    # Update example
    filter_telecord = {"useridtg": 37422429}
    update_telecord = {"$set": {"chatid": 987654321}}
    await update_db(telecorddata, filter_telecord, update_telecord)
    
    filter_telegram = {"useridtg": 786737498}
    update_telegram = {"$set": {"altchannels.channel1": 123456789}}
    await update_db(telegramdata, filter_telegram, update_telegram)
    
    # Delete example
    await delete_db(telecorddata, {"useridtg": 37422429})
    await delete_db(telegramdata, {"useridtg": 786737498})

    # Get example
    result_telecord = await get_db(telecorddata, {"useridtg": Int64(37422429)})
    print("Telecord Data:", result_telecord)
    
    result_telegram = await get_db(telegramdata, {"useridtg": Int64(786737498)})
    print("Telegram Data:", result_telegram)