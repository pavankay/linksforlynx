import pymongo

# MongoDB configuration
MONGO_URI = "mongodb+srv://pavan:PsxriMfTSYLltWgK@lfl.rvewoyg.mongodb.net/LinksforLynx?retryWrites=true&w=majority"
DB_NAME = "LinksforLynx"
PROJECT_COLLECTION = "projects"

# Initialize MongoDB client
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
project_collection = db[PROJECT_COLLECTION]

# Find all projects and update their username to lowercase
projects = project_collection.find()
for project in projects:
    updated_username = project['username'].lower()
    project_collection.update_one(
        {'_id': project['_id']},
        {'$set': {'username': updated_username}}
    )
    print(f"Updated project {project['_id']}: username={updated_username}")

# Close the MongoDB connection
client.close()
