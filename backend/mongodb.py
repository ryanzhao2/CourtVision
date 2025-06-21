from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Read password from environment variable
password = os.getenv("MONGO_PASSWORD")

# Construct the MongoDB URI with the password
uri = f"mongodb+srv://adityasen120:{password}@clustermain.cswnpek.mongodb.net/?retryWrites=true&w=majority&appName=ClusterMain"

# Connect to MongoDB
client = MongoClient(uri)

# Access database and collection
db = client["basketball_database"]
collection = db["basketball_player_stats"]

db_account = client["accounts_database"]
collection_account = db_account["account_collection"]

def create_player(name, team, points=0, assists=0, rebounds=0, fouls=0):
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
    if result.modified_count > 0:
        print(f"Player '{name}' updated successfully.")
    else:
        print(f"No updates made (player may not exist or values are the same).")

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
