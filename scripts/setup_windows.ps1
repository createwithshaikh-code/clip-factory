# One-time setup on Windows. In PowerShell, from the repo folder:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$Repo = (Get-Location).Path
if ($Repo -like "$env:WINDIR*") {
  Write-Host "This folder is inside $env:WINDIR. Clone the repo into your user folder instead:"
  Write-Host "  cd `$HOME; git clone https://github.com/createwithshaikh-code/clip-factory.git"
  exit 1
}

function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

if (-not (Have "winget")) { Write-Host "winget is missing. Update 'App Installer' from the Microsoft Store, then run again."; exit 1 }
if (-not (Have "ffmpeg")) { winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements }
if (-not (Have "uv"))     { winget install --id astral-sh.uv -e --accept-source-agreements --accept-package-agreements }
if (-not (Have "py"))     { winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements }
# yt-dlp needs a JavaScript runtime for YouTube downloads
if (-not (Have "deno"))   { winget install --id DenoLand.Deno -e --accept-source-agreements --accept-package-agreements }
# ctranslate2 / onnxruntime (used by faster-whisper) need the Visual C++ runtime
winget install --id Microsoft.VCRedist.2015+.x64 -e --accept-source-agreements --accept-package-agreements
if (-not (Have "git"))    { winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements }

# Refresh PATH for this window so the new tools are found
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

# Python 3.12 for the venv. "py" can exist without any Python installed (the new
# Python install manager), so test for a real runtime and install one if needed.
$ErrorActionPreference = "Continue"
function Py312Works { & py -3.12 -c "import sys" *> $null; return ($LASTEXITCODE -eq 0) }
if (-not (Py312Works)) {
  & py install 3.12 *> $null
  if (-not (Py312Works)) {
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
  }
}
$direct = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
if (Py312Works) { py -3.12 -m venv .venv }
elseif (Test-Path $direct) { & $direct -m venv .venv }
else { py -3 -m venv .venv }
if (-not (Test-Path .\.venv\Scripts\python.exe)) { Write-Host "Could not create .venv. Close this window, open a new PowerShell and run the script again."; exit 1 }
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "pip install failed. Copy the red error above and send it."; exit 1 }

if (-not [Environment]::GetEnvironmentVariable("ELEVENLABS_API_KEY", "User")) {
  $key = Read-Host "ElevenLabs API key (Enter to skip)"
  if ($key) { [Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", $key, "User") }
}
# Always point at this copy of the repo (it may have moved to another drive)
[Environment]::SetEnvironmentVariable("ELEVENLABS_MCP_BASE_PATH", $Repo, "User")
# Keep the Whisper models next to the repo instead of filling up C:
$hf = Join-Path $Repo ".models"
[Environment]::SetEnvironmentVariable("HF_HOME", $hf, "User")
$env:HF_HOME = $hf

.\.venv\Scripts\python.exe -m clipfactory check
Write-Host ""
Write-Host "Done. Next: add music to assets\music\<mood>\ and sound effects to assets\sfx\, then run 'claude' in this folder."
