/**
 * transform
 */
import { ColorChannels, NumStrColorChannels, ReadonlyColorMatrix, TriColorChannels, ValidateColorComponentsOptions } from '../typedef';
/**
 * validate color components
 * @param arr - color components
 * @param opt - options
 * @param opt.alpha - alpha channel
 * @param opt.minLength - min length
 * @param opt.maxLength - max length
 * @param opt.minRange - min range
 * @param opt.maxRange - max range
 * @param opt.validateRange - validate range
 * @returns result - validated color components
 */
export declare const validateColorComponents: (arr: ColorChannels | TriColorChannels, opt?: ValidateColorComponentsOptions) => ColorChannels | TriColorChannels;
/**
 * normalize color components
 * @param colorA - color components [v1, v2, v3, v4]
 * @param colorB - color components [v1, v2, v3, v4]
 * @param [skip] - skip validate
 * @returns result - [colorA, colorB]
 */
export declare const normalizeColorComponents: (colorA: NumStrColorChannels, colorB: NumStrColorChannels, skip?: boolean) => [ColorChannels, ColorChannels];
/**
 * transform matrix
 * @param mtx - 3 * 3 matrix
 * @param vct - vector
 * @param [skip] - skip validate
 * @returns TriColorChannels - [p1, p2, p3]
 */
export declare const transformMatrix: (mtx: ReadonlyColorMatrix, vct: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform rgb to linear rgb
 * @param rgb - [r, g, b] r|g|b: 0..255
 * @param [skip] - skip validate
 * @returns TriColorChannels - [r, g, b] r|g|b: 0..1
 */
export declare const transformRgbToLinearRgb: (rgb: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform rgb to xyz
 * @param rgb - [r, g, b] r|g|b: 0..255
 * @param [skip] - skip validate
 * @returns TriColorChannels - [x, y, z]
 */
export declare const transformRgbToXyz: (rgb: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform rgb to xyz-d50
 * @param rgb - [r, g, b] r|g|b: 0..255 alpha: 0..1
 * @returns TriColorChannels - [x, y, z]
 */
export declare const transformRgbToXyzD50: (rgb: TriColorChannels) => TriColorChannels;
/**
 * transform linear rgb to rgb
 * @param rgb - [r, g, b] r|g|b: 0..1
 * @param [round] - round result
 * @returns TriColorChannels - [r, g, b] r|g|b: 0..255
 */
export declare const transformLinearRgbToRgb: (rgb: TriColorChannels, round?: boolean) => TriColorChannels;
/**
 * transform xyz to rgb
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [r, g, b] r|g|b: 0..255
 */
export declare const transformXyzToRgb: (xyz: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform xyz to xyz-d50
 * @param xyz - [x, y, z]
 * @returns TriColorChannels - [x, y, z]
 */
export declare const transformXyzToXyzD50: (xyz: TriColorChannels) => TriColorChannels;
/**
 * transform xyz to hsl
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [h, s, l]
 */
export declare const transformXyzToHsl: (xyz: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform xyz to hwb
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [h, w, b]
 */
export declare const transformXyzToHwb: (xyz: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform xyz to oklab
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [l, a, b]
 */
export declare const transformXyzToOklab: (xyz: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform xyz to oklch
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [l, c, h]
 */
export declare const transformXyzToOklch: (xyz: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform xyz D50 to rgb
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [r, g, b] r|g|b: 0..255
 */
export declare const transformXyzD50ToRgb: (xyz: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform xyz-d50 to lab
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [l, a, b]
 */
export declare const transformXyzD50ToLab: (xyz: TriColorChannels, skip?: boolean) => TriColorChannels;
/**
 * transform xyz-d50 to lch
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [l, c, h]
 */
export declare const transformXyzD50ToLch: (xyz: TriColorChannels, skip?: boolean) => TriColorChannels;
