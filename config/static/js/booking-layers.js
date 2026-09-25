/* Kontur React UI portals live under body, outside the native dialog top layer.
   The paired render-container IDs below were verified against the live DOM.
   Do not reparent portals: RenderContainer mounts them back under body on render. */
(function () {
  "use strict";
  window.BookingLayers = function (modal) {
    var observer = null;
    var pending = false;
    var suspended = false;
    var vendorExitTimer = null;
    var ignoredCloses = 0;
    var returnFocus = null;
    var scrollTop = 0;
    var inertElements = new Map();
    var parkedPortals = new Map();
    var focusedInner = null;
    var hiddenRangePickContainers = new Set();

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

    function fitRangePickers() {
      document.querySelectorAll('body > .react-ui [data-tid="DateRangePicker__root"]').forEach(function (picker) {
        if (picker.closest('[data-tid="modal-content"]') || !picker.getClientRects().length) return;
        // The SDK writes viewport coordinates to an absolute popup. Our
        // scroll lock moves body upwards; an absolute popup then disappears
        // above the screen by that exact scroll offset. Keep its coordinates
        // in the viewport, including when opened from a scrolled mobile page.
        if (picker.style.position !== "fixed") picker.style.position = "fixed";
        var maxWidth = Math.max(0, window.innerWidth - 16) + "px";
        if (picker.style.maxWidth !== maxWidth) picker.style.maxWidth = maxWidth;
        var rect = picker.getBoundingClientRect();
        var top = Math.max(8, Math.min(rect.top, window.innerHeight - 168));
        var left = Math.max(8, Math.min(rect.left, window.innerWidth - rect.width - 8));
        if (Math.abs(rect.top - top) > 1) picker.style.top = top + "px";
        if (Math.abs(rect.left - left) > 1) picker.style.left = left + "px";
        // Keep the full-width date fields clickable; scroll the popup's own
        // final rows instead of shifting it up across the departure field.
        var room = Math.floor(window.innerHeight - picker.getBoundingClientRect().top - 8);
        // Once capped, client/scroll height can collapse to the cap itself.
        // Keep that state stable instead of toggling max-height on every
        // observed style mutation (which would create an observer loop).
        var cap = room >= 160 && (picker.scrollHeight > room || picker.style.maxHeight) ? room + "px" : "";
        if (picker.style.maxHeight !== cap) picker.style.maxHeight = cap;
        var overflow = cap ? "auto" : "";
        if (picker.style.overflowY !== overflow) picker.style.overflowY = overflow;
        // PopupContent is a separate, overflow:hidden layer with a 100%
        // height. Capping only the outer root hides its last dates instead
        // of making them scrollable, so scroll this inner layer as well.
        var content = picker.querySelector(':scope > [data-tid="PopupContent"]');
        if (content && content.style.overflowY !== overflow) content.style.overflowY = overflow;
      });
    }

    function sync() {
      pending = false;
      if (!observer || !modal.open) return;
      var active = portals();
      var entered = false;
      if (active.length) {
        clearTimeout(vendorExitTimer);
        vendorExitTimer = null;
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
        fitRangePickers();
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
      } else if (suspended && !vendorExitTimer) {
        // Kontur briefly removes one date portal before mounting the next one
        // when the guest switches from arrival to departure. Restoring native
        // modality in that gap makes the whole widget visibly close and reopen.
        vendorExitTimer = setTimeout(function () {
          vendorExitTimer = null;
          if (!observer || !modal.open || !suspended || portals().length) return;
          suspended = false;
          modal.inert = false;
          restoreInert();
          modal.classList.remove("booking-system--vendor-open");
          switchMode(true);
          modal.scrollTop = scrollTop;
          focus(modal.contains(returnFocus) ? returnFocus : modal.querySelector("[data-booking-close]"));
          returnFocus = null;
        }, 250);
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

    // Do not auto-hide on a timer after a day click: the SDK switches focus
    // to checkout and still needs the same popup for the second selection.
    // Only dismiss plain field calendars on an explicit outside click/Esc.
    function dismissRangePickers() {
      var dismissed = false;
      portals().forEach(function (container) {
        if (!container.querySelector('[data-tid="DateRangePicker__root"]')) return;
        if (container.querySelector('[data-tid="modal-content"][role="dialog"]')) return;
        container.hidden = true;
        hiddenRangePickContainers.add(container);
        dismissed = true;
      });
      return dismissed;
    }
    document.addEventListener("click", function (event) {
      if (!modal.open) return;
      var dateField = event.target.closest('[data-tid="DateRangePicker__start"], [data-tid="DateRangePicker__end"]');
      if (dateField && modal.contains(dateField)) {
        hiddenRangePickContainers.forEach(function (container) {
          if (container.isConnected) container.hidden = false;
        });
        hiddenRangePickContainers.clear();
        return;
      }
      // Month/year dropdowns are separate vendor portals too.
      if (event.target.closest(".react-ui")) return;
      dismissRangePickers();
    }, true);
    document.addEventListener("keydown", function (event) {
      if (!modal.open || event.key !== "Escape" || event.defaultPrevented) return;
      var active = portals();
      // Nested menus/dialogs handle Escape themselves first.
      if (active.some(function (container) { return container.querySelector('[role="listbox"], [role="menu"], [role="dialog"]'); })) return;
      if (dismissRangePickers()) {
        event.preventDefault();
        event.stopPropagation();
      }
    });

    return {
      open: function () {
        if (observer) return;
        // Preserve the SDK state, but never leave its popups floating after
        // the outer dialog is closed (for example while its date picker is open).
        parkedPortals.forEach(function (hidden, element) {
          if (element.isConnected) element.hidden = hidden;
        });
        parkedPortals.clear();
        observer = new MutationObserver(function (mutations) {
          fitRangePickers();
          if (!pending) { pending = true; requestAnimationFrame(sync); }
        });
        observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["style", "class", "hidden"] });
        document.addEventListener("keydown", trapTab);
        window.addEventListener("resize", fitRangePickers);
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
        window.removeEventListener("resize", fitRangePickers);
        clearTimeout(vendorExitTimer);
        vendorExitTimer = null;
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
