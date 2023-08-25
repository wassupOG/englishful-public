"use strict";
import { clearFormatting, editContents, selectAll } from "./adminDictionary.js";
import { manageLandingButtons, showPopup, closePopup, hashLoad } from "./index.js";
import { fold, updateGrades, preventSubmit, foldTable } from "./tests.js";
import { sayWord, speechSynthesis, trainCards } from "./userDictionary.js";

// Logo click
document.getElementById("logo").addEventListener("click", () => (window.location.href = "/"));

// Load sections
hashLoad();

// Buttons landing
manageLandingButtons();

// POPUPS
showPopup();
closePopup();

// Folding elements
fold();

// Folding Study Plan Table
foldTable();

// Form submission
preventSubmit();

// Edit marks
updateGrades();

// Dictionary
if (window.location.href.includes("dictionary")) {
  trainCards();
  sayWord();
  speechSynthesis();
  clearFormatting();
  editContents();
  selectAll();
}
