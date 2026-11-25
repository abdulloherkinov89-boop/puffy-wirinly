(function () {
  var DEFAULT_CART_KEY = "puffy_cart_v1";
  var CART_KEY = DEFAULT_CART_KEY;

  function getWebApp() {
    var webApp = window.Telegram && window.Telegram.WebApp;
    webApp && webApp.ready && webApp.ready();
    return webApp || null;
  }

  function getInitData() {
    var webApp = getWebApp();
    return webApp && webApp.initData ? webApp.initData : "";
  }

  function getTelegramUserId() {
    var initData = getInitData();
    if (!initData) return "";
    try {
      var params = new URLSearchParams(initData);
      var user = JSON.parse(params.get("user") || "{}");
      return user.id ? String(user.id) : "";
    } catch (error) {
      return "";
    }
  }

  var telegramUserId = getTelegramUserId();
  if (telegramUserId) {
    CART_KEY = DEFAULT_CART_KEY + "_" + telegramUserId;
  }

  function isMiniAppLinked() {
    return Boolean(getInitData() && getTelegramUserId());
  }

  function showLinkMessage() {
    var message = "Telegram profilingiz ulanmagan. Mini appdan kirish yoki qayta urinib ko'ring.";
    var webApp = getWebApp();
    if (webApp && typeof webApp.showAlert === "function") {
      webApp.showAlert(message);
    } else {
      window.alert(message);
    }
  }

  function readCart() {
    if (!isMiniAppLinked()) return {};
    try {
      var value = JSON.parse(localStorage.getItem(CART_KEY) || "{}");
      return value && typeof value === "object" ? value : {};
    } catch (error) {
      console.error("[cart] Could not read saved cart", error);
      return {};
    }
  }

  function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    window.dispatchEvent(new CustomEvent("shopcartchange"));
  }

  function syncWithBackend(product, quantity) {
    var initData = getInitData();
    if (!initData) return;
    fetch("/api/cart/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        init_data: initData,
        product_id: Number(product.id),
        quantity: Math.floor(quantity)
      })
    }).catch(function (error) {
      console.error("[cart] Backend cart update failed", error);
    });
  }

  function setQuantity(product, quantity) {
    if (!product || product.id == null) return;
    if (!isMiniAppLinked()) {
      showLinkMessage();
      return;
    }
    cartRevision += 1;
    var cart = readCart();
    var id = String(product.id);
    var nextQuantity = Math.floor(Number(quantity) || 0);
    if (nextQuantity <= 0) {
      delete cart[id];
    } else {
      cart[id] = {
        product: {
          id: product.id,
          name: product.name,
          price: Number(product.price) || 0,
          image_url: product.image_url || "",
          about: product.about || ""
        },
        quantity: nextQuantity
      };
    }
    saveCart(cart);
    syncWithBackend(product, nextQuantity);
  }

  function getQuantity(productId) {
    var entry = readCart()[String(productId)];
    return entry ? Number(entry.quantity) || 0 : 0;
  }

  function formatPrice(value) {
    return Number(value || 0).toLocaleString("uz-UZ") + " so'm";
  }

  function renderCart() {
    var itemsNode = document.getElementById("cart-items");
    if (!itemsNode) return;
    var entries = Object.values(readCart());
    itemsNode.replaceChildren();
    var total = 0;

    if (!entries.length) {
      var empty = document.createElement("div");
      empty.className = "empty-cart";
      empty.innerHTML = '<div class="empty-cart-icon" aria-hidden="true"><span class="bag"><span class="bag-heart">♥</span></span></div><b>Savatingiz hozircha bo\'sh</b><small>Sevimli mahsulotlarni menyudan qo\'shing.</small><a href="/foydalanuvchilar/home.html">Menyuga o\'tish</a>';
      itemsNode.appendChild(empty);
    }

    entries.forEach(function (entry) {
      var product = entry.product;
      var quantity = Number(entry.quantity) || 0;
      total += Number(product.price) * quantity;
      var row = document.createElement("div");
      row.className = "row";
      var picture = document.createElement("div");
      picture.className = "t";
      if (product.image_url) {
        var image = document.createElement("img");
        image.src = product.image_url;
        image.alt = product.name;
        image.onerror = function () {
          image.replaceWith(document.createTextNode("🍔"));
        };
        picture.appendChild(image);
      } else {
        picture.textContent = "🍔";
      }
      var info = document.createElement("div");
      info.className = "i";
      var name = document.createElement("b");
      name.textContent = product.name;
      var price = document.createElement("small");
      price.textContent = formatPrice(product.price);
      info.append(name, price);

      var controls = document.createElement("div");
      controls.className = "step sm";
      var minus = document.createElement("button");
      minus.type = "button";
      minus.textContent = "−";
      minus.addEventListener("click", function () {
        setQuantity(product, quantity - 1);
      });
      var count = document.createElement("span");
      count.textContent = quantity;
      var plus = document.createElement("button");
      plus.type = "button";
      plus.textContent = "+";
      plus.addEventListener("click", function () {
        setQuantity(product, quantity + 1);
      });
      controls.append(minus, count, plus);
      row.append(picture, info, controls);
      itemsNode.appendChild(row);
    });

    var totalNode = document.getElementById("cart-total");
    if (totalNode) totalNode.textContent = formatPrice(total);
    var orderButton = document.querySelector(".order");
    if (orderButton) orderButton.hidden = entries.length === 0;
    var totalBox = totalNode && totalNode.closest(".total");
    if (totalBox) totalBox.hidden = entries.length === 0;
  }

  var cartRevision = 0;

  function loadBackendCart() {
    var initData = getInitData();
    var revisionAtStart = cartRevision;
    if (!initData) return;
    fetch("/api/cart/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: initData })
    }).then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.json();
    }).then(function (items) {
      if (cartRevision !== revisionAtStart) return;
      var cart = {};
      items.forEach(function (item) {
        cart[String(item.product_id)] = {
          product: {
            id: item.product_id,
            name: item.name,
            price: Number(item.price) || 0,
            image_url: item.image_url || "",
            about: ""
          },
          quantity: Number(item.quantity) || 0
        };
      });
      saveCart(cart);
    }).catch(function (error) {
      console.error("[cart] Backend cart could not be loaded", error);
    });
  }

  window.ShopCart = {
    getQuantity: getQuantity,
    setQuantity: setQuantity,
    render: renderCart
  };
  window.addEventListener("shopcartchange", renderCart);
  document.addEventListener("DOMContentLoaded", function () {
    renderCart();
    loadBackendCart();
  });
  renderCart();
})();