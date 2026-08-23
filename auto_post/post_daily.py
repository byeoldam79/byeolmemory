"""
무브카운터 30일 인스타그램 매일 자동 포스팅 메인 프로그램
- 매일 19:00 KST Windows 작업 스케줄러에 의해 자동 실행됩니다.
- ImgBB에 영구 호스팅된 9종의 AI 피트니스 이미지와 30일 콘텐츠 플랜을 바탕으로 업로드합니다.
- 인스타그램 Graph API v23.0 규격에 맞춰 포스팅 후 Google Calendar에 결과를 자동 등록합니다.
"""
import json
import os
import sys
import time
import requests
from datetime import datetime, date
import pytz

# 콘솔 UTF-8 한글 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 기본 경로 및 타임존 설정
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
KST = pytz.timezone('Asia/Seoul')

ENV_FILE     = os.path.join(ROOT_DIR, ".env")
CONTENT_FILE = os.path.join(BASE_DIR, "content_plan.json")
LOG_FILE     = os.path.join(BASE_DIR, "post_log.json")
CRED_FILE    = os.path.join(BASE_DIR, "credentials", "google_calendar.json")
TOKEN_FILE   = os.path.join(BASE_DIR, "credentials", "token.json")

# ==========================================
# 환경 변수 로드 함수
# ==========================================
def load_env():
    """ .env 파일에서 설정값을 직접 읽어옵니다. """
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
ACCOUNT_ID   = config.get("INSTAGRAM_ACCOUNT_ID", "37693295306982418")
ACCESS_TOKEN = config.get("INSTAGRAM_ACCESS_TOKEN", "")
CALENDAR_ID  = config.get("GOOGLE_CALENDAR_ID", "primary")

# ==========================================
# ImgBB 영구 호스팅 이미지 URL 맵 (9종)
# ==========================================
IMAGE_URLS = {
    "squat":     "https://i.ibb.co/PGY2ChSQ/movecounter-squat.jpg",
    "pushup":    "https://i.ibb.co/ZRs65tVb/movecounter-pushup.jpg",
    "plank":     "https://i.ibb.co/NHvg6Ws/movecounter-plank.jpg",
    "lunge":     "https://i.ibb.co/r2R60mCp/movecounter-lunge.jpg",
    "morning":   "https://i.ibb.co/DDDxcNrf/movecounter-morning.jpg",
    "hiit":      "https://i.ibb.co/mrqf0qRB/movecounter-hiit.jpg",
    "core":      "https://i.ibb.co/LhPSxNCn/movecounter-core.jpg",
    "transform": "https://i.ibb.co/4wNHXyVL/movecounter-transform.jpg",
    "homegym":   "https://i.ibb.co/35sXNR2q/movecounter-homegym.jpg",
}


# ==========================================
# 포스팅 로그 관리 함수
# ==========================================
def load_log() -> dict:
    """ 이미 포스팅된 기록(post_log.json)을 읽어와 중복 발행을 방지합니다. """
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_log(log_data: dict):
    """ 포스팅 성공 기록을 post_log.json 파일에 저장합니다. """
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


# ==========================================
# 일차별 콘텐츠 플랜 로드 함수
# ==========================================
def get_today_content(day_number: int) -> dict:
    """ content_plan.json에서 일차에 해당하는 테마, 캡션, 해시태그를 반환합니다. """
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        plan = json.load(f)
    idx = (day_number - 1) % len(plan)
    return plan[idx]


# ==========================================
# 인스타그램 포스팅 함수 (2단계 공식 규격)
# ==========================================
def post_to_instagram(image_url: str, caption: str, hashtags: str) -> str | None:
    """
    Instagram Graph API v23.0을 이용해 이미지를 업로드하고 post_id를 반환합니다.
    1. 미디어 컨테이너 생성 (POST /{account_id}/media)
    2. 서버 처리 대기 (30초)
    3. 피드에 최종 발행 (POST /{account_id}/media_publish)
    """
    base_url = f"https://graph.instagram.com/v23.0/{ACCOUNT_ID}"
    full_caption = f"{caption}\n\n{hashtags}"

    print(f"\n[1/3] Instagram 미디어 컨테이너 생성 중...")
    print(f"  - 이미지 URL: {image_url}")
    
    create_res = requests.post(
        f"{base_url}/media",
        data={
            "image_url": image_url,
            "caption": full_caption,
            "access_token": ACCESS_TOKEN
        },
        timeout=30
    )
    create_data = create_res.json()
    creation_id = create_data.get("id")
    
    if not creation_id:
        print(f"❌ [오류] 컨테이너 생성 실패: {create_data}")
        return None
    print(f"  -> 컨테이너 ID 발급 완료: {creation_id}")

    print(f"[2/3] Instagram 서버 처리 대기 중 (30초)...")
    for sec in range(30, 0, -10):
        print(f"  ⏳ {sec}초 남음...")
        time.sleep(10)

    print(f"[3/3] 피드에 최종 발행 요청 중...")
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
        print(f"🎉 [성공] 인스타그램 포스팅 완료! (포스트 ID: {post_id})")
    else:
        print(f"❌ [오류] 최종 발행 실패: {publish_data}")
        
    return post_id


# ==========================================
# Google Calendar 완료 일정 등록 함수
# ==========================================
def add_to_google_calendar(day_number: int, theme: str, post_id: str, image_url: str):
    """
    Google Calendar API를 통해 포스팅 완료 결과를 일정으로 기록합니다.
    """
    if not os.path.exists(CRED_FILE):
        print("ℹ️ [Calendar] credentials/google_calendar.json 설정 파일이 없어 캘린더 등록을 건너뜁니다.")
        return

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CRED_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w', encoding='utf-8') as t:
                t.write(creds.to_json())

        service = build('calendar', 'v3', credentials=creds)
        now_kst = datetime.now(KST)

        event = {
            'summary': f'🏋️ [MoveCounter] Day {day_number} 포스팅 완료 ({theme})',
            'description': (
                f'■ 테마: {theme}\n'
                f'■ 포스트 ID: {post_id}\n'
                f'■ 사용된 이미지: {image_url}\n'
                f'■ 인스타그램: https://www.instagram.com/bdai_79/\n'
                f'■ 업로드 시각: {now_kst.strftime("%Y-%m-%d %H:%M:%S KST")}'
            ),
            'start': {
                'dateTime': now_kst.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': now_kst.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
        }
        created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"📅 [Google Calendar] 일정 등록 완료: {created.get('summary')}")
        print(f"  링크: {created.get('htmlLink')}")

    except Exception as e:
        print(f"⚠️ [Google Calendar] 일정 등록 중 오류 발생 (포스팅은 정상 완료됨): {e}")


# ==========================================
# 메인 실행 엔트리포인트
# ==========================================
def main():
    print("=" * 60)
    print("🚀 MoveCounter 30일 인스타그램 자동 포스팅 시스템 가동")
    print(f"⏰ 현재 시각 : {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 60)

    # 30일 기준 시작일 설정 (2026-08-24 기준)
    START_DATE = date(2026, 8, 24)
    today = date.today()
    day_number = (today - START_DATE).days + 1

    # 시작일 이전이거나 테스트 시 기본 1일차로 보정
    if day_number < 1:
        day_number = 1
    elif day_number > 30:
        day_number = ((day_number - 1) % 30) + 1

    print(f"📌 오늘 일정: Day {day_number} / 30")

    # 오늘 이미 포스팅을 완료했는지 중복 검사
    log = load_log()
    today_str = today.isoformat()
    if today_str in log:
        prev_post = log[today_str]
        print(f"ℹ️ [중복 방지] 오늘({today_str})은 이미 포스팅을 마쳤습니다.")
        print(f"   포스트 ID : {prev_post.get('post_id')}")
        print(f"   테마      : {prev_post.get('theme')}")
        return

    # 오늘자 콘텐츠 및 이미지 URL 로드
    content = get_today_content(day_number)
    image_key = content.get("image_key", "squat")
    image_url = IMAGE_URLS.get(image_key, IMAGE_URLS["squat"])

    print(f"📖 오늘의 테마   : {content['theme']}")
    print(f"🖼️ 선택된 이미지 : {image_key} ({image_url})")

    # 토큰 유효성 검사
    if not ACCESS_TOKEN:
        print("❌ [오류] INSTAGRAM_ACCESS_TOKEN이 .env에 설정되지 않았습니다!")
        return

    # 1. Instagram 포스팅 실행
    post_id = post_to_instagram(
        image_url=image_url,
        caption=content['caption'],
        hashtags=content['hashtags']
    )

    if not post_id:
        print("❌ [실패] 포스팅 작업이 중단되었습니다.")
        return

    # 2. 실행 로그 저장 (중복 방지용)
    log[today_str] = {
        "day": day_number,
        "theme": content['theme'],
        "post_id": post_id,
        "image_url": image_url,
        "posted_at": datetime.now(KST).isoformat()
    }
    save_log(log)
    print(f"💾 [기록] post_log.json에 포스팅 이력 저장 완료")

    # 3. Google Calendar 연동 기록
    add_to_google_calendar(
        day_number=day_number,
        theme=content['theme'],
        post_id=post_id,
        image_url=image_url
    )

    print("\n" + "=" * 60)
    print(f"✨ [최종 완료] Day {day_number} 인스타그램 자동 포스팅 및 캘린더 기록 성공!")
    print(f"   포스트 ID : {post_id}")
    print(f"   테마      : {content['theme']}")
    print(f"   인스타 확인: https://www.instagram.com/bdai_79/")
    print("=" * 60)


if __name__ == "__main__":
    main()
