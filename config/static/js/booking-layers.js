/* Stable booking layer: provider menus, dialogs and YARL photos stay above
   the shell without moving SDK nodes or reopening dialogs on focus changes. */
(function () {
  "use strict";
  window.BookingLayers = function (modal) {
    var observer = null;
    var pending = false;
    var backdrop = null;
    var focusedInner = null;
    var hadPortals = false;
    var returnFocus = null;
    var inertElements = new Map();
    var parkedPortals = new Map();
    var hiddenRangePickContainers = new Set();
    var selector = 'body > .react-ui, .react-ui[data-rendered-container-id], body > .yarl__portal';

    function portals() {
      return Array.from(document.querySelectorAll(selector)).filter(function (container, i, all) {
        return all.indexOf(container) === i && !container.hidden &&
          container.getClientRects().length && Array.from(container.children).some(function (child) {
            var style = getComputedStyle(child);
            return child.getClientRects().length && style.display !== "none" && style.visibility !== "hidden";
          });
      });
    }
    function focus(element) {
      if (element && element.isConnected) element.focus({ preventScroll: true });
    }
    function restoreInert() {
      inertElements.forEach(function (value, element) { element.inert = value; });
      inertElements.clear();
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
        // Only push the popup up when it would run off the bottom. Never pin
        // it to the top edge: the SDK moves it together with its date field
        // while the booking window scrolls, and a top clamp left it hanging
        // over the site header after the field had scrolled away (live bug).
        var top = Math.min(rect.top, window.innerHeight - 168);
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
      if (active.length && !hadPortals) returnFocus = document.activeElement;
      Array.from(document.body.children).forEach(function (element) {
        if (element === modal || element === backdrop || element.matches(selector) || /^(SCRIPT|STYLE|LINK)$/.test(element.tagName)) return;
        if (!inertElements.has(element)) inertElements.set(element, element.inert);
        if (!element.inert) element.inert = true;
      });
      var inner = active.map(function (container) {
        return container.matches('.yarl__portal') ? container : container.querySelector('[data-tid="modal-content"][role="dialog"]');
      }).filter(Boolean).pop();
      modal.inert = Boolean(inner);
      fitRangePickers();
      if (inner && inner !== focusedInner && !active.some(function (root) { return root.contains(document.activeElement); })) {
        var control = inner.querySelector('button:not([disabled]), input:not([type="hidden"]):not([disabled]), [tabindex="0"]');
        focus(control || inner);
      }
      if (hadPortals && !active.length) {
        var dateField = returnFocus && returnFocus.closest('[data-tid="DateRangePicker__start"], [data-tid="DateRangePicker__end"]');
        var form = dateField && dateField.closest('[data-booking-host], .kontur-host');
        if (form) focus(Array.from(form.querySelectorAll('button')).filter(function (button) { return !button.closest('[data-tid^="DateRangePicker"]'); })[0]);
        else if (document.activeElement === document.body || document.activeElement.closest('[inert]')) focus(modal.querySelector('[data-booking-close]'));
      }
      hadPortals = active.length > 0;
      focusedInner = inner;
    }
    function trapTab(event) {
      if (event.key !== "Tab" || !observer) return;
      var active = portals();
      var roots = modal.inert ? active : [modal].concat(active);
      var controls = roots.flatMap(function (root) { return Array.from(root.querySelectorAll('button, input, select, textarea, a[href], [tabindex]')); })
        .filter(function (element) { return element.tabIndex >= 0 && !element.disabled && !element.closest('[inert]') && element.getClientRects().length && getComputedStyle(element).visibility !== "hidden"; });
      var first = controls[0], last = controls[controls.length - 1];
      if (!first) return;
      var current = document.activeElement;
      if (event.shiftKey && (current === first || controls.indexOf(current) < 0)) { event.preventDefault(); focus(last); }
      else if (!event.shiftKey && (current === last || controls.indexOf(current) < 0)) { event.preventDefault(); focus(first); }
    }
    function dismissRangePickers() {
      var dismissed = false;
      portals().forEach(function (container) {
        if (!container.querySelector('[data-tid="DateRangePicker__root"]') || container.querySelector('[data-tid="modal-content"][role="dialog"]')) return;
        container.hidden = true;
        hiddenRangePickContainers.add(container);
        dismissed = true;
      });
      return dismissed;
    }
    document.addEventListener("click", function (event) {
      if (!modal.open) return;
      var dateField = event.target.closest('[data-tid="DateRangePicker__start"], [data-tid="DateRangePicker__end"]');
      if (dateField) {
        hiddenRangePickContainers.forEach(function (container) { if (container.isConnected) container.hidden = false; });
        hiddenRangePickContainers.clear();
        return;
      }
      if (!event.target.closest('.react-ui, .yarl__portal')) dismissRangePickers();
    }, true);
    document.addEventListener("keydown", function (event) {
      if (!observer || !modal.open || event.key !== "Escape" || event.defaultPrevented) return;
      var active = portals();
      if (active.some(function (root) { return root.matches('.yarl__portal') || !root.querySelector('[data-tid="DateRangePicker__root"]') || root.querySelector('[role="listbox"], [role="menu"], [role="dialog"]'); })) return;
      event.preventDefault();
      if (!dismissRangePickers()) modal.close();
    }, true);
    return {
      open: function () {
        if (observer) return;
        parkedPortals.forEach(function (hidden, element) { if (element.isConnected) element.hidden = hidden; });
        parkedPortals.clear();
        modal.classList.add("booking-system--layered");
        modal.setAttribute("aria-modal", "true");
        backdrop = document.createElement("div");
        backdrop.className = "booking-system-backdrop";
        backdrop.setAttribute("aria-hidden", "true");
        backdrop.addEventListener("click", function () { if (!modal.inert) modal.close(); });
        document.body.appendChild(backdrop);
        observer = new MutationObserver(function () { if (!pending) { pending = true; queueMicrotask(sync); } });
        observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["style", "class", "hidden"] });
        document.addEventListener("keydown", trapTab);
        window.addEventListener("resize", fitRangePickers);
        sync();
        focus(modal.querySelector('[data-booking-close]'));
      },
      close: function () {
        if (observer) observer.disconnect();
        portals().forEach(function (element) { parkedPortals.set(element, element.hidden); element.hidden = true; });
        document.removeEventListener("keydown", trapTab);
        window.removeEventListener("resize", fitRangePickers);
        if (backdrop) backdrop.remove();
        backdrop = null;
        observer = null;
        pending = false;
        focusedInner = null;
        hadPortals = false;
        returnFocus = null;
        modal.inert = false;
        restoreInert();
        modal.classList.remove("booking-system--layered");
        modal.removeAttribute("aria-modal");
        return true;
      },
      ownsPopup: function () { return portals().length > 0; }
    };
  };
})();
