import asyncio
import logging
from datetime import datetime, timedelta, timezone

import pytz
from pymongo import MongoClient
from pyrogram import Client, filters, idle

api_id = 'your_api_id'
api_hash = 'your_api_hash'
bot_token = 'bot_token'

OWNER_ID = 293768732
CHAT_GROUP_ID = -123456788



app = Client(
    "hexcoin_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token
)



logging.basicConfig(
    filename='hexcoin_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)



mongo_uri = (
    "mongodb+srv://example:exaple123@systemdata.vyhjllc.mongodb.net/"
    "?retryWrites=true&w=majority&appName=SystemData"
)

client = MongoClient(
    mongo_uri,
    tz_aware=True,
    tzinfo=timezone.utc
)

db = client["hexcoin_bot"]

users_collection = db["users"]



def get_current_time():
    """Return the current UTC time."""
    return datetime.now(timezone.utc)



async def send_message_to_groups():
    """
    Send a checkup message every 3 hours.
    """

    while True:
        try:
            await app.send_message(
                "@HexCoinBank",
                "Checkup Message 📝"
            )

            logger.info("Checkup message sent successfully.")

        except Exception as e:
            logger.error(
                f"Error sending checkup message: {e}",
                exc_info=True
            )

        # Wait 3 hours
        await asyncio.sleep(3 * 60 * 60)



@app.on_message(filters.command("start"))
async def start(client, message):

    try:
        user_id = message.from_user.id

        # Create wallet only if it doesn't already exist.
        result = users_collection.update_one(
            {"_id": user_id},
            {
                "$setOnInsert": {
                    "balance": 100,
                    "last_claim": None
                }
            },
            upsert=True
        )

        if result.upserted_id is not None:

            await message.reply_text(
                '''
Welcome to HexCoin Bot! 🎉

💰 Your Wallet:
A new wallet has been created for you with an initial balance of 100 hexcoins. Start your journey by exploring the commands below!

📜 Commands:

➥/balance: Check your current balance.
➥/send <amount>: Send hexcoins to another user by replying to their message.
➥/daily: Claim your daily reward of 50 hexcoins (once every 24 hours).
➥/help: Get detailed information about all available commands.

🚀 Get Started:
Use /balance to see your balance and /daily to claim your first daily reward.

If you have any questions or need help, just type /help for more information.

Happy HexCoining! 🌟
'''
            )

            logger.info(
                f"New user {user_id} registered with 100 HexCoins."
            )

        else:

            user = users_collection.find_one(
                {"_id": user_id}
            )

            if user:
                await message.reply_text(
                    f"Welcome back! \n"
                    f"Your current balance is {user['balance']} HexCoins."
                )

    except Exception as e:

        logger.error(
            f"Error in /start for user "
            f"{getattr(message.from_user, 'id', 'unknown')}: {e}",
            exc_info=True
        )

        await message.reply_text(
            "An error occurred. Please try again later."
        )



@app.on_message(filters.command("balance"))
async def balance(client, message):

    try:
        user_id = message.from_user.id

        user = users_collection.find_one(
            {"_id": user_id}
        )

        if user:

            await message.reply_text(
                f"Your current balance is "
                f"{user['balance']} HexCoins."
            )

        else:

            await message.reply_text(
                "You don't have a wallet yet. "
                "Use /start to create one."
            )

    except Exception as e:

        logger.error(
            f"Error in /balance: {e}",
            exc_info=True
        )

        await message.reply_text(
            "An error occurred. Please try again later."
        )



@app.on_message(filters.command("send"))
async def send(client, message):

    try:

        user_id = message.from_user.id

        parts = message.text.split()

        # Check command format
        if len(parts) != 2:

            await message.reply_text(
                "Usage: /send Amount"
            )

            return

        # Must be a reply
        if not message.reply_to_message:

            await message.reply_text(
                "Please reply to the user you want to send "
                "HexCoins to with the command /send Amount."
            )

            return

        # Parse amount
        try:

            amount = int(parts[1])

        except ValueError:

            await message.reply_text(
                "Please provide a valid amount."
            )

            return

        # Prevent negative / zero transfers
        if amount <= 0:

            await message.reply_text(
                "Amount must be greater than 0."
            )

            return

        # Make sure replied message has a user
        if not message.reply_to_message.from_user:

            await message.reply_text(
                "Unable to identify the target user."
            )

            return

        target_user_id = (
            message.reply_to_message.from_user.id
        )

        # Can't send to yourself
        if target_user_id == user_id:

            await message.reply_text(
                "You cannot send HexCoins to yourself!"
            )

            return

        # Check sender
        sender = users_collection.find_one(
            {"_id": user_id}
        )

        if sender is None:

            await message.reply_text(
                "You don't have a wallet yet. "
                "Use /start first."
            )

            return

        # Check receiver
        target_user = users_collection.find_one(
            {"_id": target_user_id}
        )

        if target_user is None:

            await message.reply_text(
                "The target user does not have a wallet."
            )

            return
   
        # MongoDB Atlas supports transactions.
        with client.start_session() as session:

            with session.start_transaction():

                # Deduct only if the sender actually has
                # enough balance.
                result = users_collection.update_one(
                    {
                        "_id": user_id,
                        "balance": {"$gte": amount}
                    },
                    {
                        "$inc": {
                            "balance": -amount
                        }
                    },
                    session=session
                )

                # Sender did not have enough balance
                if result.modified_count != 1:

                    session.abort_transaction()

                    await message.reply_text(
                        "You don't have enough HexCoins "
                        "to complete this transaction."
                    )

                    return

                # Add coins to receiver
                receiver_result = users_collection.update_one(
                    {"_id": target_user_id},
                    {
                        "$inc": {
                            "balance": amount
                        }
                    },
                    session=session
                )

                # Receiver disappeared / update failed
                if receiver_result.modified_count != 1:

                    session.abort_transaction()

                    await message.reply_text(
                        "Transaction failed. "
                        "Please try again later."
                    )

                    return

        # Transaction succeeded
        await message.reply_text(
            f"Successfully sent {amount} HexCoins "
            f"to user {target_user_id}."
        )

        logger.info(
            f"Transfer: {amount} HexCoins "
            f"from {user_id} to {target_user_id}"
        )

    except Exception as e:

        logger.error(
            f"Error in /send: {e}",
            exc_info=True
        )

        await message.reply_text(
            "An error occurred. Please try again later."
        )

@app.on_message(filters.command("daily"))
async def daily(client, message):

    try:

        user_id = message.from_user.id

        current_time = get_current_time()

        user = users_collection.find_one(
            {"_id": user_id}
        )

        if not user:

            await message.reply_text(
                "You don't have a wallet yet. "
                "\nUse /start to create one."
            )

            return

        last_claim_time = user.get("last_claim")

    
        if last_claim_time is None:

            result = users_collection.update_one(
                {
                    "_id": user_id,
                    "last_claim": None
                },
                {
                    "$inc": {
                        "balance": 100
                    },
                    "$set": {
                        "last_claim": current_time
                    }
                }
            )

            if result.modified_count == 1:

                await message.reply_text(
                    "Congratulations!\n"
                    "You have claimed your daily reward "
                    "of 100 HexCoins."
                )

                logger.info(
                    f"User {user_id} claimed first daily reward."
                )

            else:

                await message.reply_text(
                    "You have already claimed your daily reward."
                )

            return

        
        # MongoDB returns timezone-aware UTC because the
        # MongoClient was configured with tz_aware=True.
        next_claim_time = (
            last_claim_time + timedelta(days=1)
        )

        if current_time >= next_claim_time:

            # Atomic protection against two simultaneous
            # /daily requests.
            result = users_collection.update_one(
                {
                    "_id": user_id,
                    "last_claim": last_claim_time
                },
                {
                    "$inc": {
                        "balance": 100
                    },
                    "$set": {
                        "last_claim": current_time
                    }
                }
            )

            if result.modified_count == 1:

                await message.reply_text(
                    "Congratulations!\n"
                    "You have claimed your daily reward "
                    "of 100 HexCoins."
                )

                logger.info(
                    f"User {user_id} claimed daily reward."
                )

            else:

                await message.reply_text(
                    "You have already claimed your daily reward."
                )

        else:

            remaining_time = (
                next_claim_time - current_time
            )

            total_seconds = int(
                remaining_time.total_seconds()
            )

            hours, remainder = divmod(
                total_seconds,
                3600
            )

            minutes, seconds = divmod(
                remainder,
                60
            )

            await message.reply_text(
                "You have already claimed your daily reward.\n"
                f"Next claim available in "
                f"{hours} hours, {minutes} minutes."
            )

    except Exception as e:

        logger.error(
            f"Error in /daily: {e}",
            exc_info=True
        )

        await message.reply_text(
            "An error occurred. Please try again later."
        )



@app.on_message(filters.command("help"))
async def help_command(client, message):

    try:

        help_text = '''
HexCoin Bot Help Guide 📚

Welcome to HexCoin Bot! 
Below is a list of commands you can use to manage your HexCoins and interact with other users:

➥/start: Create a new wallet with an initial balance of 100 HexCoins.
➥/balance: Check your current HexCoin balance.
➥/send <amount>: Send HexCoins to another user by replying to their message with the command and the amount you wish to send.
➥/daily: Claim your daily reward of 100 HexCoins (once every 24 hours).
➥/help: Display this help message with a list of available commands and their descriptions.
➥/id: Get your own user ID or the ID of another user by replying to their message.

Need assistance or have questions? 
Use /help to revisit this guide at any time.

@Funtastic4k
Happy HexCoining! 🌟
'''

        await message.reply_text(
            help_text
        )

    except Exception as e:

        logger.error(
            f"Error in /help: {e}",
            exc_info=True
        )



@app.on_message(filters.command("stats"))
async def stats(client, message):

    try:

        user_count = users_collection.count_documents({})

        total_balance_cursor = users_collection.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "total": {
                            "$sum": "$balance"
                        }
                    }
                }
            ]
        )

        total_balance_data = list(
            total_balance_cursor
        )

        if total_balance_data:

            total_balance = total_balance_data[0]["total"]

        else:

            total_balance = 0

        stats_message = (
            f"➥Total number of users: {user_count}\n"
            f"➥Total hexcoins: {total_balance}"
        )

        await message.reply_text(
            stats_message
        )

    except Exception as e:

        logger.error(
            f"Error in /stats: {e}",
            exc_info=True
        )

        await message.reply_text(
            "An error occurred. Please try again later."
        )



@app.on_message(filters.command("broadcast"))
async def broadcast(client, message):

    user_id = message.from_user.id

    # Owner-only
    if user_id != OWNER_ID:

        await message.reply_text(
            "You are not authorized to use this command."
        )

        return

    # Must reply to a message
    if not message.reply_to_message:

        await message.reply_text(
            "Please reply to the message you want "
            "to broadcast with the command /broadcast."
        )

        return

    try:

        # Get text from replied message
        broadcast_message = (
            message.reply_to_message.text
        )

        # If replied message doesn't contain text
        if not broadcast_message:

            await message.reply_text(
                "The replied message does not contain text."
            )

            return

        success_count = 0
        failure_count = 0

     
        users = users_collection.find({})

        for user in users:

            target_id = user["_id"]

            try:

                await app.send_message(
                    target_id,
                    broadcast_message
                )

                success_count += 1

            except Exception as e:

                failure_count += 1

                logger.error(
                    f"Broadcast failed for user "
                    f"{target_id}: {e}"
                )

            # Small delay to reduce flood risk
            await asyncio.sleep(0.05)

        try:

            async for dialog in app.get_dialogs():

                try:

                    chat = dialog.chat

                    if chat.type in [
                        "group",
                        "supergroup"
                    ]:

                        await app.send_message(
                            chat.id,
                            broadcast_message
                        )

                        success_count += 1

                        await asyncio.sleep(0.05)

                except Exception as e:

                    failure_count += 1

                    logger.error(
                        f"Broadcast failed for chat: {e}"
                    )

        except Exception as e:

            logger.error(
                f"Error retrieving dialogs: {e}",
                exc_info=True
            )

     
        summary_message = (
            "Broadcast completed.\n"
            f"➥Success: {success_count}\n"
            f"➥Failures: {failure_count}"
        )

        await app.send_message(
            OWNER_ID,
            summary_message
        )

        logger.info(
            f"Broadcast summary: {summary_message}"
        )

    except Exception as e:

        logger.error(
            f"Error in /broadcast: {e}",
            exc_info=True
        )

        await message.reply_text(
            "An error occurred during broadcasting."
        )



@app.on_message(filters.command("id"))
async def get_user_id(client, message):

    try:

        if message.reply_to_message:

            # Get ID of replied user
            if not message.reply_to_message.from_user:

                await message.reply_text(
                    "Unable to identify the user."
                )

                return

            target_user_id = (
                message.reply_to_message.from_user.id
            )

            await message.reply_text(
                f"The ID of the user you replied to is: "
                f"{target_user_id}"
            )

        else:

            # Get own ID
            user_id = message.from_user.id

            await message.reply_text(
                f"Your ID is: {user_id}"
            )

    except Exception as e:

        logger.error(
            f"Error in /id: {e}",
            exc_info=True
        )



async def main():

    logger.info("Starting HexCoin Bot...")

    await app.start()

    logger.info("HexCoin Bot started successfully.")

    # Start the 3-hour background task
    asyncio.create_task(
        send_message_to_groups()
    )

    # Keep Pyrogram running
    await idle()

    logger.info("Stopping HexCoin Bot...")

    await app.stop()

    logger.info("HexCoin Bot stopped.")



if __name__ == "__main__":

    try:

        app.run(main())

    except KeyboardInterrupt:

        logger.info(
            "HexCoin Bot stopped by user."
        )

    except Exception as e:

        logger.critical(
            f"Fatal error: {e}",
            exc_info=True
        )
