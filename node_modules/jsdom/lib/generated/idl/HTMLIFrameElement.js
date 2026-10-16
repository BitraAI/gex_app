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

const interfaceName = "HTMLIFrameElement";

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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLIFrameElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLIFrameElement"].prototype;
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
  class HTMLIFrameElement extends globalObject.HTMLElement {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    getSVGDocument() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getSVGDocument");
      return utils.tryWrapperForImpl($impl.getSVGDocument());
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
        context: "Failed to set the 'src' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("src", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get srcdoc() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get srcdoc");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("srcdoc");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set srcdoc(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set srcdoc");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'srcdoc' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("srcdoc", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
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
        context: "Failed to set the 'name' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("name", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get allowFullscreen() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get allowFullscreen");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("allowfullscreen") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set allowFullscreen(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set allowFullscreen");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'allowFullscreen' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("allowfullscreen", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("allowfullscreen");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get width() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get width");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("width");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set width(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set width");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'width' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("width", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get height() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get height");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("height");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set height(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set height");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'height' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("height", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get contentDocument() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get contentDocument");
      return utils.tryWrapperForImpl($impl["contentDocument"]);
    }

    get contentWindow() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get contentWindow");
      return utils.tryWrapperForImpl($impl["contentWindow"]);
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
        context: "Failed to set the 'align' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("align", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get scrolling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get scrolling");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("scrolling");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set scrolling(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set scrolling");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'scrolling' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("scrolling", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get frameBorder() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get frameBorder");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("frameborder");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set frameBorder(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set frameBorder");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'frameBorder' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("frameborder", V);
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
        context: "Failed to set the 'longDesc' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("longdesc", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get marginHeight() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get marginHeight");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("marginheight");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set marginHeight(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set marginHeight");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'marginHeight' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("marginheight", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get marginWidth() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get marginWidth");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("marginwidth");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set marginWidth(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set marginWidth");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'marginWidth' property on 'HTMLIFrameElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("marginwidth", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }
  }
  Object.defineProperties(HTMLIFrameElement.prototype, {
    getSVGDocument: { enumerable: true },
    src: { enumerable: true },
    srcdoc: { enumerable: true },
    name: { enumerable: true },
    allowFullscreen: { enumerable: true },
    width: { enumerable: true },
    height: { enumerable: true },
    contentDocument: { enumerable: true },
    contentWindow: { enumerable: true },
    align: { enumerable: true },
    scrolling: { enumerable: true },
    frameBorder: { enumerable: true },
    longDesc: { enumerable: true },
    marginHeight: { enumerable: true },
    marginWidth: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLIFrameElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLIFrameElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLIFrameElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLIFrameElement-impl.js");
