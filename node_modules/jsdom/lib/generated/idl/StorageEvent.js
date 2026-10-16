"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const StorageEventInit = require("./StorageEventInit.js");
const Storage = require("./Storage.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const Event = require("./Event.js");

const interfaceName = "StorageEvent";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => Event.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'StorageEvent'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["StorageEvent"].prototype;
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
  Event._internalSetup(wrapper, globalObject);
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
  class StorageEvent extends globalObject.Event {
    constructor(type) {
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to construct 'StorageEvent': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to construct 'StorageEvent': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = StorageEventInit.convert(globalObject, curArg, {
          context: "Failed to construct 'StorageEvent': parameter 2"
        });
        args.push(curArg);
      }
      return exports.setup(Object.create(new.target.prototype), globalObject, args);
    }

    initStorageEvent(type) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "initStorageEvent");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'initStorageEvent' on 'StorageEvent': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'initStorageEvent' on 'StorageEvent': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'initStorageEvent' on 'StorageEvent': parameter 2",
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
            context: "Failed to execute 'initStorageEvent' on 'StorageEvent': parameter 3",
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
            curArg = conversions["DOMString"](curArg, {
              context: "Failed to execute 'initStorageEvent' on 'StorageEvent': parameter 4",
              globals: globalObject
            });
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[4];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = null;
          } else {
            curArg = conversions["DOMString"](curArg, {
              context: "Failed to execute 'initStorageEvent' on 'StorageEvent': parameter 5",
              globals: globalObject
            });
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[5];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = null;
          } else {
            curArg = conversions["DOMString"](curArg, {
              context: "Failed to execute 'initStorageEvent' on 'StorageEvent': parameter 6",
              globals: globalObject
            });
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[6];
        if (curArg !== undefined) {
          curArg = conversions["USVString"](curArg, {
            context: "Failed to execute 'initStorageEvent' on 'StorageEvent': parameter 7",
            globals: globalObject
          });
        } else {
          curArg = "";
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[7];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = null;
          } else {
            curArg = Storage.convert(globalObject, curArg, {
              context: "Failed to execute 'initStorageEvent' on 'StorageEvent': parameter 8"
            });
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      return $impl.initStorageEvent(...args);
    }

    get key() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get key");
      return $impl["key"];
    }

    get oldValue() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oldValue");
      return $impl["oldValue"];
    }

    get newValue() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get newValue");
      return $impl["newValue"];
    }

    get url() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get url");
      return $impl["url"];
    }

    get storageArea() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get storageArea");
      return utils.tryWrapperForImpl($impl["storageArea"]);
    }
  }
  Object.defineProperties(StorageEvent.prototype, {
    initStorageEvent: { enumerable: true },
    key: { enumerable: true },
    oldValue: { enumerable: true },
    newValue: { enumerable: true },
    url: { enumerable: true },
    storageArea: { enumerable: true },
    [Symbol.toStringTag]: { value: "StorageEvent", configurable: true }
  });
  ctorRegistry[interfaceName] = StorageEvent;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: StorageEvent
  });
};

const Impl = require("../../jsdom/living/events/StorageEvent-impl.js");
