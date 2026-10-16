"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const HTMLConstructor_jsdom_living_helpers_html_constructor =
  require("../../jsdom/living/helpers/html-constructor.js").HTMLConstructor;
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const HTMLTableCaptionElement = require("./HTMLTableCaptionElement.js");
const HTMLTableSectionElement = require("./HTMLTableSectionElement.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLTableElement";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => HTMLElement.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLTableElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLTableElement"].prototype;
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
  HTMLElement._internalSetup(wrapper, globalObject);
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
  class HTMLTableElement extends globalObject.HTMLElement {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    createCaption() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createCaption");
      return utils.tryWrapperForImpl($impl.createCaption());
    }

    deleteCaption() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "deleteCaption");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.deleteCaption();
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    createTHead() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createTHead");
      return utils.tryWrapperForImpl($impl.createTHead());
    }

    deleteTHead() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "deleteTHead");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.deleteTHead();
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    createTFoot() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createTFoot");
      return utils.tryWrapperForImpl($impl.createTFoot());
    }

    deleteTFoot() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "deleteTFoot");
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.deleteTFoot();
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    createTBody() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "createTBody");
      return utils.tryWrapperForImpl($impl.createTBody());
    }

    insertRow() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "insertRow");
      const args = [];
      {
        let curArg = arguments[0];
        if (curArg !== undefined) {
          curArg = conversions["long"](curArg, {
            context: "Failed to execute 'insertRow' on 'HTMLTableElement': parameter 1",
            globals: globalObject
          });
        } else {
          curArg = -1;
        }
        args.push(curArg);
      }
      return utils.tryWrapperForImpl($impl.insertRow(...args));
    }

    deleteRow(index) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "deleteRow");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'deleteRow' on 'HTMLTableElement': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["long"](curArg, {
          context: "Failed to execute 'deleteRow' on 'HTMLTableElement': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl.deleteRow(...args);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get caption() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get caption");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl["caption"]);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set caption(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set caption");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = HTMLTableCaptionElement.convert(globalObject, V, {
          context: "Failed to set the 'caption' property on 'HTMLTableElement': The provided value"
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["caption"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get tHead() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get tHead");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl["tHead"]);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set tHead(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set tHead");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = HTMLTableSectionElement.convert(globalObject, V, {
          context: "Failed to set the 'tHead' property on 'HTMLTableElement': The provided value"
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["tHead"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get tFoot() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get tFoot");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return utils.tryWrapperForImpl($impl["tFoot"]);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set tFoot(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set tFoot");

      if (V === null || V === undefined) {
        V = null;
      } else {
        V = HTMLTableSectionElement.convert(globalObject, V, {
          context: "Failed to set the 'tFoot' property on 'HTMLTableElement': The provided value"
        });
      }

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["tFoot"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get tBodies() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get tBodies");
      return utils.getSameObject(this, "tBodies", () => {
        return utils.tryWrapperForImpl($impl["tBodies"]);
      });
    }

    get rows() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get rows");
      return utils.getSameObject(this, "rows", () => {
        return utils.tryWrapperForImpl($impl["rows"]);
      });
    }

    get align() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get align");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("align");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set align(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set align");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'align' property on 'HTMLTableElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("align", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get border() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get border");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("border");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set border(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set border");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'border' property on 'HTMLTableElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("border", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get frame() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get frame");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("frame");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set frame(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set frame");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'frame' property on 'HTMLTableElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("frame", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get rules() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get rules");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("rules");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set rules(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set rules");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'rules' property on 'HTMLTableElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("rules", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get summary() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get summary");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("summary");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set summary(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set summary");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'summary' property on 'HTMLTableElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("summary", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get width() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get width");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("width");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set width(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set width");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'width' property on 'HTMLTableElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("width", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get bgColor() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get bgColor");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("bgcolor");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set bgColor(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set bgColor");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'bgColor' property on 'HTMLTableElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("bgcolor", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get cellPadding() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get cellPadding");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("cellpadding");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set cellPadding(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set cellPadding");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'cellPadding' property on 'HTMLTableElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("cellpadding", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get cellSpacing() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get cellSpacing");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("cellspacing");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set cellSpacing(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set cellSpacing");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'cellSpacing' property on 'HTMLTableElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("cellspacing", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }
  }
  Object.defineProperties(HTMLTableElement.prototype, {
    createCaption: { enumerable: true },
    deleteCaption: { enumerable: true },
    createTHead: { enumerable: true },
    deleteTHead: { enumerable: true },
    createTFoot: { enumerable: true },
    deleteTFoot: { enumerable: true },
    createTBody: { enumerable: true },
    insertRow: { enumerable: true },
    deleteRow: { enumerable: true },
    caption: { enumerable: true },
    tHead: { enumerable: true },
    tFoot: { enumerable: true },
    tBodies: { enumerable: true },
    rows: { enumerable: true },
    align: { enumerable: true },
    border: { enumerable: true },
    frame: { enumerable: true },
    rules: { enumerable: true },
    summary: { enumerable: true },
    width: { enumerable: true },
    bgColor: { enumerable: true },
    cellPadding: { enumerable: true },
    cellSpacing: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLTableElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLTableElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLTableElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLTableElement-impl.js");
