"use strict";
const LANDING_SECTIONS = document.querySelectorAll('[data-type="landingSection"]');
const PRICING_SECTIONS = document.querySelectorAll('[data-type="pricingSection"]');
const LANDING_BUTTONS = document.querySelectorAll('[data-type="landingButton"]');
const PRICING_BUTTONS = document.querySelectorAll('[data-type="pricingButton"]');
export const BUTTONS = [...LANDING_BUTTONS, ...PRICING_BUTTONS];

// Manage class of buttons
export function manageLandingButtons() {
  if (!BUTTONS || BUTTONS.length === 0) return;

  BUTTONS.forEach((button) => {
    button.addEventListener("click", (event) => {
      landingButtonRemoveClass(event);
      landingShowSection(button.dataset.corresponding, button.dataset.type);
    });
  });
}

export function landingButtonRemoveClass(event) {
  if (event.target.dataset.type === "landingButton") {
    LANDING_BUTTONS.forEach((button) => button.classList.remove("active"));
    event.target.classList.add("active");
  } else if (event.target.dataset.type === "pricingButton") {
    PRICING_BUTTONS.forEach((button) => button.classList.remove("active-prices"));
    event.target.classList.add("active-prices");
  }
}

export function landingShowSection(sectionID, buttonType) {
  if (buttonType === "landingButton") {
    LANDING_SECTIONS.forEach((section) => (section.style.display = "none"));
  } else if (buttonType === "pricingButton") {
    PRICING_SECTIONS.forEach((section) => (section.style.display = "none"));
  }

  const displayedSection = document.querySelector(`[data-section="${sectionID}"]`);
  displayedSection.style.display = "block";
  const offset = displayedSection.getBoundingClientRect().top + window.scrollY - 250;
  window.scrollTo({ top: offset, behavior: "smooth" });
}

// hash
export function hashLoad() {
  window.addEventListener("load", () => {
    const hash = window.location.hash;
    if (hash) {
      const hashSections = hash.split("/").map((section) => section.replace(/^[^a-zA-Z]*/, ""));
      console.log(hashSections);
      if (hashSections.length > 1) {
        hashSections.forEach((section) => document.querySelector(`[data-corresponding="${section}"]`).click());
      } else {
        document.querySelector(`[data-corresponding="${hashSections[0]}"]`).click();
      }
    }
  });
}

// Popups
const overlay = document.querySelector("#overlay");

export function showPopup() {
  const popupButtons = document.querySelectorAll(["[data-target-popup]"]);
  popupButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const displayedPopup = document.querySelector(button.dataset.targetPopup);
      if (displayedPopup == null) return;
      displayedPopup.classList.add("active-popup");
      overlay.classList.add("active-overlay");
    });
  });
}

export function closePopup() {
  const closeButtons = document.querySelectorAll(["[data-close-button]"]);
  closeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const closedPopup = button.closest(".popup-container");
      if (closedPopup == null) return;
      closedPopup.classList.remove("active-popup");
      overlay.classList.remove("active-overlay");
    });
  });

  if (overlay) {
    overlay.addEventListener("click", () => {
      document.querySelectorAll(".popup-container.active-popup").forEach((closedPopup) => {
        closedPopup.classList.remove("active-popup");
        overlay.classList.remove("active-overlay");
      });
    });
  }
}
