# setup-infrastructure.ps1
# Azure infrastructure setup for Prism productivity system
# Based on enterprise_architecture 3-RG silo pattern

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",

    [Parameter(Mandatory=$false)]
    [string]$Location = "westus2"
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "PRISM PRODUCTIVITY SYSTEM - Infrastructure Setup" -ForegroundColor Cyan
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

# ============================================================================
# Resource Group Names
# ============================================================================
# Reuse existing shared services resource group
$rgShared = "soligence-shared-services"
$rgDev = "prism-dev"
$rgProd = "prism-prod"

# Select target RG based on environment
$targetRG = if ($Environment -eq "prod") { $rgProd } else { $rgDev }

# ============================================================================
# Resource Names
# ============================================================================
# Shared resources
$acrName = "acrprismshr"  # Must be globally unique, alphanumeric only
$acsName = "acs-prism-shared"

# Environment-specific resources
$cosmosAccountName = "cosmos-prism-$Environment"
$logAnalyticsName = "prism-logs-$Environment"
$appInsightsName = "prism-insights-$Environment"
$containerAppEnvName = "prism-env-$Environment"

Write-Host "Resource Groups:" -ForegroundColor Green
Write-Host "  Shared: $rgShared"
Write-Host "  Dev: $rgDev"
Write-Host "  Prod: $rgProd"
Write-Host "  Target: $targetRG"
Write-Host ""

# ============================================================================
# Step 1: Create Resource Groups
# ============================================================================
Write-Host "Step 1: Creating Resource Groups..." -ForegroundColor Cyan

# Shared RG - reuse existing
Write-Host "  Using existing shared resource group: $rgShared..."
$sharedExists = az group exists --name $rgShared
if ($sharedExists -eq "true") {
    Write-Host "    [OK] $rgShared exists (reusing)" -ForegroundColor Green
} else {
    Write-Host "    [X] Shared RG does not exist! Please check the name." -ForegroundColor Red
    exit 1
}

# Dev RG
Write-Host "  Creating dev resource group: $rgDev..."
az group create --name $rgDev --location $Location --output none
if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] $rgDev created" -ForegroundColor Green
} else {
    Write-Host "    [i] $rgDev may already exist" -ForegroundColor Yellow
}

# Prod RG
Write-Host "  Creating prod resource group: $rgProd..."
az group create --name $rgProd --location $Location --output none
if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] $rgProd created" -ForegroundColor Green
} else {
    Write-Host "    [i] $rgProd may already exist" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Step 2: Check Shared Resources (Optional - reuse existing if available)
# ============================================================================
Write-Host "Step 2: Checking Shared Resources..." -ForegroundColor Cyan

# Check if ACR exists (reuse existing acr0shared or create prism-specific)
Write-Host "  Checking for existing ACR in $rgShared..."
$existingAcr = az acr list --resource-group $rgShared --query "[0].name" --output tsv 2>$null

if ($existingAcr) {
    $acrName = $existingAcr
    Write-Host "    [OK] Reusing existing ACR: $acrName" -ForegroundColor Green
} else {
    Write-Host "  Creating Azure Container Registry: $acrName..."
    az acr create `
        --resource-group $rgShared `
        --name $acrName `
        --sku Basic `
        --location $Location `
        --admin-enabled true `
        --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] ACR created: $acrName" -ForegroundColor Green
    } else {
        Write-Host "    [i] ACR may already exist or failed to create" -ForegroundColor Yellow
    }
}

# Check if ACS exists (reuse or create)
Write-Host "  Checking for existing ACS in $rgShared..."
$existingAcs = az communication list --resource-group $rgShared --query "[0].name" --output tsv 2>$null

if ($existingAcs) {
    $acsName = $existingAcs
    Write-Host "    [OK] Reusing existing ACS: $acsName" -ForegroundColor Green
} else {
    Write-Host "  Creating Azure Communication Services: $acsName..."
    az communication create `
        --name $acsName `
        --resource-group $rgShared `
        --location "global" `
        --data-location "United States" `
        --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] ACS created: $acsName" -ForegroundColor Green
    } else {
        Write-Host "    [i] ACS may already exist or failed to create (optional for MVP)" -ForegroundColor Yellow
    }
}

Write-Host ""

# ============================================================================
# Step 3: Create Environment-Specific Resources
# ============================================================================
Write-Host "Step 3: Creating $Environment Environment Resources..." -ForegroundColor Cyan

# Cosmos DB Account
Write-Host "  Creating Cosmos DB account: $cosmosAccountName..."
Write-Host "    (This may take 5-10 minutes...)" -ForegroundColor Gray

az cosmosdb create `
    --name $cosmosAccountName `
    --resource-group $targetRG `
    --locations regionName=$Location failoverPriority=0 isZoneRedundant=False `
    --default-consistency-level Session `
    --capabilities EnableServerless `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] Cosmos DB account created: $cosmosAccountName" -ForegroundColor Green
} else {
    Write-Host "    [i] Cosmos DB may already exist or failed to create" -ForegroundColor Yellow
}

# Cosmos DB Database (will be created by init script, but can create here too)
Write-Host "  Creating Cosmos DB database: productivity..."
az cosmosdb sql database create `
    --account-name $cosmosAccountName `
    --resource-group $targetRG `
    --name "productivity" `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] Database created: productivity" -ForegroundColor Green
} else {
    Write-Host "    [i] Database may already exist" -ForegroundColor Yellow
}

# Cosmos DB Container
Write-Host "  Creating Cosmos DB container: productivity-data..."
az cosmosdb sql container create `
    --account-name $cosmosAccountName `
    --resource-group $targetRG `
    --database-name "productivity" `
    --name "productivity-data" `
    --partition-key-path "/userId" `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] Container created: productivity-data" -ForegroundColor Green
} else {
    Write-Host "    [i] Container may already exist" -ForegroundColor Yellow
}

# Log Analytics Workspace
Write-Host "  Creating Log Analytics workspace: $logAnalyticsName..."
az monitor log-analytics workspace create `
    --resource-group $targetRG `
    --workspace-name $logAnalyticsName `
    --location $Location `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] Log Analytics created: $logAnalyticsName" -ForegroundColor Green
} else {
    Write-Host "    [i] Log Analytics may already exist" -ForegroundColor Yellow
}

# Application Insights
Write-Host "  Creating Application Insights: $appInsightsName..."

# Get Log Analytics workspace ID
$workspaceId = az monitor log-analytics workspace show `
    --resource-group $targetRG `
    --workspace-name $logAnalyticsName `
    --query id `
    --output tsv

az monitor app-insights component create `
    --app $appInsightsName `
    --location $Location `
    --resource-group $targetRG `
    --workspace $workspaceId `
    --output none `
    --only-show-errors

if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] Application Insights created: $appInsightsName" -ForegroundColor Green
} else {
    Write-Host "    [i] Application Insights may already exist" -ForegroundColor Yellow
}

# Container Apps Environment
Write-Host "  Creating Container Apps Environment: $containerAppEnvName..."
az containerapp env create `
    --name $containerAppEnvName `
    --resource-group $targetRG `
    --location $Location `
    --logs-workspace-id $workspaceId `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] Container Apps Environment created: $containerAppEnvName" -ForegroundColor Green
} else {
    Write-Host "    [i] Container Apps Environment may already exist" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Step 4: Retrieve Secrets and Update .env
# ============================================================================
Write-Host "Step 4: Retrieving Secrets..." -ForegroundColor Cyan

# Get Cosmos DB connection info
Write-Host "  Retrieving Cosmos DB credentials..."
$cosmosHost = az cosmosdb show `
    --name $cosmosAccountName `
    --resource-group $targetRG `
    --query documentEndpoint `
    --output tsv

$cosmosKey = az cosmosdb keys list `
    --name $cosmosAccountName `
    --resource-group $targetRG `
    --query primaryMasterKey `
    --output tsv

Write-Host "    [OK] Cosmos DB Host: $cosmosHost" -ForegroundColor Green
Write-Host "    [OK] Cosmos DB Key: $($cosmosKey.Substring(0,20))..." -ForegroundColor Green

# Get ACS connection string (optional - for Phase 2)
Write-Host "  Retrieving ACS connection string..."
$acsConnectionString = az communication list-key `
    --name $acsName `
    --resource-group $rgShared `
    --query primaryConnectionString `
    --output tsv 2>$null

if ($acsConnectionString) {
    Write-Host "    [OK] ACS Connection String retrieved" -ForegroundColor Green
} else {
    Write-Host "    [i] ACS Connection String not available (optional)" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Step 5: Update .env file
# ============================================================================
Write-Host "Step 5: Updating .env file..." -ForegroundColor Cyan

$envContent = @"
# ============================================================================
# PRISM PRODUCTIVITY SYSTEM - Environment Variables
# ============================================================================
# Auto-generated by setup-infrastructure.ps1
# Environment: $Environment
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Environment
ENVIRONMENT=$Environment

# ============================================================================
# COSMOS DB
# ============================================================================
COSMOS_HOST=$cosmosHost
COSMOS_KEY=$cosmosKey
COSMOS_DATABASE=productivity
COSMOS_CONTAINER=productivity-data

# ============================================================================
# AUTHENTICATION (Dev Mode - No OAuth for MVP)
# ============================================================================
DISABLE_AUTH=true
DEFAULT_USER_ID=dev-user

# ============================================================================
# SCALEKIT OAUTH (Phase 2 - Not used in MVP)
# ============================================================================
# SCALEKIT_ENVIRONMENT_URL=
# SCALEKIT_CLIENT_ID=
# SCALEKIT_CLIENT_SECRET=
# SCALEKIT_RESOURCE_ID=
# MCP_URL=http://localhost:8000

# ============================================================================
# AZURE COMMUNICATION SERVICES (Phase 2 - Optional)
# ============================================================================
# EMAIL_CONNECTION_STRING=$acsConnectionString
# ACS_SENDER_ADDRESS=DoNotReply@<your-domain>.azurecomm.net

# ============================================================================
# M2M CLIENTS (Phase 2 - Not used in MVP)
# ============================================================================
# AUTHORIZED_M2M_CLIENTS=

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL=INFO

# ============================================================================
# RESOURCE GROUPS (Reference)
# ============================================================================
RESOURCE_GROUP_SHARED=$rgShared
RESOURCE_GROUP_DEV=$rgDev
RESOURCE_GROUP_PROD=$rgProd
RESOURCE_GROUP=$targetRG

# ============================================================================
# RESOURCE NAMES (Reference)
# ============================================================================
ACR_NAME=$acrName
COSMOS_ACCOUNT_NAME=$cosmosAccountName
CONTAINER_APP_ENV=$containerAppEnvName
LOG_ANALYTICS_WORKSPACE=$logAnalyticsName
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8 -Force
Write-Host "  [OK] .env file updated with Cosmos DB credentials" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Summary
# ============================================================================
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "[OK] INFRASTRUCTURE SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""
Write-Host "Resource Groups Created:" -ForegroundColor Cyan
Write-Host "  - $rgShared (shared services)" -ForegroundColor White
Write-Host "  - $rgDev (dev environment)" -ForegroundColor White
Write-Host "  - $rgProd (prod environment)" -ForegroundColor White
Write-Host ""
Write-Host "Resources Created in $targetRG" -ForegroundColor Cyan
Write-Host "  - Cosmos DB Account: $cosmosAccountName" -ForegroundColor White
Write-Host "  - Cosmos Database: productivity" -ForegroundColor White
Write-Host "  - Cosmos Container: productivity-data (partitioned by /userId)" -ForegroundColor White
Write-Host "  - Log Analytics: $logAnalyticsName" -ForegroundColor White
Write-Host "  - Application Insights: $appInsightsName" -ForegroundColor White
Write-Host "  - Container Apps Environment: $containerAppEnvName" -ForegroundColor White
Write-Host ""
Write-Host "Shared Resources in $rgShared" -ForegroundColor Cyan
Write-Host "  - Azure Container Registry: $acrName" -ForegroundColor White
Write-Host "  - Azure Communication Services: $acsName" -ForegroundColor White
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  - .env file updated with Cosmos credentials" -ForegroundColor White
Write-Host "  - Cosmos DB serverless mode (pay-per-use, 1000 RU/s free)" -ForegroundColor White
Write-Host "  - Container partitioned by userId for efficiency" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Run: .\run_local.ps1 test-local" -ForegroundColor White
Write-Host "  2. Run: .\run_local.ps1 seed" -ForegroundColor White
Write-Host "  3. Run: .\run_local.ps1 mcp" -ForegroundColor White
Write-Host "  4. Connect Claude Desktop to http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "View resources:" -ForegroundColor Yellow
Write-Host "  az resource list --resource-group $targetRG --output table" -ForegroundColor Gray
Write-Host ""

