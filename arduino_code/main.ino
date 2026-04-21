#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>

const char* WIFI_SSID = "Your WiFi SSID";
const char* WIFI_PASS = "Your WiFi Password";
WebServer server(80);

// LED pins
const int builtinLedPin = 4;  // Built-in LED (usually GPIO 4 on AI-Thinker)

// LED control
bool shouldBlink = false;
unsigned long previousMillis = 0;
const long blinkInterval = 500;  // 500ms blink interval
bool ledState = false;

static auto res = esp32cam::Resolution::find(640, 480);

void serveJpg() {
  auto frame = esp32cam::capture();
  if (!frame) {
    server.send(503, "text/plain", "Capture failed");
    return;
  }
  
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Cache-Control", "no-cache");
  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  frame->writeTo(client);
}

void handleControl() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET");
  
  if (server.hasArg("auth")) {
    String auth = server.arg("auth");
    shouldBlink = (auth == "Flash");
    server.send(200, "text/plain", shouldBlink ? "LED_BLINKING" : "LED_OFF");
  } else {
    shouldBlink = false;
    server.send(200, "text/plain", "LED_OFF");
  }
}

void setup() {
  Serial.begin(115200);
  
  // Initialize LED pin
  pinMode(builtinLedPin, OUTPUT);
  digitalWrite(builtinLedPin, LOW);

  // Camera config
  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(res);
    cfg.setBufferCount(2);
    cfg.setJpeg(80);
    Camera.begin(cfg);
  }

  // WiFi
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // Server endpoints
  server.on("/cam.jpg", serveJpg);
  server.on("/control", handleControl);
  
  server.begin();
}

void loop() {
  server.handleClient();
  
  // Handle LED blinking
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= blinkInterval) {
    previousMillis = currentMillis;
    if (shouldBlink) {
      ledState = !ledState;
      digitalWrite(builtinLedPin, ledState ? HIGH : LOW);
    } else {
      digitalWrite(builtinLedPin, LOW);
    }
  }
  delay(10);
}
