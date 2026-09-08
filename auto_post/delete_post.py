# -*- coding: utf-8 -*-
"""게시물 삭제 시도.  python delete_post.py <포스트ID>"""
import json
import os
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(os.path.dirname(BASE), ".env")
LOG = os.path.join(BASE, "post_log.json")


def env():
    d = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


pid = sys.argv[1] if len(sys.argv) > 1 else ""
if not pid:
    print("포스트 ID를 적으십시오.")
    sys.exit(1)

c = env()
tok = c["INSTAGRAM_ACCESS_TOKEN"]

for host in ("https://graph.instagram.com/v23.0", "https://graph.facebook.com/v23.0"):
    r = requests.delete(f"{host}/{pid}", params={"access_token": tok}, timeout=30)
    print(f"DELETE {host}/{pid} → {r.status_code} {r.text[:220]}")
    if r.status_code == 200 and r.json().get("success"):
        print("✅ 삭제됨")
        log = json.load(open(LOG, encoding="utf-8"))
        for k in [k for k, v in log.items() if isinstance(v, dict) and v.get("post_id") == pid]:
            del log[k]
        json.dump(log, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("   발행 기록에서도 지웠습니다.")
        sys.exit(0)

print("\n❌ API 로는 삭제되지 않습니다. 인스타그램은 게시물 삭제 기능을 API 로 열어두지 않습니다.")
sys.exit(2)
