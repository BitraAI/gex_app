/**
 * cache
 */

import { LRUCache } from 'lru-cache';
import { Options } from '../typedef';

/* constants */
const CACHE_SIZE = 4096;

/**
 * CacheItem
 */
export class CacheItem<T = unknown> {
  /* private */
  #item: T;

  constructor(item: T) {
    this.#item = item;
  }

  get item(): T {
    return this.#item;
  }
}

/*
 * lru cache instance
 */
export const lruCache = new LRUCache<string, CacheItem<any>>({
  max: CACHE_SIZE
});

/**
 * set cache
 * @param key - cache key
 * @param value - value to cache
 * @returns void
 */
export const setCache = <T>(key: string, value: T | CacheItem<T>): void => {
  if (!key) {
    return;
  }
  if (value instanceof CacheItem) {
    lruCache.set(key, value);
  } else {
    lruCache.set(key, new CacheItem<T>(value));
  }
};

/**
 * get cache
 * @param key - cache key
 * @returns cached item or false otherwise
 */
export const getCache = <T = unknown>(key: string): CacheItem<T> | false => {
  if (!key) {
    return false;
  }
  const item = lruCache.get(key);
  if (item !== undefined) {
    return item as CacheItem<T>;
  }
  return false;
};

/**
 * helper function to sort object keys alphabetically
 * @param obj - Object
 * @returns stringified JSON
 */
const stringifySorted = (obj: Record<string, unknown>): string => {
  const keys = Object.keys(obj);
  if (keys.length === 0) {
    return '';
  }
  keys.sort();
  let result = '';
  for (const key of keys) {
    result += `${key}:${JSON.stringify(obj[key])};`;
  }
  return result;
};

/**
 * create cache key
 * @param keyData - key data
 * @param [opt] - options
 * @returns cache key
 */
export const createCacheKey = (
  keyData: Record<string, string>,
  opt: Options = {}
): string => {
  if (
    !keyData ||
    (opt.customProperty && typeof opt.customProperty.callback === 'function') ||
    (opt.dimension && typeof opt.dimension.callback === 'function')
  ) {
    return '';
  }
  const namespace = keyData.namespace || '';
  const name = keyData.name || '';
  const value = keyData.value || '';
  if (!namespace && !name && !value) {
    return '';
  }
  const baseKey = `${namespace}:${name}:${value}`;
  const opts = [];
  for (const [key, val] of Object.entries(opt)) {
    if (key !== 'customProperty' && key !== 'dimension') {
      opts.push(`${key}_${val}`);
    }
  }
  const customPropStr = opt.customProperty
    ? stringifySorted(opt.customProperty as Record<string, unknown>)
    : '';
  const dimStr = opt.dimension
    ? stringifySorted(opt.dimension as Record<string, unknown>)
    : '';
  return `${baseKey}:${opts.sort().join('|')}:${customPropStr}:${dimStr}`;
};
