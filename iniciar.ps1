$ErrorActionPreference = "Stop"

$raiz = $PSScriptRoot
$dados = Join-Path $raiz ".postgres-data"
$log = Join-Path $raiz ".postgres.log"

function Ler-Env([string]$nome, [string]$padrao) {
    $arquivoEnv = Join-Path $raiz ".env"
    if (Test-Path $arquivoEnv) {
        $linha = Get-Content $arquivoEnv |
            Where-Object { $_ -match "^$([regex]::Escape($nome))=" } |
            Select-Object -First 1
        if ($linha) {
            return ($linha -split "=", 2)[1].Trim()
        }
    }
    return $padrao
}

function Encontrar-ExecutavelPostgres([string]$nome) {
    $comando = Get-Command $nome -ErrorAction SilentlyContinue
    if ($comando) {
        return $comando.Source
    }

    $pastas = Get-ChildItem "C:\Program Files\PostgreSQL" -Directory `
        -ErrorAction SilentlyContinue | Sort-Object Name -Descending
    foreach ($pasta in $pastas) {
        $candidato = Join-Path $pasta.FullName "bin\$nome.exe"
        if (Test-Path $candidato) {
            return $candidato
        }
    }
    return $null
}

$dbHost = Ler-Env "DB_HOST" "localhost"
$dbPort = Ler-Env "DB_PORT" "5432"
$pgIsReady = Encontrar-ExecutavelPostgres "pg_isready"
$pgCtl = Encontrar-ExecutavelPostgres "pg_ctl"

$bancoPronto = $false
if ($pgIsReady) {
    & $pgIsReady -h $dbHost -p $dbPort | Out-Null
    $bancoPronto = ($LASTEXITCODE -eq 0)
}

# Mantém compatibilidade com o banco portátil já inicializado neste projeto.
if (-not $bancoPronto -and (Test-Path $dados) -and $pgCtl -and $pgIsReady) {
    & $pgCtl -D $dados -l $log -o "-p $dbPort -h $dbHost" start
    for ($tentativa = 0; $tentativa -lt 15; $tentativa++) {
        & $pgIsReady -h $dbHost -p $dbPort | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $bancoPronto = $true
            break
        }
        Start-Sleep -Seconds 1
    }
}

if (-not $bancoPronto) {
    throw "PostgreSQL indisponível em ${dbHost}:${dbPort}. Inicie o serviço e confira o arquivo .env."
}

$python = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Ambiente Python não encontrado. Siga a instalação inicial descrita no README.md."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm não encontrado. Instale o Node.js LTS e siga o README.md."
}

Start-Process -FilePath "powershell.exe" -WorkingDirectory $raiz `
    -ArgumentList "-NoExit", "-Command", `
    ".\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload"

Start-Process -FilePath "powershell.exe" -WorkingDirectory (Join-Path $raiz "frontend") `
    -ArgumentList "-NoExit", "-Command", "npm run dev -- --host 127.0.0.1"

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

Write-Host "KitchenOS iniciado. Abra manualmente: http://127.0.0.1:5173"
