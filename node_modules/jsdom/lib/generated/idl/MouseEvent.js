"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const MouseEventInit = require("./MouseEventInit.js");
const EventTarget = require("./EventTarget.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const UIEvent = require("./UIEvent.js");

const interfaceName = "MouseEvent";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => UIEvent.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'MouseEvent'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["MouseEvent"].prototype;
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
  UIEvent._internalSetup(wrapper, globalObject);
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
  class MouseEvent extends globalObject.UIEvent {
    constructor(type) {
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to construct 'MouseEvent': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to construct 'MouseEvent': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = MouseEventInit.convert(globalObject, curArg, {
          context: "Failed to construct 'MouseEvent': parameter 2"
        });
        args.push(curArg);
      }
      return exports.setup(Object.create(new.target.prototype), globalObject, args);
    }

    getModifierState(keyArg) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getModifierState");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getModifierState' on 'MouseEvent': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getModifierState' on 'MouseEvent': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.getModifierState(...args);
    }

    initMouseEvent(typeArg) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "initMouseEvent");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'initMouseEvent' on 'MouseEvent': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 2",
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
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 3",
            globals: globalObject
          });
        } else {
          curArg = false;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[3];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = null;
          } else {
            curArg = utils.tryImplForWrapper(curArg);
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[4];
        if (curArg !== undefined) {
          curArg = conversions["long"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 5",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[5];
        if (curArg !== undefined) {
          curArg = conversions["long"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 6",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[6];
        if (curArg !== undefined) {
          curArg = conversions["long"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 7",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[7];
        if (curArg !== undefined) {
          curArg = conversions["long"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 8",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[8];
        if (curArg !== undefined) {
          curArg = conversions["long"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 9",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[9];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 10",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[10];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 11",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[11];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 12",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[12];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 13",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[13];
        if (curArg !== undefined) {
          curArg = conversions["short"](curArg, {
            context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 14",
            globals: globalObject
          });
        } else {
          curArg = 0;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[14];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = null;
          } else {
            curArg = EventTarget.convert(globalObject, curArg, {
              context: "Failed to execute 'initMouseEvent' on 'MouseEvent': parameter 15"
            });
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      return $impl.initMouseEvent(...args);
    }

    get screenX() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get screenX");
      return $impl["screenX"];
    }

    get screenY() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get screenY");
      return $impl["screenY"];
    }

    get clientX() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get clientX");
      return $impl["clientX"];
    }

    get clientY() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get clientY");
      return $impl["clientY"];
    }

    get ctrlKey() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ctrlKey");
      return $impl["ctrlKey"];
    }

    get shiftKey() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get shiftKey");
      return $impl["shiftKey"];
    }

    get altKey() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get altKey");
      return $impl["altKey"];
    }

    get metaKey() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get metaKey");
      return $impl["metaKey"];
    }

    get button() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get button");
      return $impl["button"];
    }

    get buttons() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get buttons");
      return $impl["buttons"];
    }

    get relatedTarget() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get relatedTarget");
      return utils.tryWrapperForImpl($impl["relatedTarget"]);
    }

    get pageX() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get pageX");
      return $impl["pageX"];
    }

    get pageY() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get pageY");
      return $impl["pageY"];
    }

    get x() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get x");
      return $impl["x"];
    }

    get y() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get y");
      return $impl["y"];
    }

    get offsetX() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get offsetX");
      return $impl["offsetX"];
    }

    get offsetY() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get offsetY");
      return $impl["offsetY"];
    }

    get movementX() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get movementX");
      return $impl["movementX"];
    }

    get movementY() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get movementY");
      return $impl["movementY"];
    }
  }
  Object.defineProperties(MouseEvent.prototype, {
    getModifierState: { enumerable: true },
    initMouseEvent: { enumerable: true },
    screenX: { enumerable: true },
    screenY: { enumerable: true },
    clientX: { enumerable: true },
    clientY: { enumerable: true },
    ctrlKey: { enumerable: true },
    shiftKey: { enumerable: true },
    altKey: { enumerable: true },
    metaKey: { enumerable: true },
    button: { enumerable: true },
    buttons: { enumerable: true },
    relatedTarget: { enumerable: true },
    pageX: { enumerable: true },
    pageY: { enumerable: true },
    x: { enumerable: true },
    y: { enumerable: true },
    offsetX: { enumerable: true },
    offsetY: { enumerable: true },
    movementX: { enumerable: true },
    movementY: { enumerable: true },
    [Symbol.toStringTag]: { value: "MouseEvent", configurable: true }
  });
  ctorRegistry[interfaceName] = MouseEvent;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: MouseEvent
  });
};

const Impl = require("../../jsdom/living/events/MouseEvent-impl.js");
