# SOGANG Print Manager 기술 사용설명서

SOGANG Print Manager는 사용자 PC의 Client 요청을 받아 WISDOM과 통신하는 관리자 프로그램입니다. 이 문서는 Manager를 실행하는 방법만이 아니라, Manager가 왜 이런 구조로 동작하는지, 어떤 파일이 어떤 책임을 가지는지, 빌드와 설치가 어떤 파일 구조를 만드는지 설명합니다.

- [프로젝트 전체 README](../README.md)
- [Client 기술 사용설명서](../client_app/README.md)

---

## 1. Manager의 목적

Manager는 이 프로젝트의 중심 서버입니다. Client는 WISDOM 계정 정보나 충전 알고리즘을 알지 못하고, Manager에게 요청만 보냅니다. Manager는 요청을 받아 WISDOM에 로그인하고, 직원번호 검색, 매수 증가, 서버 로그아웃, 결과 검증을 수행합니다.

Manager의 핵심 책임은 다음과 같습니다.

| 책임 | 설명 |
|---|---|
| WISDOM 접속 정보 관리 | WISDOM URL, 관리자 ID, 비밀번호를 암호화된 secrets 파일로 저장 |
| Client API 제공 | `/health`, `/client-config`, `/search`, `/refill`, `/logout-user` 제공 |
| 검색/충전 처리 | WISDOM HTML 응답을 파싱하고 필요한 충전량을 계산 |
| 공지 배포 | Client에 표시할 공지사항을 `/client-config`로 제공 |
| 프로그램 정보 관리 | Manager용/Client용 프로그램 정보 JSON을 편집하고 저장 |
| 운영 로그 표시 | Client 요청과 WISDOM 처리 결과를 GUI 로그에 표시 |

---

## 2. Manager 화면 구성

![Manager 작동 중 홈 화면](../docs/images/manager-home.png)

Manager 홈 화면은 운영 중 상태 확인과 종료를 위한 화면입니다.

| 요소 | 역할 |
|---|---|
| 공지사항 영역 | Client에 내려줄 공지사항을 관리자가 확인할 수 있음 |
| 서버 상태 | Manager API 서버 실행 여부를 표시 |
| WISDOM 상태 | 설정 완료 여부와 WISDOM 처리 가능 상태를 표시 |
| 로그 표 | 검색, 충전, 로그아웃 요청 결과를 시간순으로 표시 |
| 관리자 설정 | host/port, 공지, WISDOM secrets, 관리자 비밀번호 설정 |
| 프로그램 종료 | 트레이 종료와 같은 종료 흐름을 실행 |

Manager는 서버 역할을 하므로, 화면을 닫는 것과 프로그램을 완전히 종료하는 동작을 구분해야 합니다. 현재 구조에서는 홈 화면의 종료 버튼과 트레이 메뉴의 종료가 같은 종료 로직을 사용합니다.

---

## 3. 초기 설정 화면

![Manager 초기 설정 페이지](../docs/images/manager-initial-setup.png)

초기 설정은 Manager 실행에 필요한 필수값이 없을 때 표시됩니다. 초기 설정과 일반 관리자 설정은 같은 `AdminDialog`를 재사용합니다. 이렇게 하면 초기 설정 화면과 운영 중 설정 변경 화면의 저장 규칙이 어긋나지 않습니다.

초기 설정에서 다루는 값은 두 그룹으로 나뉩니다.

| 그룹 | 저장 위치 | 설명 |
|---|---|---|
| 공개 설정 | `manager_public_config.json` | host, port, 공지사항, 관리자 비밀번호 해시 |
| 비밀 설정 | `manager_secrets.enc.json` | WISDOM URL, 관리자 ID, 관리자 비밀번호 |

관리자 비밀번호는 평문으로 저장하지 않고 해시로 저장합니다. WISDOM 접속 정보는 `CryptoProvider`를 통해 암호화 파일로 저장합니다.

---

## 4. 프로그램 정보 편집 화면

![프로그램 정보 편집 화면](../docs/images/manager-about-editor.png)

관리자 설정 화면의 `프로그램 정보` 버튼은 `AboutEditorDialog`를 엽니다. 이 화면은 Manager 정보와 Client 정보를 탭으로 나누어 편집합니다.

저장 대상은 다음과 같습니다.

```text
C:\ProgramData\SOGANG Print Manager\manager_about_content.json
C:\ProgramData\SOGANG Print Manager\client_about_content.json
```

Manager 정보는 Manager의 프로그램 정보 창에 사용됩니다. Client 정보는 `/client-config` 응답의 `aboutContent`로 내려가며, Client가 조회/충전/로그아웃 또는 Manager 설정 갱신 흐름에서 다시 받아 표시합니다.

필수 필드는 다음입니다.

| 필드 | 의미 |
|---|---|
| `app_name` | 프로그램 정보 창에 표시할 앱 이름 |
| `app_version` | 앱 버전 |
| `about_title` | 프로그램 정보 창 제목 |

---

## 5. 실행 시 초기화 흐름

Manager가 시작되면 다음 순서로 초기화됩니다.

```text
main.py
  → launch_manager_gui()
  → ManagerGUI 생성
  → PublicConfigStore.load()
  → SecretStore.load()
  → 필수 설정 검사
  → 필요 시 AdminDialog 표시
  → ManagerService 생성
  → Flask app 생성
  → ServerRuntime이 Waitress/Flask 서버 시작
  → TrayRuntime이 트레이 아이콘 실행
```

초기화 단계에서 설정 파일이 없으면 기본 설정을 만들거나 빈 secrets로 시작합니다. WISDOM 정보가 비어 있으면 Manager 서버는 실행되더라도 실제 검색/충전 처리는 설정 완료 전까지 정상 동작하지 않습니다.

---

## 6. 설정 파일 구조

Manager 설정은 ProgramData 아래에 저장됩니다.

```text
C:\ProgramData\SOGANG Print Manager\
  manager_public_config.json
  manager_secrets.enc.json
  manager_about_content.json
  client_about_content.json
```

### `manager_public_config.json`

```json
{
  "manager_host": "0.0.0.0",
  "manager_port": 8787,
  "announcement": "",
  "admin_password_hash": ""
}
```

| 필드 | 설명 |
|---|---|
| `manager_host` | Flask/Waitress 서버가 바인딩할 주소. 일반 운영에서는 `0.0.0.0` 사용 |
| `manager_port` | Client가 접속할 서버 포트. 기본값은 `8787` |
| `announcement` | Client 홈 화면에 표시할 공지사항 |
| `admin_password_hash` | 관리자 설정 진입 비밀번호의 해시 |

### `manager_secrets.enc.json`

이 파일은 평문 JSON이 아니라 암호화된 JSON payload입니다. 원본 secrets 구조는 다음과 같습니다.

```json
{
  "wisdom_base_url": "",
  "wisdom_admin_id": "",
  "wisdom_admin_pw": ""
}
```

실제 운영 파일에는 이 값들이 암호화되어 저장됩니다. GitHub에는 실제 secrets 파일을 올리지 않고 `deploy/example_manager_secrets.json.template`만 포함합니다.

---

## 7. Client API 목록

Manager는 Client를 위해 다음 API를 제공합니다.

| Method | Route | 목적 | 내부 처리 |
|---|---|---|---|
| GET | `/health` | Manager 실행 상태와 설정 완료 여부 확인 | `ManagerService.health()` |
| GET | `/client-config` | Client 공지와 프로그램 정보 제공 | `ManagerService.get_client_config()` |
| POST | `/search` | 직원번호 검색 | `ManagerService.search()` |
| POST | `/refill` | 필요한 매수 충전 | `ManagerService.refill()` |
| POST | `/logout-user` | 프린터 서버 세션 로그아웃 | `ManagerService.logout_user()` |

API route는 HTTP 요청 파싱과 JSON 응답 변환만 담당합니다. 실제 업무 판단은 `ManagerService`에 있습니다.

---

## 8. WISDOM 통신 방식

Manager는 WISDOM과 직접 통신합니다. WISDOM 연동은 공개 API가 아니라 웹 요청과 HTML 응답을 기준으로 합니다.

```text
ManagerService
  → WisdomClient.login()
  → WisdomClient.search_user()
  → parser_utils.parse_search_result()
  → WisdomClient.increase_credit()
  → WisdomClient.logout_user()
```

개발 과정에서 브라우저 HAR 기록을 분석해 로그인, 검색, 매수 증가, 로그아웃 요청에 필요한 흐름을 확인했습니다. Manager는 그 흐름을 `wisdom_client.py`로 재현하고, HTML 응답 해석은 `parser_utils.py`에 맡깁니다.

WISDOM HTML 구조가 바뀌면 `parser_utils.py`의 row 선택자, 잔여 매수 파싱, 로그아웃 상태 판정이 영향을 받을 수 있습니다.

---

## 9. 검색 알고리즘

검색은 Client가 직원번호를 입력했을 때 실행됩니다.

```text
1. Client가 /search로 empId, pcName 전송
2. Manager가 empId 공백 여부 확인
3. WISDOM 클라이언트 생성
4. WISDOM 로그인
5. 직원번호 검색 요청
6. HTML 응답 파싱
7. 현재 잔여 매수와 서버 로그인 상태 계산
8. Manager 실행 세션에서 이미 충전한 사용자 여부 확인
9. reasonCode와 수치 필드를 Client에 반환
10. GUI 로그 기록
```

검색 성공 시 Manager는 잔여 매수와 목표 매수의 차이를 계산해 `refillAmount`를 내려줍니다. 단, Client의 검색 결과 화면은 참고 정보이며, 실제 충전 요청 시 Manager가 다시 WISDOM에서 현재 값을 조회합니다.

대표 reasonCode는 다음입니다.

| reasonCode | 의미 |
|---|---|
| `SEARCH_OK_REFILLABLE` | 검색 성공, 목표 매수까지 충전 가능 |
| `SEARCH_OK_NOT_REFILLABLE` | 검색 성공, 충전 불필요 |
| `ALREADY_REFILLED_IN_SESSION` | Manager 실행 세션에서 이미 충전한 사용자 |
| `NOT_FOUND` | 직원번호 검색 결과 없음 |
| `PARSE_FAILED` | 검색은 되었지만 현재 매수 파싱 실패 |

---

## 10. 충전 알고리즘

충전은 Manager에서 가장 중요한 흐름입니다.

```mermaid
flowchart TD
    A[/refill 요청] --> B{empId 입력됨?}
    B -- 아니오 --> X[INVALID_INPUT]
    B -- 예 --> C{운영 세션에서 이미 충전?}
    C -- 예 --> Y[ALREADY_REFILLED_IN_SESSION]
    C -- 아니오 --> D[WISDOM 로그인]
    D --> E[충전 직전 현재 매수 재조회]
    E --> F{사용자/매수 확인 가능?}
    F -- 아니오 --> Z[NOT_FOUND 또는 PARSE_FAILED]
    F -- 예 --> G{목표 매수 이상?}
    G -- 예 --> N[REFILL_NOT_NEEDED]
    G -- 아니오 --> H[목표값과 현재값 차이만큼 increase]
    H --> I[최종 재조회]
    I --> J[서버 로그아웃]
    J --> K{재조회 값 일치 + 로그아웃 성공?}
    K -- 예 --> L[REFILL_OK]
    K -- 아니오 --> M[LOGOUT_FAILED / VERIFY_FAILED / VERIFY_MISMATCH]
```

충전 목표값은 `TOPUP_LIMIT = 50`입니다. Manager는 `50 - 현재 매수`만큼 증가 요청을 보냅니다. Client가 충전량을 계산하지 않는 이유는 Client 화면 상태가 오래되었을 수 있기 때문입니다.

충전 성공 판정은 단순히 increase 요청이 예외 없이 끝났는지가 아니라, **충전 후 재조회 값이 기대값과 일치하는지**입니다. 로그아웃 성공 여부는 별도 상태로 유지합니다.

대표 reasonCode는 다음입니다.

| reasonCode | 의미 |
|---|---|
| `REFILL_OK` | 충전 반영, 최종 재조회 일치, 서버 로그아웃 완료 |
| `REFILL_NOT_NEEDED` | 이미 목표 매수 이상이라 충전하지 않음 |
| `LOGOUT_FAILED` | 충전은 반영되었지만 서버 로그아웃 실패 |
| `VERIFY_FAILED` | 충전 후 최종 재확인 실패 |
| `VERIFY_AND_LOGOUT_FAILED` | 최종 재확인과 로그아웃 모두 실패 |
| `VERIFY_MISMATCH` | 재조회 값이 예상과 다름 |
| `REFILL_ERROR` | 충전 처리 중 예상하지 못한 오류 |

---

## 11. 서버 로그아웃 알고리즘

서버 로그아웃은 WISDOM 프린터 서버 세션을 종료하기 위한 기능입니다.

```text
1. Client가 /logout-user로 empId 전송
2. Manager가 WISDOM 로그인
3. 해당 직원번호의 서버 로그아웃 요청
4. 응답에 검색 결과가 있으면 그대로 사용
5. 없으면 다시 search_user로 상태 확인
6. server_login_status가 로그아웃됨이거나 can_logout이 False이면 성공
7. reasonCode 반환
```

대표 reasonCode는 다음입니다.

| reasonCode | 의미 |
|---|---|
| `LOGOUT_OK` | 프린터 서버 세션 종료 확인 |
| `LOGOUT_VERIFY_FAILED` | 로그아웃 요청 후에도 종료 확인 실패 |
| `LOGOUT_ERROR` | 로그아웃 처리 중 예외 발생 |

---

## 12. reasonCode와 message 역할

Manager는 Client로 `reasonCode`와 `message`를 함께 보냅니다. 둘의 목적은 다릅니다.

| 필드 | 목적 |
|---|---|
| `reasonCode` | Client가 사용자 표시 문구를 만들 때 사용하는 1차 기준 |
| `message` | Manager GUI 로그, 디버깅, fallback, API 호환용 보조 설명 |

Client는 긴 `message` 문장을 다시 해석하지 않습니다. 표시 문구는 `reasonCode`와 수치 필드로 만듭니다. 따라서 Manager 로그 문구를 수정해도 Client의 정상 표시 로직은 유지됩니다.

---

## 13. 운영 세션 중복 충전 방지

`SessionRefillRegistry`는 Manager 실행 세션 동안 이미 충전한 직원번호를 메모리에 기록합니다.

```text
Client 재시작
  → 기록 유지

Manager 재시작
  → 기록 초기화
```

중복 충전 방지는 Client가 판단하지 않습니다. Client가 `/refill`을 보내면 Manager가 registry를 확인하고 `ALREADY_REFILLED_IN_SESSION`을 반환합니다.

현재 코드는 `REFILL_OK`인 경우에 registry를 기록합니다. 운영상 50매 초과 충전 가능성이 낮은 환경을 전제로 하며, 충전 반영 후 로그아웃 실패 같은 세부 케이스의 기록 정책은 이후 업데이트에서 조정할 수 있습니다.

---

## 14. 동시 요청 정책

현재 Manager는 Waitress가 있으면 Waitress 서버로 실행됩니다. 따라서 동시에 여러 요청이 들어올 수 있습니다. 별도의 전역 Lock으로 WISDOM 요청을 직렬화하지는 않습니다.

현재 설계 판단은 다음과 같습니다.

| 상황 | 현재 동작 |
|---|---|
| 같은 사용자가 거의 동시에 충전 | 운영상 확률이 낮다고 보고 별도 Lock 없음 |
| 서로 다른 사용자가 동시에 요청 | 각 요청이 별도 WisdomClient와 requests.Session을 사용 |
| WISDOM 충돌/타임아웃 | `AUTH_ERROR`, `NETWORK_ERROR`, `REFILL_ERROR`, `VERIFY_MISMATCH` 등 일반 오류로 표시 |

운영 중 동시 요청 오류가 실제로 문제가 되면 `ManagerService.refill()` 또는 WISDOM 관련 전체 요청에 Lock을 추가하는 방식으로 확장할 수 있습니다.

---

## 15. 프로그램 정보 편집/배포 흐름

```text
AdminDialog의 프로그램 정보 버튼
  → AboutEditorDialog 실행
  → Manager 정보 탭 편집
  → Client 정보 탭 편집
  → 저장
  → manager_about_content.json 저장
  → client_about_content.json 저장
  → Manager 정보 창은 manager_about_content.json 로드
  → Client는 /client-config의 aboutContent로 Client 정보 갱신
```

Client 정보가 Manager 쪽에서 편집되는 이유는 사용자 PC의 Client에서 설정이나 프로그램 설명을 직접 관리하지 않도록 하기 위해서입니다.

---

## 16. Manager 빌드 방법

개발 PC에서 실행 파일을 만들 때는 프로젝트 루트 또는 `manager_app` 폴더 기준으로 작업합니다. 실제 환경에 맞춰 경로를 조정할 수 있습니다.

```powershell
cd manager_app
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PyInstaller 예시:

```powershell
pyinstaller --noconfirm --windowed --onedir `
  --name "SOGANG Print Manager" `
  --icon "assets\app_icon.ico" `
  --add-data "assets;assets" `
  main.py
```

이 명령의 결과물은 `manager_app/dist/SOGANG Print Manager/` 아래에 생깁니다. `Manager_setup.iss`의 `MySourceDir`도 이 경로를 기준으로 합니다.

---

## 17. Inno Setup 설치 파일 생성

Manager 설치 파일은 `Manager_setup.iss`로 생성합니다.

```powershell
cd manager_app
ISCC Manager_setup.iss
```

설치 스크립트의 주요 동작은 다음입니다.

| 섹션 | 동작 |
|---|---|
| `[Files]` | PyInstaller 결과물, 아이콘, 기본 프로그램 정보 JSON 복사 |
| `[Dirs]` | `C:\ProgramData\SOGANG Print Manager` 폴더 생성 및 권한 설정 |
| `[Icons]` | 시작 메뉴, 바탕화면, 시작프로그램 바로가기 생성 |
| `[Code]` | 기존 설정 초기화 옵션 처리 |

설치 파일은 `manager_app/installer_output/` 아래에 생성됩니다. 이 폴더는 GitHub 커밋 대상이 아닙니다.

---

## 18. 설치 후 ProgramData 파일

Manager 설치 직후 또는 첫 실행 후 사용되는 파일은 다음입니다.

```text
C:\ProgramData\SOGANG Print Manager\
  manager_public_config.json        # 첫 실행/설정 저장 시 생성
  manager_secrets.enc.json          # WISDOM secrets 저장 시 생성
  manager_about_content.json        # 설치 시 example_manager_about_content.json에서 복사
  client_about_content.json         # 설치 시 example_client_about_content.json에서 복사
```

운영 PC에 실제로 필요한 것은 설치된 앱 파일과 위 ProgramData 파일입니다. GitHub에는 실제 운영 secrets를 올리지 않습니다.

---

## 19. 앱 아이콘 asset

Manager는 현재 다음 asset을 사용합니다.

```text
manager_app/assets/app_icon.ico
manager_app/assets/app_icon.png
```

현재 단계에서는 제공된 서강대학교 이미지 파일을 `app_icon.png`로 복사하고, 같은 이미지를 기준으로 `app_icon.ico`를 생성했습니다. 다음 정리에서는 앱 내부 이미지 참조를 `.ico` 하나로 통합해 `png` 의존을 줄일 계획입니다.

---

## 20. 주요 코드 파일 설명

| 파일 | 역할 |
|---|---|
| `main.py` | Manager 실행 진입점 |
| `app/gui_manager.py` | Manager 홈 GUI, 설정, 로그, 종료 흐름 |
| `app/admin_dialog.py` | 관리자 설정 입력/저장 창 |
| `app/about_editor_dialog.py` | Manager/Client 프로그램 정보 편집 창 |
| `app/app_service.py` | 검색, 충전, 로그아웃 업무 로직의 중심 |
| `app/server_app.py` | Flask route와 ManagerService 연결 |
| `app/server_runtime.py` | GUI와 별도로 서버를 실행/종료 |
| `app/tray_runtime.py` | Windows 트레이 아이콘과 종료 메뉴 |
| `app/wisdom_client.py` | WISDOM HTTP 요청 처리 |
| `app/parser_utils.py` | WISDOM HTML 응답 파싱 |
| `app/session_refill_registry.py` | Manager 실행 세션 내 중복 충전 방지 |
| `app/public_config_store.py` | 공개 설정 JSON 읽기/쓰기 |
| `app/secret_store.py` | WISDOM secrets 암호화 저장/로드 |
| `app/crypto_provider.py` | secrets 암호화/복호화 |
| `app/config_models.py` | 설정과 로그 dataclass 모델 |
| `app/health_presenter.py` | GUI 상태 표시 문구 생성 |
| `app/about_content_loader.py` | Manager/Client 프로그램 정보 JSON 로드/저장 |
| `app/admin_auth.py` | 관리자 비밀번호 해시 생성/검증 |
| `app/resource_utils.py` | 설치/개발 환경에서 asset 경로 처리 |
| `app/ui_style.py` | Tkinter 스타일 정의 |
