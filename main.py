from pyrogram import Client, filters
import logging
import pytz
from datetime import datetime, timedelta
from pymongo import MongoClient
from datetime import datetime, timezone



# Replace these with your API ID, hash, and bot token
api_id = '12997033'
api_hash = '31ee7eb1bf2139d96a1147f3553e0364'
bot_token = '6673562999:AAFWNCCzLuVU0rMUEi3d5j9cIoMsJGQLWpI'
OWNER_ID = 1352973730
CHAT_GROUP_ID = -1001650922754

app = Client("hexcoin_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Configure logging
logging.basicConfig(
    filename='hexcoin_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Get the current time in UTC
utc_now = datetime.now(timezone.utc)



# MongoDB setup (replace <username>, <password>, <dbname> with actual values)
mongo_uri = "mongodb+srv://syblewilliam8103:amanpathan123@systemdata.vyhjllc.mongodb.net/?retryWrites=true&w=majority&appName=SystemData"
client = MongoClient(mongo_uri)
db = client["hexcoin_bot"]
users_collection = db["users"]

# Function to ensure time sync
def sync_time():
    utc_now = datetime.now(pytz.utc)
   

# Sync time on start
sync_time()



@app.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id

    if users_collection.find_one({"_id": user_id}) is None:
        # Create a wallet for the new user with an initial balance of 100 HexCoins
        users_collection.insert_one({"_id": user_id, "balance": 100, "last_claim": None})
        message.reply_text('''

Welcome to HexCoin Bot! 🎉

💰 Your Wallet:
A new wallet has been created for you with an initial balance of 100 hexcoins. Start your journey by exploring the commands below!

📜 Commands:

➥/balance: Check your current balance.
➥/send <amount>: Send hexcoins to another user by replying to their message.
➥/daily: Claim your daily reward of 50 hexcoins (once every 24 hours).
➥/help: Get detailed information about all available commands.

🚀 Get Started:
Use /balance to see your balance and /daily to claim your first daily reward.\nIf you have any questions or need help, just type /help for more information.

Happy HexCoining! 🌟''')
        logger.info(f"New user {user_id} registered with 100 HexCoins.")
    else:
        user = users_collection.find_one({"_id": user_id})
        message.reply_text(f"Welcome back! \nYour current balance is {user['balance']} HexCoins.")
       

@app.on_message(filters.command("balance"))
def balance(client, message):
    user_id = message.from_user.id

    user = users_collection.find_one({"_id": user_id})
    if user:
        message.reply_text(f"Your current balance is {user['balance']} HexCoins.")
    else:
        message.reply_text("You don't have a wallet yet. Use /start to create one.")
       


@app.on_message(filters.command("send"))
def send(client, message):
    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) != 2:
        message.reply_text("Usage: /send Amount")
        return

    if not message.reply_to_message:
        message.reply_text("Please reply to the user you want to send HexCoins to with the command /send Amount.")
        return

    try:
        amount = int(parts[1])
        target_user_id = message.reply_to_message.from_user.id

        if target_user_id == user_id:
            message.reply_text("You cannot send HexCoins to yourself!")
            return

        sender = users_collection.find_one({"_id": user_id})
        if sender is None or sender["balance"] < amount:
            message.reply_text("You don't have enough HexCoins to complete this transaction.")
            return

        target_user = users_collection.find_one({"_id": target_user_id})
        if target_user is None:
            message.reply_text("The target user does not have a wallet.")
            return

        # Deduct the amount from sender's balance and add to receiver's balance
        users_collection.update_one({"_id": user_id}, {"$inc": {"balance": -amount}})
        users_collection.update_one({"_id": target_user_id}, {"$inc": {"balance": amount}})

        message.reply_text(f"Successfully sent {amount} HexCoins to user {target_user_id}.")
       
    except ValueError:
        message.reply_text("Please provide a valid amount.")
       
    except Exception as e:
       
        message.reply_text("An error occurred. Please try again later.")


@app.on_message(filters.command("daily"))
def daily(client, message):
    user_id = message.from_user.id
    current_time = datetime.now()

    user = users_collection.find_one({"_id": user_id})
    if user:
        last_claim_time = user.get("last_claim")
        if last_claim_time is None or current_time - last_claim_time >= timedelta(days=1):
            users_collection.update_one({"_id": user_id},
                                        {"$inc": {"balance": 100}, "$set": {"last_claim": current_time}})
            message.reply_text("Congratulations!\nYou have claimed your daily reward of 100 HexCoins.")
           
        else:
            remaining_time = timedelta(days=1) - (current_time - last_claim_time)
            hours, remainder = divmod(remaining_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            message.reply_text(
                f"You have already claimed your daily reward.\nNext claim available in {int(hours)} hours, {int(minutes)} minutes.")
           
    else:
        message.reply_text("You don't have a wallet yet. \nUse /start to create one.")
        


@app.on_message(filters.command("help"))
def help_command(client, message):
    help_text = ('''
HexCoin Bot Help Guide 📚

Welcome to HexCoin Bot! \nBelow is a list of commands you can use to manage your HexCoins and interact with other users:

➥/start: Create a new wallet with an initial balance of 100 HexCoins.
➥/balance: Check your current HexCoin balance.
➥/send <amount>: Send HexCoins to another user by replying to their message with this command and the amount you wish to send.
➥/daily: Claim your daily reward of 100 HexCoins (once every 24 hours).
➥/help: Display this help message with a list of available commands and their descriptions.
➥/id: Get your own user ID or the ID of another user by replying to their message.

Need assistance or have questions? \nUse /help to revisit this guide at any time.

@Funtastic4k
Happy HexCoining! 🌟'''
                 )
    message.reply_text(help_text)
   

@app.on_message(filters.command("stats"))
def stats(client, message):
    user_count = users_collection.count_documents({})
    total_balance = users_collection.aggregate([
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$balance"}
            }
        }
    ])
    total_balance = list(total_balance)[0]['total'] if total_balance else 0

    stats_message = f"➥Total number of users: {user_count}\n➥Total hexcoins: {total_balance} "
    message.reply_text(stats_message)
    

@app.on_message(filters.command("broadcast"))
def broadcast(client, message):
    user_id = message.from_user.id

    if user_id != OWNER_ID:
        message.reply_text("You are not authorized to use this command.")
        return

    if not message.reply_to_message:
        message.reply_text("Please reply to the message you want to broadcast with the command /broadcast.")
        return

    broadcast_message = message.reply_to_message.text
    success_count = 0
    failure_count = 0

    users = users_collection.find({})
    for user in users:
        try:
            app.send_message(user["_id"], broadcast_message)
            success_count += 1
        except Exception as e:
            failure_count += 1
           

    try:
        chats = app.get_dialogs()
        for chat in chats:
            if chat.chat.type in ["group", "supergroup"]:
                try:
                    app.send_message(chat.chat.id, broadcast_message)
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                   
    except Exception as e:
        logger.error(f"Error retrieving dialogs: {e}")

    summary_message = f"Broadcast completed.\n➥Success: {success_count}\n➥Failures: {failure_count}"
    app.send_message(OWNER_ID, summary_message)
    logger.info(f"Broadcast summary: {summary_message}")

@app.on_message(filters.command("id"))
def get_user_id(client, message):
    if message.reply_to_message:
        # If the command is used as a reply, get the ID of the replied-to user
        target_user_id = message.reply_to_message.from_user.id
        message.reply_text(f"The ID of the user you replied to is: {target_user_id}")

    else:
        # If the command is used directly, get the ID of the sender
        user_id = message.from_user.id
        message.reply_text(f"Your ID is: {user_id}")
       

if __name__ == "__main__":
    app.run()
