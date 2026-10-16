/**
 * util
 */

import { TokenType, tokenize } from '@csstools/css-tokenizer';
import {
  HueArc,
  MatchedRegExp,
  Options,
  SpecifiedColorChannels
} from '../typedef';
import { createCacheKey, getCache, setCache } from './cache';
import { isString } from './common';

/* constants */
import {
  ANGLE,
  DEC,
  DEG,
  DEG_HALF,
  DUO,
  HEX,
  MAX_LENGTH,
  MAX_PCT,
  MAX_RGB,
  NONE,
  NUM,
  PPTH,
  TRIA,
  VAL_MIX,
  VAL_SPEC
} from './constant';
const NAMESPACE = 'util';
const {
  CloseParen: PAREN_CLOSE,
  Comma: COMMA,
  Comment: COMMENT,
  Delim: DELIM,
  EOF,
  Function: FUNC,
  OpenParen: PAREN_OPEN,
  Whitespace: W_SPACE
} = TokenType;

/* regexp */
const REG_ANGLE_TO_DEG = new RegExp(`^(${NUM})(${ANGLE})?$`);
const REG_COMMA = /^,$/;
const REG_DASHED_IDENT = /--[\w-]+/g;
const REG_SLASH = /^\/$/;
const REG_WHITESPACE = /^\s+$/;

/* absolute font size to pixel ratio */
const absoluteFontSize = new Map([
  ['xx-small', 9 / 16],
  ['x-small', 5 / 8],
  ['small', 13 / 16],
  ['medium', 1],
  ['large', 9 / 8],
  ['x-large', 3 / 2],
  ['xx-large', 2],
  ['xxx-large', 3]
]);

/* relative font size to pixel ratio */
const relativeFontSize = new Map([
  ['smaller', 1 / 1.2],
  ['larger', 1.2]
]);

/* absolute length to pixel ratio */
const absoluteLength = new Map([
  ['cm', 96 / 2.54],
  ['mm', 96 / 25.4],
  ['q', 96 / 101.6],
  ['in', 96],
  ['pc', 16],
  ['pt', 96 / 72],
  ['px', 1]
]);

/* relative length to pixel ratio */
const relativeLength = new Map([
  ['rcap', 1],
  ['rch', 0.5],
  ['rem', 1],
  ['rex', 0.5],
  ['ric', 1],
  ['rlh', 1.2]
]);

/**
 * get max length
 * @param [opt] - options
 * @returns max length
 */
export const getMaxLength = (opt: Options = {}): number => {
  const { maxLength } = opt;
  if (
    Number.isInteger(maxLength) &&
    (maxLength as number) > 0 &&
    (maxLength as number) < MAX_LENGTH
  ) {
    return maxLength as number;
  }
  return MAX_LENGTH;
};

/**
 * split value
 * NOTE: comments are stripped, it can be preserved if, in the options param,
 * `delimiter` is either ',' or '/' and with `preserveComment` set to `true`
 * @param value - CSS value
 * @param [opt] - options
 * @returns array of values
 */
export const splitValue = (value: string, opt: Options = {}): string[] => {
  if (!isString(value)) {
    throw new TypeError(`${value} is not a string.`);
  }
  const options = {
    ...opt
  };
  const strValue = value.trim();
  const maxLength = getMaxLength(options);
  if (!strValue || strValue.length > maxLength) {
    return [];
  }
  const { delimiter = ' ', preserveComment = false } = options;
  const cacheKey: string = createCacheKey(
    {
      namespace: NAMESPACE,
      name: 'splitValue',
      value: strValue
    },
    { delimiter, preserveComment }
  );
  const cachedResult = getCache<string[]>(cacheKey);
  if (cachedResult) {
    return [...cachedResult.item];
  }
  let regDelimiter;
  switch (delimiter) {
    case ',': {
      regDelimiter = REG_COMMA;
      break;
    }
    case '/': {
      regDelimiter = REG_SLASH;
      break;
    }
    default: {
      regDelimiter = REG_WHITESPACE;
    }
  }
  const tokens = tokenize({ css: strValue });
  let nest = 0;
  let currentStr = '';
  const res: string[] = [];
  for (const [type, val] of tokens) {
    switch (type) {
      case COMMA:
      case DELIM: {
        if (nest === 0 && regDelimiter.test(val)) {
          res.push(currentStr.trim());
          currentStr = '';
        } else {
          currentStr += val;
        }
        break;
      }
      case COMMENT: {
        if (preserveComment && (delimiter === ',' || delimiter === '/')) {
          currentStr += val;
        }
        break;
      }
      case FUNC:
      case PAREN_OPEN: {
        currentStr += val;
        nest++;
        break;
      }
      case PAREN_CLOSE: {
        currentStr += val;
        nest--;
        break;
      }
      case W_SPACE: {
        if (regDelimiter.test(val)) {
          if (nest === 0) {
            if (currentStr) {
              res.push(currentStr.trim());
              currentStr = '';
            }
          } else {
            currentStr += ' ';
          }
        } else if (!currentStr.endsWith(' ')) {
          currentStr += ' ';
        }
        break;
      }
      default: {
        if (type === EOF) {
          res.push(currentStr.trim());
          currentStr = '';
        } else {
          currentStr += val;
        }
      }
    }
  }
  setCache(cacheKey, res);
  return [...res];
};

/**
 * extract dashed-ident tokens
 * @param value - CSS value
 * @returns array of dashed-ident tokens
 */
export const extractDashedIdent = (value: string): string[] => {
  if (!isString(value)) {
    throw new TypeError(`${value} is not a string.`);
  }
  const strValue = value.trim();
  if (!strValue) {
    return [];
  }
  const cacheKey: string = createCacheKey({
    namespace: NAMESPACE,
    name: 'extractDashedIdent',
    value: strValue
  });
  const cachedResult = getCache<string[]>(cacheKey);
  if (cachedResult) {
    return [...cachedResult.item];
  }
  const matches = strValue.match(REG_DASHED_IDENT);
  const res = matches ? [...new Set(matches)] : [];
  setCache(cacheKey, res);
  return [...res];
};

/**
 * round to specified precision
 * @param value - numeric value
 * @param bit - minimum bits
 * @returns rounded value
 */
export const roundToPrecision = (value: number, bit: number = 0): number => {
  if (!Number.isFinite(value)) {
    throw new TypeError(`${value} is not a finite number.`);
  }
  if (!Number.isFinite(bit)) {
    throw new TypeError(`${bit} is not a finite number.`);
  }
  if (bit < 0 || bit > HEX) {
    throw new RangeError(`${bit} is not between 0 and ${HEX}.`);
  }
  if (bit === 0) {
    return Math.round(value);
  }
  const precision = bit === HEX ? 6 : bit < DEC ? 4 : 5;
  return parseFloat(value.toPrecision(precision));
};

/**
 * interpolate hue
 * @param hueA - hue value
 * @param hueB - hue value
 * @param arc - shorter | longer | increasing | decreasing
 * @returns result - [hueA, hueB]
 */
export const interpolateHue = (
  hueA: number,
  hueB: number,
  arc: HueArc | string = 'shorter'
): [number, number] => {
  if (!Number.isFinite(hueA)) {
    throw new TypeError(`${hueA} is not a finite number.`);
  }
  if (!Number.isFinite(hueB)) {
    throw new TypeError(`${hueB} is not a finite number.`);
  }
  let a = hueA;
  let b = hueB;
  switch (arc) {
    case 'decreasing': {
      if (b > a) {
        a += DEG;
      }
      break;
    }
    case 'increasing': {
      if (b < a) {
        b += DEG;
      }
      break;
    }
    case 'longer': {
      if (b > a && b < a + DEG_HALF) {
        a += DEG;
      } else if (b > a - DEG_HALF && b <= a) {
        b += DEG;
      }
      break;
    }
    case 'shorter':
    default: {
      if (b > a + DEG_HALF) {
        a += DEG;
      } else if (b < a - DEG_HALF) {
        b += DEG;
      }
    }
  }
  return [a, b];
};

/**
 * resolve length in pixels
 * @param value - value
 * @param unit - unit
 * @param [opt] - options
 * @returns pixelated value
 */
export const resolveLengthInPixels = (
  value: number | string,
  unit: string | undefined,
  opt: Options = {}
): number => {
  const { dimension = {} } = opt;
  const { callback, em, rem, vh, vw } = dimension;
  if (isString(value)) {
    const str = value.toLowerCase().trim();
    const maxLength = getMaxLength(opt);
    if (str.length > maxLength) {
      return Number.NaN;
    }
    const ratio = absoluteFontSize.get(str);
    if (ratio !== undefined && typeof rem === 'number') {
      return ratio * rem;
    }
    const relRatio = relativeFontSize.get(str);
    if (relRatio !== undefined && typeof em === 'number') {
      return relRatio * em;
    }
    return Number.NaN;
  }
  if (Number.isFinite(value) && unit) {
    const u = unit.toLowerCase();
    if (Object.hasOwn(dimension, u)) {
      const dimVal = dimension[u];
      return typeof dimVal === 'number'
        ? (value as number) * dimVal
        : Number.NaN;
    }
    if (typeof callback === 'function') {
      const cbVal = callback(u);
      return typeof cbVal === 'number' ? (value as number) * cbVal : Number.NaN;
    }
    const absRatio = absoluteLength.get(u);
    if (absRatio !== undefined) {
      return (value as number) * absRatio;
    }
    const relRatio = relativeLength.get(u);
    if (relRatio !== undefined && typeof rem === 'number') {
      return (value as number) * relRatio * rem;
    }
    const rUnitRatio = relativeLength.get(`r${u}`);
    if (rUnitRatio !== undefined && typeof em === 'number') {
      return (value as number) * rUnitRatio * em;
    }
    switch (u) {
      case 'vb': {
        return typeof vh === 'number' ? (value as number) * vh : Number.NaN;
      }
      case 'vi': {
        return typeof vw === 'number' ? (value as number) * vw : Number.NaN;
      }
      case 'vmax': {
        return typeof vh === 'number' && typeof vw === 'number'
          ? (value as number) * Math.max(vh, vw)
          : Number.NaN;
      }
      case 'vmin': {
        return typeof vh === 'number' && typeof vw === 'number'
          ? (value as number) * Math.min(vh, vw)
          : Number.NaN;
      }
      default:
    }
  }
  // unsupported or invalid value
  return Number.NaN;
};

/**
 * angle to deg
 * @param angle
 * @returns deg: 0..360
 */
export const angleToDeg = (angle: string): number => {
  if (isString(angle)) {
    angle = angle.trim();
  } else {
    throw new TypeError(`${angle} is not a string.`);
  }
  const GRAD = DEG / 400;
  const RAD = DEG / (Math.PI * DUO);
  if (!REG_ANGLE_TO_DEG.test(angle)) {
    throw new SyntaxError(`Invalid property value: ${angle}`);
  }
  const [, value, unit] = angle.match(REG_ANGLE_TO_DEG) as MatchedRegExp;
  let deg;
  switch (unit) {
    case 'grad':
      deg = parseFloat(value) * GRAD;
      break;
    case 'rad':
      deg = parseFloat(value) * RAD;
      break;
    case 'turn':
      deg = parseFloat(value) * DEG;
      break;
    default:
      deg = parseFloat(value);
  }
  deg %= DEG;
  if (deg < 0) {
    deg += DEG;
  } else if (Object.is(deg, -0)) {
    deg = 0;
  }
  return deg;
};

/**
 * number to hex string
 * @param value - numeric value
 * @returns hex string
 */
export const numberToHexString = (value: number): string => {
  if (!Number.isFinite(value)) {
    throw new TypeError(`${value} is not a number.`);
  } else {
    value = Math.round(value);
    if (value < 0 || value > MAX_RGB) {
      throw new RangeError(`${value} is not between 0 and ${MAX_RGB}.`);
    }
  }
  let hex = value.toString(HEX);
  if (hex.length === 1) {
    hex = `0${hex}`;
  }
  return hex;
};

/**
 * parse alpha
 * @param [alpha] - alpha value
 * @returns alpha: 0..1
 */
export const parseAlpha = (alpha: string = ''): number => {
  if (isString(alpha)) {
    alpha = alpha.trim();
    if (!alpha) {
      alpha = '1';
    } else if (alpha === NONE) {
      alpha = '0';
    } else {
      let a;
      if (alpha.endsWith('%')) {
        a = parseFloat(alpha) / MAX_PCT;
      } else {
        a = parseFloat(alpha);
      }
      if (!Number.isFinite(a)) {
        throw new TypeError(`${a} is not a finite number.`);
      }
      if (a < PPTH) {
        alpha = '0';
      } else if (a > 1) {
        alpha = '1';
      } else {
        alpha = a.toFixed(TRIA);
      }
    }
  } else {
    alpha = '1';
  }
  return parseFloat(alpha);
};

/**
 * parse hex alpha
 * @param value - alpha value in hex string
 * @returns alpha: 0..1
 */
export const parseHexAlpha = (value: string): number => {
  if (isString(value)) {
    if (value === '') {
      throw new SyntaxError('Invalid property value: (empty string)');
    }
    value = value.trim();
  } else {
    throw new TypeError(`${value} is not a string.`);
  }
  let alpha = parseInt(value, HEX);
  if (alpha <= 0) {
    return 0;
  }
  if (alpha >= MAX_RGB) {
    return 1;
  }
  const alphaMap = new Map();
  for (let i = 1; i < MAX_PCT; i++) {
    alphaMap.set(Math.round((i * MAX_RGB) / MAX_PCT), i);
  }
  if (alphaMap.has(alpha)) {
    alpha = alphaMap.get(alpha) / MAX_PCT;
  } else {
    alpha = Math.round(alpha / MAX_RGB / PPTH) * PPTH;
  }
  return parseFloat(alpha.toFixed(TRIA));
};

/**
 * cache invalid color value
 * @param key - cache key
 * @param nullable - is nullable
 * @returns cached value
 */
export const cacheInvalidColorValue = (
  cacheKey: string,
  format: string,
  nullable: boolean = false
): SpecifiedColorChannels | string | null => {
  if (format === VAL_SPEC) {
    const res = '';
    setCache(cacheKey, res);
    return res;
  }
  if (nullable) {
    setCache(cacheKey, null);
    return null;
  }
  const res: SpecifiedColorChannels = ['rgb', 0, 0, 0, 0];
  setCache(cacheKey, res);
  return res;
};

/**
 * resolve invalid color value
 * @param format - output format
 * @param nullable - is nullable
 * @returns resolved value
 */
export const resolveInvalidColorValue = (
  format: string,
  nullable: boolean = false
): SpecifiedColorChannels | string | null => {
  switch (format) {
    case 'hsl':
    case 'hwb':
    case VAL_MIX: {
      return null;
    }
    case VAL_SPEC: {
      return '';
    }
    default: {
      if (nullable) {
        return null;
      }
      return ['rgb', 0, 0, 0, 0] as SpecifiedColorChannels;
    }
  }
};
