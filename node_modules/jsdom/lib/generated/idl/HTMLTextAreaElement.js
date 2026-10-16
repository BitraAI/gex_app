"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const HTMLConstructor_jsdom_living_helpers_html_constructor =
  require("../../jsdom/living/helpers/html-constructor.js").HTMLConstructor;
const SelectionMode = require("./SelectionMode.js");
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const parseNonNegativeInteger_jsdom_living_helpers_strings =
  require("../../jsdom/living/helpers/strings.js").parseNonNegativeInteger;
const create_DOMException = require("./DOMException.js").create;
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const HTMLElement = require("./HTMLElement.js");

const interfaceName = "HTMLTextAreaElement";

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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLTextAreaElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLTextAreaElement"].prototype;
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
  class HTMLTextAreaElement extends globalObject.HTMLElement {
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
          `Failed to execute 'setCustomValidity' on 'HTMLTextAreaElement': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["DOMString"](curArg, {
          context: "Failed to execute 'setCustomValidity' on 'HTMLTextAreaElement': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      return $impl.setCustomValidity(...args);
    }

    select() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "select");
      return $impl.select();
    }

    setRangeText(replacement) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setRangeText");
      if (arguments.length < 1) {
        throw new globalObject.TypeError(
          `Failed to execute 'setRangeText' on 'HTMLTextAreaElement': 1 argument required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      switch (arguments.length) {
        case 1:
          {
            let curArg = arguments[0];
            curArg = conversions["DOMString"](curArg, {
              context: "Failed to execute 'setRangeText' on 'HTMLTextAreaElement': parameter 1",
              globals: globalObject
            });
            args.push(curArg);
          }
          break;
        case 2:
          throw new globalObject.TypeError(
            `Failed to execute 'setRangeText' on 'HTMLTextAreaElement': only ${arguments.length} arguments present.`
          );
          break;
        case 3:
          {
            let curArg = arguments[0];
            curArg = conversions["DOMString"](curArg, {
              context: "Failed to execute 'setRangeText' on 'HTMLTextAreaElement': parameter 1",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[1];
            curArg = conversions["unsigned long"](curArg, {
              context: "Failed to execute 'setRangeText' on 'HTMLTextAreaElement': parameter 2",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[2];
            curArg = conversions["unsigned long"](curArg, {
              context: "Failed to execute 'setRangeText' on 'HTMLTextAreaElement': parameter 3",
              globals: globalObject
            });
            args.push(curArg);
          }
          break;
        default:
          {
            let curArg = arguments[0];
            curArg = conversions["DOMString"](curArg, {
              context: "Failed to execute 'setRangeText' on 'HTMLTextAreaElement': parameter 1",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[1];
            curArg = conversions["unsigned long"](curArg, {
              context: "Failed to execute 'setRangeText' on 'HTMLTextAreaElement': parameter 2",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[2];
            curArg = conversions["unsigned long"](curArg, {
              context: "Failed to execute 'setRangeText' on 'HTMLTextAreaElement': parameter 3",
              globals: globalObject
            });
            args.push(curArg);
          }
          {
            let curArg = arguments[3];
            if (curArg !== undefined) {
              curArg = SelectionMode.convert(globalObject, curArg, {
                context: "Failed to execute 'setRangeText' on 'HTMLTextAreaElement': parameter 4"
              });
            } else {
              curArg = "preserve";
            }
            args.push(curArg);
          }
      }
      return $impl.setRangeText(...args);
    }

    setSelectionRange(start, end) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "setSelectionRange");
      if (arguments.length < 2) {
        throw new globalObject.TypeError(
          `Failed to execute 'setSelectionRange' on 'HTMLTextAreaElement': 2 arguments required, but only ${arguments.length} present.`
        );
      }
      const args = [];
      {
        let curArg = arguments[0];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'setSelectionRange' on 'HTMLTextAreaElement': parameter 1",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[1];
        curArg = conversions["unsigned long"](curArg, {
          context: "Failed to execute 'setSelectionRange' on 'HTMLTextAreaElement': parameter 2",
          globals: globalObject
        });
        args.push(curArg);
      }
      {
        let curArg = arguments[2];
        if (curArg !== undefined) {
          curArg = conversions["DOMString"](curArg, {
            context: "Failed to execute 'setSelectionRange' on 'HTMLTextAreaElement': parameter 3",
            globals: globalObject
          });
        }
        args.push(curArg);
      }
      return $impl.setSelectionRange(...args);
    }

    get autocomplete() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get autocomplete");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("autocomplete");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set autocomplete(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set autocomplete");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'autocomplete' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("autocomplete", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get autofocus() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get autofocus");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("autofocus") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set autofocus(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set autofocus");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'autofocus' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("autofocus", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("autofocus");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get cols() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get cols");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        let value = $impl._reflectGetTheContentAttribute("cols");
        if (value !== null) {
          value = parseNonNegativeInteger_jsdom_living_helpers_strings(value);
          if (value !== null && value >= 1 && value <= 2147483647) {
            return value;
          }
        }
        return 20;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set cols(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set cols");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'cols' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const newValue = V <= 2147483647 && V >= 1 ? V : 20;
        $impl._reflectSetTheContentAttribute("cols", String(newValue));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get dirName() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get dirName");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("dirname");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set dirName(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set dirName");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'dirName' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("dirname", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get disabled() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get disabled");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("disabled") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set disabled(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set disabled");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'disabled' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("disabled", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("disabled");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get form() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get form");
      return utils.tryWrapperForImpl($impl["form"]);
    }

    get inputMode() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get inputMode");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("inputmode");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set inputMode(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set inputMode");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'inputMode' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("inputmode", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get maxLength() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get maxLength");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        let value = $impl._reflectGetTheContentAttribute("maxlength");
        if (value !== null) {
          value = parseNonNegativeInteger_jsdom_living_helpers_strings(value);
          if (value !== null && conversions.long(value) === value) {
            return value;
          }
        }
        return -1;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set maxLength(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set maxLength");

      V = conversions["long"](V, {
        context: "Failed to set the 'maxLength' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V < 0) {
          throw create_DOMException(globalObject, [
            `The negative value ${V} cannot be set for the maxLength property.`,
            "IndexSizeError"
          ]);
        }

        $impl._reflectSetTheContentAttribute("maxlength", String(V));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get minLength() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get minLength");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        let value = $impl._reflectGetTheContentAttribute("minlength");
        if (value !== null) {
          value = parseNonNegativeInteger_jsdom_living_helpers_strings(value);
          if (value !== null && conversions.long(value) === value) {
            return value;
          }
        }
        return -1;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set minLength(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set minLength");

      V = conversions["long"](V, {
        context: "Failed to set the 'minLength' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V < 0) {
          throw create_DOMException(globalObject, [
            `The negative value ${V} cannot be set for the minLength property.`,
            "IndexSizeError"
          ]);
        }

        $impl._reflectSetTheContentAttribute("minlength", String(V));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
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
        context: "Failed to set the 'name' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("name", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get placeholder() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get placeholder");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("placeholder");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set placeholder(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set placeholder");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'placeholder' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("placeholder", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get readOnly() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get readOnly");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("readonly") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set readOnly(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set readOnly");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'readOnly' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("readonly", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("readonly");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get required() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get required");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("required") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set required(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set required");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'required' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("required", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("required");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get rows() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get rows");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        let value = $impl._reflectGetTheContentAttribute("rows");
        if (value !== null) {
          value = parseNonNegativeInteger_jsdom_living_helpers_strings(value);
          if (value !== null && value >= 1 && value <= 2147483647) {
            return value;
          }
        }
        return 2;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set rows(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set rows");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'rows' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const newValue = V <= 2147483647 && V >= 1 ? V : 2;
        $impl._reflectSetTheContentAttribute("rows", String(newValue));
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get wrap() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get wrap");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("wrap");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set wrap(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set wrap");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'wrap' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("wrap", V);
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
        context: "Failed to set the 'defaultValue' property on 'HTMLTextAreaElement': The provided value",
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
        context: "Failed to set the 'value' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject,
        treatNullAsEmptyString: true
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["value"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get textLength() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get textLength");
      return $impl["textLength"];
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

    get selectionStart() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get selectionStart");
      return $impl["selectionStart"];
    }

    set selectionStart(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set selectionStart");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'selectionStart' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      $impl["selectionStart"] = V;
    }

    get selectionEnd() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get selectionEnd");
      return $impl["selectionEnd"];
    }

    set selectionEnd(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set selectionEnd");

      V = conversions["unsigned long"](V, {
        context: "Failed to set the 'selectionEnd' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      $impl["selectionEnd"] = V;
    }

    get selectionDirection() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get selectionDirection");
      return $impl["selectionDirection"];
    }

    set selectionDirection(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set selectionDirection");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'selectionDirection' property on 'HTMLTextAreaElement': The provided value",
        globals: globalObject
      });

      $impl["selectionDirection"] = V;
    }
  }
  Object.defineProperties(HTMLTextAreaElement.prototype, {
    checkValidity: { enumerable: true },
    reportValidity: { enumerable: true },
    setCustomValidity: { enumerable: true },
    select: { enumerable: true },
    setRangeText: { enumerable: true },
    setSelectionRange: { enumerable: true },
    autocomplete: { enumerable: true },
    autofocus: { enumerable: true },
    cols: { enumerable: true },
    dirName: { enumerable: true },
    disabled: { enumerable: true },
    form: { enumerable: true },
    inputMode: { enumerable: true },
    maxLength: { enumerable: true },
    minLength: { enumerable: true },
    name: { enumerable: true },
    placeholder: { enumerable: true },
    readOnly: { enumerable: true },
    required: { enumerable: true },
    rows: { enumerable: true },
    wrap: { enumerable: true },
    type: { enumerable: true },
    defaultValue: { enumerable: true },
    value: { enumerable: true },
    textLength: { enumerable: true },
    willValidate: { enumerable: true },
    validity: { enumerable: true },
    validationMessage: { enumerable: true },
    labels: { enumerable: true },
    selectionStart: { enumerable: true },
    selectionEnd: { enumerable: true },
    selectionDirection: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLTextAreaElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLTextAreaElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLTextAreaElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLTextAreaElement-impl.js");
