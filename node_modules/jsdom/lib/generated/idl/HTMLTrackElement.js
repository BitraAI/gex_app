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
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLTrackElement";

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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLTrackElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLTrackElement"].prototype;
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
  class HTMLTrackElement extends globalObject.HTMLElement {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    get kind() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get kind");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("kind");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set kind(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set kind");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'kind' property on 'HTMLTrackElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("kind", V);
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
        context: "Failed to set the 'src' property on 'HTMLTrackElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("src", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get srclang() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get srclang");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("srclang");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set srclang(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set srclang");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'srclang' property on 'HTMLTrackElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("srclang", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get label() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get label");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("label");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set label(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set label");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'label' property on 'HTMLTrackElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("label", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get default() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get default");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("default") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set default(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set default");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'default' property on 'HTMLTrackElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("default", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("default");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get readyState() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get readyState");
      return $impl["readyState"];
    }
  }
  Object.defineProperties(HTMLTrackElement.prototype, {
    kind: { enumerable: true },
    src: { enumerable: true },
    srclang: { enumerable: true },
    label: { enumerable: true },
    default: { enumerable: true },
    readyState: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLTrackElement", configurable: true },
    NONE: { value: 0, enumerable: true },
    LOADING: { value: 1, enumerable: true },
    LOADED: { value: 2, enumerable: true },
    ERROR: { value: 3, enumerable: true }
  });
  Object.defineProperties(HTMLTrackElement, {
    NONE: { value: 0, enumerable: true },
    LOADING: { value: 1, enumerable: true },
    LOADED: { value: 2, enumerable: true },
    ERROR: { value: 3, enumerable: true }
  });
  ctorRegistry[interfaceName] = HTMLTrackElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLTrackElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLTrackElement-impl.js");
