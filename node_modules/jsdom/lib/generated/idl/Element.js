"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const Attr = require("./Attr.js");
const ShadowRootInit = require("./ShadowRootInit.js");
const Node = require("./Node.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "Element";

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
  throw new globalObject.TypeError(`${context} is not of type 'Element'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["Element"].prototype;
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
  class Element extends globalObject.Node {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }

    hasAttributes() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "hasAttributes");
      return $impl.hasAttributes();
    }

    getAttributeNames() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getAttributeNames");
      return utils.tryWrapperForImpl($impl.getAttributeNames());
    }

    getAttribute(qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getAttribute");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getAttribute' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getAttribute' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.getAttribute(...args);
    }

    getAttributeNS(namespace, localName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getAttributeNS");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'getAttributeNS' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'getAttributeNS' on 'Element': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getAttributeNS' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.getAttributeNS(...args);
    }

    setAttribute(qualifiedName, value) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setAttribute");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'setAttribute' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'setAttribute' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'setAttribute' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.setAttribute(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    setAttributeNS(namespace, qualifiedName, value) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setAttributeNS");
      if (arguments.length < 3) {
        throw new globalObject.TypeError(
          `Failed to execute 'setAttributeNS' on 'Element': 3 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'setAttributeNS' on 'Element': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'setAttributeNS' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[2];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'setAttributeNS' on 'Element': parameter 3",
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.setAttributeNS(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    removeAttribute(qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "removeAttribute");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'removeAttribute' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'removeAttribute' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.removeAttribute(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    removeAttributeNS(namespace, localName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "removeAttributeNS");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'removeAttributeNS' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'removeAttributeNS' on 'Element': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'removeAttributeNS' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.removeAttributeNS(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    toggleAttribute(qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "toggleAttribute");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'toggleAttribute' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'toggleAttribute' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'toggleAttribute' on 'Element': parameter 2",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.toggleAttribute(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    hasAttribute(qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "hasAttribute");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'hasAttribute' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'hasAttribute' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.hasAttribute(...args);
    }

    hasAttributeNS(namespace, localName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "hasAttributeNS");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'hasAttributeNS' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'hasAttributeNS' on 'Element': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'hasAttributeNS' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.hasAttributeNS(...args);
    }

    getAttributeNode(qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getAttributeNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getAttributeNode' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getAttributeNode' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getAttributeNode(...args));
    }

    getAttributeNodeNS(namespace, localName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getAttributeNodeNS");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'getAttributeNodeNS' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'getAttributeNodeNS' on 'Element': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getAttributeNodeNS' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getAttributeNodeNS(...args));
    }

    setAttributeNode(attr) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setAttributeNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setAttributeNode' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Attr.convert(globalObject, curArg, {
          context: "Failed to execute 'setAttributeNode' on 'Element': parameter 1"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.setAttributeNode(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    setAttributeNodeNS(attr) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setAttributeNodeNS");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setAttributeNodeNS' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Attr.convert(globalObject, curArg, {
          context: "Failed to execute 'setAttributeNodeNS' on 'Element': parameter 1"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.setAttributeNodeNS(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    removeAttributeNode(attr) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "removeAttributeNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'removeAttributeNode' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Attr.convert(globalObject, curArg, {
          context: "Failed to execute 'removeAttributeNode' on 'Element': parameter 1"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.removeAttributeNode(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    attachShadow(init) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "attachShadow");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'attachShadow' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = ShadowRootInit.convert(globalObject, curArg, {
          context: "Failed to execute 'attachShadow' on 'Element': parameter 1"
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.attachShadow(...args));
    }

    closest(selectors) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "closest");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'closest' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'closest' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.closest(...args));
    }

    matches(selectors) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "matches");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'matches' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'matches' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.matches(...args);
    }

    webkitMatchesSelector(selectors) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "webkitMatchesSelector");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'webkitMatchesSelector' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'webkitMatchesSelector' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.webkitMatchesSelector(...args);
    }

    getElementsByTagName(qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getElementsByTagName");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getElementsByTagName' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementsByTagName' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getElementsByTagName(...args));
    }

    getElementsByTagNameNS(namespace, localName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getElementsByTagNameNS");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'getElementsByTagNameNS' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'getElementsByTagNameNS' on 'Element': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementsByTagNameNS' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getElementsByTagNameNS(...args));
    }

    getElementsByClassName(classNames) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getElementsByClassName");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getElementsByClassName' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementsByClassName' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getElementsByClassName(...args));
    }

    insertAdjacentElement(where, element) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "insertAdjacentElement");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'insertAdjacentElement' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'insertAdjacentElement' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = exports.convert(globalObject, curArg, {
          context: "Failed to execute 'insertAdjacentElement' on 'Element': parameter 2"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.insertAdjacentElement(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    insertAdjacentText(where, data) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "insertAdjacentText");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'insertAdjacentText' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'insertAdjacentText' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'insertAdjacentText' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.insertAdjacentText(...args);
    }

    insertAdjacentHTML(position, text) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "insertAdjacentHTML");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'insertAdjacentHTML' on 'Element': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'insertAdjacentHTML' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'insertAdjacentHTML' on 'Element': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.insertAdjacentHTML(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    getClientRects() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getClientRects");
      return utils.tryWrapperForImpl($impl.getClientRects());
    }

    getBoundingClientRect() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getBoundingClientRect");
      return utils.tryWrapperForImpl($impl.getBoundingClientRect());
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
            context: "Failed to execute 'before' on 'Element': parameter " + (i + 1),
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
            context: "Failed to execute 'after' on 'Element': parameter " + (i + 1),
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
            context: "Failed to execute 'replaceWith' on 'Element': parameter " + (i + 1),
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

    prepend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "prepend");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        if (Node.is(curArg)) {
          curArg = utils.implForWrapper(curArg);
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'prepend' on 'Element': parameter " + (i + 1),
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
            context: "Failed to execute 'append' on 'Element': parameter " + (i + 1),
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
            context: "Failed to execute 'replaceChildren' on 'Element': parameter " + (i + 1),
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
          `Failed to execute 'querySelector' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'querySelector' on 'Element': parameter 1",
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
          `Failed to execute 'querySelectorAll' on 'Element': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'querySelectorAll' on 'Element': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.querySelectorAll(...args));
    }

    get namespaceURI() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get namespaceURI");
      return $impl["namespaceURI"];
    }

    get prefix() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get prefix");
      return $impl["prefix"];
    }

    get localName() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get localName");
      return $impl["localName"];
    }

    get tagName() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get tagName");
      return $impl["tagName"];
    }

    get id() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get id");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("id");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set id(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set id");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'id' property on 'Element': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("id", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get className() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get className");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("class");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set className(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set className");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'className' property on 'Element': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("class", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get classList() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get classList");
      return utils.getSameObject(this, "classList", () => {
        return utils.tryWrapperForImpl($impl["classList"]);
      });
    }

    set classList(V) {
      const esValue = this ?? globalObject;
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set classList");

      const Q = esValue["classList"];
      if (!utils.isObject(Q)) {
        throw new globalObject.TypeError("Property 'classList' is not an object");
      }
      Reflect.set(Q, "value", V);
    }

    get slot() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get slot");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("slot");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set slot(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set slot");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'slot' property on 'Element': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("slot", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get attributes() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get attributes");
      return utils.getSameObject(this, "attributes", () => {
        return utils.tryWrapperForImpl($impl["attributes"]);
      });
    }

    get shadowRoot() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get shadowRoot");
      return utils.tryWrapperForImpl($impl["shadowRoot"]);
    }

    get outerHTML() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get outerHTML");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["outerHTML"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set outerHTML(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set outerHTML");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'outerHTML' property on 'Element': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["outerHTML"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get scrollTop() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get scrollTop");
      return $impl["scrollTop"];
    }

    set scrollTop(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set scrollTop");

      V = conversions["unrestricted double"](V, {
        context: "Failed to set the 'scrollTop' property on 'Element': The provided value",
        globals: globalObject
      });

      $impl["scrollTop"] = V;
    }

    get scrollLeft() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get scrollLeft");
      return $impl["scrollLeft"];
    }

    set scrollLeft(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set scrollLeft");

      V = conversions["unrestricted double"](V, {
        context: "Failed to set the 'scrollLeft' property on 'Element': The provided value",
        globals: globalObject
      });

      $impl["scrollLeft"] = V;
    }

    get scrollWidth() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get scrollWidth");
      return $impl["scrollWidth"];
    }

    get scrollHeight() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get scrollHeight");
      return $impl["scrollHeight"];
    }

    get clientTop() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get clientTop");
      return $impl["clientTop"];
    }

    get clientLeft() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get clientLeft");
      return $impl["clientLeft"];
    }

    get clientWidth() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get clientWidth");
      return $impl["clientWidth"];
    }

    get clientHeight() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get clientHeight");
      return $impl["clientHeight"];
    }

    get innerHTML() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get innerHTML");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["innerHTML"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set innerHTML(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set innerHTML");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'innerHTML' property on 'Element': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["innerHTML"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get role() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get role");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("role");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set role(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set role");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'role' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("role");
        } else {
          $impl._reflectSetTheContentAttribute("role", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaAtomic() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaAtomic");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-atomic");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaAtomic(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaAtomic");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaAtomic' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-atomic");
        } else {
          $impl._reflectSetTheContentAttribute("aria-atomic", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaAutoComplete() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaAutoComplete");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-autocomplete");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaAutoComplete(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaAutoComplete");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaAutoComplete' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-autocomplete");
        } else {
          $impl._reflectSetTheContentAttribute("aria-autocomplete", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaBusy() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaBusy");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-busy");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaBusy(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaBusy");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaBusy' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-busy");
        } else {
          $impl._reflectSetTheContentAttribute("aria-busy", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaChecked() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaChecked");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-checked");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaChecked(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaChecked");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaChecked' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-checked");
        } else {
          $impl._reflectSetTheContentAttribute("aria-checked", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaColCount() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaColCount");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-colcount");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaColCount(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaColCount");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaColCount' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-colcount");
        } else {
          $impl._reflectSetTheContentAttribute("aria-colcount", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaColIndex() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaColIndex");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-colindex");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaColIndex(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaColIndex");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaColIndex' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-colindex");
        } else {
          $impl._reflectSetTheContentAttribute("aria-colindex", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaColIndexText() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaColIndexText");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-colindextext");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaColIndexText(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaColIndexText");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaColIndexText' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-colindextext");
        } else {
          $impl._reflectSetTheContentAttribute("aria-colindextext", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaColSpan() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaColSpan");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-colspan");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaColSpan(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaColSpan");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaColSpan' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-colspan");
        } else {
          $impl._reflectSetTheContentAttribute("aria-colspan", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaCurrent() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaCurrent");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-current");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaCurrent(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaCurrent");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaCurrent' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-current");
        } else {
          $impl._reflectSetTheContentAttribute("aria-current", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaDescription() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaDescription");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-description");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaDescription(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaDescription");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaDescription' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-description");
        } else {
          $impl._reflectSetTheContentAttribute("aria-description", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaDisabled() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaDisabled");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-disabled");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaDisabled(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaDisabled");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaDisabled' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-disabled");
        } else {
          $impl._reflectSetTheContentAttribute("aria-disabled", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaExpanded() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaExpanded");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-expanded");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaExpanded(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaExpanded");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaExpanded' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-expanded");
        } else {
          $impl._reflectSetTheContentAttribute("aria-expanded", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaHasPopup() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaHasPopup");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-haspopup");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaHasPopup(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaHasPopup");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaHasPopup' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-haspopup");
        } else {
          $impl._reflectSetTheContentAttribute("aria-haspopup", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaHidden() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaHidden");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-hidden");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaHidden(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaHidden");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaHidden' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-hidden");
        } else {
          $impl._reflectSetTheContentAttribute("aria-hidden", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaInvalid() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaInvalid");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-invalid");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaInvalid(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaInvalid");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaInvalid' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-invalid");
        } else {
          $impl._reflectSetTheContentAttribute("aria-invalid", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaKeyShortcuts() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaKeyShortcuts");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-keyshortcuts");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaKeyShortcuts(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaKeyShortcuts");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaKeyShortcuts' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-keyshortcuts");
        } else {
          $impl._reflectSetTheContentAttribute("aria-keyshortcuts", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaLabel() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaLabel");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-label");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaLabel(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaLabel");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaLabel' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-label");
        } else {
          $impl._reflectSetTheContentAttribute("aria-label", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaLevel() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaLevel");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-level");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaLevel(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaLevel");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaLevel' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-level");
        } else {
          $impl._reflectSetTheContentAttribute("aria-level", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaLive() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaLive");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-live");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaLive(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaLive");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaLive' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-live");
        } else {
          $impl._reflectSetTheContentAttribute("aria-live", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaModal() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaModal");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-modal");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaModal(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaModal");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaModal' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-modal");
        } else {
          $impl._reflectSetTheContentAttribute("aria-modal", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaMultiLine() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaMultiLine");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-multiline");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaMultiLine(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaMultiLine");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaMultiLine' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-multiline");
        } else {
          $impl._reflectSetTheContentAttribute("aria-multiline", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaMultiSelectable() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaMultiSelectable");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-multiselectable");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaMultiSelectable(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaMultiSelectable");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaMultiSelectable' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-multiselectable");
        } else {
          $impl._reflectSetTheContentAttribute("aria-multiselectable", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaOrientation() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaOrientation");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-orientation");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaOrientation(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaOrientation");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaOrientation' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-orientation");
        } else {
          $impl._reflectSetTheContentAttribute("aria-orientation", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaPlaceholder() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaPlaceholder");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-placeholder");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaPlaceholder(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaPlaceholder");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaPlaceholder' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-placeholder");
        } else {
          $impl._reflectSetTheContentAttribute("aria-placeholder", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaPosInSet() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaPosInSet");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-posinset");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaPosInSet(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaPosInSet");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaPosInSet' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-posinset");
        } else {
          $impl._reflectSetTheContentAttribute("aria-posinset", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaPressed() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaPressed");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-pressed");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaPressed(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaPressed");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaPressed' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-pressed");
        } else {
          $impl._reflectSetTheContentAttribute("aria-pressed", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaReadOnly() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaReadOnly");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-readonly");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaReadOnly(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaReadOnly");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaReadOnly' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-readonly");
        } else {
          $impl._reflectSetTheContentAttribute("aria-readonly", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaRequired() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaRequired");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-required");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaRequired(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaRequired");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaRequired' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-required");
        } else {
          $impl._reflectSetTheContentAttribute("aria-required", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaRoleDescription() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaRoleDescription");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-roledescription");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaRoleDescription(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaRoleDescription");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaRoleDescription' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-roledescription");
        } else {
          $impl._reflectSetTheContentAttribute("aria-roledescription", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaRowCount() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaRowCount");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-rowcount");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaRowCount(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaRowCount");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaRowCount' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-rowcount");
        } else {
          $impl._reflectSetTheContentAttribute("aria-rowcount", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaRowIndex() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaRowIndex");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-rowindex");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaRowIndex(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaRowIndex");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaRowIndex' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-rowindex");
        } else {
          $impl._reflectSetTheContentAttribute("aria-rowindex", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaRowIndexText() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaRowIndexText");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-rowindextext");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaRowIndexText(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaRowIndexText");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaRowIndexText' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-rowindextext");
        } else {
          $impl._reflectSetTheContentAttribute("aria-rowindextext", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaRowSpan() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaRowSpan");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-rowspan");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaRowSpan(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaRowSpan");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaRowSpan' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-rowspan");
        } else {
          $impl._reflectSetTheContentAttribute("aria-rowspan", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaSelected() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaSelected");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-selected");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaSelected(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaSelected");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaSelected' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-selected");
        } else {
          $impl._reflectSetTheContentAttribute("aria-selected", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaSetSize() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaSetSize");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-setsize");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaSetSize(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaSetSize");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaSetSize' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-setsize");
        } else {
          $impl._reflectSetTheContentAttribute("aria-setsize", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaSort() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaSort");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-sort");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaSort(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaSort");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaSort' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-sort");
        } else {
          $impl._reflectSetTheContentAttribute("aria-sort", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaValueMax() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaValueMax");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-valuemax");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaValueMax(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaValueMax");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaValueMax' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-valuemax");
        } else {
          $impl._reflectSetTheContentAttribute("aria-valuemax", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaValueMin() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaValueMin");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-valuemin");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaValueMin(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaValueMin");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaValueMin' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-valuemin");
        } else {
          $impl._reflectSetTheContentAttribute("aria-valuemin", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaValueNow() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaValueNow");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-valuenow");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaValueNow(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaValueNow");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaValueNow' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-valuenow");
        } else {
          $impl._reflectSetTheContentAttribute("aria-valuenow", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaValueText() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaValueText");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-valuetext");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaValueText(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaValueText");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaValueText' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-valuetext");
        } else {
          $impl._reflectSetTheContentAttribute("aria-valuetext", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get ariaRelevant() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ariaRelevant");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("aria-relevant");
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set ariaRelevant(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ariaRelevant");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'ariaRelevant' property on 'Element': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V === null) {
          $impl._reflectDeleteTheContentAttribute("aria-relevant");
        } else {
          $impl._reflectSetTheContentAttribute("aria-relevant", V);
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get previousElementSibling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get previousElementSibling");
      return utils.tryWrapperForImpl($impl["previousElementSibling"]);
    }

    get nextElementSibling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get nextElementSibling");
      return utils.tryWrapperForImpl($impl["nextElementSibling"]);
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

    get assignedSlot() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get assignedSlot");
      return utils.tryWrapperForImpl($impl["assignedSlot"]);
    }
  }
  Object.defineProperties(Element.prototype, {
    hasAttributes: { enumerable: true },
    getAttributeNames: { enumerable: true },
    getAttribute: { enumerable: true },
    getAttributeNS: { enumerable: true },
    setAttribute: { enumerable: true },
    setAttributeNS: { enumerable: true },
    removeAttribute: { enumerable: true },
    removeAttributeNS: { enumerable: true },
    toggleAttribute: { enumerable: true },
    hasAttribute: { enumerable: true },
    hasAttributeNS: { enumerable: true },
    getAttributeNode: { enumerable: true },
    getAttributeNodeNS: { enumerable: true },
    setAttributeNode: { enumerable: true },
    setAttributeNodeNS: { enumerable: true },
    removeAttributeNode: { enumerable: true },
    attachShadow: { enumerable: true },
    closest: { enumerable: true },
    matches: { enumerable: true },
    webkitMatchesSelector: { enumerable: true },
    getElementsByTagName: { enumerable: true },
    getElementsByTagNameNS: { enumerable: true },
    getElementsByClassName: { enumerable: true },
    insertAdjacentElement: { enumerable: true },
    insertAdjacentText: { enumerable: true },
    insertAdjacentHTML: { enumerable: true },
    getClientRects: { enumerable: true },
    getBoundingClientRect: { enumerable: true },
    before: { enumerable: true },
    after: { enumerable: true },
    replaceWith: { enumerable: true },
    remove: { enumerable: true },
    prepend: { enumerable: true },
    append: { enumerable: true },
    replaceChildren: { enumerable: true },
    querySelector: { enumerable: true },
    querySelectorAll: { enumerable: true },
    namespaceURI: { enumerable: true },
    prefix: { enumerable: true },
    localName: { enumerable: true },
    tagName: { enumerable: true },
    id: { enumerable: true },
    className: { enumerable: true },
    classList: { enumerable: true },
    slot: { enumerable: true },
    attributes: { enumerable: true },
    shadowRoot: { enumerable: true },
    outerHTML: { enumerable: true },
    scrollTop: { enumerable: true },
    scrollLeft: { enumerable: true },
    scrollWidth: { enumerable: true },
    scrollHeight: { enumerable: true },
    clientTop: { enumerable: true },
    clientLeft: { enumerable: true },
    clientWidth: { enumerable: true },
    clientHeight: { enumerable: true },
    innerHTML: { enumerable: true },
    role: { enumerable: true },
    ariaAtomic: { enumerable: true },
    ariaAutoComplete: { enumerable: true },
    ariaBusy: { enumerable: true },
    ariaChecked: { enumerable: true },
    ariaColCount: { enumerable: true },
    ariaColIndex: { enumerable: true },
    ariaColIndexText: { enumerable: true },
    ariaColSpan: { enumerable: true },
    ariaCurrent: { enumerable: true },
    ariaDescription: { enumerable: true },
    ariaDisabled: { enumerable: true },
    ariaExpanded: { enumerable: true },
    ariaHasPopup: { enumerable: true },
    ariaHidden: { enumerable: true },
    ariaInvalid: { enumerable: true },
    ariaKeyShortcuts: { enumerable: true },
    ariaLabel: { enumerable: true },
    ariaLevel: { enumerable: true },
    ariaLive: { enumerable: true },
    ariaModal: { enumerable: true },
    ariaMultiLine: { enumerable: true },
    ariaMultiSelectable: { enumerable: true },
    ariaOrientation: { enumerable: true },
    ariaPlaceholder: { enumerable: true },
    ariaPosInSet: { enumerable: true },
    ariaPressed: { enumerable: true },
    ariaReadOnly: { enumerable: true },
    ariaRequired: { enumerable: true },
    ariaRoleDescription: { enumerable: true },
    ariaRowCount: { enumerable: true },
    ariaRowIndex: { enumerable: true },
    ariaRowIndexText: { enumerable: true },
    ariaRowSpan: { enumerable: true },
    ariaSelected: { enumerable: true },
    ariaSetSize: { enumerable: true },
    ariaSort: { enumerable: true },
    ariaValueMax: { enumerable: true },
    ariaValueMin: { enumerable: true },
    ariaValueNow: { enumerable: true },
    ariaValueText: { enumerable: true },
    ariaRelevant: { enumerable: true },
    previousElementSibling: { enumerable: true },
    nextElementSibling: { enumerable: true },
    children: { enumerable: true },
    firstElementChild: { enumerable: true },
    lastElementChild: { enumerable: true },
    childElementCount: { enumerable: true },
    assignedSlot: { enumerable: true },
    [Symbol.toStringTag]: { value: "Element", configurable: true },
    [Symbol.unscopables]: {
      value: {
        slot: true,
        before: true,
        after: true,
        replaceWith: true,
        remove: true,
        prepend: true,
        append: true,
        replaceChildren: true,
        __proto__: null
      },
      configurable: true
    }
  });
  ctorRegistry[interfaceName] = Element;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: Element
  });
};

const Impl = require("../../jsdom/living/nodes/Element-impl.js");
