/**
 * gradient
 */

import { isValidColor } from '../resolvers/resolve-color';
import { ColorStopList, Gradient, GradientType, Options } from '../typedef';
import { createCacheKey, getCache, setCache } from '../utils/cache';
import { isString } from '../utils/common';
import { splitValue } from '../utils/util';
import {
  getGradientType,
  splitColorStop,
  validateColorStopList,
  validateGradientLine
} from './gradient-util';

/* constants */
import { VAL_SPEC } from '../utils/constant';
const NAMESPACE = 'gradient';
const COLOR_OPT = {
  format: VAL_SPEC,
  nullable: true
};

/* regexp */
const REG_GRAD = /^(?:repeating-)?(?:conic|linear|radial)-gradient\(/;

/**
 * parse CSS gradient
 * @param value - gradient value
 * @param [opt] - options
 * @returns parsed result
 */
export const parseGradient = (
  value: string,
  opt: Options = {}
): Gradient | null => {
  if (!isString(value)) {
    return null;
  }
  const trimmedValue = value.trim();
  const cacheKey: string = createCacheKey(
    { namespace: NAMESPACE, name: 'parseGradient', value: trimmedValue },
    opt
  );
  const cachedResult = getCache(cacheKey);
  if (cachedResult !== false) {
    return cachedResult.item as Gradient | null;
  }
  const type = getGradientType(trimmedValue);
  const gradValue = trimmedValue.replace(REG_GRAD, '').replace(/\)$/, '');
  if (type && gradValue) {
    const [lineOrColorStop, ...itemList] = splitValue(gradValue, {
      delimiter: ',',
      preserveComment: true
    });
    if (!lineOrColorStop) {
      setCache(cacheKey, null);
      return null;
    }
    const [firstPart] = splitColorStop(lineOrColorStop);
    if (firstPart && isValidColor(splitValue(firstPart).join(' '), COLOR_OPT)) {
      itemList.unshift(lineOrColorStop);
      const { colorStops, valid } = validateColorStopList(itemList, type, opt);
      if (valid) {
        const res: Gradient = {
          value: trimmedValue,
          type: type as GradientType,
          colorStopList: colorStops as ColorStopList
        };
        setCache(cacheKey, res);
        return res;
      }
    } else if (itemList.length > 1) {
      const { line: gradientLine, valid: validLine } = validateGradientLine(
        splitValue(lineOrColorStop).join(' '),
        type
      );
      const { colorStops, valid: validColorStops } = validateColorStopList(
        itemList,
        type,
        opt
      );
      if (validLine && validColorStops) {
        const res: Gradient = {
          value: trimmedValue,
          type: type as GradientType,
          gradientLine,
          colorStopList: colorStops as ColorStopList
        };
        setCache(cacheKey, res);
        return res;
      }
    }
  }
  setCache(cacheKey, null);
  return null;
};
