/**
 * Array utility functions for common array operations.
 */

/**
 * Removes duplicate values from an array.
 * Uses Set for efficient O(n) deduplication while preserving order of first occurrence.
 *
 * @param {Array} arr - The array to remove duplicates from
 * @returns {Array} A new array with duplicates removed
 * @throws {TypeError} If the input is not an array
 *
 * @example
 * removeDuplicates([1, 2, 2, 3, 4, 4, 5]); // [1, 2, 3, 4, 5]
 * removeDuplicates(['a', 'b', 'a', 'c']); // ['a', 'b', 'c']
 */
function removeDuplicates(arr) {
  if (!Array.isArray(arr)) {
    throw new TypeError('Input must be an array');
  }

  return [...new Set(arr)];
}

/**
 * Splits an array into chunks of a specified size.
 * The last chunk may be smaller if the array length is not evenly divisible by size.
 *
 * @param {Array} arr - The array to split into chunks
 * @param {number} size - The size of each chunk (must be a positive integer)
 * @returns {Array<Array>} An array of arrays, where each sub-array has at most `size` elements
 * @throws {TypeError} If arr is not an array or size is not a number
 * @throws {RangeError} If size is less than 1
 *
 * @example
 * chunk([1, 2, 3, 4, 5], 2); // [[1, 2], [3, 4], [5]]
 * chunk(['a', 'b', 'c', 'd'], 3); // [['a', 'b', 'c'], ['d']]
 */
function chunk(arr, size) {
  if (!Array.isArray(arr)) {
    throw new TypeError('First argument must be an array');
  }

  if (typeof size !== 'number') {
    throw new TypeError('Size must be a number');
  }

  if (size < 1 || !Number.isInteger(size)) {
    throw new RangeError('Size must be a positive integer');
  }

  const result = [];

  for (let i = 0; i < arr.length; i += size) {
    result.push(arr.slice(i, i + size));
  }

  return result;
}

module.exports = {
  removeDuplicates,
  chunk
};
