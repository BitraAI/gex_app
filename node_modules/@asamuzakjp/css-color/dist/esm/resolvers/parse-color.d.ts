/**
 * parse
 */
import { Options, SpecifiedColorChannels } from '../typedef';
/**
 * parse rgb()
 * @param value - rgb color value
 * @param opt - options
 * @returns parsed color - ['rgb', r, g, b, alpha], '(empty)', null
 */
export declare const parseRgb: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * parse hsl()
 * @param value - hsl color value
 * @param opt - options
 * @returns parsed color - ['rgb', r, g, b, alpha], '(empty)', null
 */
export declare const parseHsl: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * parse hwb()
 * @param value - hwb color value
 * @param opt - options
 * @returns parsed color - ['rgb', r, g, b, alpha], '(empty)', null
 */
export declare const parseHwb: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * parse lab()
 * @param value - lab color value
 * @param opt - options
 * @returns parsed color
 *   - [xyz-d50, x, y, z, alpha], ['lab', l, a, b, alpha], '(empty)', null
 */
export declare const parseLab: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * parse lch()
 * @param value - lch color value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-d50', x, y, z, alpha], ['lch', l, c, h, alpha], '(empty)', null
 */
export declare const parseLch: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * parse oklab()
 * @param value - oklab color value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-d65', x, y, z, alpha], ['oklab', l, a, b, alpha], '(empty)', null
 */
export declare const parseOklab: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * parse oklch()
 * @param value - oklch color value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-d65', x, y, z, alpha], ['oklch', l, c, h, alpha], '(empty)', null
 */
export declare const parseOklch: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * parse color()
 * @param value - color function value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-(d50|d65)', x, y, z, alpha], [cs, r, g, b, alpha], '(empty)', null
 */
export declare const parseColorFunc: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
/**
 * parse color value
 * @param value - CSS color value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-(d50|d65)', x, y, z, alpha], ['rgb', r, g, b, alpha]
 *   - value, '(empty)', null
 */
export declare const parseColorValue: (value: string, opt?: Options) => SpecifiedColorChannels | string | null;
