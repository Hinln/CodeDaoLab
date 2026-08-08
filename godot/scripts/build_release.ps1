param(
    [switch]$SkipTests,
    [string]$GodotBin = $env:GODOT_BIN
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$RepoRoot = (Resolve-Path (Join-Path $ProjectRoot '..')).Path
$ToolRoot = Join-Path $RepoRoot '.tools\godot'

if (-not $GodotBin) {
    $GodotBin = Join-Path $ToolRoot 'Godot_v4.7.1-stable_win64_console.exe'
}
if (-not (Test-Path -LiteralPath $GodotBin)) {
    throw "Godot console executable not found. Set GODOT_BIN: $GodotBin"
}
$RuntimeExe = Get-ChildItem -LiteralPath $ToolRoot -Filter 'Godot_v4.7.1-stable_win64.exe' -File | Select-Object -First 1
if (-not $RuntimeExe) {
    throw 'Official Godot Windows runtime executable not found.'
}

if (-not $SkipTests) {
    & (Join-Path $PSScriptRoot 'run_tests.ps1') -GodotBin $GodotBin
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$ExportDir = [IO.Path]::GetFullPath((Join-Path $ProjectRoot 'exports'))
$ExpectedParent = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\') + '\'
if (-not $ExportDir.StartsWith($ExpectedParent, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe export path: $ExportDir"
}
if (Test-Path -LiteralPath $ExportDir) {
    Remove-Item -LiteralPath $ExportDir -Recurse -Force
}
New-Item -ItemType Directory -Path $ExportDir | Out-Null

$BaseName = 'CodeDaoLab-Qingyun-Demo'
$PckPath = Join-Path $ExportDir "$BaseName.pck"
$ExePath = Join-Path $ExportDir "$BaseName.exe"

& $GodotBin --headless --path $ProjectRoot --export-pack 'Windows Desktop' $PckPath
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $PckPath)) {
    throw 'Godot PCK export failed.'
}
Copy-Item -LiteralPath $RuntimeExe.FullName -Destination $ExePath

New-Item -ItemType Directory -Path (Join-Path $ExportDir 'python_bridge'), (Join-Path $ExportDir 'data'), (Join-Path $ExportDir 'runtime\game') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'python_bridge\runner.py') -Destination (Join-Path $ExportDir 'python_bridge\runner.py')
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'data\challenges.json') -Destination (Join-Path $ExportDir 'data\challenges.json')
foreach ($File in @('__init__.py', 'config.py', 'sandbox.py', 'sandbox_bootstrap.py')) {
    Copy-Item -LiteralPath (Join-Path $RepoRoot "game\$File") -Destination (Join-Path $ExportDir "runtime\game\$File")
}

$Launcher = @(
    '@echo off',
    'setlocal',
    'where python >nul 2>nul',
    'if errorlevel 1 (',
    '  echo [CodeDaoLab] Python 3.10 or newer is required.',
    '  pause',
    '  exit /b 1',
    ')',
    'start "CodeDaoLab Qingyun Demo" "%~dp0CodeDaoLab-Qingyun-Demo.exe" --main-pack "%~dp0CodeDaoLab-Qingyun-Demo.pck"'
) -join "`r`n"
Set-Content -LiteralPath (Join-Path $ExportDir 'Start-Qingyun-Demo.bat') -Value $Launcher -Encoding ASCII

$ReleaseNotes = @(
    'CodeDaoLab: Qingyun Chapter - Godot Demo v0.1.0',
    '',
    'Run: double-click Start-Qingyun-Demo.bat.',
    'Requires: Windows 10/11 and Python 3.10 or newer.',
    'Godot is bundled. Player code runs in the packaged isolated Python bridge.',
    'Controls: WASD or arrow keys to move, E to interact.'
) -join "`r`n"
Set-Content -LiteralPath (Join-Path $ExportDir 'README.txt') -Value $ReleaseNotes -Encoding ASCII

$RequestPath = Join-Path $ExportDir 'bridge_smoke_request.json'
$ResponsePath = Join-Path $ExportDir 'bridge_smoke_response.json'
@{action='submit'; challenge_id='cycle_meridian'; code="for i in range(1, 4):`n    print(i)"} | ConvertTo-Json -Compress | Set-Content -LiteralPath $RequestPath -Encoding UTF8
python (Join-Path $ExportDir 'python_bridge\runner.py') $RequestPath $ResponsePath
if ($LASTEXITCODE -ne 0) { throw 'Packaged Python bridge smoke failed.' }
$BridgeResult = Get-Content -LiteralPath $ResponsePath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $BridgeResult.passed) { throw 'Packaged Python challenge verification failed.' }
Remove-Item -LiteralPath $RequestPath, $ResponsePath -Force

$SmokeProcess = Start-Process -FilePath $ExePath -ArgumentList @('--headless', '--main-pack', $PckPath, '--quit-after', '3') -WindowStyle Hidden -Wait -PassThru
if ($SmokeProcess.ExitCode -ne 0) { throw 'Packaged Godot runtime smoke failed.' }

$DistDir = Join-Path $ProjectRoot 'dist'
New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
$ZipPath = Join-Path $DistDir "$BaseName-v0.1.0.zip"
if (Test-Path -LiteralPath $ZipPath) { Remove-Item -LiteralPath $ZipPath -Force }
Compress-Archive -Path (Join-Path $ExportDir '*') -DestinationPath $ZipPath -CompressionLevel Optimal -ErrorAction Stop

$ZipFile = Get-Item -LiteralPath $ZipPath -ErrorAction Stop
if ($ZipFile.Length -le 0) { throw 'Release archive is empty.' }
$SizeMb = [math]::Round($ZipFile.Length / 1MB, 1)
Write-Host "RELEASE_BUILD_PASS: $ZipPath ($SizeMb MB)" -ForegroundColor Green
