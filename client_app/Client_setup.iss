#define MyAppName "서강대 프린터 클라이언트 SOGANG Print Client"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "서강대학교 디지털정보처"
#define MyAppExeName "SOGANG Print Client.exe"

#define MySourceDir "..\dist\SOGANG Print Client"
#define MyOutputDir "..\installer_output"

; Client 설치 프로그램의 기본 메타데이터와 설치 경로를 정의한다.
; PyInstaller 결과물은 MySourceDir 경로에 미리 생성되어 있어야 한다.

[Setup]
AppId={{0C4E77D8-4F67-4B85-B1B4-553AC9988A51}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SOGANG Print Client
DefaultGroupName=서강대학교 디지털정보처
DisableProgramGroupPage=yes
OutputDir={#MyOutputDir}
OutputBaseFilename=SOGANGPrintClientSetup-{#MyAppVersion}
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

; 앱 실행 파일과 Client 런타임에 필요한 asset, 기본 프로그램 정보 파일을 복사한다.
[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\app_icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\app_icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\deploy\example_client_about_content.json"; DestDir: "{commonappdata}\SOGANG Print Client"; DestName: "about_content.json"; Flags: ignoreversion onlyifdoesntexist

; Client 설정 파일을 일반 사용자 권한으로 갱신할 수 있도록 ProgramData 폴더 권한을 연다.
[Dirs]
Name: "{commonappdata}\SOGANG Print Client"; Permissions: users-modify

; 시작 메뉴, 바탕화면, 시작프로그램 바로가기를 같은 실행 파일로 연결한다.
[Icons]
Name: "{group}\SOGANG Print Client"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\SOGANG Print Client"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{commonstartup}\SOGANG Print Client"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; \
  Description: "설치 완료 후 'SOGANG Print Client' 실행"; \
  WorkingDir: "{app}"; \
  Flags: nowait postinstall skipifsilent

; 설치 중 Manager IP/Port를 입력받아 client_config.json을 생성한다.
[Code]
var
  ManagerPage: TInputQueryWizardPage;
  OptionPage: TInputOptionWizardPage;

; 포트와 IPv4 각 구간이 숫자로만 구성되었는지 검사한다.
function IsDigitsOnly(Value: String): Boolean;
var
  I: Integer;
begin
  Result := Value <> '';

  for I := 1 to Length(Value) do
  begin
    if (Value[I] < '0') or (Value[I] > '9') then
    begin
      Result := False;
      Exit;
    end;
  end;
end;

; Client 설정은 숫자 IPv4만 받도록 제한해 잘못된 URL 입력을 줄인다.
function ValidateIPv4(Value: String): Boolean;
var
  S: String;
  Part: String;
  DotPos: Integer;
  Index: Integer;
  Number: Integer;
begin
  Result := False;
  S := Trim(Value);

  if Pos('http://', Lowercase(S)) = 1 then Exit;
  if Pos('https://', Lowercase(S)) = 1 then Exit;

  for Index := 1 to 4 do
  begin
    DotPos := Pos('.', S);

    if Index < 4 then
    begin
      if DotPos = 0 then Exit;
      Part := Copy(S, 1, DotPos - 1);
      Delete(S, 1, DotPos);
    end
    else
    begin
      if Pos('.', S) > 0 then Exit;
      Part := S;
    end;

    if not IsDigitsOnly(Part) then Exit;

    Number := StrToIntDef(Part, -1);
    if (Number < 0) or (Number > 255) then Exit;
  end;

  Result := True;
end;

; Manager 서버 포트가 TCP 포트 범위 안에 있는지 확인한다.
function ValidatePort(Value: String): Boolean;
var
  Port: Integer;
begin
  Port := StrToIntDef(Trim(Value), -1);
  Result := (Port >= 1) and (Port <= 65535);
end;

; 입력받은 Manager URL을 JSON 문자열에 안전하게 넣기 위해 이스케이프한다.
function JsonEscape(Value: String): String;
begin
  Result := Value;
  StringChangeEx(Result, '\', '\\', True);
  StringChangeEx(Result, '"', '\"', True);
  StringChangeEx(Result, #13#10, '\n', True);
  StringChangeEx(Result, #13, '\n', True);
  StringChangeEx(Result, #10, '\n', True);
end;

; 설치 마법사에서 Manager 주소 입력 페이지와 설정 초기화 선택지를 만든다.
procedure InitializeWizard;
begin
  ManagerPage := CreateInputQueryPage(
    wpSelectDir,
    'Manager 주소 설정',
    'Client가 접속할 Manager 주소를 입력하세요.',
    'http:// 는 자동으로 추가됩니다. IP 주소와 포트만 입력하세요.'
  );

  ManagerPage.Add('http://  IP 주소:', False);
  ManagerPage.Add('포트:', False);
  ManagerPage.Values[1] := '8787';

  OptionPage := CreateInputOptionPage(
    ManagerPage.ID,
    '기존 설정 처리',
    '클라이언트 설정 파일을 새 입력값으로 다시 만들지 선택하세요.',
    '기존 매니저 주소가 잘못되었거나 매니저 PC가 변경된 경우 체크하세요.',
    False,
    False
  );

  OptionPage.Add('기존 클라이언트 설정 초기화');
  OptionPage.Values[0] := False;
end;

; 다음 단계로 넘어가기 전에 Manager 주소 입력값을 검증한다.
function NextButtonClick(CurPageID: Integer): Boolean;
var
  IpValue: String;
  PortValue: String;
begin
  Result := True;

  if CurPageID = ManagerPage.ID then
  begin
    IpValue := Trim(ManagerPage.Values[0]);
    PortValue := Trim(ManagerPage.Values[1]);

    if not ValidateIPv4(IpValue) then
    begin
      MsgBox('IP 주소는 숫자 IPv4 형식으로 입력하세요. 예: 192.168.0.25', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if not ValidatePort(PortValue) then
    begin
      MsgBox('포트는 1~65535 사이의 숫자로 입력하세요.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
end;

; 설치 완료 단계에서 client_config.json을 생성하거나 기존 설정을 유지한다.
procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir: String;
  ConfigPath: String;
  ManagerUrl: String;
  Json: String;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigDir := ExpandConstant('{commonappdata}\SOGANG Print Client');
    ConfigPath := ConfigDir + '\client_config.json';

    if OptionPage.Values[0] or (not FileExists(ConfigPath)) then
    begin
      DeleteFile(ConfigPath);
      DeleteFile(ExpandConstant('{userappdata}\SOGANG Print Client\client_config.json'));
      DeleteFile(ExpandConstant('{localappdata}\SOGANG Print Client\client_config.json'));

      ForceDirectories(ConfigDir);

      ManagerUrl := 'http://' + Trim(ManagerPage.Values[0]) + ':' + Trim(ManagerPage.Values[1]);

      Json := '{' + #13#10 +
        '  "manager_base_url": "' + JsonEscape(ManagerUrl) + '"' + #13#10 +
        '}';

      SaveStringToFile(ConfigPath, Json, False);
    end;
  end;
end;
