/**
 * String utility functions for common string manipulation tasks.
 *
 * @module string-helpers
 */

/**
 * Capitalizes the first letter of a string.
 *
 * @param {string} str - The string to capitalize
 * @returns {string} The string with the first letter capitalized
 * @throws {TypeError} If str is not a string
 */
function capitalize(str) {
  if (typeof str !== 'string') {
    throw new TypeError('Expected a string as input');
  }

  if (str.length === 0) {
    return str;
  }

  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Truncates a string to a maximum length and adds "..." if truncated.
 *
 * @param {string} str - The string to truncate
 * @param {number} maxLength - The maximum length before truncation
 * @returns {string} The truncated string with "..." appended if needed
 * @throws {TypeError} If str is not a string or maxLength is not a number
 * @throws {RangeError} If maxLength is less than 3
 */
function truncate(str, maxLength) {
  if (typeof str !== 'string') {
    throw new TypeError('Expected a string as input');
  }

  if (typeof maxLength !== 'number') {
    throw new TypeError('Expected maxLength to be a number');
  }

  if (maxLength < 3) {
    throw new RangeError('maxLength must be at least 3 to accommodate "..."');
  }

  if (str.length <= maxLength) {
    return str;
  }

  const ELLIPSIS = '...';
  const truncatedLength = maxLength - ELLIPSIS.length;
  return str.slice(0, truncatedLength) + ELLIPSIS;
}

module.exports = {
  capitalize,
  truncate
};
