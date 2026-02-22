# Smart Cart (ESP32 + Flask)

## Local Run
1. `python -m pip install -r requirements.txt`
2. `python app.py`
3. Open `http://127.0.0.1:5000/`
   - Login: `demo` / `SmartCart!123`

## Render Deploy
Option 1: Blueprint
- This repo includes `render.yaml`. On Render:
  - New → Blueprint → Use this repo `230701345/smart-web`
  - Render creates a Web Service and a PostgreSQL DB automatically

Option 2: Manual
- New → Web Service → Connect repo
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Add env vars:
  - `SECRET_KEY` → any random string
  - `DATABASE_URL` → Render Postgres connection string

## ESP32 Cloud
- Use HTTPS with `WiFiClientSecure` and `setInsecure()` for development.
- Set `SERVER_URL` to your Render URL: `https://<your>.onrender.com/api/scan`

## UIDs
- Milk: `66339797` (₹50)
- Rice: `6F2A9C1F` (₹40)
- Tomato: `E5340402` (₹30)
