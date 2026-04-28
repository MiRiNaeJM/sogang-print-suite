$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

python -m PyInstaller --noconfirm `
  --distpath "dist" `
  --workpath "build\client" `
  "SOGANG_Print_Client.spec"

if (Get-Command ISCC -ErrorAction SilentlyContinue) {
  ISCC "client_app\Client_setup.iss"
}
else {
  Write-Warning "ISCC 명령을 찾을 수 없습니다. Inno Setup이 PATH에 등록되어 있지 않으면 설치 파일 생성은 건너뜁니다."
  Write-Warning "수동 실행: ISCC client_app\Client_setup.iss"
}