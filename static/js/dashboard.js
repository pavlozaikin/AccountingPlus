(function () {
  function setHeights() {
    var header = document.getElementById('siteHeader');
    var footer = document.getElementById('siteFooter');
    var root = document.documentElement;
    root.style.setProperty('--header-h', header ? header.offsetHeight + 'px' : '0px');
    root.style.setProperty('--footer-h', footer ? footer.offsetHeight + 'px' : '0px');
  }
  window.addEventListener('load', setHeights);
  window.addEventListener('resize', setHeights);
})();

(function () {
  var searchForm = document.querySelector('[data-person-search-form]');
  if (!searchForm) {
    return;
  }

  var searchInput = searchForm.querySelector('[data-person-search-input]');
  if (!searchInput) {
    return;
  }

  var clearButton = searchForm.querySelector('[data-person-search-clear]');
  var debounceTimer = null;
  var lastSubmitted = searchInput.value.trim();

  function submitForm(force) {
    var currentValue = searchInput.value.trim();
    if (!force && currentValue === lastSubmitted) {
      return;
    }
    lastSubmitted = currentValue;
    if (typeof searchForm.requestSubmit === 'function') {
      searchForm.requestSubmit();
    } else {
      searchForm.submit();
    }
  }

  function updateClearVisibility() {
    if (!clearButton) {
      return;
    }
    clearButton.hidden = searchInput.value.trim() === '';
  }

  updateClearVisibility();

  searchInput.addEventListener('input', function () {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    updateClearVisibility();
    debounceTimer = setTimeout(function () {
      submitForm(false);
    }, 350);
  });

  if (clearButton) {
    clearButton.addEventListener('click', function (event) {
      event.preventDefault();
      if (debounceTimer) {
        clearTimeout(debounceTimer);
        debounceTimer = null;
      }
      searchInput.value = '';
      updateClearVisibility();
      submitForm(true);
      searchInput.focus();
    });
  }
})();
