/**
 * resolve-color
 */

import { convertHexToRgb, convertRgbToHex } from '../converters/convert-hex';
import { transformXyzD50ToRgb, transformXyzToRgb } from '../matrix/transform';
import {
  ComputedColorChannels,
  Options,
  SpecifiedColorChannels,
  TriColorChannels
} from '../typedef';
import { createCacheKey, getCache, setCache } from '../utils/cache';
import { isString } from '../utils/common';
import {
  parseAlpha,
  resolveInvalidColorValue,
  splitValue
} from '../utils/util';
import { resolveColorMix } from './color-mix';
import { cssCalc, resolveVar } from './css-calc-var';
import {
  parseColorFunc,
  parseHsl,
  parseHwb,
  parseLab,
  parseLch,
  parseOklab,
  parseOklch,
  parseRgb
} from './parse-color';
import { resolveRelativeColor } from './relative-color';

/* constants */
import {
  FN_COLOR,
  FN_MIX,
  MAX_RGB,
  SYN_COLOR_TYPE,
  SYN_FN_CALC,
  SYN_FN_COLOR,
  SYN_FN_LIGHT_DARK,
  SYN_FN_REL,
  SYN_FN_VAR,
  SYN_MIX,
  VAL_COMP,
  VAL_MIX,
  VAL_SPEC
} from '../utils/constant';
import { NAMED_COLORS } from './named-color';
const NAMESPACE = 'resolve-color';
const RGB_TRANSPARENT = 'rgba(0, 0, 0, 0)';

/* regexp */
const REG_COLOR = new RegExp(`^(?:${SYN_COLOR_TYPE})$`);
const REG_COLOR_FUNC = new RegExp(`^color\\(\\s*(${SYN_FN_COLOR})\\s*\\)$`);
const REG_CURRENT = /^currentColor$/i;
const REG_FN_CALC = new RegExp(SYN_FN_CALC);
const REG_FN_COLOR =
  /^(?:(?:ok)?l(?:ab|ch)|color(?:-mix)?|hsla?|hwb|rgba?|var)\(/;
const REG_FN_LIGHT_DARK = new RegExp(SYN_FN_LIGHT_DARK);
const REG_FN_REL = new RegExp(SYN_FN_REL);
const REG_FN_VAR = new RegExp(SYN_FN_VAR);
const REG_MIX = new RegExp(SYN_MIX);
const REG_SPEC = /^(?:specifi|comput)edValue$/;

/**
 * resolve color value
 * @param value - CSS color value
 * @param opt - options
 * @returns resolved color
 *   - [cs, v1, v2, v3, alpha], value, '(empty)', null
 */
export const resolveColorValue = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.toLowerCase().trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { colorSpace = '', format = '', nullable = false } = opt;
  const cacheKey: string = createCacheKey(
    {
      namespace: NAMESPACE,
      name: 'resolveColorValue',
      value
    },
    opt
  );
  const cachedResult = getCache(cacheKey);
  if (cachedResult !== false) {
    const { item } = cachedResult;
    if (Array.isArray(item)) {
      return [...item] as SpecifiedColorChannels;
    }
    return item as string | null;
  }
  if (!REG_COLOR.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      setCache(cacheKey, null);
      return null;
    }
    setCache(cacheKey, res);
    if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  let cs = '';
  let r = 0;
  let g = 0;
  let b = 0;
  let alpha = 0;
  // complement currentcolor as a missing color
  if (REG_CURRENT.test(value)) {
    if (format === VAL_SPEC) {
      setCache(cacheKey, value);
      return value;
    }
    // named-color
  } else if (/^[a-z]+$/.test(value)) {
    if (Object.hasOwn(NAMED_COLORS, value)) {
      if (format === VAL_SPEC) {
        setCache(cacheKey, value);
        return value;
      }
      [r, g, b] = NAMED_COLORS[
        value as keyof typeof NAMED_COLORS
      ] as TriColorChannels;
      alpha = 1;
    } else {
      switch (format) {
        case VAL_SPEC: {
          if (value === 'transparent') {
            setCache(cacheKey, value);
            return value;
          }
          const res = '';
          setCache(cacheKey, res);
          return res;
        }
        case VAL_MIX: {
          if (value === 'transparent') {
            const res: SpecifiedColorChannels = ['rgb', 0, 0, 0, 0];
            setCache(cacheKey, res);
            return [...res];
          }
          setCache(cacheKey, null);
          return null;
        }
        case VAL_COMP:
        default: {
          if (nullable && value !== 'transparent') {
            setCache(cacheKey, null);
            return null;
          }
          const res: SpecifiedColorChannels = ['rgb', 0, 0, 0, 0];
          setCache(cacheKey, res);
          return [...res];
        }
      }
    }
    // hex-color
  } else if (value[0] === '#') {
    [r, g, b, alpha] = convertHexToRgb(value);
    // hsl()
  } else if (value.startsWith('hsl')) {
    [, r, g, b, alpha] = parseHsl(value, opt) as ComputedColorChannels;
    // hwb()
  } else if (value.startsWith('hwb')) {
    [, r, g, b, alpha] = parseHwb(value, opt) as ComputedColorChannels;
    // lab(), lch()
  } else if (/^l(?:ab|ch)/.test(value)) {
    let x, y, z;
    if (value.startsWith('lab')) {
      [cs, x, y, z, alpha] = parseLab(value, opt) as ComputedColorChannels;
    } else {
      [cs, x, y, z, alpha] = parseLch(value, opt) as ComputedColorChannels;
    }
    if (REG_SPEC.test(format)) {
      const res: SpecifiedColorChannels = [cs, x, y, z, alpha];
      setCache(cacheKey, res);
      return [...res];
    }
    [r, g, b] = transformXyzD50ToRgb([x, y, z]);
    // oklab(), oklch()
  } else if (/^okl(?:ab|ch)/.test(value)) {
    let x, y, z;
    if (value.startsWith('oklab')) {
      [cs, x, y, z, alpha] = parseOklab(value, opt) as ComputedColorChannels;
    } else {
      [cs, x, y, z, alpha] = parseOklch(value, opt) as ComputedColorChannels;
    }
    if (REG_SPEC.test(format)) {
      const res: SpecifiedColorChannels = [cs, x, y, z, alpha];
      setCache(cacheKey, res);
      return [...res];
    }
    [r, g, b] = transformXyzToRgb([x, y, z]);
    // rgb()
  } else {
    [, r, g, b, alpha] = parseRgb(value, opt) as ComputedColorChannels;
  }
  if (format === VAL_MIX && colorSpace === 'srgb') {
    const res: SpecifiedColorChannels = [
      'srgb',
      r / MAX_RGB,
      g / MAX_RGB,
      b / MAX_RGB,
      alpha
    ];
    setCache(cacheKey, res);
    return [...res];
  }
  const res: SpecifiedColorChannels = [
    'rgb',
    Math.round(r),
    Math.round(g),
    Math.round(b),
    alpha
  ];
  setCache(cacheKey, res);
  return [...res];
};

/**
 * resolve color()
 * @param value - color function value
 * @param opt - options
 * @returns resolved color - [cs, v1, v2, v3, alpha], '(empty)', null
 */
export const resolveColorFunc = (
  value: string,
  opt: Options = {}
): SpecifiedColorChannels | string | null => {
  if (isString(value)) {
    value = value.toLowerCase().trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  const { colorSpace = '', format = '', nullable = false } = opt;
  const cacheKey: string = createCacheKey(
    {
      namespace: NAMESPACE,
      name: 'resolveColorFunc',
      value
    },
    opt
  );
  const cachedResult = getCache(cacheKey);
  if (cachedResult !== false) {
    const { item } = cachedResult;
    if (Array.isArray(item)) {
      return [...item] as SpecifiedColorChannels;
    }
    return item as string | null;
  }
  if (!REG_COLOR_FUNC.test(value)) {
    const res = resolveInvalidColorValue(format, nullable);
    if (res === null) {
      setCache(cacheKey, null);
      return null;
    }
    setCache(cacheKey, res);
    if (isString(res)) {
      return res as string;
    }
    return res as SpecifiedColorChannels;
  }
  const [cs, v1, v2, v3, v4] = parseColorFunc(
    value,
    opt
  ) as SpecifiedColorChannels;
  if (REG_SPEC.test(format) || (format === VAL_MIX && cs === colorSpace)) {
    const res: SpecifiedColorChannels = [cs, v1, v2, v3, v4];
    setCache(cacheKey, res);
    return [...res];
  }
  const x = parseFloat(`${v1}`);
  const y = parseFloat(`${v2}`);
  const z = parseFloat(`${v3}`);
  const alpha = parseAlpha(`${v4}`);
  const [r, g, b] = transformXyzToRgb([x, y, z], true);
  const res: SpecifiedColorChannels = ['rgb', r, g, b, alpha];
  setCache(cacheKey, res);
  return [...res];
};

/**
 * resolve color
 * @param value - CSS color value
 * @param opt - options
 * @returns resolved color
 */
export const resolveColor = (
  value: string,
  opt: Options = {}
): string | null => {
  if (!isString(value)) {
    throw new TypeError(`${value} is not a string.`);
  }
  value = value.trim();
  const {
    colorScheme = 'normal',
    currentColor = '',
    format = VAL_COMP,
    nullable = false
  } = opt;
  const cacheKey: string = createCacheKey(
    { namespace: NAMESPACE, name: 'resolve', value },
    opt
  );
  const cachedResult = getCache(cacheKey);
  if (cachedResult !== false) {
    return cachedResult.item as string | null;
  }
  // 1. var() resolution
  if (REG_FN_VAR.test(value)) {
    if (format === VAL_SPEC) {
      setCache(cacheKey, value);
      return value;
    }
    const resolvedVar = resolveVar(value, opt);
    if (resolvedVar === null) {
      const res =
        format === 'hex' || format === 'hexAlpha' || nullable
          ? null
          : RGB_TRANSPARENT;
      setCache(cacheKey, res);
      return res;
    }
    value = resolvedVar;
  }
  if (opt.format !== format) {
    opt.format = format;
  }
  value = value.toLowerCase();
  // 2. light-dark() resolution
  if (REG_FN_LIGHT_DARK.test(value) && value.endsWith(')')) {
    const colorParts = value.replace(REG_FN_LIGHT_DARK, '').replace(/\)$/, '');
    const [light = '', dark = ''] = splitValue(colorParts, { delimiter: ',' });
    if (light && dark) {
      if (format === VAL_SPEC) {
        const lightColor = resolveColor(light, opt);
        const darkColor = resolveColor(dark, opt);
        const res =
          lightColor && darkColor
            ? `light-dark(${lightColor}, ${darkColor})`
            : '';
        setCache(cacheKey, res);
        return res;
      }
      const chosen = colorScheme === 'dark' ? dark : light;
      const resolved = resolveColor(chosen, opt);
      setCache(cacheKey, resolved);
      return resolved;
    }
    // fallback for invalid light-dark
    let invalidRes;
    if (format === VAL_SPEC) {
      invalidRes = '';
    } else if (format === 'hex' || format === 'hexAlpha') {
      invalidRes = null;
    } else {
      invalidRes = RGB_TRANSPARENT;
    }
    setCache(cacheKey, invalidRes);
    return invalidRes;
  }
  // 3. Relative Color resolution
  if (REG_FN_REL.test(value)) {
    const resolvedRel = resolveRelativeColor(value, opt, resolveColor);
    if (format === VAL_COMP) {
      const res =
        resolvedRel === null && !nullable ? RGB_TRANSPARENT : resolvedRel;
      setCache(cacheKey, res);
      return res;
    }
    if (format === VAL_SPEC) {
      const res = resolvedRel === null ? '' : resolvedRel;
      setCache(cacheKey, res);
      return res;
    }
    value = resolvedRel === null ? '' : resolvedRel;
  }
  // 4. calc() resolution
  if (REG_FN_CALC.test(value)) {
    value = cssCalc(value, opt);
  }
  // 5. Keyword & Color-space resolution
  let cs = '';
  let r = NaN;
  let g = NaN;
  let b = NaN;
  let alpha = NaN;
  if (value === 'transparent') {
    let res: string | null;
    switch (format) {
      case VAL_SPEC: {
        res = value;
        break;
      }
      case 'hex': {
        res = null;
        break;
      }
      case 'hexAlpha': {
        res = '#00000000';
        break;
      }
      default: {
        res = RGB_TRANSPARENT;
      }
    }
    setCache(cacheKey, res);
    return res;
  }
  if (value === 'currentcolor') {
    if (format === VAL_SPEC) {
      setCache(cacheKey, value);
      return value;
    }
    if (currentColor) {
      let resolvedCurrent;
      if (currentColor.startsWith(FN_MIX)) {
        resolvedCurrent = resolveColorMix(currentColor, opt, resolveColor);
      } else if (currentColor.startsWith(FN_COLOR)) {
        resolvedCurrent = resolveColorFunc(currentColor, opt);
      } else {
        resolvedCurrent = resolveColorValue(currentColor, opt);
      }
      if (resolvedCurrent === null) {
        setCache(cacheKey, null);
        return null;
      }
      [cs, r, g, b, alpha] = resolvedCurrent as ComputedColorChannels;
    } else {
      // value is handled below if not VAL_COMP
      const res = format === VAL_COMP ? RGB_TRANSPARENT : value;
      if (format === VAL_COMP) {
        setCache(cacheKey, res);
        return res;
      }
    }
  } else if (format === VAL_SPEC) {
    let res = '';
    if (value.startsWith(FN_MIX)) {
      const mixRes = resolveColorMix(value, opt, resolveColor);
      if (isString(mixRes) && mixRes) {
        res = mixRes;
      }
    } else if (value.startsWith(FN_COLOR)) {
      const funcRes = resolveColorFunc(value, opt);
      if (Array.isArray(funcRes)) {
        const [scs, rr, gg, bb, aa] = funcRes as SpecifiedColorChannels;
        res =
          aa === 1
            ? `color(${scs} ${rr} ${gg} ${bb})`
            : `color(${scs} ${rr} ${gg} ${bb} / ${aa})`;
      }
    } else {
      const rgb = resolveColorValue(value, opt);
      if (Array.isArray(rgb)) {
        const [scs, rr, gg, bb, aa] = rgb as SpecifiedColorChannels;
        if (scs === 'rgb') {
          res =
            aa === 1
              ? `${scs}(${rr}, ${gg}, ${bb})`
              : `${scs}a(${rr}, ${gg}, ${bb}, ${aa})`;
        } else {
          res =
            aa === 1
              ? `${scs}(${rr} ${gg} ${bb})`
              : `${scs}(${rr} ${gg} ${bb} / ${aa})`;
        }
      } else if (rgb) {
        res = rgb;
      }
    }
    setCache(cacheKey, res);
    return res;
  } else if (value.startsWith(FN_MIX)) {
    if (currentColor) {
      value = value.replace(/currentcolor/g, currentColor);
    }
    value = value.replace(/transparent/g, RGB_TRANSPARENT);
    const resolvedMix = resolveColorMix(value, opt, resolveColor);
    if (resolvedMix === null) {
      setCache(cacheKey, null);
      return null;
    }
    [cs, r, g, b, alpha] = resolvedMix as ComputedColorChannels;
  } else if (value.startsWith(FN_COLOR)) {
    const resolvedFunc = resolveColorFunc(value, opt);
    if (resolvedFunc === null) {
      setCache(cacheKey, null);
      return null;
    }
    [cs, r, g, b, alpha] = resolvedFunc as ComputedColorChannels;
  } else if (value) {
    const resolvedVal = resolveColorValue(value, opt);
    if (resolvedVal === null) {
      setCache(cacheKey, null);
      return null;
    }
    [cs, r, g, b, alpha] = resolvedVal as ComputedColorChannels;
  }
  // 6. Format Finalization
  let finalRes: string | null = '';
  switch (format) {
    case 'hex':
    case 'hexAlpha': {
      if (
        Number.isNaN(r) ||
        Number.isNaN(g) ||
        Number.isNaN(b) ||
        Number.isNaN(alpha) ||
        (format === 'hex' && alpha === 0)
      ) {
        finalRes = null;
      } else {
        finalRes = convertRgbToHex([r, g, b, format === 'hex' ? 1 : alpha]);
      }
      break;
    }
    default: {
      if (cs === 'rgb') {
        finalRes =
          alpha === 1
            ? `${cs}(${r}, ${g}, ${b})`
            : `${cs}a(${r}, ${g}, ${b}, ${alpha})`;
      } else if (['lab', 'lch', 'oklab', 'oklch'].includes(cs)) {
        finalRes =
          alpha === 1
            ? `${cs}(${r} ${g} ${b})`
            : `${cs}(${r} ${g} ${b} / ${alpha})`;
      } else {
        finalRes =
          alpha === 1
            ? `color(${cs} ${r} ${g} ${b})`
            : `color(${cs} ${r} ${g} ${b} / ${alpha})`;
      }
    }
  }
  setCache(cacheKey, finalRes);
  return finalRes;
};

/**
 * is valid color
 * @param value - CSS value
 * @param opt - options
 * @returns result
 */
export const isValidColor = (value: unknown, opt: Options = {}): boolean => {
  if (!isString(value)) {
    return false;
  }
  const color = value.toLowerCase().trim();
  if (!color) {
    return false;
  }
  if (/^[a-z]+$/.test(color)) {
    return (
      color === 'currentcolor' ||
      color === 'transparent' ||
      Object.hasOwn(NAMED_COLORS, color)
    );
  }
  if (REG_COLOR.test(color) || REG_MIX.test(color)) {
    return true;
  }
  if (REG_FN_COLOR.test(color)) {
    const options = {
      ...opt,
      nullable: true
    };
    return !!resolveColor(color, options);
  }
  return false;
};
