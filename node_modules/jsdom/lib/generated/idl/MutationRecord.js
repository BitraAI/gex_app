"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "MutationRecord";

const $interfaceDescriptor = utils.createInterfaceDescriptor();
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
  throw new globalObject.TypeError(`${context} is not of type 'MutationRecord'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["MutationRecord"].prototype;
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

exports._internalSetup = (wrapper, globalObject) => {};

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
  class MutationRecord {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }

    get type() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get type");
      return $impl["type"];
    }

    get target() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get target");
      return utils.getSameObject(this, "target", () => {
        return utils.tryWrapperForImpl($impl["target"]);
      });
    }

    get addedNodes() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get addedNodes");
      return utils.getSameObject(this, "addedNodes", () => {
        return utils.tryWrapperForImpl($impl["addedNodes"]);
      });
    }

    get removedNodes() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get removedNodes");
      return utils.getSameObject(this, "removedNodes", () => {
        return utils.tryWrapperForImpl($impl["removedNodes"]);
      });
    }

    get previousSibling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get previousSibling");
      return utils.tryWrapperForImpl($impl["previousSibling"]);
    }

    get nextSibling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get nextSibling");
      return utils.tryWrapperForImpl($impl["nextSibling"]);
    }

    get attributeName() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get attributeName");
      return $impl["attributeName"];
    }

    get attributeNamespace() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get attributeNamespace");
      return $impl["attributeNamespace"];
    }

    get oldValue() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oldValue");
      return $impl["oldValue"];
    }
  }
  Object.defineProperties(MutationRecord.prototype, {
    type: { enumerable: true },
    target: { enumerable: true },
    addedNodes: { enumerable: true },
    removedNodes: { enumerable: true },
    previousSibling: { enumerable: true },
    nextSibling: { enumerable: true },
    attributeName: { enumerable: true },
    attributeNamespace: { enumerable: true },
    oldValue: { enumerable: true },
    [Symbol.toStringTag]: { value: "MutationRecord", configurable: true }
  });
  ctorRegistry[interfaceName] = MutationRecord;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: MutationRecord
  });
};

const Impl = require("../../jsdom/living/mutation-observer/MutationRecord-impl.js");
