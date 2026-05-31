Set-Location "$PSScriptRoot\..\backend"
if (-not (Test-Path .venv)) {
  python -m venv .venv
  .\.venv\Scripts\pip install -r requirements.txt
}
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
