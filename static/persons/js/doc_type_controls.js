document.addEventListener("DOMContentLoaded", () => {
  const docSeriesInput = document.getElementById("id_doc_series_number");
  if (!docSeriesInput) {
    return;
  }
  const docTypeInput =
    document.getElementById(docSeriesInput.dataset.docTypeInputId || "id_doc_type") || null;
  const edrpvrInput =
    document.getElementById(docSeriesInput.dataset.edrpvrInputId || "id_edrpvr_number") || null;
  if (!docTypeInput) {
    return;
  }
  const docSeriesLabel = document.querySelector(`label[for="${docSeriesInput.id}"]`);
  if (!docSeriesLabel) {
    return;
  }

  const NUMBER_ONLY_TYPES = new Set(["Військово-обліковий документ", "Резерв+"]);
  const labelSeries = docSeriesInput.dataset.labelSeries || "Серія та номер";
  const labelNumber = docSeriesInput.dataset.labelNumber || "Номер";
  const placeholderSeries = docSeriesInput.dataset.placeholderSeries || "";
  const placeholderNumber = docSeriesInput.dataset.placeholderNumber || "";
  let lastSuggestedValue = null;

  const trim = (value) => (value || "").trim();
  const isNumberMode = () => NUMBER_ONLY_TYPES.has(trim(docTypeInput.value));

  const setPlaceholder = (value) => {
    if (value) {
      docSeriesInput.setAttribute("placeholder", value);
    } else {
      docSeriesInput.removeAttribute("placeholder");
    }
  };

  const suggestFromEdrpvr = ({ allowOverride = false } = {}) => {
    if (!edrpvrInput) {
      return;
    }
    const edrpvrValue = trim(edrpvrInput.value);
    if (!edrpvrValue) {
      return;
    }
    const currentValue = docSeriesInput.value;
    const currentTrimmed = trim(currentValue);
    if (!currentTrimmed) {
      docSeriesInput.value = edrpvrValue;
      lastSuggestedValue = edrpvrValue;
      return;
    }
    if (allowOverride && currentValue === lastSuggestedValue) {
      docSeriesInput.value = edrpvrValue;
      lastSuggestedValue = edrpvrValue;
    }
  };

  const applyNumberMode = ({ prefill = false } = {}) => {
    docSeriesLabel.textContent = labelNumber;
    setPlaceholder(placeholderNumber);
    if (prefill) {
      suggestFromEdrpvr({ allowOverride: false });
    }
  };

  const applySeriesMode = () => {
    docSeriesLabel.textContent = labelSeries;
    setPlaceholder(placeholderSeries);
    lastSuggestedValue = null;
  };

  const updateMode = ({ prefill = false } = {}) => {
    if (isNumberMode()) {
      applyNumberMode({ prefill });
    } else {
      applySeriesMode();
    }
  };

  docTypeInput.addEventListener("change", () => {
    updateMode({ prefill: true });
  });

  if (edrpvrInput) {
    edrpvrInput.addEventListener("input", () => {
      if (!isNumberMode()) {
        return;
      }
      suggestFromEdrpvr({ allowOverride: true });
    });
  }

  docSeriesInput.addEventListener("input", () => {
    if (docSeriesInput.value !== lastSuggestedValue) {
      lastSuggestedValue = null;
    }
  });

  updateMode({ prefill: true });
});
