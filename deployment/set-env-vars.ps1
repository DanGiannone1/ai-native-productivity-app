# Set Environment Variables for AI Productivity MCP Server
# Configures secrets and environment variables on the Azure Container App
# Usage: .\set-env-vars.ps1 -Environment <dev|prod>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'prod')]
    [string]$Environment
)

# Dot-source common functions
. $PSScriptRoot\common.ps1

Write-Host "Setting environment variables for AI Productivity MCP Server ($Environment)..." -ForegroundColor Cyan
Write-Host ""

# Read environment files
$envVars = Read-EnvFile -Environment $Environment
if (-not $envVars) { exit 1 }

# Validate required variables
$required = @('MCP_APP_NAME', 'COSMOS_HOST', 'COSMOS_KEY', 'COSMOS_DATABASE', 'COSMOS_CONTAINER')
if (-not (Test-RequiredVariables -EnvVars $envVars -Required $required)) { exit 1 }

# Get resource group and app name
$RESOURCE_GROUP = Get-ResourceGroup -Environment $Environment -EnvVars $envVars
$MCP_APP_NAME = "$($envVars['MCP_APP_NAME'])-$Environment"

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Resource Group: $RESOURCE_GROUP"
Write-Host "  App Name: $MCP_APP_NAME"
Write-Host ""

# Step 1: Set secrets (sensitive values)
Write-Host "Setting secrets..." -ForegroundColor Yellow
az containerapp secret set `
    --name $MCP_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --secrets `
        "cosmos-key=$($envVars['COSMOS_KEY'])"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to set secrets" -ForegroundColor Red
    exit 1
}

# Step 2: Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow

# Build environment variable list
$envVarsList = @(
    "ENVIRONMENT=$Environment"
    "COSMOS_HOST=$($envVars['COSMOS_HOST'])"
    "COSMOS_KEY=secretref:cosmos-key"
    "COSMOS_DATABASE=$($envVars['COSMOS_DATABASE'])"
    "COSMOS_CONTAINER=$($envVars['COSMOS_CONTAINER'])"
    "DISABLE_AUTH=true"
    "DEFAULT_USER_ID=demo-user"
    "LOG_LEVEL=INFO"
)

# Add optional variables if present
if ($envVars['LANGSMITH_API_KEY']) {
    az containerapp secret set `
        --name $MCP_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --secrets "langsmith-key=$($envVars['LANGSMITH_API_KEY'])"
    $envVarsList += "LANGSMITH_API_KEY=secretref:langsmith-key"
    $envVarsList += "LANGSMITH_TRACING=true"
}

# Apply environment variables
az containerapp update `
    --name $MCP_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --set-env-vars $envVarsList

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to set environment variables" -ForegroundColor Red
    exit 1
}

# Step 3: Restart to apply changes
Write-Host ""
Restart-ContainerApp -AppName $MCP_APP_NAME -ResourceGroup $RESOURCE_GROUP -StepDescription "Restarting to apply changes"

# Get the app URL
$APP_URL = az containerapp show --name $MCP_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "Environment variables configured successfully!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "  App URL: https://$APP_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration applied:" -ForegroundColor Cyan
Write-Host "  - COSMOS_HOST, COSMOS_DATABASE, COSMOS_CONTAINER"
Write-Host "  - COSMOS_KEY (stored as secret)"
Write-Host "  - DISABLE_AUTH=true (no authentication for demos)"
Write-Host "  - DEFAULT_USER_ID=demo-user"
Write-Host ""
Write-Host "To connect to Microsoft Foundry Agent Service:" -ForegroundColor Cyan
Write-Host "  1. Go to Foundry portal > Agent Builder"
Write-Host "  2. Add Tool > Custom > Model Context Protocol (MCP)"
Write-Host "  3. Enter endpoint: https://$APP_URL"
Write-Host "  4. Auth: None"
Write-Host ""
