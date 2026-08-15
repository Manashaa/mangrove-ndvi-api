import requests

url = "http://127.0.0.1:8000/ndvi/P0001"

headers = {
    "X-API-Key": "R26-NDVI-TEST-2026"
}

response = requests.get(url, headers=headers)

print(response.json())