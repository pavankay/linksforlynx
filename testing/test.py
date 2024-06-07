from pymongo import MongoClient
from flask_bcrypt import Bcrypt

# MongoDB configuration
DB_NAME = "LinksforLynx"
USER_COLLECTION = "users"
MONGO_URI = "mongodb+srv://pavan:PsxriMfTSYLltWgK@lfl.rvewoyg.mongodb.net/{DB_NAME}?retryWrites=true&w=majority"

# Initialize MongoDB client and Bcrypt
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
bcrypt = Bcrypt()

# Admin credentials
admin_email = "admin@admin.admin"
admin_password = "admin"
admin_username = "admin"

# Hash the admin password
hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')

# Insert admin account into the database
user_collection = db[USER_COLLECTION]
admin_account = {
    "username": admin_username,
    "email": admin_email,
    "password": hashed_password,
    "confirmed": True  # Admin account is confirmed by default
}

# Check if admin account already exists
existing_admin = user_collection.find_one({"email": admin_email})
if existing_admin:
    print("Admin account already exists.")
else:
    user_collection.insert_one(admin_account)
    print("Admin account created successfully.")
