(function () {
  var navbar = document.querySelector(".navbar");
  var toggle = document.querySelector(".nav-toggle");
  var links = document.getElementById("site-nav-links");

  if (!navbar || !toggle || !links) {
    return;
  }

  function setExpanded(isExpanded) {
    navbar.classList.toggle("is-open", isExpanded);
    toggle.setAttribute("aria-expanded", isExpanded ? "true" : "false");
  }

  toggle.addEventListener("click", function () {
    setExpanded(toggle.getAttribute("aria-expanded") !== "true");
  });

  links.addEventListener("click", function (event) {
    if (event.target.closest("a")) {
      setExpanded(false);
    }
  });
})();
