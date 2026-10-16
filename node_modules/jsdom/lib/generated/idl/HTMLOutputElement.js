"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const HTMLConstructor_jsdom_living_helpers_html_constructor =
  require("../../jsdom/living/helpers/html-constructor.js").HTMLConstructor;
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLOutputElement";

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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLOutputElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLOutputElement"].prototype;
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
  class HTMLOutputElement extends globalObject.HTMLElement {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    checkValidity() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "checkValidity");
      return $impl.checkValidity();
    }

    reportValidity() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "reportValidity");
      return $impl.reportValidity();
    }

    setCustomValidity(error) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setCustomValidity");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setCustomValidity' on 'HTMLOutputElement': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'setCustomValidity' on 'HTMLOutputElement': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.setCustomValidity(...args);
    }

    get htmlFor() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get htmlFor");
      return utils.getSameObject(this, "htmlFor", () => {
        return utils.tryWrapperForImpl($impl["htmlFor"]);
      });
    }

    set htmlFor(V) {
      const esValue = this ?? globalObject;
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set htmlFor");

      const Q = esValue["htmlFor"];
      if (!utils.isObject(Q)) {
        throw new globalObject.TypeError("Property 'htmlFor' is not an object");
      }
      Reflect.set(Q, "value", V);
    }

    get form() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get form");
      return utils.tryWrapperForImpl($impl["form"]);
    }

    get name() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get name");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("name");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set name(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set name");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'name' property on 'HTMLOutputElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("name", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get type() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get type");
      return $impl["type"];
    }

    get defaultValue() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get defaultValue");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["defaultValue"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set defaultValue(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set defaultValue");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'defaultValue' property on 'HTMLOutputElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["defaultValue"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get value() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get value");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["value"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set value(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set value");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'value' property on 'HTMLOutputElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["value"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get willValidate() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get willValidate");
      return $impl["willValidate"];
    }

    get validity() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get validity");
      return utils.tryWrapperForImpl($impl["validity"]);
    }

    get validationMessage() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get validationMessage");
      return $impl["validationMessage"];
    }

    get labels() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get labels");
      return utils.tryWrapperForImpl($impl["labels"]);
    }
  }
  Object.defineProperties(HTMLOutputElement.prototype, {
    checkValidity: { enumerable: true },
    reportValidity: { enumerable: true },
    setCustomValidity: { enumerable: true },
    htmlFor: { enumerable: true },
    form: { enumerable: true },
    name: { enumerable: true },
    type: { enumerable: true },
    defaultValue: { enumerable: true },
    value: { enumerable: true },
    willValidate: { enumerable: true },
    validity: { enumerable: true },
    validationMessage: { enumerable: true },
    labels: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLOutputElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLOutputElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLOutputElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLOutputElement-impl.js");
