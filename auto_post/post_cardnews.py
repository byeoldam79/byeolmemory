# -*- coding: utf-8 -*-
"""
정본 카드뉴스(2장)를 인스타에 한 게시물로 올린다. (캐러셀)

  python post_cardnews.py            ← 미리보기 (올리지 않음)
  python post_cardnews.py --go       ← 실제 발행

원본: E:\\무브카운터 관리\\포스터\\무브카운터_카드뉴스_1_모집_최종.html
      E:\\무브카운터 관리\\포스터\\무브카운터_카드뉴스_2_혜택랭킹_최종.html
  → scripts/render_posters.mjs 로 1080x1350 이미지를 뽑고 ImgBB 에 올린 것.
"""
import json
import os
import sys
import time
from datetime import datetime

import requests
import pytz

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
KST = pytz.timezone("Asia/Seoul")
ENV_FILE = os.path.join(ROOT_DIR, ".env")
LOG_FILE = os.path.join(BASE_DIR, "post_log.json")
API = "https://graph.instagram.com/v23.0"

IMAGES = [
    "https://i.ibb.co/8gF187mG/f5fd677081e7.png",   # 1장 · 모집 (2026-09-10 개정)
    "https://i.ibb.co/Xr00Ktd2/6710000628f1.png",   # 2장 · 혜택·랭킹 (2026-09-10 개정)
]

CAPTION = """무브카운터 테스터를 모십니다.

카메라 앞에 서면 AI가 운동 횟수를 자동으로 셉니다.
8종 운동 인식 · 5회마다 격려 멘트 · 참여 무료.

■ 테스터 혜택
14일 앱 유지 + 피드백 작성 → 정식판 스킨 무료
조건을 채우신 분 전원에게 드립니다. (정식 출시 후 유료 판매 예정인 스킨입니다)

■ 랭킹전 2026. 9. 20 – 10. 20
1위 치킨 쿠폰 + 아이스 아메리카노 쿠폰(2잔)
2위 치킨 쿠폰
3위 아이스 아메리카노 쿠폰(2잔)

랭킹은 이벤트 기간 앱 사용 기록으로 집계합니다.
스킨과 랭킹 상품은 중복으로 받으실 수 있습니다.
부정 사용(치팅)이 확인되면 랭킹과 리워드에서 제외됩니다.

모집 인원은 1차 50명, 예비 50명입니다.
안드로이드 · 지메일(@gmail.com) 계정이 필요합니다.

👉 신청은 프로필 링크를 눌러 주세요.
   (직접 입력) srv1948777.hstgr.cloud/apply"""

HASHTAGS = ("#테스터모집 #앱테스터모집 #베타테스터 #클로즈드베타 #홈트 #홈트레이닝 "
            "#맨몸운동 #스쿼트 #플랭크 #운동앱 #AI운동 #무브카운터 #안드로이드앱 "
            "#운동기록 #다이어트")


def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def main():
    go = "--go" in sys.argv
    cfg = load_env()
    acc = cfg.get("INSTAGRAM_ACCOUNT_ID", "")
    tok = cfg.get("INSTAGRAM_ACCESS_TOKEN", "")
    full = f"{CAPTION}\n\n{HASHTAGS}"

    print("=" * 60)
    print("정본 카드뉴스 2장 (캐러셀)")
    print("=" * 60)
    for i, u in enumerate(IMAGES, 1):
        r = requests.head(u, timeout=20)
        print(f"  {i}장: {u}  (HTTP {r.status_code})")
        if r.status_code != 200:
            print("  ❌ 이미지가 열리지 않습니다. 중단합니다.")
            return 1
    print("-" * 60)
    print(full)
    print("-" * 60)
    print(f"글자 수 {len(full)} / 2200")
    if len(full) > 2200:
        print("❌ 캡션 한도 초과")
        return 1

    if not go:
        print("\n※ 미리보기입니다. 아무것도 올라가지 않았습니다. (--go 를 붙이면 발행)")
        return 0

    if not acc or not tok:
        print("❌ .env 에 계정 정보가 없습니다.")
        return 1

    print("\n[1/3] 장별 컨테이너 만들기")
    children = []
    for i, u in enumerate(IMAGES, 1):
        r = requests.post(f"{API}/{acc}/media",
                          data={"image_url": u, "is_carousel_item": "true", "access_token": tok},
                          timeout=60)
        j = r.json()
        if not j.get("id"):
            print(f"  ❌ {i}장 실패 — {j}")
            return 1
        children.append(j["id"])
        print(f"  {i}장 준비됨 ({j['id']})")

    print("[2/3] 캐러셀 묶기")
    r = requests.post(f"{API}/{acc}/media",
                      data={"media_type": "CAROUSEL", "children": ",".join(children),
                            "caption": full, "access_token": tok}, timeout=60)
    j = r.json()
    if not j.get("id"):
        print(f"  ❌ 실패 — {j}")
        return 1
    creation_id = j["id"]
    print(f"  묶음 준비됨 ({creation_id}) · 인스타 처리 대기 30초")
    time.sleep(30)

    print("[3/3] 발행")
    r = requests.post(f"{API}/{acc}/media_publish",
                      data={"creation_id": creation_id, "access_token": tok}, timeout=60)
    j = r.json()
    post_id = j.get("id")
    if not post_id:
        print(f"  ❌ 발행 실패 — {j}")
        return 1
    print(f"  🎉 발행 완료 — 포스트 ID {post_id}")
    print("  확인: https://www.instagram.com/bdai_79/")

    log = json.load(open(LOG_FILE, encoding="utf-8")) if os.path.exists(LOG_FILE) else {}
    today = datetime.now(KST).strftime("%Y-%m-%d")
    log[today] = {
        "day": 0,
        "theme": "정본 카드뉴스 · 테스터 모집 + 혜택·랭킹전",
        "post_id": post_id,
        "image_url": ", ".join(IMAGES),
        "posted_at": datetime.now(KST).isoformat(),
        "note": "2026-09-03 제작 정본 카드뉴스 2장 캐러셀",
    }
    json.dump(log, open(LOG_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("  기록 저장 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
