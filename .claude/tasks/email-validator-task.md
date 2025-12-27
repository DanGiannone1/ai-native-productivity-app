# Task: Create Email Validator Utility

## Objective
Create a new file `src/utils/email-validator.ts` with an email validation function.

## Requirements

### Function Specifications
- **Function Name**: Use a descriptive verb phrase (e.g., `validateEmail`, `isValidEmail`)
- **Input**: Accept an email string as a parameter
- **Output**: Return boolean (true if valid, false if invalid)

### Validation Rules
The function must check for:
1. Presence of @ symbol
2. Text before the @ symbol (local part)
3. Text after the @ symbol (domain part)
4. Basic format compliance

### Code Standards (from CLAUDE.md)
- Use camelCase for function names
- Keep function focused and short (under 30 lines)
- Add documentation for the public function
- Use meaningful variable names
- Include comments explaining "why" for complex logic
- Handle edge cases appropriately

### Best Practices (from .claude/rules/)
- Follow KISS principle - keep it simple
- Don't over-engineer the solution
- Make the code easy to test
- Validate all external inputs
- Provide meaningful validation logic

## Deliverable
Create `c:\projects\productivity\src\utils\email-validator.ts` with the email validation function.
