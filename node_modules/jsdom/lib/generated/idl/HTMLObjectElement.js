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
const parseNonNegativeInteger_jsdom_living_helpers_strings =
  require("../../jsdom/living/helpers/strings.js").parseNonNegativeInteger;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLObjectElement";

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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLObjectElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLObjectElement"].prototype;
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
  class HTMLObjectElement extends globalObject.HTMLElement {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    checkValidity() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "checkValidity");
      return $impl.checkValidity();
    }

    reportValidity() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "reportValidity");
      return $impl.reportValidity();
    }

    setCustomValidity(error) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setCustomValidity");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setCustomValidity' on 'HTMLObjectElement': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'setCustomValidity' on 'HTMLObjectElement': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.setCustomValidity(...args);
    }

    get data() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get data");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const impl = $impl;
        const value = impl._reflectGetTheContentAttribute("data");
        if (value === null) {
          return "";
        }

        const document = impl._ownerDocument;
        if (this._dataURLCacheKey === value && this._baseURLCache === document._baseURLCache) {
          return this._dataURLCache;
        }

        this._dataURLCacheKey = value;
        this._baseURLCache = document._baseURLCache;

        const urlRecord = document.encodingParseAURL(value);
        if (urlRecord !== null) {
          this._dataURLCache = serializeURLwhatwg_url(urlRecord);
          return this._dataURLCache;
        }
        this._dataURLCache = conversions.USVString(value);
        return this._dataURLCache;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set data(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set data");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'data' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("data", V);
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
        context: "Failed to set the 'type' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("type", V);
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
        context: "Failed to set the 'name' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("name", V);
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
        context: "Failed to set the 'useMap' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("usemap", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get form() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get form");
      return utils.tryWrapperForImpl($impl["form"]);
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
        context: "Failed to set the 'width' property on 'HTMLObjectElement': The provided value",
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
        context: "Failed to set the 'height' property on 'HTMLObjectElement': The provided value",
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

    get willValidate() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get willValidate");
      return $impl["willValidate"];
    }

    get validity() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get validity");
      return utils.tryWrapperForImpl($impl["validity"]);
    }

    get validationMessage() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get validationMessage");
      return $impl["validationMessage"];
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
        context: "Failed to set the 'align' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("align", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get archive() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get archive");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("archive");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set archive(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set archive");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'archive' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("archive", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get code() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get code");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("code");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set code(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set code");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'code' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("code", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get declare() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get declare");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("declare") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set declare(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set declare");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'declare' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("declare", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("declare");
        }
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
        context: "Failed to set the 'hspace' property on 'HTMLObjectElement': The provided value",
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

    get standby() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get standby");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("standby");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set standby(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set standby");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'standby' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("standby", V);
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
        context: "Failed to set the 'vspace' property on 'HTMLObjectElement': The provided value",
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

    get codeBase() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get codeBase");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const impl = $impl;
        const value = impl._reflectGetTheContentAttribute("codebase");
        if (value === null) {
          return "";
        }

        const document = impl._ownerDocument;
        if (this._codebaseURLCacheKey === value && this._baseURLCache === document._baseURLCache) {
          return this._codebaseURLCache;
        }

        this._codebaseURLCacheKey = value;
        this._baseURLCache = document._baseURLCache;

        const urlRecord = document.encodingParseAURL(value);
        if (urlRecord !== null) {
          this._codebaseURLCache = serializeURLwhatwg_url(urlRecord);
          return this._codebaseURLCache;
        }
        this._codebaseURLCache = conversions.USVString(value);
        return this._codebaseURLCache;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set codeBase(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set codeBase");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'codeBase' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("codebase", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get codeType() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get codeType");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("codetype");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set codeType(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set codeType");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'codeType' property on 'HTMLObjectElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("codetype", V);
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
        context: "Failed to set the 'border' property on 'HTMLObjectElement': The provided value",
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
  Object.defineProperties(HTMLObjectElement.prototype, {
    checkValidity: { enumerable: true },
    reportValidity: { enumerable: true },
    setCustomValidity: { enumerable: true },
    data: { enumerable: true },
    type: { enumerable: true },
    name: { enumerable: true },
    useMap: { enumerable: true },
    form: { enumerable: true },
    width: { enumerable: true },
    height: { enumerable: true },
    contentDocument: { enumerable: true },
    willValidate: { enumerable: true },
    validity: { enumerable: true },
    validationMessage: { enumerable: true },
    align: { enumerable: true },
    archive: { enumerable: true },
    code: { enumerable: true },
    declare: { enumerable: true },
    hspace: { enumerable: true },
    standby: { enumerable: true },
    vspace: { enumerable: true },
    codeBase: { enumerable: true },
    codeType: { enumerable: true },
    border: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLObjectElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLObjectElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLObjectElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLObjectElement-impl.js");
