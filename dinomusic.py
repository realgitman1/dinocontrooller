
import cv2
import numpy as np
import pyaudio

SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024  
VOLUME_SCALING = 0.5 

BASE_FILTER_ALPHA = 0.05 
MAX_FILTER_ALPHA = 0.5  


global_freq = 100.0 
global_gain = 0.0   
global_filter_alpha = BASE_FILTER_ALPHA 


p = pyaudio.PyAudio()
stream = None
current_phase = 0.0         
prev_filter_output = 0.0    적

def audio_callback(in_data, frame_count, time_info, status):
    """PyAudio 스트림에 의해 호출되어 실시간 오디오 데이터를 생성합니다."""
    global current_phase, global_freq, global_gain, prev_filter_output, global_filter_alpha
    
 
    t = np.arange(frame_count) / SAMPLE_RATE
    
 
    phases = current_phase + t * (2 * np.pi * global_freq)
    
    sawtooth = np.mod(phases / (2 * np.pi), 1) * 2 - 1
    
   
    filtered_data = np.zeros_like(sawtooth)
    
    current_alpha = global_filter_alpha
    
    for i in range(frame_count):
      
        filtered_data[i] = prev_filter_output + current_alpha * (sawtooth[i] - prev_filter_output)
        prev_filter_output = filtered_data[i] 


    audio_data = (filtered_data * global_gain * VOLUME_SCALING).astype(np.float32)
    
    
    current_phase = phases[-1]
    
    return (audio_data.tobytes(), pyaudio.paContinue)

def start_audio_stream():
    """PyAudio 비차단(non-blocking) 스트림을 시작합니다."""
    global stream
    stream = p.open(format=pyaudio.paFloat32,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=audio_callback)


CAMERA_INDEX = 0  


SKIN_LOWER = np.array([0, 20, 70], dtype="uint8")
SKIN_UPPER = np.array([17, 255, 255], dtype="uint8") 

MIN_CONTOUR_AREA = 5000 
MAX_AREA_EXPECTED = 50000 
FREQ_MIN = 100          
FREQ_MAX = 800           
GAIN_MIN = 0.0          
GAIN_MAX = 0.5          



def map_value(value, in_min, in_max, out_min, out_max):
    """값을 한 범위에서 다른 범위로 매핑합니다."""
    value = np.clip(value, in_min, in_max)
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def count_fingers(contour):
    """볼록성 결함을 사용하여 손가락 개수를 계산합니다."""
    if len(contour) < 5:
        return 0

    hull_indices = cv2.convexHull(contour, returnPoints=False)
    if len(hull_indices) < 3: 
        return 0
        
    defects = cv2.convexityDefects(contour, hull_indices)
    if defects is None:
        return 0

    finger_count = 0
    depth_threshold_pixels = 20 
    
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0] 
        depth_pixels = d / 256.0 
        
        if depth_pixels > depth_threshold_pixels:
            finger_count += 1
            
    return min(finger_count + 1, 5)


def process_frame(frame):
    """단일 프레임을 처리하고 전역 신디사이저 매개변수를 업데이트합니다."""
    global global_freq, global_gain, global_filter_alpha
    
    
    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape
    
   
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, SKIN_LOWER, SKIN_UPPER)
    
   
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
   
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    largest_contour = None
    max_area = MIN_CONTOUR_AREA
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        max_area = cv2.contourArea(largest_contour)
        
    if max_area > MIN_CONTOUR_AREA:
     
        M = cv2.moments(largest_contour)
        
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
         
            finger_count = count_fingers(largest_contour)
            
           
            
           
            hand_y_norm = cy / frame_height 
            target_freq = map_value(hand_y_norm, 0, 1, FREQ_MAX, FREQ_MIN)
            
          
            target_gain = map_value(finger_count, 0, 5, GAIN_MIN, GAIN_MAX)
           
            target_alpha = map_value(max_area, MIN_CONTOUR_AREA, MAX_AREA_EXPECTED, BASE_FILTER_ALPHA, MAX_FILTER_ALPHA)
            
          
            global_freq = target_freq
            global_gain = target_gain
            global_filter_alpha = target_alpha
            
          
            cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)
    
            cv2.putText(frame, f"Pitch: {target_freq:.1f} Hz", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Volume: {target_gain:.2f} ({finger_count} Fingers)", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Tone (Alpha): {target_alpha:.3f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
        else:
            global_freq = FREQ_MIN
            global_gain = GAIN_MIN
            global_filter_alpha = BASE_FILTER_ALPHA
            
    else:
        global_freq = FREQ_MIN
        global_gain = GAIN_MIN
        global_filter_alpha = BASE_FILTER_ALPHA

    
    cv2.line(frame, (0, frame_height // 2), (frame_width, frame_height // 2), (0, 0, 255), 1)

    return frame




def main():
    print("--- 모션 제어 신디사이저 (Python/OpenCV/PyAudio - 필터 적용) ---")
    print("제어 방식:")
    print("  1. Pitch (주파수): 손의 세로 위치 (위: 고음, 아래: 저음)")
    print("  2. Volume (볼륨): 펼친 손가락 개수 (많을수록: 크게)")
    print("  3. Tone (배음): 손의 크기/영역 (클수록: 날카로움/배음 많음, 작을수록: 부드러움/배음 적음)")
    print("Ctrl+C 또는 'q' 키를 눌러 종료하세요.")
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("오류: 웹캠을 열 수 없습니다. CAMERA_INDEX (0)를 확인하거나 다른 값을 시도해 보세요.")
        return
        
    try:
        start_audio_stream()
    except Exception as e:
        print(f"오류: PyAudio 스트림 시작 실패 - {e}")
        cap.release()
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("오류: 프레임을 읽을 수 없습니다. 종료합니다...")
                break

            processed_frame = process_frame(frame)
            cv2.imshow('Motion Synth Control', processed_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n키보드 인터럽트로 애플리케이션을 종료합니다...")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()