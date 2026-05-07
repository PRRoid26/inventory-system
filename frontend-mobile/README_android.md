# IT Asset Manager — Android Setup

## Run on Desktop (test before building APK)

```bash
pip install kivy kivymd requests
python main_android.py
```

## Build APK for Android

### 1. Install Buildozer (Linux only — use WSL on Windows)
```bash
pip install buildozer
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool
```

### 2. First build (downloads Android SDK/NDK automatically — ~2 GB, takes 20-30 min)
```bash
buildozer android debug
```
APK will be at: `bin/itassetmanager-1.0.0-arm64-v8a-debug.apk`

### 3. Install on phone
```bash
# via USB (adb must be installed, USB debugging enabled on phone)
buildozer android deploy run

# OR copy the APK to your phone and open it
adb install bin/itassetmanager-1.0.0-arm64-v8a-debug.apk
```

## File structure
```
frontend-mobile/
├── main_android.py    ← The full app (this file)
├── buildozer.spec     ← Android packaging config
└── README.md
```

## What's identical to the desktop app
- `APIClient` — all endpoints, pagination, auth
- `LocationHistory` — persists to ~/.it_asset_locations.json
- `_detect_api_url()` — tries local NAS first, falls back to cloud
- All worklog create/update/complete logic
- Same date formats (YYYY-MM-DD, no T00:00:00 suffix)

## Screens
| Screen         | Features                                               |
|----------------|--------------------------------------------------------|
| Login          | Username/password, auto backend detection              |
| Overview       | Status stat cards, active log summary                  |
| Inventory      | Search, status filter chips, tap for detail            |
| Active Logs    | Change Status, Make Available, tap for detail + return |
| Past Logs      | Searchable history                                     |
| Import History | List of CSV imports                                    |
