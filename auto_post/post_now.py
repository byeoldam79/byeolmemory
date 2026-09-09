"""
새로 제작된 찐따 남성 모델 + 실제 무브카운터 앱 화면 합성 시안 1번을
ImgBB에 업로드하고 인스타그램에 최종 포스팅하는 스크립트입니다.
"""
import os
import sys
import base64
import requests
import json
from datetime import datetime, date
import pytz

# 콘솔 UTF-8 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"e:\아린인스타에이전트"
ENV_FILE = os.path.join(BASE_DIR, ".env")
LOG_FILE = os.path.join(BASE_DIR, "auto_post", "post_log.json")
LOCAL_IMAGE_PATH = r"C:\Users\jw-notebook\.gemini\antigravity-ide\brain\b5d9a4bf-54b4-4b66-b334-f29eb42056b8\jjinda_movecounter_card_v1.jpg"

KST = pytz.timezone('Asia/Seoul')

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
ACCOUNT_ID = config.get("INSTAGRAM_ACCOUNT_ID")
ACCESS_TOKEN = config.get("INSTAGRAM_ACCESS_TOKEN")
IMGBB_API_KEY = config.get("IMGBB_API_KEY")

def upload_to_imgbb(image_path: str) -> str | None:
    print(f"📤 [1/3] ImgBB에 시안 1 이미지 업로드 중... ({image_path})")
    
    with open(image_path, "rb") as file:
        img_base64 = base64.b64encode(file.read()).decode("utf-8")

    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": IMGBB_API_KEY,
        "image": img_base64,
        "name": "movecounter_jjinda_real_app_day6"
    }

    response = requests.post(url, data=payload, timeout=30)
    data = response.json()

    if response.status_code == 200 and data.get("success"):
        image_url = data["data"]["url"]
        print(f"✅ ImgBB 업로드 성공! URL: {image_url}")
        return image_url
    else:
        print(f"❌ ImgBB 업로드 실패: {data}")
        return None

def post_to_instagram(image_url: str, caption: str) -> str | None:
    base_url = f"https://graph.instagram.com/v23.0/{ACCOUNT_ID}"
    
    print("📤 [2/3] 인스타그램 미디어 컨테이너 생성 중...")
    create_res = requests.post(
        f"{base_url}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN
        },
        timeout=30
    )
    create_data = create_res.json()
    creation_id = create_data.get("id")
    
    if not creation_id:
        print(f"❌ 컨테이너 생성 실패: {create_data}")
        return None
    print(f"✅ 컨테이너 생성 완료 (ID: {creation_id})")
    
    print("⏳ 인스타그램 서버 미디어 처리 대기 중 (30초)...")
    import time
    for sec in range(30, 0, -10):
        print(f"   {sec}초 남음...")
        time.sleep(10)
        
    print("🚀 [3/3] 인스타그램 피드에 최종 발행 요청 중...")
    publish_res = requests.post(
        f"{base_url}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN
        },
        timeout=30
    )
    publish_data = publish_res.json()
    post_id = publish_data.get("id")
    
    if post_id:
        print(f"🎉 인스타그램 포스팅 성공! (포스트 ID: {post_id})")
        return post_id
    else:
        print(f"❌ 인스타그램 피드 발행 실패: {publish_data}")
        return None

def update_post_log(post_id: str, image_url: str, theme: str):
    today_str = date.today().isoformat()
    log = {}
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log = json.load(f)
        except Exception:
            log = {}
            
    log[today_str] = {
        "day": 6,
        "theme": theme,
        "post_id": post_id,
        "image_count": 1,
        "image_urls": [image_url],
        "posted_at": datetime.now(KST).isoformat()
    }
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"💾 post_log.json 저장 완료")

def main():
    caption = (
        "\"내일부터 한다던 그 방구석 찐따... 드디어 1일차 시작했다!\" 🤣🔥\n\n"
        "혼자 운동하면 3개 하고 10개 했다고 우기던 시절은 끝 👋\n"
        "스마트폰 카메라만 켜두면 AI가 알아서 횟수랑 자세를 100% 온디바이스로 정확하게 카운팅해 줍니다! 🤖📱\n\n"
        "스쿼트 · 푸쉬업 · 크런치 · 런지 · 점핑잭까지!\n"
        "방구석에서도 PT 받는 것처럼 완벽하게 갓생 시작하자 💪\n\n"
        "👉 지금 바로 프로필 링크에서 무브카운터 무료 체험해보세요!\n\n"
        "#무브카운터 #MoveCounter #AI운동 #오운완 #홈트 #헬린이 #방구석운동 #푸시업 #갓생살기 #운동어플 #AI피트니스 #모션인식 #홈트레이닝"
    )
    theme = "방구석 찐따의 무브카운터 1일차 시작 컨셉 홍보 (실제 앱 화면 결합)"

    image_url = upload_to_imgbb(LOCAL_IMAGE_PATH)
    if not image_url:
        print("작업을 중단합니다.")
        return

    post_id = post_to_instagram(image_url, caption)
    if not post_id:
        print("포스팅에 실패했습니다.")
        return

    update_post_log(post_id, image_url, theme)
    print("=" * 50)
    print(f"✨ 모든 작업이 완료되었습니다! (Post ID: {post_id})")
    print("인스타그램 확인: https://www.instagram.com/bdai_79/")
    print("=" * 50)

if __name__ == "__main__":
    main()
