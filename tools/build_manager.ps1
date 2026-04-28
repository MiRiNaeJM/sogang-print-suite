$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

python -m PyInstaller --noconfirm `
  --distpath "dist" `
  --workpath "build\manager" `
  "SOGANG_Print_Manager.spec"

if (Get-Command ISCC -ErrorAction SilentlyContinue) {
  ISCC "manager_app\Manager_setup.iss"
}
else {
  Write-Warning "ISCC 명령을 찾을 수 없습니다. Inno Setup이 PATH에 등록되어 있지 않으면 설치 파일 생성은 건너뜁니다."
  Write-Warning "수동 실행: ISCC manager_app\Manager_setup.iss"
}