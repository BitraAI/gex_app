"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const PointerEventInit = require("./PointerEventInit.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const MouseEvent = require("./MouseEvent.js");

const interfaceName = "PointerEvent";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => MouseEvent.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'PointerEvent'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["PointerEvent"].prototype;
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
  MouseEvent._internalSetup(wrapper, globalObject);
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
  class PointerEvent extends globalObject.MouseEvent {
    constructor(type) {
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to construct 'PointerEvent': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to construct 'PointerEvent': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = PointerEventInit.convert(globalObject, curArg, {
          context: "Failed to construct 'PointerEvent': parameter 2"
        });
        args.push(curArg);
      }
      return exports.setup(Object.create(new.target.prototype), globalObject, args);
    }

    getCoalescedEvents() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getCoalescedEvents");
      return utils.tryWrapperForImpl($impl.getCoalescedEvents());
    }

    getPredictedEvents() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getPredictedEvents");
      return utils.tryWrapperForImpl($impl.getPredictedEvents());
    }

    get pointerId() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get pointerId");
      return $impl["pointerId"];
    }

    get width() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get width");
      return $impl["width"];
    }

    get height() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get height");
      return $impl["height"];
    }

    get pressure() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get pressure");
      return $impl["pressure"];
    }

    get tangentialPressure() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get tangentialPressure");
      return $impl["tangentialPressure"];
    }

    get tiltX() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get tiltX");
      return $impl["tiltX"];
    }

    get tiltY() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get tiltY");
      return $impl["tiltY"];
    }

    get twist() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get twist");
      return $impl["twist"];
    }

    get altitudeAngle() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get altitudeAngle");
      return $impl["altitudeAngle"];
    }

    get azimuthAngle() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get azimuthAngle");
      return $impl["azimuthAngle"];
    }

    get pointerType() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get pointerType");
      return $impl["pointerType"];
    }

    get isPrimary() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get isPrimary");
      return $impl["isPrimary"];
    }

    get persistentDeviceId() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get persistentDeviceId");
      return $impl["persistentDeviceId"];
    }
  }
  Object.defineProperties(PointerEvent.prototype, {
    getCoalescedEvents: { enumerable: true },
    getPredictedEvents: { enumerable: true },
    pointerId: { enumerable: true },
    width: { enumerable: true },
    height: { enumerable: true },
    pressure: { enumerable: true },
    tangentialPressure: { enumerable: true },
    tiltX: { enumerable: true },
    tiltY: { enumerable: true },
    twist: { enumerable: true },
    altitudeAngle: { enumerable: true },
    azimuthAngle: { enumerable: true },
    pointerType: { enumerable: true },
    isPrimary: { enumerable: true },
    persistentDeviceId: { enumerable: true },
    [Symbol.toStringTag]: { value: "PointerEvent", configurable: true }
  });
  ctorRegistry[interfaceName] = PointerEvent;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: PointerEvent
  });
};

const Impl = require("../../jsdom/living/events/PointerEvent-impl.js");
