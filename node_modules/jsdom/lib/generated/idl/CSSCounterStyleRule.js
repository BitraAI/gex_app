"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const CSSRule = require("./CSSRule.js");

const interfaceName = "CSSCounterStyleRule";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => CSSRule.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'CSSCounterStyleRule'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["CSSCounterStyleRule"].prototype;
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
  CSSRule._internalSetup(wrapper, globalObject);
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
  class CSSCounterStyleRule extends globalObject.CSSRule {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }

    get name() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get name");
      return utils.tryWrapperForImpl($impl["name"]);
    }

    set name(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set name");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'name' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["name"] = V;
    }

    get system() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get system");
      return utils.tryWrapperForImpl($impl["system"]);
    }

    set system(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set system");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'system' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["system"] = V;
    }

    get symbols() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get symbols");
      return utils.tryWrapperForImpl($impl["symbols"]);
    }

    set symbols(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set symbols");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'symbols' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["symbols"] = V;
    }

    get additiveSymbols() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get additiveSymbols");
      return utils.tryWrapperForImpl($impl["additiveSymbols"]);
    }

    set additiveSymbols(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set additiveSymbols");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'additiveSymbols' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["additiveSymbols"] = V;
    }

    get negative() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get negative");
      return utils.tryWrapperForImpl($impl["negative"]);
    }

    set negative(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set negative");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'negative' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["negative"] = V;
    }

    get prefix() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get prefix");
      return utils.tryWrapperForImpl($impl["prefix"]);
    }

    set prefix(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set prefix");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'prefix' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["prefix"] = V;
    }

    get suffix() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get suffix");
      return utils.tryWrapperForImpl($impl["suffix"]);
    }

    set suffix(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set suffix");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'suffix' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["suffix"] = V;
    }

    get range() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get range");
      return utils.tryWrapperForImpl($impl["range"]);
    }

    set range(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set range");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'range' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["range"] = V;
    }

    get pad() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get pad");
      return utils.tryWrapperForImpl($impl["pad"]);
    }

    set pad(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set pad");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'pad' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["pad"] = V;
    }

    get speakAs() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get speakAs");
      return utils.tryWrapperForImpl($impl["speakAs"]);
    }

    set speakAs(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set speakAs");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'speakAs' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["speakAs"] = V;
    }

    get fallback() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get fallback");
      return utils.tryWrapperForImpl($impl["fallback"]);
    }

    set fallback(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set fallback");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'fallback' property on 'CSSCounterStyleRule': The provided value",
        globals: globalObject
      });

      $impl["fallback"] = V;
    }
  }
  Object.defineProperties(CSSCounterStyleRule.prototype, {
    name: { enumerable: true },
    system: { enumerable: true },
    symbols: { enumerable: true },
    additiveSymbols: { enumerable: true },
    negative: { enumerable: true },
    prefix: { enumerable: true },
    suffix: { enumerable: true },
    range: { enumerable: true },
    pad: { enumerable: true },
    speakAs: { enumerable: true },
    fallback: { enumerable: true },
    [Symbol.toStringTag]: { value: "CSSCounterStyleRule", configurable: true }
  });
  ctorRegistry[interfaceName] = CSSCounterStyleRule;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: CSSCounterStyleRule
  });
};

const Impl = require("../../jsdom/living/css/CSSCounterStyleRule-impl.js");
