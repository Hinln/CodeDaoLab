param(
    [string]$GodotBin = $env:GODOT_BIN
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$RepoRoot = (Resolve-Path (Join-Path $ProjectRoot '..')).Path

if (-not $GodotBin) {
    $GodotBin = Join-Path $RepoRoot '.tools\godot\Godot_v4.7.1-stable_win64_console.exe'
}
if (-not (Test-Path -LiteralPath $GodotBin)) {
    throw "Godot console executable not found. Set GODOT_BIN: $GodotBin"
}

& $GodotBin --headless --editor --path $ProjectRoot --quit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Scenes = @(
    'G1Smoke',
    'G2Smoke',
    'G3Smoke',
    'G4Smoke',
    'G5TutorSmoke',
    'G6PlaythroughSmoke',
    'V02ASpellcastingSmoke',
    'V02BOnboardingSmoke',
    'V02CCharacterNpcSmoke',
    'V02DWorldAtmosphereSmoke',
    'V02ETechniqueBossSmoke',
    'V02FTutorCompanionSmoke',
    'V02GFullFlowSmoke',
    'V02DisplaySmoke',
    'V021BeginnerGuidanceSmoke',
    'UIAllScenesBoundsSmoke'
)

foreach ($Scene in $Scenes) {
    Write-Host "`n=== $Scene ===" -ForegroundColor Cyan
    & $GodotBin --headless --path $ProjectRoot "res://scenes/tests/$Scene.tscn"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "`nALL GODOT TESTS PASSED (212 checks)" -ForegroundColor Green
