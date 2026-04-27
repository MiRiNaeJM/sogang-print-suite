"""Client 프로그램 정보의 기본값을 정의하는 모듈.

Manager에서 Client용 정보를 내려주지 못하는 상황에서도 프로그램 정보 창이 최소 내용을 표시할 수 있게 한다.
"""

APP_NAME = "서강대 프린터 클라이언트 SOGANG Print Client"
APP_VERSION = "1.0.0"
AUTHOR = "서강대학교 디지털정보처"
GITHUB_URL = "https://github.com/OWNER/REPOSITORY"
LICENSE_NAME = ""

ABOUT_TITLE = "프로그램 정보"
ABOUT_SUMMARY = "프로그램 설명을 입력하세요."

MANUAL_TEXT = """
[Client 매뉴얼]

1. 사용 방법을 입력하세요.
2. 상태 메시지 설명을 입력하세요.
3. 오류 발생 시 안내 문구를 입력하세요.

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
