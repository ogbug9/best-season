(function () {
  "use strict";
  document.querySelectorAll("[data-nearby-open]").forEach(function (link) {
    var dialog = document.getElementById(link.getAttribute("data-nearby-open"));
    if (!dialog || typeof dialog.showModal !== "function") return;
    link.addEventListener("click", function (event) {
      event.preventDefault();
      dialog.showModal();
      dialog.querySelector("[data-nearby-close]").focus();
    });
    dialog.querySelector("[data-nearby-close]").addEventListener("click", function () {
      dialog.close();
    });
    dialog.addEventListener("close", function () { link.focus(); });
  });
}());
