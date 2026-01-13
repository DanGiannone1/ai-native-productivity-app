# Deploy Script for Prism MCP Server
# Builds and deploys the MCP server to Azure Container Apps
# Usage: .\deploy.ps1 -Environment <dev|prod> [-Version v1.0.0]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory=$false)]
    [string]$Version = 'latest'
)

# Dot-source common functions
. $PSScriptRoot\common.ps1

Write-Host "Deploying Prism MCP Server for environment: $Environment" -ForegroundColor Cyan
Write-Host ""

# Read environment files (.env.[env] first, then .env for shared vars)
$envVars = Read-EnvFile -Environment $Environment
if (-not $envVars) { exit 1 }

# Validate required variables
$required = @('ACR_NAME', 'ACR_SERVER', 'CONTAINER_APP_ENV', 'MCP_APP_NAME')
if (-not (Test-RequiredVariables -EnvVars $envVars -Required $required)) { exit 1 }

# Get resource groups
$RESOURCE_GROUP = Get-ResourceGroup -Environment $Environment -EnvVars $envVars
$RESOURCE_GROUP_SHARED = Get-SharedResourceGroup -EnvVars $envVars

if (-not $RESOURCE_GROUP) {
    Write-Host "ERROR: Could not determine resource group for environment '$Environment'" -ForegroundColor Red
    exit 1
}

# Get ACR and image prefix
$ACR_NAME = $envVars['ACR_NAME']
$ACR_SERVER = $envVars['ACR_SERVER']
$IMAGE_PREFIX = if ($envVars['IMAGE_PREFIX']) { $envVars['IMAGE_PREFIX'] } else { 'prism' }

# Get Container App Environment
$CONTAINER_APP_ENV = "$($envVars['CONTAINER_APP_ENV'])-$Environment"

# MCP App Name
$MCP_APP_NAME_BASE = $envVars['MCP_APP_NAME']
$MCP_APP_NAME = "$MCP_APP_NAME_BASE-$Environment"

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Environment: $Environment"
Write-Host "  Version: $Version"
Write-Host "  Resource Group: $RESOURCE_GROUP"
Write-Host "  Container App Env: $CONTAINER_APP_ENV"
Write-Host "  App Name: $MCP_APP_NAME"
Write-Host ""

# Login to ACR
Write-Host "Logging into ACR..." -ForegroundColor Yellow
az acr login --name $ACR_NAME
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to login to ACR" -ForegroundColor Red
    exit 1
}

# Get ACR credentials
$ACR_USERNAME = az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP_SHARED --query "username" -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP_SHARED --query "passwords[0].value" -o tsv

if (-not $ACR_USERNAME -or -not $ACR_PASSWORD) {
    Write-Host "Failed to get ACR credentials" -ForegroundColor Red
    exit 1
}

# Build image tag
if ($Version -eq 'latest') {
    $IMAGE_TAG = "${ACR_SERVER}/${IMAGE_PREFIX}-mcp:${Environment}-latest"
} else {
    $IMAGE_TAG = "${ACR_SERVER}/${IMAGE_PREFIX}-mcp:${Version}-${Environment}"
}

# Get project root
$projectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "Building MCP server image..." -ForegroundColor Yellow
docker build -f "$projectRoot\Dockerfile" -t $IMAGE_TAG $projectRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build MCP image" -ForegroundColor Red
    exit 1
}

Write-Host "Pushing MCP image to ACR..." -ForegroundColor Yellow
docker push $IMAGE_TAG
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to push MCP image" -ForegroundColor Red
    exit 1
}

# Check if Container App exists
$appExists = $null -ne (az containerapp show --name $MCP_APP_NAME --resource-group $RESOURCE_GROUP 2>$null)

if (-not $appExists) {
    Write-Host "Creating Container App..." -ForegroundColor Yellow
    az containerapp create `
        --name $MCP_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --environment $CONTAINER_APP_ENV `
        --image $IMAGE_TAG `
        --registry-server $ACR_SERVER `
        --registry-username $ACR_USERNAME `
        --registry-password $ACR_PASSWORD `
        --target-port 8000 `
        --ingress external `
        --min-replicas 0 `
        --max-replicas 1 `
        --tags "Environment=$Environment" "Service=prism-mcp"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create Container App" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Updating Container App..." -ForegroundColor Yellow
    az containerapp update --name $MCP_APP_NAME --resource-group $RESOURCE_GROUP --image $IMAGE_TAG
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to update Container App" -ForegroundColor Red
        exit 1
    }
}

# Get the app URL
$APP_URL = az containerapp show --name $MCP_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "MCP Server deployed successfully!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "  URL: https://$APP_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Set environment variables: .\deployment\set-env-vars.ps1 -Environment $Environment"
Write-Host "  2. Test the endpoint: curl https://$APP_URL/health"
Write-Host "  3. Connect to Microsoft Foundry Agent Service (optional)"
Write-Host ""
