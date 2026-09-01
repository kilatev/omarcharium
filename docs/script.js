"use strict";

const copyButton = document.getElementById("copy-command");
copyButton.addEventListener("click", async () => {
  const command = document.getElementById("install-command").textContent;
  await navigator.clipboard.writeText(command);
  copyButton.textContent = "COPIED";
  window.setTimeout(() => { copyButton.textContent = "COPY"; }, 1600);
});
