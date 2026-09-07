# -*- coding: utf-8 -*-
"""
이미지를 ImgBB(무료 사진 창고)에 올려 공개 주소를 받아 온다.

  python upload_images.py <이미지파일> [<이미지파일> ...]

인스타는 **인터넷에서 누구나 열 수 있는 https 주소**만 받는다.
PC 안의 파일 경로로는 게시가 안 되므로 반드시 이 과정을 거친다.
"""
import base64
import json
import os
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
ENV_FILE = os.path.join(ROOT_DIR, ".env")


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


def upload(api_key, path):
    with open(path, "rb") as f:
        payload = {"key": api_key, "image": base64.b64encode(f.read()).decode("utf-8")}
    r = requests.post("https://api.imgbb.com/1/upload", data=payload, timeout=60)
    j = r.json()
    if not j.get("success"):
        raise RuntimeError(j.get("error", {}).get("message", r.text[:200]))
    return j["data"]["url"]


def main():
    files = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not files:
        print("올릴 이미지 파일을 적으십시오.")
        return 1

    key = load_env().get("IMGBB_API_KEY", "")
    if not key:
        print("❌ .env 에 IMGBB_API_KEY 가 없습니다.")
        return 1

    result = {}
    for p in files:
        if not os.path.exists(p):
            print(f"❌ 파일 없음: {p}")
            continue
        try:
            url = upload(key, p)
            result[os.path.basename(p)] = url
            print(f"✅ {os.path.basename(p)}\n   {url}")
        except Exception as e:
            print(f"❌ {os.path.basename(p)} — {e}")

    out = os.path.join(BASE_DIR, "imgbb_urls.json")
    old = {}
    if os.path.exists(out):
        try:
            old = json.load(open(out, encoding="utf-8"))
        except Exception:
            old = {}
    if isinstance(old, dict):
        old.update(result)
    else:
        old = result
    json.dump(old, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n주소를 {out} 에 기록했습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
