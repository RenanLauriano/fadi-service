# FastAPI Server Ready Check

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## Build With Nuitka

1. **Setup virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. **Install requirements**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Nuitka**
   ```bash
   pip install nuitka
   ```
4. **Install OpenSSL** – ensure the `openssl` CLI is available (for Debian/Ubuntu `sudo apt install openssl`, macOS includes it by default).
5. **Generate self-signed certificates** for local HTTPS. From the repo root run:
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout privkey.pem -out cert.pem \
     -subj "/CN=localhost"
   ```
6. **Build using Nuitka** (run inside the virtual environment):
   ```bash
   python -m nuitka app/main.py \
     --onefile \
     --standalone \
     --include-package=fastapi \
     --include-package=uvicorn \
     --include-package=anyio \
     --include-package=starlette \
     --include-data-file=cert.pem=cert.pem \
     --include-data-file=privkey.pem=privkey.pem \
     --output-filename=fadi-service
   ```
7. **Run the generated binary**
   ```bash
   ./fadi-service
   ```

Visit `https://127.0.0.1:8443/health` to see:

```json
{"serverReady": true}
```
