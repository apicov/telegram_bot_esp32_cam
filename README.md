# About

This project provides a simple [Telegram](https://telegram.org/) bot that waits
for user commands and at the same time listens to incoming messages from a
[MQTT](https://mqtt.org/) broker.

The concrete application provided by this project allows the users to send
"[snap](https://github.com/apicov/esp32cam_snap)" commands to a ESP32-Cam device
and send the captured snapshots back to the user via telegram.

# Usage

The dependencies of this project are listed in the `requirements.txt` file.
Before using this bot, the required dependencies need to be
[installed](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#using-a-requirements-file).

## Configuration

The bot requires some configuration before it can be used. This project provides
an example configuration file named `application_configuration.example.yaml`
which serves a starting up point for the configuration. Copy this file into
another one and name it `application.configuration.yaml`.

The second step is to generate a
"[token](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)" for the
bot, and once the token is available, set it in the `token` field of the
configuration file.

Finally, configure the MQTT broker and topics; these values should match the
values configured for the device running the
[esp32cam_snap](https://github.com/apicov/esp32cam_snap) code. It's worth
mentioning that if the bot is running on the same host than the MQTT broker,
then the preferred IP address to use is the `127.0.0.1`.

## Execute

Run the bot by executing the following command:

```sh
  python mqtt_bot.py
```

## Security

For security reasons, the "snap" commands are processed for allowed users
*only*. The allowed users must be listed in the `allowed_users` setting in the
configuration file, such list requires the users' *Telegram numeric user ID*;
there are many ways to retrieve this ID; one of them is to ask the user to send
the "/start" command to the running instance of the bot, then the bot will reply
the message `Hola <numeric_user_id>`. Once the `allowed_users` are configured, then
the bot needs to be restarted.


