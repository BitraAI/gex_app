"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const Node = require("./Node.js");
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "DocumentFragment";

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
  throw new globalObject.TypeError(`${context} is not of type 'DocumentFragment'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["DocumentFragment"].prototype;
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
  class DocumentFragment extends globalObject.Node {
    constructor() {
      return exports.setup(Object.create(new.target.prototype), globalObject, undefined);
    }

    getElementById(elementId) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getElementById");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getElementById' on 'DocumentFragment': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementById' on 'DocumentFragment': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getElementById(...args));
    }

    prepend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "prepend");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        if (Node.is(curArg)) {
          curArg = utils.implForWrapper(curArg);
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'prepend' on 'DocumentFragment': parameter " + (i + 1),
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.prepend(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    append() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "append");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        if (Node.is(curArg)) {
          curArg = utils.implForWrapper(curArg);
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'append' on 'DocumentFragment': parameter " + (i + 1),
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.append(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    replaceChildren() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "replaceChildren");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        if (Node.is(curArg)) {
          curArg = utils.implForWrapper(curArg);
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'replaceChildren' on 'DocumentFragment': parameter " + (i + 1),
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.replaceChildren(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    querySelector(selectors) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "querySelector");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'querySelector' on 'DocumentFragment': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'querySelector' on 'DocumentFragment': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.querySelector(...args));
    }

    querySelectorAll(selectors) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "querySelectorAll");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'querySelectorAll' on 'DocumentFragment': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'querySelectorAll' on 'DocumentFragment': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.querySelectorAll(...args));
    }

    get children() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get children");
      return utils.getSameObject(this, "children", () => {
        return utils.tryWrapperForImpl($impl["children"]);
      });
    }

    get firstElementChild() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get firstElementChild");
      return utils.tryWrapperForImpl($impl["firstElementChild"]);
    }

    get lastElementChild() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get lastElementChild");
      return utils.tryWrapperForImpl($impl["lastElementChild"]);
    }

    get childElementCount() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get childElementCount");
      return $impl["childElementCount"];
    }
  }
  Object.defineProperties(DocumentFragment.prototype, {
    getElementById: { enumerable: true },
    prepend: { enumerable: true },
    append: { enumerable: true },
    replaceChildren: { enumerable: true },
    querySelector: { enumerable: true },
    querySelectorAll: { enumerable: true },
    children: { enumerable: true },
    firstElementChild: { enumerable: true },
    lastElementChild: { enumerable: true },
    childElementCount: { enumerable: true },
    [Symbol.toStringTag]: { value: "DocumentFragment", configurable: true },
    [Symbol.unscopables]: {
      value: { prepend: true, append: true, replaceChildren: true, __proto__: null },
      configurable: true
    }
  });
  ctorRegistry[interfaceName] = DocumentFragment;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: DocumentFragment
  });
};

const Impl = require("../../jsdom/living/nodes/DocumentFragment-impl.js");
