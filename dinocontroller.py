import cv2
import numpy as np
import pyautogui
import time
import sys


SKIN_LOWER = np.array([0, 20, 70], dtype="uint8")
SKIN_UPPER = np.array([20, 255, 255], dtype="uint8")

MIN_CONTOUR_AREA = 5000

current_dino_action = 'NEUTRAL'

GAME_WINDOW_TITLE = "T-Rex Game - Google Chrome"


def focus_game_window():
    """Find and activate (focus) the T-Rex game window."""
    try:
        windows = pyautogui.getWindowsWithTitle(GAME_WINDOW_TITLE)
        if not windows:
            windows = pyautogui.getWindowsWithTitle('Google Chrome')

        if windows:
            game_window = windows[0]

            if not game_window.isActive:
                game_window.activate()
                time.sleep(0.1)
            return True
        else:
            return False

    except Exception as e:
        return False


def jump(current_action, finger_count):
    """Press the 'Space' key to make the dinosaur jump."""
    if current_action == 'DUCK':
        pyautogui.keyUp('down')

    focus_game_window()
    pyautogui.press('space')
    print(f"Fingers: {finger_count} -> JUMP")
    return 'JUMP'


def duck(current_action, finger_count):
    """Press the 'Down' key to make the dinosaur duck."""
    if current_action != 'DUCK':
        focus_game_window()
        pyautogui.keyDown('down')
        print(f"Fingers: {finger_count} -> DUCK")
    return 'DUCK'


def release_key(current_action, finger_count, log_message="NEUTRAL/RUNNING"):
    """Release the 'Down' key so the dinosaur runs normally."""
    if current_action == 'DUCK':
        focus_game_window()
        pyautogui.keyUp('down')

    if current_action != 'NEUTRAL':
        print(f"Fingers: {finger_count} -> {log_message}")

    return 'NEUTRAL'


def count_fingers(contour, hull):
    """Count the number of fingers using convex hull and convexity defects."""

    defects = cv2.convexityDefects(contour, hull)

    if defects is None:
        return 0

    finger_count = 0

    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0]

        start = tuple(contour[s][0])
        end = tuple(contour[e][0])
        far = tuple(contour[f][0])

        a = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        b = np.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
        c = np.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)

        try:
            cosine_angle = (b**2 + c**2 - a**2) / (2 * b * c)
            cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
            angle = np.arccos(cosine_angle)
            angle = np.degrees(angle)

        except ZeroDivisionError:
            angle = 180
        except ValueError:
            angle = 180

        if angle <= 90 and d > 10000:
            finger_count += 1

    return min(finger_count + 1, 5)


def run_dino_controller():
    """Main controller loop."""
    print("--- Webcam Motion-Based Google Dino Game Controller (Finger Detection) ---")
    print(f"Target window title: {GAME_WINDOW_TITLE}")
    print("!!! IMPORTANT: Control is based on the number of fingers detected !!!")
    print("  - 3 or more fingers: JUMP")
    print("  - 1 or fewer fingers: DUCK")
    print("  - 2 fingers: NEUTRAL")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open webcam. Please check your camera connection.")
        return

    global current_dino_action
    current_dino_action = 'NEUTRAL'

    cv2.namedWindow("Dino Controller View (Finger Count)", cv2.WINDOW_AUTOSIZE)

    print("Move your hand to control the game. (Adjust lighting if skin detection is unstable.)")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to read frame.")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_frame, SKIN_LOWER, SKIN_UPPER)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        finger_count = 0

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            largest_area = cv2.contourArea(largest_contour)

            if largest_area > MIN_CONTOUR_AREA:

                if len(largest_contour) >= 5:
                    hull = cv2.convexHull(largest_contour, returnPoints=False)

                    finger_count = count_fingers(largest_contour, hull)

                    cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)

                    hull_points = cv2.convexHull(largest_contour, returnPoints=True)
                    cv2.drawContours(frame, [hull_points], -1, (255, 0, 0), 2)

                else:
                    finger_count = 0

                if finger_count >= 3:
                    if current_dino_action != 'JUMP':
                        current_dino_action = jump(current_dino_action, finger_count)

                elif finger_count <= 1 and finger_count != 0:
                    current_dino_action = duck(current_dino_action, finger_count)

                else:
                    if current_dino_action != 'NEUTRAL':
                        current_dino_action = release_key(current_dino_action, finger_count)

            else:
                if current_dino_action != 'NEUTRAL':
                    current_dino_action = release_key(current_dino_action, 0, "Object Too Small -> NEUTRAL/RUNNING")

        else:
            if current_dino_action != 'NEUTRAL':
                current_dino_action = release_key(current_dino_action, 0, "Object Not Found -> NEUTRAL/RUNNING")

        cv2.putText(frame,
                    f"Action: {current_dino_action}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        cv2.putText(frame,
                    f"Fingers: {finger_count}",
                    (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        cv2.putText(frame,
                    "JUMP (3+) | NEUTRAL (2) | DUCK (1)",
                    (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Dino Controller View (Finger Count)", frame)
        cv2.imshow("Skin Mask (Debug)", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("--- controller end ---")


if __name__ == "__main__":
    run_dino_controller()