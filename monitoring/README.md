# Monitoring - Observability & Diagnostics

**Source of truth for logging, tracing, dashboards, alerts, and observability practices.**

---

## Overview

The Productivity MCP Server follows the enterprise architecture observability pattern with:

- **Application Logging**: Structured logs for operational insights
- **AI Tracing**: LangSmith for AI reasoning step visibility (Phase 2+)
- **Performance Monitoring**: Application Insights for APM (Phase 2+)
- **Log Analytics**: Centralized query interface for AI agents (Phase 2+)

**Current State:** Basic application logging (Phase 1)

---

## Logging

### Current State: Console Logging

**Configuration:**
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Format (Human-Readable):**
```
2025-12-27 10:00:00 - backend.mcp_server - INFO - Starting Productivity MCP Server
2025-12-27 10:00:01 - backend.services.entity_service - INFO - [create_entity:1735297201000] Starting create_entity
2025-12-27 10:00:01 - backend.services.entity_service - INFO - [create_entity:1735297201000] ✓ create_entity completed successfully in 45.23ms
```

**What's Logged:**
- Server startup and configuration
- Tool invocations (tool name, parameters)
- Service operations (create, read, update, delete)
- Durations and success/failure status
- Errors with stack traces

**Limitations:**
- Not structured (hard to query programmatically)
- No correlation IDs across requests
- Console-only (not persistent)
- No user identity (all `dev-user`)

**Output:**
- Console (stdout/stderr)
- Captured by `.\run_local.ps1 mcp`

---

### Phase 2: Structured JSON Logging

**Purpose:** Enable programmatic querying and AI agent log analysis

**Format (JSON):**
```json
{
  "timestamp": "2025-12-27T10:00:00.000Z",
  "level": "INFO",
  "logger": "backend.services.entity_service",
  "operation": "create_entity",
  "operation_id": "create_entity:1735297201000",
  "user_id": "alice@example.com",
  "entity_type": "task",
  "entity_id": "task:abc-123",
  "duration_ms": 45.23,
  "success": true,
  "message": "create_entity completed successfully",
  "context": {
    "cosmos_ru": 5.2,
    "partition_key": "alice@example.com"
  }
}
```

**Benefits:**
- Machine-readable (JSON)
- Structured fields for filtering/aggregation
- Correlation IDs for request tracing
- Ingested directly into Azure Log Analytics

**Configuration:**
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            # ... additional fields from record
        }
        return json.dumps(log_data)

# Apply in production mode
if Config.ENVIRONMENT == "prod":
    handler.setFormatter(JSONFormatter())
```

**Implementation:** `backend/utils/logging.py` (Phase 2)

---

### Log Levels

| Level | Use Case | Examples |
|-------|----------|----------|
| **DEBUG** | Detailed diagnostic info | Request payloads, query results, internal state |
| **INFO** | General operational events | Tool calls, entity creation, schema updates |
| **WARNING** | Unexpected but handled | Missing optional fields, fallback behavior |
| **ERROR** | Errors that need attention | Validation failures, Cosmos DB errors |
| **CRITICAL** | System-level failures | Cosmos DB unreachable, config missing |

**Setting Log Level:**
```env
LOG_LEVEL=INFO  # Default for production
LOG_LEVEL=DEBUG  # For troubleshooting
```

---

## Telemetry

### Current State: Operation Logging

**Implementation:** `backend/utils/telemetry.py`

```python
from backend.utils.telemetry import with_telemetry

@with_telemetry("create_entity")
def create_entity(entity_type, data, metadata):
    # ... business logic
```

**What it does:**
1. Logs operation start with operation ID
2. Executes function
3. Logs completion with duration and success/failure
4. Re-raises exceptions after logging

**Example Output:**
```
[create_entity:1735297201000] Starting create_entity
[create_entity:1735297201000] ✓ create_entity completed successfully in 45.23ms
```

**Enhancements (Phase 2):**
- Add user_id to telemetry context
- Add request_id for cross-service tracing
- Add custom metrics (RU consumption, entity counts)

---

## AI Tracing (LangSmith)

### Phase 2: LangSmith Integration

**Purpose:** Trace AI reasoning steps, tool calls, and decision-making

**Why LangSmith?**
- Enterprise-standard per architecture guidance
- Clean UI for visualizing AI traces
- Cost-effective (free tier available)
- Easy integration with Anthropic Claude API

**Configuration:**
```env
LANGSMITH_API_KEY=lsv2_your-key-here
LANGSMITH_PROJECT=productivity-mcp
LANGSMITH_TRACING=true  # Enable/disable tracing
```

**What Gets Traced:**
- MCP tool calls (inputs, outputs, durations)
- Schema validation steps
- Entity CRUD operations
- Error conditions and retries

**Example Trace:**

```
Trace: Create Task Entity
├─ Tool Call: create_entity
│  ├─ Input: {entity_type: "task", data: {...}}
│  ├─ Validate Schema
│  │  ├─ Lookup schema for "task"
│  │  ├─ Check required fields
│  │  └─ Validate field types ✓
│  ├─ Create Cosmos DB Document
│  │  ├─ Generate entity ID
│  │  ├─ Upsert to Cosmos
│  │  └─ RU Cost: 5.2
│  └─ Output: {success: true, entity_id: "task:abc-123"}
└─ Duration: 45ms
```

**LangSmith UI:**
- View traces in browser: https://smith.langchain.com
- Filter by project, user, time range
- Drill into individual traces
- Export traces for analysis

**Implementation:**

`backend/utils/langsmith_tracer.py` (Phase 2):
```python
from langsmith import Client
from functools import wraps

langsmith_client = Client(api_key=Config.LANGSMITH_API_KEY)

def trace_mcp_tool(tool_name: str):
    """Decorator to trace MCP tool calls to LangSmith."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not Config.LANGSMITH_TRACING:
                return func(*args, **kwargs)

            with langsmith_client.trace(
                name=tool_name,
                project_name=Config.LANGSMITH_PROJECT,
                inputs={"args": args, "kwargs": kwargs}
            ) as run:
                result = func(*args, **kwargs)
                run.end(outputs=result)
                return result
        return wrapper
    return decorator

# Usage in tools
@trace_mcp_tool("create_entity")
def create_entity_tool(...):
    # ... existing logic
```

**Enabling Tracing:**
1. Sign up for LangSmith: https://smith.langchain.com
2. Create project: `productivity-mcp`
3. Get API key from settings
4. Add to `.env`: `LANGSMITH_API_KEY=lsv2_...`
5. Set `LANGSMITH_TRACING=true`
6. Restart MCP server

**Viewing Traces:**
1. Make MCP tool calls via Claude Desktop
2. Open LangSmith UI
3. Navigate to `productivity-mcp` project
4. View traces in real-time

**Cost:**
- Free tier: 5,000 traces/month
- Pro tier: $39/month (50,000 traces/month)
- Sufficient for MVP and early production

---

## Azure Monitoring (Phase 2+)

### Log Analytics Workspace

**Purpose:** Centralized log aggregation and querying

**Current Setup:**
- Workspace: `prism-logs-dev` (dev), `prism-logs-prod` (prod)
- Retention: 30 days (default)
- Location: Same region as Container Apps

**Log Ingestion:**

**Local Development:**
- Logs to console (not sent to Log Analytics)

**Container Apps Deployment:**
- Logs automatically sent to Log Analytics
- No additional configuration needed

**Querying Logs:**

**Via Azure Portal:**
1. Navigate to Log Analytics workspace
2. Open "Logs" section
3. Write KQL query

**Example KQL Queries:**

```kusto
// All MCP tool calls in last hour
traces
| where timestamp > ago(1h)
| where message contains "MCP tool"
| project timestamp, operation, user_id, duration_ms, success
| order by timestamp desc

// Error rate by operation
traces
| where success == false
| summarize ErrorCount=count() by operation
| order by ErrorCount desc

// Slowest operations (p95 latency)
traces
| summarize p95=percentile(duration_ms, 95) by operation
| order by p95 desc

// User activity (top users by operation count)
traces
| summarize OperationCount=count() by user_id
| order by OperationCount desc
| take 10
```

**AI Agent Querying:**

AI agents can query logs directly via Azure CLI:

```powershell
# AI agent runs this command to investigate issues
az monitor log-analytics query `
  --workspace prism-logs-dev `
  --analytics-query "traces | where level == 'ERROR' | take 10"
```

**Use Cases:**
- Debugging production issues
- Performance analysis
- User behavior insights
- Security monitoring (failed auth attempts)

---

### Application Insights

**Purpose:** Application Performance Monitoring (APM)

**Current Setup:**
- Resource: `prism-insights-dev` (dev), `prism-insights-prod` (prod)
- Linked to Log Analytics workspace

**Metrics Collected (Automatic):**
- Request rates (requests/sec)
- Response times (avg, p95, p99)
- Failure rates (4xx, 5xx errors)
- Dependency calls (Cosmos DB latency)
- Exceptions and stack traces

**Custom Metrics (Phase 2):**
- Entity creation rate
- Schema update frequency
- Cosmos RU consumption per operation
- User activity (DAU, MAU)

**Dashboards:**

**Pre-built:**
- Application Dashboard (Azure Portal)
- Performance (request durations, dependencies)
- Failures (error rates, exception details)

**Custom (Phase 3):**
- MCP Tool Performance Dashboard
- User Activity Dashboard
- Cost Optimization Dashboard (RU usage)

**Alerts (Phase 2):**

Configure alerts for:
- Error rate > 5% for 5 minutes
- p95 latency > 500ms
- Cosmos DB 429 errors (rate limiting)
- Failed authentication attempts > 10/min

**Example Alert:**
```powershell
az monitor metrics alert create `
  --name "High Error Rate" `
  --resource-group prism-prod `
  --scopes "/subscriptions/.../resourceGroups/prism-prod/providers/Microsoft.Insights/components/prism-insights-prod" `
  --condition "avg requests/failed > 5" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action email john@example.com
```

---

## Dashboards

### Phase 2: Operational Dashboard

**Metrics:**
- Request volume (requests/hour)
- Success rate (%)
- Avg response time (ms)
- Active users (last 24h)
- Error rate by operation
- Cosmos RU consumption

**Tools:**
- Azure Portal (Application Insights)
- Grafana (future, if needed)

**Access:**
- Azure Portal → Application Insights → Dashboards
- Pin key metrics to Azure Dashboard

---

### Phase 3: AI Agent Dashboard

**Purpose:** Dashboard queryable by AI agents for self-service monitoring

**Queries AI Agents Can Run:**

1. **"What's the error rate in the last hour?"**
   ```kusto
   traces
   | where timestamp > ago(1h)
   | summarize TotalRequests=count(), Failures=countif(success==false)
   | extend ErrorRate=Failures*100.0/TotalRequests
   ```

2. **"Who are the top 5 users today?"**
   ```kusto
   traces
   | where timestamp > startofday(now())
   | summarize OpCount=count() by user_id
   | top 5 by OpCount desc
   ```

3. **"Show me slow operations (>200ms) in the last 30 minutes"**
   ```kusto
   traces
   | where timestamp > ago(30m) and duration_ms > 200
   | project timestamp, operation, user_id, duration_ms
   | order by duration_ms desc
   ```

**Implementation:**
- MCP tool: `query_logs(kql_query: str) -> results`
- AI agents can query logs naturally
- Enables self-service troubleshooting

---

## Health Checks

### Current State: No Health Endpoint

**Phase 2: Health Endpoint**

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "cosmos_db": {
    "status": "connected",
    "latency_ms": 12
  },
  "auth": {
    "mode": "oauth",
    "provider": "scalekit"
  }
}
```

**Checks:**
- Cosmos DB connectivity
- Cosmos DB query latency
- Auth provider reachability (Scalekit)

**Use Cases:**
- Load balancer health checks
- Monitoring alerts (health endpoint down)
- Startup verification

**Implementation:**
```python
@mcp.get("/health")
async def health_check():
    cosmos_status = check_cosmos_health()
    return {
        "status": "healthy" if cosmos_status else "degraded",
        "cosmos_db": cosmos_status,
        # ...
    }
```

---

## Performance Monitoring

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| p95 Response Time | < 200ms | > 500ms |
| Success Rate | > 99% | < 95% |
| Cosmos RU/sec | < 100 | > 500 |
| Error Rate | < 1% | > 5% |
| Availability | > 99.9% | < 99% |

### Bottleneck Identification

**Common Bottlenecks:**
1. **Cosmos DB queries** (cross-partition, large result sets)
2. **Schema validation** (complex schemas with many fields)
3. **Network latency** (Cosmos DB in different region)

**Diagnosis:**
- Use Application Insights dependency tracking
- Analyze Cosmos DB RU consumption
- Check query execution times in logs

**Optimization:**
- Use single-partition queries (provide `userId`)
- Index frequently queried fields
- Cache schema documents (reduce Cosmos reads)
- Batch operations where possible

---

## Cost Monitoring

### Azure Cost Tracking

**Resources to Monitor:**
- **Cosmos DB**: RU consumption (serverless pay-per-use)
- **Log Analytics**: Data ingestion (GB/month)
- **Application Insights**: Data volume
- **Container Apps**: Compute time (future)

**Cost Estimates (Dev):**
- Cosmos DB: ~$1-5/month (serverless)
- Log Analytics: Free tier (5 GB/month)
- Application Insights: Free tier (5 GB/month)
- **Total**: ~$1-5/month

**Cost Alerts:**
```powershell
az consumption budget create `
  --budget-name "prism-dev-budget" `
  --amount 50 `
  --resource-group prism-dev `
  --time-grain Monthly `
  --notifications enabled=true email=admin@example.com threshold=80
```

**Optimization Tips:**
- Use single-partition queries (lower RU cost)
- Set appropriate log retention (30 days vs 365 days)
- Monitor Cosmos RU usage per operation
- Disable verbose logging in production

---

## Troubleshooting

### Common Issues

**1. High Latency (p95 > 500ms)**

**Diagnosis:**
- Check Application Insights dependency tracking
- Identify slow Cosmos DB queries
- Look for cross-partition queries

**Solutions:**
- Add partition key to queries
- Optimize query filters
- Cache frequently accessed data

---

**2. High Cosmos RU Consumption**

**Diagnosis:**
- Check Cosmos DB metrics in Azure Portal
- Identify operations with high RU cost
- Look for repeated reads (caching opportunity)

**Solutions:**
- Use point reads instead of queries (1 RU vs 5+ RU)
- Cache schema documents (reduce lookups)
- Batch writes where possible

---

**3. Errors in Production**

**Diagnosis:**
1. Check Application Insights "Failures" section
2. Filter by time range and operation
3. View exception details and stack traces
4. Query logs for context

**Solutions:**
- Review error patterns (specific user? specific entity type?)
- Check Cosmos DB status (throttling, outages)
- Verify configuration (env vars, auth)
- Roll back if necessary

---

**4. Authentication Failures**

**Diagnosis:**
- Check logs for "Insufficient permissions" errors
- Verify Scalekit token validation
- Check token expiration and scopes

**Solutions:**
- Verify `SCALEKIT_*` configuration
- Check Scalekit portal for MCP server registration
- Test with MCP Inspector
- Review user's Scalekit account permissions

---

## Log Retention & Compliance

### Current State

**Local Development:**
- Logs retained in console session only
- No persistent storage

**Future (Production):**
- Log Analytics: 30 days retention (default)
- Application Insights: 90 days retention (default)
- Long-term: Export to Azure Blob Storage (immutable)

### Compliance Requirements (Phase 3)

**GDPR / Data Privacy:**
- User data in logs must be pseudonymized or deleted on request
- Logs containing PII must be encrypted and access-controlled

**SOC 2 / Security:**
- Audit logs retained for 7 years
- Logs must be immutable (WORM storage)
- Access to logs must be audited

**Implementation:**
- Tag sensitive fields in logs
- Automated PII scrubbing (future)
- Export to immutable blob storage
- Audit access to log storage

---

## Related Documentation

- **Root README**: [../README.md](../README.md) - Project overview
- **Code Architecture**: [../backend/README.md](../backend/README.md) - Telemetry implementation
- **Deployment**: [../deployment/README.md](../deployment/README.md) - Log Analytics setup
- **Security**: [../security/README.md](../security/README.md) - Audit logging

**Enterprise Observability**: `C:\projects\enterprise_architecture\02-tech-stack.md` (LangSmith section)

**Agent Instructions**: [../CLAUDE.md](../CLAUDE.md)

---

**Last Updated:** 2025-12-27 (Phase 1: Enterprise Alignment)
