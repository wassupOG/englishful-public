"use strict";

// Folder
export const angleRight =
  '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M15.54 11.29L9.88 5.64a1 1 0 0 0-1.42 0a1 1 0 0 0 0 1.41l4.95 5L8.46 17a1 1 0 0 0 0 1.41a1 1 0 0 0 .71.3a1 1 0 0 0 .71-.3l5.66-5.65a1 1 0 0 0 0-1.47Z"/></svg>';

export function fold() {
  const folderElements = document.querySelectorAll(".folder");
  if (!folderElements || folderElements.length === 0) return;

  folderElements.forEach((folderElement) => {
    const content = folderElement.nextElementSibling;
    const angleElement = document.createElement("span");
    angleElement.classList.add("angle");
    angleElement.innerHTML = angleRight;
    folderElement.prepend(angleElement);

    folderElement.addEventListener("click", () => {
      if (content.style.maxHeight) {
        content.style.maxHeight = null;
        angleElement.classList.remove("down");
      } else {
        content.style.maxHeight = content.scrollHeight + "px";
        angleElement.classList.add("down");
      }
    });
  });
}

// Fold table
export function foldTable() {
  const headerFolder = document.querySelector("[data-table-header]");
  if (!headerFolder) return;

  const tableContent = document.querySelector("[data-table-content]");
  const angleElement = document.createElement("span");
  angleElement.classList.add("angle");
  angleElement.innerHTML = angleRight;
  headerFolder.prepend(angleElement);

  headerFolder.addEventListener("click", () => {
    tableContent.classList.toggle("hidden");
    if (tableContent.classList.contains("hidden")) {
      angleElement.classList.remove("down");
    } else {
      angleElement.classList.add("down");
    }
  });
}

// Update grades
export function updateGrades() {
  const gradeCells = document.querySelectorAll("[data-edit-grades]");
  if (!gradeCells || gradeCells.length === 0) return;

  gradeCells.forEach((cell) => {
    const initialGrade = cell.textContent;
    cell.addEventListener("blur", (event) => {
      const currentGrade = cell.textContent;
      if (parseInt(currentGrade) > 10 || parseInt(currentGrade) < 1) {
        alert("The grade must be within the range from 1 to 10!");
        return location.reload();
      }
      const id = event.target.dataset.gradeId;
      if (initialGrade !== currentGrade && currentGrade !== "") {
        fetch("/results_edit", {
          method: "POST",
          body: JSON.stringify({
            id: id,
            grade: currentGrade,
          }),
        })
          .then((response) => response.json())
          .then((response) => location.reload())
          .catch((error) => console.error(error));
      }
    });
  });
}

// Submit & Onbeforeunload
export function preventSubmit() {
  const form = document.querySelector("[data-test-form]");
  if (!form) return;
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const confirmed = window.confirm("Вы уверены, что хотите завершить попытку?");

    if (confirmed) {
      window.onbeforeunload = null;
      form.submit();
    }
  });

  window.onbeforeunload = function (event) {
    return "Вы уверены, что хотите закрыть / обновить страницу? Весь прогресс будет потерян!";
  };
}
