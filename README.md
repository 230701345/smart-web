# Smart Cart (ESP32 + Flask)

## Local Run
1. `python -m pip install -r requirements.txt`
2. `python app.py`
3. Open `http://127.0.0.1:5000/`
   - Login: `demo` / `SmartCart!123`

## ESP32 Local
- Put your PC and ESP32 on the same WiFi RalphSSID NB.
- Start Flask (`python app.py`) and note the LAN URL in the terminal, e.g., `http://10.0.0.5:5000`
- Set the ESP32 URL to `http://<your-pc-ip>:5000/api/scan`

## UIDs
- Milk: `66339797` (₹50)
- Rice: `6F2A9C1F` (₹40)
- Tomato: `E5340402` (₹30)
