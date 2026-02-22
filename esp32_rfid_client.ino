#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

const char* ssid = "YOUR_SSID";
const char* pass = "YOUR_PASSWORD";
const char* server = "http://10.25.75.54:5000/api/scan";

constexpr uint8_t RST_PIN = 22;
constexpr uint8_t SS_PIN = 21;

MFRC522 rfid(SS_PIN, RST_PIN);

String uidHex(const MFRC522::Uid& uid) {
  String s = "";
  for (byte i = 0; i < uid.size; i++) {
    if (uid.uidByte[i] < 16) s += "0";
    s += String(uid.uidByte[i], HEX);
  }
  s.toUpperCase();
  return s;
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pass);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < 20000) {
    delay(500);
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connect timeout");
  }
}

void setup() {
  Serial.begin(115200);
  connectWiFi();
  SPI.begin();
  rfid.PCD_Init();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    delay(50);
    return;
  }
  String uid = uidHex(rfid.uid);
  Serial.print("Scanned UID: ");
  Serial.println(uid);
  String payload = String("{\"uid\":\"") + uid + String("\"}");
  HTTPClient http;
  http.setConnectTimeout(6000);
  http.setTimeout(8000);
  http.begin(server);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(payload);
  if (code > 0) {
    String res = http.getString();
    Serial.print("HTTP ");
    Serial.println(code);
    Serial.println(res);
  } else {
    Serial.print("HTTP error: ");
    Serial.println(code);
  }
  http.end();
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(1000);
}
