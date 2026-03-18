import argparse
import json
import random
import time
from dataclasses import dataclass

import paho.mqtt.client as mqtt


@dataclass
class SensorState:
    moisture: float = 52.0
    temperature: float = 24.0

    def next_reading(self) -> dict:
        # Use a gentle random walk so the feed feels more like a real farm sensor.
        self.moisture = min(85.0, max(18.0, self.moisture + random.uniform(-4.2, 3.6)))
        self.temperature = min(37.0, max(12.0, self.temperature + random.uniform(-1.7, 1.9)))
        return {
            "moisture": round(self.moisture, 2),
            "temperature": round(self.temperature, 2),
            "sensor_id": "field-node-01",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish simulated farm sensor readings over MQTT.")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", default="farm/sensor", help="MQTT topic to publish to")
    parser.add_argument("--interval", type=float, default=3.0, help="Seconds between samples")
    return parser


def build_client() -> mqtt.Client:
    client = mqtt.Client()

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print(f"Connected to MQTT broker with result code {reason_code}.")

    client.on_connect = on_connect
    return client


def main() -> None:
    args = build_parser().parse_args()
    client = build_client()
    client.connect(args.host, args.port, keepalive=60)
    client.loop_start()

    state = SensorState()
    print(
        f"Publishing simulated readings to mqtt://{args.host}:{args.port}/{args.topic} "
        f"every {args.interval:.1f}s"
    )

    try:
        while True:
            payload = state.next_reading()
            result = client.publish(args.topic, json.dumps(payload))
            result.wait_for_publish()
            print("Published:", payload)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSensor publisher stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
