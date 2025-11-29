# FastAPI Server Ready Check

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Locally

All TurboActivate assets must live inside the `app/` directory so both local and packaged runs can load them:

- `app/TurboActivate.dat`
- Platform library (download from [https://wyday.com/limelm/api/](https://wyday.com/limelm/api/))
  - Linux: `app/libTurboActivate.so`
  - macOS: `app/libTurboActivate.dylib`
  - Windows: `app/TurboActivate.dll`

Before running, make sure you have an SSL certificate and key available. You can use the `privkey.pem` / `cert.pem` generated in the Build section (step 4) or point to your own files.

To run the HTTPS server (and automatically attempt trial mode when not activated):

```bash
python app/main.py --cert-file app/cert.pem --priv-file app/privkey.pem
```

CLI operations:

- Activate with a product key
  ```bash
  python app/main.py --activate=AAAA-BBBB-CCCC-DDDD-EEEE-FFFF-GGGG
  ```
- Deactivate the current installation
  ```bash
  python app/main.py --deactivate
  ```

If no `--cert-file/--priv-file` arguments are provided, the app falls back to the certificates bundled next to the executable (e.g., inside `app/`).

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
6. **Build using Nuitka** (run inside the virtual environment). Ensure `app/TurboActivate.dat` and the OS-specific TurboActivate library exist before running this command:
   ```bash
   python -m nuitka app/main.py \
     --onefile \
     --standalone \
     --include-package=fastapi \
     --include-package=uvicorn \
     --include-package=anyio \
     --include-package=starlette \
     --include-data-file=app/TurboActivate.dat=TurboActivate.dat \
     --include-data-file=app/libTurboActivate.so=libTurboActivate.so \
     --output-filename=fadi-service
   ```
   Replace `libTurboActivate.so` with `libTurboActivate.dylib` on macOS or `TurboActivate.dll` on Windows.
7. **Run the generated binary**
   ```bash
   ./fadi-service --cert-file /path/to/cert.pem --priv-file /path/to/privkey.pem
   ```

Visit `https://127.0.0.1:8443/health` to see:

```json
{"serverReady": true}
```
