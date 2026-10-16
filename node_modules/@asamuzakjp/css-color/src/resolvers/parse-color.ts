/**
 * parse
 */

import { convertHexToRgb, convertHexToXyz } from '../converters/convert-hex';
import {
  transformMatrix,
  transformRgbToLinearRgb,
  transformRgbToXyz
} from '../matrix/transform';
import {
  ComputedColorChannels,
  Options,
  MatchedRegExp,
  SpecifiedColorChannels,
  StringColorChannels,
  StringColorSpacedChannels,
  TriColorChannels
} from '../typedef';
import { isString } from '../utils/common';
import {
  angleToDeg,
  parseAlpha,
  resolveInvalidColorValue,
  roundToPrecision
} from '../utils/util';

/* constants */
import {
  D50,
  MATRIX_A98_TO_XYZ,
  MATRIX_D50_TO_D65,
  MATRIX_D65_TO_D50,
  MATRIX_LMS_TO_XYZ,
  MATRIX_L_RGB_TO_XYZ,
  MATRIX_OKLAB_TO_LMS,
  MATRIX_P3_TO_XYZ,
  MATRIX_PROPHOTO_TO_XYZ_D50,
  MATRIX_REC2020_TO_XYZ
} from '../matrix/matrix';
import {
  DEC,
  DEG,
  DEG_HALF,
  DOZ,
  DUO,
  HEX,
  LAB_A,
  LAB_B,
  LAB_EPSILON,
  LAB_KAPPA,
  LAB_L,
  MAX_PCT,
  MAX_RGB,
  NONE,
  OCT,
  POW_CUBE,
  POW_SQR,
  SYN_COLOR_TYPE,
  SYN_FN_COLOR,
  SYN_HSL,
  SYN_HSL_LV3,
  SYN_LCH,
  SYN_MOD,
  SYN_RGB_LV3,
  TRIA,
  VAL_COMP,
  VAL_MIX,
  VAL_SPEC
} from '../utils/constant';
import { NAMED_COLORS } from './named-color';

/* regexp */
const REG_COLOR = new RegExp(`^(?:${SYN_COLOR_TYPE})$`);
const REG_CURRENT = /^currentColor$/i;
const REG_FN_COLOR = new RegExp(`^color\\(\\s*(${SYN_FN_COLOR})\\s*\\)$`);
const REG_HSL = new RegExp(`^hsla?\\(\\s*(${SYN_HSL}|${SYN_HSL_LV3})\\s*\\)$`);
const REG_HWB = new RegExp(`^hwb\\(\\s*(${SYN_HSL})\\s*\\)$`);
const REG_LAB = new RegExp(`^lab\\(\\s*(${SYN_MOD})\\s*\\)$`);
const REG_LCH = new RegExp(`^lch\\(\\s*(${SYN_LCH})\\s*\\)$`);
const REG_OKLAB = new RegExp(`^oklab\\(\\s*(${SYN_MOD})\\s*\\)$`);
const REG_OKLCH = new RegExp(`^oklch\\(\\s*(${SYN_LCH})\\s*\\)$`);
const REG_SPEC = /^(?:specifi|comput)edValue$/;
const REG_PARSE_RGB = new RegExp(
  `^rgba?\\(\\s*(${SYN_MOD}|${SYN_RGB_LV3})\\s*\\)$`
);

/**
 * parse rgb()
 * @param value - rgb color value
 * @param opt - options
 * @returns parsed color - ['rgb', r, g, b, alpha], '(empty)', null
 */
export const parseRgb = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.toLowerCase().trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '', nullable = false } = opt;
  if (!REG_PARSE_RGB.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const [, val] = value.match(REG_PARSE_RGB) as MatchedRegExp;
  const [v1, v2, v3, v4 = ''] = val.match(/[^\s,/]+/g) as StringColorChannels;
  let r, g, b;
  if (v1 === NONE) {
    r = 0;
  } else {
    if (v1.endsWith('%')) {
      r = (parseFloat(v1) * MAX_RGB) / MAX_PCT;
    } else {
      r = parseFloat(v1);
    }
    r = Math.min(Math.max(roundToPrecision(r, OCT), 0), MAX_RGB);
  }
  if (v2 === NONE) {
    g = 0;
  } else {
    if (v2.endsWith('%')) {
      g = (parseFloat(v2) * MAX_RGB) / MAX_PCT;
    } else {
      g = parseFloat(v2);
    }
    g = Math.min(Math.max(roundToPrecision(g, OCT), 0), MAX_RGB);
  }
  if (v3 === NONE) {
    b = 0;
  } else {
    if (v3.endsWith('%')) {
      b = (parseFloat(v3) * MAX_RGB) / MAX_PCT;
    } else {
      b = parseFloat(v3);
    }
    b = Math.min(Math.max(roundToPrecision(b, OCT), 0), MAX_RGB);
  }
  const alpha = parseAlpha(v4);
  return ['rgb', r, g, b, format === VAL_MIX && v4 === NONE ? NONE : alpha];
};

/**
 * parse hsl()
 * @param value - hsl color value
 * @param opt - options
 * @returns parsed color - ['rgb', r, g, b, alpha], '(empty)', null
 */
export const parseHsl = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '', nullable = false } = opt;
  if (!REG_HSL.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const [, val] = value.match(REG_HSL) as MatchedRegExp;
  const [v1, v2, v3, v4 = ''] = val.match(/[^\s,/]+/g) as StringColorChannels;
  let h, s, l;
  if (v1 === NONE) {
    h = 0;
  } else {
    h = angleToDeg(v1);
  }
  if (v2 === NONE) {
    s = 0;
  } else {
    s = Math.min(Math.max(parseFloat(v2), 0), MAX_PCT);
  }
  if (v3 === NONE) {
    l = 0;
  } else {
    l = Math.min(Math.max(parseFloat(v3), 0), MAX_PCT);
  }
  const alpha = parseAlpha(v4);
  if (format === 'hsl') {
    return [
      format,
      v1 === NONE ? v1 : h,
      v2 === NONE ? v2 : s,
      v3 === NONE ? v3 : l,
      v4 === NONE ? v4 : alpha
    ];
  }
  h = (h / DEG) * DOZ;
  l /= MAX_PCT;
  const sa = (s / MAX_PCT) * Math.min(l, 1 - l);
  const rk = h % DOZ;
  const gk = (8 + h) % DOZ;
  const bk = (4 + h) % DOZ;
  const r = l - sa * Math.max(-1, Math.min(rk - TRIA, TRIA ** POW_SQR - rk, 1));
  const g = l - sa * Math.max(-1, Math.min(gk - TRIA, TRIA ** POW_SQR - gk, 1));
  const b = l - sa * Math.max(-1, Math.min(bk - TRIA, TRIA ** POW_SQR - bk, 1));
  return [
    'rgb',
    Math.min(Math.max(roundToPrecision(r * MAX_RGB, OCT), 0), MAX_RGB),
    Math.min(Math.max(roundToPrecision(g * MAX_RGB, OCT), 0), MAX_RGB),
    Math.min(Math.max(roundToPrecision(b * MAX_RGB, OCT), 0), MAX_RGB),
    alpha
  ];
};

/**
 * parse hwb()
 * @param value - hwb color value
 * @param opt - options
 * @returns parsed color - ['rgb', r, g, b, alpha], '(empty)', null
 */
export const parseHwb = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '', nullable = false } = opt;
  if (!REG_HWB.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const [, val] = value.match(REG_HWB) as MatchedRegExp;
  const [v1, v2, v3, v4 = ''] = val.match(/[^\s,/]+/g) as StringColorChannels;
  let h, wh, bk;
  if (v1 === NONE) {
    h = 0;
  } else {
    h = angleToDeg(v1);
  }
  if (v2 === NONE) {
    wh = 0;
  } else {
    wh = Math.min(Math.max(parseFloat(v2), 0), MAX_PCT) / MAX_PCT;
  }
  if (v3 === NONE) {
    bk = 0;
  } else {
    bk = Math.min(Math.max(parseFloat(v3), 0), MAX_PCT) / MAX_PCT;
  }
  const alpha = parseAlpha(v4);
  if (format === 'hwb') {
    return [
      format,
      v1 === NONE ? v1 : h,
      v2 === NONE ? v2 : wh * MAX_PCT,
      v3 === NONE ? v3 : bk * MAX_PCT,
      v4 === NONE ? v4 : alpha
    ];
  }
  if (wh + bk >= 1) {
    const v = roundToPrecision((wh / (wh + bk)) * MAX_RGB, OCT);
    return ['rgb', v, v, v, alpha];
  }
  const factor = (1 - wh - bk) / MAX_RGB;
  let [, r, g, b] = parseHsl(`hsl(${h} 100 50)`) as ComputedColorChannels;
  r = roundToPrecision((r * factor + wh) * MAX_RGB, OCT);
  g = roundToPrecision((g * factor + wh) * MAX_RGB, OCT);
  b = roundToPrecision((b * factor + wh) * MAX_RGB, OCT);
  return [
    'rgb',
    Math.min(Math.max(r, 0), MAX_RGB),
    Math.min(Math.max(g, 0), MAX_RGB),
    Math.min(Math.max(b, 0), MAX_RGB),
    alpha
  ];
};

/**
 * parse lab()
 * @param value - lab color value
 * @param opt - options
 * @returns parsed color
 *   - [xyz-d50, x, y, z, alpha], ['lab', l, a, b, alpha], '(empty)', null
 */
export const parseLab = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '', nullable = false } = opt;
  if (!REG_LAB.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const COEF_PCT = 1.25;
  const COND_POW = 8;
  const [, val] = value.match(REG_LAB) as MatchedRegExp;
  const [v1, v2, v3, v4 = ''] = val.match(/[^\s,/]+/g) as StringColorChannels;
  let l, a, b;
  if (v1 === NONE) {
    l = 0;
  } else {
    if (v1.endsWith('%')) {
      l = parseFloat(v1);
      if (l > MAX_PCT) {
        l = MAX_PCT;
      }
    } else {
      l = parseFloat(v1);
    }
    if (l < 0) {
      l = 0;
    }
  }
  if (v2 === NONE) {
    a = 0;
  } else {
    a = v2.endsWith('%') ? parseFloat(v2) * COEF_PCT : parseFloat(v2);
  }
  if (v3 === NONE) {
    b = 0;
  } else {
    b = v3.endsWith('%') ? parseFloat(v3) * COEF_PCT : parseFloat(v3);
  }
  const alpha = parseAlpha(v4);
  if (REG_SPEC.test(format)) {
    return [
      'lab',
      v1 === NONE ? v1 : roundToPrecision(l, HEX),
      v2 === NONE ? v2 : roundToPrecision(a, HEX),
      v3 === NONE ? v3 : roundToPrecision(b, HEX),
      v4 === NONE ? v4 : alpha
    ];
  }
  const fl = (l + HEX) / LAB_L;
  const fa = a / LAB_A + fl;
  const fb = fl - b / LAB_B;
  const powFl = Math.pow(fl, POW_CUBE);
  const powFa = Math.pow(fa, POW_CUBE);
  const powFb = Math.pow(fb, POW_CUBE);
  const xyz = [
    powFa > LAB_EPSILON ? powFa : (fa * LAB_L - HEX) / LAB_KAPPA,
    l > COND_POW ? powFl : l / LAB_KAPPA,
    powFb > LAB_EPSILON ? powFb : (fb * LAB_L - HEX) / LAB_KAPPA
  ];
  const [x, y, z] = xyz.map(
    (val, i) => val * (D50[i] as number)
  ) as TriColorChannels;
  return [
    'xyz-d50',
    roundToPrecision(x, HEX),
    roundToPrecision(y, HEX),
    roundToPrecision(z, HEX),
    alpha
  ];
};

/**
 * parse lch()
 * @param value - lch color value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-d50', x, y, z, alpha], ['lch', l, c, h, alpha], '(empty)', null
 */
export const parseLch = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '', nullable = false } = opt;
  if (!REG_LCH.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const COEF_PCT = 1.5;
  const [, val] = value.match(REG_LCH) as MatchedRegExp;
  const [v1, v2, v3, v4 = ''] = val.match(/[^\s,/]+/g) as StringColorChannels;
  let l, c, h;
  if (v1 === NONE) {
    l = 0;
  } else {
    l = parseFloat(v1);
    if (l < 0) {
      l = 0;
    }
  }
  if (v2 === NONE) {
    c = 0;
  } else {
    c = v2.endsWith('%') ? parseFloat(v2) * COEF_PCT : parseFloat(v2);
  }
  if (v3 === NONE) {
    h = 0;
  } else {
    h = angleToDeg(v3);
  }
  const alpha = parseAlpha(v4);
  if (REG_SPEC.test(format)) {
    return [
      'lch',
      v1 === NONE ? v1 : roundToPrecision(l, HEX),
      v2 === NONE ? v2 : roundToPrecision(c, HEX),
      v3 === NONE ? v3 : roundToPrecision(h, HEX),
      v4 === NONE ? v4 : alpha
    ];
  }
  const a = c * Math.cos((h * Math.PI) / DEG_HALF);
  const b = c * Math.sin((h * Math.PI) / DEG_HALF);
  const [, x, y, z] = parseLab(`lab(${l} ${a} ${b})`) as ComputedColorChannels;
  return [
    'xyz-d50',
    roundToPrecision(x, HEX),
    roundToPrecision(y, HEX),
    roundToPrecision(z, HEX),
    alpha as number
  ];
};

/**
 * parse oklab()
 * @param value - oklab color value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-d65', x, y, z, alpha], ['oklab', l, a, b, alpha], '(empty)', null
 */
export const parseOklab = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '', nullable = false } = opt;
  if (!REG_OKLAB.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const COEF_PCT = 0.4;
  const [, val] = value.match(REG_OKLAB) as MatchedRegExp;
  const [v1, v2, v3, v4 = ''] = val.match(/[^\s,/]+/g) as StringColorChannels;
  let l, a, b;
  if (v1 === NONE) {
    l = 0;
  } else {
    l = v1.endsWith('%') ? parseFloat(v1) / MAX_PCT : parseFloat(v1);
    if (l < 0) {
      l = 0;
    }
  }
  if (v2 === NONE) {
    a = 0;
  } else if (v2.endsWith('%')) {
    a = (parseFloat(v2) * COEF_PCT) / MAX_PCT;
  } else {
    a = parseFloat(v2);
  }
  if (v3 === NONE) {
    b = 0;
  } else if (v3.endsWith('%')) {
    b = (parseFloat(v3) * COEF_PCT) / MAX_PCT;
  } else {
    b = parseFloat(v3);
  }
  const alpha = parseAlpha(v4);
  if (REG_SPEC.test(format)) {
    return [
      'oklab',
      v1 === NONE ? v1 : roundToPrecision(l, HEX),
      v2 === NONE ? v2 : roundToPrecision(a, HEX),
      v3 === NONE ? v3 : roundToPrecision(b, HEX),
      v4 === NONE ? v4 : alpha
    ];
  }
  const lms = transformMatrix(MATRIX_OKLAB_TO_LMS, [l, a, b]);
  const xyzLms = lms.map((c: number) =>
    Math.pow(c, POW_CUBE)
  ) as TriColorChannels;
  const [x, y, z] = transformMatrix(MATRIX_LMS_TO_XYZ, xyzLms, true);
  return [
    'xyz-d65',
    roundToPrecision(x, HEX),
    roundToPrecision(y, HEX),
    roundToPrecision(z, HEX),
    alpha as number
  ];
};

/**
 * parse oklch()
 * @param value - oklch color value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-d65', x, y, z, alpha], ['oklch', l, c, h, alpha], '(empty)', null
 */
export const parseOklch = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { format = '', nullable = false } = opt;
  if (!REG_OKLCH.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const COEF_PCT = 0.4;
  const [, val] = value.match(REG_OKLCH) as MatchedRegExp;
  const [v1, v2, v3, v4 = ''] = val.match(/[^\s,/]+/g) as StringColorChannels;
  let l, c, h;
  if (v1 === NONE) {
    l = 0;
  } else {
    l = v1.endsWith('%') ? parseFloat(v1) / MAX_PCT : parseFloat(v1);
    if (l < 0) {
      l = 0;
    }
  }
  if (v2 === NONE) {
    c = 0;
  } else {
    if (v2.endsWith('%')) {
      c = (parseFloat(v2) * COEF_PCT) / MAX_PCT;
    } else {
      c = parseFloat(v2);
    }
    if (c < 0) {
      c = 0;
    }
  }
  if (v3 === NONE) {
    h = 0;
  } else {
    h = angleToDeg(v3);
  }
  const alpha = parseAlpha(v4);
  if (REG_SPEC.test(format)) {
    return [
      'oklch',
      v1 === NONE ? v1 : roundToPrecision(l, HEX),
      v2 === NONE ? v2 : roundToPrecision(c, HEX),
      v3 === NONE ? v3 : roundToPrecision(h, HEX),
      v4 === NONE ? v4 : alpha
    ];
  }
  const a = c * Math.cos((h * Math.PI) / DEG_HALF);
  const b = c * Math.sin((h * Math.PI) / DEG_HALF);
  const lms = transformMatrix(MATRIX_OKLAB_TO_LMS, [l, a, b]);
  const xyzLms = lms.map((cc: number) =>
    Math.pow(cc, POW_CUBE)
  ) as TriColorChannels;
  const [x, y, z] = transformMatrix(MATRIX_LMS_TO_XYZ, xyzLms, true);
  return [
    'xyz-d65',
    roundToPrecision(x, HEX),
    roundToPrecision(y, HEX),
    roundToPrecision(z, HEX),
    alpha
  ];
};

/**
 * parse color()
 * @param value - color function value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-(d50|d65)', x, y, z, alpha], [cs, r, g, b, alpha], '(empty)', null
 */
export const parseColorFunc = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { colorSpace = '', d50 = false, format = '', nullable = false } = opt;
  if (!REG_FN_COLOR.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const [, val] = value.match(REG_FN_COLOR) as MatchedRegExp;
  let [cs, v1, v2, v3, v4 = ''] = val.match(
    /[^\s,/]+/g
  ) as StringColorSpacedChannels;
  let r, g, b;
  if (cs === 'xyz') {
    cs = 'xyz-d65';
  }
  if (v1 === NONE) {
    r = 0;
  } else {
    r = v1.endsWith('%') ? parseFloat(v1) / MAX_PCT : parseFloat(v1);
  }
  if (v2 === NONE) {
    g = 0;
  } else {
    g = v2.endsWith('%') ? parseFloat(v2) / MAX_PCT : parseFloat(v2);
  }
  if (v3 === NONE) {
    b = 0;
  } else {
    b = v3.endsWith('%') ? parseFloat(v3) / MAX_PCT : parseFloat(v3);
  }
  const alpha = parseAlpha(v4);
  if (REG_SPEC.test(format) || (format === VAL_MIX && cs === colorSpace)) {
    return [
      cs,
      v1 === NONE ? v1 : roundToPrecision(r, DEC),
      v2 === NONE ? v2 : roundToPrecision(g, DEC),
      v3 === NONE ? v3 : roundToPrecision(b, DEC),
      v4 === NONE ? v4 : alpha
    ];
  }
  let x = 0;
  let y = 0;
  let z = 0;
  // srgb-linear
  if (cs === 'srgb-linear') {
    [x, y, z] = transformMatrix(MATRIX_L_RGB_TO_XYZ, [r, g, b]);
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
    // display-p3
  } else if (cs === 'display-p3') {
    const linearRgb = transformRgbToLinearRgb([
      r * MAX_RGB,
      g * MAX_RGB,
      b * MAX_RGB
    ]);
    [x, y, z] = transformMatrix(MATRIX_P3_TO_XYZ, linearRgb);
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
    // rec2020
  } else if (cs === 'rec2020') {
    const ALPHA = 1.09929682680944;
    const BETA = 0.018053968510807;
    const REC_COEF = 0.45;
    const rgb = [r, g, b].map(c => {
      let cl;
      if (c < BETA * REC_COEF * DEC) {
        cl = c / (REC_COEF * DEC);
      } else {
        cl = Math.pow((c + ALPHA - 1) / ALPHA, 1 / REC_COEF);
      }
      return cl;
    }) as TriColorChannels;
    [x, y, z] = transformMatrix(MATRIX_REC2020_TO_XYZ, rgb);
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
    // a98-rgb
  } else if (cs === 'a98-rgb') {
    const POW_A98 = 563 / 256;
    const rgb = [r, g, b].map(c => {
      const cl = Math.pow(c, POW_A98);
      return cl;
    }) as TriColorChannels;
    [x, y, z] = transformMatrix(MATRIX_A98_TO_XYZ, rgb);
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
    // prophoto-rgb
  } else if (cs === 'prophoto-rgb') {
    const POW_PROPHOTO = 1.8;
    const rgb = [r, g, b].map(c => {
      let cl;
      if (c > 1 / (HEX * DUO)) {
        cl = Math.pow(c, POW_PROPHOTO);
      } else {
        cl = c / HEX;
      }
      return cl;
    }) as TriColorChannels;
    [x, y, z] = transformMatrix(MATRIX_PROPHOTO_TO_XYZ_D50, rgb);
    if (!d50) {
      [x, y, z] = transformMatrix(MATRIX_D50_TO_D65, [x, y, z], true);
    }
    // xyz, xyz-d50, xyz-d65
  } else if (/^xyz(?:-d(?:50|65))?$/.test(cs)) {
    [x, y, z] = [r, g, b];
    if (cs === 'xyz-d50') {
      if (!d50) {
        [x, y, z] = transformMatrix(MATRIX_D50_TO_D65, [x, y, z]);
      }
    } else if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
    // srgb
  } else {
    [x, y, z] = transformRgbToXyz([r * MAX_RGB, g * MAX_RGB, b * MAX_RGB]);
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
  }
  return [
    d50 ? 'xyz-d50' : 'xyz-d65',
    roundToPrecision(x, HEX),
    roundToPrecision(y, HEX),
    roundToPrecision(z, HEX),
    format === VAL_MIX && v4 === NONE ? v4 : alpha
  ];
};

/**
 * parse color value
 * @param value - CSS color value
 * @param opt - options
 * @returns parsed color
 *   - ['xyz-(d50|d65)', x, y, z, alpha], ['rgb', r, g, b, alpha]
 *   - value, '(empty)', null
 */
export const parseColorValue = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.toLowerCase().trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { d50 = false, format = '', nullable = false } = opt;
  if (!REG_COLOR.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      return null;
    } else if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  let x = 0;
  let y = 0;
  let z = 0;
  let alpha = 0;
  // complement currentcolor as a missing color
  if (REG_CURRENT.test(value)) {
    if (format === VAL_COMP) {
      return ['rgb', 0, 0, 0, 0];
    }
    if (format === VAL_SPEC) {
      return value;
    }
    // named-color
  } else if (/^[a-z]+$/.test(value)) {
    if (Object.hasOwn(NAMED_COLORS, value)) {
      if (format === VAL_SPEC) {
        return value;
      }
      const [r, g, b] = NAMED_COLORS[
        value as keyof typeof NAMED_COLORS
      ] as TriColorChannels;
      alpha = 1;
      if (format === VAL_COMP) {
        return ['rgb', r, g, b, alpha];
      }
      [x, y, z] = transformRgbToXyz([r, g, b], true);
      if (d50) {
        [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
      }
    } else {
      switch (format) {
        case VAL_COMP: {
          if (nullable && value !== 'transparent') {
            return null;
          }
          return ['rgb', 0, 0, 0, 0];
        }
        case VAL_SPEC: {
          if (value === 'transparent') {
            return value;
          }
          return '';
        }
        case VAL_MIX: {
          if (value === 'transparent') {
            return ['rgb', 0, 0, 0, 0];
          }
          return null;
        }
        default:
      }
    }
    // hex-color
  } else if (value[0] === '#') {
    if (REG_SPEC.test(format)) {
      const rgb = convertHexToRgb(value);
      return ['rgb', ...rgb];
    }
    [x, y, z, alpha] = convertHexToXyz(value);
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
    // lab()
  } else if (value.startsWith('lab')) {
    if (REG_SPEC.test(format)) {
      return parseLab(value, opt);
    }
    [, x, y, z, alpha] = parseLab(value) as ComputedColorChannels;
    if (!d50) {
      [x, y, z] = transformMatrix(MATRIX_D50_TO_D65, [x, y, z], true);
    }
    // lch()
  } else if (value.startsWith('lch')) {
    if (REG_SPEC.test(format)) {
      return parseLch(value, opt);
    }
    [, x, y, z, alpha] = parseLch(value) as ComputedColorChannels;
    if (!d50) {
      [x, y, z] = transformMatrix(MATRIX_D50_TO_D65, [x, y, z], true);
    }
    // oklab()
  } else if (value.startsWith('oklab')) {
    if (REG_SPEC.test(format)) {
      return parseOklab(value, opt);
    }
    [, x, y, z, alpha] = parseOklab(value) as ComputedColorChannels;
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
    // oklch()
  } else if (value.startsWith('oklch')) {
    if (REG_SPEC.test(format)) {
      return parseOklch(value, opt);
    }
    [, x, y, z, alpha] = parseOklch(value) as ComputedColorChannels;
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
  } else {
    let r, g, b;
    // hsl()
    if (value.startsWith('hsl')) {
      [, r, g, b, alpha] = parseHsl(value) as ComputedColorChannels;
      // hwb()
    } else if (value.startsWith('hwb')) {
      [, r, g, b, alpha] = parseHwb(value) as ComputedColorChannels;
      // rgb()
    } else {
      [, r, g, b, alpha] = parseRgb(value, opt) as ComputedColorChannels;
    }
    if (REG_SPEC.test(format)) {
      return ['rgb', Math.round(r), Math.round(g), Math.round(b), alpha];
    }
    [x, y, z] = transformRgbToXyz([r, g, b]);
    if (d50) {
      [x, y, z] = transformMatrix(MATRIX_D65_TO_D50, [x, y, z], true);
    }
  }
  return [
    d50 ? 'xyz-d50' : 'xyz-d65',
    roundToPrecision(x, HEX),
    roundToPrecision(y, HEX),
    roundToPrecision(z, HEX),
    alpha
  ];
};
