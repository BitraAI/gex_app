/**
 * convert-hex
 */

import {
  transformMatrix,
  validateColorComponents,
  transformLinearRgbToRgb,
  transformRgbToLinearRgb
} from '../matrix/transform';
import { ColorChannels, MatchedRegExp3, MatchedRegExp4 } from '../typedef';
import { isString } from '../utils/common';
import { numberToHexString, parseHexAlpha } from '../utils/util';

/* constants */
import {
  MATRIX_D50_TO_D65,
  MATRIX_L_RGB_TO_XYZ,
  MATRIX_XYZ_TO_L_RGB
} from '../matrix/matrix';
import { HEX, QUAD, MAX_RGB } from '../utils/constant';

/**
 * convert rgb to hex color
 * @param rgb - [r, g, b, alpha] r|g|b: 0..255 alpha: 0..1
 * @returns hex color
 */
export const convertRgbToHex = (rgb: ColorChannels): string => {
  const [r, g, b, alpha] = validateColorComponents(rgb, {
    alpha: true,
    maxRange: MAX_RGB
  }) as ColorChannels;
  const rr = numberToHexString(r);
  const gg = numberToHexString(g);
  const bb = numberToHexString(b);
  const aa = numberToHexString(alpha * MAX_RGB);
  return aa === 'ff' ? `#${rr}${gg}${bb}` : `#${rr}${gg}${bb}${aa}`;
};

/**
 * convert linear rgb to hex color
 * @param rgb - [r, g, b, alpha] r|g|b|alpha: 0..1
 * @param [skip] - skip validate
 * @returns hex color
 */
export const convertLinearRgbToHex = (
  rgb: ColorChannels,
  skip: boolean = false
): string => {
  let r: number, g: number, b: number, alpha: number;
  if (skip) {
    [r, g, b, alpha] = rgb;
  } else {
    [r, g, b, alpha] = validateColorComponents(rgb, {
      minLength: QUAD
    }) as ColorChannels;
  }
  [r, g, b] = transformLinearRgbToRgb([r, g, b], true);
  const rr = numberToHexString(r);
  const gg = numberToHexString(g);
  const bb = numberToHexString(b);
  const aa = numberToHexString(alpha * MAX_RGB);
  return aa === 'ff' ? `#${rr}${gg}${bb}` : `#${rr}${gg}${bb}${aa}`;
};

/**
 * convert xyz to hex color
 * @param xyz - [x, y, z, alpha]
 * @returns hex color
 */
export const convertXyzToHex = (xyz: ColorChannels): string => {
  const [x, y, z, alpha] = validateColorComponents(xyz, {
    minLength: QUAD,
    validateRange: false
  }) as ColorChannels;
  const [r, g, b] = transformMatrix(MATRIX_XYZ_TO_L_RGB, [x, y, z], true);
  return convertLinearRgbToHex(
    [
      Math.min(Math.max(r, 0), 1),
      Math.min(Math.max(g, 0), 1),
      Math.min(Math.max(b, 0), 1),
      alpha
    ],
    true
  );
};

/**
 * convert xyz D50 to hex color
 * @param xyz - [x, y, z, alpha]
 * @returns hex color
 */
export const convertXyzD50ToHex = (xyz: ColorChannels): string => {
  const [x, y, z, alpha] = validateColorComponents(xyz, {
    minLength: QUAD,
    validateRange: false
  }) as ColorChannels;
  const xyzD65 = transformMatrix(MATRIX_D50_TO_D65, [x, y, z], true);
  const [r, g, b] = transformMatrix(MATRIX_XYZ_TO_L_RGB, xyzD65, true);
  return convertLinearRgbToHex([
    Math.min(Math.max(r, 0), 1),
    Math.min(Math.max(g, 0), 1),
    Math.min(Math.max(b, 0), 1),
    alpha
  ]);
};

/**
 * convert hex color to rgb
 * @param value - hex color value
 * @returns ColorChannels - [r, g, b, alpha] r|g|b: 0..255 alpha: 0..1
 */
export const convertHexToRgb = (value: string): ColorChannels => {
  if (isString(value)) {
    value = value.toLowerCase().trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  if (!(
    /^#[\da-f]{6}$/.test(value) ||
    /^#[\da-f]{3}$/.test(value) ||
    /^#[\da-f]{8}$/.test(value) ||
    /^#[\da-f]{4}$/.test(value)
  )) {
    throw new SyntaxError(`Invalid property value: ${value}`);
  }
  const arr: number[] = [];
  if (/^#[\da-f]{3}$/.test(value)) {
    const [, r, g, b] = value.match(
      /^#([\da-f])([\da-f])([\da-f])$/
    ) as MatchedRegExp3;
    arr.push(
      parseInt(`${r}${r}`, HEX),
      parseInt(`${g}${g}`, HEX),
      parseInt(`${b}${b}`, HEX),
      1
    );
  } else if (/^#[\da-f]{4}$/.test(value)) {
    const [, r, g, b, alpha] = value.match(
      /^#([\da-f])([\da-f])([\da-f])([\da-f])$/
    ) as MatchedRegExp4;
    arr.push(
      parseInt(`${r}${r}`, HEX),
      parseInt(`${g}${g}`, HEX),
      parseInt(`${b}${b}`, HEX),
      parseHexAlpha(`${alpha}${alpha}`)
    );
  } else if (/^#[\da-f]{8}$/.test(value)) {
    const [, r, g, b, alpha] = value.match(
      /^#([\da-f]{2})([\da-f]{2})([\da-f]{2})([\da-f]{2})$/
    ) as MatchedRegExp4;
    arr.push(
      parseInt(r, HEX),
      parseInt(g, HEX),
      parseInt(b, HEX),
      parseHexAlpha(alpha)
    );
  } else {
    const [, r, g, b] = value.match(
      /^#([\da-f]{2})([\da-f]{2})([\da-f]{2})$/
    ) as MatchedRegExp3;
    arr.push(parseInt(r, HEX), parseInt(g, HEX), parseInt(b, HEX), 1);
  }
  return arr as ColorChannels;
};

/**
 * convert hex color to linear rgb
 * @param value - hex color value
 * @returns ColorChannels - [r, g, b, alpha] r|g|b|alpha: 0..1
 */
export const convertHexToLinearRgb = (value: string): ColorChannels => {
  const [rr, gg, bb, alpha] = convertHexToRgb(value);
  const [r, g, b] = transformRgbToLinearRgb([rr, gg, bb], true);
  return [r, g, b, alpha];
};

/**
 * convert hex color to xyz
 * @param value - hex color value
 * @returns ColorChannels - [x, y, z, alpha]
 */
export const convertHexToXyz = (value: string): ColorChannels => {
  const [r, g, b, alpha] = convertHexToLinearRgb(value);
  const [x, y, z] = transformMatrix(MATRIX_L_RGB_TO_XYZ, [r, g, b], true);
  return [x, y, z, alpha];
};
