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
    var focusedInner = null;

    function portals() {
      // Kontur normally annotates portal roots with data-rendered-container-id.
      // Some booking screens (the availability result, and the date picker
      // opened from inside it) mount the same .react-ui root WITHOUT that
      // attribute. Those un-annotated roots carry no id a <noscript> marker
      // could ever match, so a marker-matching pass can never find them —
      // that used to leave them out of `result` entirely, which is the bug:
      // an un-annotated portal was never treated as an active layer, so it
      // stayed BEHIND the native <dialog>'s top layer (invisible stacking,
      // unclickable) while our own inert/tab-trap bookkeeping ignored it.
      // Every Kontur widget on this site lives inside this one modal, so
      // there is no unrelated portal to filter out — any body-level
      // .react-ui root is ours. Just take all of them directly.
      var containers = Array.from(document.querySelectorAll(".react-ui[data-rendered-container-id], body > .react-ui"));
      containers = containers.filter(function (container, index, all) {
        return all.indexOf(container) === index;
      });
      return containers.filter(function (container) {
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
        // Never inert a Kontur portal itself, only unrelated body children —
        // not just the ones active RIGHT NOW. A portal Kontur mounts once and
        // toggles internally (the date-picker attached to a plain field is
        // exactly this) can be genuinely empty/invisible at the instant this
        // runs (still loading, mid-transition), which used to get it inerted
        // here. inert blocks pointer events on the whole subtree, including
        // future clicks that would have opened it — so an un-lucky first
        // check permanently deadlocked that control: it could never become
        // "active" by our own visibility check again, because inert stopped
        // the very click that would have shown it. Kontur portals are never
        // background noise on this site (every one belongs to our modal), so
        // just leave the whole .react-ui class alone, active or not.
        Array.from(document.body.children).forEach(function (element) {
          if (element === modal || element.classList.contains("react-ui") || /^(SCRIPT|STYLE|LINK)$/.test(element.tagName)) return;
          if (!inertElements.has(element)) inertElements.set(element, element.inert);
          element.inert = true;
        });
        var inner = active.map(function (container) {
          return container.querySelector('[data-tid="modal-content"][role="dialog"]');
        }).filter(Boolean).pop();
        modal.inert = Boolean(inner);
        if (!inner) {
          focusedInner = null;
          if (entered) focus(returnFocus);
        } else if (inner !== focusedInner && !active.some(function (container) { return container.contains(document.activeElement); })) {
          // Steal focus into a newly opened vendor dialog once (SDK autofocus may
          // have run while the native dialog still made the portal inert). Every
          // later mutation — picking a day, the grid redrawing — also moves focus
          // out of the DOM for a tick, but re-stealing it back to the FIRST control
          // on every one of those renders is what snapped the calendar back to its
          // opening date and trapped guests inside it. Only the dialog's first
          // appearance gets this nudge; after that its own focus handling is left
          // alone even if it transiently loses focus during a re-render.
          var control = inner.querySelector('button:not([disabled]), input:not([type="hidden"]):not([disabled]), [tabindex="0"]');
          if (!control) { inner.setAttribute("tabindex", "-1"); control = inner; }
          focus(control);
          focusedInner = inner;
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

    // The date-range calendar attached to a plain "Заезд"/"Выезд" field has no
    // close/apply control of its own and does not react to a click outside it
    // either (confirmed live: it only ever disappears when the whole booking
    // modal closes, via the forced hide() in close() below). Left alone it
    // just sits there covering whatever the page has under it — including,
    // in practice, the general "Проверить наличие" button right next to the
    // fields. Hiding a Kontur portal ourselves is already known-safe: that is
    // exactly what close() below does. So do the same thing here, a moment
    // after the guest stops clicking days, instead of only at modal close.
    // Scoped to plain calendar popups only (they carry day-picker cells and
    // nothing that looks like a full dialog screen) so a date picker that is
    // genuinely part of a bigger vendor dialog — the nested "check
    // availability" flow — is left for that dialog to manage.
    var rangePickTimer = null;
    document.addEventListener("click", function (event) {
      if (!event.target.closest("[data-date-range-picker-day]")) return;
      clearTimeout(rangePickTimer);
      rangePickTimer = setTimeout(function () {
        Array.from(document.querySelectorAll("body > .react-ui")).forEach(function (container) {
          if (container.hidden) return;
          if (!container.querySelector("[data-date-range-picker-day]")) return;
          if (container.querySelector('[data-tid="modal-content"][role="dialog"]')) return;
          container.hidden = true;
        });
      }, 400);
    }, true);

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
        focusedInner = null;
        modal.inert = false;
        restoreInert();
        modal.classList.remove("booking-system--vendor-open");
        return true;
      },
      ownsPopup: function () { return portals().length > 0; },
    };
  };
})();
