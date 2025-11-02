#!/usr/bin/env python3
"""Test script for V-Guard MQTT discovery."""
import asyncio
import json
import paho.mqtt.client as mqtt_client

# Configuration
MQTT_BROKER = "192.168.0.4"
MQTT_PORT = 1883
DISCOVERY_TOPIC = "device/dups/CE01/#"
DISCOVERY_TIMEOUT = 10  # Shorter timeout for testing

discovered = {}

def on_connect(client, userdata, flags, rc):
    """Handle MQTT connection."""
    if rc == 0:
        print(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(DISCOVERY_TOPIC)
        print(f"✓ Subscribed to topic: {DISCOVERY_TOPIC}")
    else:
        print(f"✗ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Handle MQTT messages."""
    try:
        print(f"\n📨 Received message on topic: {msg.topic}")
        print(f"   Payload length: {len(msg.payload)} bytes")

        # Extract serial from topic
        topic_parts = msg.topic.split("/")
        serial = None

        # Handle both telemetry and LWT topics
        if "lwt" in topic_parts:
            # LWT topic: device/dups/CE01/lwt/{serial}
            if len(topic_parts) >= 5:
                serial = topic_parts[4]
                print(f"   Found serial from LWT topic: {serial}")
        elif len(topic_parts) >= 4:
            # Telemetry topic: device/dups/CE01/{serial}
            serial = topic_parts[3]
            print(f"   Found serial from telemetry topic: {serial}")
        else:
            print(f"   ✗ Topic format not recognized")
            return

        # Validate serial
        if serial and len(serial) > 5:
            if serial not in discovered:
                discovered[serial] = {
                    "host": MQTT_BROKER,
                    "port": MQTT_PORT,
                    "serial": serial,
                }
                print(f"   ✓ Discovered new device: {serial}")
            else:
                print(f"   ⊙ Device already discovered: {serial}")

            # Try to parse payload
            try:
                if msg.payload:
                    payload = json.loads(msg.payload)
                    print(f"   Payload keys: {list(payload.keys())}")
            except json.JSONDecodeError:
                print(f"   Payload (raw): {msg.payload.decode()}")
        else:
            print(f"   ✗ Invalid serial: {serial}")

    except Exception as err:
        print(f"   ✗ Error processing message: {err}")

async def test_discovery():
    """Test the discovery process."""
    print("=" * 60)
    print("V-Guard MQTT Discovery Test")
    print("=" * 60)

    # Create MQTT client
    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"\n🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT}...")

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        # Wait for discovery
        print(f"\n⏱️  Listening for {DISCOVERY_TIMEOUT} seconds...\n")
        for i in range(DISCOVERY_TIMEOUT):
            await asyncio.sleep(1)
            if (i + 1) % 5 == 0:
                print(f"   [{i+1}/{DISCOVERY_TIMEOUT}s] Found {len(discovered)} device(s)")

        # Stop MQTT client
        client.loop_stop()
        client.disconnect()

        # Show results
        print("\n" + "=" * 60)
        print(f"Discovery Complete - Found {len(discovered)} device(s)")
        print("=" * 60)

        if discovered:
            for serial, info in discovered.items():
                print(f"\n✓ Device: {serial}")
                print(f"  Host: {info['host']}")
                print(f"  Port: {info['port']}")
        else:
            print("\n✗ No devices found!")
            print("\nTroubleshooting:")
            print("1. Check if inverter is publishing to MQTT")
            print("2. Verify DNS: vguardbox.com → MQTT broker")
            print("3. Run: mosquitto_sub -h 192.168.0.4 -p 1883 -t 'device/dups/CE01/#' -v")

    except Exception as err:
        print(f"✗ Error: {err}")

if __name__ == "__main__":
    asyncio.run(test_discovery())
