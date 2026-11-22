import time
import RNS
import LXMF
import os
import requests
from datetime import datetime
import subprocess

def delivery_callback(message):
    print("\n--- New LXMF Message Received ---")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sender_hash = RNS.prettyhexrep(message.source_hash)
    print(f"From (Sender Hash): {sender_hash}")

    # Extract timestamps and content
    print(f"Sent at           : {time.ctime(message.timestamp)}")
    print(f"Title/Subject     : {message.title}")
    content = message.content.decode('utf-8')
    print(f"Content           : {content}")

    # Extract generic file attachments
    if LXMF.FIELD_FILE_ATTACHMENTS in message.fields:
        for attachment in message.fields[LXMF.FIELD_FILE_ATTACHMENTS]:
            filename, file_bytes = attachment[0], attachment[1]
            # Sanitize filename before saving to disk
            safe_name = os.path.basename(filename)
            with open(f"./downloads/{safe_name}", "wb") as f:
                f.write(file_bytes)

    # Extract inline image
    if LXMF.FIELD_IMAGE in message.fields:
        img_ext, img_bytes = message.fields[LXMF.FIELD_IMAGE]
        with open(f"./downloads/received_image-{timestamp}.{img_ext}", "wb") as f:
            f.write(img_bytes)

    # Extract audio clip
    if LXMF.FIELD_AUDIO in message.fields:
        audio_mode, audio_bytes = message.fields[LXMF.FIELD_AUDIO]
        soundf = f"./downloads/received_audio-{timestamp}.bin"
        with open(f"./downloads/received_audio-{timestamp}.bin", "wb") as f:
            f.write(audio_bytes)
    # Uncomment below to auto-play received audio "notes"/files using vlc cli
  # result = subprocess.run(["cvlc", f"{soundf}", "vlc://quit"], capture_output=False, text=False, check=False)

    print("---------------------------------\n")

def main():
    reticulum = RNS.Reticulum(require_shared_instance=False)
    router = LXMF.LXMRouter(storagepath="./lxmf_storage")
    os.makedirs("./identities", exist_ok=True)
    KEY_PATH = "./identities/identity.LXMF"
    os.makedirs("./downloads", exist_ok=True)

    if os.path.exists(KEY_PATH):
        my_identity = RNS.Identity.from_file(KEY_PATH)
        print("Loaded existing identity.")
    else:
        my_identity = RNS.Identity()
        my_identity.to_file(KEY_PATH)
        print("Created and saved a new identity.")

    my_lxmf_destination = router.register_delivery_identity(
        my_identity,
        display_name="LXMF Receiver - Receive Only"
    )

    router.register_delivery_callback(delivery_callback)
    my_lxmf_destination.announce()

    my_address_hex = RNS.prettyhexrep(my_lxmf_destination.hash)
    print(f"[+] LXMF Receiver Ready.")
    print(f"[+] Your LXMF Address is: {my_address_hex}")
    print("[+] Listening for incoming messages... (Press Ctrl+C to exit)")
    ainterval = 600
    try:
        ai = 0
        while True:
            time.sleep(1)
            ai += 1
            if ( ai > ainterval ):
                ai=0
                my_lxmf_destination.announce()
    except KeyboardInterrupt:
        print("\n[-] Shutting down receiver.")

if __name__ == "__main__":
    main()

