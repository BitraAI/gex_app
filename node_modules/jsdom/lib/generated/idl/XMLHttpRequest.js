"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const Document = require("./Document.js");
const Blob = require("./Blob.js");
const FormData = require("./FormData.js");
const EventHandlerNonNull = require("./EventHandlerNonNull.js");
const XMLHttpRequestResponseType = require("./XMLHttpRequestResponseType.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const XMLHttpRequestEventTarget = require("./XMLHttpRequestEventTarget.js");

const interfaceName = "XMLHttpRequest";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => XMLHttpRequestEventTarget.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'XMLHttpRequest'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["XMLHttpRequest"].prototype;
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
  XMLHttpRequestEventTarget._internalSetup(wrapper, globalObject);
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

const exposed = new Set(["Window", "DedicatedWorker", "SharedWorker"]);

exports.install = (globalObject, globalNames) => {
  if (!globalNames.some(globalName => exposed.has(globalName))) {
    return;
  }

  const ctorRegistry = utils.initCtorRegistry(globalObject);
  class XMLHttpRequest extends globalObject.XMLHttpRequestEventTarget {
    constructor() {
      return exports.setup(Object.create(new.target.prototype), globalObject, undefined);
    }

    open(method, url) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "open");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'open' on 'XMLHttpRequest': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      switch (arguments.length) {
        case 2:
          {
            let curArg = arguments[0];
            curArg = conversions["ByteString"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 1",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[1];
            curArg = conversions["USVString"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 2",
              globals: globalObject
            });
            args.push(curArg);
          }
          break;
        case 3:
          {
            let curArg = arguments[0];
            curArg = conversions["ByteString"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 1",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[1];
            curArg = conversions["USVString"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 2",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[2];
            curArg = conversions["boolean"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 3",
              globals: globalObject
            });
            args.push(curArg);
          }
          break;
        case 4:
          {
            let curArg = arguments[0];
            curArg = conversions["ByteString"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 1",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[1];
            curArg = conversions["USVString"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 2",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[2];
            curArg = conversions["boolean"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 3",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[3];
            if (curArg !== undefined) {
              if (curArg === null || curArg === undefined) {
                curArg = null;
              } else {
                curArg = conversions["USVString"](curArg, {
                  context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 4",
                  globals: globalObject
                });
              }
            } else {
              curArg = null;
            }
            args.push(curArg);
          }
          break;
        default:
          {
            let curArg = arguments[0];
            curArg = conversions["ByteString"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 1",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[1];
            curArg = conversions["USVString"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 2",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[2];
            curArg = conversions["boolean"](curArg, {
              context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 3",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[3];
            if (curArg !== undefined) {
              if (curArg === null || curArg === undefined) {
                curArg = null;
              } else {
                curArg = conversions["USVString"](curArg, {
                  context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 4",
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
                curArg = conversions["USVString"](curArg, {
                  context: "Failed to execute 'open' on 'XMLHttpRequest': parameter 5",
                  globals: globalObject
                });
              }
            } else {
              curArg = null;
            }
            args.push(curArg);
          }
      }
      return $impl.open(...args);
    }

    setRequestHeader(name, value) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setRequestHeader");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'setRequestHeader' on 'XMLHttpRequest': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["ByteString"](curArg, {
          context: "Failed to execute 'setRequestHeader' on 'XMLHttpRequest': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["ByteString"](curArg, {
          context: "Failed to execute 'setRequestHeader' on 'XMLHttpRequest': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.setRequestHeader(...args);
    }

    send() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "send");
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = null;
          } else {
            if (Document.is(curArg) || Blob.is(curArg) || FormData.is(curArg)) {
              curArg = utils.implForWrapper(curArg);
            } else if (utils.isArrayBuffer(curArg)) {
              curArg = conversions["ArrayBuffer"](curArg, {
                context: "Failed to execute 'send' on 'XMLHttpRequest': parameter 1",
                globals: globalObject
              });
            } else if (ArrayBuffer.isView(curArg)) {
              curArg = conversions["ArrayBufferView"](curArg, {
                context: "Failed to execute 'send' on 'XMLHttpRequest': parameter 1",
                globals: globalObject
              });
            } else {
              curArg = conversions["USVString"](curArg, {
                context: "Failed to execute 'send' on 'XMLHttpRequest': parameter 1",
                globals: globalObject
              });
            }
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      return $impl.send(...args);
    }

    abort() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "abort");
      return $impl.abort();
    }

    getResponseHeader(name) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getResponseHeader");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getResponseHeader' on 'XMLHttpRequest': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["ByteString"](curArg, {
          context: "Failed to execute 'getResponseHeader' on 'XMLHttpRequest': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.getResponseHeader(...args);
    }

    getAllResponseHeaders() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getAllResponseHeaders");
      return $impl.getAllResponseHeaders();
    }

    overrideMimeType(mime) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "overrideMimeType");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'overrideMimeType' on 'XMLHttpRequest': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'overrideMimeType' on 'XMLHttpRequest': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.overrideMimeType(...args);
    }

    get onreadystatechange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onreadystatechange");
      return utils.tryWrapperForImpl($impl["onreadystatechange"]);
    }

    set onreadystatechange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onreadystatechange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onreadystatechange' property on 'XMLHttpRequest': The provided value"
        });
      }
      $impl["onreadystatechange"] = V;
    }

    get readyState() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get readyState");
      return $impl["readyState"];
    }

    get timeout() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get timeout");
      return $impl["timeout"];
    }

    set timeout(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set timeout");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'timeout' property on 'XMLHttpRequest': The provided value",
        globals: globalObject
      });

      $impl["timeout"] = V;
    }

    get withCredentials() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get withCredentials");
      return $impl["withCredentials"];
    }

    set withCredentials(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set withCredentials");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'withCredentials' property on 'XMLHttpRequest': The provided value",
        globals: globalObject
      });

      $impl["withCredentials"] = V;
    }

    get upload() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get upload");
      return utils.getSameObject(this, "upload", () => {
        return utils.tryWrapperForImpl($impl["upload"]);
      });
    }

    get responseURL() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get responseURL");
      return $impl["responseURL"];
    }

    get status() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get status");
      return $impl["status"];
    }

    get statusText() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get statusText");
      return $impl["statusText"];
    }

    get responseType() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get responseType");
      return utils.tryWrapperForImpl($impl["responseType"]);
    }

    set responseType(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set responseType");

      V = `${V}`;
      if (!XMLHttpRequestResponseType.enumerationValues.has(V)) {
        return;
      }

      $impl["responseType"] = V;
    }

    get response() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get response");
      return $impl["response"];
    }

    get responseText() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get responseText");
      return $impl["responseText"];
    }

    get responseXML() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get responseXML");
      return utils.tryWrapperForImpl($impl["responseXML"]);
    }
  }
  Object.defineProperties(XMLHttpRequest.prototype, {
    open: { enumerable: true },
    setRequestHeader: { enumerable: true },
    send: { enumerable: true },
    abort: { enumerable: true },
    getResponseHeader: { enumerable: true },
    getAllResponseHeaders: { enumerable: true },
    overrideMimeType: { enumerable: true },
    onreadystatechange: { enumerable: true },
    readyState: { enumerable: true },
    timeout: { enumerable: true },
    withCredentials: { enumerable: true },
    upload: { enumerable: true },
    responseURL: { enumerable: true },
    status: { enumerable: true },
    statusText: { enumerable: true },
    responseType: { enumerable: true },
    response: { enumerable: true },
    responseText: { enumerable: true },
    responseXML: { enumerable: true },
    [Symbol.toStringTag]: { value: "XMLHttpRequest", configurable: true },
    UNSENT: { value: 0, enumerable: true },
    OPENED: { value: 1, enumerable: true },
    HEADERS_RECEIVED: { value: 2, enumerable: true },
    LOADING: { value: 3, enumerable: true },
    DONE: { value: 4, enumerable: true }
  });
  Object.defineProperties(XMLHttpRequest, {
    UNSENT: { value: 0, enumerable: true },
    OPENED: { value: 1, enumerable: true },
    HEADERS_RECEIVED: { value: 2, enumerable: true },
    LOADING: { value: 3, enumerable: true },
    DONE: { value: 4, enumerable: true }
  });
  ctorRegistry[interfaceName] = XMLHttpRequest;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: XMLHttpRequest
  });
};

const Impl = require("../../jsdom/living/xhr/XMLHttpRequest-impl.js");
