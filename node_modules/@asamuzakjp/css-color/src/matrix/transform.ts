/**
 * transform
 */

import {
  ColorChannels,
  NumStrColorChannels,
  ReadonlyColorMatrix,
  TriColorChannels,
  ValidateColorComponentsOptions
} from '../typedef';

/* constants */
import {
  DEG,
  DEG_HALF,
  DUO,
  HALF,
  HEX,
  LAB_A,
  LAB_B,
  LAB_EPSILON,
  LAB_KAPPA,
  LAB_L,
  LINEAR_COEF,
  LINEAR_OFFSET,
  MAX_PCT,
  MAX_RGB,
  NONE,
  POW_LINEAR,
  POW_SQR,
  QUAD,
  SEXA,
  TRIA
} from '../utils/constant';
import {
  D50,
  MATRIX_D50_TO_D65,
  MATRIX_D65_TO_D50,
  MATRIX_LMS_TO_OKLAB,
  MATRIX_L_RGB_TO_XYZ,
  MATRIX_XYZ_TO_LMS,
  MATRIX_XYZ_TO_L_RGB
} from './matrix';

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
export const validateColorComponents = (
  arr: ColorChannels | TriColorChannels,
  opt: ValidateColorComponentsOptions = {}
): ColorChannels | TriColorChannels => {
  if (!Array.isArray(arr)) {
    throw new TypeError(`${arr} is not an array.`);
  }
  const {
    alpha = false,
    minLength = TRIA,
    maxLength = QUAD,
    minRange = 0,
    maxRange = 1,
    validateRange = true
  } = opt;
  if (!Number.isFinite(minLength)) {
    throw new TypeError(`${minLength} is not a number.`);
  }
  if (!Number.isFinite(maxLength)) {
    throw new TypeError(`${maxLength} is not a number.`);
  }
  if (!Number.isFinite(minRange)) {
    throw new TypeError(`${minRange} is not a number.`);
  }
  if (!Number.isFinite(maxRange)) {
    throw new TypeError(`${maxRange} is not a number.`);
  }
  const l = arr.length;
  if (l < minLength || l > maxLength) {
    throw new Error(`Unexpected array length ${l}.`);
  }
  let i = 0;
  while (i < l) {
    const v = arr[i] as number;
    if (!Number.isFinite(v)) {
      throw new TypeError(`${v} is not a number.`);
    } else if (i < TRIA && validateRange && (v < minRange || v > maxRange)) {
      throw new RangeError(`${v} is not between ${minRange} and ${maxRange}.`);
    } else if (i === TRIA && (v < 0 || v > 1)) {
      throw new RangeError(`${v} is not between 0 and 1.`);
    }
    i++;
  }
  if (alpha && l === TRIA) {
    arr.push(1);
  }
  return arr;
};

/**
 * normalize color components
 * @param colorA - color components [v1, v2, v3, v4]
 * @param colorB - color components [v1, v2, v3, v4]
 * @param [skip] - skip validate
 * @returns result - [colorA, colorB]
 */
export const normalizeColorComponents = (
  colorA: NumStrColorChannels,
  colorB: NumStrColorChannels,
  skip: boolean = false
): [ColorChannels, ColorChannels] => {
  if (!Array.isArray(colorA)) {
    throw new TypeError(`${colorA} is not an array.`);
  } else if (colorA.length !== QUAD) {
    throw new Error(`Unexpected array length ${colorA.length}.`);
  }
  if (!Array.isArray(colorB)) {
    throw new TypeError(`${colorB} is not an array.`);
  } else if (colorB.length !== QUAD) {
    throw new Error(`Unexpected array length ${colorB.length}.`);
  }
  let i = 0;
  while (i < QUAD) {
    if (colorA[i] === NONE && colorB[i] === NONE) {
      colorA[i] = 0;
      colorB[i] = 0;
    } else if (colorA[i] === NONE) {
      colorA[i] = colorB[i] as number;
    } else if (colorB[i] === NONE) {
      colorB[i] = colorA[i] as number;
    }
    i++;
  }
  if (skip) {
    return [colorA as ColorChannels, colorB as ColorChannels];
  }
  const validatedColorA = validateColorComponents(colorA as ColorChannels, {
    minLength: QUAD,
    validateRange: false
  });
  const validatedColorB = validateColorComponents(colorB as ColorChannels, {
    minLength: QUAD,
    validateRange: false
  });
  return [validatedColorA as ColorChannels, validatedColorB as ColorChannels];
};

/**
 * transform matrix
 * @param mtx - 3 * 3 matrix
 * @param vct - vector
 * @param [skip] - skip validate
 * @returns TriColorChannels - [p1, p2, p3]
 */
export const transformMatrix = (
  mtx: ReadonlyColorMatrix,
  vct: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  if (!Array.isArray(mtx)) {
    throw new TypeError(`${mtx} is not an array.`);
  } else if (mtx.length !== TRIA) {
    throw new Error(`Unexpected array length ${mtx.length}.`);
  } else if (!skip) {
    for (let i of mtx) {
      i = validateColorComponents(i as TriColorChannels, {
        maxLength: TRIA,
        validateRange: false
      }) as TriColorChannels;
    }
  }
  const [[r1c1, r1c2, r1c3], [r2c1, r2c2, r2c3], [r3c1, r3c2, r3c3]] = mtx;
  let v1, v2, v3;
  if (skip) {
    [v1, v2, v3] = vct;
  } else {
    [v1, v2, v3] = validateColorComponents(vct, {
      maxLength: TRIA,
      validateRange: false
    });
  }
  const p1 = r1c1 * v1 + r1c2 * v2 + r1c3 * v3;
  const p2 = r2c1 * v1 + r2c2 * v2 + r2c3 * v3;
  const p3 = r3c1 * v1 + r3c2 * v2 + r3c3 * v3;
  return [p1, p2, p3];
};

/**
 * transform rgb to linear rgb
 * @param rgb - [r, g, b] r|g|b: 0..255
 * @param [skip] - skip validate
 * @returns TriColorChannels - [r, g, b] r|g|b: 0..1
 */
export const transformRgbToLinearRgb = (
  rgb: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  let rr, gg, bb;
  if (skip) {
    [rr, gg, bb] = rgb;
  } else {
    [rr, gg, bb] = validateColorComponents(rgb, {
      maxLength: TRIA,
      maxRange: MAX_RGB
    });
  }
  let r = rr / MAX_RGB;
  let g = gg / MAX_RGB;
  let b = bb / MAX_RGB;
  const COND_POW = 0.04045;
  if (r > COND_POW) {
    r = Math.pow((r + LINEAR_OFFSET) / (1 + LINEAR_OFFSET), POW_LINEAR);
  } else {
    r /= LINEAR_COEF;
  }
  if (g > COND_POW) {
    g = Math.pow((g + LINEAR_OFFSET) / (1 + LINEAR_OFFSET), POW_LINEAR);
  } else {
    g /= LINEAR_COEF;
  }
  if (b > COND_POW) {
    b = Math.pow((b + LINEAR_OFFSET) / (1 + LINEAR_OFFSET), POW_LINEAR);
  } else {
    b /= LINEAR_COEF;
  }
  return [r, g, b];
};

/**
 * transform rgb to xyz
 * @param rgb - [r, g, b] r|g|b: 0..255
 * @param [skip] - skip validate
 * @returns TriColorChannels - [x, y, z]
 */
export const transformRgbToXyz = (
  rgb: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  if (!skip) {
    rgb = validateColorComponents(rgb, {
      maxLength: TRIA,
      maxRange: MAX_RGB
    }) as TriColorChannels;
  }
  rgb = transformRgbToLinearRgb(rgb, true);
  const xyz = transformMatrix(MATRIX_L_RGB_TO_XYZ, rgb, true);
  return xyz;
};

/**
 * transform rgb to xyz-d50
 * @param rgb - [r, g, b] r|g|b: 0..255 alpha: 0..1
 * @returns TriColorChannels - [x, y, z]
 */
export const transformRgbToXyzD50 = (
  rgb: TriColorChannels
): TriColorChannels => {
  let xyz = transformRgbToXyz(rgb);
  xyz = transformMatrix(MATRIX_D65_TO_D50, xyz, true);
  return xyz;
};

/**
 * transform linear rgb to rgb
 * @param rgb - [r, g, b] r|g|b: 0..1
 * @param [round] - round result
 * @returns TriColorChannels - [r, g, b] r|g|b: 0..255
 */
export const transformLinearRgbToRgb = (
  rgb: TriColorChannels,
  round: boolean = false
): TriColorChannels => {
  let [r, g, b] = validateColorComponents(rgb, {
    maxLength: TRIA
  });
  const COND_POW = 809 / 258400;
  if (r > COND_POW) {
    r = Math.pow(r, 1 / POW_LINEAR) * (1 + LINEAR_OFFSET) - LINEAR_OFFSET;
  } else {
    r *= LINEAR_COEF;
  }
  r *= MAX_RGB;
  if (g > COND_POW) {
    g = Math.pow(g, 1 / POW_LINEAR) * (1 + LINEAR_OFFSET) - LINEAR_OFFSET;
  } else {
    g *= LINEAR_COEF;
  }
  g *= MAX_RGB;
  if (b > COND_POW) {
    b = Math.pow(b, 1 / POW_LINEAR) * (1 + LINEAR_OFFSET) - LINEAR_OFFSET;
  } else {
    b *= LINEAR_COEF;
  }
  b *= MAX_RGB;
  return [
    round ? Math.round(r) : r,
    round ? Math.round(g) : g,
    round ? Math.round(b) : b
  ];
};

/**
 * transform xyz to rgb
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [r, g, b] r|g|b: 0..255
 */
export const transformXyzToRgb = (
  xyz: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  if (!skip) {
    xyz = validateColorComponents(xyz, {
      maxLength: TRIA,
      validateRange: false
    }) as TriColorChannels;
  }
  let [r, g, b] = transformMatrix(MATRIX_XYZ_TO_L_RGB, xyz, true);
  [r, g, b] = transformLinearRgbToRgb(
    [
      Math.min(Math.max(r, 0), 1),
      Math.min(Math.max(g, 0), 1),
      Math.min(Math.max(b, 0), 1)
    ],
    true
  );
  return [r, g, b];
};

/**
 * transform xyz to xyz-d50
 * @param xyz - [x, y, z]
 * @returns TriColorChannels - [x, y, z]
 */
export const transformXyzToXyzD50 = (
  xyz: TriColorChannels
): TriColorChannels => {
  xyz = validateColorComponents(xyz, {
    maxLength: TRIA,
    validateRange: false
  }) as TriColorChannels;
  xyz = transformMatrix(MATRIX_D65_TO_D50, xyz, true);
  return xyz;
};

/**
 * transform xyz to hsl
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [h, s, l]
 */
export const transformXyzToHsl = (
  xyz: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  const [rr, gg, bb] = transformXyzToRgb(xyz, skip);
  const r = rr / MAX_RGB;
  const g = gg / MAX_RGB;
  const b = bb / MAX_RGB;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const d = max - min;
  const l = (max + min) * HALF * MAX_PCT;
  let h, s;
  if (Math.round(l) === 0 || Math.round(l) === MAX_PCT) {
    h = 0;
    s = 0;
  } else {
    s = (d / (1 - Math.abs(max + min - 1))) * MAX_PCT;
    if (s === 0) {
      h = 0;
    } else {
      switch (max) {
        case r:
          h = (g - b) / d;
          break;
        case g:
          h = (b - r) / d + DUO;
          break;
        case b:
        default:
          h = (r - g) / d + QUAD;
          break;
      }
      h = (h * SEXA) % DEG;
      if (h < 0) {
        h += DEG;
      }
    }
  }
  return [h, s, l];
};

/**
 * transform xyz to hwb
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [h, w, b]
 */
export const transformXyzToHwb = (
  xyz: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  const [r, g, b] = transformXyzToRgb(xyz, skip);
  const wh = Math.min(r, g, b) / MAX_RGB;
  const bk = 1 - Math.max(r, g, b) / MAX_RGB;
  let h;
  if (wh + bk === 1) {
    h = 0;
  } else {
    [h] = transformXyzToHsl(xyz);
  }
  return [h, wh * MAX_PCT, bk * MAX_PCT];
};

/**
 * transform xyz to oklab
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [l, a, b]
 */
export const transformXyzToOklab = (
  xyz: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  if (!skip) {
    xyz = validateColorComponents(xyz, {
      maxLength: TRIA,
      validateRange: false
    }) as TriColorChannels;
  }
  const lms = transformMatrix(MATRIX_XYZ_TO_LMS, xyz, true);
  const xyzLms = lms.map((c: number) => Math.cbrt(c)) as TriColorChannels;
  let [l, a, b] = transformMatrix(MATRIX_LMS_TO_OKLAB, xyzLms, true);
  l = Math.min(Math.max(l, 0), 1);
  const lPct = Math.round(parseFloat(l.toFixed(QUAD)) * MAX_PCT);
  if (lPct === 0 || lPct === MAX_PCT) {
    a = 0;
    b = 0;
  }
  return [l, a, b];
};

/**
 * transform xyz to oklch
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [l, c, h]
 */
export const transformXyzToOklch = (
  xyz: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  const [l, a, b] = transformXyzToOklab(xyz, skip);
  let c, h;
  const lPct = Math.round(parseFloat(l.toFixed(QUAD)) * MAX_PCT);
  if (lPct === 0 || lPct === MAX_PCT) {
    c = 0;
    h = 0;
  } else {
    c = Math.max(Math.sqrt(Math.pow(a, POW_SQR) + Math.pow(b, POW_SQR)), 0);
    if (parseFloat(c.toFixed(QUAD)) === 0) {
      h = 0;
    } else {
      h = (Math.atan2(b, a) * DEG_HALF) / Math.PI;
      if (h < 0) {
        h += DEG;
      }
    }
  }
  return [l, c, h];
};

/**
 * transform xyz D50 to rgb
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [r, g, b] r|g|b: 0..255
 */
export const transformXyzD50ToRgb = (
  xyz: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  if (!skip) {
    xyz = validateColorComponents(xyz, {
      maxLength: TRIA,
      validateRange: false
    }) as TriColorChannels;
  }
  const xyzD65 = transformMatrix(MATRIX_D50_TO_D65, xyz, true);
  const rgb = transformXyzToRgb(xyzD65, true);
  return rgb;
};

/**
 * transform xyz-d50 to lab
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [l, a, b]
 */
export const transformXyzD50ToLab = (
  xyz: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  if (!skip) {
    xyz = validateColorComponents(xyz, {
      maxLength: TRIA,
      validateRange: false
    }) as TriColorChannels;
  }
  const xyzD50 = xyz.map((val: number, i: number) => val / (D50[i] as number));
  const [f0, f1, f2] = xyzD50.map((val: number) =>
    val > LAB_EPSILON ? Math.cbrt(val) : (LAB_KAPPA * val + 16) / LAB_L
  ) as TriColorChannels;
  const l = Math.min(Math.max(LAB_L * f1 - HEX, 0), MAX_PCT);
  let a, b;
  if (l === 0 || l === MAX_PCT) {
    a = 0;
    b = 0;
  } else {
    a = (f0 - f1) * LAB_A;
    b = (f1 - f2) * LAB_B;
  }
  return [l, a, b];
};

/**
 * transform xyz-d50 to lch
 * @param xyz - [x, y, z]
 * @param [skip] - skip validate
 * @returns TriColorChannels - [l, c, h]
 */
export const transformXyzD50ToLch = (
  xyz: TriColorChannels,
  skip: boolean = false
): TriColorChannels => {
  const [l, a, b] = transformXyzD50ToLab(xyz, skip);
  let c, h;
  if (l === 0 || l === MAX_PCT) {
    c = 0;
    h = 0;
  } else {
    c = Math.max(Math.sqrt(Math.pow(a, POW_SQR) + Math.pow(b, POW_SQR)), 0);
    h = (Math.atan2(b, a) * DEG_HALF) / Math.PI;
    if (h < 0) {
      h += DEG;
    }
  }
  return [l, c, h];
};
