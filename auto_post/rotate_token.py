# -*- coding: utf-8 -*-
"""
토큰 교체 — 새 장기 토큰을 발급받아 .env 에 갈아 끼운다.

  python rotate_token.py            ← 교체하고, 옛 토큰이 죽었는지까지 확인
  python rotate_token.py --check    ← 지금 토큰이 살아 있는지만 본다

왜 필요한가
  2026-09-08 — 접속 토큰이 공개 깃허브 저장소에 올라가 있던 것이 확인됐다.
  토큰은 60일마다도 새로 받아야 하므로, 이 도구를 정기적으로 돌린다.
"""
import os
import shutil
import sys
from datetime import datetime

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
ENV_FILE = os.path.join(ROOT_DIR, ".env")
API = "https://graph.instagram.com"


def read_env_lines():
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def get_value(lines, key):
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, v = s.split("=", 1)
            if k.strip() == key:
                return v.strip()
    return ""


def set_value(lines, key, value):
    out, done = [], False
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s and s.split("=", 1)[0].strip() == key:
            out.append(f"{key}={value}")
            done = True
        else:
            out.append(line)
    if not done:
        out.append(f"{key}={value}")
    return out


def alive(token):
    r = requests.get(f"{API}/v23.0/me", params={"fields": "id,username", "access_token": token}, timeout=20)
    return r.status_code == 200, r.json()


def main():
    lines = read_env_lines()
    old = get_value(lines, "INSTAGRAM_ACCESS_TOKEN")
    if not old:
        print("❌ .env 에 INSTAGRAM_ACCESS_TOKEN 이 없습니다.")
        return 1

    ok, info = alive(old)
    print(f"현재 토큰: {'살아 있음 — @' + info.get('username', '?') if ok else '죽어 있음'}")
    if "--check" in sys.argv:
        if not ok:
            print(f"  응답: {info}")
        return 0 if ok else 2
    if not ok:
        print("  → 이미 못 쓰는 토큰입니다. 새로 발급받아야 합니다(사람 손 필요).")
        return 2

    print("\n새 토큰 발급 중...")
    r = requests.get(f"{API}/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": old}, timeout=30)
    j = r.json()
    new = j.get("access_token")
    if not new:
        print(f"❌ 발급 실패 — {j}")
        return 1
    days = round(j.get("expires_in", 0) / 86400)
    print(f"✅ 새 토큰 발급됨 (약 {days}일 유효)")

    ok_new, info_new = alive(new)
    if not ok_new:
        print(f"❌ 새 토큰이 동작하지 않습니다. .env 를 건드리지 않고 멈춥니다. — {info_new}")
        return 1
    print(f"   새 토큰 확인 — @{info_new.get('username')}")

    shutil.copy2(ENV_FILE, ENV_FILE + f".backup-{datetime.now():%Y%m%d-%H%M}")
    lines = set_value(lines, "INSTAGRAM_ACCESS_TOKEN", new)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("   .env 갱신 완료 (원본은 .env.backup-... 로 남김)")

    ok_old, info_old = alive(old)
    print("\n[옛 토큰 상태 확인]")
    if ok_old:
        print("  ⚠️ 옛 토큰이 아직 살아 있습니다.")
        print("     인스타는 발급만으로 옛 토큰을 죽이지 않습니다. 만료될 때까지 유효합니다.")
        print("     유출된 적이 있다면 Meta 화면에서 앱 권한을 직접 해제해야 완전히 막힙니다.")
    else:
        print("  ✅ 옛 토큰이 더 이상 동작하지 않습니다. 유출본은 무력화됐습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
