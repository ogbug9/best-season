/* Kontur React UI portals live under body, outside the native dialog top layer.
   The paired render-container IDs below were verified against the live DOM.
   Do not reparent portals: RenderContainer mounts them back under body on render. */
(function () {
  "use strict";
  window.BookingLayers = function (modal) {
    var observer = null;
    var pending = false;
    var suspended = false;
    var ignoredCloses = 0;
    var returnFocus = null;
    var scrollTop = 0;
    var inertElements = new Map();
    var parkedPortals = new Map();

    function portals() {
      var containers = Array.from(document.querySelectorAll(".react-ui[data-rendered-container-id]"));
      var owners = [modal];
      var result = [];
      // Follow nested portal ownership too (calendar/guest picker inside a modal).
      for (var i = 0; i < owners.length; i++) {
        owners[i].querySelectorAll("noscript[data-render-container-id]").forEach(function (marker) {
          var id = marker.getAttribute("data-render-container-id");
          containers.forEach(function (container) {
            if (container.getAttribute("data-rendered-container-id") === id && result.indexOf(container) < 0) {
              result.push(container);
              owners.push(container);
            }
          });
        });
      }
      return result.filter(function (container) {
        return Array.from(container.children).some(function (child) {
          var style = getComputedStyle(child);
          return child.getClientRects().length && style.display !== "none" && style.visibility !== "hidden";
        });
      });
    }

    function restoreInert() {
      inertElements.forEach(function (value, element) { element.inert = value; });
      inertElements.clear();
    }

    function focus(element) {
      if (element && element.isConnected) element.focus({ preventScroll: true });
    }

    function switchMode(nativeModal) {
      // close events are queued, even when the dialog is immediately reopened.
      ignoredCloses++;
      modal.close();
      if (nativeModal) modal.showModal();
      else modal.show();
    }

    function sync() {
      pending = false;
      if (!observer || !modal.open) return;
      var active = portals();
      var entered = false;
      if (active.length) {
        if (!suspended) {
          entered = true;
          returnFocus = document.activeElement;
          scrollTop = modal.scrollTop;
          var rect = modal.getBoundingClientRect();
          modal.style.setProperty("--booking-layer-top", rect.top + "px");
          modal.style.setProperty("--booking-layer-width", rect.width + "px");
          modal.style.setProperty("--booking-layer-height", rect.height + "px");
          suspended = true;
          modal.classList.add("booking-system--vendor-open");
          switchMode(false);
          modal.scrollTop = scrollTop;
        }
        var zIndexes = active.flatMap(function (container) {
          return Array.from(container.children).map(function (child) { return parseInt(getComputedStyle(child).zIndex, 10); });
        }).filter(Number.isFinite);
        // Derive the shell's layer from the actual SDK layer, never an arbitrary high z-index.
        var layer = String(zIndexes.length ? Math.min.apply(Math, zIndexes) - 1 : 0);
        if (modal.style.getPropertyValue("--booking-layer-z") !== layer) modal.style.setProperty("--booking-layer-z", layer);
        Array.from(document.body.children).forEach(function (element) {
          if (element === modal || active.indexOf(element) >= 0 || /^(SCRIPT|STYLE|LINK)$/.test(element.tagName)) return;
          if (!inertElements.has(element)) inertElements.set(element, element.inert);
          element.inert = true;
        });
        // A previously inactive portal may become active again in a nested workflow.
        active.forEach(function (element) {
          if (inertElements.has(element)) {
            element.inert = inertElements.get(element);
            inertElements.delete(element);
          }
        });
        var inner = active.map(function (container) {
          return container.querySelector('[data-tid="modal-content"][role="dialog"]');
        }).filter(Boolean).pop();
        modal.inert = Boolean(inner);
        if (!inner && entered) focus(returnFocus);
        if (inner && !active.some(function (container) { return container.contains(document.activeElement); })) {
          // SDK autofocus may have run while the native dialog still made the portal inert.
          var control = inner.querySelector('button:not([disabled]), input:not([type="hidden"]):not([disabled]), [tabindex="0"]');
          if (!control) { inner.setAttribute("tabindex", "-1"); control = inner; }
          focus(control);
        }
      } else if (suspended) {
        suspended = false;
        modal.inert = false;
        restoreInert();
        modal.classList.remove("booking-system--vendor-open");
        switchMode(true);
        modal.scrollTop = scrollTop;
        focus(modal.contains(returnFocus) ? returnFocus : modal.querySelector("[data-booking-close]"));
        returnFocus = null;
      }
    }

    function trapTab(event) {
      if (event.key !== "Tab" || !suspended) return;
      var active = portals();
      var roots = modal.inert ? active : [modal].concat(active);
      var controls = roots.flatMap(function (root) {
        return Array.from(root.querySelectorAll('button, input, select, textarea, a[href], [tabindex]'));
      }).filter(function (element) {
        return element.tabIndex >= 0 && !element.disabled && !element.closest('[inert]') &&
          element.getClientRects().length && getComputedStyle(element).visibility !== "hidden";
      });
      var first = controls[0], last = controls[controls.length - 1];
      if (!first) return;
      var current = document.activeElement;
      if (event.shiftKey && (current === first || controls.indexOf(current) < 0)) {
        event.preventDefault(); focus(last);
      } else if (!event.shiftKey && (current === last || controls.indexOf(current) < 0)) {
        event.preventDefault(); focus(first);
      }
    }

    return {
      open: function () {
        if (observer) return;
        // Preserve the SDK state, but never leave its popups floating after
        // the outer dialog is closed (for example while its date picker is open).
        parkedPortals.forEach(function (hidden, element) {
          if (element.isConnected) element.hidden = hidden;
        });
        parkedPortals.clear();
        observer = new MutationObserver(function () {
          if (!pending) { pending = true; requestAnimationFrame(sync); }
        });
        observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["style", "class", "hidden"] });
        document.addEventListener("keydown", trapTab);
        if (!pending) { pending = true; requestAnimationFrame(sync); }
      },
      close: function () {
        if (ignoredCloses) { ignoredCloses--; return false; }
        if (observer) observer.disconnect();
        portals().forEach(function (element) {
          parkedPortals.set(element, element.hidden);
          element.hidden = true;
        });
        document.removeEventListener("keydown", trapTab);
        observer = null;
        pending = false;
        suspended = false;
        modal.inert = false;
        restoreInert();
        modal.classList.remove("booking-system--vendor-open");
        return true;
      },
      ownsPopup: function () { return portals().length > 0; },
    };
  };
})();
