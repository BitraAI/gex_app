"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "SVGRect";

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
  throw new globalObject.TypeError(`${context} is not of type 'SVGRect'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["SVGRect"].prototype;
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
  class SVGRect {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }

    get x() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get x");
      return $impl["x"];
    }

    set x(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set x");

      V = conversions["float"](V, {
        context: "Failed to set the 'x' property on 'SVGRect': The provided value",
        globals: globalObject
      });

      $impl["x"] = V;
    }

    get y() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get y");
      return $impl["y"];
    }

    set y(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set y");

      V = conversions["float"](V, {
        context: "Failed to set the 'y' property on 'SVGRect': The provided value",
        globals: globalObject
      });

      $impl["y"] = V;
    }

    get width() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get width");
      return $impl["width"];
    }

    set width(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set width");

      V = conversions["float"](V, {
        context: "Failed to set the 'width' property on 'SVGRect': The provided value",
        globals: globalObject
      });

      $impl["width"] = V;
    }

    get height() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get height");
      return $impl["height"];
    }

    set height(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set height");

      V = conversions["float"](V, {
        context: "Failed to set the 'height' property on 'SVGRect': The provided value",
        globals: globalObject
      });

      $impl["height"] = V;
    }
  }
  Object.defineProperties(SVGRect.prototype, {
    x: { enumerable: true },
    y: { enumerable: true },
    width: { enumerable: true },
    height: { enumerable: true },
    [Symbol.toStringTag]: { value: "SVGRect", configurable: true }
  });
  ctorRegistry[interfaceName] = SVGRect;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: SVGRect
  });
};

const Impl = require("../../jsdom/living/svg/SVGRect-impl.js");
