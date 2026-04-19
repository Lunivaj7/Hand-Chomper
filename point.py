import cv2
import mediapipe as mp
import time
import math
import paho.mqtt.client as mqtt

#mqtt setup
PI_IP = "10.184.176.60"
client = mqtt.Client()

print(f"Connecting to Pi at {PI_IP}...")
try:
    client.connect(PI_IP, 1883, 60)
    # Starts a background thread to handle MQTT network traffic smoothly
    client.loop_start() 
    print("Connected to MQTT Broker! Ready for gestures.")
except Exception as e:
    print(f"Could not connect: {e}")
    print("Make sure the Pi is on the same Wi-Fi and the broker is running!")
    # We won't exit here so you can still test the camera if the Pi is offline

#mediapipe setup
mpHands = mp.solutions.hands
hands = mpHands.Hands(
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mpDraw = mp.solutions.drawing_utils
landmark_style = mpDraw.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=3)
connection_style = mpDraw.DrawingSpec(color=(0, 255, 0), thickness=2)

# Video capture setup
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

lastFrameTime = 0
frame_count = 0
process_frames = 2
process_data_frames = 10

# State tracker to prevent spamming the same command over and over
last_sent_cmd = None

#hand sensor
def get_hand_arr(handLms, img):
    h, w, c = img.shape
    lm = []

    for i in range(21):
        x = int(handLms.landmark[i].x * w)
        y = int(handLms.landmark[i].y * h)
        lm.append((x, y))

    x11, y11 = lm[7]
    x12, y12 = lm[8]

    
    dir_threshold = 12    

    output = "STOP"

    dx = x12 - x11
    dy = y12 - y11

    if abs(dx) > abs(dy) + 6: # Horizontal
        if dx > dir_threshold: # Left
            output = "RIGHT"
        elif dx < -dir_threshold: # Right
            output = "LEFT"
    else: # Vertical
        if dy > dir_threshold: # Up
            output = "DOWN" 
        elif dy < -dir_threshold: # Down
            output = "UP"

    return output

def send(message):
    global last_sent_cmd
    
    # Only publish if the command is an actual direction
    if message in ["UP", "DOWN", "LEFT", "RIGHT"]:
        # Only publish if it's a NEW command (prevents spamming the Pi)
        if message != last_sent_cmd:
            try:
                client.publish("pacman/control", message)
                print(f"MQTT Sent: {message}")
                last_sent_cmd = message
            except Exception as e:
                print(f"Failed to send MQTT message: {e}")
                
    # If the user stops pinching, reset the last command 
    # so they can send the same direction again if they want to
    elif message == "STOP":
        last_sent_cmd = None

#Loop
while True:
    success, img = cap.read()
    if not success:
        continue
    
    img = cv2.flip(img, 1) 
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    thisFrameTime = time.time()
    frame_dif = thisFrameTime - lastFrameTime
    if (frame_dif != 0):
        fps = 1 / (frame_dif)
    else:
        fps = 0
    lastFrameTime = thisFrameTime
    cv2.putText(img, f'FPS:{int(fps)}', (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    frame_count += 1

    if frame_count % process_frames == 0:
        results = hands.process(imgRGB)
        
        if results.multi_hand_landmarks:
            for handLms, handLabel in zip(results.multi_hand_landmarks, results.multi_handedness):
                mpDraw.draw_landmarks(
                    img, 
                    handLms, 
                    mpHands.HAND_CONNECTIONS,
                    landmark_style,
                    connection_style
                )

                if (frame_count % process_data_frames == 0):
                    hand_gesture = get_hand_arr(handLms, img)
                    # Pass the gesture directly to our updated send function
                    send(hand_gesture) 

    cv2.imshow("Hand Control", img)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ==========================================
# 5. CLEANUP
# ==========================================
cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
print("Disconnected and closed.")