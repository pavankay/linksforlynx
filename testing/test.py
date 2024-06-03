import pymongo
from flask_bcrypt import Bcrypt

# MongoDB configuration
MONGO_URI = "mongodb+srv://pavan:PsxriMfTSYLltWgK@lfl.rvewoyg.mongodb.net/LinksforLynx?retryWrites=true&w=majority"
DB_NAME = "LinksforLynx"
USER_COLLECTION = "users"

# Initialize MongoDB client
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
user_collection = db[USER_COLLECTION]

# Initialize Bcrypt
bcrypt = Bcrypt()

# Define the user data
username = "joe"
email = "bob@gmail.com"
password = "123"

# Hash the password
hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

# Check if the user already exists
if user_collection.find_one({"email": email}):
    print(f"User with email {email} already exists.")
else:
    # Insert the new user
    user_collection.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password
    })
    print(f"User {username} created successfully with email {email}.")

# Close the MongoDB connection
client.close()
