(function () {
  var CART_KEY = "puffy_cart_v1";

  function readCart() {
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

  function setQuantity(product, quantity) {
    if (!product || product.id == null) return;
    var cart = readCart();
    var id = String(product.id);
    if (quantity <= 0) {
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
        quantity: Math.floor(quantity)
      };
    }
    saveCart(cart);
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
      var empty = document.createElement("p");
      empty.className = "catalog-status";
      empty.textContent = "Savatingiz hozircha bo'sh.";
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
  }

  window.ShopCart = {
    getQuantity: getQuantity,
    setQuantity: setQuantity,
    render: renderCart
  };
  window.addEventListener("shopcartchange", renderCart);
  document.addEventListener("DOMContentLoaded", renderCart);
  renderCart();
})();