"""
신규 생성된 이미지를 ImgBB에 업로드하고 content_plan.json에 자동으로 기록하는 스크립트
파일명: upload_custom_image.py
설명:
  1. .env 파일에서 IMGBB_API_KEY를 읽어옵니다.
  2. 로컬에 생성된 이미지(day6_jumpingjack_1788084567149.jpg)를 읽어와 Base64로 인코딩합니다.
  3. ImgBB API를 호출하여 영구 보존용 웹 이미지 URL을 획득합니다.
  4. content_plan.json을 파싱하여 Day 6 항목에 'image_url' 필드로 해당 URL을 저장합니다.
"""
import os
import sys
import json
import base64
import requests

# 콘솔 UTF-8 설정 (한글 출력 깨짐 방지)
sys.stdout.reconfigure(encoding='utf-8')

# 기본 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
ENV_FILE = os.path.join(ROOT_DIR, ".env")
CONTENT_FILE = os.path.join(BASE_DIR, "content_plan.json")

# 업로드할 로컬 이미지 파일 경로 (생성된 이미지 파일)
LOCAL_IMAGE_PATH = r"C:\Users\qowhd\.gemini\antigravity-ide\brain\44483099-6cb6-4812-b562-2e3d18620748\day6_jumpingjack_v2_1788084668075.jpg"

def load_env() -> dict:
    """ .env 파일에서 설정값들을 안전하게 파싱해 읽어옵니다. """
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

def upload_to_imgbb(api_key: str, image_path: str) -> str | None:
    """ 이미지를 ImgBB에 업로드하고 영구 URL을 가져옵니다. """
    if not os.path.exists(image_path):
        print(f"❌ [오류] 로컬 이미지 파일을 찾을 수 없습니다: {image_path}")
        return None
        
    print(f"🔄 ImgBB에 이미지 업로드 중... ({os.path.basename(image_path)})")
    
    # 1. 이미지를 바이너리로 읽어 base64로 인코딩합니다.
    with open(image_path, "rb") as file:
        img_base64 = base64.b64encode(file.read()).decode('utf-8')
        
    # 2. ImgBB 업로드 API 호출
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": api_key,
        "image": img_base64
    }
    
    try:
        response = requests.post(url, data=payload, timeout=30)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            img_url = result["data"]["url"]
            print(f"✅ [업로드 성공] 이미지 URL: {img_url}")
            return img_url
        else:
            print(f"❌ [업로드 실패] API 에러 내용: {result}")
            return None
    except Exception as e:
        print(f"❌ [업로드 오류] 통신 예외 발생: {e}")
        return None

def update_content_plan(day: int, image_url: str):
    """ content_plan.json에서 특정 Day를 찾아 image_url 필드를 업데이트합니다. """
    if not os.path.exists(CONTENT_FILE):
        print(f"❌ [오류] 콘텐츠 플랜 파일이 없습니다: {CONTENT_FILE}")
        return
        
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        plans = json.load(f)
        
    updated = False
    for plan in plans:
        if plan.get("day") == day:
            plan["image_url"] = image_url
            updated = True
            break
            
    if updated:
        with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump(plans, f, ensure_ascii=False, indent=2)
        print(f"💾 [업데이트 완료] content_plan.json의 Day {day}에 이미지 URL 등록 성공!")
    else:
        print(f"⚠️ [주의] content_plan.json에서 Day {day}를 찾지 못했습니다.")

def main():
    config = load_env()
    api_key = config.get("IMGBB_API_KEY")
    
    if not api_key:
        print("❌ [오류] .env 파일에 IMGBB_API_KEY가 설정되어 있지 않습니다!")
        return
        
    # ImgBB 업로드 실행
    img_url = upload_to_imgbb(api_key, LOCAL_IMAGE_PATH)
    
    if img_url:
        # Day 6의 콘텐츠 플랜에 저장
        update_content_plan(6, img_url)

if __name__ == "__main__":
    main()
