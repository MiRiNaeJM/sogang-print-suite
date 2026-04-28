# SOGANG Print Client 기술 사용설명서

SOGANG Print Client는 사용자 PC에서 직원번호를 입력하고 Manager에 프린터 매수 조회, 충전, 프린터 서버 로그아웃 요청을 보내는 Windows GUI 프로그램입니다. Client는 WISDOM과 직접 통신하지 않으며 WISDOM 계정 정보와 충전 알고리즘을 저장하지 않습니다.

- [프로젝트 전체 README](../README.md)
- [SOGANG Print Manager 기술 사용설명서](../manager_app/README.md)

## 1. 목적

Client의 목적은 사용자에게 단순한 입력/표시 화면을 제공하고, 모든 실제 처리를 Manager에 위임하는 것입니다.

| 항목 | 설명 |
|---|---|
| Manager 주소 로드 | `client_config.json`에서 `manager_base_url` 읽기 |
| Manager 상태 확인 | `/health` 요청으로 Manager 실행 여부와 설정 완료 여부 확인 |
| 공지/프로그램 정보 수신 | `/client-config`에서 `announcement`와 `aboutContent` 수신 |
| 직원번호 검색 | `/search` 요청 전송 |
| 충전 요청 | `/refill` 요청 전송 |
| 서버 로그아웃 요청 | `/logout-user` 요청 전송 |
| 사용자 메시지 표시 | Manager의 `reasonCode`와 수치 필드 기준으로 한국어/영어 메시지 표시 |

Client가 하지 않는 일은 다음입니다.

```text
- WISDOM에 직접 로그인하지 않는다.
- WISDOM 계정 정보를 저장하지 않는다.
- 최종 충전 가능 여부를 직접 확정하지 않는다.
- Manager의 긴 message 문장을 정규식으로 해석하지 않는다.
- 관리자 설정을 앱 내부에서 저장하지 않는다.
- 충전량을 직접 계산하지 않는다.
```

## 2. 화면 구성

![Client 작동 중 홈 화면](../docs/images/client-home.png)

| 요소 | 역할 |
|---|---|
| 공지사항 영역 | Manager의 `/client-config`에서 받은 announcement 표시 |
| 직원번호 입력칸 | 검색, 충전, 로그아웃 대상 직원번호 입력 |
| 조회 버튼 | Manager `/search` 호출 |
| 충전 버튼 | Manager `/refill` 호출 |
| 서버 로그아웃 버튼 | Manager `/logout-user` 호출 |
| 상태 메시지 | reasonCode 기반 한국어/영어 안내 표시 |
| 프로그램 정보 | Manager에서 내려준 aboutContent 또는 로컬 기본 정보 표시 |

버튼 활성화는 사용성을 위한 보조 상태입니다. 실제 충전 허용 여부와 충전량은 충전 요청 시점에 Manager가 WISDOM을 다시 조회해 결정합니다.

## 3. 설치 중 Manager 주소 입력

![Client 설치 페이지 Manager 주소 입력 화면](../docs/images/client-install-server-url.png)

Client 설치 프로그램은 설치 중 Manager IPv4 주소와 포트를 입력받습니다. `http://`는 사용자가 입력하지 않고 설치 스크립트가 자동으로 붙입니다.

생성되는 설정 파일은 다음 형식입니다.

```json
{
  "manager_base_url": "http://192.168.0.25:8787"
}
```

저장 위치는 다음입니다.

```text
C:\ProgramData\SOGANG Print Client\client_config.json
```

설치 페이지는 숫자 IPv4와 TCP 포트 범위를 검증합니다.

## 4. 실행 초기화 흐름

```text
main.py
  → launch_client_gui()
  → ClientConfigStore.load()
  → ClientContext.from_current_machine()
  → ManagerApi 생성
  → Manager /health 확인
  → Manager /client-config 요청
  → 공지사항 표시
  → aboutContent를 프로그램 정보 창에 반영
```

Manager 연결에 실패하면 Client는 로컬 기본 프로그램 정보와 기본 공지 상태로 시작합니다. 검색, 충전, 서버 로그아웃은 Manager 연결이 필요합니다.

## 5. Manager API 호출

`client_config.json`의 `manager_base_url`이 `http://192.168.0.25:8787`인 경우 Client는 다음 API를 호출합니다.

```text
GET  http://192.168.0.25:8787/health
GET  http://192.168.0.25:8787/client-config
POST http://192.168.0.25:8787/search
POST http://192.168.0.25:8787/refill
POST http://192.168.0.25:8787/logout-user
```

Client는 앱 시작, 검색, 충전, 서버 로그아웃 같은 사용자 동작 시점에 Manager 응답을 확인합니다.

## 6. 직원번호 검색 흐름

```mermaid
flowchart TD
    A[직원번호 입력] --> B[조회 버튼]
    B --> C[Client POST /search]
    C --> D[Manager WISDOM 로그인]
    D --> E[WISDOM 직원번호 검색]
    E --> F[HTML 파싱]
    F --> G[reasonCode와 currentCredit 반환]
    G --> H[Client 상태 메시지 표시]
```

세부 단계는 다음입니다.

```text
1. 사용자가 직원번호를 입력한다.
2. Client가 pcName과 empId를 Manager에 보낸다.
3. Manager가 WISDOM에 로그인한다.
4. Manager가 WISDOM에서 직원번호를 검색한다.
5. Manager가 HTML 응답에서 현재 매수와 서버 로그인 상태를 파싱한다.
6. Manager가 reasonCode, currentCredit, refillAmount, canRefill을 반환한다.
7. Client가 reasonCode와 수치 필드로 사용자 메시지를 만든다.
```

검색 성공 reasonCode는 다음입니다.

| reasonCode | Client 표시 의미 |
|---|---|
| `SEARCH_OK_REFILLABLE` | 조회됨, 현재 잔여 매수와 충전 후 목표값 표시 |
| `SEARCH_OK_NOT_REFILLABLE` | 조회됨, 충전 불필요 |
| `ALREADY_REFILLED_IN_SESSION` | 조회됨, Manager 실행 세션에서 이미 충전함 |

## 7. 충전 흐름

```text
1. 사용자가 충전 버튼을 누른다.
2. Client가 /refill 요청을 보낸다.
3. Manager가 운영 세션 중복 충전 여부를 확인한다.
4. Manager가 WISDOM에서 현재 매수를 다시 조회한다.
5. Manager가 목표값 50매와 현재값의 차이를 계산한다.
6. Manager가 WISDOM increase 요청을 보낸다.
7. Manager가 다시 조회해 실제 반영값을 확인한다.
8. Manager가 서버 로그아웃을 시도한다.
9. Client는 reasonCode 기준으로 결과 메시지를 표시한다.
10. Client는 /client-config를 다시 불러와 공지와 프로그램 정보를 갱신한다.
```

대표 표시 결과는 다음입니다.

| reasonCode | 사용자에게 보이는 의미 |
|---|---|
| `REFILL_OK` | 충전 완료, 전/후 매수 표시 |
| `REFILL_NOT_NEEDED` | 현재 잔여 매수가 충분해 충전 불필요 |
| `ALREADY_REFILLED_IN_SESSION` | 이미 이번 운영 세션에서 충전함 |
| `LOGOUT_FAILED` | 충전은 반영되었지만 서버 로그아웃 실패 |
| `VERIFY_FAILED` | 충전 후 최종 재확인 실패 |
| `VERIFY_MISMATCH` | 재조회 값이 예상과 다름 |

## 8. 서버 로그아웃 흐름

서버 로그아웃은 WISDOM 프린터 서버 세션을 종료하기 위한 기능입니다.

```text
1. 사용자가 서버 로그아웃 버튼을 누른다.
2. Client가 /logout-user 요청을 보낸다.
3. Manager가 WISDOM에 로그인한다.
4. Manager가 해당 직원번호의 서버 로그아웃 요청을 보낸다.
5. Manager가 로그아웃 상태를 재확인한다.
6. Client가 결과를 표시한다.
```

대표 reasonCode는 다음입니다.

| reasonCode | 의미 |
|---|---|
| `LOGOUT_OK` | 프린터 서버 세션 종료 확인 |
| `LOGOUT_VERIFY_FAILED` | 서버 세션 종료를 확인하지 못함 |
| `LOGOUT_ERROR` | 로그아웃 처리 중 문제 발생 |

## 9. `/client-config` 갱신

Client는 다음 시점에 `/client-config`를 호출합니다.

```text
- 앱 시작 후
- 검색 후
- 충전 후
- 서버 로그아웃 후
```

`/client-config` 응답에는 공지사항과 Client 프로그램 정보가 함께 포함됩니다.

```json
{
  "ok": true,
  "announcement": "공지사항 내용",
  "managerVersion": "1.0.0",
  "aboutContent": {
    "app_name": "서강대 프린터 클라이언트 SOGANG Print Client",
    "app_version": "1.0.0",
    "author": "서강대학교 디지털정보처",
    "github_url": "https://github.com/MiRiNaeJM/sogang-print-suite",
    "license_name": "",
    "about_title": "프로그램 정보",
    "about_summary": "클라이언트 프로그램 설명",
    "manual_text": "사용 안내"
  }
}
```

## 10. 프로그램 정보 표시

Client 프로그램 정보 창은 다음 순서로 내용을 결정합니다.

```text
1. 기본값: client_app/app/about_content.py
2. 로컬 파일: C:\ProgramData\SOGANG Print Client\about_content.json
3. Manager 응답: /client-config의 aboutContent
```

Manager와 연결되면 Manager가 내려준 `aboutContent`가 우선 반영됩니다. Client 프로그램 정보는 사용자 PC에서 직접 편집하지 않고 Manager에서 중앙 관리합니다.

## 11. reasonCode 기반 메시지 표시

Client의 `i18n.py`는 Manager가 보낸 긴 `message` 문장을 해석하지 않습니다. `reasonCode`와 수치 필드를 기준으로 한국어/영어 문구를 만듭니다.

예시 응답은 다음입니다.

```json
{
  "reasonCode": "REFILL_OK",
  "beforeCredit": 12,
  "afterCredit": 50,
  "refillAmount": 38
}
```

표시 문구는 다음과 같은 형태입니다.

```text
충전되었습니다
12매 → 50매

Refill completed
12 to 50
```

`message`는 알 수 없는 reasonCode나 예외 fallback 상황에서만 보조적으로 사용합니다.

## 12. 오류 상황별 확인 위치

| 상황 | 대표 reasonCode | 사용자 표시 의미 | 확인할 위치 |
|---|---|---|---|
| Manager 주소 없음 | 없음 | Manager 주소가 설정되지 않음 | `client_config.json` |
| Manager 연결 실패 | 없음 | Manager에 연결할 수 없음 | Manager 실행 여부, 방화벽, IP/Port |
| 직원번호 미입력 | `INVALID_INPUT` | 학번/사번 입력 필요 | Client 입력값 |
| 직원번호 없음 | `NOT_FOUND` | 조회 결과 없음 | WISDOM 데이터 |
| 현재 매수 파싱 실패 | `PARSE_FAILED` | WISDOM HTML 구조 확인 필요 | `parser_utils.py` |
| 이미 충전함 | `ALREADY_REFILLED_IN_SESSION` | Manager 실행 세션에서 이미 충전 | Manager 재시작 여부 |
| 충전 불필요 | `REFILL_NOT_NEEDED` | 이미 목표 매수 이상 | WISDOM 현재 매수 |
| 인증 실패 | `AUTH_ERROR` | WISDOM 로그인 실패 | Manager secrets |
| 통신 실패 | `NETWORK_ERROR` | WISDOM 통신 실패 | 네트워크, WISDOM 상태 |
| 재조회 불일치 | `VERIFY_MISMATCH` | 충전 후 값이 예상과 다름 | Manager 로그, WISDOM 실제 값 |

## 13. 설치 후 ProgramData 파일

```text
C:\ProgramData\SOGANG Print Client\
  client_config.json
  about_content.json
```

`client_config.json`은 설치 중 입력한 Manager 주소로 생성됩니다. `about_content.json`은 Manager에 연결하지 못할 때 사용할 기본 프로그램 정보입니다. 정상 운영에서는 Manager의 `/client-config`에 포함된 `aboutContent`가 우선 반영됩니다.

## 14. 빌드

프로젝트 루트에서 Client 실행 파일을 생성합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r client_app\requirements.txt
python -m PyInstaller --noconfirm `
  --distpath "dist" `
  --workpath "build\client" `
  "SOGANG_Print_Client.spec"
```

빌드 결과물은 다음 위치에 생성됩니다.

```text
dist\SOGANG Print Client\
```

## 15. 설치 파일 생성

Client 설치 파일은 `client_app/Client_setup.iss`로 생성합니다.

```powershell
cd client_app
ISCC Client_setup.iss
```

설치 스크립트의 주요 동작은 다음입니다.

| 섹션 | 동작 |
|---|---|
| `[Files]` | PyInstaller 결과물, 공유 아이콘, 기본 프로그램 정보 JSON 복사 |
| `[Dirs]` | `C:\ProgramData\SOGANG Print Client` 폴더 생성 및 권한 설정 |
| `[Icons]` | 시작 메뉴, 바탕화면, 시작프로그램 바로가기 생성 |
| `[Code]` | Manager IPv4/Port 입력, 기존 설정 초기화 옵션 처리 |

설치 파일은 `client_app/installer_output/` 아래에 생성됩니다. 이 폴더는 GitHub 커밋 대상이 아닙니다.

## 16. 운영 PC 배치 기준

Client 운영 PC에는 다음이 필요합니다.

```text
- 설치된 SOGANG Print Client 프로그램
- C:\ProgramData\SOGANG Print Client\client_config.json
- Manager PC로 접속 가능한 네트워크
- Manager 서버 포트 접근 허용
```

Client 설치 프로그램은 시작프로그램 바로가기와 바탕화면 바로가기를 생성합니다.

## 17. 아이콘과 리소스

Client는 루트 공유 아이콘을 사용합니다.

```text
assets/app_icon.ico
```

PyInstaller spec 파일은 루트 `assets` 폴더를 실행 파일 배포본의 `assets` 폴더로 포함합니다. `client_app/app/resource_utils.py`는 개발 환경과 PyInstaller 실행 환경에서 `assets/app_icon.ico`를 찾습니다. Tkinter 라벨에 표시할 아이콘 이미지는 Pillow로 ICO 파일을 읽어 `ImageTk.PhotoImage`로 변환합니다.

## 18. 주요 코드 파일

| 파일 | 역할 |
|---|---|
| `main.py` | Client 실행 진입점 |
| `app/gui_client.py` | Client 메인 GUI, 검색/충전/로그아웃 버튼 흐름 |
| `app/manager_api.py` | Manager HTTP API 호출 래퍼 |
| `app/api_models.py` | Manager 응답 dataclass 모델 |
| `app/i18n.py` | reasonCode 기반 사용자 메시지 생성 |
| `app/config_store.py` | `client_config.json` 로드 |
| `app/client_context.py` | PC 이름/사용자 이름 등 운영 로그용 Client 정보 생성 |
| `app/about_content.py` | Client 프로그램 정보 기본값 |
| `app/about_content_loader.py` | 로컬/Manager aboutContent 정규화 |
| `app/about_dialog.py` | 프로그램 정보 창 |
| `app/paths.py` | ProgramData 경로 계산 |
| `app/resource_utils.py` | 아이콘 asset 로드 |
| `app/ui_style.py` | Tkinter 스타일 정의 |
