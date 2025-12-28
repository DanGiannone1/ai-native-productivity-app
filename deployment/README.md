# Deployment - Infrastructure & CI/CD

**Source of truth for infrastructure provisioning, environments, and deployment processes.**

---

## Overview

The Productivity MCP Server follows the enterprise architecture 3-RG (Resource Group) silo pattern for environment isolation and resource management.

**Deployment Strategy:**
- **Dev Environment**: Serverless Cosmos DB, rapid iteration, auth disabled
- **Prod Environment**: Serverless Cosmos DB, Scalekit OAuth enabled (Phase 2)
- **Infrastructure**: Azure Container Apps (serverless), Cosmos DB (serverless), Log Analytics

---

## The 3-Resource-Group Model

Following the enterprise architecture pattern, we use three resource groups:

| Resource Group | Purpose | Resources |
|----------------|---------|-----------|
| **soligence-shared-services** | High fixed-cost, logically shared resources | ACR (Azure Container Registry), ACS (Communication Services) |
| **prism-dev** | Development environment | Cosmos DB (serverless), Log Analytics, App Insights, Container Apps Environment |
| **prism-prod** | Production environment | Cosmos DB (serverless), Log Analytics, App Insights, Container Apps Environment |

**Rationale:**
- **Shared RG**: Avoid duplicate costs for container registry, email services
- **Environment RGs**: Isolated dev/prod for independent scaling, access control
- **Serverless**: Pay-per-use, ideal for bursty MCP workloads

---

## Infrastructure Components

### Shared Resources (`soligence-shared-services`)

1. **Azure Container Registry (ACR)**
   - Name: `acrprismshr` (or reuse existing `acr0shared`)
   - SKU: Basic
   - Purpose: Store MCP server container images
   - Shared across all environments

2. **Azure Communication Services (ACS)**
   - Name: `acs-prism-shared`
   - Purpose: Email notifications (Phase 2+)
   - Shared across all environments

### Environment-Specific Resources

#### Dev Environment (`prism-dev`)

1. **Cosmos DB Account**
   - Name: `cosmos-prism-dev`
   - Mode: **Serverless** (1000 RU/s free tier)
   - Database: `productivity`
   - Container: `productivity-data`
   - Partition Key: `/userId`
   - Consistency: Session

2. **Log Analytics Workspace**
   - Name: `prism-logs-dev`
   - Purpose: Centralized logging, queryable by AI agents

3. **Application Insights**
   - Name: `prism-insights-dev`
   - Purpose: Application performance monitoring
   - Linked to Log Analytics

4. **Container Apps Environment**
   - Name: `prism-env-dev`
   - Purpose: Host MCP server container
   - Future: Auto-scaling, custom domains

#### Prod Environment (`prism-prod`)

Same resources as dev with `-prod` suffix, plus:
- Scalekit OAuth enabled (Phase 2)
- IP restrictions on ingress (Phase 2)
- Higher throughput if needed

---

## Setup Scripts

### `setup-infrastructure.ps1` - Infrastructure Provisioning

**Purpose:** Create all Azure resources for dev or prod

**Usage:**
```powershell
.\scripts\setup-infrastructure.ps1 -Environment dev -Location westus2
```

**Parameters:**
- `-Environment`: `dev` or `prod` (default: `dev`)
- `-Location`: Azure region (default: `westus2`)

**What it does:**
1. Creates resource groups (shared, dev, prod)
2. Creates or reuses shared resources (ACR, ACS)
3. Creates environment-specific resources (Cosmos DB, Log Analytics, etc.)
4. Creates Cosmos database and container with `/userId` partition key
5. Retrieves secrets (Cosmos connection string)
6. Updates `.env` file with connection details

**Output:**
- Infrastructure provisioned in Azure
- `.env` file updated with Cosmos credentials
- Ready for local development

**Prerequisites:**
- Azure CLI installed (`az --version`)
- Logged into Azure (`az login`)
- Appropriate Azure subscription permissions

**Post-Setup:**
```powershell
# Verify connection
.\run_local.ps1 init

# Seed sample data
.\run_local.ps1 seed

# Start MCP server
.\run_local.ps1 mcp
```

---

## Environments

### Development (`dev`)

**Purpose:** Local development and testing

**Characteristics:**
- Serverless Cosmos DB (1000 RU/s free tier)
- Auth disabled (`DISABLE_AUTH=true`)
- Verbose logging (`LOG_LEVEL=INFO`)
- Default user: `dev-user`

**Access:**
- No authentication required
- Local MCP server: `http://localhost:8000`
- Cosmos DB: Direct connection with primary key

**Cost:** Minimal (serverless free tier + storage)

---

### Production (`prod`)

**Purpose:** Production workloads (Phase 2+)

**Characteristics:**
- Serverless Cosmos DB (pay-per-use)
- Scalekit OAuth enabled
- Structured JSON logging for Azure Log Analytics
- LangSmith tracing enabled

**Access:**
- Scalekit OAuth required
- MCP server: `https://prism-mcp.azurecontainerapps.io/`
- Cosmos DB: Managed identity or Key Vault secrets

**Cost:** Pay-per-use (RU consumption + storage)

---

## Deployment Process

### Current State (MVP - Local Development)

**Local MCP Server:**
```powershell
.\run_local.ps1 mcp
```

Starts FastMCP server on `http://localhost:8000` using local Cosmos DB credentials.

**Configuration:**
- Loaded from `.env` file
- Dev mode auth bypass enabled
- Connects to dev Cosmos DB

---

### Phase 2: Container Deployment (Future)

**Build & Push:**
```powershell
# Build container
docker build -t productivity-mcp:latest .

# Tag for ACR
docker tag productivity-mcp:latest acrprismshr.azurecr.io/productivity-mcp:latest

# Push to ACR
docker push acrprismshr.azurecr.io/productivity-mcp:latest
```

**Deploy to Container Apps:**
```powershell
az containerapp create `
  --name prism-mcp `
  --resource-group prism-dev `
  --environment prism-env-dev `
  --image acrprismshr.azurecr.io/productivity-mcp:latest `
  --target-port 8000 `
  --ingress external `
  --env-vars COSMOS_HOST=secretref:cosmos-host COSMOS_KEY=secretref:cosmos-key
```

**Configuration:**
- Secrets stored in Container Apps secrets
- Environment variables for non-sensitive config
- Managed identity for Cosmos DB (future)

---

## Cosmos DB Configuration

### Partition Strategy

**Partition Key:** `/userId`

**Rationale:**
- All user data in single partition (efficient queries)
- No cross-partition queries needed for most operations
- Lower RU costs (single-partition reads/writes)
- Natural isolation boundary

**Document Types:**
- **Schema**: `id: "schema:{userId}"`
- **Entities**: `id: "{entityType}:{uuid}"`

All documents include `userId` field for partitioning.

### Serverless Mode

**Characteristics:**
- Pay-per-request (no provisioned throughput)
- Automatic scaling (up to 5000 RU/s)
- 1000 RU/s free tier (sufficient for dev/testing)
- Storage: $0.25/GB/month

**Cost Estimate (Dev):**
- Schema operations: ~10 RU each
- Entity CRUD: ~5-10 RU each
- Queries: 5-50 RU depending on complexity
- Free tier covers ~100-200 operations/day

**When to Switch to Provisioned:**
- Consistent high throughput (>5000 RU/s sustained)
- Cost optimization at scale
- Not needed for MCP use case (bursty workloads)

### Consistency Level

**Session Consistency** (default)

**Rationale:**
- Read-your-writes guarantee within session
- Lower latency than Strong consistency
- Sufficient for single-user productivity data

---

## Database Initialization

### `scripts/init_cosmos.py` - Database Setup

**Purpose:** Create database and container if not exists

**Usage:**
```powershell
.\run_local.ps1 init
```

**What it does:**
1. Connects to Cosmos DB using `.env` credentials
2. Creates database if not exists
3. Creates container with `/userId` partition key
4. Verifies connectivity

**When to run:**
- After infrastructure provisioning
- When starting fresh development
- If database accidentally deleted

---

### `scripts/seed_data.py` - Sample Data

**Purpose:** Populate database with sample entity types and entities

**Usage:**
```powershell
.\run_local.ps1 seed
```

**What it creates:**
- 3 entity types: `task`, `goal`, `habit`
- 10+ sample entities across types
- Realistic data for testing

**Use cases:**
- Testing MCP tools
- Demonstrating functionality
- Developing UI (Phase 3)

---

## Monitoring & Logs

See [../monitoring/README.md](../monitoring/README.md) for observability details.

**Quick Access:**

**Local Logs:**
```powershell
# MCP server logs (console)
.\run_local.ps1 mcp

# Verbose logs
$env:LOG_LEVEL="DEBUG"
.\run_local.ps1 mcp
```

**Azure Logs (Future):**
- Log Analytics workspace: `prism-logs-dev`
- Application Insights: `prism-insights-dev`
- Query via Azure Portal or AI agents

---

## Infrastructure as Code

### PowerShell (Current)

**Why PowerShell?**
- AI agents demonstrate higher accuracy with PowerShell than Bicep
- Pragmatic choice per enterprise architecture guidance
- Easier to debug and iterate

**Scripts:**
- `setup-infrastructure.ps1`: Provision all resources
- `init_cosmos.py`: Initialize database
- `seed_data.py`: Populate sample data

### Future: Bicep (Optional)

If AI tooling improves for Bicep, we may migrate to declarative IaC.

---

## Security

See [../security/README.md](../security/README.md) for security details.

**Deployment Security:**
- Secrets stored in Azure Key Vault (Phase 2)
- Managed identities for Cosmos DB access (Phase 2)
- IP restrictions on Container Apps ingress (Phase 2)
- Scalekit OAuth for authentication (Phase 2)

---

## CI/CD (Future - Phase 3)

**Planned:**
- GitHub Actions for build/deploy
- Automated testing on PR
- Deploy to dev on merge to `main`
- Manual approval for prod deployment

**Pipeline:**
1. Lint & format (ruff)
2. Run tests (pytest)
3. Build container
4. Push to ACR
5. Deploy to Container Apps
6. Health check

---

## Disaster Recovery

### Backup Strategy

**Cosmos DB:**
- Automatic backups (every 4 hours, retained 30 days)
- Point-in-time restore (PITR) available
- Contact Azure support for restore

**No manual backup needed** - Cosmos DB handles automatically

### Recovery Procedure

1. **Accidental deletion**: Restore from Cosmos DB backup
2. **Corruption**: Roll back to previous backup
3. **Region failure**: Cosmos DB handles failover automatically (if multi-region)

**Current State:** Single-region (cost optimization), acceptable for MVP

---

## Cost Optimization

### Current Costs (Dev)

- **Cosmos DB**: Free tier (1000 RU/s) + storage (~$0.25/month)
- **Log Analytics**: Free tier (5 GB/month)
- **Container Apps**: Not deployed yet (future: ~$15-30/month)
- **Total**: < $1/month (dev environment)

### Monitoring Costs

Check Azure Cost Management:
```powershell
az consumption usage list --resource-group prism-dev
```

---

## Troubleshooting

### Common Issues

**Setup fails with "Cosmos account name taken":**
- Cosmos account names are globally unique
- Change `$cosmosAccountName` in `setup-infrastructure.ps1`

**`.env` file not updated:**
- Run `setup-infrastructure.ps1` again
- Manually retrieve keys: `az cosmosdb keys list ...`

**Connection fails:**
- Verify `COSMOS_HOST` and `COSMOS_KEY` in `.env`
- Check firewall rules (allow local IP)
- Test: `.\run_local.ps1 init`

**MCP server won't start:**
- Check logs for specific error
- Verify `.env` file exists
- Run `uv sync` to install dependencies

---

## Related Documentation

- **Root README**: [../README.md](../README.md) - Project overview
- **Code Architecture**: [../backend/README.md](../backend/README.md) - Code structure
- **Security**: [../security/README.md](../security/README.md) - Auth and secrets
- **Monitoring**: [../monitoring/README.md](../monitoring/README.md) - Observability
- **Tests**: [../tests/README.md](../tests/README.md) - Testing strategy

**Agent Instructions**: [../CLAUDE.md](../CLAUDE.md)

---

**Last Updated:** 2025-12-27 (Phase 1: Enterprise Alignment)
