document.addEventListener("DOMContentLoaded", () => {
  const passportSeriesInput = document.getElementById("id_passport_series_number");
  if (!passportSeriesInput) {
    return;
  }

  const passportTypeInputId = passportSeriesInput.dataset.passportTypeInputId || "id_passport_type";
  const passportTypeInput = document.getElementById(passportTypeInputId);
  if (!passportTypeInput) {
    return;
  }

  const passportSeriesLabel = document.querySelector(`label[for="${passportSeriesInput.id}"]`);
  if (!passportSeriesLabel) {
    return;
  }

  const labelSeries = passportSeriesInput.dataset.labelSeries || "Серія та номер";
  const labelNumber = passportSeriesInput.dataset.labelNumber || "Номер";
  const typeBookValue = passportSeriesInput.dataset.passportTypeValueBook || "Книжечка";
  const typeIdValue = passportSeriesInput.dataset.passportTypeValueId || "ID-картка";

  const trim = (value) => (value || "").trim();

  const updateLabel = () => {
    const currentType = trim(passportTypeInput.value);
    if (currentType === typeIdValue) {
      passportSeriesLabel.textContent = labelNumber;
    } else {
      passportSeriesLabel.textContent = labelSeries;
    }
  };

  passportTypeInput.addEventListener("change", () => {
    updateLabel();
  });

  updateLabel();
});
