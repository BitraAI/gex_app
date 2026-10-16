"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const Node = require("./Node.js");

const interfaceName = "Attr";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => Node.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'Attr'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["Attr"].prototype;
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
  Node._internalSetup(wrapper, globalObject);
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
  class Attr extends globalObject.Node {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }

    get namespaceURI() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get namespaceURI");
      return $impl["namespaceURI"];
    }

    get prefix() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get prefix");
      return $impl["prefix"];
    }

    get localName() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get localName");
      return $impl["localName"];
    }

    get name() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get name");
      return $impl["name"];
    }

    get value() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get value");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["value"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set value(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set value");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'value' property on 'Attr': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["value"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ownerElement() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ownerElement");
      return utils.tryWrapperForImpl($impl["ownerElement"]);
    }

    get specified() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get specified");
      return $impl["specified"];
    }
  }
  Object.defineProperties(Attr.prototype, {
    namespaceURI: { enumerable: true },
    prefix: { enumerable: true },
    localName: { enumerable: true },
    name: { enumerable: true },
    value: { enumerable: true },
    ownerElement: { enumerable: true },
    specified: { enumerable: true },
    [Symbol.toStringTag]: { value: "Attr", configurable: true }
  });
  ctorRegistry[interfaceName] = Attr;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: Attr
  });
};

const Impl = require("../../jsdom/living/attributes/Attr-impl.js");
