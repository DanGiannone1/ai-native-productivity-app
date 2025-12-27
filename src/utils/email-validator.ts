/**
 * Validates an email address according to basic rules.
 *
 * This function performs basic email validation by checking for:
 * - Presence of exactly one @ symbol
 * - Non-empty text before the @ (local part)
 * - Non-empty text after the @ (domain part)
 * - Basic domain structure (contains at least one dot after @)
 *
 * Note: This is a basic validator and does not implement full RFC 5322 compliance.
 * For production use, consider using a more comprehensive validation library.
 *
 * @param email - The email string to validate
 * @returns True if the email meets basic validation rules, false otherwise
 */
export function isValidEmail(email: string): boolean {
  // Handle null, undefined, or non-string inputs
  if (!email || typeof email !== 'string') {
    return false;
  }

  // Trim whitespace to handle edge cases
  const trimmedEmail = email.trim();

  // Basic length check - email should have minimum length
  if (trimmedEmail.length < 3) {
    return false;
  }

  // Check for exactly one @ symbol
  const atSymbolCount = (trimmedEmail.match(/@/g) || []).length;
  if (atSymbolCount !== 1) {
    return false;
  }

  // Split email into local and domain parts
  const [localPart, domainPart] = trimmedEmail.split('@');

  // Validate local part (before @)
  if (!localPart || localPart.length === 0) {
    return false;
  }

  // Validate domain part (after @)
  if (!domainPart || domainPart.length === 0) {
    return false;
  }

  // Check that domain has at least one dot
  if (!domainPart.includes('.')) {
    return false;
  }

  // Ensure domain doesn't start or end with a dot
  if (domainPart.startsWith('.') || domainPart.endsWith('.')) {
    return false;
  }

  // Check for valid characters in domain extension (after last dot)
  const domainParts = domainPart.split('.');
  const extension = domainParts[domainParts.length - 1];
  if (!extension || extension.length < 2) {
    return false;
  }

  return true;
}
