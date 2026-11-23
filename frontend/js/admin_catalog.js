(function () {
  var statusNode = document.getElementById("admin-status");
  var firstCategory = document.getElementById("first-category");
  var actionsNode = document.getElementById("admin-actions");
  var categoryList = document.getElementById("category-list");
  var productList = document.getElementById("product-list");
  var searchInput = document.getElementById("product-search");
  var modal = document.getElementById("admin-modal");
  var categoryForm = document.getElementById("category-form");
  var productForm = document.getElementById("product-form");
  var currentCategories = [];
  var currentProducts = [];
  var selectedCategory = "all";
  var telegramApp = window.Telegram && window.Telegram.WebApp;

  function showStatus(message, isError) {
    statusNode.textContent = message;
    statusNode.className = "rounded-2xl px-4 py-3 text-sm " +
      (isError ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700");
    statusNode.classList.remove("hidden");
  }

  function initData() {
    return telegramApp ? telegramApp.initData : "";
  }

  function request(url, options) {
    return fetch(url, Object.assign({ cache: "no-store" }, options || {})).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (body) {
        if (!response.ok) {
          throw new Error(body.detail || "So‘rov bajarilmadi (" + response.status + ")");
        }
        return body;
      });
    });
  }

  function renderCategories() {
    categoryList.replaceChildren();
    var allButton = document.createElement("button");
    allButton.type = "button";
    allButton.textContent = "Hammasi";
    allButton.className = "shrink-0 rounded-full px-4 py-2 text-xs font-bold " +
      (selectedCategory === "all" ? "bg-[#f7edd4] text-[#9a6715]" : "bg-zinc-100 text-zinc-600");
    allButton.addEventListener("click", function () {
      selectedCategory = "all";
      renderCategories();
      renderProducts();
    });
    categoryList.appendChild(allButton);

    currentCategories.forEach(function (category) {
      var button = document.createElement("button");
      button.type = "button";
      button.textContent = category.name;
      button.className = "shrink-0 rounded-full px-4 py-2 text-xs font-bold " +
        (selectedCategory === category.id ? "bg-[#f7edd4] text-[#9a6715]" : "bg-zinc-100 text-zinc-600");
      button.addEventListener("click", function () {
        selectedCategory = category.id;
        renderCategories();
        renderProducts();
      });
      categoryList.appendChild(button);
    });
  }

  function renderProducts() {
    var filter = searchInput.value.trim().toLocaleLowerCase();
    productList.replaceChildren();
    var visibleProducts = currentProducts.filter(function (product) {
      var matchesCategory = selectedCategory === "all" || product.category_id === selectedCategory;
      var matchesSearch = !filter || (product.name + " " + product.category_name).toLocaleLowerCase().includes(filter);
      return matchesCategory && matchesSearch;
    });

    if (!visibleProducts.length) {
      var empty = document.createElement("p");
      empty.className = "rounded-2xl bg-[#f4f4f5] p-5 text-center text-sm text-zinc-500";
      empty.textContent = currentProducts.length ? "Bu bo‘limda mos mahsulot yo‘q." : "Hozircha mahsulot qo‘shilmagan.";
      productList.appendChild(empty);
      return;
    }

    visibleProducts.forEach(function (product) {
      var card = document.createElement("article");
      card.className = "flex items-center justify-between gap-3 rounded-2xl bg-[#f4f4f5] p-4";
      var info = document.createElement("div");
      info.className = "flex min-w-0 items-center gap-3.5";
      var image = document.createElement("img");
      image.className = "h-14 w-14 shrink-0 rounded-xl bg-white object-cover";
      image.src = product.image_url;
      image.alt = product.name;
      image.onerror = function () {
        image.replaceWith(Object.assign(document.createElement("div"), {
          className: "flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-white text-xs text-zinc-400",
          textContent: "Rasm"
        }));
      };
      var details = document.createElement("div");
      details.className = "min-w-0";
      var name = document.createElement("h3");
      name.className = "truncate text-sm font-bold";
      name.textContent = product.name;
      var category = document.createElement("p");
      category.className = "mt-0.5 text-xs text-zinc-500";
      category.textContent = product.category_name;
      var price = document.createElement("p");
      price.className = "mt-1 text-sm font-extrabold text-[#e11d2a]";
      price.textContent = Number(product.price).toLocaleString("uz-UZ") + " so‘m";
      details.append(name, category, price);
      info.append(image, details);
      card.appendChild(info);
      productList.appendChild(card);
    });
  }

  function openModal(kind) {
    if (!initData()) {
      showStatus("Admin boshqaruvi faqat Telegram mini app ichida ochiladi. Botdagi tugmadan qayta kiring.", true);
      return;
    }
    categoryForm.classList.toggle("hidden", kind !== "category");
    productForm.classList.toggle("hidden", kind !== "product");
    document.getElementById("modal-title").textContent = kind === "category" ? "Yangi kategoriya" : "Yangi mahsulot";
    if (kind === "product") {
      var select = productForm.elements.category_id;
      select.replaceChildren();
      currentCategories.forEach(function (category) {
        var option = document.createElement("option");
        option.value = category.id;
        option.textContent = category.name;
        select.appendChild(option);
      });
    }
    modal.classList.remove("hidden");
    modal.classList.add("flex");
  }

  function closeModal() {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    categoryForm.reset();
    productForm.reset();
  }

  function loadAdminCatalog() {
    return Promise.all([request("/api/categories"), request("/api/products")]).then(function (data) {
      currentCategories = data[0];
      currentProducts = data[1];
      var hasCategories = currentCategories.length > 0;
      firstCategory.classList.toggle("hidden", hasCategories);
      actionsNode.classList.toggle("hidden", !hasCategories);
      searchInput.classList.toggle("hidden", !hasCategories);
      categoryList.classList.toggle("hidden", !hasCategories);
      if (!hasCategories) {
        productList.replaceChildren();
        return;
      }
      if (selectedCategory !== "all" && !currentCategories.some(function (category) { return category.id === selectedCategory; })) {
        selectedCategory = "all";
      }
      renderCategories();
      renderProducts();
    }).catch(function (error) {
      showStatus(error.message, true);
    });
  }

  function authorizeAdmin() {
    if (!initData()) {
      throw new Error("Admin panelga faqat Telegram orqali kirish mumkin. Botdagi admin tugmasini bosing.");
    }
    return request("/api/admin/auth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: initData() })
    });
  }

  document.getElementById("first-category-button").addEventListener("click", function () { openModal("category"); });
  document.getElementById("add-category-button").addEventListener("click", function () { openModal("category"); });
  document.getElementById("add-product-button").addEventListener("click", function () { openModal("product"); });
  document.getElementById("modal-close").addEventListener("click", closeModal);
  modal.addEventListener("click", function (event) { if (event.target === modal) closeModal(); });
  searchInput.addEventListener("input", renderProducts);

  categoryForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var submitButton = categoryForm.querySelector("button[type='submit'], button:not([type])");
    submitButton.disabled = true;
    request("/api/admin/categories", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: initData(), name: categoryForm.elements.name.value })
    }).then(function (category) {
      showStatus("«" + category.name + "» kategoriyasi qo‘shildi.", false);
      closeModal();
      selectedCategory = "all";
      return loadAdminCatalog();
    }).catch(function (error) {
      showStatus(error.message, true);
    }).finally(function () { submitButton.disabled = false; });
  });

  productForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var submitButton = productForm.querySelector("button[type='submit'], button:not([type])");
    var imageFile = productForm.elements.image.files[0];
    var payload = {
      init_data: initData(),
      name: productForm.elements.name.value,
      price: Number(productForm.elements.price.value),
      category_id: Number(productForm.elements.category_id.value),
      about: productForm.elements.about.value,
      image_url: productForm.elements.image_url.value.trim() || null
    };
    submitButton.disabled = true;
    var imagePromise = Promise.resolve();
    if (imageFile) {
      if (imageFile.size > 5 * 1024 * 1024) {
        showStatus("Rasm hajmi 5 MB dan oshmasligi kerak.", true);
        submitButton.disabled = false;
        return;
      }
      imagePromise = new Promise(function (resolve, reject) {
        var reader = new FileReader();
        reader.onload = function () {
          payload.image_data = String(reader.result).split(",")[1];
          payload.image_type = imageFile.type;
          resolve();
        };
        reader.onerror = function () { reject(new Error("Rasm faylini o‘qib bo‘lmadi.")); };
        reader.readAsDataURL(imageFile);
      });
    }
    imagePromise.then(function () {
      return request("/api/admin/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }).then(function (product) {
      showStatus("«" + product.name + "» mahsuloti qo‘shildi.", false);
      closeModal();
      return loadAdminCatalog();
    }).catch(function (error) {
      showStatus(error.message, true);
    }).finally(function () { submitButton.disabled = false; });
  });

  if (telegramApp) telegramApp.ready();
  authorizeAdmin().then(loadAdminCatalog).catch(function (error) {
    showStatus("Kirish rad etildi: " + error.message, true);
    firstCategory.classList.add("hidden");
    actionsNode.classList.add("hidden");
    searchInput.classList.add("hidden");
    categoryList.classList.add("hidden");
    productList.replaceChildren();
  });
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) authorizeAdmin().then(loadAdminCatalog).catch(function (error) {
      showStatus("Kirish rad etildi: " + error.message, true);
      firstCategory.classList.add("hidden");
      actionsNode.classList.add("hidden");
      productList.replaceChildren();
    });
  });
})();
