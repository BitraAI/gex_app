/**
 * util
 */
import { HueArc, Options, SpecifiedColorChannels } from '../typedef';
/**
 * get max length
 * @param [opt] - options
 * @returns max length
 */
export declare const getMaxLength: (opt?: Options) => number;
/**
 * split value
 * NOTE: comments are stripped, it can be preserved if, in the options param,
 * `delimiter` is either ',' or '/' and with `preserveComment` set to `true`
 * @param value - CSS value
 * @param [opt] - options
 * @returns array of values
 */
export declare const splitValue: (value: string, opt?: Options) => string[];
/**
 * extract dashed-ident tokens
 * @param value - CSS value
 * @returns array of dashed-ident tokens
 */
export declare const extractDashedIdent: (value: string) => string[];
/**
 * round to specified precision
 * @param value - numeric value
 * @param bit - minimum bits
 * @returns rounded value
 */
export declare const roundToPrecision: (value: number, bit?: number) => number;
/**
 * interpolate hue
 * @param hueA - hue value
 * @param hueB - hue value
 * @param arc - shorter | longer | increasing | decreasing
 * @returns result - [hueA, hueB]
 */
export declare const interpolateHue: (hueA: number, hueB: number, arc?: HueArc | string) => [number, number];
/**
 * resolve length in pixels
 * @param value - value
 * @param unit - unit
 * @param [opt] - options
 * @returns pixelated value
 */
export declare const resolveLengthInPixels: (value: number | string, unit: string | undefined, opt?: Options) => number;
/**
 * angle to deg
 * @param angle
 * @returns deg: 0..360
 */
export declare const angleToDeg: (angle: string) => number;
/**
 * number to hex string
 * @param value - numeric value
 * @returns hex string
 */
export declare const numberToHexString: (value: number) => string;
/**
 * parse alpha
 * @param [alpha] - alpha value
 * @returns alpha: 0..1
 */
export declare const parseAlpha: (alpha?: string) => number;
/**
 * parse hex alpha
 * @param value - alpha value in hex string
 * @returns alpha: 0..1
 */
export declare const parseHexAlpha: (value: string) => number;
/**
 * cache invalid color value
 * @param key - cache key
 * @param nullable - is nullable
 * @returns cached value
 */
export declare const cacheInvalidColorValue: (cacheKey: string, format: string, nullable?: boolean) => SpecifiedColorChannels | string | null;
/**
 * resolve invalid color value
 * @param format - output format
 * @param nullable - is nullable
 * @returns resolved value
 */
export declare const resolveInvalidColorValue: (format: string, nullable?: boolean) => SpecifiedColorChannels | string | null;
