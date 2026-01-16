# test_upload.py
import requests
files = {'image': open('test_img.png','rb')}   # put a small test_img.png in project root
try:
    r = requests.post('http://127.0.0.1:5000/predict_image', files=files, timeout=30)
    print("Status:", r.status_code)
    try:
        print(r.json())
    except Exception:
        print("Raw response:", r.text[:1000])
except Exception as e:
    print("Request error:", e)
