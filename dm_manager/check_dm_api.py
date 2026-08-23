"""
Instagram Graph API DM 대화방 및 메시지 조회 테스트 스크립트
"""
import os
import sys
import requests
import json

sys.stdout.reconfigure(encoding='utf-8')

# .env 파일에서 계정 정보 로드
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT_DIR, ".env")

def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

config = load_env()
ACCOUNT_ID = config.get("INSTAGRAM_ACCOUNT_ID", "37693295306982418")
ACCESS_TOKEN = config.get("INSTAGRAM_ACCESS_TOKEN", "")

print("=" * 60)
print("📥 Instagram DM 대화방 조회 테스트")
print("=" * 60)

url = f"https://graph.instagram.com/v23.0/{ACCOUNT_ID}/conversations"
params = {
    "fields": "id,updated_time,participants,messages{id,text,created_time,from}",
    "access_token": ACCESS_TOKEN
}

res = requests.get(url, params=params)
data = res.json()

if "error" in data:
    err = data["error"]
    print(f"❌ [API 응답 에러] {err.get('message')}")
    print(f"   에러 코드: {err.get('code')} (Subcode: {err.get('error_subcode')})")
    print(f"   타입: {err.get('type')}")
else:
    print(f"✅ [조회 성공] 대화방 목록:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
