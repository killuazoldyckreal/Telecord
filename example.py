import time

# Assuming `data_dict` is the dictionary loaded from the MongoDB collection
data_dict = {}

async def watch_for_changes(interval=60):
    while True:
        await asyncio.sleep(interval)
        # Check for changes
        new_data_dict = await load_collection()
        updates = {}
        
        for key, value in new_data_dict.items():
            if key in data_dict:
                if data_dict[key] != value:
                    updates[key] = value
            else:
                updates[key] = value
        
        if updates:
            await update_mongo(updates)
            data_dict.update(updates)
            print(f"Updated documents: {updates}")

async def update_mongo(updates):
    # Update MongoDB with changes
    for key, value in updates.items():
        await collection.update_one({'_id': value['_id']}, {'$set': value})

async def main():
    global data_dict
    data_dict = await load_collection()
    await watch_for_changes()

# Run the main function to start watching for changes
asyncio.run(main())


async def watch_changes():
    async with collection.watch() as stream:
        async for change in stream:
            process_change(change)

def process_change(change):
    global data_dict
    document_id = str(change['documentKey']['_id'])
    
    if change['operationType'] == 'update':
        updated_fields = change['updateDescription']['updatedFields']
        for field, value in updated_fields.items():
            data_dict[document_id][field] = value
    elif change['operationType'] == 'insert':
        data_dict[document_id] = change['fullDocument']
    elif change['operationType'] == 'delete':
        del data_dict[document_id]

async def main():
    global data_dict
    data_dict = await load_collection()
    asyncio.create_task(watch_changes())
    while True:
        await asyncio.sleep(60)  # Keep the main function running

# Run the main function to start watching for changes
asyncio.run(main())
