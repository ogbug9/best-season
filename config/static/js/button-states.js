/* Реальные состояния отправки заявки; открытие бронирования не означает успех. */
(function () {
  'use strict';
  var originals = new WeakMap();
  function set(button, state) {
    if (!button || !button.matches('.btn') || button.closest('.kontur-host, .react-ui')) return;
    var host = button.matches('button') ? button : button.closest('button');
    if (!originals.has(button)) originals.set(button, {
      html: button.innerHTML, minWidth: button.style.minWidth, minHeight: button.style.minHeight,
      disabled: host ? host.disabled : false,
      ariaDisabled: button.getAttribute('aria-disabled'), busy: button.getAttribute('aria-busy')
    });
    var original = originals.get(button);
    button.classList.remove('is-loading', 'is-success');
    button.removeAttribute('data-state');
    if (state !== 'loading' && state !== 'success') {
      button.innerHTML = original.html;
      button.style.minWidth = original.minWidth;
      button.style.minHeight = original.minHeight;
      if (host) host.disabled = original.disabled;
      ['aria-disabled', 'aria-busy'].forEach(function (attr) {
        var value = attr === 'aria-disabled' ? original.ariaDisabled : original.busy;
        if (value === null) button.removeAttribute(attr); else button.setAttribute(attr, value);
      });
      originals.delete(button);
      return;
    }
    var box = button.getBoundingClientRect();
    if (!button.style.minWidth && box.width > 0) button.style.minWidth = box.width + 'px';
    if (!button.style.minHeight && box.height > 0) button.style.minHeight = box.height + 'px';
    button.classList.add('is-' + state);
    button.setAttribute('data-state', state);
    button.setAttribute('aria-disabled', 'true');
    button.setAttribute('aria-busy', state === 'loading' ? 'true' : 'false');
    if (host) host.disabled = true;
    button.textContent = state === 'loading' ? 'Загрузка' : button.matches('.btn--primary') && (host || button).matches('[data-booking-open]') ? 'Забронировано' : 'Успешно';
  }
  window.BSButtonState = set;
  document.querySelectorAll('[data-request-form][data-confirmed-success] button[type="submit"]').forEach(function (button) {
    set(button, 'success');
  });
  document.addEventListener('click', function (event) {
    var target = event.target.closest('.btn, button, summary, label');
    if (!target || target.closest('.kontur-host, .react-ui')) return;
    var selector = '.btn:is(.is-loading, .is-success, [data-state="loading"], [data-state="success"], [aria-disabled="true"])';
    if (target.matches(selector) || target.querySelector(selector)) {
      event.preventDefault(); event.stopImmediatePropagation();
    }
  }, true);
  document.addEventListener('submit', function (event) {
    var form = event.target;
    if (!form.matches('[data-request-form]')) return;
    if (form.dataset.submitting) { event.preventDefault(); return; }
    form.dataset.submitting = 'true';
    set(event.submitter || form.querySelector('button[type="submit"]'), 'loading');
  });
  window.addEventListener('pageshow', function () {
    document.querySelectorAll('[data-request-form][data-submitting]').forEach(function (form) {
      delete form.dataset.submitting;
      set(form.querySelector('button[type="submit"]'), 'default');
    });
  });
})();
