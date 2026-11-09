// Plotly can measure its container before layout settles (e.g. right after a report re-renders),
// leaving charts squashed. Nudge it to re-measure once the DOM and fonts are stable.
(function () {
  var timer = null;
  function nudge() {
    [60, 400, 1200].forEach(function (delay) {
      setTimeout(function () { window.dispatchEvent(new Event("resize")); }, delay);
    });
  }
  function watch() {
    var panel = document.getElementById("report-panel");
    if (!panel) { return setTimeout(watch, 200); }
    new MutationObserver(function () {
      clearTimeout(timer);
      timer = setTimeout(nudge, 50);
    }).observe(panel, { childList: true });
    nudge();
  }
  window.addEventListener("load", watch);
})();
