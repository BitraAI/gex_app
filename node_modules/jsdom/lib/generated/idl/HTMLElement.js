"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const HTMLConstructor_jsdom_living_helpers_html_constructor =
  require("../../jsdom/living/helpers/html-constructor.js").HTMLConstructor;
const ceReactionsPreSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPreSteps;
const ceReactionsPostSteps_jsdom_living_helpers_custom_elements =
  require("../../jsdom/living/helpers/custom-elements.js").ceReactionsPostSteps;
const EventHandlerNonNull = require("./EventHandlerNonNull.js");
const OnErrorEventHandlerNonNull = require("./OnErrorEventHandlerNonNull.js");
const ctorRegistrySymbol = utils.ctorRegistrySymbol;
const Element = require("./Element.js");

const interfaceName = "HTMLElement";

const $interfaceDescriptor = utils.createInterfaceDescriptor(() => Element.interfaceDescriptor);
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
  throw new globalObject.TypeError(`${context} is not of type 'HTMLElement'.`);
};

function makeWrapper(globalObject, newTarget) {
  let proto;
  if (newTarget !== undefined) {
    proto = newTarget.prototype;
  }

  if (!utils.isObject(proto)) {
    proto = globalObject[ctorRegistrySymbol]["HTMLElement"].prototype;
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
  Element._internalSetup(wrapper, globalObject);
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
  class HTMLElement extends globalObject.Element {
    constructor() {
      return HTMLConstructor_jsdom_living_helpers_html_constructor(globalObject, interfaceName, new.target);
    }

    click() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "click");
      return $impl.click();
    }

    attachInternals() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "attachInternals");
      return utils.tryWrapperForImpl($impl.attachInternals());
    }

    focus() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "focus");
      return $impl.focus();
    }

    blur() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "blur");
      return $impl.blur();
    }

    get title() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get title");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("title");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set title(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set title");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'title' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("title", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get lang() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get lang");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("lang");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set lang(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set lang");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'lang' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("lang", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get translate() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get translate");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["translate"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set translate(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set translate");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'translate' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["translate"] = V;
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
        context: "Failed to set the 'dir' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["dir"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get hidden() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get hidden");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl._reflectGetTheContentAttribute("hidden") !== null;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set hidden(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set hidden");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'hidden' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        if (V) {
          $impl._reflectSetTheContentAttribute("hidden", "");
        } else {
          $impl._reflectDeleteTheContentAttribute("hidden");
        }
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get accessKey() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get accessKey");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        const value = $impl._reflectGetTheContentAttribute("accesskey");
        return value === null ? "" : value;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set accessKey(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set accessKey");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'accessKey' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl._reflectSetTheContentAttribute("accesskey", V);
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get draggable() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get draggable");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["draggable"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set draggable(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set draggable");

      V = conversions["boolean"](V, {
        context: "Failed to set the 'draggable' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["draggable"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    get offsetParent() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get offsetParent");
      return utils.tryWrapperForImpl($impl["offsetParent"]);
    }

    get offsetTop() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get offsetTop");
      return $impl["offsetTop"];
    }

    get offsetLeft() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get offsetLeft");
      return $impl["offsetLeft"];
    }

    get offsetWidth() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get offsetWidth");
      return $impl["offsetWidth"];
    }

    get offsetHeight() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get offsetHeight");
      return $impl["offsetHeight"];
    }

    get style() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get style");
      return utils.getSameObject(this, "style", () => {
        return utils.tryWrapperForImpl($impl["style"]);
      });
    }

    set style(V) {
      const esValue = this ?? globalObject;
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set style");

      const Q = esValue["style"];
      if (!utils.isObject(Q)) {
        throw new globalObject.TypeError("Property 'style' is not an object");
      }
      Reflect.set(Q, "cssText", V);
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
          context: "Failed to set the 'onabort' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onauxclick' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onbeforeinput' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onbeforematch' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onbeforetoggle' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onblur' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncancel' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncanplay' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncanplaythrough' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onchange' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onclick' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onclose' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncontextlost' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncontextmenu' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncontextrestored' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncopy' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncuechange' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oncut' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondblclick' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondrag' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondragend' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondragenter' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondragleave' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondragover' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondragstart' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondrop' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ondurationchange' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onemptied' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onended' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onerror' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onfocus' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onformdata' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oninput' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'oninvalid' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onkeydown' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onkeypress' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onkeyup' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onload' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onloadeddata' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onloadedmetadata' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onloadstart' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onmousedown' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onmouseenter' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onmouseleave' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onmousemove' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onmouseout' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onmouseover' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onmouseup' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpaste' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpause' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onplay' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onplaying' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onprogress' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onratechange' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onreset' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onresize' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onscroll' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onscrollend' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onsecuritypolicyviolation' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onseeked' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onseeking' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onselect' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onslotchange' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onstalled' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onsubmit' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onsuspend' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ontimeupdate' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ontoggle' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onvolumechange' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onwaiting' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onwebkitanimationend' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onwebkitanimationiteration' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onwebkitanimationstart' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onwebkittransitionend' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onwheel' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ontouchstart' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ontouchend' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ontouchmove' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ontouchcancel' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointerover' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointerenter' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointerdown' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointermove' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointerrawupdate' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointerup' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointercancel' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointerout' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onpointerleave' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'ongotpointercapture' property on 'HTMLElement': The provided value"
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
          context: "Failed to set the 'onlostpointercapture' property on 'HTMLElement': The provided value"
        });
      }
      $impl["onlostpointercapture"] = V;
    }

    get dataset() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get dataset");
      return utils.getSameObject(this, "dataset", () => {
        return utils.tryWrapperForImpl($impl["dataset"]);
      });
    }

    get nonce() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get nonce");

      const value = $impl._reflectGetTheContentAttribute("nonce");
      return value === null ? "" : value;
    }

    set nonce(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set nonce");

      V = conversions["DOMString"](V, {
        context: "Failed to set the 'nonce' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      $impl._reflectSetTheContentAttribute("nonce", V);
    }

    get tabIndex() {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "get tabIndex");

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        return $impl["tabIndex"];
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }

    set tabIndex(V) {
      const $impl = $requireImpl(this ?? globalObject, globalObject, "set tabIndex");

      V = conversions["long"](V, {
        context: "Failed to set the 'tabIndex' property on 'HTMLElement': The provided value",
        globals: globalObject
      });

      ceReactionsPreSteps_jsdom_living_helpers_custom_elements(globalObject);
      try {
        $impl["tabIndex"] = V;
      } finally {
        ceReactionsPostSteps_jsdom_living_helpers_custom_elements(globalObject);
      }
    }
  }
  Object.defineProperties(HTMLElement.prototype, {
    click: { enumerable: true },
    attachInternals: { enumerable: true },
    focus: { enumerable: true },
    blur: { enumerable: true },
    title: { enumerable: true },
    lang: { enumerable: true },
    translate: { enumerable: true },
    dir: { enumerable: true },
    hidden: { enumerable: true },
    accessKey: { enumerable: true },
    draggable: { enumerable: true },
    offsetParent: { enumerable: true },
    offsetTop: { enumerable: true },
    offsetLeft: { enumerable: true },
    offsetWidth: { enumerable: true },
    offsetHeight: { enumerable: true },
    style: { enumerable: true },
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
    dataset: { enumerable: true },
    nonce: { enumerable: true },
    tabIndex: { enumerable: true },
    [Symbol.toStringTag]: { value: "HTMLElement", configurable: true }
  });
  ctorRegistry[interfaceName] = HTMLElement;

  Object.defineProperty(globalObject, interfaceName, {
    configurable: true,
    writable: true,
    value: HTMLElement
  });
};

const Impl = require("../../jsdom/living/nodes/HTMLElement-impl.js");
