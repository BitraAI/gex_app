/**
 * cache
 */
import { LRUCache } from 'lru-cache';
import { Options } from '../typedef';
/**
 * CacheItem
 */
export declare class CacheItem<T = unknown> {
    #private;
    constructor(item: T);
    get item(): T;
}
export declare const lruCache: LRUCache<string, CacheItem<any>, unknown>;
/**
 * set cache
 * @param key - cache key
 * @param value - value to cache
 * @returns void
 */
export declare const setCache: <T>(key: string, value: T | CacheItem<T>) => void;
/**
 * get cache
 * @param key - cache key
 * @returns cached item or false otherwise
 */
export declare const getCache: <T = unknown>(key: string) => CacheItem<T> | false;
/**
 * create cache key
 * @param keyData - key data
 * @param [opt] - options
 * @returns cache key
 */
export declare const createCacheKey: (keyData: Record<string, string>, opt?: Options) => string;
