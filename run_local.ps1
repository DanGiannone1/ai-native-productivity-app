# run_local.ps1 - Local runner script for productivity MCP server
# Adapted from enterprise_architecture template

param(
    [string]$Command = "help"
)

# Get project root
$projectRoot = Get-Location
$env:PYTHONPATH = Join-Path $projectRoot "backend"

# Detect virtual environment Python
$python = if ($IsWindows -or $env:OS -eq "Windows_NT") {
    ".\.venv\Scripts\python.exe"
} else {
    "./.venv/bin/python"
}

# Load .env file
if (Test-Path ".env") {
    Write-Host "Loading environment from .env..." -ForegroundColor Green
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
} else {
    Write-Host "Warning: .env file not found. Using environment defaults." -ForegroundColor Yellow
    Write-Host "Run 'cp .env.example .env' and configure your settings." -ForegroundColor Yellow
}

# Command routing
switch ($Command) {
    "mcp" {
        Write-Host "Starting MCP server on http://localhost:8000..." -ForegroundColor Cyan
        & $python -m backend.mcp_server
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
        Write-Host "Running tests..." -ForegroundColor Cyan
        & $python -m pytest tests/ -v
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
        & $python -m ruff check backend/ scripts/
    }
    "format" {
        Write-Host "Formatting code with ruff..." -ForegroundColor Cyan
        & $python -m ruff format backend/ scripts/
    }
    "migrate-serverless" {
        Write-Host "Migrating to serverless Cosmos DB..." -ForegroundColor Cyan
        & powershell scripts/migrate-to-serverless.ps1 -Environment dev
    }
    "help" {
        Write-Host @"
Productivity MCP Server - Local Runner

Usage: .\run_local.ps1 <command>

Commands:
  setup              Create Azure infrastructure (resource groups, Cosmos DB, etc.)
  migrate-serverless Migrate Cosmos DB to serverless mode (recommended for dev)
  mcp                Start the FastMCP server (default port 8000)
  init               Initialize Cosmos DB container (if not using setup)
  seed               Seed sample data for testing
  test               Run pytest test suite
  test-local         Test services directly (without MCP)
  test-mcp           Test MCP server with curl (server must be running)
  lint               Run ruff linter
  format             Format code with ruff
  help               Show this help message

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
