"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const HTMLConstructor_jsdom_living_helpers_html_constructor =
  require("../../jsdom/living/helpers/html-constructor.js").HTMLConstructor;
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const EventHandlerNonNull = require("./EventHandlerNonNull.js");
const OnBeforeUnloadEventHandlerNonNull = require("./OnBeforeUnloadEventHandlerNonNull.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLBodyElement";

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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLBodyElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLBodyElement"].prototype;
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
  class HTMLBodyElement extends globalObject.HTMLElement {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    get text() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get text");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("text");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set text(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set text");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'text' property on 'HTMLBodyElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("text", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get link() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get link");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("link");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set link(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set link");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'link' property on 'HTMLBodyElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("link", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get vLink() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get vLink");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("vlink");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set vLink(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set vLink");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'vLink' property on 'HTMLBodyElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("vlink", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get aLink() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get aLink");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("alink");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set aLink(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set aLink");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'aLink' property on 'HTMLBodyElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("alink", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get bgColor() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get bgColor");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("bgcolor");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set bgColor(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set bgColor");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'bgColor' property on 'HTMLBodyElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("bgcolor", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get background() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get background");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("background");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set background(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set background");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'background' property on 'HTMLBodyElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("background", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get onafterprint() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onafterprint");
      return utils.tryWrapperForImpl($impl["onafterprint"]);
    }

    set onafterprint(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onafterprint");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onafterprint' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onafterprint"] = V;
    }

    get onbeforeprint() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onbeforeprint");
      return utils.tryWrapperForImpl($impl["onbeforeprint"]);
    }

    set onbeforeprint(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onbeforeprint");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onbeforeprint' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onbeforeprint"] = V;
    }

    get onbeforeunload() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onbeforeunload");
      return utils.tryWrapperForImpl($impl["onbeforeunload"]);
    }

    set onbeforeunload(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onbeforeunload");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = OnBeforeUnloadEventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onbeforeunload' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onbeforeunload"] = V;
    }

    get onhashchange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onhashchange");
      return utils.tryWrapperForImpl($impl["onhashchange"]);
    }

    set onhashchange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onhashchange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onhashchange' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onhashchange"] = V;
    }

    get onlanguagechange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onlanguagechange");
      return utils.tryWrapperForImpl($impl["onlanguagechange"]);
    }

    set onlanguagechange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onlanguagechange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onlanguagechange' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onlanguagechange"] = V;
    }

    get onmessage() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onmessage");
      return utils.tryWrapperForImpl($impl["onmessage"]);
    }

    set onmessage(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onmessage");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmessage' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onmessage"] = V;
    }

    get onmessageerror() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onmessageerror");
      return utils.tryWrapperForImpl($impl["onmessageerror"]);
    }

    set onmessageerror(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onmessageerror");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmessageerror' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onmessageerror"] = V;
    }

    get onoffline() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onoffline");
      return utils.tryWrapperForImpl($impl["onoffline"]);
    }

    set onoffline(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onoffline");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onoffline' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onoffline"] = V;
    }

    get ononline() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ononline");
      return utils.tryWrapperForImpl($impl["ononline"]);
    }

    set ononline(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ononline");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ononline' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["ononline"] = V;
    }

    get onpagehide() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpagehide");
      return utils.tryWrapperForImpl($impl["onpagehide"]);
    }

    set onpagehide(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpagehide");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpagehide' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onpagehide"] = V;
    }

    get onpageshow() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpageshow");
      return utils.tryWrapperForImpl($impl["onpageshow"]);
    }

    set onpageshow(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpageshow");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpageshow' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onpageshow"] = V;
    }

    get onpopstate() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpopstate");
      return utils.tryWrapperForImpl($impl["onpopstate"]);
    }

    set onpopstate(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpopstate");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpopstate' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onpopstate"] = V;
    }

    get onrejectionhandled() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onrejectionhandled");
      return utils.tryWrapperForImpl($impl["onrejectionhandled"]);
    }

    set onrejectionhandled(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onrejectionhandled");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onrejectionhandled' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onrejectionhandled"] = V;
    }

    get onstorage() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onstorage");
      return utils.tryWrapperForImpl($impl["onstorage"]);
    }

    set onstorage(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onstorage");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onstorage' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onstorage"] = V;
    }

    get onunhandledrejection() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onunhandledrejection");
      return utils.tryWrapperForImpl($impl["onunhandledrejection"]);
    }

    set onunhandledrejection(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onunhandledrejection");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onunhandledrejection' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onunhandledrejection"] = V;
    }

    get onunload() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onunload");
      return utils.tryWrapperForImpl($impl["onunload"]);
    }

    set onunload(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onunload");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onunload' property on 'HTMLBodyElement': The provided value"
        });
      }
      $impl["onunload"] = V;
    }
  }
  Object.defineProperties(HTMLBodyElement.prototype, {
    text: { enumerable: true },
    link: { enumerable: true },
    vLink: { enumerable: true },
    aLink: { enumerable: true },
    bgColor: { enumerable: true },
    background: { enumerable: true },
    onafterprint: { enumerable: true },
    onbeforeprint: { enumerable: true },
    onbeforeunload: { enumerable: true },
    onhashchange: { enumerable: true },
    onlanguagechange: { enumerable: true },
    onmessage: { enumerable: true },
    onmessageerror: { enumerable: true },
    onoffline: { enumerable: true },
    ononline: { enumerable: true },
    onpagehide: { enumerable: true },
    onpageshow: { enumerable: true },
    onpopstate: { enumerable: true },
    onrejectionhandled: { enumerable: true },
    onstorage: { enumerable: true },
    onunhandledrejection: { enumerable: true },
    onunload: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLBodyElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLBodyElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLBodyElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLBodyElement-impl.js");
