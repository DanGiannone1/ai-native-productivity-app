# Enterprise Architecture Alignment Task

## Objective
Align the Prism productivity MCP server with the enterprise architecture standards defined in `../enterprise_architecture`.

## Context
- Enterprise architecture repo: C:\projects\enterprise_architecture
- Prism repo: C:\projects\productivity
- Task initiated: 2025-12-27

## Gap Analysis Completed
See orchestrator analysis for detailed findings.

## Implementation Phases

### Phase 1: Documentation Structure (CRITICAL)
- [ ] Create src/README.md (code architecture)
- [ ] Create deployment/README.md (infrastructure & deployment)
- [ ] Create security/README.md (auth, secrets, access control)
- [ ] Create monitoring/README.md (observability)
- [ ] Create tests/README.md (testing strategy)
- [ ] Update root README.md (proper entrypoint)
- [ ] Update CLAUDE.md (match enterprise agent-instructions template)

### Phase 2: Project Structure Realignment
- [ ] Move backend/ → src/productivity_mcp/
- [ ] Update all imports
- [ ] Update pyproject.toml
- [ ] Update run_local.ps1
- [ ] Update setup-infrastructure.ps1 references

### Phase 3: Authentication & Observability
- [ ] Add LangSmith integration
- [ ] Add Scalekit OAuth scaffolding
- [ ] Implement JSON-structured logging
- [ ] Update config.py with new variables

### Phase 4: Standards Compliance
- [ ] Update .env.example (enterprise template)
- [ ] Enhance run_local.ps1 (enterprise patterns)
- [ ] Update pyproject.toml dependencies
- [ ] Add missing enterprise-standard utilities

## Success Criteria
1. All folder-level READMEs exist and follow enterprise pattern
2. Root README serves as proper entrypoint
3. CLAUDE.md matches enterprise agent-instructions template
4. Code structure matches enterprise pattern (src/)
5. LangSmith integration functional
6. Scalekit OAuth scaffolding in place (ready for Phase 2)
7. JSON logging implemented
8. All enterprise-standard dependencies present

## Notes
- This is a multi-agent orchestrated task
- Each phase will be validated before proceeding
- Preserve all existing functionality
- Add missing patterns without breaking current implementation
