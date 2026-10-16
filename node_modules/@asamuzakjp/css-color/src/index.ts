/*!
 * CSS color - Resolve, parse, convert CSS color.
 * @license MIT
 * @copyright asamuzaK (Kazz)
 * @see {@link https://github.com/asamuzaK/cssColor/blob/main/LICENSE}
 */

import { isGradient, resolveGradient } from './gradients/gradient';
import { cssCalc, cssVar } from './resolvers/css-calc-var';
import { isColor } from './resolvers/resolve';
import {
  extractDashedIdent,
  resolveLengthInPixels,
  splitValue
} from './utils/util';

export { convert } from './converters/convert';
export { resolveGradient } from './gradients/gradient';
export { resolve } from './resolvers/resolve';

/* utils */
export const utils = {
  cssCalc,
  cssVar,
  extractDashedIdent,
  isColor,
  isGradient,
  /**
   * @deprecated Use `resolveGradient` directly instead.
   */
  resolveGradient,
  resolveLengthInPixels,
  splitValue
};
