/**
 * convert-hex
 */
import { ColorChannels } from '../typedef';
/**
 * convert rgb to hex color
 * @param rgb - [r, g, b, alpha] r|g|b: 0..255 alpha: 0..1
 * @returns hex color
 */
export declare const convertRgbToHex: (rgb: ColorChannels) => string;
/**
 * convert linear rgb to hex color
 * @param rgb - [r, g, b, alpha] r|g|b|alpha: 0..1
 * @param [skip] - skip validate
 * @returns hex color
 */
export declare const convertLinearRgbToHex: (rgb: ColorChannels, skip?: boolean) => string;
/**
 * convert xyz to hex color
 * @param xyz - [x, y, z, alpha]
 * @returns hex color
 */
export declare const convertXyzToHex: (xyz: ColorChannels) => string;
/**
 * convert xyz D50 to hex color
 * @param xyz - [x, y, z, alpha]
 * @returns hex color
 */
export declare const convertXyzD50ToHex: (xyz: ColorChannels) => string;
/**
 * convert hex color to rgb
 * @param value - hex color value
 * @returns ColorChannels - [r, g, b, alpha] r|g|b: 0..255 alpha: 0..1
 */
export declare const convertHexToRgb: (value: string) => ColorChannels;
/**
 * convert hex color to linear rgb
 * @param value - hex color value
 * @returns ColorChannels - [r, g, b, alpha] r|g|b|alpha: 0..1
 */
export declare const convertHexToLinearRgb: (value: string) => ColorChannels;
/**
 * convert hex color to xyz
 * @param value - hex color value
 * @returns ColorChannels - [x, y, z, alpha]
 */
export declare const convertHexToXyz: (value: string) => ColorChannels;
