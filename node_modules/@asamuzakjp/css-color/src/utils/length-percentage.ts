/**
 * length-percentage
 */

import {
  CSSToken,
  ParseError,
  tokenize,
  TokenType
} from '@csstools/css-tokenizer';
import { CalculationState } from '../typedef';
import { isString } from './common';

/* constants */
import { LENGTH } from './constant';

/* regexp */
const REG_LENGTH = new RegExp(`^(?:${LENGTH})$`, 'i');
const REG_CALC = /^(?:calc|min|max|clamp)\(/i;
const REG_CALC_KEYWORD = /^(?:e|pi|-?infinity|NaN)$/i;

/**
 * Advance past whitespace and comments in a calculation.
 * @param state - token stream and cursor
 */
export const skipCalculationWhitespace = (state: CalculationState): void => {
  while (
    state.tokens[state.index]![0] === TokenType.Whitespace ||
    state.tokens[state.index]![0] === TokenType.Comment
  ) {
    state.index++;
  }
};

/**
 * Check for actual whitespace, ignoring adjacent comments.
 * @param tokens - token stream
 * @param start - first token to check
 * @param step - direction to scan
 * @returns whether whitespace occurs before another non-comment token
 */
export const hasCalculationWhitespace = (
  tokens: CSSToken[],
  start: number,
  step: 1 | -1
): boolean => {
  for (let i = start; i >= 0 && i < tokens.length; i += step) {
    if (tokens[i]![0] === TokenType.Whitespace) {
      return true;
    }
    if (tokens[i]![0] !== TokenType.Comment) {
      break;
    }
  }
  return false;
};

/**
 * Parse multiplication and division of calculation operands.
 * Multiplication requires a number on one side, division a number divisor.
 * This subset intentionally excludes CSS Values Level 4 typed arithmetic.
 * @param state - token stream and cursor
 * @returns calculation type or null on failure
 */
export const parseCalculationProduct = (
  state: CalculationState
): number | null => {
  let type = parseCalculationValue(state);
  if (type === null) {
    return null;
  }
  skipCalculationWhitespace(state);
  while (
    state.tokens[state.index]![0] === TokenType.Delim &&
    (state.tokens[state.index]![1] === '*' ||
      state.tokens[state.index]![1] === '/')
  ) {
    const operator = state.tokens[state.index++]![1];
    const right = parseCalculationValue(state);
    if (
      right === null ||
      (operator === '*' ? type !== 0 && right !== 0 : right !== 0)
    ) {
      return null;
    }
    type += right;
    skipCalculationWhitespace(state);
  }
  return type;
};

/**
 * Parse addition and subtraction, requiring matching operand types.
 * @param state - token stream and cursor
 * @returns calculation type or null on failure
 */
export const parseCalculationSum = (state: CalculationState): number | null => {
  const type = parseCalculationProduct(state);
  if (type === null) {
    return null;
  }
  while (
    state.tokens[state.index]![0] === TokenType.Delim &&
    (state.tokens[state.index]![1] === '+' ||
      state.tokens[state.index]![1] === '-')
  ) {
    if (
      !hasCalculationWhitespace(state.tokens, state.index - 1, -1) ||
      !hasCalculationWhitespace(state.tokens, state.index + 1, 1)
    ) {
      return null;
    }
    state.index++;
    if (parseCalculationProduct(state) !== type) {
      return null;
    }
  }
  return type;
};

/**
 * Parse a scalar, length, percentage, parenthesized sum or math function.
 * Percentages receive the length percent hint in this context.
 * @param state - token stream and cursor
 * @returns calculation type or null on failure
 */
export function parseCalculationValue(state: CalculationState): number | null {
  skipCalculationWhitespace(state);
  if (state.tokens[state.index]![0] === TokenType.EOF) {
    return null;
  }
  const token = state.tokens[state.index++]!;
  switch (token[0]) {
    case TokenType.Number: {
      return 0;
    }
    case TokenType.Percentage: {
      return 1;
    }
    case TokenType.Dimension: {
      return REG_LENGTH.test(token[4].unit) ? 1 : null;
    }
    case TokenType.Ident: {
      return REG_CALC_KEYWORD.test(token[4].value) ? 0 : null;
    }
    case TokenType.OpenParen:
    case TokenType.Function: {
      const name =
        token[0] === TokenType.Function ? token[4].value.toLowerCase() : 'calc';
      if (!['calc', 'min', 'max', 'clamp'].includes(name)) {
        return null;
      }
      const type = parseCalculationSum(state);
      if (type === null) {
        return null;
      }
      let count = 1;
      while (state.tokens[state.index]![0] === TokenType.Comma) {
        state.index++;
        if (parseCalculationSum(state) !== type) {
          return null;
        }
        count++;
      }
      if (
        state.tokens[state.index]![0] !== TokenType.CloseParen ||
        (name === 'calc' && count !== 1) ||
        (name === 'clamp' && count !== 3)
      ) {
        return null;
      }
      state.index++;
      return type;
    }
    default: {
      return null;
    }
  }
}

/**
 * Validate a calculation in a length-percentage context. Types are represented
 * as 0 for numbers and 1 for lengths/percentages, with scalar products only.
 * @param value - calculation
 * @returns whether the calculation has type length-percentage
 */
export const isLengthPercentageCalculation = (value: unknown): boolean => {
  if (!isString(value) || !REG_CALC.test(value)) {
    return false;
  }
  const errors: ParseError[] = [];
  const state: CalculationState = {
    tokens: tokenize(
      { css: value },
      { onParseError: errors.push.bind(errors) }
    ),
    index: 0
  };
  const type = parseCalculationValue(state);
  skipCalculationWhitespace(state);
  return (
    errors.length === 0 &&
    type === 1 &&
    state.tokens[state.index]![0] === TokenType.EOF
  );
};
