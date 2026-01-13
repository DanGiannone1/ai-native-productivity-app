# Deployment - Azure Container Apps

**Source of truth for infrastructure provisioning and deployment.**

---

## Overview

The AI Productivity MCP Server deploys to Azure Container Apps with Cosmos DB backend. This guide covers both local development and cloud deployment.

**Deployment Strategy:**
- **Local Development**: Docker Compose with Cosmos DB connection
- **Dev Environment**: Azure Container Apps (serverless), Cosmos DB Free Tier
- **Prod Environment**: Azure Container Apps (serverless), Cosmos DB Serverless

---

## Quick Start

### Prerequisites

1. Azure CLI installed (`az --version`)
2. Docker installed (`docker --version`)
3. Logged into Azure (`az login`)
4. PowerShell 7+ (`pwsh --version`)

### Setup Infrastructure

```powershell
# 1. Copy example environment files
cp example.env .env
cp example.env.dev .env.dev

# 2. Edit .env and .env.dev with your values
# (Update ACR_NAME, RESOURCE_GROUP, etc.)

# 3. Provision Azure resources
.\deployment\setup-infrastructure.ps1 -Environment dev -Location westus2

# 4. Copy the COSMOS_HOST and COSMOS_KEY output into .env.dev

# 5. Deploy the MCP server
.\deployment\deploy.ps1 -Environment dev

# 6. Configure environment variables
.\deployment\set-env-vars.ps1 -Environment dev
```

---

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `setup-infrastructure.ps1` | Create Azure resources (Cosmos DB, Container App Env, ACR, Log Analytics) |
| `deploy.ps1` | Build Docker image and deploy to Azure Container Apps |
| `set-env-vars.ps1` | Configure secrets and environment variables on Container App |
| `common.ps1` | Shared PowerShell functions |

---

## Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Shared Resource Group (ai-productivity-shared)             │
│  └── Azure Container Registry (ACR)                         │
├─────────────────────────────────────────────────────────────┤
│  Dev Resource Group (ai-productivity-dev)                   │
│  ├── Cosmos DB Account (ai-prod-cosmos-dev)                 │
│  │   ├── Database: productivity                             │
│  │   └── Container: productivity-data (PK: /userId)         │
│  ├── Log Analytics Workspace (logs-ai-prod-dev)             │
│  ├── Container App Environment (ai-prod-env-dev)            │
│  └── Container App (ai-prod-mcp-dev)                        │
├─────────────────────────────────────────────────────────────┤
│  Prod Resource Group (ai-productivity-prod) - Same structure│
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Configuration

### Environment Files

| File | Purpose |
|------|---------|
| `.env` | Shared settings (ACR name, database names) |
| `.env.dev` | Dev-specific (Cosmos credentials, resource group) |
| `.env.prod` | Prod-specific (Cosmos credentials, resource group) |

**Note:** Never commit `.env` files to git. Use `example.env*` as templates.

### Required Variables

**In `.env` (shared):**
```env
ACR_NAME=your-acr-name
ACR_SERVER=your-acr-name.azurecr.io
RESOURCE_GROUP_SHARED=ai-productivity-shared
CONTAINER_APP_ENV=ai-prod-env
MCP_APP_NAME=ai-prod-mcp
COSMOS_DATABASE=productivity
COSMOS_CONTAINER=productivity-data
```

**In `.env.dev` or `.env.prod` (environment-specific):**
```env
RESOURCE_GROUP=ai-productivity-dev
COSMOS_HOST=https://your-cosmos-dev.documents.azure.com:443/
COSMOS_KEY=your-cosmos-primary-key
```

---

## Deployment Commands

### Full Deployment (First Time)

```powershell
# 1. Setup infrastructure
.\deployment\setup-infrastructure.ps1 -Environment dev

# 2. Update .env.dev with Cosmos credentials from output

# 3. Build and deploy
.\deployment\deploy.ps1 -Environment dev

# 4. Configure environment
.\deployment\set-env-vars.ps1 -Environment dev
```

### Update Deployment (Code Changes)

```powershell
# Rebuild and redeploy (uses existing infrastructure)
.\deployment\deploy.ps1 -Environment dev
```

### Update Configuration Only

```powershell
# Reconfigure environment variables (no rebuild)
.\deployment\set-env-vars.ps1 -Environment dev
```

---

## Local Development

### Option 1: Docker Compose

```powershell
# Requires .env and .env.dev files
docker-compose up
```

Access at: http://localhost:8000

### Option 2: Direct Python

```powershell
# Using run_local.ps1
.\run_local.ps1 mcp

# Or directly
uv run python -m productivity_mcp.mcp_server
```

---

## Microsoft Foundry Agent Service Integration

After deploying, connect your MCP server to Foundry:

1. Get your deployed URL:
   ```powershell
   az containerapp show --name ai-prod-mcp-dev --resource-group ai-productivity-dev --query "properties.configuration.ingress.fqdn" -o tsv
   ```

2. In Foundry portal:
   - Go to **Agent Builder** > **Add Tool**
   - Select **Custom** > **Model Context Protocol (MCP)**
   - Enter endpoint: `https://your-app.azurecontainerapps.io`
   - Authentication: **None** (for Phase 1)

3. Test the connection by asking the agent to use your MCP tools

---

## Cosmos DB Configuration

### Partition Strategy

**Partition Key:** `/userId`

All documents include `userId` field:
- Schema documents: `{ "id": "schema:user123", "userId": "user123", ... }`
- Entity documents: `{ "id": "task:abc-def", "userId": "user123", ... }`

### Cost Optimization

| Environment | Cosmos Mode | Cost |
|-------------|-------------|------|
| Dev | Free Tier | ~$0/month (up to 1000 RU/s) |
| Prod | Serverless | Pay-per-request (~$0.25/100K operations) |

---

## Troubleshooting

### Common Issues

**"ACR login failed":**
```powershell
az acr login --name your-acr-name
```

**"Container App not starting":**
```powershell
# Check logs
az containerapp logs show --name ai-prod-mcp-dev --resource-group ai-productivity-dev --follow
```

**"Cosmos connection refused":**
- Verify `COSMOS_HOST` and `COSMOS_KEY` in `.env.dev`
- Check Cosmos DB firewall allows Azure services

**"Image not found":**
```powershell
# Verify image exists in ACR
az acr repository list --name your-acr-name --output table
```

### Useful Commands

```powershell
# Get Container App URL
az containerapp show --name ai-prod-mcp-dev --resource-group ai-productivity-dev --query "properties.configuration.ingress.fqdn" -o tsv

# View Container App logs
az containerapp logs show --name ai-prod-mcp-dev --resource-group ai-productivity-dev --follow

# Restart Container App
$revision = az containerapp revision list --name ai-prod-mcp-dev --resource-group ai-productivity-dev --query "[0].name" -o tsv
az containerapp revision restart --name ai-prod-mcp-dev --resource-group ai-productivity-dev --revision $revision

# List Cosmos DB keys
az cosmosdb keys list --name ai-prod-cosmos-dev --resource-group ai-productivity-dev
```

---

## Security Notes

### Current State (No Auth)

- `DISABLE_AUTH=true` - No authentication required
- `DEFAULT_USER_ID=demo-user` - All requests use same user
- Suitable for demos and development

### Future Authentication Options

1. **API Key**: Simple header-based auth
2. **Entra ID OAuth**: Microsoft identity platform
3. **Entra Agent ID**: For AI agent identity (when GA)

---

## Related Documentation

- **Root README**: [../README.md](../README.md) - Project overview
- **Code Architecture**: [../src/README.md](../src/README.md) - Code structure
- **Agent Instructions**: [../CLAUDE.md](../CLAUDE.md) - AI development workflow

---

**Last Updated:** 2026-01-13
