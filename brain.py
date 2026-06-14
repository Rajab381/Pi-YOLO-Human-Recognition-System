import cv2
import requests
from ultralytics import YOLO

# Load the AI model
model = YOLO('yolov8n.pt')

# ⚠️ UPDATE THIS WITH YOUR RASPBERRY PI'S IP ADDRESS
PI_IP = "192.168.93.88"
stream_url = f"http://{PI_IP}:5000/video_feed"
control_url = f"http://{PI_IP}:5000/control"

cap = cv2.VideoCapture(stream_url)
last_cmd = ""


def send_command(direction):
    global last_cmd
    if direction != last_cmd:  # Only sends when direction changes to save network lag
        try:
            requests.get(f"{control_url}/{direction}", timeout=0.05)
            last_cmd = direction
        except:
            pass


print("AI Brain started. Processing stream in real-time...")

while True:
    # ⚡ BUFFER CLEARING TRICK: Skip old backlogged frames to get the absolute newest frame
    for _ in range(4):
        cap.grab()
    ret, frame = cap.retrieve()

    if not ret:
        print("Lost stream connection.")
        break

    screen_center = frame.shape[1] // 2
    results = model.track(frame, persist=True, classes=[0], verbose=False)

    if results[0].boxes and results[0].boxes.xyxy is not None:
        box = results[0].boxes.xyxy[0].cpu().numpy()
        p_center = int((box[0] + box[2]) / 2)

        # Draw green bounding box around the detected person
        cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)

        # Determine tracking direction based on screen center offset
        offset = p_center - screen_center
        if offset < -60:
            print("◀️ LEFT")
            send_command("left")
        elif offset > 60:
            print("▶️ RIGHT")
            send_command("right")
        else:
            print("🚶‍♂️ FORWARD")
            send_command("forward")
    else:
        print("❌ STOP (No person found)")
        send_command("stop")

    # Display the live window on your laptop desktop
    cv2.imshow("Robot Vision (High-Speed Testing)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()