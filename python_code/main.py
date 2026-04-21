import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
import requests
import time
from requests.exceptions import RequestException
import csv
from datetime import datetime
import os

# Configuration
ESP_IP = "192.168.71.166"  # Update with your ESP32's IP
CAM_URL = f"http://{ESP_IP}/cam.jpg"
CTRL_URL = f"http://{ESP_IP}/control"
VALID_BLOCKS = ["Block-A", "Block-B", "Block-C", "Block-D", "Block-E"]
TIMEOUT = 3
SCAN_INTERVAL = 0.1
MAX_RETRIES = 3
LOG_FILE = "qr_scan_log.csv" #Update with your csv file name

class QRScanner:
    def __init__(self):
        self.last_qr = None
        self.window_name = "QR Scanner"
        self.current_block = None
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        self.initialize_log_file()
        
    def initialize_log_file(self):
        """Initialize the log file with headers"""
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "timestamp",
                    "qr_data",
                    "status",
                    "control_sent",
                    "control_status"
                ])
    
    def get_current_timestamp(self):
        """Get properly formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def log_event(self, qr_data, status, control_sent, control_status):
        """Log an event to the CSV file"""
        timestamp = self.get_current_timestamp()
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp,
                qr_data if qr_data else "None",
                status,
                "Yes" if control_sent else "No",
                "Success" if control_status else "Failed"
            ])
    
    def get_frame(self):
        """Capture frame from camera"""
        for _ in range(MAX_RETRIES):
            try:
                resp = requests.get(CAM_URL, timeout=TIMEOUT)
                if resp.status_code == 200:
                    img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        return img
            except RequestException as e:
                print(f"Camera error: {str(e)}")
            time.sleep(0.5)
        return None
    
    def send_control(self, qr_data):
        """Send control command to ESP32"""
        try:
            # Determine if QR code is valid
            is_valid = qr_data in VALID_BLOCKS
            params = {"auth": "Flash" if is_valid else "NoFlash"}
            
            # Update status message
            if is_valid:
                status_message = f"Valid Block: {qr_data} - LED flashing"
                self.current_block = qr_data
            else:
                status_message = f"Unauthorized: {qr_data} - No action"
                self.current_block = None
            
            # Send command to ESP32
            resp = requests.get(CTRL_URL, params=params, timeout=TIMEOUT)
            success = resp.status_code == 200
            return success, status_message
        except RequestException as e:
            print(f"Control error: {str(e)}")
            return False, "Control command failed"
    
    def process_frame(self, frame):
        """Process frame for QR codes and update display"""
        decoded = pyzbar.decode(frame)
        current_qr = decoded[0].data.decode() if decoded else None
        
        if current_qr != self.last_qr:
            if current_qr:
                control_status, status_message = self.send_control(current_qr)
                print(status_message)
                
                # Log the event
                status = "Valid Block" if current_qr in VALID_BLOCKS else "Unauthorized"
                self.log_event(current_qr, status, True, control_status)
                
                if not control_status:
                    print("Failed to send control command")
            else:
                print("QR lost")
                self.send_control(None)
                self.log_event(None, "No QR", True, False)
                self.current_block = None
            
            self.last_qr = current_qr
        
        # Display status
        status = "Valid Block" if self.current_block else "Unauthorized" if current_qr else "No QR"
        color = (0, 255, 0) if status == "Valid Block" else (0, 0, 255) if status == "Unauthorized" else (255, 255, 255)
        
        # Main status text
        cv2.putText(frame, f"Status: {status}", (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # Additional info line
        info_text = self.current_block if self.current_block else (current_qr if current_qr else "Scanning...")
        cv2.putText(frame, info_text, (20, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        return frame
    
    def run(self):
        """Main scanning loop"""
        try:
            print(f"Starting QR scanner. Logging to {LOG_FILE}")
            print("Valid blocks: " + ", ".join(VALID_BLOCKS))
            print("Press ESC to stop...")
            
            while True:
                frame = self.get_frame()
                if frame is None:
                    print("Failed to get frame, retrying...")
                    continue
                
                frame = self.process_frame(frame)
                cv2.imshow(self.window_name, frame)
                
                if cv2.waitKey(1) == 27:  # ESC key
                    break
                
                time.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print("\nScanner stopped by user")
        finally:
            cv2.destroyAllWindows()
            print(f"Scanner stopped. Data logged to {LOG_FILE}")

if __name__ == "__main__":
    scanner = QRScanner()
    scanner.run()
