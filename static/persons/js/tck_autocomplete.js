(function () {
  "use strict";

  const MAX_SUGGESTIONS = 25;

  function normalise(value) {
    return value.toLocaleLowerCase("uk-UA");
  }

  function prepareMatches(options, query) {
    if (!query) {
      return options.slice(0, MAX_SUGGESTIONS);
    }
    const search = normalise(query.trim());
    if (!search) {
      return options.slice(0, MAX_SUGGESTIONS);
    }
    return options
      .map((option, index) => {
        const lower = normalise(option);
        const startIndex = lower.indexOf(search);
        const score = startIndex === -1 ? Infinity : startIndex;
        return { option, score, index };
      })
      .filter((item) => Number.isFinite(item.score))
      .sort((a, b) => {
        if (a.score !== b.score) {
          return a.score - b.score;
        }
        return a.index - b.index;
      })
      .slice(0, MAX_SUGGESTIONS)
      .map((item) => item.option);
  }

  function populateDatalist(datalist, matches) {
    while (datalist.firstChild) {
      datalist.removeChild(datalist.firstChild);
    }
    matches.forEach((match) => {
      const option = document.createElement("option");
      option.value = match;
      datalist.appendChild(option);
    });
  }

  function initAutocomplete(input) {
    const optionsId = input.getAttribute("data-tck-options-id");
    if (!optionsId) {
      return;
    }
    const script = document.getElementById(optionsId);
    if (!script) {
      return;
    }
    let options;
    try {
      options = JSON.parse(script.textContent);
    } catch (error) {
      console.error("Не вдалося розпарсити список ТЦК:", error);
      return;
    }
    if (!Array.isArray(options) || options.length === 0) {
      return;
    }

    const datalistId = input.getAttribute("list");
    if (!datalistId) {
      return;
    }
    const datalist = document.getElementById(datalistId);
    if (!datalist) {
      return;
    }

    const render = (currentValue) => {
      populateDatalist(datalist, prepareMatches(options, currentValue));
    };

    render(input.value || "");

    input.addEventListener("input", (event) => {
      render(event.target.value || "");
    });

    input.addEventListener("focus", () => {
      render(input.value || "");
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document
      .querySelectorAll('input[data-tck-autocomplete="true"]')
      .forEach((input) => initAutocomplete(input));
  });
})();
