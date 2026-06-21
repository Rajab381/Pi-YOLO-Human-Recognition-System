import cv2
import requests
import time
from ultralytics import YOLO

# Model initialization
model = YOLO('yolov8n.pt')

# ⚠️ APNA IP ADDRESS YAHA UPDATE RAKHEIN
PI_IP = "192.168.199.88"
control_url = f"http://{PI_IP}:5000/control"
stream_url = f"http://{PI_IP}:5000/video_feed"
buzzer_url = f"http://{PI_IP}:5000/buzzer/lock"

cap = cv2.VideoCapture(stream_url)

# Non-blocking burst controls
motor_start_time = 0
motor_active = False
current_direction = "stop"

# --- 🎯 THE PERFECTED UNI-HOTSPOT PARAMETERS ---
forward_burst = 0.035  # Safe micro-forward approach
turn_burst = 0.016  # 🔥 ULTRA-SHORT TICK (Inertia controls over-turning)
burst_duration = 0.04

# Master Lock Configurations
target_locked = False
lock_start_time = None
lock_duration = 3.0
locked_box_center = None


def send_command_instant(url_route):
    try:
        # Strict timeout to never freeze the processing script
        requests.get(url_route, timeout=0.01)
    except:
        pass


print("⚡ UNI-HOTSPOT BULLETPROOF ENGINE ACTIVE... Stand centered to lock.")

while True:
    # 🔥 CORE NETWORK FIX: Force-clear OpenCV's network queue cache completely
    # Takes only the freshest frame directly from the network pipeline
    for _ in range(5):
        cap.grab()
    ret, frame = cap.retrieve()

    if not ret:
        print("Camera Stream Error.")
        break

    # Real-time resolution compression down to optimize inference speed over hotspot
    frame = cv2.resize(frame, (320, 240))

    h, w, c = frame.shape
    screen_center = w // 2
    current_time = time.time()

    # 1. Non-Blocking Physical Burst Handler
    if motor_active and (current_time - motor_start_time >= burst_duration):
        send_command_instant(f"{control_url}/stop")

        # 🔥 THE NETWORK LAG FLUSHER:
        if current_direction in ["left", "right"]:
            print("⏳ Damping inertia... Flushing hotspot delay frames.")
            time.sleep(0.55)  # Shanti break for turns to absorb floor momentum
            for _ in range(20):  # Dump all bottlenecked past movement frames
                cap.grab()
        else:
            time.sleep(0.18)  # Break for straight lines
            for _ in range(10):
                cap.grab()

        motor_active = False
        current_direction = "stop"

    # 2. Precision Vision Processing Engine
    if not motor_active:
        current_conf = 0.65 if not target_locked else 0.40
        results = model(frame, classes=[0], conf=current_conf, verbose=False)
        boxes = results[0].boxes.xyxy.cpu().numpy() if (results[0].boxes and results[0].boxes.xyxy is not None) else []

        # --- PHASE 1: TARGET COUNTDOWN LOCK ---
        if not target_locked:
            send_command_instant(f"{control_url}/stop")
            if len(boxes) > 0:
                if lock_start_time is None:
                    lock_start_time = time.time()

                elapsed_time = time.time() - lock_start_time
                remaining = max(0, int(lock_duration - elapsed_time))

                box = boxes[0]
                cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 165, 255), 2)
                cv2.putText(frame, f"LOCKING IN: {remaining}s", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

                if elapsed_time >= lock_duration:
                    target_locked = True
                    locked_box_center = int((box[0] + box[2]) / 2)
                    print("🎯 MASTER SECURED. Triggering Pi Buzzer...")

                    # 🔥 TRIGGER PI BUZZER TUNE ON SUCCESSFUL LOCK
                    send_command_instant(buzzer_url)
            else:
                lock_start_time = None
                cv2.putText(frame, "SEARCHING FOR MASTER...", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # --- PHASE 2: MASTER LOCKED TRACKING MODE ---
        else:
            best_box = None
            min_dist = float('inf')

            for box in boxes:
                current_center = int((box[0] + box[2]) / 2)
                dist = abs(current_center - locked_box_center)
                if dist < min_dist and dist < 350:
                    min_dist = dist
                    best_box = box

            if best_box is not None:
                locked_box_center = int((best_box[0] + best_box[2]) / 2)
                box_height = best_box[3] - best_box[1]
                # WIDER DEADZONE TO FILTER OUT NETWORK PING LATENCY FLICKERS
                offset = locked_box_center - screen_center

                cv2.rectangle(frame, (int(best_box[0]), int(best_box[1])), (int(best_box[2]), int(best_box[3])),
                              (0, 255, 0), 2)
                cv2.putText(frame, f"🔓 MASTER ACTIVE | OFFSET: {offset}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # --- THE DYNAMIC MOVEMENT DECISION TREE (Deadzone = 95) ---
                if offset < -95:
                    print("▶️ HOTSPOT TURN: Right Micro-Tick")
                    burst_duration = turn_burst
                    send_command_instant(f"{control_url}/right")
                    motor_start_time = time.time()
                    motor_active = True
                    current_direction = "right"

                elif offset > 95:
                    print("◀️ HOTSPOT TURN: Left Micro-Tick")
                    burst_duration = turn_burst
                    send_command_instant(f"{control_url}/left")
                    motor_start_time = time.time()
                    motor_active = True
                    current_direction = "left"

                else:
                    if box_height > 160:  # Scaled for 320x240 frame format
                        print("⚠️ Guard Active -> Safe Step Backward")
                        burst_duration = 0.05
                        send_command_instant(f"{control_url}/backward")
                        motor_start_time = time.time()
                        motor_active = True
                        current_direction = "backward"

                    elif box_height < 110:  # Scaled for 320x240 frame format
                        print("🚶‍♂️ Pursuit Active -> Step Forward")
                        burst_duration = forward_burst
                        send_command_instant(f"{control_url}/forward")
                        motor_start_time = time.time()
                        motor_active = True
                        current_direction = "forward"

                    else:
                        if current_direction != "stop":
                            send_command_instant(f"{control_url}/stop")
                            current_direction = "stop"
            else:
                cv2.putText(frame, "⚠️ TARGET LOST! Standing Still.", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                if current_direction != "stop":
                    send_command_instant(f"{control_url}/stop")
                    current_direction = "stop"

    cv2.imshow("King Uni-Hotspot Fail-Safe Follower", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('r'):
        target_locked = False
        lock_start_time = None
        print("🔄 Manual lock reset triggered...")
    elif key == ord('q'):
        send_command_instant(f"{control_url}/stop")
        break

cap.release()
cv2.destroyAllWindows()