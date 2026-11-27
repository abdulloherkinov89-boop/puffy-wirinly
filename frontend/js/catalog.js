(function () {
  var categoriesNode = document.getElementById("cats");
  var catalogNode = document.getElementById("catalog");
  var statusNode = document.getElementById("catalog-status");
  var quantity = 1;
  var basePrice = 0;
  var selectedProduct = null;

  function formatPrice(value) {
    return Number(value || 0).toLocaleString("uz-UZ") + " so'm";
  }

  function closeSheet() {
    document.getElementById("ov").classList.remove("on");
    document.getElementById("sheet").classList.remove("on");
    document.body.style.overflow = "";
  }

  function updateQuantity() {
    document.getElementById("mq").textContent = quantity;
    document.getElementById("go").textContent = "Savatga +";
  }

  function appendProductImage(container, product) {
    if (!product.image_url) {
      container.textContent = "🍔";
      return;
    }

    var image = document.createElement("img");
    image.src = product.image_url;
    image.alt = product.name;
    image.onerror = function () {
      console.error("[catalog] Product image failed to load", {
        url: image.src,
        productId: product.id,
        productName: product.name
      });
      image.replaceWith(document.createTextNode("🍔"));
    };
    container.appendChild(image);
  }

  function openProduct(product) {
    selectedProduct = product;
    quantity = 1;
    basePrice = Number(product.price);
    var picture = document.getElementById("m-pic");
    picture.replaceChildren();
    appendProductImage(picture, product);
    document.getElementById("m-n").textContent = product.name;
    document.getElementById("m-d").textContent = product.about;
    document.getElementById("m-p").textContent = formatPrice(basePrice);
    document.getElementById("m-o").textContent = "";
    updateQuantity();
    document.getElementById("ov").classList.add("on");
    document.getElementById("sheet").classList.add("on");
    document.body.style.overflow = "hidden";
  }

  function makeProductCard(product) {
    var card = document.createElement("div");
    card.className = "card";
    card.tabIndex = 0;
    var cardQuantity = window.ShopCart.getQuantity(product.id);

    var picture = document.createElement("div");
    picture.className = "pic";
    appendProductImage(picture, product);
    var addControl = document.createElement("div");
    addControl.className = "plus";

    function renderAddControl() {
      addControl.replaceChildren();
      if (cardQuantity === 0) {
        var addButton = document.createElement("button");
        addButton.type = "button";
        addButton.className = "quick-add";
        addButton.textContent = "+";
        addButton.setAttribute("aria-label", product.name + " savatga qo'shish");
        addButton.addEventListener("click", function (event) {
          event.stopPropagation();
          if (window.ShopCart.setQuantity(product, 1)) {
            cardQuantity = 1;
            renderAddControl();
          }
        });
        addControl.appendChild(addButton);
        return;
      }

      var minusButton = document.createElement("button");
      minusButton.type = "button";
      minusButton.textContent = "−";
      minusButton.setAttribute("aria-label", product.name + " sonini kamaytirish");
      minusButton.addEventListener("click", function (event) {
        event.stopPropagation();
        if (window.ShopCart.setQuantity(product, cardQuantity - 1)) {
          cardQuantity -= 1;
          renderAddControl();
        }
      });
      var count = document.createElement("span");
      count.textContent = cardQuantity;
      var plusButton = document.createElement("button");
      plusButton.type = "button";
      plusButton.textContent = "+";
      plusButton.setAttribute("aria-label", product.name + " sonini oshirish");
      plusButton.addEventListener("click", function (event) {
        event.stopPropagation();
        if (window.ShopCart.setQuantity(product, cardQuantity + 1)) {
          cardQuantity += 1;
          renderAddControl();
        }
      });
      addControl.append(minusButton, count, plusButton);
    }
    renderAddControl();
    window.addEventListener("shopcartchange", function () {
      cardQuantity = window.ShopCart.getQuantity(product.id);
      renderAddControl();
    });
    picture.appendChild(addControl);

    var price = document.createElement("div");
    price.className = "price";
    price.textContent = formatPrice(product.price);
    var name = document.createElement("div");
    name.className = "name";
    name.textContent = product.name;
    var about = document.createElement("div");
    about.className = "desc";
    about.textContent = product.about;

    card.append(picture, price, name, about);
    card.addEventListener("click", function () { openProduct(product); });
    card.addEventListener("keydown", function (event) {
      if (event.target !== card) return;
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openProduct(product);
      }
    });
    return card;
  }

  function renderCatalog(categories, products) {
    categoriesNode.replaceChildren();
    catalogNode.replaceChildren();
    if (!categories.length) {
      statusNode.textContent = "Hozircha kategoriya va mahsulotlar qo'shilmagan.";
      catalogNode.appendChild(statusNode);
      return;
    }

    var productsByCategory = new Map();
    products.forEach(function (product) {
      var group = productsByCategory.get(product.category_id) || [];
      group.push(product);
      productsByCategory.set(product.category_id, group);
    });

    categories.forEach(function (category, index) {
      var sectionId = "category-" + category.id;
      var link = document.createElement("a");
      link.className = "cat" + (index === 0 ? " on" : "");
      link.href = "#" + sectionId;
      link.textContent = category.name;
      link.addEventListener("click", function (event) {
        event.preventDefault();
        var section = document.getElementById(sectionId);
        window.scrollTo({
          top: section.getBoundingClientRect().top + window.scrollY - 112,
          behavior: "smooth"
        });
        categoriesNode.querySelectorAll(".cat").forEach(function (item) {
          item.classList.toggle("on", item === link);
        });
      });
      categoriesNode.appendChild(link);

      var heading = document.createElement("h2");
      heading.id = sectionId;
      heading.textContent = category.name;
      catalogNode.appendChild(heading);
      var grid = document.createElement("div");
      grid.className = "grid";
      var categoryProducts = productsByCategory.get(category.id) || [];
      if (!categoryProducts.length) {
        var empty = document.createElement("p");
        empty.className = "catalog-status";
        empty.textContent = "Bu kategoriyada mahsulot hozircha yo'q.";
        grid.appendChild(empty);
      } else {
        categoryProducts.forEach(function (product) {
          grid.appendChild(makeProductCard(product));
        });
      }
      catalogNode.appendChild(grid);
    });
  }

  document.getElementById("ov").addEventListener("click", closeSheet);
  document.getElementById("x").addEventListener("click", closeSheet);
  document.getElementById("pl").addEventListener("click", function () {
    quantity += 1;
    updateQuantity();
  });
  document.getElementById("mi").addEventListener("click", function () {
    if (quantity > 1) {
      quantity -= 1;
      updateQuantity();
    }
  });
  document.getElementById("go").addEventListener("click", function () {
    var success = window.ShopCart.setQuantity(
      selectedProduct,
      window.ShopCart.getQuantity(selectedProduct.id) + quantity
    );
    if (success) closeSheet();
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeSheet();
  });

  function fetchJson(url) {
    return fetch(url, { cache: "no-store" }).then(function (response) {
      if (!response.ok) {
        return response.text().then(function (body) {
          var details = body ? ": " + body.slice(0, 300) : "";
          var error = new Error(
            "HTTP " + response.status + " " + response.statusText + details
          );
          error.status = response.status;
          throw error;
        });
      }
      return response.json().catch(function (error) {
        throw new Error("Invalid JSON response: " + error.message);
      });
    }).catch(function (error) {
      console.error("[catalog] API request failed", {
        url: url,
        status: error.status || null,
        message: error.message
      });
      throw error;
    });
  }

  function validateCatalog(categories, products) {
    if (!Array.isArray(categories)) {
      throw new Error("/api/categories must return a JSON array");
    }
    if (!Array.isArray(products)) {
      throw new Error("/api/products must return a JSON array");
    }

    categories.forEach(function (category, index) {
      if (!category || category.id == null || typeof category.name !== "string") {
        throw new Error("Invalid category at index " + index + ": expected id and name");
      }
    });

    var productFields = [
      "id", "name", "price", "image_url", "category_id", "about", "category_name"
    ];
    products.forEach(function (product, index) {
      var missingField = productFields.find(function (field) {
        return !product || !Object.prototype.hasOwnProperty.call(product, field);
      });
      if (missingField) {
        throw new Error(
          "Invalid product at index " + index + ": missing " + missingField
        );
      }
    });
  }

  function loadCatalog() {
    Promise.all([
      fetchJson("/api/categories"),
      fetchJson("/api/products")
    ]).then(function (data) {
      validateCatalog(data[0], data[1]);
      renderCatalog(data[0], data[1]);
    }).catch(function (error) {
      console.error("[catalog] Menu could not be loaded", error);
      statusNode.textContent = "Menyuni yuklab bo'lmadi. Sahifani yangilab ko'ring.";
      catalogNode.replaceChildren(statusNode);
    });
  }

  loadCatalog();
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) loadCatalog();
  });
  window.addEventListener("pageshow", function (event) {
    if (event.persisted) loadCatalog();
  });
})();