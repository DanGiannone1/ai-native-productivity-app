# Project Configuration for Claude Code

This file defines the rules, context, and guidelines for AI agents working on this project.

## Project Overview

**Project Name**: Productivity  
**Description**: [Add your project description here]  
**Primary Language**: [Add primary language, e.g., TypeScript, Python]

## Agent Configuration

This project uses a multi-agent orchestration system:

- **Orchestrator**: Manages workflow and coordinates other agents
- **Implementer**: Executes coding tasks
- **Validator**: Reviews implementations for compliance

### Invoking the Multi-Agent System

To use the orchestrator for complex tasks:
```
Use the orchestrator agent to [describe your task]
```

## Project Rules

### Code Style
<!-- Add your specific code style rules here -->
- Use consistent indentation (spaces or tabs - specify your preference)
- Keep line length reasonable (80-120 characters)
- Use meaningful variable and function names
- Add comments for complex logic

### File Organization
<!-- Add your file organization rules here -->
- Keep related files together
- Use clear, descriptive file names
- Follow the established project structure

### Commit Standards
<!-- Add your commit message rules here -->
- Use clear, descriptive commit messages
- Reference issue numbers when applicable

## Reference Documents

The following documents contain additional guidelines:

- **Coding Guidelines**: `.claude/rules/guidelines.md`
- **Best Practices**: `.claude/rules/best-practices.md`

## Custom Rules

You are authorized to edit any files in this repo as needed. Do not ask me to edit.


### Security Rules
- Never commit secrets or API keys
- Sanitize user inputs
- Use secure defaults

### Quality Rules
- No commented-out code in production
- Remove unused imports and variables
- Handle errors appropriately

---

*This file is read by Claude Code agents. Customize it to match your project's requirements.*

