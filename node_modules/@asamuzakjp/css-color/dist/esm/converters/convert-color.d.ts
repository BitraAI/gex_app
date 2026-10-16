/**
 * color
 */
import { ColorChannels, ColorChannelsWithPowerless, LinearRgbOptions, Options } from '../typedef';
/**
 * convert color value to linear rgb
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [r, g, b, alpha] r|g|b|alpha: 0..1
 */
export declare const convertColorToLinearRgb: (value: string, opt?: LinearRgbOptions) => ColorChannels | null;
/**
 * convert color value to rgb
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [r, g, b, alpha] r|g|b: 0..255 alpha: 0..1
 */
export declare const convertColorToRgb: (value: string, opt?: Options) => ColorChannels | null;
/**
 * convert color value to xyz
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [x, y, z, alpha]
 */
export declare const convertColorToXyz: (value: string, opt?: Options) => ColorChannels | null;
/**
 * convert color value to hsl
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [h, s, l, alpha], hue may be powerless
 */
export declare const convertColorToHsl: (value: string, opt?: Options) => ColorChannels | ColorChannelsWithPowerless | null;
/**
 * convert color value to hwb
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [h, w, b, alpha], hue may be powerless
 */
export declare const convertColorToHwb: (value: string, opt?: Options) => ColorChannels | [number | string, number, number, number] | null;
/**
 * convert color value to lab
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [l, a, b, alpha]
 */
export declare const convertColorToLab: (value: string, opt?: Options) => ColorChannels | null;
/**
 * convert color value to lch
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [l, c, h, alpha], hue may be powerless
 */
export declare const convertColorToLch: (value: string, opt?: Options) => ColorChannels | [number, number, number | string, number] | null;
/**
 * convert color value to oklab
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [l, a, b, alpha]
 */
export declare const convertColorToOklab: (value: string, opt?: Options) => ColorChannels | null;
/**
 * convert color value to oklch
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [l, c, h, alpha], hue may be powerless
 */
export declare const convertColorToOklch: (value: string, opt?: Options) => ColorChannels | [number, number, number | string, number] | null;
