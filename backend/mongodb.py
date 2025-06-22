from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Read password from environment variable
password = os.getenv("MONGO_PASSWORD")

# Construct the MongoDB URI with the password (no ssl_cert_reqs in URI)
uri = f"mongodb+srv://adityasen120:{password}@cluster0.xwt5zar.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB with tlsAllowInvalidCertificates for macOS dev
try:
    client = MongoClient(uri, tlsAllowInvalidCertificates=True)
    # Test the connection
    client.admin.command('ping')
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    client = None

""" Player DB """
if client is not None:
    db = client["basketball_database"]
    collection = db["basketball_player_stats"]
else:
    db = None
    collection = None

def create_player(name, team, points=0, assists=0, rebounds=0, fouls=0):
    if collection is None:
        return None
        
    if collection.find_one({"name": name}):
        return None
    
    player = {
        "name": name,
        "team": team,
        "points": points,
        "assists": assists,
        "rebounds": rebounds,
        "fouls": fouls
    }
    try:
        result = collection.insert_one(player)
        return result.inserted_id
    except Exception as e:
        print(f"Error creating player: {e}")
        return None

def update_player(name, updates):
    if collection is None:
        return 0
        
    try:
        result = collection.update_one(
            {"name": name},
            {"$set": updates}
        )
        return result.modified_count
    except Exception as e:
        print(f"Error updating player: {e}")
        return 0

def get_player(name):
    if collection is None:
        return None
        
    try:
        player = collection.find_one({"name": name})
        return player
    except Exception as e:
        print(f"Error getting player: {e}")
        return None

def get_all_players():
    if collection is None:
        return []
        
    try:
        players = list(collection.find())
        return players
    except Exception as e:
        print(f"Error getting all players: {e}")
        return []

def delete_player(name):
    if collection is None:
        return 0
        
    try:
        result = collection.delete_one({"name": name})
        return result.deleted_count
    except Exception as e:
        print(f"Error deleting player: {e}")
        return 0

""" User Account DB """
if client is not None:
    user_db = client["UserDB"]
    users_collection = user_db["users"]
else:
    user_db = None
    users_collection = None

def create_user(first_name, last_name, email, password):
    if users_collection is None:
        return None
        
    try:
        if users_collection.find_one({"email": email}):
            return None

        user = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password
        }
        result = users_collection.insert_one(user)
        return result.inserted_id
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def update_user(email, updates):
    if users_collection is None:
        return 0
        
    try:
        result = users_collection.update_one(
            {"email": email},
            {"$set": updates}
        )
        return result.modified_count
    except Exception as e:
        print(f"Error updating user: {e}")
        return 0

def get_user(email):
    if users_collection is None:
        return None
        
    try:
        user = users_collection.find_one({"email": email})
        return user
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    
def get_all_users():
    if users_collection is None:
        return []
        
    try:
        users = list(users_collection.find())
        return users
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []

def delete_user(email):
    if users_collection is None:
        return 0
        
    try:
        result = users_collection.delete_one({"email": email})
        return result.deleted_count
    except Exception as e:
        print(f"Error deleting user: {e}")
        return 0
