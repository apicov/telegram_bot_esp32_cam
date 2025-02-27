import base64
from io import BytesIO
from PIL import Image
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import asyncio
import threading

async def send_photo_async(chat_id, img_bytes):
    try:
        print("Preparing to send the image...")
        img_bytes.seek(0)  # Ensure the BytesIO pointer is at the start
        await bot_instance.send_photo(chat_id=chat_id, photo=img_bytes, caption='Received Image')
        print("Image sent successfully.")
    except Exception as e:
        print(f"Error sending photo: {e}")

#async def send_photo_async(chat_id, img_bytes):
#    print("llego la imagen")
#    await bot_instance.send_photo(chat_id=chat_id, photo=img_bytes, caption='Received Image')

# Load mqtt and bot info 
with open("private_data.json", "r") as read_file:
    data = json.load(read_file)

TOKEN = data['telegram_token']

# MQTT settings
MQTT_BROKER = data['mqtt_broker_ip']
MQTT_PORT = data['mqtt_broker_port']
MQTT_TOPIC_CMD = "/camera/cmd"
MQTT_TOPIC_IMG = "/camera/img"

# Initialize MQTT client
mqtt_client = mqtt.Client()

# Global variable to store the bot instance
bot_instance = None
# Global variable to store the event loop
telegram_event_loop = None

# Dictionary to store chat_ids for each user
user_chat_ids = {}
# Dictionary to store the user who requested the snap
snap_requests = {}


def on_message(client, userdata, message):
    print('mensaje')
    if message.topic == MQTT_TOPIC_IMG:
        print('foto')

        # Decode the base64 image
        img_data = base64.b64decode(message.payload)
        
        # Open the image using Pillow
        img = Image.open(BytesIO(img_data))

        # Optionally, you can perform some processing with Pillow here
        # For example, resizing the image
        #img = img.resize((100, 100))  # Resize to 100x100 pixels

        # Convert image to bytes for sending via Telegram
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)  # Move to the beginning of the BytesIO buffer

        # Create a list of user IDs to process
        user_ids_to_process = list(snap_requests.keys())
        print(f"User IDs to process: {user_ids_to_process}")

        for user_id in user_ids_to_process:
            chat_id = user_chat_ids.get(user_id)
            if chat_id is not None:
                print(f"Scheduling photo send to chat_id: {chat_id}")
                try:
                    future = asyncio.run_coroutine_threadsafe(send_photo_async(chat_id, img_bytes), telegram_event_loop)
                    print("Coroutine scheduled.")
                except Exception as e:
                    print(f"Error scheduling coroutine: {e}")
                del snap_requests[user_id]



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_chat_ids[user_id] = update.message.chat_id  # Store the chat_id for the user
    await update.message.reply_text("Hola")

async def snap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_chat_ids[user_id] = update.message.chat_id  # Update the chat_id for the user
    snap_requests[user_id] = True  # Mark this user as having requested a snap
    # Send the /snap command through MQTT
    command = "snap"  # Define the command you want to send
    mqtt_client.publish(MQTT_TOPIC_CMD, command)
    await update.message.reply_text("Snap command sent!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Your existing handle_photo code...
    pass  # Implement your photo handling logic here


# Function to run the MQTT client in a separate thread
def start_mqtt():
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    mqtt_client.loop_forever()


# Create the Telegram bot application
app = ApplicationBuilder().token(TOKEN).build()
# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("snap", snap))  # Add the /snap command handler
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# Store the bot instance in the global variable
bot_instance = app.bot

# Set the global event loop immediately after creating the bot
telegram_event_loop = asyncio.get_event_loop()


# Set up MQTT client
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.subscribe(MQTT_TOPIC_IMG)
mqtt_client.loop_start()  # Start the MQTT loop

# Run the MQTT client in a separate thread
#mqtt_thread = threading.Thread(target=start_mqtt)
#mqtt_thread.start()


# Start the bot
app.run_polling()

# Stop the MQTT client when done
mqtt_client.loop_stop()
mqtt_client.disconnect()

