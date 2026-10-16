/**
 * color-mix
 */

import {
  convertColorToHsl,
  convertColorToHwb,
  convertColorToLab,
  convertColorToLch,
  convertColorToLinearRgb,
  convertColorToOklab,
  convertColorToOklch,
  convertColorToRgb,
  convertColorToXyz
} from '../converters/convert-color';
import {
  ChannelNoneFlags,
  ColorAndPct,
  ColorChannels,
  ColorFormat,
  ColorResolverFn,
  ColorSpace,
  ColorSpaceParseResult,
  ComputedColorChannels,
  InterpolatedComponents,
  NormalizedPercentages,
  NumStrColorChannels,
  Options,
  SpecifiedColorChannels,
  TriColorChannels
} from '../typedef';
import {
  normalizeColorComponents,
  transformXyzD50ToRgb,
  transformXyzToRgb
} from '../matrix/transform';
import { parseColorFunc, parseColorValue } from '../resolvers/parse-color';
import { resolveColorValue } from '../resolvers/resolve-color';
import { createCacheKey, getCache, setCache } from '../utils/cache';
import { isString } from '../utils/common';
import {
  cacheInvalidColorValue,
  interpolateHue,
  roundToPrecision,
  splitValue
} from '../utils/util';

/* constants */
import {
  DEG,
  FN_COLOR,
  FN_LIGHT_DARK,
  FN_MIX,
  HALF,
  HEX,
  MAX_PCT,
  MAX_RGB,
  NONE,
  VAL_COMP,
  VAL_MIX,
  VAL_SPEC
} from '../utils/constant';
const NAMESPACE = 'color-mix';

/**
 * parse color space
 * @param arg - color space argument string
 * @returns object containing colorSpace and hueArc, or null if invalid
 */
export const parseColorSpace = (arg: string): ColorSpaceParseResult | null => {
  const csTokens = splitValue(arg).filter(Boolean);
  if (csTokens[0] !== 'in' || csTokens.length < 2) {
    return null;
  }
  const hueIndex = csTokens.indexOf('hue');
  if (csTokens.length > 2 && hueIndex > -1) {
    return {
      colorSpace: csTokens[1] as string,
      hueArc: csTokens.slice(2, hueIndex).join(' ')
    };
  }
  return {
    colorSpace: csTokens.slice(1).join(' '),
    hueArc: ''
  };
};

/**
 * parse color and percentage
 * @param arg - color and percentage argument string
 * @returns object containing color string and percentage string
 */
export const parseColorAndPct = (arg: string): ColorAndPct => {
  const tokens = splitValue(arg).filter(Boolean);
  let color = '';
  let pct = '';
  if (tokens.length === 1) {
    color = tokens[0] as string;
  } else {
    const isPct = (t: string) => {
      return t.endsWith('%') || t.startsWith('calc(') || t === 'none';
    };
    if (isPct(tokens[tokens.length - 1] as string)) {
      pct = tokens.pop() as string;
      color = tokens.join(' ');
    } else if (isPct(tokens[0] as string)) {
      pct = tokens.shift() as string;
      color = tokens.join(' ');
    } else {
      color = tokens.join(' ');
    }
  }
  return { color, pct };
};

/**
 * resolve if nested function
 * @param colorStr - color string
 * @param opt - options
 * @param resolver - resolver function
 * @returns resolved color string or original string
 */
export const resolveIfNested = (
  colorStr: string,
  opt: Options,
  resolver: ColorResolverFn
): string => {
  let current = colorStr;
  while (
    isString(current) &&
    (current.startsWith('color-mix(') ||
      current.startsWith('var(') ||
      current.startsWith('light-dark('))
  ) {
    const resolved = resolver(current, {
      ...opt,
      format: opt.format === VAL_SPEC ? opt.format : VAL_COMP
    });
    if (!resolved) {
      break;
    }
    if (Array.isArray(resolved)) {
      const [cs, v1, v2, v3, v4] = resolved;
      if (v4 === 1 || v4 === undefined) {
        current =
          cs === 'rgb'
            ? `${cs}(${v1}, ${v2}, ${v3})`
            : `${cs}(${v1} ${v2} ${v3})`;
      } else {
        current =
          cs === 'rgb'
            ? `${cs}a(${v1}, ${v2}, ${v3}, ${v4})`
            : `${cs}(${v1} ${v2} ${v3} / ${v4})`;
      }
      break;
    }
    if (typeof resolved === 'string') {
      if (resolved === current) {
        break;
      }
      current = resolved;
    } else {
      break;
    }
  }
  return current;
};

/**
 * normalize percentages
 * @param pctA - percentage for color A
 * @param pctB - percentage for color B
 * @returns object containing normalized percentages and multiplier, or null if invalid
 */
export const normalizePercentages = (
  pctA: string,
  pctB: string
): NormalizedPercentages | null => {
  let pA, pB, m;
  if (pctA && pctB) {
    const p1 = parseFloat(pctA) / MAX_PCT;
    const p2 = parseFloat(pctB) / MAX_PCT;
    if (
      Number.isNaN(p1) ||
      Number.isNaN(p2) ||
      p1 < 0 ||
      p1 > 1 ||
      p2 < 0 ||
      p2 > 1 ||
      (p1 === 0 && p2 === 0)
    ) {
      return null;
    }
    const factor = p1 + p2;
    pA = p1 / factor;
    pB = p2 / factor;
    m = factor < 1 ? factor : 1;
  } else {
    if (pctA) {
      const numA = parseFloat(pctA);
      if (Number.isNaN(numA) || numA < 0 || numA > MAX_PCT) {
        return null;
      }
      pA = numA / MAX_PCT;
      pB = (MAX_PCT - numA) / MAX_PCT;
    } else if (pctB) {
      const numB = parseFloat(pctB);
      if (Number.isNaN(numB) || numB < 0 || numB > MAX_PCT) {
        return null;
      }
      pB = numB / MAX_PCT;
      pA = (MAX_PCT - numB) / MAX_PCT;
    } else {
      pA = HALF;
      pB = HALF;
    }
    m = 1;
  }
  return { pA, pB, m };
};

/**
 * process color
 * @param colorStr - color string
 * @param opt - options
 * @returns specified color string
 */
export const processColor = (colorStr: string, opt: Options): string => {
  if (!isString(colorStr)) {
    return '';
  }
  if (colorStr.startsWith(FN_MIX) || colorStr.startsWith(FN_LIGHT_DARK)) {
    return colorStr;
  }
  if (colorStr.startsWith(FN_COLOR)) {
    const [cs, v1, v2, v3, v4] = parseColorFunc(
      colorStr,
      opt
    ) as SpecifiedColorChannels;
    if (v4 === 1) {
      return `color(${cs} ${v1} ${v2} ${v3})`;
    } else {
      return `color(${cs} ${v1} ${v2} ${v3} / ${v4})`;
    }
  }
  const val = parseColorValue(colorStr, opt);
  if (Array.isArray(val)) {
    const [cs, v1, v2, v3, v4] = val;
    if (v4 === 1) {
      if (cs === 'rgb') {
        return `${cs}(${v1}, ${v2}, ${v3})`;
      }
      return `${cs}(${v1} ${v2} ${v3})`;
    } else {
      if (cs === 'rgb') {
        return `${cs}a(${v1}, ${v2}, ${v3}, ${v4})`;
      }
      return `${cs}(${v1} ${v2} ${v3} / ${v4})`;
    }
  }
  if (!isString(val) || !val) {
    return '';
  }
  return val as string;
};

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
export const buildSpecifiedColorMix = (
  colorSpace: string,
  hueArc: string,
  colorA: string,
  pctA: string,
  colorB: string,
  pctB: string,
  opt: Options
): string => {
  let valueA = processColor(colorA, opt);
  let valueB = processColor(colorB, opt);
  if (!valueA || !valueB) {
    return '';
  }
  if (pctA && pctB) {
    valueA += ` ${parseFloat(pctA)}%`;
    valueB += ` ${parseFloat(pctB)}%`;
  } else if (pctA) {
    const numPctA = parseFloat(pctA);
    if (numPctA !== MAX_PCT * HALF) {
      valueA += ` ${numPctA}%`;
    }
  } else if (pctB) {
    const numPctA = MAX_PCT - parseFloat(pctB);
    if (numPctA !== MAX_PCT * HALF) {
      valueA += ` ${numPctA}%`;
    }
  }
  if (hueArc) {
    return `color-mix(in ${colorSpace} ${hueArc} hue, ${valueA}, ${valueB})`;
  }
  return `color-mix(in ${colorSpace}, ${valueA}, ${valueB})`;
};

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
export const interpolateComponents = (
  compA: TriColorChannels,
  compB: TriColorChannels,
  alphaA: number,
  alphaB: number,
  pA: number,
  pB: number
): InterpolatedComponents => {
  const factorA = alphaA * pA;
  const factorB = alphaB * pB;
  const alpha = factorA + factorB;
  let comps: TriColorChannels;
  if (alpha === 0) {
    comps = [
      compA[0] * pA + compB[0] * pB,
      compA[1] * pA + compB[1] * pB,
      compA[2] * pA + compB[2] * pB
    ];
  } else {
    comps = [
      (compA[0] * factorA + compB[0] * factorB) / alpha,
      (compA[1] * factorA + compB[1] * factorB) / alpha,
      (compA[2] * factorA + compB[2] * factorB) / alpha
    ];
  }
  return { comps, alpha };
};

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
export const formatMixedColor = (
  colorSpace: ColorSpace,
  comps: TriColorChannels,
  nones: ChannelNoneFlags,
  alpha: number,
  m: number,
  format: ColorFormat,
  rgbOverride?: TriColorChannels
): SpecifiedColorChannels => {
  const [c1None, c2None, c3None, alphaNone] = nones;
  const [c1, c2, c3] = comps;
  if (format === VAL_COMP) {
    return [
      colorSpace,
      c1None ? NONE : roundToPrecision(c1, HEX),
      c2None ? NONE : roundToPrecision(c2, HEX),
      c3None ? NONE : roundToPrecision(c3, HEX),
      alphaNone ? NONE : alpha * m
    ];
  }
  const [r, g, b] = rgbOverride ?? comps;
  return [
    'rgb',
    Math.round(r),
    Math.round(g),
    Math.round(b),
    parseFloat((alpha * m).toFixed(3))
  ];
};

/**
 * Fetch raw channels or fallback for currentcolor
 * @param color - color input string
 * @param convertFn - conversion function
 * @param opt - conversion options
 * @returns color channel values or null if invalid
 */
export const getRawChannels = (
  color: string | NumStrColorChannels,
  convertFn: (c: string, opt: any) => any,
  opt: any
): NumStrColorChannels | null => {
  if (Array.isArray(color)) {
    return color as NumStrColorChannels;
  }
  if (color === 'currentcolor') {
    return [NONE, NONE, NONE, NONE];
  }
  return convertFn(color, opt);
};

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
export const mixSrgbSpace = (
  colorSpace: ColorSpace,
  colorA: string,
  colorB: string,
  pA: number,
  pB: number,
  format: ColorFormat,
  m: number
): SpecifiedColorChannels | null => {
  const convertFn =
    colorSpace === 'srgb' ? convertColorToRgb : convertColorToLinearRgb;
  const rgbA = getRawChannels(colorA, convertFn, {
    colorSpace,
    format: VAL_MIX
  });
  const rgbB = getRawChannels(colorB, convertFn, {
    colorSpace,
    format: VAL_MIX
  });
  if (!rgbA || !rgbB) {
    return null;
  }
  const [rrA, ggA, bbA, aaA] = rgbA;
  const [rrB, ggB, bbB, aaB] = rgbB;
  const nones: [boolean, boolean, boolean, boolean] = [
    rrA === NONE && rrB === NONE,
    ggA === NONE && ggB === NONE,
    bbA === NONE && bbB === NONE,
    aaA === NONE && aaB === NONE
  ];
  const [[rA, gA, bA, alphaA], [rB, gB, bB, alphaB]] = normalizeColorComponents(
    rgbA,
    rgbB,
    true
  );
  const { comps, alpha } = interpolateComponents(
    [rA, gA, bA],
    [rB, gB, bB],
    alphaA,
    alphaB,
    pA,
    pB
  );
  const rgbOverride: [number, number, number] = [
    comps[0] * MAX_RGB,
    comps[1] * MAX_RGB,
    comps[2] * MAX_RGB
  ];
  return formatMixedColor(
    colorSpace,
    comps,
    nones,
    alpha,
    m,
    format,
    rgbOverride
  );
};

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
export const mixXyzSpace = (
  colorSpace: string,
  colorA: string,
  colorB: string,
  pA: number,
  pB: number,
  format: string,
  m: number
): SpecifiedColorChannels | null => {
  const isD50 = colorSpace === 'xyz-d50';
  const opt = { colorSpace, d50: isD50, format: VAL_MIX };
  const xyzA = getRawChannels(colorA, convertColorToXyz, opt);
  const xyzB = getRawChannels(colorB, convertColorToXyz, opt);
  if (!xyzA || !xyzB) {
    return null;
  }
  const [xxA, yyA, zzA, aaA] = xyzA;
  const [xxB, yyB, zzB, aaB] = xyzB;
  const nones: [boolean, boolean, boolean, boolean] = [
    xxA === NONE && xxB === NONE,
    yyA === NONE && yyB === NONE,
    zzA === NONE && zzB === NONE,
    aaA === NONE && aaB === NONE
  ];
  const [[xA, yA, zA, alphaA], [xB, yB, zB, alphaB]] = normalizeColorComponents(
    xyzA,
    xyzB,
    true
  );
  const { comps, alpha } = interpolateComponents(
    [xA, yA, zA],
    [xB, yB, zB],
    alphaA,
    alphaB,
    pA,
    pB
  );
  const rgb = isD50
    ? transformXyzD50ToRgb(comps, true)
    : transformXyzToRgb(comps, true);
  return formatMixedColor(colorSpace, comps, nones, alpha, m, format, rgb);
};

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
export const mixHslHwbSpace = (
  colorSpace: string,
  hueArc: string,
  colorA: string,
  colorB: string,
  pA: number,
  pB: number,
  format: string,
  m: number
): SpecifiedColorChannels | null => {
  const convertFn =
    colorSpace === 'hsl' ? convertColorToHsl : convertColorToHwb;
  const opt = { colorSpace, format: VAL_MIX };
  const hslA = getRawChannels(colorA, convertFn, opt);
  const hslB = getRawChannels(colorB, convertFn, opt);
  if (!hslA || !hslB) {
    return null;
  }
  const [, , , aaA] = hslA;
  const [, , , aaB] = hslB;
  const nones: [boolean, boolean, boolean, boolean] = [
    false,
    false,
    false,
    aaA === NONE && aaB === NONE
  ];
  let [[hA, sA, lA, alphaA], [hB, sB, lB, alphaB]] = normalizeColorComponents(
    hslA,
    hslB,
    true
  );
  if (hueArc) {
    [hA, hB] = interpolateHue(hA, hB, hueArc);
  }
  const factorA = alphaA * pA;
  const factorB = alphaB * pB;
  const alpha = factorA + factorB;
  const h = (hA * pA + hB * pB) % DEG;
  let s: number, l: number;
  if (alpha === 0) {
    s = sA * pA + sB * pB;
    l = lA * pA + lB * pB;
  } else {
    s = (sA * factorA + sB * factorB) / alpha;
    l = (lA * factorA + lB * factorB) / alpha;
  }
  const [r, g, b] = convertColorToRgb(
    `${colorSpace}(${h} ${s} ${l})`
  ) as ColorChannels;
  const compsForValComp: TriColorChannels = [
    r / MAX_RGB,
    g / MAX_RGB,
    b / MAX_RGB
  ];
  const targetSpace = format === VAL_COMP ? 'srgb' : colorSpace;
  return formatMixedColor(
    targetSpace,
    compsForValComp,
    nones,
    alpha,
    m,
    format,
    [r, g, b]
  );
};

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
export const mixLchSpace = (
  colorSpace: string,
  hueArc: string,
  colorA: string,
  colorB: string,
  pA: number,
  pB: number,
  format: string,
  m: number
): SpecifiedColorChannels | null => {
  const convertFn =
    colorSpace === 'lch' ? convertColorToLch : convertColorToOklch;
  const opt = { colorSpace, format: VAL_MIX };
  const lchA = getRawChannels(colorA, convertFn, opt);
  const lchB = getRawChannels(colorB, convertFn, opt);
  if (!lchA || !lchB) {
    return null;
  }
  const [llA, ccA, hhA, aaA] = lchA;
  const [llB, ccB, hhB, aaB] = lchB;
  const nones: [boolean, boolean, boolean, boolean] = [
    llA === NONE && llB === NONE,
    ccA === NONE && ccB === NONE,
    hhA === NONE && hhB === NONE,
    aaA === NONE && aaB === NONE
  ];
  let [[lA, cA, hA, alphaA], [lB, cB, hB, alphaB]] = normalizeColorComponents(
    lchA,
    lchB,
    true
  );
  if (hueArc) {
    [hA, hB] = interpolateHue(hA, hB, hueArc);
  }
  const factorA = alphaA * pA;
  const factorB = alphaB * pB;
  const alpha = factorA + factorB;
  const h = (hA * pA + hB * pB) % DEG;
  let l: number, c: number;
  if (alpha === 0) {
    l = lA * pA + lB * pB;
    c = cA * pA + cB * pB;
  } else {
    l = (lA * factorA + lB * factorB) / alpha;
    c = (cA * factorA + cB * factorB) / alpha;
  }
  let rgbOverride: [number, number, number] | undefined;
  if (format !== VAL_COMP) {
    const [, r, g, b] = resolveColorValue(
      `${colorSpace}(${l} ${c} ${h})`
    ) as ComputedColorChannels;
    rgbOverride = [r, g, b];
  }
  return formatMixedColor(
    colorSpace,
    [l, c, h],
    nones,
    alpha,
    m,
    format,
    rgbOverride
  );
};

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
export const mixLabSpace = (
  colorSpace: string,
  colorA: string,
  colorB: string,
  pA: number,
  pB: number,
  format: string,
  m: number
): SpecifiedColorChannels | null => {
  const convertFn =
    colorSpace === 'lab' ? convertColorToLab : convertColorToOklab;
  const opt = { colorSpace, format: VAL_MIX };
  const labA = getRawChannels(colorA, convertFn, opt);
  const labB = getRawChannels(colorB, convertFn, opt);
  if (!labA || !labB) {
    return null;
  }
  const [llA, aaA, bbA, alA] = labA;
  const [llB, aaB, bbB, alB] = labB;
  const nones: [boolean, boolean, boolean, boolean] = [
    llA === NONE && llB === NONE,
    aaA === NONE && aaB === NONE,
    bbA === NONE && bbB === NONE,
    alA === NONE && alB === NONE
  ];
  const [[lA, aA, bA, alphaA], [lB, aB, bB, alphaB]] = normalizeColorComponents(
    labA,
    labB,
    true
  );
  const { comps, alpha } = interpolateComponents(
    [lA, aA, bA],
    [lB, aB, bB],
    alphaA,
    alphaB,
    pA,
    pB
  );
  let rgbOverride: [number, number, number] | undefined;
  if (format !== VAL_COMP) {
    const [, r, g, b] = resolveColorValue(
      `${colorSpace}(${comps[0]} ${comps[1]} ${comps[2]})`
    ) as ComputedColorChannels;
    rgbOverride = [r, g, b];
  }
  return formatMixedColor(
    colorSpace,
    comps,
    nones,
    alpha,
    m,
    format,
    rgbOverride
  );
};

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
export const computeMixedColor = (
  colorSpace: string,
  hueArc: string,
  colorA: string,
  colorB: string,
  pA: number,
  pB: number,
  m: number,
  format: string,
  nullable: boolean,
  cacheKey: string
): SpecifiedColorChannels | null => {
  let res: SpecifiedColorChannels | null = null;
  if (/^srgb(?:-linear)?$/.test(colorSpace)) {
    res = mixSrgbSpace(colorSpace, colorA, colorB, pA, pB, format, m);
  } else if (/^xyz(?:-d65|-d50)?$/.test(colorSpace)) {
    res = mixXyzSpace(colorSpace, colorA, colorB, pA, pB, format, m);
  } else if (/^h(?:sl|wb)$/.test(colorSpace)) {
    res = mixHslHwbSpace(colorSpace, hueArc, colorA, colorB, pA, pB, format, m);
  } else if (/^(?:ok)?lch$/.test(colorSpace)) {
    res = mixLchSpace(colorSpace, hueArc, colorA, colorB, pA, pB, format, m);
  } else if (/^(?:ok)?lab$/.test(colorSpace)) {
    res = mixLabSpace(colorSpace, colorA, colorB, pA, pB, format, m);
  }
  if (res === null) {
    return cacheInvalidColorValue(cacheKey, format, nullable) as null;
  }
  return res;
};

/**
 * resolve color-mix()
 * @param value - color-mix color value
 * @param opt - options
 * @param resolver - resolver function
 * @returns resolved color - [cs, v1, v2, v3, alpha], '(empty)', null
 */
export const resolveColorMix = (
  value: string,
  opt: Options = {},
  resolver: ColorResolverFn = () => null
): SpecifiedColorChannels | string | null => {
  if (!isString(value)) {
    throw new TypeError(`${value} is not a string.`);
  }
  value = value.toLowerCase().trim();
  const { format = '', nullable = false } = opt;
  const cacheKey: string = createCacheKey(
    { namespace: NAMESPACE, name: 'resolveColorMix', value },
    opt
  );
  const cachedResult = getCache(cacheKey);
  if (cachedResult !== false) {
    const { item } = cachedResult;
    if (Array.isArray(item)) {
      return [...item] as SpecifiedColorChannels;
    }
    if (isString(item)) {
      return item;
    }
    return null;
  }
  if (!value.startsWith('color-mix(') || !value.endsWith(')')) {
    return cacheInvalidColorValue(cacheKey, format, nullable);
  }
  const innerContent = value.slice(10, -1).trim();
  const args = splitValue(innerContent, { delimiter: ',' }).map(s => s.trim());
  if (args.length !== 3) {
    return cacheInvalidColorValue(cacheKey, format, nullable);
  }
  // 1. Parse Color Space
  const csResult = parseColorSpace(args[0] as string);
  if (!csResult) {
    return cacheInvalidColorValue(cacheKey, format, nullable);
  }
  let { colorSpace, hueArc } = csResult;
  // 2. Extract Color and Percentages
  let { color: colorA, pct: pctA } = parseColorAndPct(args[1] as string);
  let { color: colorB, pct: pctB } = parseColorAndPct(args[2] as string);
  // 3. Resolve Nested Functions
  colorA = resolveIfNested(colorA, opt, resolver);
  colorB = resolveIfNested(colorB, opt, resolver);
  // 4. Normalize Percentages
  const pResult = normalizePercentages(pctA, pctB);
  if (!pResult) {
    return cacheInvalidColorValue(cacheKey, format, nullable);
  }
  const { pA, pB, m } = pResult;
  if (colorSpace === 'xyz') {
    colorSpace = 'xyz-d65';
  }
  // 5. Format & Return
  if (format === VAL_SPEC) {
    const specifiedRes = buildSpecifiedColorMix(
      colorSpace,
      hueArc,
      colorA,
      pctA,
      colorB,
      pctB,
      opt
    );
    if (!specifiedRes) {
      const invalidRes = cacheInvalidColorValue(cacheKey, format, nullable);
      return invalidRes;
    }
    setCache(cacheKey, specifiedRes);
    return specifiedRes;
  }
  const computedRes = computeMixedColor(
    colorSpace,
    hueArc,
    colorA,
    colorB,
    pA,
    pB,
    m,
    format,
    nullable,
    cacheKey
  );
  if (computedRes) {
    setCache(cacheKey, computedRes);
  }
  return computedRes;
};
