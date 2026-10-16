"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const DOMRectInit = require("./DOMRectInit.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "DOMRectReadOnly";

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
  throw new globalObject.TypeError(`${context} is not of type 'DOMRectReadOnly'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["DOMRectReadOnly"].prototype;
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

const exposed = new Set(["Window", "Worker"]);

exports.install = (globalObject, globalNames) => {
  if (!globalNames.some(globalName => exposed.has(globalName))) {
    return;
  }

  const ctorRegistry = utils.initCtorRegistry(globalObject);
  class DOMRectReadOnly {
    constructor() {
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg !== undefined) {
          curArg = conversions["unrestricted double"](curArg, {
            context: "Failed to construct 'DOMRectReadOnly': parameter 1",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["unrestricted double"](curArg, {
            context: "Failed to construct 'DOMRectReadOnly': parameter 2",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[2];
        if (curArg !== undefined) {
          curArg = conversions["unrestricted double"](curArg, {
            context: "Failed to construct 'DOMRectReadOnly': parameter 3",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[3];
        if (curArg !== undefined) {
          curArg = conversions["unrestricted double"](curArg, {
            context: "Failed to construct 'DOMRectReadOnly': parameter 4",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      return exports.setup(Object.create(new.target.prototype), globalObject, args);
    }

    toJSON() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "toJSON");
      return $impl.toJSON();
    }

    get x() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get x");
      return $impl["x"];
    }

    get y() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get y");
      return $impl["y"];
    }

    get width() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get width");
      return $impl["width"];
    }

    get height() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get height");
      return $impl["height"];
    }

    get top() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get top");
      return $impl["top"];
    }

    get right() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get right");
      return $impl["right"];
    }

    get bottom() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get bottom");
      return $impl["bottom"];
    }

    get left() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get left");
      return $impl["left"];
    }

    static fromRect() {
      const args = [];
      {
        let curArg = arguments[0];
        curArg = DOMRectInit.convert(globalObject, curArg, {
          context: "Failed to execute 'fromRect' on 'DOMRectReadOnly': parameter 1"
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl(Impl.implementation.fromRect(globalObject, ...args));
    }
  }
  Object.defineProperties(DOMRectReadOnly.prototype, {
    toJSON: { enumerable: true },
    x: { enumerable: true },
    y: { enumerable: true },
    width: { enumerable: true },
    height: { enumerable: true },
    top: { enumerable: true },
    right: { enumerable: true },
    bottom: { enumerable: true },
    left: { enumerable: true },
    [Symbol.toStringTag]: { value: "DOMRectReadOnly", configurable: true }
  });
  Object.defineProperties(DOMRectReadOnly, { fromRect: { enumerable: true } });
  ctorRegistry[interfaceName] = DOMRectReadOnly;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: DOMRectReadOnly
  });
};

const Impl = require("../../jsdom/living/geometry/DOMRectReadOnly-impl.js");
