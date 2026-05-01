import requests
import json

url = "http://127.0.0.1:5000/fact-check"
data = {
    "statement": "The sky is blue",
    "email": "test@example.com"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
