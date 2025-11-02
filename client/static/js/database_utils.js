/**
 * This module stores all required methods in the frontend to communicate with the database.
 */

/**
 * This method is responsible for displaying popup whether user wants to save
 * their data in the database after clicking submit button in the new_analysis page.
 * Depending on the user's choice, a hidden input is added to the form to indicate consent/disagreement
 * before submitting the form. This form will be used in the backend by flask (/protect) to save data in the db.
 */
document.addEventListener("DOMContentLoaded", () => {
  const submitBtn = document.getElementById("submit-analysis-btn");
  const confirmSaveBtn = document.getElementById("confirm-save-btn");
  const form = document.getElementById("upload-form");
  const loadingOverlay = document.getElementById("loading-overlay");
  const agreeCheckbox = document.getElementById("agree-terms");
  // Disable submit button initially until terms are accepted
  if (agreeCheckbox) {
    submitBtn.disabled = !agreeCheckbox.checked;
    agreeCheckbox.addEventListener("change", () => {
      submitBtn.disabled = !agreeCheckbox.checked;
    });
  }

  // When user clicks Submit
  submitBtn.addEventListener("click", (e) => {
    e.preventDefault();
    // Check if terms and conditions are accepted
    if (agreeCheckbox && !agreeCheckbox.checked) {
      alert("Please agree to the DNAvi Terms and Conditions before submitting.");
      return;
    }
    // Check if form is valid (all required files are uploaded)
    // Do not allow submission if not valid
    if (!form.checkValidity()) {
      form.reportValidity(); 
      return;
    }
    // Form is valid, show the popup to ask do you want to save you data in the database?
    const modal = new bootstrap.Modal(document.getElementById("saveConsent"));
    modal.show();
  });
  // If user clicks yes, save my data
  confirmSaveBtn.addEventListener("click", () => {
    const hiddenInput = document.createElement("input");
    hiddenInput.type = "hidden";
    hiddenInput.name = "save_to_db";
    hiddenInput.value = "yes";
    form.appendChild(hiddenInput);
    loadingOverlay.style.display = "block";
    form.submit();
  });
  // If user clicks no
  document.querySelector('#saveConsent .btn-outline-secondary').addEventListener("click", () => {
    const hiddenInput = document.createElement("input");
    hiddenInput.type = "hidden";
    hiddenInput.name = "save_to_db";
    hiddenInput.value = "no";
    form.appendChild(hiddenInput);
    loadingOverlay.style.display = "block";
    form.submit();
  });
});