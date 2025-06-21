from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Read password from environment variable
password = os.getenv("MONGO_PASSWORD")

# Construct the MongoDB URI with the password
uri = f"mongodb+srv://adityasen120:{password}@cluster0.xwt5zar.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB
client = MongoClient(uri)

""" Player DB """
db = client["basketball_database"]
collection = db["basketball_player_stats"]

def create_player(name, team, points=0, assists=0, rebounds=0, fouls=0):
    if users_collection.find_one({"name": name}):
        return None
    
    player = {
        "name": name,
        "team": team,
        "points": points,
        "assists": assists,
        "rebounds": rebounds,
        "fouls": fouls
    }
    result = collection.insert_one(player)

def update_player(name, updates):
    result = collection.update_one(
        {"name": name},
        {"$set": updates}
    )

    return result.modified_count

def get_player(name):
    player = collection.find_one({"name": name})
    if player:
        return player
    else:
        return None

def get_all_players():
    players = list(collection.find())

    return players

def delete_player(name):
    result = collection.delete_one({"name": name})

    return result.deleted_count


""" User Account DB """
db = client["UserDB"]
users_collection = db["users"]

def create_user(first_name, last_name, email, password):
    if users_collection.find_one({"email": email}):
        return None

    user = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password  # You can hash this later
    }
    result = users_collection.insert_one(user)

    return result.inserted_id

def update_user(email, updates):
    result = users_collection.update_one(
        {"email": email},
        {"$set": updates}
    )
    
    return result.modified_count

def get_user(email):
    user = users_collection.find_one({"email": email})

    if user:
        return user
    else:
        return None
    
def get_all_users():
    users = list(users_collection.find())

    return users

def delete_user(email):
    result = users_collection.delete_one({"email": email})
    
    return result.deleted_count
