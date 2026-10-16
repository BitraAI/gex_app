"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const Node = require("./Node.js");
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const AbstractRange = require("./AbstractRange.js");

const interfaceName = "Range";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => AbstractRange.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'Range'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["Range"].prototype;
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
  AbstractRange._internalSetup(wrapper, globalObject);
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
  class Range extends globalObject.AbstractRange {
    constructor() {
      return exports.setup(Object.create(new.target.prototype), globalObject, undefined);
    }

    setStart(node, offset) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setStart");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'setStart' on 'Range': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'setStart' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'setStart' on 'Range': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.setStart(...args);
    }

    setEnd(node, offset) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setEnd");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'setEnd' on 'Range': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, { context: "Failed to execute 'setEnd' on 'Range': parameter 1" });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'setEnd' on 'Range': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.setEnd(...args);
    }

    setStartBefore(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setStartBefore");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setStartBefore' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'setStartBefore' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.setStartBefore(...args);
    }

    setStartAfter(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setStartAfter");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setStartAfter' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'setStartAfter' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.setStartAfter(...args);
    }

    setEndBefore(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setEndBefore");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setEndBefore' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'setEndBefore' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.setEndBefore(...args);
    }

    setEndAfter(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setEndAfter");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setEndAfter' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'setEndAfter' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.setEndAfter(...args);
    }

    collapse() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "collapse");
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'collapse' on 'Range': parameter 1",
            globals: globalObject
          });
        } else {
          curArg = false;
        }
        args.push(curArg);
      }
      return $impl.collapse(...args);
    }

    selectNode(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "selectNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'selectNode' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'selectNode' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.selectNode(...args);
    }

    selectNodeContents(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "selectNodeContents");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'selectNodeContents' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'selectNodeContents' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.selectNodeContents(...args);
    }

    compareBoundaryPoints(how, sourceRange) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "compareBoundaryPoints");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'compareBoundaryPoints' on 'Range': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["unsigned short"](curArg, {
          context: "Failed to execute 'compareBoundaryPoints' on 'Range': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = exports.convert(globalObject, curArg, {
          context: "Failed to execute 'compareBoundaryPoints' on 'Range': parameter 2"
        });
        args.push(curArg);
      }
      return $impl.compareBoundaryPoints(...args);
    }

    deleteContents() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "deleteContents");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.deleteContents();
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    extractContents() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "extractContents");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.extractContents());
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    cloneContents() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "cloneContents");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.cloneContents());
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    insertNode(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "insertNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'insertNode' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'insertNode' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.insertNode(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    surroundContents(newParent) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "surroundContents");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'surroundContents' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'surroundContents' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.surroundContents(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    cloneRange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "cloneRange");
      return utils.tryWrapperForImpl($impl.cloneRange());
    }

    detach() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "detach");
      return $impl.detach();
    }

    isPointInRange(node, offset) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "isPointInRange");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'isPointInRange' on 'Range': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'isPointInRange' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'isPointInRange' on 'Range': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.isPointInRange(...args);
    }

    comparePoint(node, offset) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "comparePoint");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'comparePoint' on 'Range': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'comparePoint' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'comparePoint' on 'Range': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.comparePoint(...args);
    }

    intersectsNode(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "intersectsNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'intersectsNode' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'intersectsNode' on 'Range': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.intersectsNode(...args);
    }

    toString() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "toString");
      return $impl.toString();
    }

    createContextualFragment(fragment) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createContextualFragment");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createContextualFragment' on 'Range': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createContextualFragment' on 'Range': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.createContextualFragment(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get commonAncestorContainer() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get commonAncestorContainer");
      return utils.tryWrapperForImpl($impl["commonAncestorContainer"]);
    }
  }
  Object.defineProperties(Range.prototype, {
    setStart: { enumerable: true },
    setEnd: { enumerable: true },
    setStartBefore: { enumerable: true },
    setStartAfter: { enumerable: true },
    setEndBefore: { enumerable: true },
    setEndAfter: { enumerable: true },
    collapse: { enumerable: true },
    selectNode: { enumerable: true },
    selectNodeContents: { enumerable: true },
    compareBoundaryPoints: { enumerable: true },
    deleteContents: { enumerable: true },
    extractContents: { enumerable: true },
    cloneContents: { enumerable: true },
    insertNode: { enumerable: true },
    surroundContents: { enumerable: true },
    cloneRange: { enumerable: true },
    detach: { enumerable: true },
    isPointInRange: { enumerable: true },
    comparePoint: { enumerable: true },
    intersectsNode: { enumerable: true },
    toString: { enumerable: true },
    createContextualFragment: { enumerable: true },
    commonAncestorContainer: { enumerable: true },
    [Symbol.toStringTag]: { value: "Range", configurable: true },
    START_TO_START: { value: 0, enumerable: true },
    START_TO_END: { value: 1, enumerable: true },
    END_TO_END: { value: 2, enumerable: true },
    END_TO_START: { value: 3, enumerable: true }
  });
  Object.defineProperties(Range, {
    START_TO_START: { value: 0, enumerable: true },
    START_TO_END: { value: 1, enumerable: true },
    END_TO_END: { value: 2, enumerable: true },
    END_TO_START: { value: 3, enumerable: true }
  });
  ctorRegistry[interfaceName] = Range;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: Range
  });
};

const Impl = require("../../jsdom/living/range/Range-impl.js");
