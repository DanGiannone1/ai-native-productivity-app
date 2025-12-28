# run_local.ps1 - Local runner script for productivity MCP server
# Adapted from enterprise_architecture template

param(
    [string]$Command = "help"
)

# Get project root
$projectRoot = Get-Location
$env:PYTHONPATH = Join-Path $projectRoot "src"

# Detect virtual environment Python
$python = if ($IsWindows -or $env:OS -eq "Windows_NT") {
    ".\.venv\Scripts\python.exe"
} else {
    "./.venv/bin/python"
}

# --- Load Environment Variables ---
function Load-EnvFile {
    param([string]$Path)
    if (Test-Path $Path) {
        Get-Content $Path | ForEach-Object {
            if ($_ -match "^\s*([^#=]+?)\s*=\s*(.*)$") {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Remove surrounding quotes if present
                if ($value -match '^"(.*)"$' -or $value -match "^'(.*)'$") {
                    $value = $matches[1]
                }
                [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
        return $true
    }
    return $false
}

# Load environment-specific .env file (e.g., .env.dev, .env.prod)
$environment = $env:ENVIRONMENT
if (-not $environment) {
    $environment = "dev"  # Default to dev
}

$envSpecificFile = Join-Path $projectRoot ".env.$environment"
$fallbackFile = Join-Path $projectRoot ".env"

if (Load-EnvFile -Path $envSpecificFile) {
    Write-Host "Loaded environment from .env.$environment" -ForegroundColor Gray
} elseif (Load-EnvFile -Path $fallbackFile) {
    Write-Host "Loaded environment from .env (fallback)" -ForegroundColor Gray
} else {
    Write-Host "WARNING: No .env or .env.$environment file found" -ForegroundColor Yellow
    Write-Host "Run 'cp .env.example .env' and configure your settings." -ForegroundColor Yellow
}

# Command routing
switch ($Command) {
    "mcp" {
        Write-Host "Starting MCP server on http://localhost:8000..." -ForegroundColor Cyan
        & $python -m productivity_mcp.mcp_server
    }
    "setup" {
        Write-Host "Setting up Azure infrastructure..." -ForegroundColor Cyan
        & powershell scripts/setup-infrastructure.ps1 -Environment dev
    }
    "init" {
        Write-Host "Initializing Cosmos DB..." -ForegroundColor Cyan
        & $python scripts/init_cosmos.py
    }
    "seed" {
        Write-Host "Seeding sample data..." -ForegroundColor Cyan
        & $python scripts/seed_data.py
    }
    "test" {
        Write-Host "Running all tests..." -ForegroundColor Cyan
        & $python -m pytest tests/ -v
    }
    "test-unit" {
        Write-Host "Running unit tests..." -ForegroundColor Cyan
        & $python -m pytest tests/ -v -m unit
    }
    "test-integration" {
        Write-Host "Running integration tests..." -ForegroundColor Cyan
        & $python -m pytest tests/ -v -m integration
    }
    "test-local" {
        Write-Host "Running local service tests..." -ForegroundColor Cyan
        & $python scripts/test_local.py
    }
    "test-mcp" {
        Write-Host "Testing MCP server with curl..." -ForegroundColor Cyan
        Write-Host "Note: Server must be running in another terminal" -ForegroundColor Yellow
        & powershell scripts/test_mcp_curl.ps1
    }
    "lint" {
        Write-Host "Running ruff linter..." -ForegroundColor Cyan
        & $python -m ruff check src/productivity_mcp/ scripts/
    }
    "format" {
        Write-Host "Formatting code with ruff..." -ForegroundColor Cyan
        & $python -m ruff format src/productivity_mcp/ scripts/
    }
    "type-check" {
        Write-Host "Running mypy type checker..." -ForegroundColor Cyan
        & $python -m mypy src/productivity_mcp/
    }
    "check-all" {
        Write-Host "Running all checks (lint + type-check + test)..." -ForegroundColor Cyan
        Write-Host "`n[1/3] Linting..." -ForegroundColor Yellow
        & $python -m ruff check src/productivity_mcp/ scripts/
        Write-Host "`n[2/3] Type checking..." -ForegroundColor Yellow
        & $python -m mypy src/productivity_mcp/
        Write-Host "`n[3/3] Testing..." -ForegroundColor Yellow
        & $python -m pytest tests/ -v
    }
    "migrate-serverless" {
        Write-Host "Migrating to serverless Cosmos DB..." -ForegroundColor Cyan
        & powershell scripts/migrate-to-serverless.ps1 -Environment dev
    }
    "help" {
        Write-Host @"
Productivity MCP Server - Local Runner

Usage: .\run_local.ps1 <command>

Infrastructure:
  setup              Create Azure infrastructure (resource groups, Cosmos DB, etc.)
  migrate-serverless Migrate Cosmos DB to serverless mode (recommended for dev)
  init               Initialize Cosmos DB container (if not using setup)
  seed               Seed sample data for testing

Development:
  mcp                Start the FastMCP server (default port 8000)
  lint               Run ruff linter
  format             Format code with ruff
  type-check         Run mypy type checker
  check-all          Run all checks (lint + type-check + test)

Testing:
  test               Run all pytest tests
  test-unit          Run unit tests only (fast, no external deps)
  test-integration   Run integration tests (may use external services)
  test-local         Test services directly (without MCP)
  test-mcp           Test MCP server with curl (server must be running)

Setup:
  1. Run 'uv sync' to install dependencies
  2. Run '.\run_local.ps1 setup' to create Azure resources
  3. Run '.\run_local.ps1 test-local' to verify it works
  4. Run '.\run_local.ps1 seed' to add sample data
  5. Run '.\run_local.ps1 mcp' to start server

"@ -ForegroundColor White
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\run_local.ps1 help' for usage information." -ForegroundColor Yellow
    }
}
