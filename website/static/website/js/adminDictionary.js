"use strict";

const editableCells = document.querySelectorAll('[contenteditable="true"]');

export function clearFormatting() {
  editableCells.forEach((td) => {
    td.addEventListener("paste", (e) => {
      // Prevent the default paste behavior
      e.preventDefault();
      // Get the plain text value from the clipboard
      const text = e.clipboardData.getData("text/plain");

      // Insert the plain text value into the <td> element without any formatting
      navigator.clipboard.writeText(text);
      td.textContent = text; // Update the content of the <td> element
    });
  });
}

export function editContents() {
  editableCells.forEach((cell) => {
    cell.addEventListener("focus", () => {
      const initialValue = cell.innerHTML;
      cell.addEventListener("blur", (event) => {
        const currentValue = cell.textContent.replace(/<a[^>]*>([^<]+)<\/a>/g, "");
        const id = event.target.getAttribute("id");
        const name = event.target.getAttribute("name");

        if (initialValue !== currentValue) {
          // Send a POST request to the server to save the changes
          fetch("/dictionary_edit", {
            method: "POST",
            body: JSON.stringify({
              id: id,
              name: name,
              value: currentValue,
            }),
          })
            .then((response) => response.json())
            .then((response) => console.log(response))
            .catch((error) => console.error(error));
        }
      });
    });
  });
}

export function selectAll() {
  const selectAllCheckbox = document.querySelector("[data-select-all]");
  if (!selectAllCheckbox) return;

  const wordCheckboxes = document.querySelectorAll('input[name="words[]"]');

  selectAllCheckbox.addEventListener("change", () => {
    wordCheckboxes.forEach((checkbox) => {
      checkbox.checked = selectAllCheckbox.checked;
    });
  });
}
