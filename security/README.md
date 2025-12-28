# Security - Authentication, Authorization & Secrets

**Source of truth for authentication flows, authorization patterns, secret management, and access control.**

---

## Overview

The Productivity MCP Server implements a phased security approach:

- **Phase 1 (MVP)**: Dev-mode authentication bypass for rapid development
- **Phase 2**: Scalekit OAuth 2.1 for production authentication
- **Phase 3**: Multi-tenant isolation, RBAC, audit logging

**Current State:** Phase 1 (dev-mode, auth disabled)

---

## Authentication

### Current State: Dev-Mode Auth Bypass

**Configuration:**
```env
DISABLE_AUTH=true
DEFAULT_USER_ID=dev-user
```

**How it works:**
1. All MCP requests assumed to be from `dev-user`
2. No token validation
3. No scope checking
4. Suitable for local development only

**Implementation:**
- `backend/auth/dev_auth.py`: Returns `DEFAULT_USER_ID` for all requests
- `backend/config.py`: `DISABLE_AUTH` flag controls auth mode
- `backend/mcp_server.py`: FastMCP initialized without auth provider

**Security Implications:**
- **DO NOT** deploy to production with `DISABLE_AUTH=true`
- Anyone with network access can read/write all data
- No audit trail of who made changes
- Acceptable for local development only

---

### Phase 2: Scalekit OAuth 2.1

**Status:** Scaffolding in place, not enabled

**Architecture:**
```
User → Claude Desktop → MCP Server (401) → Scalekit Login → Token → MCP Server (Authenticated)
```

#### OAuth Flows

**1. Interactive Flow (Auth Code + PKCE)**

Used by Claude Desktop and MCP Inspector.

```
1. Claude Desktop connects to MCP endpoint
2. Server returns 401 with OAuth discovery URL
3. Claude initiates Auth Code + PKCE flow with Scalekit
4. User authenticates via browser (Scalekit SSO)
5. Claude receives JWT token with scopes in claims
6. Claude makes authenticated requests with Bearer token
7. Server validates JWT and checks scopes
```

**Scopes in JWT:**
- Scopes embedded in token claims (`scope` or `scp` field)
- Example: `["Read", "Write"]`

**2. Machine-to-Machine (Client Credentials)**

Used for testing, CI/CD, and service-to-service calls.

```
1. Service requests token from Scalekit via client_credentials grant
2. Scalekit issues JWT token
3. Service makes requests with Bearer token
4. Server validates JWT signature
5. Server checks client_id against whitelist (scopes NOT in JWT for M2M)
6. Access granted if whitelisted
```

**M2M Whitelist (Dev/Testing Only):**
```env
AUTHORIZED_M2M_CLIENTS=skc_test-client-id,skc_ci-client-id
```

**Security Note:** M2M whitelist bypasses scope checking. Use only in dev/testing environments. Production should require interactive auth.

---

#### Scalekit Configuration

**Environment Variables:**
```env
SCALEKIT_ENVIRONMENT_URL=https://soligence.scalekit.dev
SCALEKIT_CLIENT_ID=skc_your-client-id
SCALEKIT_CLIENT_SECRET=your-client-secret
SCALEKIT_RESOURCE_ID=res_productivity-mcp
MCP_URL=https://prism-mcp.azurecontainerapps.io/
```

**Scalekit Portal Setup:**
1. Register MCP server in Scalekit dashboard
2. Set **Server URL**: `https://prism-mcp.azurecontainerapps.io/` (with trailing slash)
3. Define **Scopes**: `Read`, `Write`
4. Note **Resource ID**: `res_productivity-mcp`
5. Create static client for M2M testing (optional)

**FastMCP Integration:**
```python
from fastmcp.server.auth.providers.scalekit import ScalekitProvider

if not Config.DISABLE_AUTH:
    mcp = FastMCP(
        "Productivity MCP Server",
        stateless_http=True,
        auth=ScalekitProvider(
            environment_url=Config.SCALEKIT_ENVIRONMENT_URL,
            client_id=Config.SCALEKIT_CLIENT_ID,
            resource_id=Config.SCALEKIT_RESOURCE_ID,
            mcp_url=Config.MCP_URL,
        ),
    )
```

**Enabling OAuth (Phase 2):**
1. Set `DISABLE_AUTH=false` in `.env`
2. Configure Scalekit environment variables
3. Register MCP server in Scalekit portal
4. Test with MCP Inspector or Claude Desktop
5. Verify token validation and scope checking

---

#### Scope Validation

**Required Scopes:**

| Operation | Scope | Rationale |
|-----------|-------|-----------|
| `get_user_schema`, `get_entity`, `list_entities`, `count_entities` | `Read` | Read-only operations |
| `create_entity_type`, `update_entity_type`, `delete_entity_type` | `Write` | Schema modifications |
| `create_entity`, `update_entity`, `delete_entity` | `Write` | Data modifications |

**Implementation:**

`backend/auth/scalekit_auth.py` (Phase 2):
```python
def _require_scope(scope: str) -> Optional[str]:
    """Return None if authorized, error message if not."""

    # Skip auth in dev mode
    if Config.DISABLE_AUTH:
        return None

    # Get access token from request
    token: AccessToken = get_access_token()

    # Check JWT scope claims (interactive tokens)
    if scope in token.scopes:
        return None

    # Fallback: check raw claims
    claims = getattr(token, "claims", {}) or {}
    raw_scope = claims.get("scope") or claims.get("scp")
    if raw_scope:
        claim_scopes = raw_scope.split() if isinstance(raw_scope, str) else raw_scope
        if scope in claim_scopes:
            return None

    # M2M client whitelist (dev/testing only)
    if Config.AUTHORIZED_M2M_CLIENTS:
        token_client_id = claims.get("client_id", "")
        if token_client_id in Config.AUTHORIZED_M2M_CLIENTS:
            logger.warning(f"M2M client authorized via whitelist: {token_client_id}")
            return None

    return f"Insufficient permissions: `{scope}` scope required."
```

**Tool Integration:**
```python
@mcp.tool()
def create_entity(...):
    error = _require_scope("Write")
    if error:
        return {"error": error}

    # ... existing logic
```

---

## Authorization

### Current State: No Authorization

**User Isolation:**
- All operations scoped to `userId` (from auth context)
- Cosmos DB partitioned by `/userId`
- No cross-user data access possible

**Future (Phase 3):**
- **Role-Based Access Control (RBAC)**: Admin, User, ReadOnly roles
- **Resource-Level Permissions**: Per-entity access control
- **Sharing**: Allow users to share entities with others

---

## Secret Management

### Current State: `.env` File (Local Development)

**Secrets Stored:**
- `COSMOS_KEY`: Cosmos DB primary key
- `SCALEKIT_CLIENT_SECRET`: Scalekit OAuth secret (future)

**Security:**
- `.env` file in `.gitignore` (never commit)
- Local file system protection
- Suitable for development only

**Risk:** If `.env` file is exposed, full database access is compromised

---

### Phase 2: Azure Key Vault

**Migration Plan:**
1. Store secrets in Azure Key Vault
2. Container Apps retrieves secrets via managed identity
3. No secrets in environment variables or config files

**Key Vault Secrets:**
- `cosmos-key`: Cosmos DB primary key
- `scalekit-client-secret`: Scalekit OAuth secret
- `langsmith-api-key`: LangSmith tracing key (future)

**Container Apps Configuration:**
```powershell
az containerapp create `
  --name prism-mcp `
  --resource-group prism-prod `
  --secrets cosmos-key=keyvaultref:https://prism-kv.vault.azure.net/secrets/cosmos-key `
  --env-vars COSMOS_KEY=secretref:cosmos-key
```

**Benefits:**
- Centralized secret storage
- Audit trail of secret access
- Automatic rotation support
- No secrets in code or config

---

### Phase 3: Managed Identity

**Current:** Service Principal or primary key for Cosmos DB

**Future:** Managed identity for passwordless access

**Benefits:**
- No credentials to manage
- Azure AD-based authentication
- Automatic credential rotation
- Reduced attack surface

**Implementation:**
```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
cosmos_client = CosmosClient(url=Config.COSMOS_HOST, credential=credential)
```

**Container Apps Setup:**
1. Enable system-assigned managed identity on Container App
2. Grant "Cosmos DB Data Contributor" role to managed identity
3. Remove `COSMOS_KEY` from config
4. Code uses `DefaultAzureCredential()` automatically

---

## Network Security

### Current State: Public Access

**MCP Server:**
- Local development: `http://localhost:8000`
- No network restrictions

**Cosmos DB:**
- Public endpoint (authenticated via key)
- Firewall rules: Allow all IPs (development)

**Risk:** No network-level protection, relies solely on authentication

---

### Phase 2: IP Restrictions

**Container Apps Ingress:**
```powershell
az containerapp ingress access-restriction set `
  --name prism-mcp `
  --resource-group prism-prod `
  --rule-name "allow-office" `
  --ip-address 203.0.113.0/24 `
  --action Allow
```

**Cosmos DB Firewall:**
```powershell
az cosmosdb network-rule add `
  --name cosmos-prism-prod `
  --resource-group prism-prod `
  --ip-range-filter 203.0.113.0/24
```

**Use Cases:**
- Restrict MCP access to office IP range
- Restrict Cosmos DB access to Container Apps subnet
- Defense in depth

---

### Phase 3: Private Endpoints

**Current:** Public endpoints (internet-accessible)

**Future:** Private endpoints (VNet-only access)

**Benefits:**
- No public internet exposure
- Traffic stays within Azure network
- Lower latency, higher security

**Implementation:**
1. Create Azure VNet for Container Apps
2. Create private endpoint for Cosmos DB
3. Configure DNS for private endpoint resolution
4. Remove public endpoint access

**Cost:** Additional ~$7/month per private endpoint

---

## Audit Logging

### Current State: Basic Application Logs

**What's Logged:**
- MCP tool calls (tool name, duration, success/failure)
- Service operations (create, update, delete)
- Errors and exceptions

**Limitations:**
- No user identity in logs (all `dev-user`)
- No request tracing (correlation IDs)
- Logs not structured for querying

---

### Phase 2: Structured Audit Logs

**Log Format (JSON):**
```json
{
  "timestamp": "2025-12-27T10:00:00Z",
  "level": "INFO",
  "operation": "create_entity",
  "user_id": "alice@example.com",
  "entity_type": "task",
  "entity_id": "task:abc-123",
  "duration_ms": 45,
  "success": true,
  "client_id": "claude-desktop",
  "request_id": "req-xyz-789"
}
```

**Storage:**
- Azure Log Analytics workspace
- Retention: 30 days (configurable)
- Queryable via KQL (Kusto Query Language)

**Query Examples:**
```kusto
// All operations by specific user
traces
| where user_id == "alice@example.com"
| order by timestamp desc

// Failed operations in last hour
traces
| where success == false and timestamp > ago(1h)
| summarize count() by operation, user_id
```

---

### Phase 3: Compliance Audit Trail

**Requirements:**
- Immutable audit logs (WORM storage)
- Long-term retention (7 years for compliance)
- Tamper-proof (cryptographic signing)

**Implementation:**
- Export logs to Azure Blob Storage (immutable)
- Use Azure Monitor Diagnostic Settings
- Enable log integrity verification

---

## Data Protection

### Encryption at Rest

**Cosmos DB:**
- Automatic encryption at rest (AES-256)
- Microsoft-managed keys (default)
- Option: Customer-managed keys (CMK) for compliance

**Container Apps:**
- Persistent storage encrypted at rest
- Secrets encrypted in Azure Key Vault

**No additional configuration needed** - enabled by default

---

### Encryption in Transit

**All Connections TLS 1.2+:**
- MCP Server → Cosmos DB: HTTPS
- Claude Desktop → MCP Server: HTTPS
- Container Apps ingress: TLS termination

**Enforce TLS:**
```powershell
az containerapp ingress update `
  --name prism-mcp `
  --resource-group prism-prod `
  --transport http2  # HTTP/2 only (implicitly TLS)
```

---

### Data Residency

**Current:** Single Azure region (westus2)

**Compliance:**
- Data stored in US West (Microsoft datacenter)
- Subject to US jurisdiction
- No cross-border data transfer

**Multi-Region (Future):**
- Cosmos DB supports multi-region replication
- Choose regions based on compliance requirements
- Example: EU data in West Europe, US data in East US

---

## Threat Model

### Threats Mitigated

| Threat | Mitigation | Phase |
|--------|-----------|-------|
| Unauthorized access | Scalekit OAuth, JWT validation | Phase 2 |
| Token theft | Short-lived JWTs (1 hour), PKCE | Phase 2 |
| Credential exposure | Azure Key Vault, managed identity | Phase 2-3 |
| Man-in-the-middle | TLS 1.2+ for all connections | Phase 1 |
| Data breach | Encryption at rest, network isolation | Phase 1-3 |
| Cross-user access | Cosmos DB partitioning, user_id scoping | Phase 1 |

### Residual Risks

| Risk | Impact | Mitigation Plan |
|------|--------|-----------------|
| Compromised Scalekit account | High | Enable MFA, audit Scalekit access logs |
| Azure subscription compromise | Critical | Enable Azure AD Conditional Access, PIM |
| Insider threat | Medium | Audit logs, least privilege access |
| DDoS attack | Medium | Azure DDoS Protection (future) |

---

## Security Checklist

### Before Enabling OAuth (Phase 2)

- [ ] Register MCP server in Scalekit portal
- [ ] Configure `SCALEKIT_*` environment variables
- [ ] Implement `_require_scope()` validation in all tools
- [ ] Test with MCP Inspector (interactive flow)
- [ ] Test with M2M client (client_credentials flow)
- [ ] Set `DISABLE_AUTH=false` only after successful testing
- [ ] Remove M2M whitelist from production config

### Before Production Deployment (Phase 2+)

- [ ] Migrate secrets to Azure Key Vault
- [ ] Enable managed identity for Cosmos DB access
- [ ] Configure IP restrictions on Container Apps ingress
- [ ] Enable Cosmos DB firewall rules
- [ ] Configure structured audit logging (JSON)
- [ ] Set up Log Analytics alerts for security events
- [ ] Document incident response procedures
- [ ] Conduct security review with stakeholders

---

## Incident Response

### Security Event Handling

**Detection:**
- Monitor Azure Log Analytics for anomalies
- Alert on failed authentication attempts (>10 in 5 min)
- Alert on unusual data access patterns

**Response:**
1. **Identify**: Determine scope of incident (logs, user_id, resources affected)
2. **Contain**: Revoke compromised tokens, disable affected accounts
3. **Eradicate**: Rotate secrets, patch vulnerabilities
4. **Recover**: Restore from backups if needed
5. **Post-Mortem**: Document incident, update security measures

**Contacts:**
- **Security Lead**: [TBD]
- **Azure Support**: support.microsoft.com
- **Scalekit Support**: support@scalekit.com

---

## Related Documentation

- **Root README**: [../README.md](../README.md) - Project overview
- **Code Architecture**: [../backend/README.md](../backend/README.md) - Auth implementation
- **Deployment**: [../deployment/README.md](../deployment/README.md) - Infrastructure setup
- **Monitoring**: [../monitoring/README.md](../monitoring/README.md) - Security monitoring

**Enterprise Security Guide**: `C:\projects\enterprise_architecture\guides\scalekit-setup.md`

**Agent Instructions**: [../CLAUDE.md](../CLAUDE.md)

---

**Last Updated:** 2025-12-27 (Phase 1: Enterprise Alignment)
