*****Installation & Setup*****

1. Hardware Setup: 

    Connect ESP32-CAM with ESP32-CAM-MB
  
    Plug into your system via USB
  
2. Arduino IDE Setup:

    Install Arduino IDE
    
    Add ESP32 board support:
    
    Go to File → Preferences

    Add this URL in Additional Board Manager URLs: https://dl.espressif.com/dl/package_esp32_index.json
    
    Go to Tools → Board → Board Manager
    
    Install ESP32 by Espressif Systems
    
    Select board: AI Thinker ESP32-CAM
  
3. Upload Code to ESP32-CAM:

    Open Arduino code from arduino_code/main.ino
  
    Update:
    
        Wi-Fi SSID
      
        Password
    
    Upload code to ESP32-CAM
    
    Open Serial Monitor → Copy the IP Address
  
4. Python Setup:

    Install dependencies:
      pip install opencv-python pyzbar requests
    
5. Run Python Script:

    Open python_code/main.py
    
    Replace ESP32 IP:
      ESP32_IP = "http://your-ip-address"
      
     Run:
     python main.py

    
*****How It Works*****

ESP32-CAM streams live video

Python script scans QR codes

Extracted data is validated:

If in authorized list → send signal to in-built LED to flash

Else → ignore

Logs stored in CSV file
