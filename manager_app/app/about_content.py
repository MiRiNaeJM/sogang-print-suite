"""Manager 프로그램 정보의 기본값을 정의하는 모듈.

프로그램 정보 JSON이 없거나 깨졌을 때도 Manager 정보 창이 기본 내용을 표시할 수 있게 한다.
"""

APP_NAME = "서강대 프린터 매니저 SOGANG Print Manager"
APP_VERSION = "1.0.0"
AUTHOR = "서강대학교 디지털정보처"
GITHUB_URL = "https://github.com/OWNER/REPOSITORY"
LICENSE_NAME = ""

ABOUT_TITLE = "프로그램 정보"
ABOUT_SUMMARY = "프로그램 설명을 입력하세요."

MANUAL_TEXT = """
[Manager 매뉴얼]

1. 서버 시작/종료 설명을 입력하세요.
2. 공지사항 관리 방법을 입력하세요.
3. WISDOM 설정 설명을 입력하세요.
4. 로그 확인 방법을 입력하세요.
5. 마스터 비밀번호 초기화 방법을 입력하세요.

[문의]
관리자 문의 정보를 입력하세요.
""".strip()


DEFAULT_ABOUT_CONTENT = {
    "app_name": APP_NAME,
    "app_version": APP_VERSION,
    "author": AUTHOR,
    "github_url": GITHUB_URL,
    "license_name": LICENSE_NAME,
    "about_title": ABOUT_TITLE,
    "about_summary": ABOUT_SUMMARY,
    "manual_text": MANUAL_TEXT,
}

DEFAULT_CLIENT_ABOUT_CONTENT = {
    "app_name": "서강대 프린터 클라이언트 SOGANG Print Client",
    "app_version": APP_VERSION,
    "author": AUTHOR,
    "github_url": GITHUB_URL,
    "license_name": LICENSE_NAME,
    "about_title": "프로그램 정보",
    "about_summary": "클라이언트 프로그램 설명을 입력하세요.",
    "manual_text": """[클라이언트 매뉴얼]

1. 사용 방법을 입력하세요.
2. 상태 메시지 설명을 입력하세요.
3. 오류 발생 시 안내 문구를 입력하세요.

[문의]
관리자 문의 정보를 입력하세요.
""".strip(),
}
