"""
실제 무브카운터 앱 스크린샷과 현실적인 찐따 남성 모델 이미지를 합성하여
인스타그램 홍보용 고퀄리티 배너를 제작하는 스크립트입니다.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# 콘솔 UTF-8 한글 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
BRAIN_DIR = r"C:\Users\jw-notebook\.gemini\antigravity-ide\brain\b5d9a4bf-54b4-4b66-b334-f29eb42056b8"
MAN_IMG_PATH = os.path.join(BRAIN_DIR, "nerd_guy_workout_1788066658194.jpg")
APP_IMG_PATH = os.path.join(BRAIN_DIR, ".user_uploaded", "media_1788066610563.jpg")

OUTPUT_PATH_1 = os.path.join(BRAIN_DIR, "jjinda_movecounter_card_v1.jpg")
OUTPUT_PATH_2 = os.path.join(BRAIN_DIR, "jjinda_movecounter_card_v2.jpg")

# 폰트 설정
FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"
FONT_REG  = r"C:\Windows\Fonts\malgun.ttf"

def create_option_1():
    """
    옵션 1: 인스타 최적화 1:1 카드뉴스 스타일
    - 메인: 방구석 운동 찐따남
    - 우측 상단/하단: 실제 앱 UI를 스마트폰 목업 형태로 띄우고 강조 배너 추가
    """
    base_img = Image.open(MAN_IMG_PATH).convert("RGBA")
    app_img = Image.open(APP_IMG_PATH).convert("RGBA")
    
    # 1080 x 1080 캔버스
    canvas_size = (1080, 1080)
    base_img = base_img.resize(canvas_size, Image.Resampling.LANCZOS)
    
    # 앱 스크린샷 비율 유지하며 스마트폰 목업 형태로 리사이즈
    # 앱 원본 크기 비율 확인
    app_w, app_h = app_img.size
    phone_h = 680
    phone_w = int(app_w * (phone_h / app_h))
    app_resized = app_img.resize((phone_w, phone_h), Image.Resampling.LANCZOS)
    
    # 스마트폰 프레임 만들기 (둥근 모서리 + 그림자 + 네온 테두리)
    mask = Image.new("L", (phone_w, phone_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (phone_w, phone_h)], radius=36, fill=255)
    
    phone_canvas = Image.new("RGBA", (phone_w + 30, phone_h + 30), (0, 0, 0, 0))
    # 그림자 효과
    shadow = Image.new("RGBA", (phone_w + 30, phone_h + 30), (0, 0, 0, 0))
    draw_shadow = ImageDraw.Draw(shadow)
    draw_shadow.rounded_rectangle([(15, 15), (phone_w + 15, phone_h + 15)], radius=36, fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    
    # 테두리 (네온 시안)
    border_img = Image.new("RGBA", (phone_w, phone_h), (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border_img)
    draw_border.rounded_rectangle([(0, 0), (phone_w-1, phone_h-1)], radius=36, outline=(0, 240, 255, 220), width=4)
    
    # 베이스 이미지에 그림자 및 앱 화면 합성
    pos_x = 1080 - phone_w - 50
    pos_y = 60
    
    # 합성
    base_img.paste(shadow, (pos_x - 15, pos_y - 15), shadow)
    base_img.paste(app_resized, (pos_x, pos_y), mask)
    base_img.paste(border_img, (pos_x, pos_y), border_img)
    
    # 상단 / 하단 자막 배너 추가
    draw = ImageDraw.Draw(base_img)
    
    # 상단 헤드라인 박스 (블랙 반투명 글래스모피즘)
    headline_box = [(40, 40), (pos_x - 30, 220)]
    draw.rounded_rectangle(headline_box, radius=20, fill=(10, 15, 25, 230), outline=(0, 210, 255, 180), width=2)
    
    f_tag = ImageFont.truetype(FONT_BOLD, 22)
    f_title = ImageFont.truetype(FONT_BOLD, 38)
    f_sub = ImageFont.truetype(FONT_REG, 24)
    
    draw.text((60, 58), "🚨 방구석 찐따의 대변신 프로젝트", font=f_tag, fill=(255, 200, 50))
    draw.text((60, 95), "“오늘부터 1일차다...”", font=f_title, fill=(255, 255, 255))
    draw.text((60, 155), "카메라면 켜두면 AI가\n횟수/자세 알아서 다 세어줌! 📱", font=f_sub, fill=(200, 240, 255))
    
    # 하단 강조 배너
    bottom_box = [(40, 930), (1040, 1040)]
    draw.rounded_rectangle(bottom_box, radius=24, fill=(15, 20, 35, 235), outline=(0, 255, 200, 200), width=3)
    
    f_bottom_main = ImageFont.truetype(FONT_BOLD, 36)
    f_bottom_sub  = ImageFont.truetype(FONT_BOLD, 26)
    draw.text((70, 948), "🤖 MoveCounter AI 아케이드 피트니스", font=f_bottom_main, fill=(0, 240, 255))
    draw.text((70, 995), "스쿼트 · 푸쉬업 · 크런치 · 런지 · 점핑잭 | 온디바이스 AI 보안 100%", font=f_bottom_sub, fill=(255, 255, 255))
    
    # 최종 저장 (RGB 변환)
    base_img.convert("RGB").save(OUTPUT_PATH_1, "JPEG", quality=95)
    print(f"✅ 옵션 1 생성 완료: {OUTPUT_PATH_1}")


def create_option_2():
    """
    옵션 2: 좌우 2분할 (스토리텔링형 프리미엄 카드)
    - 좌측: 방구석 찐따의 처절한 푸시업 1일차
    - 우측: 실제 앱 화면 정밀 배치 + 기능 설명 포인트
    """
    canvas = Image.new("RGBA", (1080, 1080), (13, 17, 23, 255))
    draw = ImageDraw.Draw(canvas)
    
    # 배경 그라데이션 및 네온 라인
    draw.rectangle([(0, 0), (1080, 100)], fill=(18, 24, 38, 255))
    
    # 좌측: 인물 사진 크롭 및 배치 (폭 500)
    man_img = Image.open(MAN_IMG_PATH).convert("RGBA")
    # 정사각형 중앙 크롭
    w, h = man_img.size
    crop_man = man_img.crop((0, 0, w, h)).resize((500, 800), Image.Resampling.LANCZOS)
    
    # 둥근 모서리
    mask_man = Image.new("L", (500, 800), 0)
    draw_mask_m = ImageDraw.Draw(mask_man)
    draw_mask_m.rounded_rectangle([(0, 0), (500, 800)], radius=24, fill=255)
    
    canvas.paste(crop_man, (40, 140), mask_man)
    
    # 좌측 사진 테두리
    draw.rounded_rectangle([(40, 140), (540, 940)], radius=24, outline=(255, 100, 100, 180), width=3)
    
    # 좌측 라벨
    f_badge = ImageFont.truetype(FONT_BOLD, 22)
    draw.rounded_rectangle([(60, 160), (280, 205)], radius=12, fill=(220, 40, 40, 240))
    draw.text((75, 170), "🔥 현실 찐따 1일차", font=f_badge, fill=(255, 255, 255))
    
    # 우측: 앱 스크린샷 배치 (폭 460)
    app_img = Image.open(APP_IMG_PATH).convert("RGBA")
    app_w, app_h = app_img.size
    target_app_h = 800
    target_app_w = int(app_w * (target_app_h / app_h))
    app_resized = app_img.resize((target_app_w, target_app_h), Image.Resampling.LANCZOS)
    
    mask_app = Image.new("L", (target_app_w, target_app_h), 0)
    draw_mask_a = ImageDraw.Draw(mask_app)
    draw_mask_a.rounded_rectangle([(0, 0), (target_app_w, target_app_h)], radius=24, fill=255)
    
    app_x = 570
    canvas.paste(app_resized, (app_x, 140), mask_app)
    draw.rounded_rectangle([(app_x, 140), (app_x + target_app_w, 940)], radius=24, outline=(0, 220, 255, 200), width=3)
    
    # 상단 전체 타이틀
    f_main_title = ImageFont.truetype(FONT_BOLD, 42)
    f_main_sub   = ImageFont.truetype(FONT_BOLD, 24)
    draw.text((40, 28), "MOVECOUNTER", font=f_main_title, fill=(0, 240, 255))
    draw.text((370, 42), "방구석 헬린이도 AI로 갓생 시작! ⚡", font=f_main_sub, fill=(255, 255, 255))
    
    # 하단 바
    draw.rounded_rectangle([(40, 970), (1040, 1050)], radius=16, fill=(25, 35, 55, 255), outline=(0, 200, 255, 150), width=2)
    f_bar = ImageFont.truetype(FONT_BOLD, 26)
    draw.text((70, 992), "📱 카메라 켜고 자세 잡으면 AI가 100% 온디바이스 자동 카운팅!", font=f_bar, fill=(0, 255, 200))
    
    canvas.convert("RGB").save(OUTPUT_PATH_2, "JPEG", quality=95)
    print(f"✅ 옵션 2 생성 완료: {OUTPUT_PATH_2}")

if __name__ == "__main__":
    create_option_1()
    create_option_2()
