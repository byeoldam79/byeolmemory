"""
무브카운터 30일 인스타그램 매일 자동 포스팅 메인 프로그램 (완전 중복 방지 버전)
파일명: post_daily.py
설명:
  1. 인스타그램 Graph API를 실시간 호출하여 실제 피드에 올라간 최근 게시글 캡션을 조회합니다.
  2. 로컬 로그(post_log.json)의 역대 발행 기록을 전수 대조합니다.
  3. [인스타그램 실제 피드] + [로컬 로그] 양쪽 모두에 단 한 번도 올라가지 않은 '미발행 콘텐츠'를 1일차부터 순차적으로 찾아 안전하게 발행합니다.
  4. 오늘 이미 글을 올렸거나, 조금이라도 중복된 내용이 발견되면 절대 발행하지 않습니다.
"""
import json
import os
import sys
import time
import requests
from datetime import datetime, date
import pytz

# 콘솔 UTF-8 한글 인코딩 설정 (터미널 및 로그 파일 한글 깨짐 방지)
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 1. 기본 경로 및 한국 표준시(KST) 타임존 설정
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
# 2. 환경 변수 로드 (.env 안전 로더)
# ==========================================
def load_env() -> dict:
    """ .env 파일에서 계정 ID, 토큰, 캘린더 ID를 읽어옵니다. """
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
# 3. ImgBB 영구 호스팅 이미지 URL 맵 (9종)
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
# 4. 로컬 포스팅 로그 관리 함수
# ==========================================
def load_log() -> dict:
    """ post_log.json 파일에서 과거의 모든 포스팅 이력을 불러옵니다. """
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_log(log_data: dict):
    """ 포스팅 성공 기록을 post_log.json 파일에 안전하게 저장합니다. """
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


# ==========================================
# 5. [중복 방지 1단계] 인스타그램 실제 피드 실시간 대조
# ==========================================
def fetch_live_instagram_captions() -> list[str]:
    """
    인스타그램 Graph API를 직접 호출하여 현재 인스타그램 피드에 올라가 있는
    최근 게시물들의 실제 캡션(본문 텍스트) 목록을 가져옵니다.
    """
    if not ACCESS_TOKEN or not ACCOUNT_ID:
        return []
    
    url = f"https://graph.instagram.com/v23.0/{ACCOUNT_ID}/media"
    params = {
        "fields": "id,caption,timestamp",
        "limit": "50",
        "access_token": ACCESS_TOKEN
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            captions = [item.get("caption", "") for item in data.get("data", []) if item.get("caption")]
            return captions
        else:
            print(f"⚠️ [주의] 인스타그램 피드 실시간 조회 실패: {res.text}")
            return []
    except Exception as e:
        print(f"⚠️ [주의] 인스타그램 API 통신 오류: {e}")
        return []


# ==========================================
# 6. [중복 방지 2단계] 100% 미발행 콘텐츠 자동 선별
# ==========================================
def get_next_unposted_content(all_plans: list[dict], log_data: dict, live_captions: list[str]) -> dict | None:
    """
    30일치 콘텐츠 플랜 전체를 1일차부터 순회하며:
    1) post_log.json에 기록된 적이 있는지 확인
    2) 인스타그램 실제 피드의 캡션에 해당 글의 핵심 문장/테마가 이미 존재하는지 확인
    두 조건 모두에서 '단 한 번도 올라간 적 없는' 가장 첫 번째 콘텐츠를 반환합니다.
    """
    # 1. 로컬 로그에서 이미 발행된 테마 및 일차 수집
    posted_themes_in_log = set()
    posted_days_in_log = set()
    for date_key, info in log_data.items():
        if isinstance(info, dict):
            if "theme" in info:
                posted_themes_in_log.add(info["theme"].strip())
            if "day" in info:
                posted_days_in_log.add(info["day"])

    # 2. 1일차부터 30일차까지 순차적으로 미발행 여부 검사
    for plan in all_plans:
        day_num = plan.get("day")
        theme = plan.get("theme", "").strip()
        caption = plan.get("caption", "")
        # 본문의 첫 줄 또는 대표 문구 추출
        first_line = caption.split('\n')[0].strip() if caption else ""

        # 검사 A: 로컬 로그에 테마나 일차가 이미 존재하는가?
        is_in_log = (theme in posted_themes_in_log) or (day_num in posted_days_in_log)

        # 검사 B: 실제 인스타그램 피드 캡션에 이 테마나 첫 줄 문구가 이미 올라가 있는가?
        is_in_live_feed = False
        for live_cap in live_captions:
            if (theme and theme in live_cap) or (first_line and first_line in live_cap):
                is_in_live_feed = True
                break

        # 로컬 로그에도 없고, 실제 인스타그램 피드에도 없다면 -> 오늘 올릴 안전한 콘텐츠로 확정!
        if not is_in_log and not is_in_live_feed:
            print(f"🎯 [선택 완료] 미발행 콘텐츠 발견: Day {day_num} - '{theme}'")
            return plan
        else:
            reason = []
            if is_in_log:
                reason.append("로컬 로그 기록됨")
            if is_in_live_feed:
                reason.append("실제 인스타그램 피드에 이미 존재함")
            print(f"⏭️ [스킵] Day {day_num} ('{theme}') 건너뜀 사유: {', '.join(reason)}")

    # 30일치 모든 콘텐츠가 이미 발행된 경우
    return None


# ==========================================
# 7. 인스타그램 포스팅 함수 (2단계 공식 규격)
# ==========================================
def post_to_instagram(image_url: str, caption: str, hashtags: str) -> str | None:
    """
    Instagram Graph API v23.0 규격에 따라 미디어를 2단계로 발행합니다.
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
# 8. Google Calendar 완료 일정 등록 함수
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
# 9. 메인 실행 엔트리포인트
# ==========================================
def main():
    print("=" * 60)
    print("🚀 MoveCounter 30일 인스타그램 자동 포스팅 시스템 가동 (완전 중복 방지)")
    now_kst = datetime.now(KST)
    today_str = now_kst.strftime('%Y-%m-%d')
    print(f"⏰ 현재 시각 : {now_kst.strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 60)

    # 1. 오늘 날짜 중복 발행 여부 1차 체크
    log = load_log()
    if today_str in log:
        prev_post = log[today_str]
        print(f"ℹ️ [중복 방지 1차 차단] 오늘({today_str})은 이미 포스팅을 마쳤습니다.")
        print(f"   포스트 ID : {prev_post.get('post_id')}")
        print(f"   테마      : {prev_post.get('theme')}")
        print("   -> 하루에 2회 이상 포스팅되지 않도록 안전하게 종료합니다.")
        return

    # 2. 토큰 및 필수 설정값 검증
    if not ACCESS_TOKEN:
        print("❌ [오류] INSTAGRAM_ACCESS_TOKEN이 .env에 설정되지 않았습니다!")
        return

    # 3. 인스타그램 실시간 피드 캡션 목록 조회
    print("\n🔍 [실시간 검증] 인스타그램 최근 피드 게시물 대조 중...")
    live_captions = fetch_live_instagram_captions()
    print(f"  -> 인스타그램 최근 게시글 {len(live_captions)}개 캡션 수집 완료")

    # 4. 30일 콘텐츠 플랜 로드
    if not os.path.exists(CONTENT_FILE):
        print(f"❌ [오류] 콘텐츠 플랜 파일이 없습니다: {CONTENT_FILE}")
        return

    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        all_plans = json.load(f)

    # 5. [핵심] 인스타그램 피드와 로컬 로그를 대조하여 단 한 번도 안 올라간 다음 글 선택
    print("\n📋 [콘텐츠 선별] 미발행 콘텐츠 검색 중...")
    content = get_next_unposted_content(all_plans, log, live_captions)

    if not content:
        print("🎉 [안내] 30일치 모든 콘텐츠가 이미 인스타그램에 성공적으로 발행되었습니다!")
        return

    day_number = content.get("day", 1)
    theme = content.get("theme", "")
    
    # [새로운 기능] content_plan.json에 직접 이미지 URL(image_url)이 등록되어 있다면 우선적으로 사용합니다.
    # 만약 등록되어 있지 않다면, 기존처럼 image_key를 사용해 사전에 선언된 기본 이미지 URL을 가져옵니다.
    image_url = content.get("image_url")
    image_key = None
    if not image_url:
        image_key = content.get("image_key", "squat")
        image_url = IMAGE_URLS.get(image_key, IMAGE_URLS["squat"])
        print(f"🖼️ [기본 이미지 사용] 설정된 이미지 키: {image_key}")
    else:
        print(f"🖼️ [커스텀 이미지 사용] 외부 이미지 URL 적용: {image_url}")

    print("\n" + "-" * 60)
    print(f"📌 [오늘의 확정 콘텐츠] Day {day_number} / 30")
    print(f"📖 오늘의 테마   : {theme}")
    if image_key:
        print(f"🖼️ 선택된 이미지 : {image_key} ({image_url})")
    else:
        print(f"🖼️ 선택된 이미지 : 커스텀 이미지 ({image_url})")
    print("-" * 60)

    # 6. Instagram Graph API 포스팅 실행
    post_id = post_to_instagram(
        image_url=image_url,
        caption=content['caption'],
        hashtags=content['hashtags']
    )

    if not post_id:
        print("❌ [실패] 포스팅 작업이 중단되었습니다.")
        return

    # 7. 실행 로그 저장 (오늘 날짜 키로 안전하게 누적 기록)
    log[today_str] = {
        "day": day_number,
        "theme": theme,
        "post_id": post_id,
        "image_url": image_url,
        "posted_at": datetime.now(KST).isoformat()
    }
    save_log(log)
    print(f"💾 [기록] post_log.json에 포스팅 이력 저장 완료")

    # 8. Google Calendar 연동 기록
    add_to_google_calendar(
        day_number=day_number,
        theme=theme,
        post_id=post_id,
        image_url=image_url
    )

    print("\n" + "=" * 60)
    print(f"✨ [최종 완료] Day {day_number} 인스타그램 자동 포스팅 및 캘린더 기록 성공!")
    print(f"   포스트 ID : {post_id}")
    print(f"   테마      : {theme}")
    print(f"   인스타 확인: https://www.instagram.com/bdai_79/")
    print("=" * 60)


if __name__ == "__main__":
    main()
