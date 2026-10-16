"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const EventInit = require("./EventInit.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "Event";

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
  throw new globalObject.TypeError(`${context} is not of type 'Event'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["Event"].prototype;
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

function getUnforgeables(globalObject) {
  let unforgeables = unforgeablesMap.get(globalObject);
  if (unforgeables === undefined) {
    unforgeables = Object.create(null);
    utils.define(unforgeables, {
      get isTrusted() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get isTrusted");
        return $impl["isTrusted"];
      }
    });
    Object.defineProperties(unforgeables, {
      isTrusted: { configurable: false }
    });
    unforgeablesMap.set(globalObject, unforgeables);
  }
  return unforgeables;
}

exports._internalSetup = (wrapper, globalObject) => {
  utils.define(wrapper, getUnforgeables(globalObject));
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

const unforgeablesMap = new WeakMap();
const exposed = new Set(["Window", "Worker", "AudioWorklet"]);

exports.install = (globalObject, globalNames) => {
  if (!globalNames.some(globalName => exposed.has(globalName))) {
    return;
  }

  const ctorRegistry = utils.initCtorRegistry(globalObject);
  class Event {
    constructor(type) {
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to construct 'Event': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to construct 'Event': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = EventInit.convert(globalObject, curArg, { context: "Failed to construct 'Event': parameter 2" });
        args.push(curArg);
      }
      return exports.setup(Object.create(new.target.prototype), globalObject, args);
    }

    composedPath() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "composedPath");
      return utils.tryWrapperForImpl($impl.composedPath());
    }

    stopPropagation() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "stopPropagation");
      return $impl.stopPropagation();
    }

    stopImmediatePropagation() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "stopImmediatePropagation");
      return $impl.stopImmediatePropagation();
    }

    preventDefault() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "preventDefault");
      return $impl.preventDefault();
    }

    initEvent(type) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "initEvent");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'initEvent' on 'Event': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'initEvent' on 'Event': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'initEvent' on 'Event': parameter 2",
            globals: globalObject
          });
        } else {
          curArg = false;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[2];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'initEvent' on 'Event': parameter 3",
            globals: globalObject
          });
        } else {
          curArg = false;
        }
        args.push(curArg);
      }
      return $impl.initEvent(...args);
    }

    get type() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get type");
      return $impl["type"];
    }

    get target() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get target");
      return utils.tryWrapperForImpl($impl["target"]);
    }

    get srcElement() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get srcElement");
      return utils.tryWrapperForImpl($impl["srcElement"]);
    }

    get currentTarget() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get currentTarget");
      return utils.tryWrapperForImpl($impl["currentTarget"]);
    }

    get eventPhase() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get eventPhase");
      return $impl["eventPhase"];
    }

    get cancelBubble() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get cancelBubble");
      return $impl["cancelBubble"];
    }

    set cancelBubble(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set cancelBubble");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'cancelBubble' property on 'Event': The provided value",
        globals: globalObject
      });

      $impl["cancelBubble"] = V;
    }

    get bubbles() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get bubbles");
      return $impl["bubbles"];
    }

    get cancelable() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get cancelable");
      return $impl["cancelable"];
    }

    get returnValue() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get returnValue");
      return $impl["returnValue"];
    }

    set returnValue(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set returnValue");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'returnValue' property on 'Event': The provided value",
        globals: globalObject
      });

      $impl["returnValue"] = V;
    }

    get defaultPrevented() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get defaultPrevented");
      return $impl["defaultPrevented"];
    }

    get composed() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get composed");
      return $impl["composed"];
    }

    get timeStamp() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get timeStamp");
      return $impl["timeStamp"];
    }
  }
  Object.defineProperties(Event.prototype, {
    composedPath: { enumerable: true },
    stopPropagation: { enumerable: true },
    stopImmediatePropagation: { enumerable: true },
    preventDefault: { enumerable: true },
    initEvent: { enumerable: true },
    type: { enumerable: true },
    target: { enumerable: true },
    srcElement: { enumerable: true },
    currentTarget: { enumerable: true },
    eventPhase: { enumerable: true },
    cancelBubble: { enumerable: true },
    bubbles: { enumerable: true },
    cancelable: { enumerable: true },
    returnValue: { enumerable: true },
    defaultPrevented: { enumerable: true },
    composed: { enumerable: true },
    timeStamp: { enumerable: true },
    [Symbol.toStringTag]: { value: "Event", configurable: true },
    NONE: { value: 0, enumerable: true },
    CAPTURING_PHASE: { value: 1, enumerable: true },
    AT_TARGET: { value: 2, enumerable: true },
    BUBBLING_PHASE: { value: 3, enumerable: true }
  });
  Object.defineProperties(Event, {
    NONE: { value: 0, enumerable: true },
    CAPTURING_PHASE: { value: 1, enumerable: true },
    AT_TARGET: { value: 2, enumerable: true },
    BUBBLING_PHASE: { value: 3, enumerable: true }
  });
  ctorRegistry[interfaceName] = Event;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: Event
  });
};

const Impl = require("../../jsdom/living/events/Event-impl.js");
