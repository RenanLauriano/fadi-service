import argparse
import sys
from pathlib import Path

from fastapi import FastAPI
import uvicorn
from turboactivate import (
    TurboActivate,
    IsGenuineResult,
    TurboActivateError,
    TurboActivateTrialExpiredError,
    TA_USER, TA_SYSTEM
)

app = FastAPI()


def runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


@app.get("/health")
def read_health():
    return {"serverReady": True}


def get_cert_paths(cert_override: str | None, key_override: str | None) -> tuple[str, str]:
    module_dir = runtime_dir()

    certfile = Path(cert_override) if cert_override else module_dir / "cert.pem"
    keyfile = Path(key_override) if key_override else module_dir / "privkey.pem"

    if not certfile.is_file() or not keyfile.is_file():
        print("ERROR: SSL certificate files not found.", file=sys.stderr)
        print(f"  Expected: {certfile}", file=sys.stderr)
        print(f"  Expected: {keyfile}", file=sys.stderr)
        sys.exit(1)

    return str(certfile), str(keyfile)


def get_turboactivate_paths() -> tuple[str, str]:
    module_dir = runtime_dir()
    dat_path = module_dir / "TurboActivate.dat"
    if not dat_path.is_file():
        sys.exit(f"TurboActivate.dat not found at {dat_path}")

    lib_name = "TurboActivate.dll"
    if sys.platform == "darwin":
        lib_name = "libTurboActivate.dylib"
    elif sys.platform not in ("win32", "cygwin"):
        lib_name = "libTurboActivate.so"

    lib_path = module_dir / lib_name
    if not lib_path.is_file():
        sys.exit(f"{lib_name} not found at {lib_path}")

    return str(dat_path), str(module_dir)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TurboActivate-protected FastAPI service")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--activate", metavar="PRODUCT_KEY", help="Activate the product with the provided key")
    group.add_argument("--deactivate", action="store_true", help="Deactivate the current installation")
    parser.add_argument("--cert-file", dest="cert_file", help="Path to SSL certificate (defaults to bundled cert.pem)")
    parser.add_argument("--priv-file", dest="priv_file", help="Path to SSL private key (defaults to bundled privkey.pem)")
    return parser


def activate_product_key(ta: TurboActivate, product_key: str) -> None:
    try:
        if ta.check_and_save_pkey(product_key):
            print("Product key saved successfully.")
        else:
            sys.exit("Product key was not valid for this product version")

        ta.activate()
        print("Activated successfully!")
    except TurboActivateError as e:
        sys.exit("Failed to activate product key: " + str(e))


def deactivate_product_key(ta: TurboActivate) -> None:
    try:
        print("Deactivating...")
        ta.deactivate(True)
        print("Deactivated successfully.")
    except TurboActivateError as e:
        sys.exit("Failed to deactivate product key: " + str(e))


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    DAYS_BETWEEN_CHECKS = 90
    GRACE_PERIOD_LENGTH = 14
    trial_days = 0
    verified_trial = True

    # now begins the licensing bit of the code
    isGenuine = False

    ta_dat_path, ta_library_folder = get_turboactivate_paths()

    try:
        ta = TurboActivate("kqleto2xmx3cyolhetce7dz6tju3txa", TA_USER, ta_dat_path, ta_library_folder)
        #=============

        if args.activate:
            activate_product_key(ta, args.activate)
            return

        if args.deactivate:
            deactivate_product_key(ta)
            return

            # try to activate the product key
        try:
            ta.activate()
            isGenuine = True
        except TurboActivateError as e:
            print("Product not activated, trying trial...")

        if not isGenuine:
            try:
                # Start or re-validate the trial if it has already started.
                # This need to be called at least once before you can use
                # any other trial functions.
                ta.use_trial(verified_trial)

                # Get the number of trial days remaining.
                trial_days = ta.trial_days_remaining(verified_trial)

                if trial_days > 0:
                    print("Trial days remaining %d" % trial_days)
                else:
                    print("There are no trial days remaining. You must activate now to continue to use this app.")
            except TurboActivateTrialExpiredError as e:
                sys.exit("There are no trial days remaining. You must activate now to continue to use this app.")
            except TurboActivateError as e:
                sys.exit("Failed to start the trial: " + str(e))

        #==================

        # Check if we're activated, and every 90 days verify it with the activation servers
        # In this example we won't show an error if the activation was done offline
        # (see the 3rd parameter of the IsGenuine() function)
        # https://wyday.com/limelm/help/offline-activation/
        gen_r = ta.is_genuine_ex(DAYS_BETWEEN_CHECKS, GRACE_PERIOD_LENGTH, True)

        isGenuine = (gen_r == IsGenuineResult.Genuine
                     or gen_r == IsGenuineResult.GenuineFeaturesChanged

                     # an internet error means the user is activated but
                     # TurboActivate failed to contact the LimeLM servers
                     or gen_r == IsGenuineResult.InternetError
                     )

        if not isGenuine and ta.is_activated():

            # There is still activation data on the computer, and it's valid.

            # This means that IsGenuineEx() is saying "not activated" (a.k.a. TA_FAIL)
            # because the customer blocked connections to the activation servers (intentionally or not)
            # for nDaysBetweenChecks + nGraceDaysOnInetErr days.

            # What you should do now is prompt the user telling them before they can use your app that they need
            # to reverify with the activation servers.

            print('You must reverify with the activation servers before you can use this app. ')
            print('Type R and then press enter to retry after you\'ve ensured that you\'re connected to the internet. ')
            print('Or to exit the app press X. ')

            while True:
                user_resp = sys.stdin.read(1)

                if user_resp == 'x' or user_resp == 'X':
                    sys.exit("Exiting now. Bye.")

                if user_resp == 'r' or user_resp == 'R':
                    # Now we're using TA_IsGenuine() to retry immediately. Note that we're not using
                    # TA_IsGenuineEx() because TA_IsGenuineEx() waits 5 hours after an internet failure
                    # before retrying to contact the servers. TA_IsGenuine() retries immediately.
                    igr = ta.is_genuine()

                    if igr == IsGenuineResult.Genuine or igr == IsGenuineResult.GenuineFeaturesChanged:
                        print('Successfully reverified with the servers! You can now continue to use the app!')
                        break
                    else:
                        print('Failed to reverify with the servers. ')
                        print('Make sure you\'re connected to the internet and that you\'re not blocking access to the activation servers. ')
                        print('Then press R to retry again. ')
                else:
                    print('Invalid input. Press R to try to reverify with the servers. Press X to exit the app.')
        print("Activation verified.")
    except TurboActivateError as e:
        sys.exit("Failed to check if activated: " + str(e))

    print("Starting FastAPI HTTPS server...")

    certfile, keyfile = get_cert_paths(args.cert_file, args.priv_file)
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
