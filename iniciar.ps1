$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
Set-Location $raiz

# 1. Localiza automaticamente qualquer versão do PostgreSQL instalada
$pgBin = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin" -Directory -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending |
    Select-Object -First 1 -ExpandProperty FullName

if (-not $pgBin) {
    Write-Error "PostgreSQL não encontrado em 'C:\Program Files\PostgreSQL'. Instale o PostgreSQL e tente novamente."
}

$dados = Join-Path $raiz ".postgres-data"
$log = Join-Path $raiz ".postgres.log"

# 2. Cria o .env a partir do .env.example se ainda não existir
$envFile = Join-Path $raiz ".env"
$envExample = Join-Path $raiz ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host "Arquivo .env criado a partir do .env.example."
}

# 3. Inicializa o banco exclusivo do projeto na primeira execução
$primeiraVezBanco = -not (Test-Path $dados)
if ($primeiraVezBanco) {
    Write-Host "Inicializando banco de dados local em .postgres-data..."
    & (Join-Path $pgBin "initdb.exe") -D $dados -U kitchenos --encoding=UTF8 --no-locale -A trust
    Add-Content -Path (Join-Path $dados "postgresql.conf") -Value "`nport = 5433`nlisten_addresses = '127.0.0.1'"
}

# 4. Inicia o PostgreSQL exclusivo na porta 5433 se ainda não estiver rodando
& (Join-Path $pgBin "pg_isready.exe") -h 127.0.0.1 -p 5433 | Out-Null
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $pgBin "pg_ctl.exe") -D $dados -l $log start
}

# 5. Cria o banco 'restaurante' e roda DDL + Seeds na primeira execução
if ($primeiraVezBanco) {
    Write-Host "Criando banco 'restaurante' e populando tabelas iniciais..."
    & (Join-Path $pgBin "createdb.exe") -h 127.0.0.1 -p 5433 -U kitchenos restaurante
    & (Join-Path $pgBin "psql.exe") -h 127.0.0.1 -p 5433 -U kitchenos -d restaurante -f (Join-Path $raiz "database\ddl\01_create_tables.sql")
    & (Join-Path $pgBin "psql.exe") -h 127.0.0.1 -p 5433 -U kitchenos -d restaurante -f (Join-Path $raiz "database\seeds\02_insert_data.sql")
    & (Join-Path $pgBin "psql.exe") -h 127.0.0.1 -p 5433 -U kitchenos -d restaurante -f (Join-Path $raiz "database\ddl\02_create_embeddings.sql")
    & (Join-Path $pgBin "psql.exe") -h 127.0.0.1 -p 5433 -U kitchenos -d restaurante -f (Join-Path $raiz "database\ddl\03_create_chat.sql")
}

# 6. Cria a .venv e instala dependências Python se não existir
# 6. Cria a .venv e instala dependências Python se não existir
$pythonVenv = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonVenv)) {
    Write-Host "Criando ambiente virtual Python (.venv) e instalando dependências..."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -m venv (Join-Path $raiz ".venv")
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv (Join-Path $raiz ".venv")
    }
    else {
        Write-Error "Python não encontrado. Instale o Python 3.10+ e tente novamente."
    }
    & $pythonVenv -m pip install -r (Join-Path $raiz "backend\requirements.txt")
}
if ($primeiraVezBanco) {
    Write-Host "Gerando embeddings iniciais das receitas..."
    & $pythonVenv -c "from backend.embeddings import gerar_embeddings; gerar_embeddings()"
}

# 7. Instala dependências do frontend se node_modules não existir
$frontendDir = Join-Path $raiz "frontend"
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "Instalando dependências do frontend (npm install)..."
    Push-Location $frontendDir
    npm install
    Pop-Location
}

# 8. Abre backend e frontend em terminais separados
Start-Process -FilePath "powershell.exe" -WorkingDirectory $raiz `
    -ArgumentList "-NoExit", "-Command", `
    '$env:PGCLIENTENCODING="UTF8"; .\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload'

Start-Process -FilePath "powershell.exe" -WorkingDirectory $frontendDir `
    -ArgumentList "-NoExit", "-Command", "npm run dev"

# 9. Aguarda a API responder e abre o navegador em localhost
$apiPronta = $false
for ($tentativa = 0; $tentativa -lt 30; $tentativa++) {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/" -TimeoutSec 1 | Out-Null
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

Start-Process "http://localhost:5173"