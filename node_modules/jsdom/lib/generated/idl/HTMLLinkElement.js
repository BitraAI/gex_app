"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const HTMLConstructor_jsdom_living_helpers_html_constructor =
  require("../../jsdom/living/helpers/html-constructor.js").HTMLConstructor;
const serializeURLwhatwg_url = require("whatwg-url").serializeURL;
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLLinkElement";

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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLLinkElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLLinkElement"].prototype;
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
  class HTMLLinkElement extends globalObject.HTMLElement {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    get href() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get href");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const impl = $impl;
        const value = impl._reflectGetTheContentAttribute("href");
        if (value === null) {
          return "";
        }

        const document = impl._ownerDocument;
        if (this._hrefURLCacheKey === value && this._baseURLCache === document._baseURLCache) {
          return this._hrefURLCache;
        }

        this._hrefURLCacheKey = value;
        this._baseURLCache = document._baseURLCache;

        const urlRecord = document.encodingParseAURL(value);
        if (urlRecord !== null) {
          this._hrefURLCache = serializeURLwhatwg_url(urlRecord);
          return this._hrefURLCache;
        }
        this._hrefURLCache = conversions.USVString(value);
        return this._hrefURLCache;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set href(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set href");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'href' property on 'HTMLLinkElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("href", V);
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
          context: "Failed to set the 'crossOrigin' property on 'HTMLLinkElement': The provided value",
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

    get rel() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get rel");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("rel");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set rel(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set rel");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'rel' property on 'HTMLLinkElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("rel", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get relList() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get relList");
      return utils.getSameObject(this, "relList", () => {
        return utils.tryWrapperForImpl($impl["relList"]);
      });
    }

    set relList(V) {
      const esValue = this ?? globalObject;
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set relList");

      const Q = esValue["relList"];
      if (!utils.isObject(Q)) {
        throw new globalObject.TypeError("Property 'relList' is not an object");
      }
      Reflect.set(Q, "value", V);
    }

    get media() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get media");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("media");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set media(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set media");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'media' property on 'HTMLLinkElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("media", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get hreflang() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get hreflang");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("hreflang");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set hreflang(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set hreflang");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'hreflang' property on 'HTMLLinkElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("hreflang", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get type() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get type");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("type");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set type(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set type");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'type' property on 'HTMLLinkElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("type", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get charset() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get charset");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("charset");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set charset(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set charset");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'charset' property on 'HTMLLinkElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("charset", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get rev() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get rev");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("rev");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set rev(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set rev");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'rev' property on 'HTMLLinkElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("rev", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get target() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get target");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("target");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set target(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set target");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'target' property on 'HTMLLinkElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("target", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get sheet() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get sheet");
      return utils.tryWrapperForImpl($impl["sheet"]);
    }
  }
  Object.defineProperties(HTMLLinkElement.prototype, {
    href: { enumerable: true },
    crossOrigin: { enumerable: true },
    rel: { enumerable: true },
    relList: { enumerable: true },
    media: { enumerable: true },
    hreflang: { enumerable: true },
    type: { enumerable: true },
    charset: { enumerable: true },
    rev: { enumerable: true },
    target: { enumerable: true },
    sheet: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLLinkElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLLinkElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLLinkElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLLinkElement-impl.js");
