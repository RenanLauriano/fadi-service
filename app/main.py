from fastapi import FastAPI
import uvicorn
from pathlib import Path
import sys

app = FastAPI()


@app.get("/health")
def read_health():
    return {"serverReady": True}


def get_cert_paths() -> tuple[str, str]:
    module_dir = Path(__file__).resolve().parent

    certfile = module_dir / "cert.pem"
    keyfile = module_dir / "privkey.pem"

    if not certfile.is_file() or not keyfile.is_file():
        print("ERROR: SSL certificate files not found.", file=sys.stderr)
        print(f"  Expected: {certfile}", file=sys.stderr)
        print(f"  Expected: {keyfile}", file=sys.stderr)
        sys.exit(1)

    return str(certfile), str(keyfile)


def main():
    print("Starting FastAPI HTTPS server...")

    certfile, keyfile = get_cert_paths()
    print(f"Using certfile={certfile}")
    print(f"Using keyfile={keyfile}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8443,
        ssl_certfile=certfile,
        ssl_keyfile=keyfile,
    )


if __name__ == "__main__":
    main()
