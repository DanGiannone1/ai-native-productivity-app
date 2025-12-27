# Best Practices

This document outlines best practices that the validator agent will check against. These complement the coding guidelines and focus on patterns and approaches.

## Code Quality

### DRY (Don't Repeat Yourself)
- Extract repeated code into reusable functions
- Use constants for repeated values
- Create shared utilities for common operations
- Exception: Some duplication is acceptable if it improves clarity

### KISS (Keep It Simple, Stupid)
- Avoid premature optimization
- Don't over-engineer solutions
- Choose boring technology when appropriate
- Add complexity only when necessary

### YAGNI (You Aren't Gonna Need It)
- Don't implement features "just in case"
- Build for current requirements
- Refactor when new requirements emerge
- Avoid speculative generalization

## Architecture

### Separation of Concerns
- Keep business logic separate from presentation
- Isolate external dependencies
- Use clear boundaries between modules

### Dependencies
- Minimize external dependencies
- Pin dependency versions
- Keep dependencies up to date
- Audit dependencies for security

## Testing Considerations

### Testability
- Write code that is easy to test
- Use dependency injection where appropriate
- Avoid global state
- Keep side effects at the edges

### Test Coverage
- Test critical paths and edge cases
- Don't aim for 100% coverage blindly
- Focus on meaningful tests over quantity

## Performance

### Efficiency
- Consider algorithmic complexity
- Avoid unnecessary operations in loops
- Be mindful of memory usage
- Profile before optimizing

### Caching
- Cache expensive operations when appropriate
- Invalidate caches correctly
- Consider cache consistency

## Security

### Input Validation
- Validate all external inputs
- Sanitize data before use
- Use allowlists over denylists when possible

### Data Protection
- Never log sensitive data
- Use secure communication channels
- Follow principle of least privilege

### Authentication & Authorization
- Use established libraries for auth
- Implement proper session management
- Validate permissions on every request

## Maintainability

### Code Review
- Write code with reviewers in mind
- Keep changes focused and atomic
- Provide context in commit messages

### Debugging
- Include meaningful logging
- Make errors actionable
- Preserve error context

### Documentation
- Keep documentation close to code
- Update docs when code changes
- Document decisions and rationale

---

*These best practices are guidelines, not absolutes. Use judgment and adapt to context.*

