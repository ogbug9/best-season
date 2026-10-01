/* Порог уверенного жеста тачпада: 120 px за 400 мс, пауза 700 мс. */
(function (root) {
  'use strict';
  function createScrollIntent() {
    var samples = [], blockedUntil = 0;
    return {
      reset: function () { samples = []; },
      block: function (now) { samples = []; blockedUntil = now + 700; },
      push: function (delta, now) {
        if (!Number.isFinite(delta) || !delta || now < blockedUntil) return false;
        if (samples.length && Math.sign(samples[samples.length - 1].delta) !== Math.sign(delta)) samples = [];
        samples = samples.filter(function (sample) { return now - sample.at <= 400; });
        samples.push({ delta: delta, at: now });
        var sum = samples.reduce(function (total, sample) { return total + sample.delta; }, 0);
        if (Math.abs(sum) < 120) return false;
        samples = [];
        blockedUntil = now + 700;
        return true;
      }
    };
  }
  if (typeof module === 'object' && module.exports) module.exports = createScrollIntent;
  else root.BSScrollIntent = createScrollIntent;
})(typeof window === 'object' ? window : globalThis);
