(function () {
  "use strict";

  var FORM_SELECTOR = "form.wpcf7-form";
  var ENDPOINT = "/contact-submit.php";

  function languageFor(form) {
    var field = form.querySelector('[name="trp-form-language"]');
    if (field && field.value === "en") return "en";
    return document.documentElement.lang && document.documentElement.lang.indexOf("en") === 0 ? "en" : "de";
  }

  function messages(form) {
    return languageFor(form) === "en"
      ? {
          sending: "Sending…",
          success: "Thank you. Your message has been sent successfully.",
          error: "Your message could not be sent. Please try again or email info@ai-experts.network directly.",
          invalid: "Please complete all required fields and enter a valid email address."
        }
      : {
          sending: "Wird gesendet…",
          success: "Vielen Dank. Ihre Nachricht wurde erfolgreich gesendet.",
          error: "Ihre Nachricht konnte nicht gesendet werden. Bitte versuchen Sie es erneut oder schreiben Sie direkt an info@ai-experts.network.",
          invalid: "Bitte füllen Sie alle Pflichtfelder aus und geben Sie eine gültige E-Mail-Adresse ein."
        };
  }

  function outputFor(form) {
    var output = form.querySelector(".wpcf7-response-output");
    if (!output) {
      output = document.createElement("div");
      output.className = "wpcf7-response-output";
      form.appendChild(output);
    }
    output.setAttribute("role", "status");
    output.setAttribute("aria-live", "polite");
    return output;
  }

  function showStatus(form, text, status) {
    var output = outputFor(form);
    output.textContent = text;
    output.style.display = "block";
    form.setAttribute("data-status", status);
  }

  function requiredFieldsAreValid(form) {
    var valid = true;
    var required = form.querySelectorAll('input[aria-required="true"], select[aria-required="true"], textarea[aria-required="true"]');

    Array.prototype.forEach.call(required, function (field) {
      var empty = field.type === "checkbox" ? !field.checked : !field.value.trim();
      field.setCustomValidity(empty ? "required" : "");
      if (!field.checkValidity()) valid = false;
    });

    var email = form.querySelector('input[type="email"]');
    if (email && !email.checkValidity()) valid = false;

    var checkboxGroups = form.querySelectorAll(".wpcf7-checkbox.wpcf7-validates-as-required");
    Array.prototype.forEach.call(checkboxGroups, function (group) {
      var first = group.querySelector('input[type="checkbox"]');
      var checked = group.querySelector('input[type="checkbox"]:checked');
      if (first) {
        first.setCustomValidity(checked ? "" : "required");
        if (!checked) valid = false;
      }
    });

    if (!valid && typeof form.reportValidity === "function") form.reportValidity();
    return valid;
  }

  function installSpamFields(form) {
    if (!form.querySelector('[name="website"]')) {
      var honeypot = document.createElement("input");
      honeypot.type = "text";
      honeypot.name = "website";
      honeypot.tabIndex = -1;
      honeypot.autocomplete = "off";
      honeypot.setAttribute("aria-hidden", "true");
      honeypot.style.position = "absolute";
      honeypot.style.left = "-10000px";
      honeypot.style.width = "1px";
      honeypot.style.height = "1px";
      form.appendChild(honeypot);
    }

    if (!form.querySelector('[name="form_started_at"]')) {
      var started = document.createElement("input");
      started.type = "hidden";
      started.name = "form_started_at";
      started.value = String(Date.now());
      form.appendChild(started);
    }
  }

  function submitForm(event) {
    var form = event.target;
    if (!form.matches(FORM_SELECTOR)) return;

    event.preventDefault();
    event.stopImmediatePropagation();

    var copy = messages(form);
    if (!requiredFieldsAreValid(form)) {
      showStatus(form, copy.invalid, "invalid");
      return;
    }

    installSpamFields(form);
    var submit = form.querySelector('[type="submit"]');
    var originalLabel = submit ? submit.value : "";
    if (submit) {
      submit.disabled = true;
      submit.value = copy.sending;
    }
    showStatus(form, copy.sending, "submitting");

    var data = new FormData(form);
    data.set("source_page", window.location.href);

    fetch(ENDPOINT, {
      method: "POST",
      body: data,
      credentials: "same-origin",
      headers: { Accept: "application/json" }
    })
      .then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (body) {
          if (!response.ok || !body.success) throw new Error(body.message || "mail_failed");
          return body;
        });
      })
      .then(function () {
        showStatus(form, copy.success, "sent");
        form.reset();
        var started = form.querySelector('[name="form_started_at"]');
        if (started) started.value = String(Date.now());

        var formId = form.querySelector('[name="_wpcf7"]');
        document.dispatchEvent(new CustomEvent("wpcf7mailsent", {
          detail: { contactFormId: formId ? formId.value : "" }
        }));
      })
      .catch(function () {
        showStatus(form, copy.error, "failed");
      })
      .then(function () {
        if (submit) {
          submit.disabled = false;
          submit.value = originalLabel;
        }
      });
  }

  Array.prototype.forEach.call(document.querySelectorAll(FORM_SELECTOR), installSpamFields);
  // Capture at window level so the archived Contact Form 7 handler cannot
  // forward the submission to the former WordPress REST API.
  window.addEventListener("submit", submitForm, true);
})();
