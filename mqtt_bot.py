import base64
from io import BytesIO
from PIL import Image
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from urllib.parse import urlparse
import yaml
import asyncio

async def send_photo_async(chat_id, img_bytes):
    """
    Send the IMAGE_BYTES as a photo to the given CHAT_ID.
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
    id = update.message.from_user.id;
    if (id not in allowed_users):
        print(f"user {id} isn't allowed to use the 'start' command")
    else:
        await update.message.reply_text(f"Hola {id}")


async def snap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the "snap" command. It forwards the command to the MQTT broker.
    """
    id = update.message.from_user.id
    if (id not in allowed_users):
        print(f"user {id} isn't allowed to use the 'snap' command")
    else:
        user_chat_ids[id] = update.message.chat_id  # Update the chat_id for the user
        snap_requests[id] = True  # Mark this user as having requested a snap
        mqtt_client.publish(MQTT_TOPIC_CMD, "snap")
        await update.message.reply_text("Snap command sent!")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Your existing handle_photo code...
    pass  # Implement your photo handling logic here


if __name__ == '__main__':
    # Dictionary to store chat_ids for each user
    user_chat_ids = {}

    # Dictionary to store the user who requested the snap
    snap_requests = {}

    # Load mqtt and bot info
    with open("app_configuration.yaml", "r") as config_file:
        c_ = yaml.safe_load(config_file)

    # list of allowed telegram user IDs
    allowed_users = set(c_['telegram']['allowed_users'])

    # MQTT settings
    broker = urlparse(c_['mqtt']['broker_uri'])
    topics = c_['mqtt']['topics']
    MQTT_TOPIC_IMG = topics.get('images'  , '/camera/img')
    MQTT_TOPIC_CMD = topics.get('commands', '/camera/cmd')

    # Initialize MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.connect(broker.hostname, broker.port or 1883, 60)
    mqtt_client.subscribe(MQTT_TOPIC_IMG)
    mqtt_client.loop_start()  # Start the MQTT loop

    # Create the Telegram bot application
    app = ApplicationBuilder().token(c_['telegram']['token']).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("snap", snap))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Global variable to store the bot instance
    bot_instance = app.bot

    telegram_event_loop = asyncio.get_event_loop()

    # Start the bot
    app.run_polling()

    # Stop the MQTT client when done
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
