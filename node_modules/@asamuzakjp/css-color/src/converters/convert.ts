/**
 * convert
 */

import { cssCalc, resolveVar } from '../resolvers/css-calc-var';
import { parseColorFunc, parseColorValue } from '../resolvers/parse-color';
import { resolveRelativeColor } from '../resolvers/relative-color';
import { resolveColor } from '../resolvers/resolve-color';
import {
  ColorChannels,
  ColorConvertFn,
  ComputedColorChannels,
  Options
} from '../typedef';
import { createCacheKey, getCache, setCache } from '../utils/cache';
import { isString } from '../utils/common';
import { getMaxLength, numberToHexString } from '../utils/util';
import {
  convertColorToHsl,
  convertColorToHwb,
  convertColorToLab,
  convertColorToLch,
  convertColorToOklab,
  convertColorToOklch,
  convertColorToRgb
} from './convert-color';

/* constants */
import {
  SYN_FN_CALC,
  SYN_FN_REL,
  SYN_FN_VAR,
  VAL_COMP
} from '../utils/constant';
const NAMESPACE = 'convert';

/* regexp */
const REG_FN_CALC = new RegExp(SYN_FN_CALC);
const REG_FN_REL = new RegExp(SYN_FN_REL);
const REG_FN_VAR = new RegExp(SYN_FN_VAR);

/**
 * pre process
 * @param value - CSS color value
 * @param opt - options
 * @returns value
 */
export const preProcess = (value: string, opt: Options): string | null => {
  if (!isString(value)) {
    return null;
  }
  value = value.trim();
  const maxLength = getMaxLength(opt);
  if (!value || value.length > maxLength) {
    return null;
  }
  const cacheKey: string = createCacheKey(
    { namespace: NAMESPACE, name: 'preProcess', value },
    opt
  );
  const cachedResult = getCache(cacheKey);
  if (cachedResult !== false) {
    return cachedResult.item as string | null;
  }
  let res: string | null = value;
  if (REG_FN_VAR.test(value)) {
    const resolved = resolveVar(value, opt);
    if (isString(resolved)) {
      res = resolved;
    } else {
      setCache(cacheKey, null);
      return null;
    }
  }
  if (REG_FN_REL.test(res)) {
    const resolved = resolveRelativeColor(res, opt);
    if (isString(resolved)) {
      res = resolved;
    } else {
      setCache(cacheKey, null);
      return null;
    }
  } else if (REG_FN_CALC.test(res)) {
    res = cssCalc(res, opt);
  }
  if (res.startsWith('color-mix')) {
    const resolvedColorMix = resolveColor(res, {
      ...opt,
      format: VAL_COMP,
      nullable: true
    });
    res = typeof resolvedColorMix === 'string' ? resolvedColorMix : null;
  }
  if (!res || res.length > maxLength) {
    setCache(cacheKey, null);
    return null;
  }
  setCache(cacheKey, res);
  return res;
};

/**
 * converter factory to reduce boilerplate
 * @param name - function name for cache
 * @param format - color format
 * @param convertFn - conversion function
 * @returns color converter function
 */
const createColorConverter = (
  name: string,
  format: string,
  convertFn: ColorConvertFn
) => {
  return (value: string, opt: Options = {}): ColorChannels => {
    if (!isString(value)) {
      throw new TypeError(`${value} is not a string.`);
    }
    const options = {
      ...opt
    };
    const resolved = preProcess(value, options);
    if (resolved === null) {
      return [0, 0, 0, 0];
    }
    const val = resolved.toLowerCase();
    const cacheKey = createCacheKey(
      { namespace: NAMESPACE, name, value: val },
      options
    );
    const cached = getCache(cacheKey);
    if (cached !== false) {
      return [...(cached.item as ColorChannels)] as ColorChannels;
    }
    const result = convertFn(val, { ...options, format }) as ColorChannels;
    setCache(cacheKey, result);
    return [...result];
  };
};

/**
 * convert number to hex string
 * @param value - numeric value
 * @returns hex string: 00..ff
 */
export const numberToHex = (value: number): string => numberToHexString(value);

/**
 * convert color to hex
 * @param value - CSS color value
 * @param [opt] - options
 * @param [opt.alpha] - enable alpha channel
 * @returns #rrggbb | #rrggbbaa | null
 */
export const colorToHex = (value: string, opt: Options = {}): string | null => {
  if (!isString(value)) {
    throw new TypeError(`${value} is not a string.`);
  }
  const options = {
    ...opt
  };
  const resolved = preProcess(value, options);
  if (resolved === null) {
    return null;
  }
  const val = resolved.toLowerCase();
  const cacheKey = createCacheKey(
    { namespace: NAMESPACE, name: 'colorToHex', value: val },
    options
  );
  const cached = getCache(cacheKey);
  if (cached !== false) {
    return cached.item as string | null;
  }
  const hex = resolveColor(val, {
    ...options,
    nullable: true,
    format: options.alpha ? 'hexAlpha' : 'hex'
  });
  if (isString(hex)) {
    setCache(cacheKey, hex);
    return hex;
  }
  setCache(cacheKey, null);
  return null;
};

/**
 * convert color to hsl
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [h, s, l, alpha]
 */
export const colorToHsl = createColorConverter(
  'colorToHsl',
  'hsl',
  convertColorToHsl
);

/**
 * convert color to hwb
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [h, w, b, alpha]
 */
export const colorToHwb = createColorConverter(
  'colorToHwb',
  'hwb',
  convertColorToHwb
);

/**
 * convert color to lab
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [l, a, b, alpha]
 */
export const colorToLab = createColorConverter(
  'colorToLab',
  'lab',
  convertColorToLab
);

/**
 * convert color to lch
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [l, c, h, alpha]
 */
export const colorToLch = createColorConverter(
  'colorToLch',
  'lch',
  convertColorToLch
);

/**
 * convert color to oklab
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [l, a, b, alpha]
 */
export const colorToOklab = createColorConverter(
  'colorToOklab',
  'oklab',
  convertColorToOklab
);

/**
 * convert color to oklch
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [l, c, h, alpha]
 */
export const colorToOklch = createColorConverter(
  'colorToOklch',
  'oklch',
  convertColorToOklch
);

/**
 * convert color to rgb
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [r, g, b, alpha]
 */
export const colorToRgb = createColorConverter(
  'colorToRgb',
  'rgb',
  convertColorToRgb
);

/**
 * convert color to xyz
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [x, y, z, alpha]
 */
export const colorToXyz = (value: string, opt: Options = {}): ColorChannels => {
  if (!isString(value)) {
    throw new TypeError(`${value} is not a string.`);
  }
  const options = {
    ...opt
  };
  const resolved = preProcess(value, options);
  if (resolved === null) {
    return [0, 0, 0, 0];
  }
  const val = resolved.toLowerCase();
  const cacheKey = createCacheKey(
    { namespace: NAMESPACE, name: 'colorToXyz', value: val },
    options
  );
  const cached = getCache(cacheKey);
  if (cached !== false) {
    return [...(cached.item as ColorChannels)] as ColorChannels;
  }
  let parsed;
  if (val.startsWith('color(')) {
    parsed = parseColorFunc(val, options);
  } else {
    parsed = parseColorValue(val, options);
  }
  const [, ...xyz] = parsed as ComputedColorChannels;
  setCache(cacheKey, xyz);
  return [...xyz] as ColorChannels;
};

/**
 * convert color to xyz-d50
 * @param value - CSS color value
 * @param [opt] - options
 * @returns ColorChannels - [x, y, z, alpha]
 */
export const colorToXyzD50 = (
  value: string,
  opt: Options = {}
): ColorChannels => {
  const options = {
    ...opt,
    d50: true
  };
  return colorToXyz(value, options);
};

/* convert */
export const convert = {
  colorToHex,
  colorToHsl,
  colorToHwb,
  colorToLab,
  colorToLch,
  colorToOklab,
  colorToOklch,
  colorToRgb,
  colorToXyz,
  colorToXyzD50,
  numberToHex
};
