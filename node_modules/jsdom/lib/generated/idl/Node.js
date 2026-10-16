"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const GetRootNodeOptions = require("./GetRootNodeOptions.js");
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const EventTarget = require("./EventTarget.js");

const interfaceName = "Node";

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
  throw new globalObject.TypeError(`${context} is not of type 'Node'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["Node"].prototype;
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

const exposed = new Set(["Window"]);

exports.install = (globalObject, globalNames) => {
  if (!globalNames.some(globalName => exposed.has(globalName))) {
    return;
  }

  const ctorRegistry = utils.initCtorRegistry(globalObject);
  class Node extends globalObject.EventTarget {
    constructor() {
      throw new globalObject.TypeError("Illegal constructor");
    }

    getRootNode() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getRootNode");
      const args = [];
      {
        let curArg = arguments[0];
        curArg = GetRootNodeOptions.convert(globalObject, curArg, {
          context: "Failed to execute 'getRootNode' on 'Node': parameter 1"
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getRootNode(...args));
    }

    hasChildNodes() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "hasChildNodes");
      return $impl.hasChildNodes();
    }

    normalize() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "normalize");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.normalize();
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    cloneNode() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "cloneNode");
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'cloneNode' on 'Node': parameter 1",
            globals: globalObject
          });
        } else {
          curArg = false;
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.cloneNode(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    isEqualNode(otherNode) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "isEqualNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'isEqualNode' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = exports.convert(globalObject, curArg, {
            context: "Failed to execute 'isEqualNode' on 'Node': parameter 1"
          });
        }
        args.push(curArg);
      }
      return $impl.isEqualNode(...args);
    }

    isSameNode(otherNode) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "isSameNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'isSameNode' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = exports.convert(globalObject, curArg, {
            context: "Failed to execute 'isSameNode' on 'Node': parameter 1"
          });
        }
        args.push(curArg);
      }
      return $impl.isSameNode(...args);
    }

    compareDocumentPosition(other) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "compareDocumentPosition");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'compareDocumentPosition' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = exports.convert(globalObject, curArg, {
          context: "Failed to execute 'compareDocumentPosition' on 'Node': parameter 1"
        });
        args.push(curArg);
      }
      return $impl.compareDocumentPosition(...args);
    }

    contains(other) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "contains");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'contains' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = exports.convert(globalObject, curArg, {
            context: "Failed to execute 'contains' on 'Node': parameter 1"
          });
        }
        args.push(curArg);
      }
      return $impl.contains(...args);
    }

    lookupPrefix(namespace) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "lookupPrefix");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'lookupPrefix' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'lookupPrefix' on 'Node': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      return $impl.lookupPrefix(...args);
    }

    lookupNamespaceURI(prefix) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "lookupNamespaceURI");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'lookupNamespaceURI' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'lookupNamespaceURI' on 'Node': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      return $impl.lookupNamespaceURI(...args);
    }

    isDefaultNamespace(namespace) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "isDefaultNamespace");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'isDefaultNamespace' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'isDefaultNamespace' on 'Node': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      return $impl.isDefaultNamespace(...args);
    }

    insertBefore(node, child) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "insertBefore");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'insertBefore' on 'Node': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = exports.convert(globalObject, curArg, {
          context: "Failed to execute 'insertBefore' on 'Node': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = exports.convert(globalObject, curArg, {
            context: "Failed to execute 'insertBefore' on 'Node': parameter 2"
          });
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.insertBefore(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    appendChild(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "appendChild");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'appendChild' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = exports.convert(globalObject, curArg, {
          context: "Failed to execute 'appendChild' on 'Node': parameter 1"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.appendChild(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    replaceChild(node, child) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "replaceChild");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'replaceChild' on 'Node': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = exports.convert(globalObject, curArg, {
          context: "Failed to execute 'replaceChild' on 'Node': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = exports.convert(globalObject, curArg, {
          context: "Failed to execute 'replaceChild' on 'Node': parameter 2"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.replaceChild(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    removeChild(child) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "removeChild");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'removeChild' on 'Node': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = exports.convert(globalObject, curArg, {
          context: "Failed to execute 'removeChild' on 'Node': parameter 1"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.removeChild(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get nodeType() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get nodeType");
      return $impl["nodeType"];
    }

    get nodeName() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get nodeName");
      return $impl["nodeName"];
    }

    get baseURI() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get baseURI");
      return $impl["baseURI"];
    }

    get isConnected() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get isConnected");
      return $impl["isConnected"];
    }

    get ownerDocument() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ownerDocument");
      return utils.tryWrapperForImpl($impl["ownerDocument"]);
    }

    get parentNode() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get parentNode");
      return utils.tryWrapperForImpl($impl["parentNode"]);
    }

    get parentElement() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get parentElement");
      return utils.tryWrapperForImpl($impl["parentElement"]);
    }

    get childNodes() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get childNodes");
      return utils.getSameObject(this, "childNodes", () => {
        return utils.tryWrapperForImpl($impl["childNodes"]);
      });
    }

    get firstChild() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get firstChild");
      return utils.tryWrapperForImpl($impl["firstChild"]);
    }

    get lastChild() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get lastChild");
      return utils.tryWrapperForImpl($impl["lastChild"]);
    }

    get previousSibling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get previousSibling");
      return utils.tryWrapperForImpl($impl["previousSibling"]);
    }

    get nextSibling() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get nextSibling");
      return utils.tryWrapperForImpl($impl["nextSibling"]);
    }

    get nodeValue() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get nodeValue");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["nodeValue"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set nodeValue(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set nodeValue");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'nodeValue' property on 'Node': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["nodeValue"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get textContent() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get textContent");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["textContent"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set textContent(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set textContent");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = conversions["DOMString"](V, {
          context: "Failed to set the 'textContent' property on 'Node': The provided value",
          globals: globalObject
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["textContent"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }
  }
  Object.defineProperties(Node.prototype, {
    getRootNode: { enumerable: true },
    hasChildNodes: { enumerable: true },
    normalize: { enumerable: true },
    cloneNode: { enumerable: true },
    isEqualNode: { enumerable: true },
    isSameNode: { enumerable: true },
    compareDocumentPosition: { enumerable: true },
    contains: { enumerable: true },
    lookupPrefix: { enumerable: true },
    lookupNamespaceURI: { enumerable: true },
    isDefaultNamespace: { enumerable: true },
    insertBefore: { enumerable: true },
    appendChild: { enumerable: true },
    replaceChild: { enumerable: true },
    removeChild: { enumerable: true },
    nodeType: { enumerable: true },
    nodeName: { enumerable: true },
    baseURI: { enumerable: true },
    isConnected: { enumerable: true },
    ownerDocument: { enumerable: true },
    parentNode: { enumerable: true },
    parentElement: { enumerable: true },
    childNodes: { enumerable: true },
    firstChild: { enumerable: true },
    lastChild: { enumerable: true },
    previousSibling: { enumerable: true },
    nextSibling: { enumerable: true },
    nodeValue: { enumerable: true },
    textContent: { enumerable: true },
    [Symbol.toStringTag]: { value: "Node", configurable: true },
    ELEMENT_NODE: { value: 1, enumerable: true },
    ATTRIBUTE_NODE: { value: 2, enumerable: true },
    TEXT_NODE: { value: 3, enumerable: true },
    CDATA_SECTION_NODE: { value: 4, enumerable: true },
    ENTITY_REFERENCE_NODE: { value: 5, enumerable: true },
    ENTITY_NODE: { value: 6, enumerable: true },
    PROCESSING_INSTRUCTION_NODE: { value: 7, enumerable: true },
    COMMENT_NODE: { value: 8, enumerable: true },
    DOCUMENT_NODE: { value: 9, enumerable: true },
    DOCUMENT_TYPE_NODE: { value: 10, enumerable: true },
    DOCUMENT_FRAGMENT_NODE: { value: 11, enumerable: true },
    NOTATION_NODE: { value: 12, enumerable: true },
    DOCUMENT_POSITION_DISCONNECTED: { value: 0x01, enumerable: true },
    DOCUMENT_POSITION_PRECEDING: { value: 0x02, enumerable: true },
    DOCUMENT_POSITION_FOLLOWING: { value: 0x04, enumerable: true },
    DOCUMENT_POSITION_CONTAINS: { value: 0x08, enumerable: true },
    DOCUMENT_POSITION_CONTAINED_BY: { value: 0x10, enumerable: true },
    DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC: { value: 0x20, enumerable: true }
  });
  Object.defineProperties(Node, {
    ELEMENT_NODE: { value: 1, enumerable: true },
    ATTRIBUTE_NODE: { value: 2, enumerable: true },
    TEXT_NODE: { value: 3, enumerable: true },
    CDATA_SECTION_NODE: { value: 4, enumerable: true },
    ENTITY_REFERENCE_NODE: { value: 5, enumerable: true },
    ENTITY_NODE: { value: 6, enumerable: true },
    PROCESSING_INSTRUCTION_NODE: { value: 7, enumerable: true },
    COMMENT_NODE: { value: 8, enumerable: true },
    DOCUMENT_NODE: { value: 9, enumerable: true },
    DOCUMENT_TYPE_NODE: { value: 10, enumerable: true },
    DOCUMENT_FRAGMENT_NODE: { value: 11, enumerable: true },
    NOTATION_NODE: { value: 12, enumerable: true },
    DOCUMENT_POSITION_DISCONNECTED: { value: 0x01, enumerable: true },
    DOCUMENT_POSITION_PRECEDING: { value: 0x02, enumerable: true },
    DOCUMENT_POSITION_FOLLOWING: { value: 0x04, enumerable: true },
    DOCUMENT_POSITION_CONTAINS: { value: 0x08, enumerable: true },
    DOCUMENT_POSITION_CONTAINED_BY: { value: 0x10, enumerable: true },
    DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC: { value: 0x20, enumerable: true }
  });
  ctorRegistry[interfaceName] = Node;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: Node
  });
};

const Impl = require("../../jsdom/living/nodes/Node-impl.js");
