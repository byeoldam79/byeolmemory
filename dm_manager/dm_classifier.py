"""
AI 스마트 DM 중요도 분석 및 분류 엔진
(규칙 기반 고속 분석 + 의미 맥락 판별)
"""
import re
from typing import Dict, Any

class DMClassifier:
    """
    인스타그램 DM 텍스트의 맥락을 분석하여 중요도 및 카테고리를 판별하는 클래스
    """
    
    # 1. 비즈니스 / 광고 / 제휴 키워드 패턴
    BUSINESS_KEYWORDS = [
        "광고", "협찬", "제휴", "비즈니스", "콜라보", "미팅", "투자", "단가", 
        "마케팅", "스폰서", "파트너십", "원고료", "포스팅 비용", "인플루언서", "협업",
        "business", "sponsor", "collaboration", "partnership", "ads"
    ]
    
    # 2. 앱 버그 / 오류 제보 / 기능 건의 키워드 패턴
    FEEDBACK_KEYWORDS = [
        "오류", "버그", "에러", "안 돼요", "안돼요", "작동이 안", "멈춤", "튕김",
        "인식이 안", "카운트가 안", "횟수가 안", "자세 감지", "피드백", "건의",
        "개선", "업데이트", "불편", "버벅", "렉", "error", "bug", "issue"
    ]
    
    # 3. 테스터 참여 / 구글 이메일 접수 패턴
    TESTER_KEYWORDS = [
        "테스터", "테스트 참여", "테스터 신청", "이메일 보냅니다", "구글 계정", "설치 링크",
        "내부 테스트", "플레이스토어", "베타", "참여하고 싶"
    ]
    EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

    def classify(self, text: str, sender_name: str = "Unknown") -> Dict[str, Any]:
        """
        메시지 텍스트를 분석하여 중요도(is_important), 등급(priority), 카테고리(category), 요약 이유(reason)를 반환합니다.
        
        반환값:
            {
                "is_important": bool,
                "priority": "HIGH" | "MEDIUM" | "LOW",
                "category": "BUSINESS" | "FEEDBACK" | "TESTER" | "NORMAL",
                "reason": str,
                "extracted_email": str | None
            }
        """
        clean_text = text.strip()
        lower_text = clean_text.lower()
        
        # 1. 이메일 주소 추출 검사 (테스터 신청자 가능성)
        emails = re.findall(self.EMAIL_REGEX, clean_text)
        extracted_email = emails[0] if emails else None
        
        # 2. 비즈니스 / 협찬 제안 검사 (최우선 중요도)
        matched_biz = [kw for kw in self.BUSINESS_KEYWORDS if kw in lower_text]
        if matched_biz:
            return {
                "is_important": True,
                "priority": "HIGH",
                "category": "BUSINESS",
                "reason": f"비즈니스/협찬 관련 키워드 감지: [{', '.join(matched_biz[:3])}]",
                "extracted_email": extracted_email
            }
            
        # 3. 앱 오류 / 버그 / 피드백 검사 (높은 중요도)
        matched_feedback = [kw for kw in self.FEEDBACK_KEYWORDS if kw in lower_text]
        if matched_feedback:
            return {
                "is_important": True,
                "priority": "HIGH",
                "category": "FEEDBACK",
                "reason": f"앱 오류 제보 또는 사용자 피드백 감지: [{', '.join(matched_feedback[:3])}]",
                "extracted_email": extracted_email
            }
            
        # 4. 테스터 참여 신청 검사
        matched_tester = [kw for kw in self.TESTER_KEYWORDS if kw in lower_text]
        if matched_tester or extracted_email:
            reason = "테스터 신청 키워드 감지"
            if extracted_email:
                reason += f" (구글 이메일 발견: {extracted_email})"
            return {
                "is_important": True,
                "priority": "MEDIUM",
                "category": "TESTER",
                "reason": reason,
                "extracted_email": extracted_email
            }
            
        # 5. 일반 메시지 (단순 인사, 스팸 등)
        return {
            "is_important": False,
            "priority": "LOW",
            "category": "NORMAL",
            "reason": "단순 인사 또는 일반 문의",
            "extracted_email": None
        }

if __name__ == "__main__":
    classifier = DMClassifier()
    sample_messages = [
        "안녕하세요! 운동 관련해서 광고 협찬 제안드리고 싶어 연락드립니다.",
        "무브카운터 써봤는데 스쿼트할 때 횟수가 15개에서 멈추는 버그가 있어요 ㅠㅠ",
        "테스터 참여하고 싶습니다! 구글 이메일은 testuser@gmail.com 입니다.",
        "안녕하세요~ 피드 잘 보고 갑니다 맞팔해요!",
        "부업으로 월 300만원 버는 법 프로필 링크 확인하세요"
    ]
    
    print("=" * 60)
    print("🧪 DM 분류 엔진 테스트")
    print("=" * 60)
    for msg in sample_messages:
        res = classifier.classify(msg)
        icon = "🔥 [중요]" if res["is_important"] else "💤 [일반]"
        print(f"\n{icon} 카테고리: {res['category']} (우선순위: {res['priority']})")
        print(f"  내용: \"{msg}\"")
        print(f"  이유: {res['reason']}")
