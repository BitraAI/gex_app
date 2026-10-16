/**
 * resolve-color
 */
import { Options, SpecifiedColorChannels } from '../typedef';
/**
 * resolve color value
 * @param value - CSS color value
 * @param opt - options
 * @returns resolved color
 *   - [cs, v1, v2, v3, alpha], value, '(empty)', null
 */
export declare const resolveColorValue: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * resolve color()
 * @param value - color function value
 * @param opt - options
 * @returns resolved color - [cs, v1, v2, v3, alpha], '(empty)', null
 */
export declare const resolveColorFunc: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * resolve color
 * @param value - CSS color value
 * @param opt - options
 * @returns resolved color
 */
export declare const resolveColor: (value: string, opt?: Options) => string | null;
/**
 * is valid color
 * @param value - CSS value
 * @param opt - options
 * @returns result
 */
export declare const isValidColor: (value: unknown, opt?: Options) => boolean;
