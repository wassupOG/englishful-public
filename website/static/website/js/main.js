"use strict";
import { clearFormatting, editContents, selectAll } from "./adminDictionary.js";
import { manageLandingButtons, showPopup, closePopup, hashLoad } from "./landingPage.js";
import { fold, updateGrades, preventSubmit, foldTable } from "./tests.js";
import { sayUtterance, setupSpeechSynthesis, trainCards } from "./userDictionary.js";

// Logo click
document.getElementById("logo").addEventListener("click", () => (window.location.href = "/"));

// Load hashed sections
hashLoad();

// Managing buttons & displaying sections corresponding to them
manageLandingButtons();

// POPUPS: show & close
showPopup();
closePopup();

// Folding elements
fold();

// Folding Study Plan Table
foldTable();

// Prevent accidental form submissions & window unloading events
preventSubmit();

// Edit grades in teacher profile
updateGrades();

// Dictionary
if (window.location.href.includes("dictionary")) {
  trainCards();
  sayUtterance();
  setupSpeechSynthesis();
  clearFormatting();
  editContents();
  selectAll();
}
