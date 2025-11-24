import base64

import requests

# REPLACE THIS with the URL provided by 'modal deploy app.py'
API_URL = "https://bernatsampera--deepseek-ocr-server-ocrmodel-generate.modal.run"


def run_remote_ocr(image_path):
    print(f"Encoding image: {image_path}...")

    # 1. Encode local image to Base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    payload = {
        "image": base64_image,
        "prompt": "<image>\nFree OCR.",  # Optional, defaults are handled in server
    }

    print("Sending request to Modal...")
    try:
        # 2. Send POST request
        response = requests.post(API_URL, json=payload, timeout=600)
        response.raise_for_status()

        # 3. Print Result
        result = response.json()
        if "text" in result:
            print("\n--- OCR Result ---\n")
            print(result["text"])
            print("\n------------------")
        else:
            print("Error from server:", result)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(e.response.text)


if __name__ == "__main__":
    # Usage: python trigger.py path/to/image.png

    path = "/Users/bsampera/Documents/test/playground/Stundenplan-Muc.png"
    run_remote_ocr(path)
