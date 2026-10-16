/**
 * resolve
 */

import { Options } from '../typedef';
import { isValidColor, resolveColor } from './resolve-color';

/**
 * resolve CSS color
 * @param value - CSS color value. system colors are not supported
 * @param opt - options
 * @returns resolved value
 */
export const resolve = (value: string, opt: Options = {}): string | null => {
  const options = {
    ...opt
  };
  return resolveColor(value, options);
};

/**
 * is color
 * @param value - CSS value
 * @param opt - options
 * @returns result
 */
export const isColor = (value: unknown, opt: Options = {}): boolean => {
  const options = {
    ...opt,
    nullable: true
  };
  return !!isValidColor(value, options);
};
