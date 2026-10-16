"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const Node = require("./Node.js");
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "CharacterData";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => Node.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'CharacterData'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["CharacterData"].prototype;
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
  Node._internalSetup(wrapper, globalObject);
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
  class CharacterData extends globalObject.Node {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }

    substringData(offset, count) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "substringData");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'substringData' on 'CharacterData': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'substringData' on 'CharacterData': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'substringData' on 'CharacterData': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.substringData(...args);
    }

    appendData(data) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "appendData");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'appendData' on 'CharacterData': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'appendData' on 'CharacterData': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.appendData(...args);
    }

    insertData(offset, data) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "insertData");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'insertData' on 'CharacterData': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'insertData' on 'CharacterData': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'insertData' on 'CharacterData': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.insertData(...args);
    }

    deleteData(offset, count) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "deleteData");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'deleteData' on 'CharacterData': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'deleteData' on 'CharacterData': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'deleteData' on 'CharacterData': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.deleteData(...args);
    }

    replaceData(offset, count, data) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "replaceData");
      if (arguments.length < 3) {
        throw new globalObject.TypeError(
          `Failed to execute 'replaceData' on 'CharacterData': 3 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'replaceData' on 'CharacterData': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'replaceData' on 'CharacterData': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[2];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'replaceData' on 'CharacterData': parameter 3",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.replaceData(...args);
    }

    before() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "before");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        if (Node.is(curArg)) {
          curArg = utils.implForWrapper(curArg);
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'before' on 'CharacterData': parameter " + (i + 1),
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.before(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    after() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "after");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        if (Node.is(curArg)) {
          curArg = utils.implForWrapper(curArg);
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'after' on 'CharacterData': parameter " + (i + 1),
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.after(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    replaceWith() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "replaceWith");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        if (Node.is(curArg)) {
          curArg = utils.implForWrapper(curArg);
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'replaceWith' on 'CharacterData': parameter " + (i + 1),
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.replaceWith(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    remove() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "remove");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.remove();
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get data() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get data");
      return $impl["data"];
    }

    set data(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set data");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'data' property on 'CharacterData': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      $impl["data"] = V;
    }

    get length() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get length");
      return $impl["length"];
    }

    get previousElementSibling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get previousElementSibling");
      return utils.tryWrapperForImpl($impl["previousElementSibling"]);
    }

    get nextElementSibling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get nextElementSibling");
      return utils.tryWrapperForImpl($impl["nextElementSibling"]);
    }
  }
  Object.defineProperties(CharacterData.prototype, {
    substringData: { enumerable: true },
    appendData: { enumerable: true },
    insertData: { enumerable: true },
    deleteData: { enumerable: true },
    replaceData: { enumerable: true },
    before: { enumerable: true },
    after: { enumerable: true },
    replaceWith: { enumerable: true },
    remove: { enumerable: true },
    data: { enumerable: true },
    length: { enumerable: true },
    previousElementSibling: { enumerable: true },
    nextElementSibling: { enumerable: true },
    [Symbol.toStringTag]: { value: "CharacterData", configurable: true },
    [Symbol.unscopables]: {
      value: { before: true, after: true, replaceWith: true, remove: true, __proto__: null },
      configurable: true
    }
  });
  ctorRegistry[interfaceName] = CharacterData;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: CharacterData
  });
};

const Impl = require("../../jsdom/living/nodes/CharacterData-impl.js");
