# -*- coding: utf-8 -*-
"""
자동 게시가 왜 안 올라가는지 진단한다. **아무것도 게시하지 않는다.** (읽기 전용)

  python diagnose.py
"""
import json
import os
import sys
from datetime import datetime

import requests
import pytz

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
KST = pytz.timezone("Asia/Seoul")
ENV_FILE = os.path.join(ROOT_DIR, ".env")
CONTENT_FILE = os.path.join(BASE_DIR, "content_plan.json")
LOG_FILE = os.path.join(BASE_DIR, "post_log.json")


def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


cfg = load_env()
ACCOUNT_ID = cfg.get("INSTAGRAM_ACCOUNT_ID", "")
TOKEN = cfg.get("INSTAGRAM_ACCESS_TOKEN", "")

print("=" * 60)
print("인스타 자동 게시 진단 (읽기 전용 — 아무것도 올리지 않습니다)")
print(f"현재 시각: {datetime.now(KST).strftime('%Y-%m-%d %H:%M KST')}")
print("=" * 60)

# 1) 열쇠
print("\n[1] 설정")
print(f"  계정 ID : {ACCOUNT_ID or '(없음)'}")
print(f"  토큰    : {'있음 (%d자)' % len(TOKEN) if TOKEN else '(없음)'}")
if not TOKEN or not ACCOUNT_ID:
    print("  ❌ 열쇠가 없습니다. 여기서 멈춥니다.")
    sys.exit(1)

# 2) 토큰이 살아 있는가
print("\n[2] 토큰 확인")
r = requests.get("https://graph.instagram.com/v23.0/me",
                 params={"fields": "id,username,account_type", "access_token": TOKEN}, timeout=20)
if r.status_code == 200:
    me = r.json()
    print(f"  ✅ 살아 있음 — @{me.get('username')} ({me.get('account_type')}, id {me.get('id')})")
else:
    err = r.json().get("error", {})
    print(f"  ❌ 토큰 문제 — {err.get('message', r.text)[:200]}")
    print(f"     코드 {err.get('code')} / 종류 {err.get('type')}")
    print("     → 토큰 만료입니다. 새로 발급받아 .env 를 고쳐야 합니다.")
    sys.exit(2)

# 3) 실제 피드
print("\n[3] 인스타 실제 피드")
r = requests.get(f"https://graph.instagram.com/v23.0/{ACCOUNT_ID}/media",
                 params={"fields": "id,caption,timestamp", "limit": "50", "access_token": TOKEN}, timeout=20)
live = []
if r.status_code == 200:
    items = r.json().get("data", [])
    live = [i.get("caption", "") for i in items if i.get("caption")]
    print(f"  게시물 {len(items)}개 조회됨")
    for i in items[:5]:
        first = (i.get("caption", "") or "").split("\n")[0][:40]
        print(f"    · {i.get('timestamp','')[:10]}  {first}")
else:
    print(f"  ⚠️ 피드 조회 실패 — {r.text[:200]}")

# 4) 로컬 기록
print("\n[4] 로컬 발행 기록")
log = json.load(open(LOG_FILE, encoding="utf-8")) if os.path.exists(LOG_FILE) else {}
print(f"  기록 {len(log)}건 · 마지막 {max(log) if log else '(없음)'}")
today = datetime.now(KST).strftime("%Y-%m-%d")
if today in log:
    print(f"  ℹ️ 오늘({today})은 이미 발행 기록이 있어 프로그램이 그냥 종료됩니다.")

# 5) 다음에 올라갈 글
print("\n[5] 다음에 올라갈 글 판정")
plans = json.load(open(CONTENT_FILE, encoding="utf-8"))
posted_themes = {v["theme"].strip() for v in log.values() if isinstance(v, dict) and "theme" in v}
posted_days = {v["day"] for v in log.values() if isinstance(v, dict) and "day" in v}

chosen = None
for p in plans:
    theme = (p.get("theme") or "").strip()
    first = (p.get("caption") or "").split("\n")[0].strip()
    in_log = theme in posted_themes or p.get("day") in posted_days
    in_feed = any((theme and theme in c) or (first and first in c) for c in live)
    if not in_log and not in_feed:
        chosen = p
        print(f"  🎯 Day {p.get('day')} — {theme}")
        break
    why = " / ".join(x for x in ["로컬기록" if in_log else "", "실제피드" if in_feed else ""] if x)
    print(f"  건너뜀 Day {p.get('day')} ({theme}) — {why}")

if not chosen:
    print("\n  ❗ 올릴 글이 없습니다. 30일치가 전부 '이미 올라간 것'으로 판정됐습니다.")
    print("     → 새 글을 content_plan.json 에 추가해야 다시 돌아갑니다.")

print("\n" + "=" * 60)
