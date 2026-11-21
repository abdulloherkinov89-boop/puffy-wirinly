(function () {
  var statusNode = document.getElementById("profile-status");
  var loginButton = document.getElementById("telegram-login");

  function showMessage(message) {
    statusNode.textContent = message;
    statusNode.hidden = false;
  }

  function connectTelegram() {
    var webApp = window.Telegram && window.Telegram.WebApp;
    if (!webApp || !webApp.initData) {
      showMessage("Telegram profilingizga ulanish uchun Mini Appni Telegram ichidan oching.");
      return;
    }

    webApp.ready();
    webApp.expand();
    showMessage("Telegram profilingizga ulanmoqda...");
    loginButton.disabled = true;

    fetch("/api/auth/telegram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: webApp.initData })
    }).then(function (response) {
      return response.json().then(function (body) {
        if (!response.ok) {
          throw new Error("HTTP " + response.status + ": " + (body.detail || "Login xatosi"));
        }
        return body;
      });
    }).then(function (result) {
      var user = result.user;
      document.getElementById("profile-name").textContent = user.full_name;
      document.getElementById("profile-phone").textContent =
        user.phone_number || (user.username ? "@" + user.username : "Telefon raqami ulanmagan");
      document.getElementById("profile-avatar").textContent =
        (user.first_name || user.full_name || "T").charAt(0).toUpperCase();
      showMessage("Telegram profilingiz muvaffaqiyatli ulandi.");
      loginButton.textContent = "Telegram ulandi";
    }).catch(function (error) {
      console.error("[profile] Telegram authentication failed", error);
      showMessage("Telegramga ulanish amalga oshmadi. Qayta urinib ko'ring.");
    }).finally(function () {
      loginButton.disabled = false;
    });
  }

  loginButton.addEventListener("click", connectTelegram);
  connectTelegram();
})();