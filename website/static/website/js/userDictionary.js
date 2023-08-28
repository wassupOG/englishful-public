"use strict";

export function trainCards() {
  // Get all buttons and couter elements
  const startTrainingBtn = document.querySelector("#start-training");
  if (!startTrainingBtn) return;

  const stopTrainingBtn = document.querySelector("#stop-training");
  const dictMain = document.querySelector("#dict-main");
  const trainingCards = document.querySelector("#training-cards");
  const correctCounter = document.querySelector("#correct-counter");
  const wrongCounter = document.querySelector("#wrong-counter");

  // Get all cards and buttons
  const cards = Array.from(document.querySelectorAll(".card"));
  cards.sort(() => Math.random() - 0.5);

  const totalCardCount = cards.length;
  let currentCardIndex = 0;
  let correctCount = 0;
  let wrongCount = 0;

  // Add click event listener to start training button
  startTrainingBtn.addEventListener("click", () => {
    dictMain.classList.add("hidden");
    trainingCards.classList.remove("hidden");
    cards[0].classList.remove("hidden");
    updateCardCounter();
    checkWord();
  });

  stopTrainingBtn.addEventListener("click", () => location.reload());

  // Function to update the card counter
  function updateCardCounter() {
    const cardCounter = document.querySelector("#card-counter");
    cardCounter.innerHTML = `${currentCardIndex + 1} из ${totalCardCount}`;
  }

  function checkWord() {
    const currentCardId = cards[currentCardIndex].dataset.cardId;
    const currentCardElement = cards[currentCardIndex];
    const nextCardElement = cards[currentCardIndex + 1];
    const currentCheck = document.querySelector(`[data-check-id="${currentCardId}"]`);
    currentCheck.addEventListener("click", () => currentCardElement.classList.toggle("flipped"));

    const nextButton = document.querySelector(`[data-next-id="${currentCardId}"]`);
    const plusProgress = document.querySelector(`[data-plus-id="${currentCardId}"]`);
    const minusProgress = document.querySelector(`[data-minus-id="${currentCardId}"]`);
    const progressBar = document.querySelector(`[data-progress-bar="${currentCardId}"]`);
    const progressMessage = progressBar.nextElementSibling;
    const progressButtons = [plusProgress, minusProgress];

    progressButtons.forEach((button) => {
      button.addEventListener("click", () => {
        plusProgress.classList.add("hidden");
        minusProgress.classList.add("hidden");
        nextButton.classList.toggle("hidden");

        const data = {
          word_id: currentCardId,
          type: button.dataset.progressType,
        };
        fetch("/update_progress", {
          method: "POST",
          body: JSON.stringify(data),
        })
          .then((response) => response.json())
          .then((result) => {
            if (button.dataset.progressType === "+") {
              progressBar.value += 5;
              progressBar.style.accentColor = "lightgreen";
              progressMessage.innerHTML = `Current progress: <b class="good_grade">${progressBar.value}%</b>`;
              correctCounter.textContent = correctCount += 1;
            } else if (button.dataset.progressType === "-") {
              progressBar.value -= 5;
              progressBar.style.accentColor = "lightcoral";
              progressMessage.innerHTML = `Current progress: <b class="bad_grade">${progressBar.value}%</b>`;
              wrongCounter.textContent = wrongCount += 1;
            }
          })
          .catch((error) => console.error(error));
      });
    });

    if (currentCardIndex + 1 === totalCardCount) {
      nextButton.textContent = "Finish";
      nextButton.addEventListener("click", () => {
        location.reload();
      });
    }

    if (currentCardIndex + 1 < totalCardCount) {
      nextButton.addEventListener("click", () => {
        currentCardElement.classList.add("hidden");
        nextCardElement.classList.toggle("hidden");
        currentCardIndex++;
        updateCardCounter();
        checkWord();
      });
    }
  }
}

export function sayUtterance() {
  const speechIcons = document.querySelectorAll("[data-say-word]");
  speechIcons.forEach((icon) => {
    const context = icon.previousElementSibling.textContent.replace(/['"\\]/g, "");
    icon.addEventListener("click", () => {
      setupSpeechSynthesis(context);
    });
  });
}

export function setupSpeechSynthesis(text) {
  const synth = window.speechSynthesis;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.pitch = 1;

  let rateValue;
  if (!document.querySelector("#dict-main").classList.contains("hidden")) {
    rateValue = document.querySelector("#dict-rate").value;
  } else if (!document.querySelector("#training-cards").classList.contains("hidden")) {
    rateValue = document.querySelector("#cards-rate").value;
  } else {
    rateValue = 0.9; // default value
  }
  utterance.rate = rateValue;

  utterance.volume = 1;
  utterance.lang = "en-US";

  function getVoiceByName(voices, name) {
    return voices.find((voice) => {
      return voice.name === name;
    });
  }

  function getVoiceByVoiceURI(voices, voiceURI) {
    return voices.find((voice) => {
      return voice.voiceURI === voiceURI;
    });
  }

  function waitUntilVoicesLoaded() {
    return new Promise((resolve, reject) => {
      let voices = synth.getVoices();
      if (voices.length > 0) {
        resolve(voices);
      } else {
        synth.onvoiceschanged = () => {
          voices = synth.getVoices();
          if (voices.length > 0) {
            resolve(voices);
          } else {
            reject("No voices available");
          }
        };
      }
    });
  }

  waitUntilVoicesLoaded()
    .then((voices) => {
      let selectedVoice;
      const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
      if (isSafari) {
        selectedVoice = getVoiceByVoiceURI(voices, "com.apple.voice.compact.en-US.Samantha");
      } else {
        selectedVoice = getVoiceByVoiceURI(voices, "Google US English");
        if (!selectedVoice) {
          selectedVoice = getVoiceByName(voices, "Google US English");
        }
      }
      utterance.voice = selectedVoice;
      synth.speak(utterance);
    })
    .catch((error) => {
      console.error(error);
    });
}
