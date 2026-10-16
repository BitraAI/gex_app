/**
 * typedef
 */

import { CSSToken } from '@csstools/css-tokenizer';

/**
 * Supported CSS gradient function types.
 */
export type GradientType =
  | 'linear-gradient'
  | 'repeating-linear-gradient'
  | 'radial-gradient'
  | 'repeating-radial-gradient'
  | 'conic-gradient'
  | 'repeating-conic-gradient';

/**
 * Known CSS color spaces.
 */
type KnownColorSpace =
  | 'srgb'
  | 'srgb-linear'
  | 'display-p3'
  | 'a98-rgb'
  | 'prophoto-rgb'
  | 'rec2020'
  | 'xyz'
  | 'xyz-d50'
  | 'xyz-d65';

/**
 * Supported CSS color space string or custom space.
 */
export type ColorSpace = KnownColorSpace | (string & {});

/**
 * Known CSS color output and input formats.
 */
type KnownColorFormat =
  | 'hex'
  | 'hexAlpha'
  | 'rgb'
  | 'hsl'
  | 'hwb'
  | 'lab'
  | 'lch'
  | 'oklab'
  | 'oklch'
  | 'computed'
  | 'specified'
  | 'mix';

/**
 * Color format option or custom string.
 */
export type ColorFormat = KnownColorFormat | (string & {});

/**
 * Hue interpolation methods for color spaces with hue.
 */
export type HueArc = 'shorter' | 'longer' | 'increasing' | 'decreasing';

/**
 * Flags indicating missing or powerless channels [c1, c2, c3, alpha].
 */
export type ChannelNoneFlags = [
  c1: boolean,
  c2: boolean,
  c3: boolean,
  alpha: boolean
];

/**
 * AST node representation for the calc() parser.
 */
export type CalcASTNode = string | CalcASTNode[];

/**
 * Calculation token stream, including its terminal EOF token, and cursor.
 */
export interface CalculationState {
  tokens: CSSToken[];
  index: number;
}

/**
 * Custom property resolver value or callback function.
 */
type CustomPropertyResolver = string | ((key: string) => string | undefined);

/**
 * Dimension resolver value or callback function.
 */
type DimensionResolver = number | ((key: string) => number | undefined);

/**
 * CSS dimension unit resolution map.
 */
interface DimensionMap {
  [key: string]: DimensionResolver | undefined;
  /** Custom dimension unit resolver callback. */
  callback?: (key: string) => number | undefined;
  /** Font size of the element in pixels. */
  em?: number;
  /** Root element font size in pixels. */
  rem?: number;
  /** Viewport height in pixels. */
  vh?: number;
  /** Viewport width in pixels. */
  vw?: number;
}

/**
 * Custom property lookup map or callback handler.
 */
interface CustomPropertyMap {
  [key: string]: CustomPropertyResolver | undefined;
  /** Custom property resolver callback function. */
  callback?: (key: string) => string | undefined;
}

/**
 * Parsing and resolution options.
 */
export interface Options {
  /** Force alpha channel output. */
  alpha?: boolean;
  /** Preferred color scheme context. */
  colorScheme?: string;
  /** Target color space for output. */
  colorSpace?: ColorSpace;
  /** Value used for `currentColor` keyword. */
  currentColor?: string;
  /** Custom property resolvers. */
  customProperty?: CustomPropertyMap;
  /** Adapt XYZ coordinates to D50 illuminant. */
  d50?: boolean;
  /** Channel values delimiter string or list. */
  delimiter?: string | readonly string[];
  /** Dimension resolution settings. */
  dimension?: DimensionMap;
  /** Output color format. */
  format?: ColorFormat;
  /** Maximum length limit for parsed string. */
  maxLength?: number;
  /** Return null instead of throwing on invalid input. */
  nullable?: boolean;
  /** Retain comments during parsing. */
  preserveComment?: boolean;
}

/**
 * Three-element color channel tuple [x, y, z].
 */
export type TriColorChannels = [x: number, y: number, z: number];

/**
 * Readonly three-element color channel tuple [x, y, z].
 */
export type ReadonlyTriColorChannels = readonly [
  x: number,
  y: number,
  z: number
];

/**
 * 3x3 color conversion matrix tuple.
 */
export type ReadonlyColorMatrix = readonly [
  r1: ReadonlyTriColorChannels,
  r2: ReadonlyTriColorChannels,
  r3: ReadonlyTriColorChannels
];

/**
 * Four-element color channel numeric tuple [x, y, z, alpha].
 */
export type ColorChannels = [x: number, y: number, z: number, alpha: number];

/**
 * Four-element color channel string tuple [x, y, z, alpha].
 */
export type StringColorChannels = [
  x: string,
  y: string,
  z: string,
  alpha: string | undefined
];

/**
 * Four-element color channel numeric/string tuple [x, y, z, alpha].
 */
export type NumStrColorChannels = [
  x: number | string,
  y: number | string,
  z: number | string,
  alpha: number | string
];

/**
 * Color channel tuple with missing/powerless string tags.
 */
export type ColorChannelsWithPowerless = [
  x: number | string,
  y: number | string,
  z: number | string,
  alpha: number
];

/**
 * Color space name and three channel strings with alpha.
 */
export type StringColorSpacedChannels = [
  cs: string,
  x: string,
  y: string,
  z: string,
  alpha: string | undefined
];

/**
 * Resolved computed color channel representation.
 */
export type ComputedColorChannels = [
  cs: string,
  x: number,
  y: number,
  z: number,
  alpha: number
];

/**
 * Resolved specified color channel representation.
 */
export type SpecifiedColorChannels = [
  cs: string,
  x: number | string,
  y: number | string,
  z: number | string,
  alpha: number | string
];

/**
 * RegExp match result tuple with 3 capture groups.
 */
export type MatchedRegExp3 = [
  match: string,
  gr1: string,
  gr2: string,
  gr3: string
];

/**
 * RegExp match result tuple with 4 capture groups.
 */
export type MatchedRegExp4 = [
  match: string,
  gr1: string,
  gr2: string,
  gr3: string,
  gr4: string
];

/**
 * Standard matched RegExp tuple alias.
 */
export type MatchedRegExp = MatchedRegExp4;

/**
 * Component validation configuration.
 */
export interface ValidateColorComponentsOptions {
  /** Validate alpha channel presence. */
  alpha?: boolean;
  /** Minimum number of components. */
  minLength?: number;
  /** Maximum number of components. */
  maxLength?: number;
  /** Minimum allowed component value. */
  minRange?: number;
  /** Maximum allowed component value. */
  maxRange?: number;
  /** Whether to enforce component value range check. */
  validateRange?: boolean;
}

/**
 * Options for linear RGB conversion.
 */
export interface LinearRgbOptions {
  /** Target color space for conversion. */
  colorSpace?: ColorSpace;
  /** Output color format. */
  format?: ColorFormat;
}

/**
 * Function type for converting color string to channel values.
 */
export type ColorConvertFn = (
  value: string,
  opt?: Options
) => ColorChannels | ColorChannelsWithPowerless | null;

/**
 * Function type for resolving CSS color expressions.
 */
export type ColorResolverFn = (
  value: string,
  opt?: Options
) => SpecifiedColorChannels | string | null;

/**
 * Parsed CSS gradient object structure.
 */
export interface Gradient {
  /** Raw gradient CSS string value. */
  value: string;
  /** Type of gradient expression. */
  type: GradientType;
  /** Parsed gradient line parameter. */
  gradientLine?: string;
  /** List of color stops. */
  colorStopList: ColorStopList;
}

/**
 * Color stops validation result.
 */
export interface ValidateColorStops {
  /** Extracted color stop strings. */
  colorStops: string[];
  /** Flag indicating stop list validity. */
  valid: boolean;
}

/**
 * Gradient line validation result.
 */
export interface ValidateGradientLine {
  /** Extracted gradient line string. */
  line: string;
  /** Flag indicating line syntax validity. */
  valid: boolean;
}

/**
 * Tuple representing a minimum of two color stops.
 */
export type ColorStopList = [string, string, ...string[]];

/**
 * Parsed color space parameter for color-mix().
 */
export interface ColorSpaceParseResult {
  /** Color space name. */
  colorSpace: ColorSpace;
  /** Interpolation hue method. */
  hueArc: HueArc | string;
}

/**
 * Color and percentage pair for color-mix().
 */
export interface ColorAndPct {
  /** Raw color string. */
  color: string;
  /** Raw percentage string. */
  pct: string;
}

/**
 * Normalized percentage values for color mixing.
 */
export interface NormalizedPercentages {
  /** First color percentage weight (0 to 1). */
  pA: number;
  /** Second color percentage weight (0 to 1). */
  pB: number;
  /** Multiplier factor for un-normalized sums. */
  m: number;
}

/**
 * Interpolated channels and alpha output.
 */
export interface InterpolatedComponents {
  /** Three-element color component values. */
  comps: TriColorChannels;
  /** Resulting alpha transparency. */
  alpha: number;
}
