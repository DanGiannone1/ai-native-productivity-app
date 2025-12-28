# Project Configuration for Claude Code

This file defines the rules, context, and guidelines for AI agents working on this project.

## Project Overview

**Project Name**: Productivity
**Description**: AI-driven schema-flexible productivity MCP server with multi-agent development workflow
**Primary Language**: Python, TypeScript
**Architecture**: MCP Server with Cosmos DB backend

---

## 🚨 RULE #1: START FROM THE README

**Before doing ANYTHING, read the root `README.md` and fan out from there.**

This repository follows a README-first documentation model:
- `README.md` (root) → Entrypoint. Purpose, structure, local setup.
- `src/README.md` → Code architecture, key modules
- `deployment/README.md` → Infra, environments, deploy process
- `security/README.md` → Auth, secrets, access control
- `monitoring/README.md` → Dashboards, alerts, logs
- `tests/README.md` → Testing strategy, how to run

**Navigation pattern:**
1. Read root README to understand purpose and structure
2. Follow links to relevant folder READMEs for deeper context
3. Only then dive into code files

**If you skip this step, you will make mistakes.**

---

## COMPLEXITY ASSESSMENT

**BEFORE IMPLEMENTING**: Determine if this is a complex task.

**Simple tasks** (proceed directly):
- Factual questions
- Single-file typo fixes
- Running scripts
- Trivial documentation updates

**Complex tasks** (requires multi-agent workflow):
- Architecture changes
- Multi-file refactors
- Debugging
- New feature implementation
- Code refactoring or restructuring
- Bug fixes affecting multiple files
- Integration with external systems
- Database schema changes
- API endpoint changes
- Security-sensitive modifications
- **ANY task where missing context could cause problems**

**If unclear, assume COMPLEX.**

---

## 🚨 MANDATORY MULTI-AGENT WORKFLOW

**ALL COMPLEX TASKS MUST USE THE ORCHESTRATOR AGENT.**

This project uses a rigorous multi-agent orchestration system to prevent the common failure mode of AI coding agents missing critical context, files, or dependencies.

### Complex Task Rules

For complex tasks, we prioritize **accuracy and completeness over speed.**

#### Before Implementation:

1. **Start from README** - Read root README, then fan out to relevant folder READMEs
2. **Read extensively** - 20-30+ files, not 5-10. Include docs, configs, tests.
3. **Explain your understanding** - Go back and forth until you have shared understanding
4. **Finalize the plan** - Implementation steps, testing approach, docs to update
5. **Get confirmation** - Do not proceed until user confirms the plan

#### During Implementation:

- Check that code and documentation stay aligned
- If you find a discrepancy, stop and call it out
- Do not rush. Correctness > speed.

#### After Implementation:

1. Verify your work (tests, lints, self-review)
2. Offer a retrospective: "Would you like to codify any lessons learned?"

### How to Invoke

For all complex tasks:
```
Use the orchestrator agent to [describe your task]
```

The orchestrator will automatically coordinate the planner, validator, implementer, and documentation agents in the correct sequence.

---

## Agent Architecture

This project uses a multi-agent orchestration system with specialized agents:

### 1. **Orchestrator** (`.claude/agents/orchestrator.md`)
   - **Role**: Master coordinator that manages the entire workflow
   - **When to use**: For ANY complex task
   - **Workflow**: Planner → Validator (plan) → Implementer → Validator (code) → Documentation

### 2. **Planner** (`.claude/agents/planner.md`)
   - **Role**: Creates exhaustive, detailed implementation plans
   - **Philosophy**: Completeness over speed
   - **Process**:
     - Reads ALL project documentation (README, CLAUDE.md, guidelines, best-practices)
     - Explores entire relevant codebase using Glob, Grep, Read, LSP
     - Maps ALL affected files and dependencies
     - Creates junior-developer-ready step-by-step instructions
     - Identifies minimum 3 edge cases/risks
   - **Output**: Detailed plan with specific files, line numbers, code examples, and standards

### 3. **Validator** (`.claude/agents/validator.md`)
   - **Role**: Quality gate that validates both plans AND implementations
   - **Validates Plans For**:
     - Evidence of thorough codebase exploration
     - Documentation review completion
     - Complete dependency mapping
     - Junior-developer-ready detail level
     - Edge case identification
     - Standards compliance
   - **Validates Implementations For**:
     - Plan adherence
     - Code quality (DRY, KISS, YAGNI)
     - Standards compliance (naming, organization, comments)
     - Security requirements
     - No obvious bugs
   - **Authority**: Can FAIL plans or implementations with specific feedback

### 4. **Implementer** (`.claude/agents/implementer.md`)
   - **Role**: Executes approved implementation plans with precision
   - **Approach**: Follow the plan exactly, do not improvise or deviate
   - **Responsibilities**:
     - Execute ALL steps in sequence
     - Use exact naming conventions from plan
     - Handle all edge cases identified
     - Report blockers immediately

### 5. **Documentation** (`.claude/agents/documentation.md`)
   - **Role**: Maintains all project documentation
   - **Handles**:
     - README files (top-level and folder-level)
     - Inline code comments
     - API documentation
     - Architecture documentation
     - Keeping docs synchronized with code changes

---

## RETROSPECTIVE (Codify Step)

After completing a complex task, do a retrospective with the AI:

> "What technical challenges did we face? Was there anything you struggled with that clearer instructions might have helped with?"

This is collaborative. Get the user's input, then update the agent instructions or documentation if needed.

**When doing a retrospective:**
1. **Technical challenges**: What was tricky?
2. **AI meta-reflection**: What did you struggle with? Would clearer instructions have helped?
3. **Codification**: Should we update CLAUDE.md, any README, or best-practices?

The goal is to make each task compound on the previous ones, making the next task easier.

---

## WHEN FIXING BUGS

Before patching the symptom, ask:
> "What underlying principle, if documented, would make this class of bug impossible?"

Check if the principle already exists in a README or documentation file. Prefer one source of truth over duplication.

---

## PROJECT-SPECIFIC STANDARDS

### Technology Stack
- **Backend**: Python with MCP protocol
- **Database**: Azure Cosmos DB (NoSQL, schema-flexible)
- **Infrastructure**: Azure (Cosmos DB, App Service)
- **Deployment**: Automated via PowerShell scripts

### Architecture Patterns
- MCP server with tool-based interface
- Schema-flexible data model (no rigid schemas)
- AI-driven data interpretation
- Cosmos DB for persistent storage

### Key Files to Always Consider
- `src/productivity_mcp/server.py` - Main MCP server
- `src/productivity_mcp/cosmos_db.py` - Database operations
- `pyproject.toml` - Python dependencies
- `scripts/` - Infrastructure and deployment scripts

### Code Style

**Naming Conventions** (per `.claude/rules/guidelines.md`):
- Variables and functions: `camelCase`
- Classes and types: `PascalCase`
- Constants: `SCREAMING_SNAKE_CASE`
- Files: `kebab-case` (e.g., `user-service.ts`)

**Code Structure**:
- Use consistent indentation (4 spaces for Python, 2 spaces for TypeScript/JavaScript)
- Keep line length reasonable (80-120 characters)
- Use meaningful variable and function names
- Add comments for complex logic (explain "why", not "what")
- Keep functions focused and short (aim for under 30 lines)

### File Organization

- Keep related files together
- Use clear, descriptive file names
- Follow the established project structure:
  ```
  /src          - Source code
  /.claude      - Agent configurations and rules
  /scripts      - Utility scripts
  /docs         - Documentation
  ```

### Commit Standards

- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Follow conventional commits format when possible

---

## Reference Documents

**CRITICAL**: All agents MUST read these documents before planning or implementing:

1. **Root README**: `README.md`
   - Project purpose, structure, local setup

2. **Coding Guidelines**: `.claude/rules/guidelines.md`
   - Naming conventions, code structure, documentation standards

3. **Best Practices**: `.claude/rules/best-practices.md`
   - DRY, KISS, YAGNI principles
   - Security, performance, maintainability practices

4. **Agent Configurations**:
   - `.claude/agents/orchestrator.md` - Workflow coordination
   - `.claude/agents/planner.md` - Planner requirements
   - `.claude/agents/validator.md` - Validation criteria
   - `.claude/agents/implementer.md` - Implementation standards
   - `.claude/agents/documentation.md` - Documentation standards

---

## Custom Rules

### Authorization

**You are authorized to edit ANY files in this repo as needed. Do not ask for permission to edit.**

The multi-agent system provides sufficient quality gates (plan validation, implementation validation) to ensure changes meet standards.

### Security Rules

- **NEVER commit secrets or API keys**
- Sanitize and validate all user inputs
- Use secure defaults
- Follow principle of least privilege
- Use environment variables for configuration
- No sensitive data in logs

### Quality Rules

- **Completeness over Speed**: Take time to explore thoroughly
- **No Assumptions**: Verify patterns by reading actual code
- **Test Edge Cases**: Consider and handle error conditions
- **Follow Existing Patterns**: Match how similar things are done in the codebase
- **Standards Compliance**: Explicitly follow guidelines and best practices
- **Documentation**: Keep docs synchronized with code

### Development Workflow

1. **Planning Phase**:
   - Read root README first
   - Read this file (CLAUDE.md)
   - Read all `.claude/rules/*.md` files
   - Explore codebase extensively
   - Map all dependencies
   - Create detailed plan

2. **Validation Phase**:
   - Verify plan completeness
   - Check standards compliance
   - Assess risks and edge cases

3. **Implementation Phase**:
   - Follow approved plan exactly
   - Use correct naming conventions
   - Handle all edge cases
   - Write clean, maintainable code

4. **Verification Phase**:
   - Validate against plan
   - Check code quality
   - Verify standards compliance

5. **Documentation Phase**:
   - Update relevant docs
   - Add inline comments where needed
   - Keep examples current

6. **Retrospective Phase**:
   - Identify what was challenging
   - Codify lessons learned
   - Update instructions if needed

---

## Why This Approach?

### The Problem

As codebases grow, AI coding agents frequently:
- ❌ Miss important files or functions
- ❌ Make assumptions about patterns without verifying
- ❌ Skip reading documentation
- ❌ Overlook edge cases and dependencies
- ❌ Create circular debugging loops

This wastes time and creates frustration.

### The Solution

The multi-agent system with mandatory workflow ensures:
- ✅ **README-First**: Always start with project overview and context
- ✅ **Thorough Exploration**: Planner MUST explore entire codebase
- ✅ **Documentation Review**: All docs read before planning
- ✅ **Quality Gates**: Validator catches issues early
- ✅ **Standards Compliance**: Explicit checks against guidelines
- ✅ **Edge Case Handling**: Required to identify minimum 3 risks
- ✅ **Junior-Dev-Ready Plans**: So detailed that implementation can't fail
- ✅ **Continuous Improvement**: Retrospectives codify lessons learned

### The Cost-Benefit

**Cost**: Extra time upfront for planning and validation
**Benefit**: No circular debugging, no missing context, no rework

**The thoroughness always pays off.**

---

## Frequently Asked Questions

**Q: Do I really need to use the orchestrator for every complex task?**
A: For ANY task that involves writing or modifying code beyond a simple typo fix, YES. Only skip for pure documentation updates or trivial single-line fixes.

**Q: What if I'm in a hurry?**
A: The multi-agent workflow actually saves time by preventing rework from missed context. Rushing leads to longer overall time.

**Q: Can I skip the planner if I already know what to do?**
A: NO. The planner ensures you didn't miss anything. Even "obvious" tasks often have hidden dependencies.

**Q: What if validation fails repeatedly?**
A: After 3 attempts, the orchestrator will escalate to the user for clarification. This prevents infinite loops.

**Q: Should I read the README first even for simple questions?**
A: For factual questions or simple queries, you can skip directly to answering. For implementation tasks, ALWAYS start with README.

---

## Summary

**For ALL complex tasks, invoke the orchestrator:**

```
Use the orchestrator agent to [your task description]
```

The orchestrator will:
1. 🔍 Engage planner for exhaustive planning
2. ✓ Validate the plan for completeness
3. 🔨 Execute with implementer
4. ✓ Validate the implementation
5. 📝 Update documentation
6. 🔄 Offer retrospective for continuous improvement
7. ✅ Deliver quality result

**This is not optional. This is how we ensure quality.**

---

*Last Updated: 2025-12-27*
