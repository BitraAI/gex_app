/**
 * matrix
 */
import { ReadonlyColorMatrix, ReadonlyTriColorChannels } from '../typedef';
/**
 * conversion matrices
 * @see https://drafts.csswg.org/css-color-4/#color-conversion-code
 */
export declare const D50: ReadonlyTriColorChannels;
export declare const MATRIX_D50_TO_D65: ReadonlyColorMatrix;
export declare const MATRIX_D65_TO_D50: ReadonlyColorMatrix;
export declare const MATRIX_L_RGB_TO_XYZ: ReadonlyColorMatrix;
export declare const MATRIX_XYZ_TO_L_RGB: ReadonlyColorMatrix;
export declare const MATRIX_XYZ_TO_LMS: ReadonlyColorMatrix;
export declare const MATRIX_LMS_TO_XYZ: ReadonlyColorMatrix;
export declare const MATRIX_OKLAB_TO_LMS: ReadonlyColorMatrix;
export declare const MATRIX_LMS_TO_OKLAB: ReadonlyColorMatrix;
export declare const MATRIX_P3_TO_XYZ: ReadonlyColorMatrix;
export declare const MATRIX_REC2020_TO_XYZ: ReadonlyColorMatrix;
export declare const MATRIX_A98_TO_XYZ: ReadonlyColorMatrix;
export declare const MATRIX_PROPHOTO_TO_XYZ_D50: ReadonlyColorMatrix;
