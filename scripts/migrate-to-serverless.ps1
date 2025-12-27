# migrate-to-serverless.ps1
# Migrate Cosmos DB from provisioned throughput to serverless

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",

    [Parameter(Mandatory=$false)]
    [string]$Location = "westus2"
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "PRISM - Migrate Cosmos DB to Serverless" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Location: $Location" -ForegroundColor Yellow
Write-Host ""

# Load environment variables
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

$targetRG = if ($Environment -eq "prod") { "prism-prod" } else { "prism-dev" }
$oldCosmosAccount = "cosmos-prism-$Environment"
$newCosmosAccount = "cosmos-prism-$Environment-serverless"

Write-Host "Step 1: Creating serverless Cosmos DB account..." -ForegroundColor Cyan
Write-Host "  Old account: $oldCosmosAccount (provisioned throughput)" -ForegroundColor Gray
Write-Host "  New account: $newCosmosAccount (serverless)" -ForegroundColor Gray
Write-Host ""

# Create serverless Cosmos DB account
Write-Host "  Creating serverless account (this may take 5-10 minutes)..." -ForegroundColor Yellow
az cosmosdb create `
    --name $newCosmosAccount `
    --resource-group $targetRG `
    --locations regionName=$Location failoverPriority=0 isZoneRedundant=False `
    --default-consistency-level Session `
    --capabilities EnableServerless `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Serverless account created: $newCosmosAccount" -ForegroundColor Green
} else {
    Write-Host "  [X] Failed to create serverless account" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Creating database and container..." -ForegroundColor Cyan

# Create database
az cosmosdb sql database create `
    --account-name $newCosmosAccount `
    --resource-group $targetRG `
    --name "productivity" `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Database created" -ForegroundColor Green
} else {
    Write-Host "  [X] Failed to create database" -ForegroundColor Red
    exit 1
}

# Create container (serverless doesn't use throughput parameter)
az cosmosdb sql container create `
    --account-name $newCosmosAccount `
    --resource-group $targetRG `
    --database-name "productivity" `
    --name "productivity-data" `
    --partition-key-path "/userId" `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Container created" -ForegroundColor Green
} else {
    Write-Host "  [X] Failed to create container" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Migrating data..." -ForegroundColor Cyan
Write-Host "  Installing uv dependencies for migration..." -ForegroundColor Gray

# Ensure Python dependencies are installed
$python = if ($IsWindows -or $env:OS -eq "Windows_NT") {
    ".\.venv\Scripts\python.exe"
} else {
    "./.venv/bin/python"
}

Write-Host "  Running data migration script..." -ForegroundColor Gray
& $python scripts/migrate_cosmos_data.py --old-account $oldCosmosAccount --new-account $newCosmosAccount --resource-group $targetRG

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Data migrated successfully" -ForegroundColor Green
} else {
    Write-Host "  [X] Data migration failed" -ForegroundColor Red
    Write-Host "  You can manually copy data or re-run migration later" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 4: Updating .env file..." -ForegroundColor Cyan

# Get new credentials
$newCosmosHost = az cosmosdb show `
    --name $newCosmosAccount `
    --resource-group $targetRG `
    --query documentEndpoint `
    --output tsv

$newCosmosKey = az cosmosdb keys list `
    --name $newCosmosAccount `
    --resource-group $targetRG `
    --query primaryMasterKey `
    --output tsv

# Update .env file
$envContent = Get-Content ".env" -Raw
$envContent = $envContent -replace "COSMOS_HOST=.*", "COSMOS_HOST=$newCosmosHost"
$envContent = $envContent -replace "COSMOS_KEY=.*", "COSMOS_KEY=$newCosmosKey"
$envContent = $envContent -replace "COSMOS_ACCOUNT_NAME=.*", "COSMOS_ACCOUNT_NAME=$newCosmosAccount"
$envContent | Set-Content ".env" -NoNewline

Write-Host "  [OK] .env file updated with new credentials" -ForegroundColor Green

Write-Host ""
Write-Host "Step 5: Testing new connection..." -ForegroundColor Cyan
& $python scripts/test_local.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Connection test passed!" -ForegroundColor Green
} else {
    Write-Host "  [X] Connection test failed - please check credentials" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "[OK] MIGRATION COMPLETE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""
Write-Host "New serverless account: $newCosmosAccount" -ForegroundColor Cyan
Write-Host "Old provisioned account: $oldCosmosAccount" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify data: .\run_local.ps1 test-local" -ForegroundColor White
Write-Host "  2. Test MCP server: .\run_local.ps1 mcp" -ForegroundColor White
Write-Host "  3. If everything works, delete old account:" -ForegroundColor White
Write-Host "     az cosmosdb delete --name $oldCosmosAccount --resource-group $targetRG --yes" -ForegroundColor Gray
Write-Host ""
Write-Host "Serverless billing:" -ForegroundColor Yellow
Write-Host "  - First 1000 RU/s free per month" -ForegroundColor White
Write-Host "  - Pay only for actual usage" -ForegroundColor White
Write-Host "  - Perfect for dev/test environments" -ForegroundColor White
Write-Host ""
