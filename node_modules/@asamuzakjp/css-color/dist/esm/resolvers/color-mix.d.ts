/**
 * color-mix
 */
import { ChannelNoneFlags, ColorAndPct, ColorFormat, ColorResolverFn, ColorSpace, ColorSpaceParseResult, InterpolatedComponents, NormalizedPercentages, NumStrColorChannels, Options, SpecifiedColorChannels, TriColorChannels } from '../typedef';
/**
 * parse color space
 * @param arg - color space argument string
 * @returns object containing colorSpace and hueArc, or null if invalid
 */
export declare const parseColorSpace: (arg: string) => ColorSpaceParseResult | null;
/**
 * parse color and percentage
 * @param arg - color and percentage argument string
 * @returns object containing color string and percentage string
 */
export declare const parseColorAndPct: (arg: string) => ColorAndPct;
/**
 * resolve if nested function
 * @param colorStr - color string
 * @param opt - options
 * @param resolver - resolver function
 * @returns resolved color string or original string
 */
export declare const resolveIfNested: (colorStr: string, opt: Options, resolver: ColorResolverFn) => string;
/**
 * normalize percentages
 * @param pctA - percentage for color A
 * @param pctB - percentage for color B
 * @returns object containing normalized percentages and multiplier, or null if invalid
 */
export declare const normalizePercentages: (pctA: string, pctB: string) => NormalizedPercentages | null;
/**
 * process color
 * @param colorStr - color string
 * @param opt - options
 * @returns specified color string
 */
export declare const processColor: (colorStr: string, opt: Options) => string;
/**
 * build specified color mix
 * @param colorSpace - color space
 * @param hueArc - hue interpolation method
 * @param colorA - first color
 * @param pctA - percentage for first color
 * @param colorB - second color
 * @param pctB - percentage for second color
 * @param opt - options
 * @returns specified value string for color-mix()
 */
export declare const buildSpecifiedColorMix: (colorSpace: string, hueArc: string, colorA: string, pctA: string, colorB: string, pctB: string, opt: Options) => string;
/**
 * Perform alpha-weighted interpolation for color components.
 * @param compA - color components for color A
 * @param compB - color components for color B
 * @param alphaA - alpha channel value for color A
 * @param alphaB - alpha channel value for color B
 * @param pA - normalized ratio for first color
 * @param pB - normalized ratio for second color
 * @returns object containing interpolated components and combined alpha
 */
export declare const interpolateComponents: (compA: TriColorChannels, compB: TriColorChannels, alphaA: number, alphaB: number, pA: number, pB: number) => InterpolatedComponents;
/**
 * Format computed color into specified or computed channel array.
 * @param colorSpace - target color space
 * @param comps - 3-channel color components
 * @param nones - boolean flags indicating if channels are 'none'
 * @param alpha - calculated alpha channel value
 * @param m - multiplier factor
 * @param format - output format option
 * @param rgbOverride - optional pre-calculated RGB channels
 * @returns specified color channels array
 */
export declare const formatMixedColor: (colorSpace: ColorSpace, comps: TriColorChannels, nones: ChannelNoneFlags, alpha: number, m: number, format: ColorFormat, rgbOverride?: TriColorChannels) => SpecifiedColorChannels;
/**
 * Fetch raw channels or fallback for currentcolor
 * @param color - color input string
 * @param convertFn - conversion function
 * @param opt - conversion options
 * @returns color channel values or null if invalid
 */
export declare const getRawChannels: (color: string | NumStrColorChannels, convertFn: (c: string, opt: any) => any, opt: any) => NumStrColorChannels | null;
/**
 * Mix colors in srgb or srgb-linear space.
 * @param colorSpace - color space name ('srgb' | 'srgb-linear')
 * @param colorA - first color string
 * @param colorB - second color string
 * @param pA - ratio for first color
 * @param pB - ratio for second color
 * @param format - output format
 * @param m - multiplier factor
 * @returns mixed color channels or null
 */
export declare const mixSrgbSpace: (colorSpace: ColorSpace, colorA: string, colorB: string, pA: number, pB: number, format: ColorFormat, m: number) => SpecifiedColorChannels | null;
/**
 * Mix colors in xyz, xyz-d50, or xyz-d65 space.
 * @param colorSpace - color space name
 * @param colorA - first color string
 * @param colorB - second color string
 * @param pA - ratio for first color
 * @param pB - ratio for second color
 * @param format - output format
 * @param m - multiplier factor
 * @returns mixed color channels or null
 */
export declare const mixXyzSpace: (colorSpace: string, colorA: string, colorB: string, pA: number, pB: number, format: string, m: number) => SpecifiedColorChannels | null;
/**
 * Mix colors in hsl or hwb space.
 * @param colorSpace - color space name ('hsl' | 'hwb')
 * @param hueArc - hue interpolation method
 * @param colorA - first color string
 * @param colorB - second color string
 * @param pA - ratio for first color
 * @param pB - ratio for second color
 * @param format - output format
 * @param m - multiplier factor
 * @returns mixed color channels or null
 */
export declare const mixHslHwbSpace: (colorSpace: string, hueArc: string, colorA: string, colorB: string, pA: number, pB: number, format: string, m: number) => SpecifiedColorChannels | null;
/**
 * Mix colors in lch or oklch space.
 * @param colorSpace - color space name ('lch' | 'oklch')
 * @param hueArc - hue interpolation method
 * @param colorA - first color string
 * @param colorB - second color string
 * @param pA - ratio for first color
 * @param pB - ratio for second color
 * @param format - output format
 * @param m - multiplier factor
 * @returns mixed color channels or null
 */
export declare const mixLchSpace: (colorSpace: string, hueArc: string, colorA: string, colorB: string, pA: number, pB: number, format: string, m: number) => SpecifiedColorChannels | null;
/**
 * Mix colors in lab or oklab space.
 * @param colorSpace - color space name ('lab' | 'oklab')
 * @param colorA - first color string
 * @param colorB - second color string
 * @param pA - ratio for first color
 * @param pB - ratio for second color
 * @param format - output format
 * @param m - multiplier factor
 * @returns mixed color channels or null
 */
export declare const mixLabSpace: (colorSpace: string, colorA: string, colorB: string, pA: number, pB: number, format: string, m: number) => SpecifiedColorChannels | null;
/**
 * compute mixed color
 * @param colorSpace - color space
 * @param hueArc - hue interpolation method
 * @param colorA - first color
 * @param colorB - second color
 * @param pA - normalized ratio for first color
 * @param pB - normalized ratio for second color
 * @param m - multiplier
 * @param format - output format
 * @param nullable - is nullable
 * @param cacheKey - cache key
 * @returns computed color channels or null
 */
export declare const computeMixedColor: (colorSpace: string, hueArc: string, colorA: string, colorB: string, pA: number, pB: number, m: number, format: string, nullable: boolean, cacheKey: string) => SpecifiedColorChannels | null;
/**
 * resolve color-mix()
 * @param value - color-mix color value
 * @param opt - options
 * @param resolver - resolver function
 * @returns resolved color - [cs, v1, v2, v3, alpha], '(empty)', null
 */
export declare const resolveColorMix: (value: string, opt?: Options, resolver?: ColorResolverFn) => SpecifiedColorChannels | string | null;
