#define MyAppName "서강대 프린터 매니저 SOGANG Print Manager"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "서강대학교 디지털정보처"
#define MyAppExeName "SOGANG Print Manager.exe"

#define MySourceDir "..\dist\SOGANG Print Manager"
#define MyOutputDir "..\installer_output"

; Manager 설치 프로그램의 기본 메타데이터와 설치 경로를 정의한다.
; Manager 서버 설정과 WISDOM 정보는 설치 후 앱 내부 초기 설정에서 입력한다.

[Setup]
AppId={{E02D2072-8552-46F6-8A16-37BF6B7E9289}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SOGANG Print Manager
DefaultGroupName=서강대학교 디지털정보처
DisableProgramGroupPage=yes
OutputDir={#MyOutputDir}
OutputBaseFilename=SOGANGPrintManagerSetup-{#MyAppVersion}
SetupIconFile=..\assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

; 앱 실행 파일, asset, Manager/Client 프로그램 정보 기본 JSON을 복사한다.
[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\app_icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\deploy\example_client_about_content.json"; DestDir: "{commonappdata}\SOGANG Print Manager"; DestName: "client_about_content.json"; Flags: ignoreversion onlyifdoesntexist
Source: "..\deploy\example_manager_about_content.json"; DestDir: "{commonappdata}\SOGANG Print Manager"; DestName: "manager_about_content.json"; Flags: ignoreversion onlyifdoesntexist

; 관리자 설정과 프로그램 정보 JSON을 저장할 ProgramData 폴더 권한을 연다.
[Dirs]
Name: "{commonappdata}\SOGANG Print Manager"; Permissions: users-modify

; 시작 메뉴, 바탕화면, 시작프로그램 바로가기를 같은 실행 파일로 연결한다.
[Icons]
Name: "{group}\SOGANG Print Manager"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\SOGANG Print Manager"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{commonstartup}\SOGANG Print Manager"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; \
  Description: "설치 완료 후 'SOGANG Print Manager' 실행"; \
  WorkingDir: "{app}"; \
  Flags: nowait postinstall skipifsilent

; 기존 Manager 설정을 유지하거나 초기화하는 설치 옵션을 처리한다.
[Code]
var
  OptionPage: TInputOptionWizardPage;

// 설치 마법사에 기존 설정 초기화 선택지를 추가한다.
procedure InitializeWizard;
begin
  OptionPage := CreateInputOptionPage(
    wpSelectDir,
    '기존 설정 처리',
    'Manager 설정 파일을 유지할지 초기화할지 선택하세요.',
    '비밀번호를 잊었거나 WISDOM/Manager 설정을 처음부터 다시 해야 하는 경우에만 체크하세요.',
    False,
    False
  );

  OptionPage.Add('기존 Manager 설정 초기화');
  OptionPage.Values[0] := False;
end;

// 설치 완료 단계에서 필요한 ProgramData 폴더를 만들고 선택 시 기존 설정을 삭제한다.
procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir: String;
  PublicConfigPath: String;
  SecretsPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigDir := ExpandConstant('{commonappdata}\SOGANG Print Manager');
    PublicConfigPath := ConfigDir + '\manager_public_config.json';
    SecretsPath := ConfigDir + '\manager_secrets.enc.json';

    ForceDirectories(ConfigDir);

    if OptionPage.Values[0] then
    begin
      DeleteFile(PublicConfigPath);
      DeleteFile(SecretsPath);

      DeleteFile(ExpandConstant('{userappdata}\SOGANG Print Manager\manager_public_config.json'));
      DeleteFile(ExpandConstant('{userappdata}\SOGANG Print Manager\manager_secrets.enc.json'));

      DeleteFile(ExpandConstant('{localappdata}\SOGANG Print Manager\manager_public_config.json'));
      DeleteFile(ExpandConstant('{localappdata}\SOGANG Print Manager\manager_secrets.enc.json'));
    end;
  end;
end;
