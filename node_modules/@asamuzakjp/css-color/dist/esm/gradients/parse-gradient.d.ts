/**
 * gradient
 */
import { Gradient, Options } from '../typedef';
/**
 * parse CSS gradient
 * @param value - gradient value
 * @param [opt] - options
 * @returns parsed result
 */
export declare const parseGradient: (value: string, opt?: Options) => Gradient | null;
