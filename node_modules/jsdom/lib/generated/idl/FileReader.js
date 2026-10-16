"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const Blob = require("./Blob.js");
const EventHandlerNonNull = require("./EventHandlerNonNull.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const EventTarget = require("./EventTarget.js");

const interfaceName = "FileReader";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => EventTarget.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'FileReader'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["FileReader"].prototype;
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
  EventTarget._internalSetup(wrapper, globalObject);
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

const exposed = new Set(["Window", "Worker"]);

exports.install = (globalObject, globalNames) => {
  if (!globalNames.some(globalName => exposed.has(globalName))) {
    return;
  }

  const ctorRegistry = utils.initCtorRegistry(globalObject);
  class FileReader extends globalObject.EventTarget {
    constructor() {
      return exports.setup(Object.create(new.target.prototype), globalObject, undefined);
    }

    readAsArrayBuffer(blob) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "readAsArrayBuffer");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'readAsArrayBuffer' on 'FileReader': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Blob.convert(globalObject, curArg, {
          context: "Failed to execute 'readAsArrayBuffer' on 'FileReader': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.readAsArrayBuffer(...args);
    }

    readAsBinaryString(blob) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "readAsBinaryString");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'readAsBinaryString' on 'FileReader': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Blob.convert(globalObject, curArg, {
          context: "Failed to execute 'readAsBinaryString' on 'FileReader': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.readAsBinaryString(...args);
    }

    readAsText(blob) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "readAsText");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'readAsText' on 'FileReader': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Blob.convert(globalObject, curArg, {
          context: "Failed to execute 'readAsText' on 'FileReader': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'readAsText' on 'FileReader': parameter 2",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      return $impl.readAsText(...args);
    }

    readAsDataURL(blob) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "readAsDataURL");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'readAsDataURL' on 'FileReader': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Blob.convert(globalObject, curArg, {
          context: "Failed to execute 'readAsDataURL' on 'FileReader': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.readAsDataURL(...args);
    }

    abort() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "abort");
      return $impl.abort();
    }

    get readyState() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get readyState");
      return $impl["readyState"];
    }

    get result() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get result");
      return utils.tryWrapperForImpl($impl["result"]);
    }

    get error() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get error");
      return utils.tryWrapperForImpl($impl["error"]);
    }

    get onloadstart() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onloadstart");
      return utils.tryWrapperForImpl($impl["onloadstart"]);
    }

    set onloadstart(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onloadstart");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onloadstart' property on 'FileReader': The provided value"
        });
      }
      $impl["onloadstart"] = V;
    }

    get onprogress() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onprogress");
      return utils.tryWrapperForImpl($impl["onprogress"]);
    }

    set onprogress(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onprogress");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onprogress' property on 'FileReader': The provided value"
        });
      }
      $impl["onprogress"] = V;
    }

    get onload() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onload");
      return utils.tryWrapperForImpl($impl["onload"]);
    }

    set onload(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onload");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onload' property on 'FileReader': The provided value"
        });
      }
      $impl["onload"] = V;
    }

    get onabort() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onabort");
      return utils.tryWrapperForImpl($impl["onabort"]);
    }

    set onabort(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onabort");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onabort' property on 'FileReader': The provided value"
        });
      }
      $impl["onabort"] = V;
    }

    get onerror() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onerror");
      return utils.tryWrapperForImpl($impl["onerror"]);
    }

    set onerror(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onerror");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onerror' property on 'FileReader': The provided value"
        });
      }
      $impl["onerror"] = V;
    }

    get onloadend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onloadend");
      return utils.tryWrapperForImpl($impl["onloadend"]);
    }

    set onloadend(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onloadend");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onloadend' property on 'FileReader': The provided value"
        });
      }
      $impl["onloadend"] = V;
    }
  }
  Object.defineProperties(FileReader.prototype, {
    readAsArrayBuffer: { enumerable: true },
    readAsBinaryString: { enumerable: true },
    readAsText: { enumerable: true },
    readAsDataURL: { enumerable: true },
    abort: { enumerable: true },
    readyState: { enumerable: true },
    result: { enumerable: true },
    error: { enumerable: true },
    onloadstart: { enumerable: true },
    onprogress: { enumerable: true },
    onload: { enumerable: true },
    onabort: { enumerable: true },
    onerror: { enumerable: true },
    onloadend: { enumerable: true },
    [Symbol.toStringTag]: { value: "FileReader", configurable: true },
    EMPTY: { value: 0, enumerable: true },
    LOADING: { value: 1, enumerable: true },
    DONE: { value: 2, enumerable: true }
  });
  Object.defineProperties(FileReader, {
    EMPTY: { value: 0, enumerable: true },
    LOADING: { value: 1, enumerable: true },
    DONE: { value: 2, enumerable: true }
  });
  ctorRegistry[interfaceName] = FileReader;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: FileReader
  });
};

const Impl = require("../../jsdom/living/file-api/FileReader-impl.js");
