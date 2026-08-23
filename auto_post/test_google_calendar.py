"""
Google Calendar 최초 1회 인증 및 토큰 발급 스크립트
"""
import os
import sys
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRED_DIR = os.path.join(BASE_DIR, "credentials")
CRED_FILE = os.path.join(CRED_DIR, "google_calendar.json")
TOKEN_FILE = os.path.join(CRED_DIR, "token.json")

SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    print("=" * 60)
    print("Google Calendar 인증 시작")
    print("=" * 60)

    if not os.path.exists(CRED_FILE):
        print(f"❌ 설정 파일이 없습니다: {CRED_FILE}")
        return

    flow = InstalledAppFlow.from_client_secrets_file(
        CRED_FILE,
        scopes=SCOPES
    )

    print("\n👉 브라우저를 열고 있습니다...")
    creds = flow.run_local_server(port=0, open_browser=True, prompt='consent', access_type='offline')

    # 토큰 저장
    with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
        token.write(creds.to_json())
    print(f"\n🎉 [성공] 인증 완료! token.json 저장됨: {TOKEN_FILE}")

    # 캘린더 확인
    service = build('calendar', 'v3', credentials=creds)
    cals = service.calendarList().list().execute()
    print("\n📅 연동된 캘린더 목록:")
    for c in cals.get('items', []):
        print(f"  - {c.get('summary')}")

if __name__ == "__main__":
    main()
