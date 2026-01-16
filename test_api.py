import requests

url = "http://127.0.0.1:5000/predict"
payload = {"ingredients_text": "Ingredients: milk powder, sugar, wheat flour, soy lecithin"}

r = requests.post(url, json=payload)
print("Status code:", r.status_code)
print("Raw response text:")
print(r.text)