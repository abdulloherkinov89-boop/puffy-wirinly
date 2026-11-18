(function () {
  var categoriesNode = document.getElementById("cats");
  var catalogNode = document.getElementById("catalog");
  var statusNode = document.getElementById("catalog-status");
  var quantity = 1;
  var basePrice = 0;

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
    document.getElementById("go").textContent =
      "Savatga + · " + formatPrice(basePrice * quantity);
  }

  function openProduct(product) {
    quantity = 1;
    basePrice = Number(product.price);
    var picture = document.getElementById("m-pic");
    picture.replaceChildren();
    if (product.image_url) {
      var image = document.createElement("img");
      image.src = product.image_url;
      image.alt = product.name;
      picture.appendChild(image);
    } else {
      picture.textContent = "🍔";
    }
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

    var picture = document.createElement("div");
    picture.className = "pic";
    if (product.image_url) {
      var image = document.createElement("img");
      image.src = product.image_url;
      image.alt = product.name;
      picture.appendChild(image);
    } else {
      picture.textContent = "🍔";
    }
    var plus = document.createElement("span");
    plus.className = "plus";
    plus.textContent = "+";
    picture.appendChild(plus);

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
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeSheet();
  });

  function loadCatalog() {
    Promise.all([
      fetch("/api/categories", { cache: "no-store" }).then(function (response) {
        if (!response.ok) throw new Error("Kategoriyalar olinmadi");
        return response.json();
      }),
      fetch("/api/products", { cache: "no-store" }).then(function (response) {
        if (!response.ok) throw new Error("Mahsulotlar olinmadi");
        return response.json();
      })
    ]).then(renderCatalog).catch(function () {
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