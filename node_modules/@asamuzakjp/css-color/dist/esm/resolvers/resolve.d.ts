/**
 * resolve
 */
import { Options } from '../typedef';
/**
 * resolve CSS color
 * @param value - CSS color value. system colors are not supported
 * @param opt - options
 * @returns resolved value
 */
export declare const resolve: (value: string, opt?: Options) => string | null;
/**
 * is color
 * @param value - CSS value
 * @param opt - options
 * @returns result
 */
export declare const isColor: (value: unknown, opt?: Options) => boolean;
