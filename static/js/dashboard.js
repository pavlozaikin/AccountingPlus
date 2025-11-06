(function () {
  function setHeights() {
    var header = document.getElementById('siteHeader');
    var footer = document.getElementById('siteFooter');
    var root = document.documentElement;
    if (header) {
      root.style.setProperty('--app-header-h', header.offsetHeight + 'px');
    }
    if (footer) {
      root.style.setProperty('--app-footer-h', footer.offsetHeight + 'px');
    }
  }
  window.addEventListener('load', setHeights);
  window.addEventListener('resize', setHeights);
  setHeights();
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
  var resultsContainer = document.querySelector('[data-person-search-results]');
  var debounceTimer = null;
  var lastSubmitted = searchInput.value.trim();
  var activeToken = null;
  var supportsDynamicUpdate = Boolean(resultsContainer && window.fetch && window.DOMParser);

  function updateClearVisibility() {
    if (!clearButton) {
      return;
    }
    clearButton.hidden = searchInput.value.trim() === '';
  }

  function buildTargetUrl() {
    var actionAttr = searchForm.getAttribute('action') || searchForm.action || window.location.href;
    var url = new URL(actionAttr, window.location.origin);
    var formData = new FormData(searchForm);
    var params = new URLSearchParams(formData);
    url.search = params.toString();
    return url.toString();
  }

  function replaceResults(html) {
    if (!resultsContainer) {
      return false;
    }
    var parser = new DOMParser();
    var doc = parser.parseFromString(html, 'text/html');
    var nextContainer = doc.querySelector('[data-person-search-results]');
    if (!nextContainer) {
      return false;
    }
    resultsContainer.replaceWith(nextContainer);
    resultsContainer = nextContainer;
    return true;
  }

  function updateHistory(url) {
    if (!window.history || typeof window.history.replaceState !== 'function') {
      return;
    }
    window.history.replaceState(null, '', url);
  }

  function submitForm(force) {
    var currentValue = searchInput.value.trim();
    if (!force && currentValue === lastSubmitted) {
      return;
    }
    lastSubmitted = currentValue;
    var targetUrl = buildTargetUrl();

    if (!supportsDynamicUpdate) {
      window.location.href = targetUrl;
      return;
    }

    var requestToken = String(Date.now());
    activeToken = requestToken;

    fetch(targetUrl, {
      method: 'GET',
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Failed to fetch search results');
        }
        return response.text();
      })
      .then(function (html) {
        if (activeToken !== requestToken) {
          return;
        }
        if (!replaceResults(html)) {
          window.location.href = targetUrl;
          return;
        }
        updateHistory(targetUrl);
      })
      .catch(function () {
        window.location.href = targetUrl;
      });
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

  searchForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
    submitForm(true);
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
