# Enterprise Architecture Alignment Plan
## Prism Productivity MCP Server

**Generated:** 2025-12-27
**Status:** Ready for Implementation
**Approach:** Multi-Agent Orchestrated Workflow

---

## Executive Summary

This document outlines the comprehensive plan to align the Prism productivity MCP server with the enterprise architecture standards defined in `C:\projects\enterprise_architecture`.

**Overall Assessment:** Prism is ~60% aligned with enterprise standards. The foundation is solid, but critical gaps exist in documentation structure, project organization, and observability infrastructure.

---

## Gap Analysis

### ✅ Currently Aligned (60%)

1. **Multi-Agent Workflow System** - COMPLETE
   - Orchestrator, planner, validator, implementer, documentation agents configured
   - Workflow patterns match enterprise standards

2. **Technology Stack** - ALIGNED
   - Python as primary language ✓
   - UV package manager ✓
   - Azure Cosmos DB (serverless) ✓
   - FastMCP server ✓
   - Ruff linting/formatting ✓

3. **Infrastructure Pattern** - ALIGNED
   - 3-RG silo model (shared, dev, prod) ✓
   - PowerShell for IaC ✓
   - Azure Container Apps ready ✓

4. **Code Quality Patterns** - ALIGNED
   - Telemetry decorators present ✓
   - Error handling utilities ✓
   - Configuration management ✓

### ❌ Critical Gaps (40%)

#### 1. Documentation Structure - MAJOR GAP (Priority 1)

**Current State:**
- Single root README.md
- No folder-level READMEs
- CLAUDE.md doesn't follow enterprise template structure

**Enterprise Requirement:**
```
my-service/
├── README.md              # ENTRYPOINT - purpose, structure, local setup
├── .cursorrules           # AI agent instructions (or CLAUDE.md, AGENTS.md)
├── src/                   # Application code
│   └── README.md          # Code architecture, key modules, patterns
├── tests/                 # Test suite
│   └── README.md          # Testing strategy, how to run, coverage
├── deployment/            # Infrastructure & CI/CD
│   └── README.md          # Environments, provisioning, deploy process
├── security/              # Auth, secrets, network config
│   └── README.md          # Auth flows, secret locations, access control
└── monitoring/            # Observability
    └── README.md          # Dashboards, alerts, log queries
```

**Gap:** Missing 5 folder-level READMEs + root README doesn't follow entrypoint pattern

**Impact:** AI agents cannot navigate codebase efficiently, missing context leads to errors

---

#### 2. Agent Instructions File - MAJOR GAP (Priority 1)

**Current State:**
- CLAUDE.md has multi-agent workflow rules
- Missing complexity assessment guidance
- Missing "start from README" mandate
- Missing retrospective/codify step
- Doesn't match enterprise template structure

**Enterprise Requirement:**
- Must start with "RULE #1: START FROM THE README"
- Must include complexity assessment (simple vs complex tasks)
- Must include retrospective/codify process
- Must include project-specific standards section

**Impact:** Agents may skip critical exploration steps, miss context

---

#### 3. Project Structure - MISALIGNMENT (Priority 2)

**Current State:**
```
C:\projects\productivity\
├── backend/              # Code here
├── scripts/
├── tests/
```

**Enterprise Standard:**
```
C:\projects\productivity\
├── src/
│   └── productivity_mcp/  # Code here (named after project)
├── deployment/            # Infrastructure scripts
├── security/              # Auth configs
├── monitoring/            # Observability
├── tests/
```

**Gap:** Code in `backend/` instead of `src/productivity_mcp/`

**Impact:** Inconsistent with enterprise patterns, harder for agents to navigate

---

#### 4. Observability - PARTIAL (Priority 2)

**Current State:**
- Basic logging with telemetry decorators
- No structured JSON logging
- No LangSmith integration

**Enterprise Requirement:**
- JSON-formatted logs for Azure Log Analytics ingestion
- LangSmith tracing for AI-driven interactions
- Structured logging for agent queries

**Gap:** Missing LangSmith, non-structured logging

**Impact:** Cannot trace AI reasoning steps, logs not queryable by AI agents

---

#### 5. Authentication Scaffolding - NOT IMPLEMENTED (Priority 3)

**Current State:**
- Dev-mode auth bypass (DISABLE_AUTH=true)
- Scalekit OAuth commented out
- No ScalekitProvider integration in mcp_server.py

**Enterprise Requirement:**
- Scalekit OAuth integration ready (even if disabled in dev)
- Scope validation with M2M whitelist pattern
- Auth infrastructure in place for Phase 2

**Gap:** Auth code not scaffolded, only config placeholders exist

**Impact:** Phase 2 OAuth integration requires significant refactoring

---

#### 6. Environment Configuration - INCOMPLETE (Priority 3)

**Current State (.env.example):**
```env
ENVIRONMENT=dev
COSMOS_HOST=...
COSMOS_KEY=...
DISABLE_AUTH=true
LOG_LEVEL=INFO
```

**Enterprise Template (.env.example):**
```env
ENVIRONMENT=dev
# Azure Resource Groups
RESOURCE_GROUP_SHARED=...
RESOURCE_GROUP_DEV=...
RESOURCE_GROUP_PROD=...
# Cosmos DB
COSMOS_HOST=...
COSMOS_KEY=...
# AI Providers
CLAUDE_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=...
# Scalekit OAuth
SCALEKIT_ENVIRONMENT_URL=...
# etc.
```

**Gap:** Missing enterprise-standard environment variables

**Impact:** Missing observability config, incomplete resource group tracking

---

#### 7. Dependencies - MINOR GAPS (Priority 3)

**Current State (pyproject.toml):**
```toml
dependencies = [
    "fastmcp==2.2.0",
    "azure-cosmos==4.7.0",
    "uvicorn[standard]==0.32.1",
    "pydantic==2.10.4",
    "python-dotenv==1.0.1",
]
```

**Enterprise Standard:**
```toml
dependencies = [
    # ... existing ...
    "langsmith==0.1.147",  # MISSING - AI observability
    "anthropic==0.34.2",   # MISSING - direct Claude API (optional)
    "tiktoken==0.8.0",     # MISSING - token counting (optional)
]
```

**Gap:** LangSmith missing, optional AI utilities missing

**Impact:** No AI tracing capability

---

## Implementation Plan

### Phased Approach

**Rationale:** Tackle documentation first (foundation for all agents), then structure, then features.

---

### PHASE 1: Documentation Structure (CRITICAL - DO FIRST)

**Goal:** Establish README-first documentation model for AI agent navigation

**Files to Create:**

1. **src/README.md** (NEW)
   - Purpose: Code architecture and module documentation
   - Content:
     - Overview of productivity_mcp architecture
     - Key modules: mcp_server, services, schema, tools, auth, utils
     - Design patterns: singleton Cosmos client, tool decorators, schema validation
     - Data model: multi-document Cosmos design
     - Future: relationship to deployment/, security/, monitoring/

2. **deployment/README.md** (NEW - move scripts/ here)
   - Purpose: Infrastructure and deployment processes
   - Content:
     - 3-RG silo explanation (shared, dev, prod)
     - setup-infrastructure.ps1 usage
     - Cosmos DB configuration (serverless, partitioning)
     - Container Apps deployment (future)
     - Environment-specific differences

3. **security/README.md** (NEW)
   - Purpose: Authentication, authorization, secrets management
   - Content:
     - Current state: Dev mode (DISABLE_AUTH=true)
     - Future: Scalekit OAuth 2.1 integration
     - Scope requirements: Read, Write
     - M2M client whitelist pattern
     - Secret storage: Azure Key Vault (future)
     - Network security: IP restrictions (future)

4. **monitoring/README.md** (NEW)
   - Purpose: Observability and diagnostics
   - Content:
     - Current state: Basic logging
     - Future: LangSmith AI tracing
     - Future: JSON structured logs → Azure Log Analytics
     - Future: Application Insights dashboards
     - Log query examples for AI agents

5. **tests/README.md** (NEW)
   - Purpose: Testing strategy and execution
   - Content:
     - Current state: Basic pytest setup
     - Test categories: unit, integration, MCP tools
     - Running tests: .\run_local.ps1 test
     - Seed data: .\run_local.ps1 seed
     - Future: Coverage targets, CI/CD integration

6. **README.md** (UPDATE - Root Entrypoint)
   - **Current:** Feature-focused, usage examples
   - **Update to:**
     - Lead with: "AI agents: Start here, then fan out to folder READMEs"
     - Clear repo structure with links to each folder README
     - Quick start (local setup)
     - Link to CLAUDE.md for agent instructions
     - Link to enterprise_architecture for philosophy

7. **CLAUDE.md** (UPDATE - Agent Instructions)
   - **Current:** Has multi-agent workflow, missing enterprise patterns
   - **Update to match enterprise template:**
     - **RULE #1: START FROM THE README** (add this section)
     - **COMPLEXITY ASSESSMENT** (add this section)
     - **COMPLEX TASK RULES** (enhance existing multi-agent workflow section)
     - **RETROSPECTIVE (Codify Step)** (add this section)
     - **PROJECT-SPECIFIC STANDARDS** (enhance existing section)
     - Keep existing multi-agent orchestration workflow

**Validation Criteria:**
- [ ] All 5 folder READMEs exist and are complete
- [ ] Root README clearly states "start here, fan out"
- [ ] Root README links to all folder READMEs
- [ ] CLAUDE.md has "RULE #1: START FROM README"
- [ ] CLAUDE.md has complexity assessment section
- [ ] CLAUDE.md has retrospective/codify section
- [ ] Agent instructions match enterprise template structure

**Estimated Effort:** 3-4 hours (content writing)

---

### PHASE 2: Project Structure Realignment (MEDIUM PRIORITY)

**Goal:** Move code to `src/productivity_mcp/` to match enterprise standard

**Migration Steps:**

1. **Create new structure:**
   ```
   src/
   └── productivity_mcp/
       ├── __init__.py
       ├── __main__.py
       ├── mcp_server.py
       ├── config.py
       ├── cosmos_client.py
       ├── auth/
       ├── schema/
       ├── services/
       ├── tools/
       └── utils/
   ```

2. **Move files:**
   - `backend/* → src/productivity_mcp/*`
   - Preserve all directory structure within

3. **Update imports:**
   - Replace `from backend.` → `from productivity_mcp.`
   - Update all relative imports
   - Use find-and-replace with validation

4. **Update pyproject.toml:**
   - Update `packages` configuration for hatchling
   - Ensure `src/` is discovered correctly

5. **Update run_local.ps1:**
   - Change `PYTHONPATH` from `backend` to `src`
   - Update module invocation: `python -m productivity_mcp.mcp_server`

6. **Update setup-infrastructure.ps1:**
   - Update any references to `backend/`

7. **Move scripts/ to deployment/:**
   - `scripts/ → deployment/scripts/`
   - Update run_local.ps1 references

**Validation Criteria:**
- [ ] All code in `src/productivity_mcp/`
- [ ] All imports updated and working
- [ ] `.\run_local.ps1 mcp` starts server successfully
- [ ] `.\run_local.ps1 test` passes all tests
- [ ] No `backend/` directory remains (except in .venv)

**Estimated Effort:** 2-3 hours (careful refactoring)

---

### PHASE 3: Observability Infrastructure (MEDIUM PRIORITY)

**Goal:** Add LangSmith AI tracing and structured logging

**Implementation Steps:**

1. **Add LangSmith Dependency:**
   ```toml
   dependencies = [
       # ... existing ...
       "langsmith==0.1.147",
   ]
   ```
   - Run `uv sync` to install

2. **Update config.py:**
   ```python
   # LangSmith Observability
   LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
   LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "productivity-mcp")
   LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
   ```

3. **Create src/productivity_mcp/utils/langsmith_tracer.py:**
   - Wrapper for LangSmith tracing
   - Optional tracing decorator (enabled if LANGSMITH_TRACING=true)
   - Trace MCP tool calls, schema operations, entity CRUD

4. **Update mcp_server.py:**
   - Add LangSmith tracing to tool functions (optional decorator)
   - Trace tool inputs, outputs, durations
   - Link to LangSmith project for visualization

5. **Implement JSON Structured Logging:**
   - Update logging configuration in mcp_server.py
   - Use JSON formatter for production mode
   - Keep human-readable logs for dev mode
   - Include: timestamp, level, message, tool_name, user_id, duration_ms, success

6. **Update .env.example:**
   ```env
   # LangSmith (AI Observability)
   LANGSMITH_API_KEY=lsv2_your-key-here
   LANGSMITH_PROJECT=productivity-mcp
   LANGSMITH_TRACING=true  # Set to false to disable
   ```

**Validation Criteria:**
- [ ] LangSmith dependency installed
- [ ] LangSmith config in config.py
- [ ] LangSmith tracer utility created
- [ ] Tool calls traced (when LANGSMITH_TRACING=true)
- [ ] JSON logging implemented (production mode)
- [ ] .env.example updated with LangSmith vars

**Estimated Effort:** 2-3 hours

---

### PHASE 4: Authentication Scaffolding (LOWER PRIORITY)

**Goal:** Add Scalekit OAuth infrastructure (ready for Phase 2, disabled in MVP)

**Implementation Steps:**

1. **Update mcp_server.py:**
   - Import ScalekitProvider from fastmcp
   - Add conditional auth initialization:
     ```python
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
     else:
         mcp = FastMCP("Productivity MCP Server", dependencies=[])
     ```

2. **Create src/productivity_mcp/auth/scalekit_auth.py:**
   - `_require_scope(scope: str)` function (from enterprise template)
   - Checks JWT scopes or M2M whitelist
   - Returns None if authorized, error message if not

3. **Update Tools with Scope Validation:**
   - Add scope checks to each tool (Read, Write)
   - Example:
     ```python
     @mcp.tool()
     def create_entity(...):
         error = _require_scope("Write")
         if error:
             return {"error": error}
         # ... existing logic
     ```

4. **Update .env.example:**
   - Ensure Scalekit vars are documented (already present)

**Validation Criteria:**
- [ ] ScalekitProvider conditionally initialized
- [ ] Scope validation function created
- [ ] Tools validate scopes when auth enabled
- [ ] Server still works with DISABLE_AUTH=true
- [ ] Ready for Scalekit setup in Phase 2

**Estimated Effort:** 2-3 hours

---

### PHASE 5: Standards Compliance (POLISH)

**Goal:** Full alignment with enterprise standards

**Implementation Steps:**

1. **Update .env.example:**
   - Add all enterprise-standard variables
   - Match enterprise template structure
   - Include resource group tracking
   - Include Azure Communication Services (future)
   - Include all AI provider options

2. **Enhance run_local.ps1:**
   - Add helper functions from enterprise template:
     - `Load-EnvFile` (more robust)
     - Better error handling
     - PYTHONPATH management
   - Match enterprise template structure

3. **Update pyproject.toml:**
   - Add optional dependencies:
     - `anthropic` (for direct Claude API calls, future)
     - `tiktoken` (for token counting, future)
   - Match enterprise template structure
   - Add [tool.pytest.ini_options] section

4. **Create deployment/README.md Content:**
   - Document deployment process
   - Document infrastructure setup
   - Document environment differences (dev vs prod)

**Validation Criteria:**
- [ ] .env.example has all enterprise variables
- [ ] run_local.ps1 matches enterprise patterns
- [ ] pyproject.toml has enterprise-standard dependencies
- [ ] All documentation complete

**Estimated Effort:** 2-3 hours

---

## Risk Assessment

### Low Risk (Green)
- Documentation additions (no code changes)
- .env.example updates (template only)
- Adding new dependencies (optional features)

### Medium Risk (Yellow)
- Project structure migration (requires careful import updates)
- LangSmith integration (new feature, optional)

### Higher Risk (Orange)
- Scalekit OAuth scaffolding (authentication critical, but currently disabled)

### Mitigation Strategies
1. **Test after each phase** - Run `.\run_local.ps1 test` after each change
2. **Git commits per phase** - Easy rollback if needed
3. **Validation checklist** - Ensure criteria met before proceeding
4. **Keep DISABLE_AUTH=true** - Don't enable OAuth until Phase 2 is ready

---

## Success Criteria (Overall)

### Documentation (Phase 1)
- [ ] All folder READMEs exist and complete
- [ ] Root README serves as proper entrypoint
- [ ] CLAUDE.md matches enterprise agent-instructions template
- [ ] AI agents can navigate using README-first approach

### Structure (Phase 2)
- [ ] Code in `src/productivity_mcp/`
- [ ] All imports updated
- [ ] Server starts and runs successfully
- [ ] Tests pass

### Observability (Phase 3)
- [ ] LangSmith integration functional (when enabled)
- [ ] JSON logging implemented
- [ ] Logs queryable by AI agents

### Authentication (Phase 4)
- [ ] Scalekit OAuth scaffolding in place
- [ ] Scope validation ready
- [ ] Works with auth disabled (current MVP state)
- [ ] Ready for Phase 2 OAuth enablement

### Standards (Phase 5)
- [ ] .env.example complete with all enterprise vars
- [ ] run_local.ps1 matches enterprise patterns
- [ ] pyproject.toml has enterprise-standard dependencies
- [ ] All documentation complete

---

## Execution Strategy

### Recommended Approach

**Use Multi-Agent Orchestrated Workflow:**

1. **Phase 1 (Documentation)**
   - PLANNER: Create detailed content for each README
   - VALIDATOR: Verify completeness and enterprise alignment
   - IMPLEMENTER: Write the README files
   - VALIDATOR: Verify all files exist and are complete
   - DOCUMENTATION: Update links and cross-references

2. **Phase 2 (Structure)**
   - PLANNER: Create step-by-step migration plan
   - VALIDATOR: Verify plan covers all imports and references
   - IMPLEMENTER: Execute migration carefully
   - VALIDATOR: Verify server runs and tests pass
   - DOCUMENTATION: Update READMEs with new structure

3. **Phase 3 (Observability)**
   - PLANNER: Design LangSmith integration approach
   - VALIDATOR: Verify design matches enterprise patterns
   - IMPLEMENTER: Add LangSmith and JSON logging
   - VALIDATOR: Verify tracing works and logs are structured
   - DOCUMENTATION: Update monitoring/README.md

4. **Phase 4 (Authentication)**
   - PLANNER: Design Scalekit scaffolding approach
   - VALIDATOR: Verify auth pattern matches enterprise template
   - IMPLEMENTER: Add auth scaffolding
   - VALIDATOR: Verify server works with auth disabled
   - DOCUMENTATION: Update security/README.md

5. **Phase 5 (Standards)**
   - PLANNER: Identify remaining gaps
   - VALIDATOR: Verify all enterprise standards covered
   - IMPLEMENTER: Complete final updates
   - VALIDATOR: Final compliance check
   - DOCUMENTATION: Final documentation polish

### Timeline Estimate

- **Phase 1:** 3-4 hours (documentation writing)
- **Phase 2:** 2-3 hours (code migration)
- **Phase 3:** 2-3 hours (observability features)
- **Phase 4:** 2-3 hours (auth scaffolding)
- **Phase 5:** 2-3 hours (final polish)

**Total:** 11-16 hours (with validation and testing)

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Get approval** to proceed
3. **Execute Phase 1** using multi-agent workflow
4. **Validate Phase 1** before proceeding
5. **Continue phases** sequentially

---

## Notes

- This plan preserves all existing functionality
- Changes are additive (new patterns) not destructive
- Each phase is independently valuable
- Phases can be executed in order or selectively
- Git commits after each phase enable easy rollback

---

**END OF PLAN**

Ready for execution via multi-agent orchestrated workflow.
