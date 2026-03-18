import json
import sqlite3
import time
from typing import Optional

import paho.mqtt.client as mqtt
import requests


DB_PATH = "farm.db"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "farm/sensor"
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=42.3&longitude=-83.0&current_weather=true"
)


def initialize_database() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moisture REAL,
            temperature REAL,
            weather_temp REAL,
            timestamp INTEGER
        )
        """
    )
    conn.commit()
    return conn


def fetch_weather_temperature(last_known: Optional[float]) -> float:
    try:
        response = requests.get(WEATHER_URL, timeout=10)
        response.raise_for_status()
        payload = response.json()
        current_weather = payload.get("current_weather", {})
        weather_temp = current_weather.get("temperature")
        if weather_temp is None:
            raise ValueError("Weather response did not include a temperature.")
        return float(weather_temp)
    except (requests.RequestException, ValueError) as exc:
        if last_known is not None:
            print(f"Weather lookup failed, reusing previous value {last_known:.1f} C. Reason: {exc}")
            return last_known
        print(f"Weather lookup failed with no fallback available. Reason: {exc}")
        return 0.0


def main() -> None:
    conn = initialize_database()
    cursor = conn.cursor()
    last_weather_temp: Optional[float] = None

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print(f"Connected to broker with result code {reason_code}. Subscribing to {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)

    def on_message(client, userdata, msg):
        nonlocal last_weather_temp
        try:
            data = json.loads(msg.payload.decode())
            moisture = float(data["moisture"])
            temperature = float(data["temperature"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            print(f"Skipping malformed message: {exc}")
            return

        weather_temp = fetch_weather_temperature(last_weather_temp)
        last_weather_temp = weather_temp
        timestamp = int(time.time())

        cursor.execute(
            "INSERT INTO data (moisture, temperature, weather_temp, timestamp) VALUES (?, ?, ?, ?)",
            (moisture, temperature, weather_temp, timestamp),
        )
        conn.commit()

        print(
            "Saved reading:",
            {
                "moisture": moisture,
                "temperature": temperature,
                "weather_temp": weather_temp,
                "timestamp": timestamp,
            },
        )

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    print(f"Listening for sensor data on mqtt://{MQTT_HOST}:{MQTT_PORT}/{MQTT_TOPIC}")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nIngestion service stopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
