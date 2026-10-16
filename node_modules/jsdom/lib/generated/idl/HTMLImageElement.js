"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const HTMLConstructor_jsdom_living_helpers_html_constructor =
  require("../../jsdom/living/helpers/html-constructor.js").HTMLConstructor;
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const serializeURLwhatwg_url = require("whatwg-url").serializeURL;
const parseNonNegativeInteger_jsdom_living_helpers_strings =
  require("../../jsdom/living/helpers/strings.js").parseNonNegativeInteger;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLImageElement";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => HTMLElement.interfaceDescriptor);
exports.interfaceDescriptor = $interfaceDescriptor;

function $requireImpl(wrapper, globalObject, context) {
  return utils.requireImplForWrapper(wrapper, $interfaceDescriptor, globalObject, interfaceName, context);
}

exports.is = value => {
  return utils.implForWrapperWithInterface(value, $interfaceDescriptor) !== null;
};
exports.isImpl = value => {
  return utils.isObject(value) && value instanceof Impl.implementation;
};
exports.convert = (globalObject, value, { context = "The provided value" } = {}) => {
  const impl = utils.implForWrapperWithInterface(value, $interfaceDescriptor);
  if (impl !== null) {
    return impl;
  }
  throw new globalObject.TypeError(`${context} is not of type 'HTMLImageElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLImageElement"].prototype;
  }

  return Object.create(proto);
}

exports.create = (globalObject, constructorArgs, privateData) => {
  const wrapper = makeWrapper(globalObject);
  return exports.setup(wrapper, globalObject, constructorArgs, privateData);
};

exports.createImpl = (globalObject, constructorArgs, privateData) => {
  const wrapper = exports.create(globalObject, constructorArgs, privateData);
  return utils.implForWrapper(wrapper);
};

exports._internalSetup = (wrapper, globalObject) => {
  HTMLElement._internalSetup(wrapper, globalObject);
};

exports.setup = (wrapper, globalObject, constructorArgs = [], privateData = {}) => {
  privateData.wrapper = wrapper;

  exports._internalSetup(wrapper, globalObject);
  const impl = new Impl.implementation(globalObject, constructorArgs, privateData);

  utils.registerWrapper(wrapper, impl, $interfaceDescriptor);
  impl[utils.wrapperSymbol] = wrapper;
  if (Impl.init) {
    Impl.init(impl);
  }
  return wrapper;
};

exports.new = (globalObject, newTarget) => {
  const wrapper = makeWrapper(globalObject, newTarget);

  exports._internalSetup(wrapper, globalObject);
  const impl = Object.create(Impl.implementation.prototype);

  utils.registerWrapper(wrapper, impl, $interfaceDescriptor);
  impl[utils.wrapperSymbol] = wrapper;
  if (Impl.init) {
    Impl.init(impl);
  }
  return impl;
};

const exposed = new Set(["Window"]);

exports.install = (globalObject, globalNames) => {
  if (!globalNames.some(globalName => exposed.has(globalName))) {
    return;
  }

  const ctorRegistry = utils.initCtorRegistry(globalObject);
  class HTMLImageElement extends globalObject.HTMLElement {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    get alt() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get alt");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("alt");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set alt(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set alt");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'alt' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("alt", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get src() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get src");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const impl = $impl;
        const value = impl._reflectGetTheContentAttribute("src");
        if (value === null) {
          return "";
        }

        const document = impl._ownerDocument;
        if (this._srcURLCacheKey === value && this._baseURLCache === document._baseURLCache) {
          return this._srcURLCache;
        }

        this._srcURLCacheKey = value;
        this._baseURLCache = document._baseURLCache;

        const urlRecord = document.encodingParseAURL(value);
        if (urlRecord !== null) {
          this._srcURLCache = serializeURLwhatwg_url(urlRecord);
          return this._srcURLCache;
        }
        this._srcURLCache = conversions.USVString(value);
        return this._srcURLCache;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set src(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set src");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'src' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("src", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get srcset() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get srcset");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("srcset");
        return value === null ? "" : conversions.USVString(value);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set srcset(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set srcset");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'srcset' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("srcset", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get sizes() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get sizes");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("sizes");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set sizes(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set sizes");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'sizes' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("sizes", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get crossOrigin() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get crossOrigin");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("crossorigin");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set crossOrigin(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set crossOrigin");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'crossOrigin' property on 'HTMLImageElement': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("crossorigin");
        } else {
          $impl._reflectSetTheContentAttribute("crossorigin", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get useMap() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get useMap");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("usemap");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set useMap(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set useMap");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'useMap' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("usemap", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get isMap() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get isMap");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("ismap") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set isMap(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set isMap");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'isMap' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("ismap", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("ismap");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get width() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get width");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["width"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set width(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set width");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'width' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["width"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get height() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get height");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["height"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set height(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set height");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'height' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["height"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get naturalWidth() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get naturalWidth");
      return $impl["naturalWidth"];
    }

    get naturalHeight() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get naturalHeight");
      return $impl["naturalHeight"];
    }

    get complete() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get complete");
      return $impl["complete"];
    }

    get currentSrc() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get currentSrc");
      return $impl["currentSrc"];
    }

    get name() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get name");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("name");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set name(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set name");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'name' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("name", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get lowsrc() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get lowsrc");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const impl = $impl;
        const value = impl._reflectGetTheContentAttribute("lowsrc");
        if (value === null) {
          return "";
        }

        const document = impl._ownerDocument;
        if (this._lowsrcURLCacheKey === value && this._baseURLCache === document._baseURLCache) {
          return this._lowsrcURLCache;
        }

        this._lowsrcURLCacheKey = value;
        this._baseURLCache = document._baseURLCache;

        const urlRecord = document.encodingParseAURL(value);
        if (urlRecord !== null) {
          this._lowsrcURLCache = serializeURLwhatwg_url(urlRecord);
          return this._lowsrcURLCache;
        }
        this._lowsrcURLCache = conversions.USVString(value);
        return this._lowsrcURLCache;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set lowsrc(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set lowsrc");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'lowsrc' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("lowsrc", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get align() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get align");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("align");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set align(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set align");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'align' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("align", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get hspace() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get hspace");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        let value = $impl._reflectGetTheContentAttribute("hspace");
        if (value !== null) {
          value = parseNonNegativeInteger_jsdom_living_helpers_strings(value);
          if (value !== null && value >= 0 && value <= 2147483647) {
            return value;
          }
        }
        return 0;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set hspace(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set hspace");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'hspace' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const newValue = V <= 2147483647 && V >= 0 ? V : 0;
        $impl._reflectSetTheContentAttribute("hspace", String(newValue));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get vspace() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get vspace");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        let value = $impl._reflectGetTheContentAttribute("vspace");
        if (value !== null) {
          value = parseNonNegativeInteger_jsdom_living_helpers_strings(value);
          if (value !== null && value >= 0 && value <= 2147483647) {
            return value;
          }
        }
        return 0;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set vspace(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set vspace");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'vspace' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const newValue = V <= 2147483647 && V >= 0 ? V : 0;
        $impl._reflectSetTheContentAttribute("vspace", String(newValue));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get longDesc() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get longDesc");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const impl = $impl;
        const value = impl._reflectGetTheContentAttribute("longdesc");
        if (value === null) {
          return "";
        }

        const document = impl._ownerDocument;
        if (this._longdescURLCacheKey === value && this._baseURLCache === document._baseURLCache) {
          return this._longdescURLCache;
        }

        this._longdescURLCacheKey = value;
        this._baseURLCache = document._baseURLCache;

        const urlRecord = document.encodingParseAURL(value);
        if (urlRecord !== null) {
          this._longdescURLCache = serializeURLwhatwg_url(urlRecord);
          return this._longdescURLCache;
        }
        this._longdescURLCache = conversions.USVString(value);
        return this._longdescURLCache;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set longDesc(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set longDesc");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'longDesc' property on 'HTMLImageElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("longdesc", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get border() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get border");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("border");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set border(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set border");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'border' property on 'HTMLImageElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("border", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }
  }
  Object.defineProperties(HTMLImageElement.prototype, {
    alt: { enumerable: true },
    src: { enumerable: true },
    srcset: { enumerable: true },
    sizes: { enumerable: true },
    crossOrigin: { enumerable: true },
    useMap: { enumerable: true },
    isMap: { enumerable: true },
    width: { enumerable: true },
    height: { enumerable: true },
    naturalWidth: { enumerable: true },
    naturalHeight: { enumerable: true },
    complete: { enumerable: true },
    currentSrc: { enumerable: true },
    name: { enumerable: true },
    lowsrc: { enumerable: true },
    align: { enumerable: true },
    hspace: { enumerable: true },
    vspace: { enumerable: true },
    longDesc: { enumerable: true },
    border: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLImageElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLImageElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLImageElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLImageElement-impl.js");
