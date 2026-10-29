document.querySelectorAll(".copy-button").forEach(function (button) {
  button.addEventListener("click", function () {
    var status = document.getElementById("copy-status");
    if (!navigator.clipboard || !navigator.clipboard.writeText) {
      status.textContent = "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요.";
      return;
    }
    navigator.clipboard.writeText(button.dataset.copy).then(
      function () { status.textContent = "복사했습니다."; },
      function () { status.textContent = "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."; }
    );
  });
});
