"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "Navigator";

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
  throw new globalObject.TypeError(`${context} is not of type 'Navigator'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["Navigator"].prototype;
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
  class Navigator {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }

    javaEnabled() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "javaEnabled");
      return $impl.javaEnabled();
    }

    get appCodeName() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get appCodeName");
      return $impl["appCodeName"];
    }

    get appName() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get appName");
      return $impl["appName"];
    }

    get appVersion() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get appVersion");
      return $impl["appVersion"];
    }

    get platform() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get platform");
      return $impl["platform"];
    }

    get product() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get product");
      return $impl["product"];
    }

    get productSub() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get productSub");
      return $impl["productSub"];
    }

    get userAgent() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get userAgent");
      return $impl["userAgent"];
    }

    get vendor() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get vendor");
      return $impl["vendor"];
    }

    get vendorSub() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get vendorSub");
      return $impl["vendorSub"];
    }

    get language() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get language");
      return $impl["language"];
    }

    get languages() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get languages");
      return utils.tryWrapperForImpl($impl["languages"]);
    }

    get onLine() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onLine");
      return $impl["onLine"];
    }

    get cookieEnabled() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get cookieEnabled");
      return $impl["cookieEnabled"];
    }

    get plugins() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get plugins");
      return utils.getSameObject(this, "plugins", () => {
        return utils.tryWrapperForImpl($impl["plugins"]);
      });
    }

    get mimeTypes() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get mimeTypes");
      return utils.getSameObject(this, "mimeTypes", () => {
        return utils.tryWrapperForImpl($impl["mimeTypes"]);
      });
    }

    get hardwareConcurrency() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get hardwareConcurrency");
      return $impl["hardwareConcurrency"];
    }
  }
  Object.defineProperties(Navigator.prototype, {
    javaEnabled: { enumerable: true },
    appCodeName: { enumerable: true },
    appName: { enumerable: true },
    appVersion: { enumerable: true },
    platform: { enumerable: true },
    product: { enumerable: true },
    productSub: { enumerable: true },
    userAgent: { enumerable: true },
    vendor: { enumerable: true },
    vendorSub: { enumerable: true },
    language: { enumerable: true },
    languages: { enumerable: true },
    onLine: { enumerable: true },
    cookieEnabled: { enumerable: true },
    plugins: { enumerable: true },
    mimeTypes: { enumerable: true },
    hardwareConcurrency: { enumerable: true },
    [Symbol.toStringTag]: { value: "Navigator", configurable: true }
  });
  ctorRegistry[interfaceName] = Navigator;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: Navigator
  });
};

const Impl = require("../../jsdom/living/navigator/Navigator-impl.js");
