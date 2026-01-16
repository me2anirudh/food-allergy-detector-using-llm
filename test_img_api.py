# test_img_api.py
import requests, json, os, sys

url = "http://127.0.0.1:5000/predict_from_image"
image_path = "test_img.png"   # update if different

# basic checks
if not os.path.exists(image_path):
    print("ERROR: image file not found at", image_path)
    sys.exit(1)

with open(image_path, "rb") as f:
    files = {"file": (os.path.basename(image_path), f, "image/png")}
    try:
        r = requests.post(url, files=files, timeout=30)
    except Exception as e:
        print("Request failed:", e)
        sys.exit(1)

print("Status code:", r.status_code)
# Print raw text too (useful when flask returns HTML error)
print("Raw response text:")
print(r.text[:10000])   # print first 10k chars to avoid flooding
try:
    data = r.json()
    print("\nPretty JSON:")
    print(json.dumps(data, indent=2))
except Exception:
    pass
