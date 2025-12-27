# Coding Guidelines

These guidelines define the coding standards for this project. The validator agent will check implementations against these rules.

## General Principles

1. **Clarity over cleverness**: Write code that is easy to understand
2. **Consistency**: Follow established patterns in the codebase
3. **Simplicity**: Choose the simplest solution that works
4. **Maintainability**: Write code that is easy to modify and extend

## Naming Conventions

### Variables
<!-- Customize these for your project -->
- Use descriptive names that indicate purpose
- Use camelCase for variables and functions
- Use PascalCase for classes and types
- Use SCREAMING_SNAKE_CASE for constants

### Files
- Use kebab-case for file names (e.g., `user-service.ts`)
- Match file names to their primary export when applicable
- Use `.test.` or `.spec.` suffix for test files

### Functions
- Use verb phrases for function names (e.g., `getUserById`, `calculateTotal`)
- Keep functions focused on a single task
- Limit function parameters (prefer objects for 3+ parameters)

## Code Structure

### Functions
- Keep functions short and focused (aim for under 30 lines)
- Extract complex conditions into well-named variables or functions
- Return early to reduce nesting

### Classes
- Follow single responsibility principle
- Keep classes focused and cohesive
- Prefer composition over inheritance

### Modules
- One primary export per file when possible
- Group related functionality together
- Keep imports organized (external, then internal)

## Documentation

### Comments
- Explain "why", not "what" (code should be self-documenting)
- Keep comments up to date with code changes
- Use TODO comments sparingly and include context

### Function Documentation
- Document public APIs and exported functions
- Include parameter descriptions for complex functions
- Document return values and potential exceptions

## Error Handling

- Handle errors at appropriate boundaries
- Provide meaningful error messages
- Don't swallow errors silently
- Use typed errors when the language supports it

---

*Customize these guidelines to match your team's preferences and project requirements.*

