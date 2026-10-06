import requests
from config import GROQ_API_KEY

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}"
}

res = requests.get(
    "https://api.groq.com/openai/v1/models",
    headers=headers
)

print("상태 코드:", res.status_code)

data = res.json()

if "data" in data:
    print("\n사용 가능한 모델 목록:\n")

    for model in data["data"]:
        print(model["id"])
else:
    print(data)