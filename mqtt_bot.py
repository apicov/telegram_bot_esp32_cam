import base64
from io import BytesIO
from PIL import Image
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import asyncio

async def send_photo_async(chat_id, img_bytes):
    """
    Send the IMAGE_BYTES to the given CHAT_ID as a photo.
    """
    print(f"{chat_id}: Preparing to send the photo")
    try:
        img_bytes.seek(0)  # Ensure the BytesIO pointer is at the start
        await bot_instance.send_photo(chat_id, img_bytes, caption='Received Image')
        print(f"{chat_id}: The photo was sent")
    except Exception as e:
        print(f"{chat_id}: ERROR sending photo: {e}")


def on_message(client, userdata, message):
    """
    This function is called when the there's an incoming MESSAGE
    from the MQTT CLIENT. If the message is an image, then that
    image forwarded
    """
    print(f'Incoming message in {message.topic}')
    if message.topic == MQTT_TOPIC_IMG:
        # Decode the base64 image
        img_data = base64.b64decode(message.payload)

        # Open the image using Pillow
        img = Image.open(BytesIO(img_data))

        # Convert image to bytes for sending via Telegram
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)  # Move to the beginning of the BytesIO buffer

        # Create a list of user IDs to process
        # TODO: To use a dictionary to store the users' requests
        # is an error for Python prior v3.7 because they're
        # unordered, so there are chances that the picture is
        # forwarded to the wrong user. So why not use a list instead?
        user_ids_to_process = list(snap_requests.keys())
        for user_id in user_ids_to_process:
            chat_id = user_chat_ids.get(user_id)
            if chat_id is not None:
                try:
                    asyncio.run_coroutine_threadsafe(send_photo_async(chat_id, img_bytes), telegram_event_loop)
                    print(f"{chat_id}: Image scheduled to be sent")
                except Exception as e:
                    print(f"Error scheduling coroutine: {e}")
                del snap_requests[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the "start" command. It replies with the text "Hola".
    """
    await update.message.reply_text("Hola")


async def snap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the "snap" command. It forwards the command to the MQTT broker.
    """
    user_id = update.message.from_user.id
    user_chat_ids[user_id] = update.message.chat_id  # Update the chat_id for the user
    snap_requests[user_id] = True  # Mark this user as having requested a snap

    mqtt_client.publish(MQTT_TOPIC_CMD, "snap")
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


if __name__ == '__main__':

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


    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.subscribe(MQTT_TOPIC_IMG)
    mqtt_client.loop_start()  # Start the MQTT loop

    # Start the bot
    app.run_polling()

    # Stop the MQTT client when done
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
