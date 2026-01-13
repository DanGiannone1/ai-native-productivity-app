# Setup Infrastructure for Prism MCP Server
# Creates all Azure infrastructure resources
# Usage: .\setup-infrastructure.ps1 -Environment <dev|prod> [-Location westus2]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory=$false)]
    [string]$Location = 'westus2'
)

# Dot-source common functions
. $PSScriptRoot\common.ps1

Write-Host "Setting up Prism MCP Server Infrastructure..." -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan

# Read .env file for the specified environment
$envVars = Read-EnvFile -Environment $Environment
if (-not $envVars) { exit 1 }

# Validate required variables
$required = @('RESOURCE_GROUP', 'ACR_NAME', 'CONTAINER_APP_ENV', 'COSMOS_DATABASE', 'COSMOS_CONTAINER')
if (-not (Test-RequiredVariables -EnvVars $envVars -Required $required)) { exit 1 }

# Extract variables
$RESOURCE_GROUP = $envVars['RESOURCE_GROUP']
$RESOURCE_GROUP_SHARED = Get-SharedResourceGroup -EnvVars $envVars
$ACR_NAME = $envVars['ACR_NAME']
$COSMOS_DATABASE = $envVars['COSMOS_DATABASE']
$COSMOS_CONTAINER = $envVars['COSMOS_CONTAINER']
$BASE_ENV_NAME = $envVars['CONTAINER_APP_ENV']

# Check Azure Login
$account = az account show 2>$null
if (-not $account) {
    Write-Host "ERROR: Please run 'az login'" -ForegroundColor Red
    exit 1
}

# --- Step 1: Resource Groups ---
Write-Host "`nStep 1: Creating Resource Groups" -ForegroundColor Cyan
$rgs = @($RESOURCE_GROUP_SHARED, $RESOURCE_GROUP) | Select-Object -Unique
foreach ($rg in $rgs) {
    if (Test-AzureResource -ResourceType "ResourceGroup" -ResourceName $rg) {
        Write-Host "  RG '$rg' exists" -ForegroundColor Gray
    } else {
        Write-Host "  Creating RG '$rg'..." -ForegroundColor Yellow
        az group create --name $rg --location $Location --output none
    }
}

# --- Step 2: Shared ACR ---
Write-Host "`nStep 2: Shared Container Registry" -ForegroundColor Cyan
if (Test-AzureResource -ResourceType "ACR" -ResourceName $ACR_NAME -ResourceGroup $RESOURCE_GROUP_SHARED) {
    Write-Host "  ACR '$ACR_NAME' exists" -ForegroundColor Gray
} else {
    Write-Host "  Creating ACR '$ACR_NAME'..." -ForegroundColor Yellow
    az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP_SHARED --sku Basic --admin-enabled true --location $Location --output none
}

# --- Step 3: Log Analytics ---
Write-Host "`nStep 3: Log Analytics Workspace" -ForegroundColor Cyan
$laName = "logs-prism-$Environment"
if (-not (Test-AzureResource -ResourceType "LogAnalytics" -ResourceName $laName -ResourceGroup $RESOURCE_GROUP)) {
    Write-Host "  Creating Log Analytics '$laName'..." -ForegroundColor Yellow
    az monitor log-analytics workspace create --workspace-name $laName --resource-group $RESOURCE_GROUP --location $Location --output none
}
$laId = az monitor log-analytics workspace show --workspace-name $laName --resource-group $RESOURCE_GROUP --query customerId -o tsv

# --- Step 4: Container App Environment ---
Write-Host "`nStep 4: Container App Environment" -ForegroundColor Cyan
$caeName = "$BASE_ENV_NAME-$Environment"
if (-not (Test-AzureResource -ResourceType "ContainerAppEnv" -ResourceName $caeName -ResourceGroup $RESOURCE_GROUP)) {
    Write-Host "  Creating Container App Env '$caeName'..." -ForegroundColor Yellow
    az containerapp env create --name $caeName --resource-group $RESOURCE_GROUP --location $Location --logs-workspace-id $laId --output none
}

# --- Step 5: Cosmos DB ---
Write-Host "`nStep 5: Cosmos DB Account" -ForegroundColor Cyan
$cosmosName = "prism-cosmos-$Environment"

if (-not (Test-AzureResource -ResourceType "CosmosDB" -ResourceName $cosmosName -ResourceGroup $RESOURCE_GROUP)) {
    Write-Host "  Creating Cosmos Account '$cosmosName'..." -ForegroundColor Yellow
    # Dev gets Free Tier, Prod gets Serverless
    if ($Environment -eq 'dev') {
        az cosmosdb create --name $cosmosName --resource-group $RESOURCE_GROUP --enable-free-tier true --output none
    } else {
        az cosmosdb create --name $cosmosName --resource-group $RESOURCE_GROUP --capabilities EnableServerless --output none
    }
}

# Database & Container
Write-Host "  Ensuring Database '$COSMOS_DATABASE'..." -ForegroundColor Gray
az cosmosdb sql database create --account-name $cosmosName --resource-group $RESOURCE_GROUP --name $COSMOS_DATABASE --output none 2>$null

# Single container for Prism (partitioned by userId)
Write-Host "  Ensuring Container '$COSMOS_CONTAINER' (PK: /userId)..." -ForegroundColor Gray
az cosmosdb sql container create --account-name $cosmosName --resource-group $RESOURCE_GROUP --database-name $COSMOS_DATABASE --name $COSMOS_CONTAINER --partition-key-path /userId --output none 2>$null

# --- Step 6: Get Cosmos Keys ---
Write-Host "`nStep 6: Retrieving Cosmos DB Connection Info" -ForegroundColor Cyan
$cosmosHost = az cosmosdb show --name $cosmosName --resource-group $RESOURCE_GROUP --query documentEndpoint -o tsv
$cosmosKey = az cosmosdb keys list --name $cosmosName --resource-group $RESOURCE_GROUP --query primaryMasterKey -o tsv

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "Infrastructure Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "Add these to your .env.$Environment file:" -ForegroundColor Cyan
Write-Host ""
Write-Host "COSMOS_HOST=$cosmosHost"
Write-Host "COSMOS_KEY=$cosmosKey"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Update .env.$Environment with the Cosmos credentials above"
Write-Host "  2. Deploy the MCP server: .\deployment\deploy.ps1 -Environment $Environment"
Write-Host "  3. Set environment variables: .\deployment\set-env-vars.ps1 -Environment $Environment"
