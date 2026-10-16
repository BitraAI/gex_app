/**
 * color
 */

import {
  transformMatrix,
  transformLinearRgbToRgb,
  transformXyzD50ToLab,
  transformXyzD50ToLch,
  transformXyzToHsl,
  transformXyzToHwb,
  transformXyzToOklab,
  transformXyzToOklch
} from '../matrix/transform';
import {
  parseColorFunc,
  parseColorValue,
  parseHsl,
  parseHwb,
  parseLab,
  parseLch,
  parseOklab,
  parseOklch
} from '../resolvers/parse-color';
import {
  resolveColorFunc,
  resolveColorValue
} from '../resolvers/resolve-color';
import {
  ColorChannels,
  ColorChannelsWithPowerless,
  ComputedColorChannels,
  LinearRgbOptions,
  MatchedRegExp,
  Options,
  StringColorSpacedChannels,
  TriColorChannels
} from '../typedef';
import { isString } from '../utils/common';

/* constants */
import { MATRIX_XYZ_TO_L_RGB } from '../matrix/matrix';
import {
  FN_COLOR,
  MAX_RGB,
  NONE,
  SYN_FN_COLOR,
  SYN_HSL,
  SYN_HSL_LV3,
  SYN_LCH,
  SYN_MOD,
  VAL_COMP,
  VAL_MIX
} from '../utils/constant';

/* regexp */
const REG_FN_COLOR = new RegExp(`^color\\(\\s*(${SYN_FN_COLOR})\\s*\\)$`);
const REG_HSL = new RegExp(`^hsla?\\(\\s*(${SYN_HSL}|${SYN_HSL_LV3})\\s*\\)$`);
const REG_HWB = new RegExp(`^hwb\\(\\s*(${SYN_HSL})\\s*\\)$`);
const REG_LAB = new RegExp(`^lab\\(\\s*(${SYN_MOD})\\s*\\)$`);
const REG_LCH = new RegExp(`^lch\\(\\s*(${SYN_LCH})\\s*\\)$`);
const REG_OKLAB = new RegExp(`^oklab\\(\\s*(${SYN_MOD})\\s*\\)$`);
const REG_OKLCH = new RegExp(`^oklch\\(\\s*(${SYN_LCH})\\s*\\)$`);

/**
 * convert color value to linear rgb
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [r, g, b, alpha] r|g|b|alpha: 0..1
 */
export const convertColorToLinearRgb = (
  value: string,
  opt: LinearRgbOptions = {}
): ColorChannels | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { colorSpace = '', format = '' } = opt;
  let cs = '';
  let r, g, b, alpha, x, y, z;
  if (format === VAL_MIX) {
    let xyz;
    if (value.startsWith(FN_COLOR)) {
      xyz = parseColorFunc(value, opt);
    } else {
      xyz = parseColorValue(value, opt);
    }
    if (xyz === null) {
      return null;
    }
    [cs, x, y, z, alpha] = xyz as ComputedColorChannels;
    if (cs === colorSpace) {
      return [x, y, z, alpha];
    }
    [r, g, b] = transformMatrix(MATRIX_XYZ_TO_L_RGB, [x, y, z], true);
  } else if (value.startsWith(FN_COLOR)) {
    const [, val] = value.match(REG_FN_COLOR) as MatchedRegExp;
    const [cs] = val.match(/[^\s,/]+/g) as StringColorSpacedChannels;
    if (cs === 'srgb-linear') {
      [, r, g, b, alpha] = resolveColorFunc(value, {
        format: VAL_COMP
      }) as ComputedColorChannels;
    } else {
      [, x, y, z, alpha] = parseColorFunc(value) as ComputedColorChannels;
      [r, g, b] = transformMatrix(MATRIX_XYZ_TO_L_RGB, [x, y, z], true);
    }
  } else {
    [, x, y, z, alpha] = parseColorValue(value) as ComputedColorChannels;
    [r, g, b] = transformMatrix(MATRIX_XYZ_TO_L_RGB, [x, y, z], true);
  }
  return [
    Math.min(Math.max(r, 0), 1),
    Math.min(Math.max(g, 0), 1),
    Math.min(Math.max(b, 0), 1),
    alpha
  ];
};

/**
 * convert color value to rgb
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [r, g, b, alpha] r|g|b: 0..255 alpha: 0..1
 */
export const convertColorToRgb = (
  value: string,
  opt: Options = {}
): ColorChannels | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '' } = opt;
  let r, g, b, alpha;
  if (format === VAL_MIX) {
    let rgb;
    if (value.startsWith(FN_COLOR)) {
      rgb = resolveColorFunc(value, opt);
    } else {
      rgb = resolveColorValue(value, opt);
    }
    if (rgb === null) {
      return null;
    }
    [, r, g, b, alpha] = rgb as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    const [, val] = value.match(REG_FN_COLOR) as MatchedRegExp;
    const [cs] = val.match(/[^\s,/]+/g) as StringColorSpacedChannels;
    if (cs === 'srgb') {
      [, r, g, b, alpha] = resolveColorFunc(value, {
        format: VAL_COMP
      }) as ComputedColorChannels;
      r *= MAX_RGB;
      g *= MAX_RGB;
      b *= MAX_RGB;
    } else {
      [, r, g, b, alpha] = resolveColorFunc(value) as ComputedColorChannels;
    }
  } else if (/^(?:ok)?l(?:ab|ch)/.test(value)) {
    [r, g, b, alpha] = convertColorToLinearRgb(value) as ColorChannels;
    [r, g, b] = transformLinearRgbToRgb([r, g, b]);
  } else {
    [, r, g, b, alpha] = resolveColorValue(value, {
      format: VAL_COMP
    }) as ComputedColorChannels;
  }
  return [r, g, b, alpha];
};

/**
 * convert color value to xyz
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [x, y, z, alpha]
 */
export const convertColorToXyz = (
  value: string,
  opt: Options = {}
): ColorChannels | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { d50 = false, format = '' } = opt;
  let x, y, z, alpha;
  if (format === VAL_MIX) {
    let xyz;
    if (value.startsWith(FN_COLOR)) {
      xyz = parseColorFunc(value, opt);
    } else {
      xyz = parseColorValue(value, opt);
    }
    if (xyz === null) {
      return null;
    }
    [, x, y, z, alpha] = xyz as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    const [, val] = value.match(REG_FN_COLOR) as MatchedRegExp;
    const [cs] = val.match(/[^\s,/]+/g) as StringColorSpacedChannels;
    if (d50) {
      if (cs === 'xyz-d50') {
        [, x, y, z, alpha] = resolveColorFunc(value, {
          format: VAL_COMP
        }) as ComputedColorChannels;
      } else {
        [, x, y, z, alpha] = parseColorFunc(
          value,
          opt
        ) as ComputedColorChannels;
      }
    } else if (/^xyz(?:-d65)?$/.test(cs)) {
      [, x, y, z, alpha] = resolveColorFunc(value, {
        format: VAL_COMP
      }) as ComputedColorChannels;
    } else {
      [, x, y, z, alpha] = parseColorFunc(value) as ComputedColorChannels;
    }
  } else {
    [, x, y, z, alpha] = parseColorValue(value, opt) as ComputedColorChannels;
  }
  return [x, y, z, alpha];
};

/**
 * convert color value to hsl
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [h, s, l, alpha], hue may be powerless
 */
export const convertColorToHsl = (
  value: string,
  opt: Options = {}
): ColorChannels | ColorChannelsWithPowerless | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '' } = opt;
  let h, s, l, alpha;
  if (REG_HSL.test(value)) {
    [, h, s, l, alpha] = parseHsl(value, {
      format: 'hsl'
    }) as ComputedColorChannels;
    if (format === 'hsl') {
      return [Math.round(h), Math.round(s), Math.round(l), alpha];
    }
    return [h, s, l, alpha];
  }
  let x, y, z;
  if (format === VAL_MIX) {
    let xyz;
    if (value.startsWith(FN_COLOR)) {
      xyz = parseColorFunc(value, opt);
    } else {
      xyz = parseColorValue(value, opt);
    }
    if (xyz === null) {
      return null;
    }
    [, x, y, z, alpha] = xyz as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    [, x, y, z, alpha] = parseColorFunc(value) as ComputedColorChannels;
  } else {
    [, x, y, z, alpha] = parseColorValue(value) as ComputedColorChannels;
  }
  [h, s, l] = transformXyzToHsl([x, y, z], true) as TriColorChannels;
  if (format === 'hsl') {
    return [Math.round(h), Math.round(s), Math.round(l), alpha];
  }
  return [format === VAL_MIX && s === 0 ? NONE : h, s, l, alpha];
};

/**
 * convert color value to hwb
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [h, w, b, alpha], hue may be powerless
 */
export const convertColorToHwb = (
  value: string,
  opt: Options = {}
): ColorChannels | [number | string, number, number, number] | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '' } = opt;
  let h, w, b, alpha;
  if (REG_HWB.test(value)) {
    [, h, w, b, alpha] = parseHwb(value, {
      format: 'hwb'
    }) as ComputedColorChannels;
    if (format === 'hwb') {
      return [Math.round(h), Math.round(w), Math.round(b), alpha];
    }
    return [h, w, b, alpha];
  }
  let x, y, z;
  if (format === VAL_MIX) {
    let xyz;
    if (value.startsWith(FN_COLOR)) {
      xyz = parseColorFunc(value, opt);
    } else {
      xyz = parseColorValue(value, opt);
    }
    if (xyz === null) {
      return null;
    }
    [, x, y, z, alpha] = xyz as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    [, x, y, z, alpha] = parseColorFunc(value) as ComputedColorChannels;
  } else {
    [, x, y, z, alpha] = parseColorValue(value) as ComputedColorChannels;
  }
  [h, w, b] = transformXyzToHwb([x, y, z], true) as TriColorChannels;
  if (format === 'hwb') {
    return [Math.round(h), Math.round(w), Math.round(b), alpha];
  }
  return [format === VAL_MIX && w + b >= 100 ? NONE : h, w, b, alpha];
};

/**
 * convert color value to lab
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [l, a, b, alpha]
 */
export const convertColorToLab = (
  value: string,
  opt: Options = {}
): ColorChannels | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '' } = opt;
  let l, a, b, alpha;
  if (REG_LAB.test(value)) {
    [, l, a, b, alpha] = parseLab(value, {
      format: VAL_COMP
    }) as ComputedColorChannels;
    return [l, a, b, alpha];
  }
  let x, y, z;
  if (format === VAL_MIX) {
    let xyz;
    const options = {
      ...opt,
      d50: true
    };
    if (value.startsWith(FN_COLOR)) {
      xyz = parseColorFunc(value, options);
    } else {
      xyz = parseColorValue(value, options);
    }
    if (xyz === null) {
      return null;
    }
    [, x, y, z, alpha] = xyz as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    [, x, y, z, alpha] = parseColorFunc(value, {
      d50: true
    }) as ComputedColorChannels;
  } else {
    [, x, y, z, alpha] = parseColorValue(value, {
      d50: true
    }) as ComputedColorChannels;
  }
  [l, a, b] = transformXyzD50ToLab([x, y, z], true);
  return [l, a, b, alpha];
};

/**
 * convert color value to lch
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [l, c, h, alpha], hue may be powerless
 */
export const convertColorToLch = (
  value: string,
  opt: Options = {}
): ColorChannels | [number, number, number | string, number] | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '' } = opt;
  let l, c, h, alpha;
  if (REG_LCH.test(value)) {
    [, l, c, h, alpha] = parseLch(value, {
      format: VAL_COMP
    }) as ComputedColorChannels;
    return [l, c, h, alpha];
  }
  let x, y, z;
  if (format === VAL_MIX) {
    let xyz;
    const options = {
      ...opt,
      d50: true
    };
    if (value.startsWith(FN_COLOR)) {
      xyz = parseColorFunc(value, options);
    } else {
      xyz = parseColorValue(value, options);
    }
    if (xyz === null) {
      return null;
    }
    [, x, y, z, alpha] = xyz as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    [, x, y, z, alpha] = parseColorFunc(value, {
      d50: true
    }) as ComputedColorChannels;
  } else {
    [, x, y, z, alpha] = parseColorValue(value, {
      d50: true
    }) as ComputedColorChannels;
  }
  [l, c, h] = transformXyzD50ToLch([x, y, z], true);
  return [l, c, format === VAL_MIX && c === 0 ? NONE : h, alpha];
};

/**
 * convert color value to oklab
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [l, a, b, alpha]
 */
export const convertColorToOklab = (
  value: string,
  opt: Options = {}
): ColorChannels | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '' } = opt;
  let l, a, b, alpha;
  if (REG_OKLAB.test(value)) {
    [, l, a, b, alpha] = parseOklab(value, {
      format: VAL_COMP
    }) as ComputedColorChannels;
    return [l, a, b, alpha];
  }
  let x, y, z;
  if (format === VAL_MIX) {
    let xyz;
    if (value.startsWith(FN_COLOR)) {
      xyz = parseColorFunc(value, opt);
    } else {
      xyz = parseColorValue(value, opt);
    }
    if (xyz === null) {
      return null;
    }
    [, x, y, z, alpha] = xyz as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    [, x, y, z, alpha] = parseColorFunc(value) as ComputedColorChannels;
  } else {
    [, x, y, z, alpha] = parseColorValue(value) as ComputedColorChannels;
  }
  [l, a, b] = transformXyzToOklab([x, y, z], true);
  return [l, a, b, alpha];
};

/**
 * convert color value to oklch
 * @param value - CSS color value
 * @param opt - options
 * @returns ColorChannels | null - [l, c, h, alpha], hue may be powerless
 */
export const convertColorToOklch = (
  value: string,
  opt: Options = {}
): ColorChannels | [number, number, number | string, number] | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '' } = opt;
  let l, c, h, alpha;
  if (REG_OKLCH.test(value)) {
    [, l, c, h, alpha] = parseOklch(value, {
      format: VAL_COMP
    }) as ComputedColorChannels;
    return [l, c, h, alpha];
  }
  let x, y, z;
  if (format === VAL_MIX) {
    let xyz;
    if (value.startsWith(FN_COLOR)) {
      xyz = parseColorFunc(value, opt);
    } else {
      xyz = parseColorValue(value, opt);
    }
    if (xyz === null) {
      return null;
    }
    [, x, y, z, alpha] = xyz as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    [, x, y, z, alpha] = parseColorFunc(value) as ComputedColorChannels;
  } else {
    [, x, y, z, alpha] = parseColorValue(value) as ComputedColorChannels;
  }
  [l, c, h] = transformXyzToOklch([x, y, z], true) as TriColorChannels;
  return [l, c, format === VAL_MIX && c === 0 ? NONE : h, alpha];
};
