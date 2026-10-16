/*!
 * CSS color - Resolve, parse, convert CSS color.
 * @license MIT
 * @copyright asamuzaK (Kazz)
 * @see {@link https://github.com/asamuzaK/cssColor/blob/main/LICENSE}
 */
export { convert } from './converters/convert';
export { resolveGradient } from './gradients/gradient';
export { resolve } from './resolvers/resolve';
export declare const utils: {
    cssCalc: (value: string, opt?: import("./typedef").Options) => string;
    cssVar: (value: string, opt?: import("./typedef").Options) => string;
    extractDashedIdent: (value: string) => string[];
    isColor: (value: unknown, opt?: import("./typedef").Options) => boolean;
    isGradient: (value: string, opt?: import("./typedef").Options) => boolean;
    /**
     * @deprecated Use `resolveGradient` directly instead.
     */
    resolveGradient: (value: string, opt?: import("./typedef").Options) => string;
    resolveLengthInPixels: (value: number | string, unit: string | undefined, opt?: import("./typedef").Options) => number;
    splitValue: (value: string, opt?: import("./typedef").Options) => string[];
};
