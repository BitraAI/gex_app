"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "Location";

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
  throw new globalObject.TypeError(`${context} is not of type 'Location'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["Location"].prototype;
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
      assign(url) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "assign");
        if (arguments.length < 1) {
          throw new globalObject.TypeError(
            `Failed to execute 'assign' on 'Location': 1 argument required, but only ${arguments.length} present.`
          );
        }
        const args = [];
        {
          let curArg = arguments[0];
          curArg = conversions["USVString"](curArg, {
            context: "Failed to execute 'assign' on 'Location': parameter 1",
            globals: globalObject
          });
          args.push(curArg);
        }
        return $impl.assign(...args);
      },
      replace(url) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "replace");
        if (arguments.length < 1) {
          throw new globalObject.TypeError(
            `Failed to execute 'replace' on 'Location': 1 argument required, but only ${arguments.length} present.`
          );
        }
        const args = [];
        {
          let curArg = arguments[0];
          curArg = conversions["USVString"](curArg, {
            context: "Failed to execute 'replace' on 'Location': parameter 1",
            globals: globalObject
          });
          args.push(curArg);
        }
        return $impl.replace(...args);
      },
      reload() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "reload");
        return $impl.reload();
      },
      get href() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get href");
        return $impl["href"];
      },
      set href(V) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set href");

        V = conversions["USVString"](V, {
          context: "Failed to set the 'href' property on 'Location': The provided value",
          globals: globalObject
        });

        $impl["href"] = V;
      },
      toString() {
        const $impl = $requireImpl(this, globalObject, "toString");

        return $impl["href"];
      },
      get origin() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get origin");
        return $impl["origin"];
      },
      get protocol() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get protocol");
        return $impl["protocol"];
      },
      set protocol(V) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set protocol");

        V = conversions["USVString"](V, {
          context: "Failed to set the 'protocol' property on 'Location': The provided value",
          globals: globalObject
        });

        $impl["protocol"] = V;
      },
      get host() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get host");
        return $impl["host"];
      },
      set host(V) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set host");

        V = conversions["USVString"](V, {
          context: "Failed to set the 'host' property on 'Location': The provided value",
          globals: globalObject
        });

        $impl["host"] = V;
      },
      get hostname() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get hostname");
        return $impl["hostname"];
      },
      set hostname(V) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set hostname");

        V = conversions["USVString"](V, {
          context: "Failed to set the 'hostname' property on 'Location': The provided value",
          globals: globalObject
        });

        $impl["hostname"] = V;
      },
      get port() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get port");
        return $impl["port"];
      },
      set port(V) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set port");

        V = conversions["USVString"](V, {
          context: "Failed to set the 'port' property on 'Location': The provided value",
          globals: globalObject
        });

        $impl["port"] = V;
      },
      get pathname() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get pathname");
        return $impl["pathname"];
      },
      set pathname(V) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set pathname");

        V = conversions["USVString"](V, {
          context: "Failed to set the 'pathname' property on 'Location': The provided value",
          globals: globalObject
        });

        $impl["pathname"] = V;
      },
      get search() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get search");
        return $impl["search"];
      },
      set search(V) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set search");

        V = conversions["USVString"](V, {
          context: "Failed to set the 'search' property on 'Location': The provided value",
          globals: globalObject
        });

        $impl["search"] = V;
      },
      get hash() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get hash");
        return $impl["hash"];
      },
      set hash(V) {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set hash");

        V = conversions["USVString"](V, {
          context: "Failed to set the 'hash' property on 'Location': The provided value",
          globals: globalObject
        });

        $impl["hash"] = V;
      }
    });
    Object.defineProperties(unforgeables, {
      assign: { configurable: false, writable: false },
      replace: { configurable: false, writable: false },
      reload: { configurable: false, writable: false },
      href: { configurable: false },
      toString: { configurable: false, writable: false },
      origin: { configurable: false },
      protocol: { configurable: false },
      host: { configurable: false },
      hostname: { configurable: false },
      port: { configurable: false },
      pathname: { configurable: false },
      search: { configurable: false },
      hash: { configurable: false }
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
const exposed = new Set(["Window"]);

exports.install = (globalObject, globalNames) => {
  if (!globalNames.some(globalName => exposed.has(globalName))) {
    return;
  }

  const ctorRegistry = utils.initCtorRegistry(globalObject);
  class Location {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }
  }
  Object.defineProperties(Location.prototype, { [Symbol.toStringTag]: { value: "Location", configurable: true } });
  ctorRegistry[interfaceName] = Location;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: Location
  });
};

const Impl = require("../../jsdom/living/window/Location-impl.js");
