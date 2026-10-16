"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const HTMLConstructor_jsdom_living_helpers_html_constructor =
  require("../../jsdom/living/helpers/html-constructor.js").HTMLConstructor;
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLAreaElement";

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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLAreaElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLAreaElement"].prototype;
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
  class HTMLAreaElement extends globalObject.HTMLElement {
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
        context: "Failed to set the 'alt' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("alt", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get coords() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get coords");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("coords");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set coords(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set coords");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'coords' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("coords", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get shape() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get shape");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("shape");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set shape(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set shape");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'shape' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("shape", V);
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
        context: "Failed to set the 'target' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("target", V);
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
        context: "Failed to set the 'rel' property on 'HTMLAreaElement': The provided value",
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

    get noHref() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get noHref");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("nohref") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set noHref(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set noHref");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'noHref' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("nohref", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("nohref");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get href() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get href");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["href"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set href(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set href");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'href' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["href"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    toString() {
      const $impl = $requireImpl(this, globalObject, "toString");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["href"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get origin() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get origin");
      return $impl["origin"];
    }

    get protocol() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get protocol");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["protocol"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set protocol(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set protocol");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'protocol' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["protocol"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get username() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get username");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["username"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set username(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set username");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'username' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["username"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get password() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get password");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["password"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set password(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set password");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'password' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["password"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get host() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get host");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["host"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set host(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set host");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'host' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["host"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get hostname() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get hostname");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["hostname"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set hostname(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set hostname");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'hostname' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["hostname"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get port() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get port");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["port"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set port(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set port");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'port' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["port"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get pathname() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get pathname");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["pathname"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set pathname(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set pathname");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'pathname' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["pathname"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get search() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get search");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["search"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set search(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set search");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'search' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["search"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get hash() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get hash");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["hash"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set hash(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set hash");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'hash' property on 'HTMLAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["hash"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }
  }
  Object.defineProperties(HTMLAreaElement.prototype, {
    alt: { enumerable: true },
    coords: { enumerable: true },
    shape: { enumerable: true },
    target: { enumerable: true },
    rel: { enumerable: true },
    relList: { enumerable: true },
    noHref: { enumerable: true },
    href: { enumerable: true },
    toString: { enumerable: true },
    origin: { enumerable: true },
    protocol: { enumerable: true },
    username: { enumerable: true },
    password: { enumerable: true },
    host: { enumerable: true },
    hostname: { enumerable: true },
    port: { enumerable: true },
    pathname: { enumerable: true },
    search: { enumerable: true },
    hash: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLAreaElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLAreaElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLAreaElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLAreaElement-impl.js");
