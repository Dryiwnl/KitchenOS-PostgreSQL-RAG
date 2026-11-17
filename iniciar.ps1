$ErrorActionPreference = "Stop"

$raiz = $PSScriptRoot
$pgRoot = "C:\Program Files\PostgreSQL\18\bin"
$dados = Join-Path $raiz ".postgres-data"
$log = Join-Path $raiz ".postgres.log"

& (Join-Path $pgRoot "pg_isready.exe") -h 127.0.0.1 -p 55432 | Out-Null
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $pgRoot "pg_ctl.exe") -D $dados -l $log `
        -o '"-p 55432 -h 127.0.0.1"' start
}

Start-Process -FilePath "powershell.exe" -WorkingDirectory $raiz `
    -ArgumentList "-NoExit", "-Command", `
    ".\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload"

Start-Process -FilePath "powershell.exe" -WorkingDirectory (Join-Path $raiz "frontend") `
    -ArgumentList "-NoExit", "-Command", "npm run dev"

$apiPronta = $false
for ($tentativa = 0; $tentativa -lt 30; $tentativa++) {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/" `
            -TimeoutSec 1 | Out-Null
        $apiPronta = $true
        break
    }
    catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $apiPronta) {
    Write-Warning "O backend ainda não respondeu. Consulte o terminal aberto."
}

Start-Process "http://127.0.0.1:5173"
