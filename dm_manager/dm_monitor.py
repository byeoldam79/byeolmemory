"""
인스타그램 AI 스마트 DM 모니터링 & Google Calendar 알림 발송 시스템 (3안 적용)
- 주기적으로 Instagram Graph API를 조회하여 새로운 DM을 확인합니다.
- AI 엔진(DMClassifier)으로 중요 메시지(비즈니스, 버그/피드백, 테스터 신청)를 자동 선별합니다.
- 선별된 중요 DM은 Google Calendar에 즉시 알림 이벤트로 자동 등록되고, important_dms.md 리포트에 기록됩니다.
"""
import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Any
import pytz

# 콘솔 UTF-8 한글 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 기본 경로 및 설정 로드
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
KST = pytz.timezone('Asia/Seoul')

ENV_FILE         = os.path.join(ROOT_DIR, ".env")
HISTORY_FILE     = os.path.join(BASE_DIR, "dm_history.json")
IMPORTANT_JSON   = os.path.join(BASE_DIR, "important_dms.json")
IMPORTANT_MD     = os.path.join(BASE_DIR, "important_dms.md")
CALENDAR_TOKEN   = os.path.join(ROOT_DIR, "auto_post", "credentials", "token.json")

# 분류 엔진 불러오기
from dm_classifier import DMClassifier

def load_env():
    """ .env 파일에서 계정 설정값을 로드합니다. """
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
# 히스토리 및 중요 DM 데이터 관리
# ==========================================
def load_json(filepath: str, default: Any = None):
    """ JSON 파일을 안전하게 읽어옵니다. """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default if default is not None else {}
    return default if default is not None else {}

def save_json(filepath: str, data: Any):
    """ 데이터를 JSON 파일로 안전하게 저장합니다. """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_markdown_report(important_list: list):
    """ 사용자 친화적인 마크다운 요약 리포트(important_dms.md)를 생성합니다. """
    now_str = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')
    
    md_content = f"""# 📬 인스타그램 중요 DM 모니터링 리포트
> **최종 갱신 시각:** {now_str}  
> **모니터링 계정:** @bdai_79 | **총 선별된 중요 DM:** {len(important_list)}건  
> **알림 연동:** 📅 Google Calendar 자동 알림 등록 활성화됨

---

## 📋 선별된 중요 DM 목록

"""
    if not important_list:
        md_content += "현재 새로 접수된 중요 DM이 없습니다. AI가 백그라운드에서 실시간 모니터링 중입니다. ☕\n"
    else:
        for idx, item in enumerate(reversed(important_list), 1):
            category_badge = {
                "BUSINESS": "🔥 [비즈니스/협찬 제안]",
                "FEEDBACK": "💡 [앱 오류/피드백 제보]",
                "TESTER": "🙋 [테스터 참여 신청]",
                "NORMAL": "💬 [일반]"
            }.get(item.get("category"), "📌 [알림]")
            
            md_content += f"""### {idx}. {category_badge} - 발신자: `{item.get('sender_id', 'Unknown')}`
- **수신 시각:** {item.get('received_at')}
- **우선순위:** `{item.get('priority')}`
- **분류 사유:** {item.get('reason')}
- **추출된 이메일:** `{item.get('extracted_email') or '없음'}`
- **캘린더 등록:** {'✅ 등록 완료' if item.get('calendar_event_id') else '미등록'}
- **메시지 원문:**
> {item.get('text')}

---
"""

    with open(IMPORTANT_MD, 'w', encoding='utf-8') as f:
        f.write(md_content)


# ==========================================
# Google Calendar 중요 알림 이벤트 등록 (3안 핵심)
# ==========================================
def add_dm_to_google_calendar(dm_info: dict) -> str | None:
    """
    중요 DM 발생 시 구글 캘린더에 즉시 팝업 알림이 설정된 이벤트를 등록합니다.
    """
    if not os.path.exists(CALENDAR_TOKEN):
        print("ℹ️ [Calendar] token.json이 없어 캘린더 등록을 건너뜁니다.")
        return None

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = Credentials.from_authorized_user_file(CALENDAR_TOKEN, SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        
        now_kst = datetime.now(KST)
        end_kst = now_kst + timedelta(minutes=30)
        
        category_title = {
            "BUSINESS": "🔥 [인스타 중요 DM: 비즈니스/협찬 제안]",
            "FEEDBACK": "💡 [인스타 중요 DM: 앱 오류/피드백 제보]",
            "TESTER": "🙋 [인스타 중요 DM: 테스터 참여 신청]"
        }.get(dm_info.get("category"), "📬 [인스타 중요 DM 알림]")

        sender = dm_info.get("sender_id", "Unknown")
        email_str = f"■ 추출된 이메일: {dm_info.get('extracted_email')}\n" if dm_info.get("extracted_email") else ""

        description = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📬 인스타그램 @bdai_79 로 중요 DM이 도착했습니다!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"■ 발신자: @{sender}\n"
            f"■ 분류 등급: {dm_info.get('priority')} ({dm_info.get('category')})\n"
            f"■ AI 판별 사유: {dm_info.get('reason')}\n"
            f"{email_str}"
            f"■ 수신 시각: {dm_info.get('received_at', now_kst.strftime('%Y-%m-%d %H:%M:%S KST'))}\n\n"
            f"💬 [메시지 원문]\n"
            f"\"{dm_info.get('text')}\"\n\n"
            f"👉 인스타그램 앱에서 직접 확인 및 답장을 보내주세요!"
        )

        event = {
            'summary': f'{category_title} - @{sender}',
            'description': description,
            'start': {
                'dateTime': now_kst.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': end_kst.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            # 캘린더 알림 팝업 강제 설정
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 0},  # 즉시 팝업 알림
                ],
            },
        }
        
        created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        event_id = created.get('id')
        print(f"📅 [Google Calendar] 중요 DM 알림 등록 성공!")
        print(f"  - 제목: {created.get('summary')}")
        print(f"  - 링크: {created.get('htmlLink')}")
        return event_id
        
    except Exception as e:
        print(f"⚠️ [Google Calendar] 일정 등록 중 오류: {e}")
        return None


# ==========================================
# DM 수신 및 분석 메인 실행 함수
# ==========================================
def check_new_dms():
    print("=" * 65)
    print(f"📬 인스타그램 DM 스마트 모니터링 시스템 가동")
    print(f"⏰ 실행 시각: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 65)

    if not ACCESS_TOKEN:
        print("❌ [오류] INSTAGRAM_ACCESS_TOKEN이 .env에 설정되지 않았습니다!")
        return

    classifier = DMClassifier()
    history = load_json(HISTORY_FILE, default={"processed_message_ids": []})
    important_list = load_json(IMPORTANT_JSON, default=[])
    processed_ids = set(history.get("processed_message_ids", []))

    # 1. Instagram Graph API 대화방 조회
    url = f"https://graph.instagram.com/v23.0/{ACCOUNT_ID}/conversations"
    params = {
        "fields": "id,updated_time,participants,messages{id,text,created_time,from}",
        "access_token": ACCESS_TOKEN
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
    except Exception as e:
        print(f"❌ [네트워크 오류] API 요청 실패: {e}")
        return

    if "error" in data:
        print(f"❌ [API 오류] {data['error'].get('message')}")
        return

    conversations = data.get("data", [])
    print(f"📥 현재 활성 대화방 수: {len(conversations)}개")

    new_important_count = 0

    # 2. 각 대화방 순회
    for conv in conversations:
        messages_obj = conv.get("messages", {})
        messages = messages_obj.get("data", [])
        
        for msg in messages:
            msg_id = msg.get("id")
            if not msg_id or msg_id in processed_ids:
                continue  # 이미 처리한 메시지는 스킵

            msg_text = msg.get("text", "")
            sender_info = msg.get("from", {})
            sender_id = sender_info.get("username") or sender_info.get("id", "Unknown")
            
            # 본인 계정이 보낸 메시지는 제외
            if sender_id == ACCOUNT_ID or sender_id == "bdai_79":
                processed_ids.add(msg_id)
                continue

            print(f"\n🔍 [새 메시지 분석] 발신자: @{sender_id}")
            print(f"  - 내용: \"{msg_text}\"")

            # 3. AI 중요도 및 의도 분석
            analysis = classifier.classify(msg_text, sender_name=sender_id)
            
            if analysis["is_important"]:
                new_important_count += 1
                icon = "🔥" if analysis["category"] == "BUSINESS" else ("💡" if analysis["category"] == "FEEDBACK" else "🙋")
                print(f"  {icon} [중요 DM 감지!] 카테고리: {analysis['category']} (우선순위: {analysis['priority']})")
                print(f"     사유: {analysis['reason']}")
                
                dm_record = {
                    "message_id": msg_id,
                    "conversation_id": conv.get("id"),
                    "sender_id": sender_id,
                    "text": msg_text,
                    "category": analysis["category"],
                    "priority": analysis["priority"],
                    "reason": analysis["reason"],
                    "extracted_email": analysis.get("extracted_email"),
                    "received_at": datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST'),
                    "calendar_event_id": None
                }
                
                # 4. Google Calendar 알림 등록 (3안 핵심)
                cal_event_id = add_dm_to_google_calendar(dm_record)
                dm_record["calendar_event_id"] = cal_event_id
                
                important_list.append(dm_record)
            else:
                print(f"  💤 [일반/필터링] {analysis['reason']}")

            # 처리된 ID로 기록
            processed_ids.add(msg_id)

    # 5. 상태 및 리포트 저장
    history["processed_message_ids"] = list(processed_ids)
    history["last_checked_at"] = datetime.now(KST).isoformat()
    save_json(HISTORY_FILE, history)
    save_json(IMPORTANT_JSON, important_list)
    update_markdown_report(important_list)

    print("\n" + "=" * 65)
    print(f"✨ DM 점검 완료! (신규 선별된 중요 DM: {new_important_count}건)")
    print(f"📄 요약 리포트: e:\\아린인스타그램에이전트\\dm_manager\\important_dms.md")
    print("=" * 65)


if __name__ == "__main__":
    check_new_dms()
