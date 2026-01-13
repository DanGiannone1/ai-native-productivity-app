# Common Deployment Functions for AI Productivity MCP Server
# Shared functions for all deployment scripts

# Read environment files and return hashtable
# Prioritizes .env.dev or .env.prod, falls back to .env for shared vars
function Read-EnvFile {
    param(
        [Parameter(Mandatory=$false)]
        [ValidateSet('dev', 'prod')]
        [string]$Environment = $null
    )

    # Define files to search for
    $filesToRead = @()
    if ($Environment) {
        $filesToRead += ".env.$Environment"
    }
    $filesToRead += ".env"

    $envVars = @{}

    # Get project root (assuming common.ps1 is in deployment/)
    $projectRoot = if ($PSScriptRoot.EndsWith("deployment")) { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }

    foreach ($fileName in $filesToRead) {
        $filePath = Join-Path $projectRoot $fileName
        if (Test-Path $filePath) {
            Write-Host "Reading $fileName..." -ForegroundColor Gray
            Get-Content $filePath | ForEach-Object {
                if ($_ -match '^\s*([^#][^=]*?)\s*=\s*(.*)$') {
                    $key = $matches[1].Trim()
                    $value = $matches[2].Trim().Trim('"').Trim("'")
                    # Don't overwrite if already set (prioritizes earlier files)
                    if (-not $envVars.ContainsKey($key)) {
                        $envVars[$key] = $value
                    }
                }
            }
        }
    }

    if ($envVars.Count -eq 0) {
        Write-Host "WARNING: No environment variables found in .env or .env.[env]" -ForegroundColor Yellow
    }

    return $envVars
}

# Get resource group name for environment
function Get-ResourceGroup {
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet('dev', 'prod')]
        [string]$Environment,

        [hashtable]$EnvVars
    )

    # Pattern: RESOURCE_GROUP is set in .env.dev or .env.prod
    $resourceGroup = $EnvVars['RESOURCE_GROUP']

    if (-not $resourceGroup) {
        Write-Host "ERROR: Could not determine Resource Group. Set RESOURCE_GROUP in .env.$Environment" -ForegroundColor Red
        exit 1
    }

    return $resourceGroup
}

# Get shared resource group (for ACR)
function Get-SharedResourceGroup {
    param(
        [hashtable]$EnvVars
    )

    $resourceGroup = $EnvVars['RESOURCE_GROUP_SHARED']
    if (-not $resourceGroup) {
        # Fallback: use RESOURCE_GROUP if shared not specified
        $resourceGroup = $EnvVars['RESOURCE_GROUP']
    }

    return $resourceGroup
}

# Validate required environment variables
function Test-RequiredVariables {
    param(
        [hashtable]$EnvVars,
        [string[]]$Required
    )

    $missing = $Required | Where-Object { -not $EnvVars.ContainsKey($_) }
    if ($missing) {
        Write-Host "ERROR: Missing required variables in .env: $($missing -join ', ')" -ForegroundColor Red
        return $false
    }
    return $true
}

# Helper function to check if resource exists
function Test-AzureResource {
    param(
        [string]$ResourceType,
        [string]$ResourceName,
        [string]$ResourceGroup
    )

    switch ($ResourceType) {
        "ResourceGroup" {
            $exists = az group exists --name $ResourceName -o tsv
            return $exists -eq "true"
        }
        "ACR" {
            $result = az acr show --name $ResourceName --resource-group $ResourceGroup 2>$null
            return $null -ne $result
        }
        "CosmosDB" {
            $result = az cosmosdb show --name $ResourceName --resource-group $ResourceGroup 2>$null
            return $null -ne $result
        }
        "LogAnalytics" {
            $result = az monitor log-analytics workspace show --workspace-name $ResourceName --resource-group $ResourceGroup 2>$null
            return $null -ne $result
        }
        "ContainerAppEnv" {
            $result = az containerapp env show --name $ResourceName --resource-group $ResourceGroup 2>$null
            return $null -ne $result
        }
        "ContainerApp" {
            $result = az containerapp show --name $ResourceName --resource-group $ResourceGroup 2>$null
            return $null -ne $result
        }
    }
    return $false
}

# Get ACR credentials
function Get-ACRCredentials {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ACRName,

        [Parameter(Mandatory=$true)]
        [string]$ResourceGroup
    )

    $creds = az acr credential show --name $ACRName --resource-group $ResourceGroup --query "{username:username, password:passwords[0].value}" -o json 2>$null | ConvertFrom-Json

    if ($LASTEXITCODE -ne 0 -or -not $creds) {
        return $null, $null
    }

    return $creds.username, $creds.password
}

# Restart Container App to apply configuration changes
function Restart-ContainerApp {
    param(
        [Parameter(Mandatory=$true)]
        [string]$AppName,

        [Parameter(Mandatory=$true)]
        [string]$ResourceGroup,

        [string]$StepDescription = "Restarting Container App"
    )

    Write-Host "$StepDescription..." -ForegroundColor Yellow

    $latestRevision = az containerapp revision list --name $AppName --resource-group $ResourceGroup --query "[0].name" -o tsv 2>$null

    if ($LASTEXITCODE -eq 0 -and $latestRevision) {
        az containerapp revision restart --name $AppName --resource-group $ResourceGroup --revision $latestRevision 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Container App restarted successfully" -ForegroundColor Green
            return $true
        }
    }

    Write-Host "Warning: Container App may need manual restart for changes to take effect" -ForegroundColor Yellow
    return $false
}
