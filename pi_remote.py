import paho.mqtt.client as mqtt
import time

PI_IP = "10.184.176.60"
client = mqtt.Client()

print(f"Connecting to Pi at {PI_IP}...")

try:
    client.connect(PI_IP, 1883, 60)
    print("Connected! Type UP, DOWN, LEFT, or RIGHT (or 'q' to quit)")

    while True:
        cmd = input("Command: ").upper()

        if cmd == 'Q':
            break

        if cmd in ["UP", "DOWN", "LEFT", "RIGHT"]:
            # This sends the message to the Pi
            client.publish("pacman/control", cmd)
            print(f"Sent: {cmd}")
        else:
            print("Invalid command. Use UP, DOWN, LEFT, or RIGHT.")

except Exception as e:
    print(f"Could not connect: {e}")
    print("Make sure the Pi is on the same Wi-Fi and the pacman_input.py script is running!")

finally:
    client.disconnect()