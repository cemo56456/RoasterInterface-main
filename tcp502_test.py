import time
import ssl
from paho.mqtt import client as mqtt_client

from services.config import load_config

_mqtt_cfg = load_config()["mqtt"]
broker = _mqtt_cfg["broker"]
port = _mqtt_cfg["port"]
topic = "TOPIC1"
username = _mqtt_cfg["username"]
password = _mqtt_cfg["password"]


def connect_mqtt():

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code:", rc)

    client = mqtt_client.Client(
        mqtt_client.CallbackAPIVersion.VERSION1,
        client_id="cem_python_script"
    )

    client.username_pw_set(username, password)

    client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    client.on_connect = on_connect

    client.connect(broker, port)

    return client


client = connect_mqtt()

client.loop_start()

while True:
    time.sleep(1)