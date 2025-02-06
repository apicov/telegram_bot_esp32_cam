import paho.mqtt.client as mqtt
import base64
import os
import json

with open("private_data.json", "r") as read_file:
    p_data = json.load(read_file)


# Define the MQTT settings
broker = p_data["mqtt_broker_ip"]  # Change this to your broker's address
port = p_data["mqtt_broker_port"]            # Default MQTT port
topic = "/camera/img"   # Topic to subscribe to for image data

counter = 0



# Callback when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribe to the topic
    client.subscribe(topic)

# Callback when a message is received from the server
def on_message(client, userdata, msg):
    global counter
    print(f"Message received on topic {msg.topic}")
    
    # Decode the base64 image
    try:
        image_data = base64.b64decode(msg.payload)
        
        # Save the image to a file
        image_filename = f"./images_test/received_image{counter}.jpg"
        counter += 1
        with open(image_filename, "wb") as image_file:
            image_file.write(image_data)
        
        print(f"Image saved as {image_filename}")
    except Exception as e:
        print(f"Error decoding or saving image: {e}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(broker, port, 60)

# Start the loop to process network traffic and dispatch callbacks
client.loop_start()

# Keep the script running to listen for messages
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting...")
finally:
    client.loop_stop()
    client.disconnect()
