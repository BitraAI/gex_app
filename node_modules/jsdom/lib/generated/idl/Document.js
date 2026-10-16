"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const ElementCreationOptions = require("./ElementCreationOptions.js");
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const Node = require("./Node.js");
const NodeFilter = require("./NodeFilter.js");
const HTMLElement = require("./HTMLElement.js");
const EventHandlerNonNull = require("./EventHandlerNonNull.js");
const OnErrorEventHandlerNonNull = require("./OnErrorEventHandlerNonNull.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;

const interfaceName = "Document";

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
  throw new globalObject.TypeError(`${context} is not of type 'Document'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["Document"].prototype;
  }

  return Object.create(proto);
}

function makeProxy(wrapper, impl, globalObject) {
  let proxyHandler = proxyHandlerCache.get(globalObject);
  if (proxyHandler === undefined) {
    proxyHandler = new ProxyHandler(globalObject);
    proxyHandlerCache.set(globalObject, proxyHandler);
  }
  // The target needs an implementation for proxy traps, but only the final proxy gets the interface brand.
  utils.registerWrapper(wrapper, impl, undefined);
  return new Proxy(wrapper, proxyHandler);
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
      get location() {
        const $impl = $requireImpl(this ?? globalObject, globalObject, "get location");
        return utils.tryWrapperForImpl($impl["location"]);
      },
      set location(V) {
        const esValue = this ?? globalObject;
        const $impl = $requireImpl(this ?? globalObject, globalObject, "set location");

        const Q = esValue["location"];
        if (!utils.isObject(Q)) {
          throw new globalObject.TypeError("Property 'location' is not an object");
        }
        Reflect.set(Q, "href", V);
      }
    });
    Object.defineProperties(unforgeables, {
      location: { configurable: false }
    });
    unforgeablesMap.set(globalObject, unforgeables);
  }
  return unforgeables;
}

exports._internalSetup = (wrapper, globalObject) => {
  Node._internalSetup(wrapper, globalObject);

  utils.define(wrapper, getUnforgeables(globalObject));
};

exports.setup = (wrapper, globalObject, constructorArgs = [], privateData = {}) => {
  privateData.wrapper = wrapper;

  exports._internalSetup(wrapper, globalObject);
  const impl = new Impl.implementation(globalObject, constructorArgs, privateData);

  wrapper = makeProxy(wrapper, impl, globalObject);

  utils.registerWrapper(wrapper, impl, $interfaceDescriptor);
  impl[utils.wrapperSymbol] = wrapper;
  if (Impl.init) {
    Impl.init(impl);
  }
  return wrapper;
};

exports.new = (globalObject, newTarget) => {
  let wrapper = makeWrapper(globalObject, newTarget);

  exports._internalSetup(wrapper, globalObject);
  const impl = Object.create(Impl.implementation.prototype);

  wrapper = makeProxy(wrapper, impl, globalObject);

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
  class Document extends globalObject.Node {
    constructor() {
      return exports.setup(Object.create(new.target.prototype), globalObject, undefined);
    }

    getElementsByTagName(qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getElementsByTagName");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getElementsByTagName' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementsByTagName' on 'Document': parameter 1",
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
          `Failed to execute 'getElementsByTagNameNS' on 'Document': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'getElementsByTagNameNS' on 'Document': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementsByTagNameNS' on 'Document': parameter 2",
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
          `Failed to execute 'getElementsByClassName' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementsByClassName' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getElementsByClassName(...args));
    }

    createElement(localName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createElement");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createElement' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createElement' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = ElementCreationOptions.convert(globalObject, curArg, {
              context: "Failed to execute 'createElement' on 'Document': parameter 2"
            });
          } else if (utils.isObject(curArg)) {
            curArg = ElementCreationOptions.convert(globalObject, curArg, {
              context: "Failed to execute 'createElement' on 'Document': parameter 2" + " dictionary"
            });
          } else {
            curArg = conversions["DOMString"](curArg, {
              context: "Failed to execute 'createElement' on 'Document': parameter 2",
              globals: globalObject
            });
          }
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.createElement(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    createElementNS(namespace, qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createElementNS");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'createElementNS' on 'Document': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'createElementNS' on 'Document': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createElementNS' on 'Document': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[2];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = ElementCreationOptions.convert(globalObject, curArg, {
              context: "Failed to execute 'createElementNS' on 'Document': parameter 3"
            });
          } else if (utils.isObject(curArg)) {
            curArg = ElementCreationOptions.convert(globalObject, curArg, {
              context: "Failed to execute 'createElementNS' on 'Document': parameter 3" + " dictionary"
            });
          } else {
            curArg = conversions["DOMString"](curArg, {
              context: "Failed to execute 'createElementNS' on 'Document': parameter 3",
              globals: globalObject
            });
          }
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.createElementNS(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    createDocumentFragment() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createDocumentFragment");
      return utils.tryWrapperForImpl($impl.createDocumentFragment());
    }

    createTextNode(data) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createTextNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createTextNode' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createTextNode' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createTextNode(...args));
    }

    createCDATASection(data) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createCDATASection");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createCDATASection' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createCDATASection' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createCDATASection(...args));
    }

    createComment(data) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createComment");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createComment' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createComment' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createComment(...args));
    }

    createProcessingInstruction(target, data) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createProcessingInstruction");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'createProcessingInstruction' on 'Document': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createProcessingInstruction' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createProcessingInstruction' on 'Document': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createProcessingInstruction(...args));
    }

    importNode(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "importNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'importNode' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'importNode' on 'Document': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["boolean"](curArg, {
            context: "Failed to execute 'importNode' on 'Document': parameter 2",
            globals: globalObject
          });
        } else {
          curArg = false;
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.importNode(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    adoptNode(node) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "adoptNode");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'adoptNode' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'adoptNode' on 'Document': parameter 1"
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.adoptNode(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    createAttribute(localName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createAttribute");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createAttribute' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createAttribute' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createAttribute(...args));
    }

    createAttributeNS(namespace, qualifiedName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createAttributeNS");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'createAttributeNS' on 'Document': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg === null || curArg === undefined) {
          curArg = null;
        } else {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'createAttributeNS' on 'Document': parameter 1",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createAttributeNS' on 'Document': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createAttributeNS(...args));
    }

    createEvent(interface_) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createEvent");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createEvent' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'createEvent' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createEvent(...args));
    }

    createRange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createRange");
      return utils.tryWrapperForImpl($impl.createRange());
    }

    createNodeIterator(root) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createNodeIterator");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createNodeIterator' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'createNodeIterator' on 'Document': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["unsigned long"](curArg, {
            context: "Failed to execute 'createNodeIterator' on 'Document': parameter 2",
            globals: globalObject
          });
        } else {
          curArg = 0xffffffff;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[2];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = null;
          } else {
            curArg = NodeFilter.convert(globalObject, curArg, {
              context: "Failed to execute 'createNodeIterator' on 'Document': parameter 3"
            });
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createNodeIterator(...args));
    }

    createTreeWalker(root) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createTreeWalker");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'createTreeWalker' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = Node.convert(globalObject, curArg, {
          context: "Failed to execute 'createTreeWalker' on 'Document': parameter 1"
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["unsigned long"](curArg, {
            context: "Failed to execute 'createTreeWalker' on 'Document': parameter 2",
            globals: globalObject
          });
        } else {
          curArg = 0xffffffff;
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[2];
        if (curArg !== undefined) {
          if (curArg === null || curArg === undefined) {
            curArg = null;
          } else {
            curArg = NodeFilter.convert(globalObject, curArg, {
              context: "Failed to execute 'createTreeWalker' on 'Document': parameter 3"
            });
          }
        } else {
          curArg = null;
        }
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.createTreeWalker(...args));
    }

    getElementsByName(elementName) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getElementsByName");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getElementsByName' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementsByName' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.getElementsByName(...args));
    }

    open() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "open");
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg !== undefined) {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'open' on 'Document': parameter 1",
            globals: globalObject
          });
        } else {
          curArg = "text/html";
        }
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        if (curArg !== undefined) {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'open' on 'Document': parameter 2",
            globals: globalObject
          });
        } else {
          curArg = "";
        }
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl.open(...args));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    close() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "close");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.close();
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    write() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "write");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'write' on 'Document': parameter " + (i + 1),
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.write(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    writeln() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "writeln");
      const args = [];
      for (let i = 0; i < arguments.length; i++) {
        let curArg = arguments[i];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'writeln' on 'Document': parameter " + (i + 1),
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.writeln(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    hasFocus() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "hasFocus");
      return $impl.hasFocus();
    }

    clear() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "clear");
      return $impl.clear();
    }

    captureEvents() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "captureEvents");
      return $impl.captureEvents();
    }

    releaseEvents() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "releaseEvents");
      return $impl.releaseEvents();
    }

    getSelection() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getSelection");
      return utils.tryWrapperForImpl($impl.getSelection());
    }

    getElementById(elementId) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "getElementById");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'getElementById' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'getElementById' on 'Document': parameter 1",
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
            context: "Failed to execute 'prepend' on 'Document': parameter " + (i + 1),
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
            context: "Failed to execute 'append' on 'Document': parameter " + (i + 1),
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
            context: "Failed to execute 'replaceChildren' on 'Document': parameter " + (i + 1),
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
          `Failed to execute 'querySelector' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'querySelector' on 'Document': parameter 1",
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
          `Failed to execute 'querySelectorAll' on 'Document': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'querySelectorAll' on 'Document': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.querySelectorAll(...args));
    }

    get implementation() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get implementation");
      return utils.getSameObject(this, "implementation", () => {
        return utils.tryWrapperForImpl($impl["implementation"]);
      });
    }

    get URL() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get URL");
      return $impl["URL"];
    }

    get documentURI() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get documentURI");
      return $impl["documentURI"];
    }

    get compatMode() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get compatMode");
      return $impl["compatMode"];
    }

    get characterSet() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get characterSet");
      return $impl["characterSet"];
    }

    get charset() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get charset");
      return $impl["charset"];
    }

    get inputEncoding() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get inputEncoding");
      return $impl["inputEncoding"];
    }

    get contentType() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get contentType");
      return $impl["contentType"];
    }

    get doctype() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get doctype");
      return utils.tryWrapperForImpl($impl["doctype"]);
    }

    get documentElement() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get documentElement");
      return utils.tryWrapperForImpl($impl["documentElement"]);
    }

    get referrer() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get referrer");
      return $impl["referrer"];
    }

    get cookie() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get cookie");
      return $impl["cookie"];
    }

    set cookie(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set cookie");

      V = conversions["USVString"](V, {
        context: "Failed to set the 'cookie' property on 'Document': The provided value",
        globals: globalObject
      });

      $impl["cookie"] = V;
    }

    get lastModified() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get lastModified");
      return $impl["lastModified"];
    }

    get readyState() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get readyState");
      return utils.tryWrapperForImpl($impl["readyState"]);
    }

    get title() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get title");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["title"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set title(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set title");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'title' property on 'Document': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["title"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get dir() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get dir");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["dir"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set dir(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set dir");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'dir' property on 'Document': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["dir"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get body() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get body");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl["body"]);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set body(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set body");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = HTMLElement.convert(globalObject, V, {
          context: "Failed to set the 'body' property on 'Document': The provided value"
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["body"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get head() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get head");
      return utils.tryWrapperForImpl($impl["head"]);
    }

    get images() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get images");
      return utils.getSameObject(this, "images", () => {
        return utils.tryWrapperForImpl($impl["images"]);
      });
    }

    get embeds() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get embeds");
      return utils.getSameObject(this, "embeds", () => {
        return utils.tryWrapperForImpl($impl["embeds"]);
      });
    }

    get plugins() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get plugins");
      return utils.getSameObject(this, "plugins", () => {
        return utils.tryWrapperForImpl($impl["plugins"]);
      });
    }

    get links() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get links");
      return utils.getSameObject(this, "links", () => {
        return utils.tryWrapperForImpl($impl["links"]);
      });
    }

    get forms() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get forms");
      return utils.getSameObject(this, "forms", () => {
        return utils.tryWrapperForImpl($impl["forms"]);
      });
    }

    get scripts() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get scripts");
      return utils.getSameObject(this, "scripts", () => {
        return utils.tryWrapperForImpl($impl["scripts"]);
      });
    }

    get currentScript() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get currentScript");
      return utils.tryWrapperForImpl($impl["currentScript"]);
    }

    get defaultView() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get defaultView");
      return utils.tryWrapperForImpl($impl["defaultView"]);
    }

    get onreadystatechange() {
      const $impl = utils.implForWrapperWithInterface(this ?? globalObject, $interfaceDescriptor);
      if ($impl === null) {
        return;
      }

      return utils.tryWrapperForImpl($impl["onreadystatechange"]);
    }

    set onreadystatechange(V) {
      const $impl = utils.implForWrapperWithInterface(this ?? globalObject, $interfaceDescriptor);
      if ($impl === null) {
        return;
      }

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onreadystatechange' property on 'Document': The provided value"
        });
      }
      $impl["onreadystatechange"] = V;
    }

    get anchors() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get anchors");
      return utils.getSameObject(this, "anchors", () => {
        return utils.tryWrapperForImpl($impl["anchors"]);
      });
    }

    get applets() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get applets");
      return utils.getSameObject(this, "applets", () => {
        return utils.tryWrapperForImpl($impl["applets"]);
      });
    }

    get styleSheets() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get styleSheets");
      return utils.getSameObject(this, "styleSheets", () => {
        return utils.tryWrapperForImpl($impl["styleSheets"]);
      });
    }

    get hidden() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get hidden");
      return $impl["hidden"];
    }

    get visibilityState() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get visibilityState");
      return utils.tryWrapperForImpl($impl["visibilityState"]);
    }

    get onvisibilitychange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onvisibilitychange");
      return utils.tryWrapperForImpl($impl["onvisibilitychange"]);
    }

    set onvisibilitychange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onvisibilitychange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onvisibilitychange' property on 'Document': The provided value"
        });
      }
      $impl["onvisibilitychange"] = V;
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
          context: "Failed to set the 'onabort' property on 'Document': The provided value"
        });
      }
      $impl["onabort"] = V;
    }

    get onauxclick() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onauxclick");
      return utils.tryWrapperForImpl($impl["onauxclick"]);
    }

    set onauxclick(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onauxclick");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onauxclick' property on 'Document': The provided value"
        });
      }
      $impl["onauxclick"] = V;
    }

    get onbeforeinput() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onbeforeinput");
      return utils.tryWrapperForImpl($impl["onbeforeinput"]);
    }

    set onbeforeinput(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onbeforeinput");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onbeforeinput' property on 'Document': The provided value"
        });
      }
      $impl["onbeforeinput"] = V;
    }

    get onbeforematch() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onbeforematch");
      return utils.tryWrapperForImpl($impl["onbeforematch"]);
    }

    set onbeforematch(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onbeforematch");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onbeforematch' property on 'Document': The provided value"
        });
      }
      $impl["onbeforematch"] = V;
    }

    get onbeforetoggle() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onbeforetoggle");
      return utils.tryWrapperForImpl($impl["onbeforetoggle"]);
    }

    set onbeforetoggle(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onbeforetoggle");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onbeforetoggle' property on 'Document': The provided value"
        });
      }
      $impl["onbeforetoggle"] = V;
    }

    get onblur() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onblur");
      return utils.tryWrapperForImpl($impl["onblur"]);
    }

    set onblur(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onblur");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onblur' property on 'Document': The provided value"
        });
      }
      $impl["onblur"] = V;
    }

    get oncancel() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncancel");
      return utils.tryWrapperForImpl($impl["oncancel"]);
    }

    set oncancel(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncancel");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncancel' property on 'Document': The provided value"
        });
      }
      $impl["oncancel"] = V;
    }

    get oncanplay() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncanplay");
      return utils.tryWrapperForImpl($impl["oncanplay"]);
    }

    set oncanplay(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncanplay");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncanplay' property on 'Document': The provided value"
        });
      }
      $impl["oncanplay"] = V;
    }

    get oncanplaythrough() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncanplaythrough");
      return utils.tryWrapperForImpl($impl["oncanplaythrough"]);
    }

    set oncanplaythrough(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncanplaythrough");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncanplaythrough' property on 'Document': The provided value"
        });
      }
      $impl["oncanplaythrough"] = V;
    }

    get onchange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onchange");
      return utils.tryWrapperForImpl($impl["onchange"]);
    }

    set onchange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onchange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onchange' property on 'Document': The provided value"
        });
      }
      $impl["onchange"] = V;
    }

    get onclick() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onclick");
      return utils.tryWrapperForImpl($impl["onclick"]);
    }

    set onclick(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onclick");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onclick' property on 'Document': The provided value"
        });
      }
      $impl["onclick"] = V;
    }

    get onclose() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onclose");
      return utils.tryWrapperForImpl($impl["onclose"]);
    }

    set onclose(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onclose");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onclose' property on 'Document': The provided value"
        });
      }
      $impl["onclose"] = V;
    }

    get oncontextlost() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncontextlost");
      return utils.tryWrapperForImpl($impl["oncontextlost"]);
    }

    set oncontextlost(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncontextlost");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncontextlost' property on 'Document': The provided value"
        });
      }
      $impl["oncontextlost"] = V;
    }

    get oncontextmenu() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncontextmenu");
      return utils.tryWrapperForImpl($impl["oncontextmenu"]);
    }

    set oncontextmenu(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncontextmenu");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncontextmenu' property on 'Document': The provided value"
        });
      }
      $impl["oncontextmenu"] = V;
    }

    get oncontextrestored() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncontextrestored");
      return utils.tryWrapperForImpl($impl["oncontextrestored"]);
    }

    set oncontextrestored(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncontextrestored");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncontextrestored' property on 'Document': The provided value"
        });
      }
      $impl["oncontextrestored"] = V;
    }

    get oncopy() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncopy");
      return utils.tryWrapperForImpl($impl["oncopy"]);
    }

    set oncopy(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncopy");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncopy' property on 'Document': The provided value"
        });
      }
      $impl["oncopy"] = V;
    }

    get oncuechange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncuechange");
      return utils.tryWrapperForImpl($impl["oncuechange"]);
    }

    set oncuechange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncuechange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncuechange' property on 'Document': The provided value"
        });
      }
      $impl["oncuechange"] = V;
    }

    get oncut() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oncut");
      return utils.tryWrapperForImpl($impl["oncut"]);
    }

    set oncut(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oncut");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oncut' property on 'Document': The provided value"
        });
      }
      $impl["oncut"] = V;
    }

    get ondblclick() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondblclick");
      return utils.tryWrapperForImpl($impl["ondblclick"]);
    }

    set ondblclick(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondblclick");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondblclick' property on 'Document': The provided value"
        });
      }
      $impl["ondblclick"] = V;
    }

    get ondrag() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondrag");
      return utils.tryWrapperForImpl($impl["ondrag"]);
    }

    set ondrag(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondrag");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondrag' property on 'Document': The provided value"
        });
      }
      $impl["ondrag"] = V;
    }

    get ondragend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondragend");
      return utils.tryWrapperForImpl($impl["ondragend"]);
    }

    set ondragend(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondragend");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondragend' property on 'Document': The provided value"
        });
      }
      $impl["ondragend"] = V;
    }

    get ondragenter() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondragenter");
      return utils.tryWrapperForImpl($impl["ondragenter"]);
    }

    set ondragenter(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondragenter");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondragenter' property on 'Document': The provided value"
        });
      }
      $impl["ondragenter"] = V;
    }

    get ondragleave() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondragleave");
      return utils.tryWrapperForImpl($impl["ondragleave"]);
    }

    set ondragleave(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondragleave");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondragleave' property on 'Document': The provided value"
        });
      }
      $impl["ondragleave"] = V;
    }

    get ondragover() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondragover");
      return utils.tryWrapperForImpl($impl["ondragover"]);
    }

    set ondragover(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondragover");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondragover' property on 'Document': The provided value"
        });
      }
      $impl["ondragover"] = V;
    }

    get ondragstart() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondragstart");
      return utils.tryWrapperForImpl($impl["ondragstart"]);
    }

    set ondragstart(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondragstart");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondragstart' property on 'Document': The provided value"
        });
      }
      $impl["ondragstart"] = V;
    }

    get ondrop() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondrop");
      return utils.tryWrapperForImpl($impl["ondrop"]);
    }

    set ondrop(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondrop");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondrop' property on 'Document': The provided value"
        });
      }
      $impl["ondrop"] = V;
    }

    get ondurationchange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ondurationchange");
      return utils.tryWrapperForImpl($impl["ondurationchange"]);
    }

    set ondurationchange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ondurationchange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ondurationchange' property on 'Document': The provided value"
        });
      }
      $impl["ondurationchange"] = V;
    }

    get onemptied() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onemptied");
      return utils.tryWrapperForImpl($impl["onemptied"]);
    }

    set onemptied(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onemptied");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onemptied' property on 'Document': The provided value"
        });
      }
      $impl["onemptied"] = V;
    }

    get onended() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onended");
      return utils.tryWrapperForImpl($impl["onended"]);
    }

    set onended(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onended");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onended' property on 'Document': The provided value"
        });
      }
      $impl["onended"] = V;
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
        V = OnErrorEventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onerror' property on 'Document': The provided value"
        });
      }
      $impl["onerror"] = V;
    }

    get onfocus() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onfocus");
      return utils.tryWrapperForImpl($impl["onfocus"]);
    }

    set onfocus(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onfocus");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onfocus' property on 'Document': The provided value"
        });
      }
      $impl["onfocus"] = V;
    }

    get onformdata() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onformdata");
      return utils.tryWrapperForImpl($impl["onformdata"]);
    }

    set onformdata(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onformdata");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onformdata' property on 'Document': The provided value"
        });
      }
      $impl["onformdata"] = V;
    }

    get oninput() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oninput");
      return utils.tryWrapperForImpl($impl["oninput"]);
    }

    set oninput(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oninput");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oninput' property on 'Document': The provided value"
        });
      }
      $impl["oninput"] = V;
    }

    get oninvalid() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get oninvalid");
      return utils.tryWrapperForImpl($impl["oninvalid"]);
    }

    set oninvalid(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set oninvalid");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'oninvalid' property on 'Document': The provided value"
        });
      }
      $impl["oninvalid"] = V;
    }

    get onkeydown() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onkeydown");
      return utils.tryWrapperForImpl($impl["onkeydown"]);
    }

    set onkeydown(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onkeydown");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onkeydown' property on 'Document': The provided value"
        });
      }
      $impl["onkeydown"] = V;
    }

    get onkeypress() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onkeypress");
      return utils.tryWrapperForImpl($impl["onkeypress"]);
    }

    set onkeypress(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onkeypress");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onkeypress' property on 'Document': The provided value"
        });
      }
      $impl["onkeypress"] = V;
    }

    get onkeyup() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onkeyup");
      return utils.tryWrapperForImpl($impl["onkeyup"]);
    }

    set onkeyup(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onkeyup");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onkeyup' property on 'Document': The provided value"
        });
      }
      $impl["onkeyup"] = V;
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
          context: "Failed to set the 'onload' property on 'Document': The provided value"
        });
      }
      $impl["onload"] = V;
    }

    get onloadeddata() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onloadeddata");
      return utils.tryWrapperForImpl($impl["onloadeddata"]);
    }

    set onloadeddata(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onloadeddata");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onloadeddata' property on 'Document': The provided value"
        });
      }
      $impl["onloadeddata"] = V;
    }

    get onloadedmetadata() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onloadedmetadata");
      return utils.tryWrapperForImpl($impl["onloadedmetadata"]);
    }

    set onloadedmetadata(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onloadedmetadata");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onloadedmetadata' property on 'Document': The provided value"
        });
      }
      $impl["onloadedmetadata"] = V;
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
          context: "Failed to set the 'onloadstart' property on 'Document': The provided value"
        });
      }
      $impl["onloadstart"] = V;
    }

    get onmousedown() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onmousedown");
      return utils.tryWrapperForImpl($impl["onmousedown"]);
    }

    set onmousedown(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onmousedown");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmousedown' property on 'Document': The provided value"
        });
      }
      $impl["onmousedown"] = V;
    }

    get onmouseenter() {
      const $impl = utils.implForWrapperWithInterface(this ?? globalObject, $interfaceDescriptor);
      if ($impl === null) {
        return;
      }

      return utils.tryWrapperForImpl($impl["onmouseenter"]);
    }

    set onmouseenter(V) {
      const $impl = utils.implForWrapperWithInterface(this ?? globalObject, $interfaceDescriptor);
      if ($impl === null) {
        return;
      }

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmouseenter' property on 'Document': The provided value"
        });
      }
      $impl["onmouseenter"] = V;
    }

    get onmouseleave() {
      const $impl = utils.implForWrapperWithInterface(this ?? globalObject, $interfaceDescriptor);
      if ($impl === null) {
        return;
      }

      return utils.tryWrapperForImpl($impl["onmouseleave"]);
    }

    set onmouseleave(V) {
      const $impl = utils.implForWrapperWithInterface(this ?? globalObject, $interfaceDescriptor);
      if ($impl === null) {
        return;
      }

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmouseleave' property on 'Document': The provided value"
        });
      }
      $impl["onmouseleave"] = V;
    }

    get onmousemove() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onmousemove");
      return utils.tryWrapperForImpl($impl["onmousemove"]);
    }

    set onmousemove(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onmousemove");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmousemove' property on 'Document': The provided value"
        });
      }
      $impl["onmousemove"] = V;
    }

    get onmouseout() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onmouseout");
      return utils.tryWrapperForImpl($impl["onmouseout"]);
    }

    set onmouseout(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onmouseout");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmouseout' property on 'Document': The provided value"
        });
      }
      $impl["onmouseout"] = V;
    }

    get onmouseover() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onmouseover");
      return utils.tryWrapperForImpl($impl["onmouseover"]);
    }

    set onmouseover(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onmouseover");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmouseover' property on 'Document': The provided value"
        });
      }
      $impl["onmouseover"] = V;
    }

    get onmouseup() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onmouseup");
      return utils.tryWrapperForImpl($impl["onmouseup"]);
    }

    set onmouseup(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onmouseup");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onmouseup' property on 'Document': The provided value"
        });
      }
      $impl["onmouseup"] = V;
    }

    get onpaste() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpaste");
      return utils.tryWrapperForImpl($impl["onpaste"]);
    }

    set onpaste(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpaste");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpaste' property on 'Document': The provided value"
        });
      }
      $impl["onpaste"] = V;
    }

    get onpause() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpause");
      return utils.tryWrapperForImpl($impl["onpause"]);
    }

    set onpause(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpause");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpause' property on 'Document': The provided value"
        });
      }
      $impl["onpause"] = V;
    }

    get onplay() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onplay");
      return utils.tryWrapperForImpl($impl["onplay"]);
    }

    set onplay(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onplay");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onplay' property on 'Document': The provided value"
        });
      }
      $impl["onplay"] = V;
    }

    get onplaying() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onplaying");
      return utils.tryWrapperForImpl($impl["onplaying"]);
    }

    set onplaying(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onplaying");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onplaying' property on 'Document': The provided value"
        });
      }
      $impl["onplaying"] = V;
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
          context: "Failed to set the 'onprogress' property on 'Document': The provided value"
        });
      }
      $impl["onprogress"] = V;
    }

    get onratechange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onratechange");
      return utils.tryWrapperForImpl($impl["onratechange"]);
    }

    set onratechange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onratechange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onratechange' property on 'Document': The provided value"
        });
      }
      $impl["onratechange"] = V;
    }

    get onreset() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onreset");
      return utils.tryWrapperForImpl($impl["onreset"]);
    }

    set onreset(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onreset");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onreset' property on 'Document': The provided value"
        });
      }
      $impl["onreset"] = V;
    }

    get onresize() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onresize");
      return utils.tryWrapperForImpl($impl["onresize"]);
    }

    set onresize(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onresize");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onresize' property on 'Document': The provided value"
        });
      }
      $impl["onresize"] = V;
    }

    get onscroll() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onscroll");
      return utils.tryWrapperForImpl($impl["onscroll"]);
    }

    set onscroll(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onscroll");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onscroll' property on 'Document': The provided value"
        });
      }
      $impl["onscroll"] = V;
    }

    get onscrollend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onscrollend");
      return utils.tryWrapperForImpl($impl["onscrollend"]);
    }

    set onscrollend(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onscrollend");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onscrollend' property on 'Document': The provided value"
        });
      }
      $impl["onscrollend"] = V;
    }

    get onsecuritypolicyviolation() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onsecuritypolicyviolation");
      return utils.tryWrapperForImpl($impl["onsecuritypolicyviolation"]);
    }

    set onsecuritypolicyviolation(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onsecuritypolicyviolation");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onsecuritypolicyviolation' property on 'Document': The provided value"
        });
      }
      $impl["onsecuritypolicyviolation"] = V;
    }

    get onseeked() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onseeked");
      return utils.tryWrapperForImpl($impl["onseeked"]);
    }

    set onseeked(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onseeked");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onseeked' property on 'Document': The provided value"
        });
      }
      $impl["onseeked"] = V;
    }

    get onseeking() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onseeking");
      return utils.tryWrapperForImpl($impl["onseeking"]);
    }

    set onseeking(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onseeking");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onseeking' property on 'Document': The provided value"
        });
      }
      $impl["onseeking"] = V;
    }

    get onselect() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onselect");
      return utils.tryWrapperForImpl($impl["onselect"]);
    }

    set onselect(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onselect");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onselect' property on 'Document': The provided value"
        });
      }
      $impl["onselect"] = V;
    }

    get onslotchange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onslotchange");
      return utils.tryWrapperForImpl($impl["onslotchange"]);
    }

    set onslotchange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onslotchange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onslotchange' property on 'Document': The provided value"
        });
      }
      $impl["onslotchange"] = V;
    }

    get onstalled() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onstalled");
      return utils.tryWrapperForImpl($impl["onstalled"]);
    }

    set onstalled(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onstalled");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onstalled' property on 'Document': The provided value"
        });
      }
      $impl["onstalled"] = V;
    }

    get onsubmit() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onsubmit");
      return utils.tryWrapperForImpl($impl["onsubmit"]);
    }

    set onsubmit(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onsubmit");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onsubmit' property on 'Document': The provided value"
        });
      }
      $impl["onsubmit"] = V;
    }

    get onsuspend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onsuspend");
      return utils.tryWrapperForImpl($impl["onsuspend"]);
    }

    set onsuspend(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onsuspend");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onsuspend' property on 'Document': The provided value"
        });
      }
      $impl["onsuspend"] = V;
    }

    get ontimeupdate() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ontimeupdate");
      return utils.tryWrapperForImpl($impl["ontimeupdate"]);
    }

    set ontimeupdate(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ontimeupdate");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ontimeupdate' property on 'Document': The provided value"
        });
      }
      $impl["ontimeupdate"] = V;
    }

    get ontoggle() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ontoggle");
      return utils.tryWrapperForImpl($impl["ontoggle"]);
    }

    set ontoggle(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ontoggle");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ontoggle' property on 'Document': The provided value"
        });
      }
      $impl["ontoggle"] = V;
    }

    get onvolumechange() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onvolumechange");
      return utils.tryWrapperForImpl($impl["onvolumechange"]);
    }

    set onvolumechange(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onvolumechange");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onvolumechange' property on 'Document': The provided value"
        });
      }
      $impl["onvolumechange"] = V;
    }

    get onwaiting() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onwaiting");
      return utils.tryWrapperForImpl($impl["onwaiting"]);
    }

    set onwaiting(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onwaiting");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onwaiting' property on 'Document': The provided value"
        });
      }
      $impl["onwaiting"] = V;
    }

    get onwebkitanimationend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onwebkitanimationend");
      return utils.tryWrapperForImpl($impl["onwebkitanimationend"]);
    }

    set onwebkitanimationend(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onwebkitanimationend");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onwebkitanimationend' property on 'Document': The provided value"
        });
      }
      $impl["onwebkitanimationend"] = V;
    }

    get onwebkitanimationiteration() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onwebkitanimationiteration");
      return utils.tryWrapperForImpl($impl["onwebkitanimationiteration"]);
    }

    set onwebkitanimationiteration(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onwebkitanimationiteration");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onwebkitanimationiteration' property on 'Document': The provided value"
        });
      }
      $impl["onwebkitanimationiteration"] = V;
    }

    get onwebkitanimationstart() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onwebkitanimationstart");
      return utils.tryWrapperForImpl($impl["onwebkitanimationstart"]);
    }

    set onwebkitanimationstart(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onwebkitanimationstart");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onwebkitanimationstart' property on 'Document': The provided value"
        });
      }
      $impl["onwebkitanimationstart"] = V;
    }

    get onwebkittransitionend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onwebkittransitionend");
      return utils.tryWrapperForImpl($impl["onwebkittransitionend"]);
    }

    set onwebkittransitionend(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onwebkittransitionend");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onwebkittransitionend' property on 'Document': The provided value"
        });
      }
      $impl["onwebkittransitionend"] = V;
    }

    get onwheel() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onwheel");
      return utils.tryWrapperForImpl($impl["onwheel"]);
    }

    set onwheel(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onwheel");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onwheel' property on 'Document': The provided value"
        });
      }
      $impl["onwheel"] = V;
    }

    get ontouchstart() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ontouchstart");
      return utils.tryWrapperForImpl($impl["ontouchstart"]);
    }

    set ontouchstart(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ontouchstart");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ontouchstart' property on 'Document': The provided value"
        });
      }
      $impl["ontouchstart"] = V;
    }

    get ontouchend() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ontouchend");
      return utils.tryWrapperForImpl($impl["ontouchend"]);
    }

    set ontouchend(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ontouchend");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ontouchend' property on 'Document': The provided value"
        });
      }
      $impl["ontouchend"] = V;
    }

    get ontouchmove() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ontouchmove");
      return utils.tryWrapperForImpl($impl["ontouchmove"]);
    }

    set ontouchmove(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ontouchmove");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ontouchmove' property on 'Document': The provided value"
        });
      }
      $impl["ontouchmove"] = V;
    }

    get ontouchcancel() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ontouchcancel");
      return utils.tryWrapperForImpl($impl["ontouchcancel"]);
    }

    set ontouchcancel(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ontouchcancel");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ontouchcancel' property on 'Document': The provided value"
        });
      }
      $impl["ontouchcancel"] = V;
    }

    get onpointerover() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointerover");
      return utils.tryWrapperForImpl($impl["onpointerover"]);
    }

    set onpointerover(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointerover");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointerover' property on 'Document': The provided value"
        });
      }
      $impl["onpointerover"] = V;
    }

    get onpointerenter() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointerenter");
      return utils.tryWrapperForImpl($impl["onpointerenter"]);
    }

    set onpointerenter(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointerenter");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointerenter' property on 'Document': The provided value"
        });
      }
      $impl["onpointerenter"] = V;
    }

    get onpointerdown() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointerdown");
      return utils.tryWrapperForImpl($impl["onpointerdown"]);
    }

    set onpointerdown(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointerdown");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointerdown' property on 'Document': The provided value"
        });
      }
      $impl["onpointerdown"] = V;
    }

    get onpointermove() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointermove");
      return utils.tryWrapperForImpl($impl["onpointermove"]);
    }

    set onpointermove(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointermove");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointermove' property on 'Document': The provided value"
        });
      }
      $impl["onpointermove"] = V;
    }

    get onpointerrawupdate() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointerrawupdate");
      return utils.tryWrapperForImpl($impl["onpointerrawupdate"]);
    }

    set onpointerrawupdate(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointerrawupdate");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointerrawupdate' property on 'Document': The provided value"
        });
      }
      $impl["onpointerrawupdate"] = V;
    }

    get onpointerup() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointerup");
      return utils.tryWrapperForImpl($impl["onpointerup"]);
    }

    set onpointerup(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointerup");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointerup' property on 'Document': The provided value"
        });
      }
      $impl["onpointerup"] = V;
    }

    get onpointercancel() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointercancel");
      return utils.tryWrapperForImpl($impl["onpointercancel"]);
    }

    set onpointercancel(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointercancel");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointercancel' property on 'Document': The provided value"
        });
      }
      $impl["onpointercancel"] = V;
    }

    get onpointerout() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointerout");
      return utils.tryWrapperForImpl($impl["onpointerout"]);
    }

    set onpointerout(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointerout");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointerout' property on 'Document': The provided value"
        });
      }
      $impl["onpointerout"] = V;
    }

    get onpointerleave() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onpointerleave");
      return utils.tryWrapperForImpl($impl["onpointerleave"]);
    }

    set onpointerleave(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onpointerleave");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onpointerleave' property on 'Document': The provided value"
        });
      }
      $impl["onpointerleave"] = V;
    }

    get ongotpointercapture() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get ongotpointercapture");
      return utils.tryWrapperForImpl($impl["ongotpointercapture"]);
    }

    set ongotpointercapture(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set ongotpointercapture");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'ongotpointercapture' property on 'Document': The provided value"
        });
      }
      $impl["ongotpointercapture"] = V;
    }

    get onlostpointercapture() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get onlostpointercapture");
      return utils.tryWrapperForImpl($impl["onlostpointercapture"]);
    }

    set onlostpointercapture(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set onlostpointercapture");

      if (!utils.isObject(V)) {
        V = null;
      } else {
        V = EventHandlerNonNull.convert(globalObject, V, {
          context: "Failed to set the 'onlostpointercapture' property on 'Document': The provided value"
        });
      }
      $impl["onlostpointercapture"] = V;
    }

    get activeElement() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get activeElement");
      return utils.tryWrapperForImpl($impl["activeElement"]);
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
  Object.defineProperties(Document.prototype, {
    getElementsByTagName: { enumerable: true },
    getElementsByTagNameNS: { enumerable: true },
    getElementsByClassName: { enumerable: true },
    createElement: { enumerable: true },
    createElementNS: { enumerable: true },
    createDocumentFragment: { enumerable: true },
    createTextNode: { enumerable: true },
    createCDATASection: { enumerable: true },
    createComment: { enumerable: true },
    createProcessingInstruction: { enumerable: true },
    importNode: { enumerable: true },
    adoptNode: { enumerable: true },
    createAttribute: { enumerable: true },
    createAttributeNS: { enumerable: true },
    createEvent: { enumerable: true },
    createRange: { enumerable: true },
    createNodeIterator: { enumerable: true },
    createTreeWalker: { enumerable: true },
    getElementsByName: { enumerable: true },
    open: { enumerable: true },
    close: { enumerable: true },
    write: { enumerable: true },
    writeln: { enumerable: true },
    hasFocus: { enumerable: true },
    clear: { enumerable: true },
    captureEvents: { enumerable: true },
    releaseEvents: { enumerable: true },
    getSelection: { enumerable: true },
    getElementById: { enumerable: true },
    prepend: { enumerable: true },
    append: { enumerable: true },
    replaceChildren: { enumerable: true },
    querySelector: { enumerable: true },
    querySelectorAll: { enumerable: true },
    implementation: { enumerable: true },
    URL: { enumerable: true },
    documentURI: { enumerable: true },
    compatMode: { enumerable: true },
    characterSet: { enumerable: true },
    charset: { enumerable: true },
    inputEncoding: { enumerable: true },
    contentType: { enumerable: true },
    doctype: { enumerable: true },
    documentElement: { enumerable: true },
    referrer: { enumerable: true },
    cookie: { enumerable: true },
    lastModified: { enumerable: true },
    readyState: { enumerable: true },
    title: { enumerable: true },
    dir: { enumerable: true },
    body: { enumerable: true },
    head: { enumerable: true },
    images: { enumerable: true },
    embeds: { enumerable: true },
    plugins: { enumerable: true },
    links: { enumerable: true },
    forms: { enumerable: true },
    scripts: { enumerable: true },
    currentScript: { enumerable: true },
    defaultView: { enumerable: true },
    onreadystatechange: { enumerable: true },
    anchors: { enumerable: true },
    applets: { enumerable: true },
    styleSheets: { enumerable: true },
    hidden: { enumerable: true },
    visibilityState: { enumerable: true },
    onvisibilitychange: { enumerable: true },
    onabort: { enumerable: true },
    onauxclick: { enumerable: true },
    onbeforeinput: { enumerable: true },
    onbeforematch: { enumerable: true },
    onbeforetoggle: { enumerable: true },
    onblur: { enumerable: true },
    oncancel: { enumerable: true },
    oncanplay: { enumerable: true },
    oncanplaythrough: { enumerable: true },
    onchange: { enumerable: true },
    onclick: { enumerable: true },
    onclose: { enumerable: true },
    oncontextlost: { enumerable: true },
    oncontextmenu: { enumerable: true },
    oncontextrestored: { enumerable: true },
    oncopy: { enumerable: true },
    oncuechange: { enumerable: true },
    oncut: { enumerable: true },
    ondblclick: { enumerable: true },
    ondrag: { enumerable: true },
    ondragend: { enumerable: true },
    ondragenter: { enumerable: true },
    ondragleave: { enumerable: true },
    ondragover: { enumerable: true },
    ondragstart: { enumerable: true },
    ondrop: { enumerable: true },
    ondurationchange: { enumerable: true },
    onemptied: { enumerable: true },
    onended: { enumerable: true },
    onerror: { enumerable: true },
    onfocus: { enumerable: true },
    onformdata: { enumerable: true },
    oninput: { enumerable: true },
    oninvalid: { enumerable: true },
    onkeydown: { enumerable: true },
    onkeypress: { enumerable: true },
    onkeyup: { enumerable: true },
    onload: { enumerable: true },
    onloadeddata: { enumerable: true },
    onloadedmetadata: { enumerable: true },
    onloadstart: { enumerable: true },
    onmousedown: { enumerable: true },
    onmouseenter: { enumerable: true },
    onmouseleave: { enumerable: true },
    onmousemove: { enumerable: true },
    onmouseout: { enumerable: true },
    onmouseover: { enumerable: true },
    onmouseup: { enumerable: true },
    onpaste: { enumerable: true },
    onpause: { enumerable: true },
    onplay: { enumerable: true },
    onplaying: { enumerable: true },
    onprogress: { enumerable: true },
    onratechange: { enumerable: true },
    onreset: { enumerable: true },
    onresize: { enumerable: true },
    onscroll: { enumerable: true },
    onscrollend: { enumerable: true },
    onsecuritypolicyviolation: { enumerable: true },
    onseeked: { enumerable: true },
    onseeking: { enumerable: true },
    onselect: { enumerable: true },
    onslotchange: { enumerable: true },
    onstalled: { enumerable: true },
    onsubmit: { enumerable: true },
    onsuspend: { enumerable: true },
    ontimeupdate: { enumerable: true },
    ontoggle: { enumerable: true },
    onvolumechange: { enumerable: true },
    onwaiting: { enumerable: true },
    onwebkitanimationend: { enumerable: true },
    onwebkitanimationiteration: { enumerable: true },
    onwebkitanimationstart: { enumerable: true },
    onwebkittransitionend: { enumerable: true },
    onwheel: { enumerable: true },
    ontouchstart: { enumerable: true },
    ontouchend: { enumerable: true },
    ontouchmove: { enumerable: true },
    ontouchcancel: { enumerable: true },
    onpointerover: { enumerable: true },
    onpointerenter: { enumerable: true },
    onpointerdown: { enumerable: true },
    onpointermove: { enumerable: true },
    onpointerrawupdate: { enumerable: true },
    onpointerup: { enumerable: true },
    onpointercancel: { enumerable: true },
    onpointerout: { enumerable: true },
    onpointerleave: { enumerable: true },
    ongotpointercapture: { enumerable: true },
    onlostpointercapture: { enumerable: true },
    activeElement: { enumerable: true },
    children: { enumerable: true },
    firstElementChild: { enumerable: true },
    lastElementChild: { enumerable: true },
    childElementCount: { enumerable: true },
    [Symbol.toStringTag]: { value: "Document", configurable: true },
    [Symbol.unscopables]: {
      value: { prepend: true, append: true, replaceChildren: true, __proto__: null },
      configurable: true
    }
  });
  ctorRegistry[interfaceName] = Document;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: Document
  });
};

const proxyHandlerCache = new WeakMap();
class ProxyHandler {
  constructor(globalObject) {
    this._globalObject = globalObject;
  }

  get(target, P, receiver) {
    if (typeof P === "symbol") {
      return Reflect.get(target, P, receiver);
    }
    const impl = utils.implForWrapper(target);

    if (impl[utils.supportsPropertyName](P) && !Object.hasOwn(target, P)) {
      const namedValue = impl[utils.namedGet](P);
      return utils.tryWrapperForImpl(namedValue);
    }

    return Reflect.get(target, P, receiver);
  }

  has(target, P) {
    if (typeof P === "symbol") {
      return Reflect.has(target, P);
    }
    const desc = this.getOwnPropertyDescriptor(target, P);
    if (desc !== undefined) {
      return true;
    }
    const parent = Object.getPrototypeOf(target);
    if (parent !== null) {
      return Reflect.has(parent, P);
    }
    return false;
  }

  ownKeys(target) {
    const impl = utils.implForWrapper(target);
    const keys = new Set();

    for (const key of impl[utils.supportedPropertyNames]) {
      if (!Object.hasOwn(target, key)) {
        keys.add(`${key}`);
      }
    }

    for (const key of Reflect.ownKeys(target)) {
      keys.add(key);
    }
    return [...keys];
  }

  getOwnPropertyDescriptor(target, P) {
    if (typeof P === "symbol") {
      return Reflect.getOwnPropertyDescriptor(target, P);
    }
    const impl = utils.implForWrapper(target);

    if (impl[utils.supportsPropertyName](P) && !Object.hasOwn(target, P)) {
      const namedValue = impl[utils.namedGet](P);
      return {
        writable: false,
        enumerable: true,
        configurable: true,
        value: utils.tryWrapperForImpl(namedValue)
      };
    }

    return Reflect.getOwnPropertyDescriptor(target, P);
  }

  set(target, P, V, receiver) {
    if (typeof P === "symbol") {
      return Reflect.set(target, P, V, receiver);
    }
    const impl = utils.implForWrapper(target);
    // The `receiver` argument refers to the Proxy exotic object or an object
    // that inherits from it, whereas `target` refers to the Proxy target:
    if (utils.wrapperForImpl(impl) === receiver) {
      const globalObject = this._globalObject;
    }
    let ownDesc;

    if (ownDesc === undefined) {
      ownDesc = Reflect.getOwnPropertyDescriptor(target, P);
    }
    return utils.ordinarySetWithOwnDescriptor(target, P, V, receiver, ownDesc);
  }

  defineProperty(target, P, desc) {
    if (typeof P === "symbol") {
      return Reflect.defineProperty(target, P, desc);
    }
    const impl = utils.implForWrapper(target);

    const globalObject = this._globalObject;
    if (!["location"].includes(P)) {
      const creating = !impl[utils.supportsPropertyName](P);
      if (!creating) {
        return false;
      }
    }
    return Reflect.defineProperty(target, P, desc);
  }

  deleteProperty(target, P) {
    if (typeof P === "symbol") {
      return Reflect.deleteProperty(target, P);
    }
    const impl = utils.implForWrapper(target);

    const globalObject = this._globalObject;

    if (impl[utils.supportsPropertyName](P) && !Object.hasOwn(target, P)) {
      return false;
    }

    return Reflect.deleteProperty(target, P);
  }

  preventExtensions() {
    return false;
  }
}

const Impl = require("../../jsdom/living/nodes/Document-impl.js");
