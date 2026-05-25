(function () {
  function insertSnippet(textarea, snippet) {
    var start = textarea.selectionStart || 0;
    var end = textarea.selectionEnd || 0;
    var value = textarea.value;
    var before = value.slice(0, start);
    var after = value.slice(end);
    var prefix = before && !before.endsWith("\n") ? "\n" : "";
    var suffix = after && !after.startsWith("\n") ? "\n" : "";
    var inserted = prefix + snippet + suffix;

    textarea.value = before + inserted + after;
    textarea.focus();
    textarea.selectionStart = textarea.selectionEnd = start + inserted.length;
  }

  document.addEventListener("click", function (event) {
    var insertButton = event.target.closest("[data-media-insert]");
    if (insertButton) {
      var textarea = document.getElementById("body");
      var snippet = insertButton.getAttribute("data-media-snippet") || "";
      if (textarea && snippet) {
        insertSnippet(textarea, snippet);
      }
      return;
    }

    var copyButton = event.target.closest("[data-media-copy]");
    if (copyButton && navigator.clipboard) {
      var copyText = copyButton.getAttribute("data-media-snippet") || "";
      if (copyText) {
        navigator.clipboard.writeText(copyText);
      }
    }
  });
})();
