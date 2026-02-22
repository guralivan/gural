const ordersList = document.getElementById("ordersList");
const refreshBtn = document.getElementById("refreshBtn");
const productsList = document.getElementById("productsList");
const ordersSection = document.getElementById("ordersSection");
const customersSection = document.getElementById("customersSection");
const productsSection = document.getElementById("productsSection");
const bonusSection = document.getElementById("bonusSection");
const designSection = document.getElementById("designSection");
const customersList = document.getElementById("customersList");
const customersSearch = document.getElementById("customersSearch");
const tabs = document.querySelectorAll(".admin-tabs .chip");
let activeTab = "orders";
let customersCache = [];
const filterCategoriesInput = document.getElementById("filterCategoriesInput");
const filterColorsInput = document.getElementById("filterColorsInput");
const filterFeaturesInput = document.getElementById("filterFeaturesInput");
const saveFiltersBtn = document.getElementById("saveFiltersBtn");
const productsCsvInput = document.getElementById("productsCsvInput");
const createProductBtn = document.getElementById("createProductBtn");
const importCsvBtn = document.getElementById("importCsvBtn");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const setTodayBtn = document.getElementById("setTodayBtn");
const setTomorrowBtn = document.getElementById("setTomorrowBtn");
const themeColorInput = document.getElementById("themeColorInput");
const themeColorPicker = document.getElementById("themeColorPicker");
const themePalette = document.getElementById("themePalette");
const saveThemeBtn = document.getElementById("saveThemeBtn");
const heroTitleInput = document.getElementById("heroTitleInput");
const heroSubtitleInput = document.getElementById("heroSubtitleInput");
const saveHeroBtn = document.getElementById("saveHeroBtn");
const offerLinkTitleInput = document.getElementById("offerLinkTitleInput");
const offerPageTextInput = document.getElementById("offerPageTextInput");
const offerLinkInput = document.getElementById("offerLinkInput");
const offerEnabledInput = document.getElementById("offerEnabledInput");
const saveOfferBtn = document.getElementById("saveOfferBtn");
const bonusBalanceInput = document.getElementById("bonusBalanceInput");
const bonusEarnRateInput = document.getElementById("bonusEarnRateInput");
const bonusValueInput = document.getElementById("bonusValueInput");
const serviceFeeRateInput = document.getElementById("serviceFeeRateInput");
const saveBonusBtn = document.getElementById("saveBonusBtn");
const promoCodesInput = document.getElementById("promoCodesInput");
const savePromoBtn = document.getElementById("savePromoBtn");
const placeholderImage =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><rect width='100%25' height='100%25' fill='%23f0f0f0'/><text x='50%25' y='50%25' fill='%23999' font-size='18' font-family='Arial' text-anchor='middle' dominant-baseline='middle'>Фото</text></svg>";

function formatRub(value) {
  return `${Math.round(value)} ₽`;
}

function formatPromoCodes(list) {
  if (!Array.isArray(list)) return "";
  return list
    .map((item) => `${item.code},${item.type},${item.value}`)
    .join("\n");
}

function parsePromoCodes(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [code, type, value] = line.split(",").map((v) => v.trim());
      return {
        code: (code || "").toUpperCase(),
        type: type === "percent" ? "percent" : "fixed",
        value: Number(value || 0),
      };
    })
    .filter((item) => item.code && item.value > 0);
}

function renderOrders(orders) {
  ordersList.innerHTML = "";
  if (!orders.length) {
    ordersList.innerHTML = "<div>Пока нет заказов</div>";
    return;
  }
  const sortedOrders = [...orders].sort((a, b) => (b.id || 0) - (a.id || 0));
  sortedOrders.forEach((order) => {
    const card = document.createElement("div");
    card.className = "admin-card";
    const itemsHtml = (order.items || [])
      .map((item) => {
        const product = (window.productsCache || []).find((p) => p.id === item.id);
        const image = item.image || product?.image || placeholderImage;
        return `
          <div class="admin-item">
            <img src="${image}" alt="${item.name}" />
            <span>${item.name} × ${item.qty}</span>
          </div>
        `;
      })
      .join("");
    card.innerHTML = `
      <div class="admin-row">
        <div class="admin-title">Заказ №${order.id}</div>
        <div class="admin-status">
          <select class="status-select" data-order-id="${order.id}">
            <option value="не обработан" ${order.status === "не обработан" ? "selected" : ""}>не обработан</option>
            <option value="собран" ${order.status === "собран" ? "selected" : ""}>собран</option>
            <option value="отправлен" ${order.status === "отправлен" ? "selected" : ""}>отправлен</option>
            <option value="оплачен" ${order.status === "оплачен" ? "selected" : ""}>оплачен</option>
            <option value="выполнен" ${order.status === "выполнен" ? "selected" : ""}>выполнен</option>
            <option value="отменен" ${order.status === "отменен" ? "selected" : ""}>отменен</option>
          </select>
        </div>
      </div>
      <div class="admin-meta">
        <div>${order.created_at}</div>
        <div>${order.phone}</div>
      </div>
      <div class="admin-items">${itemsHtml}</div>
      <div class="admin-total">
        <span>Итого</span>
        <span>${formatRub(order.total)}</span>
      </div>
      <div class="admin-details">
        <label>Имя <input type="text" data-field="name" value="${order.name || ""}" /></label>
        <label>Email <input type="text" data-field="email" value="${order.email || ""}" /></label>
        <label>Адрес <input type="text" data-field="address" value="${order.address || ""}" /></label>
        <label>Время <input type="text" data-field="delivery_time" value="${order.delivery_time || ""}" /></label>
        <label>Получатель <input type="text" data-field="recipient_name" value="${order.recipient_name || ""}" /></label>
        <label>Тел. получателя <input type="text" data-field="recipient_phone" value="${order.recipient_phone || ""}" /></label>
        <label>Доставка <input type="text" data-field="delivery_id" value="${order.delivery_id || ""}" /></label>
        <label>Доставка, ₽ <input type="number" data-field="delivery_fee" value="${order.delivery_fee || 0}" /></label>
        <label>Промокод <input type="text" data-field="promo_code" value="${order.promo_code || ""}" /></label>
      </div>
      <div class="product-actions">
        <button class="save-btn" data-action="save-order" data-id="${order.id}">Сохранить</button>
        <button class="secondary" data-action="delete-order" data-id="${order.id}">Удалить</button>
      </div>
    `;
    ordersList.appendChild(card);
    applyStatusClass(card.querySelector(".status-select"));
  });
}

function renderCustomers(customers) {
  customersList.innerHTML = "";
  if (!customers.length) {
    customersList.innerHTML = "<div>Пока нет заказчиков</div>";
    return;
  }
  customers.forEach((customer) => {
    const card = document.createElement("div");
    card.className = "admin-card";
    const addresses = (customer.addresses || []).join(", ");
    const orders = customer.order_details || [];
    const ordersHtml = orders.length
      ? orders
          .map((order) => {
            const items = (order.items || [])
              .map((item) => `${item.name} × ${item.qty}`)
              .join(", ");
            return `
              <div class="customer-order">
                <div><strong>Заказ №${order.id}</strong> ${order.created_at || ""}</div>
                <div>Товары: ${items || "—"}</div>
                <div>Адрес: ${order.address || "—"}</div>
                <div>Время доставки: ${order.delivery_time || "—"}</div>
                <div>Получатель: ${order.recipient_name || "—"}</div>
                <div>Тел. получателя: ${order.recipient_phone || "—"}</div>
                <div>Статус: ${order.status || "—"}</div>
                <div>Сумма: ${formatRub(order.total || 0)}</div>
                <div>Бонусы списаны: ${formatRub(order.bonus || 0)}</div>
                <div>Промокод: ${order.promo_code || "—"}</div>
              </div>
            `;
          })
          .join("")
      : "<div>Заказов нет</div>";
    card.innerHTML = `
      <div class="admin-row">
        <div class="admin-title">Клиент ${customer.user_id || ""}</div>
        <div class="admin-status">${customer.username ? `@${customer.username}` : "—"}</div>
      </div>
      <div class="admin-meta">
        <div>${customer.name || "Без имени"}</div>
        <div>${customer.phone || "—"}</div>
      </div>
      <div class="admin-details">
        <label>Почта <input type="text" value="${customer.email || ""}" disabled /></label>
        <label>Адреса <input type="text" value="${addresses}" disabled /></label>
        <label>Бонусы <input type="text" value="${customer.bonus_balance ?? 0}" disabled /></label>
        <label>Заказов всего <input type="text" value="${orders.length}" disabled /></label>
      </div>
      <div class="admin-items">${ordersHtml}</div>
      <div class="product-actions">
        <button class="secondary" data-action="delete-customer" data-id="${customer.user_id}">Удалить заказчика</button>
      </div>
    `;
    customersList.appendChild(card);
  });
}

async function loadCustomers() {
  try {
    const response = await fetch("/api/customers?include=orders");
    const data = await response.json();
    customersCache = Array.isArray(data) ? data : [];
    renderCustomers(customersCache);
  } catch (error) {
    customersList.innerHTML = "<div>Ошибка загрузки заказчиков</div>";
  }
}

function applyStatusClass(selectEl) {
  if (!selectEl) return;
  selectEl.classList.remove(
    "status-new",
    "status-packed",
    "status-sent",
    "status-paid",
    "status-done",
    "status-canceled"
  );
  if (selectEl.value === "не обработан") {
    selectEl.classList.add("status-new");
  } else if (selectEl.value === "собран") {
    selectEl.classList.add("status-packed");
  } else if (selectEl.value === "отправлен") {
    selectEl.classList.add("status-sent");
  } else if (selectEl.value === "оплачен") {
    selectEl.classList.add("status-paid");
  } else if (selectEl.value === "выполнен") {
    selectEl.classList.add("status-done");
  } else if (selectEl.value === "отменен") {
    selectEl.classList.add("status-canceled");
  }
}

async function loadOrders() {
  refreshBtn.disabled = true;
  refreshBtn.textContent = "Загрузка...";
  try {
    const response = await fetch("/api/orders");
    const data = await response.json();
    renderOrders(data);
  } catch (error) {
    ordersList.innerHTML = "<div>Ошибка загрузки заказов</div>";
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = "Обновить";
  }
}

refreshBtn.addEventListener("click", () => {
  if (activeTab === "customers") {
    loadCustomers();
  } else {
    loadOrders();
  }
});

loadOrders();

function renderProducts(products) {
  productsList.innerHTML = "";
  if (!products.length) {
    productsList.innerHTML = "<div>Нет товаров</div>";
    return;
  }
  products.forEach((product) => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `
      <img src="${product.image || placeholderImage}" alt="${product.name}" />
      <div class="product-info">
        <div class="product-title">${product.name}</div>
        <input type="text" value="${product.name || ""}" placeholder="Название" data-field="name" />
        <input type="number" value="${product.price || 0}" placeholder="Цена" data-field="price" />
        <textarea rows="2" placeholder="Описание" data-field="description">${product.description || ""}</textarea>
        <input type="number" value="${product.min_qty || 1}" placeholder="Мин. количество" data-field="min_qty" min="1" />
        <input type="text" value="${(product.tags || []).join(", ")}" placeholder="Теги (через запятую)" data-field="tags" />
        <select data-field="delivery_label">
          <option value="">Доставим завтра</option>
          <option value="Доставим сегодня" ${product.delivery_label === "Доставим сегодня" ? "selected" : ""}>
            Доставим сегодня
          </option>
        </select>
        <div class="product-actions">
          <button class="save-btn" data-action="data" data-id="${product.id}">
            Сохранить данные
          </button>
          <button class="secondary product-delete" data-action="delete" data-id="${product.id}">
            Удалить товар
          </button>
        </div>
        <input type="text" value="${product.image || ""}" placeholder="Ссылка на картинку" data-field="image" />
        <div class="product-actions">
          <button class="save-btn" data-action="link" data-id="${product.id}">
            Сохранить ссылку
          </button>
        </div>
        <input type="file" accept="image/*" class="file-input" />
        <div class="product-actions">
          <button class="save-btn upload-btn" data-action="upload" data-id="${product.id}">
            Загрузить файл
          </button>
        </div>
      </div>
    `;
    productsList.appendChild(card);
  });
}

async function loadProducts() {
  try {
    const response = await fetch("/api/products");
    const data = await response.json();
    window.productsCache = data;
    renderProducts(data);
  } catch (error) {
    productsList.innerHTML = "<div>Ошибка загрузки товаров</div>";
  }
}

async function saveAllProducts() {
  const payload = [];
  document.querySelectorAll(".product-card").forEach((card) => {
    const info = card.querySelector(".product-info");
    const id = info.querySelector("[data-field='name']").closest(".product-info")
      .parentElement.querySelector(".save-btn")?.dataset.id;
    const data = { id };
    info.querySelectorAll("[data-field]").forEach((field) => {
      const key = field.dataset.field;
      if (key === "price" || key === "min_qty") {
        data[key] = Number(field.value || 0);
      } else if (key === "tags") {
        data[key] = field.value
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean);
      } else {
        data[key] = field.value.trim();
      }
    });
    payload.push(data);
  });
  const response = await fetch("/api/products/bulk", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ products: payload }),
  });
  return response.ok;
}

productsList.addEventListener("click", async (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  const productId = target.dataset.id;
  const action = target.dataset.action;
  if (!action || !productId) return;
  const info = target.closest(".product-info");
  target.disabled = true;
  target.textContent = "Сохраняем...";
  try {
    if (action === "delete") {
      const ok = confirm("Удалить товар?");
      if (!ok) {
        target.disabled = false;
        return;
      }
      const response = await fetch(`/api/products/${productId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error("Ошибка удаления");
      }
      await loadProducts();
    } else if (action === "link") {
      const input = info.querySelector("input[data-field='image']");
      const image = input.value.trim();
      const response = await fetch(`/api/products/${productId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image }),
      });
      if (!response.ok) {
        throw new Error("Ошибка сохранения");
      }
    } else if (action === "data") {
      const payload = {};
      info.querySelectorAll("[data-field]").forEach((field) => {
        const key = field.dataset.field;
        if (key === "price" || key === "min_qty") {
          payload[key] = Number(field.value || 0);
        } else if (key === "tags") {
          payload[key] = field.value
            .split(",")
            .map((v) => v.trim())
            .filter(Boolean);
        } else if (key === "delivery_label") {
          payload[key] = field.value.trim();
        } else {
          payload[key] = field.value.trim();
        }
      });
      const response = await fetch(`/api/products/${productId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error("Ошибка сохранения");
      }
    } else {
      const fileInput = info.querySelector("input[type='file']");
      const file = fileInput.files[0];
      if (!file) {
        throw new Error("Выберите файл");
      }
      const formData = new FormData();
      formData.append("image", file);
      const response = await fetch(`/api/products/${productId}/image`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error("Ошибка загрузки");
      }
    }
    await loadProducts();
  } catch (error) {
    target.textContent = "Ошибка";
    setTimeout(() => {
    if (action === "upload") {
        target.textContent = "Загрузить файл";
    } else if (action === "delete") {
      target.textContent = "Удалить товар";
      } else if (action === "data") {
        target.textContent = "Сохранить данные";
      } else {
        target.textContent = "Сохранить ссылку";
      }
    }, 1500);
  } finally {
    target.disabled = false;
  }
});

loadProducts();

ordersList.addEventListener("change", async (event) => {
  const target = event.target;
  if (!target.classList.contains("status-select")) return;
  const orderId = target.dataset.orderId;
  const status = target.value;
  try {
    const response = await fetch(`/api/orders/${orderId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!response.ok) {
      throw new Error("Ошибка сохранения");
    }
    applyStatusClass(target);
  } catch (error) {
    target.value = "не обработан";
    applyStatusClass(target);
  }
});

ordersList.addEventListener("click", async (event) => {
  const target = event.target;
  const action = target.dataset.action;
  const orderId = target.dataset.id;
  if (!action || !orderId) return;
  if (action === "delete-order") {
    const ok = confirm("Удалить заказ?");
    if (!ok) return;
    const response = await fetch(`/api/orders/${orderId}`, {
      method: "DELETE",
    });
    if (response.ok) {
      loadOrders();
    }
    return;
  }
  if (action === "save-order") {
    const card = target.closest(".admin-card");
    const payload = {};
    card.querySelectorAll("[data-field]").forEach((field) => {
      const key = field.dataset.field;
      if (field.type === "number") {
        payload[key] = Number(field.value || 0);
      } else {
        payload[key] = field.value;
      }
    });
    const response = await fetch(`/api/orders/${orderId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (response.ok) {
      loadOrders();
    }
  }
});

function switchTab(tab) {
  activeTab = tab;
  tabs.forEach((btn) => btn.classList.remove("active"));
  tabs.forEach((btn) => {
    if (btn.dataset.tab === tab) btn.classList.add("active");
  });
  ordersSection.classList.toggle("hidden", tab !== "orders");
  customersSection.classList.toggle("hidden", tab !== "customers");
  productsSection.classList.toggle("hidden", tab !== "products");
  bonusSection.classList.toggle("hidden", tab !== "bonus");
  designSection.classList.toggle("hidden", tab !== "design");
  if (tab === "customers") {
    loadCustomers();
  }
}

tabs.forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

async function loadSettings() {
  try {
    const response = await fetch("/api/settings");
    const data = await response.json();
    bonusBalanceInput.value = data.bonus_balance ?? 500;
    bonusEarnRateInput.value = data.bonus_earn_rate ?? 0.01;
    bonusValueInput.value = data.bonus_value ?? 300;
    serviceFeeRateInput.value = data.service_fee_rate ?? 0.1;
    themeColorInput.value = data.theme_color ?? "#94a36a";
    themeColorPicker.value = data.theme_color ?? "#94a36a";
    document.documentElement.style.setProperty(
      "--accent",
      data.theme_color ?? "#94a36a"
    );
    document.body.style.setProperty(
      "--accent",
      data.theme_color ?? "#94a36a"
    );
    heroTitleInput.value = data.hero_title ?? "Цветы по себестоимости";
    heroSubtitleInput.value = data.hero_subtitle ?? "Доставка по Москве";
    if (data.filters) {
      filterCategoriesInput.value = (data.filters.categories || []).join(", ");
      filterColorsInput.value = (data.filters.colors || []).join(", ");
      filterFeaturesInput.value = (data.filters.features || []).join(", ");
    }
    promoCodesInput.value = formatPromoCodes(data.promo_codes || []);
    offerLinkTitleInput.value =
      data.offer_link_title ??
      data.offer_text ??
      "Я принимаю условия Публичной оферты, а также даю согласие на обработку персональных данных.";
    offerPageTextInput.value =
      data.offer_page_text ?? data.offer_text ?? "Публичная оферта";
    offerLinkInput.value = data.offer_link ?? "";
    offerEnabledInput.checked = data.offer_enabled ?? true;
  } catch (error) {
    // ignore
  }
}

saveFiltersBtn.addEventListener("click", async () => {
  saveFiltersBtn.disabled = true;
  saveFiltersBtn.textContent = "Сохраняем...";
  try {
    const payload = {
      filters: {
        categories: filterCategoriesInput.value
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        colors: filterColorsInput.value
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        features: filterFeaturesInput.value
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
      },
    };
    const response = await fetch("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error("Ошибка сохранения");
    }
    saveFiltersBtn.textContent = "Сохранено";
  } catch (error) {
    saveFiltersBtn.textContent = "Ошибка";
  } finally {
    setTimeout(() => {
      saveFiltersBtn.textContent = "Сохранить фильтры";
      saveFiltersBtn.disabled = false;
    }, 1500);
  }
});

const saveAllProductsBtn = document.getElementById("saveAllProductsBtn");
if (saveAllProductsBtn) {
  saveAllProductsBtn.addEventListener("click", async () => {
    saveAllProductsBtn.disabled = true;
    saveAllProductsBtn.textContent = "Сохраняем...";
    const ok = await saveAllProducts();
    saveAllProductsBtn.textContent = ok ? "Сохранено" : "Ошибка";
    setTimeout(() => {
      saveAllProductsBtn.textContent = "Сохранить все";
      saveAllProductsBtn.disabled = false;
    }, 1500);
  });
}

themePalette.addEventListener("click", (event) => {
  const target = event.target;
  if (!target.classList.contains("palette-color")) return;
  const color = target.dataset.color;
  themeColorInput.value = color;
  themeColorPicker.value = color;
  document.documentElement.style.setProperty("--accent", color);
  document.body.style.setProperty("--accent", color);
});

themeColorPicker.addEventListener("input", () => {
  themeColorInput.value = themeColorPicker.value;
  document.documentElement.style.setProperty("--accent", themeColorPicker.value);
  document.body.style.setProperty("--accent", themeColorPicker.value);
});

saveThemeBtn.addEventListener("click", async () => {
  saveThemeBtn.disabled = true;
  saveThemeBtn.textContent = "Сохраняем...";
  try {
    const payload = {
      theme_color: themeColorInput.value.trim() || "#94a36a",
    };
    const response = await fetch("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error("Ошибка сохранения");
    }
    document.documentElement.style.setProperty("--accent", payload.theme_color);
    document.body.style.setProperty("--accent", payload.theme_color);
    saveThemeBtn.textContent = "Сохранено";
  } catch (error) {
    saveThemeBtn.textContent = "Ошибка";
  } finally {
    setTimeout(() => {
      saveThemeBtn.textContent = "Сохранить цвет";
      saveThemeBtn.disabled = false;
    }, 1500);
  }
});

saveHeroBtn.addEventListener("click", async () => {
  saveHeroBtn.disabled = true;
  saveHeroBtn.textContent = "Сохраняем...";
  try {
    const payload = {
      hero_title: heroTitleInput.value.trim(),
      hero_subtitle: heroSubtitleInput.value.trim(),
    };
    const response = await fetch("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error("Ошибка сохранения");
    }
    saveHeroBtn.textContent = "Сохранено";
  } catch (error) {
    saveHeroBtn.textContent = "Ошибка";
  } finally {
    setTimeout(() => {
      saveHeroBtn.textContent = "Сохранить текст";
      saveHeroBtn.disabled = false;
    }, 1500);
  }
});

saveOfferBtn.addEventListener("click", async () => {
  saveOfferBtn.disabled = true;
  saveOfferBtn.textContent = "Сохраняем...";
  try {
    const payload = {
      offer_link_title:
        offerLinkTitleInput.value.trim() ||
        "Я принимаю условия Публичной оферты, а также даю согласие на обработку персональных данных.",
      offer_page_text: offerPageTextInput.value.trim() || "Публичная оферта",
      offer_link: offerLinkInput.value.trim(),
      offer_enabled: offerEnabledInput.checked,
    };
    const response = await fetch("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error("Ошибка сохранения");
    }
    saveOfferBtn.textContent = "Сохранено";
  } catch (error) {
    saveOfferBtn.textContent = "Ошибка";
  } finally {
    setTimeout(() => {
      saveOfferBtn.textContent = "Сохранить оферту";
      saveOfferBtn.disabled = false;
    }, 1500);
  }
});

importCsvBtn.addEventListener("click", async () => {
  const file = productsCsvInput.files[0];
  if (!file) {
    importCsvBtn.textContent = "Выберите файл";
    setTimeout(() => (importCsvBtn.textContent = "Импортировать"), 1500);
    return;
  }
  importCsvBtn.disabled = true;
  importCsvBtn.textContent = "Импорт...";
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch("/api/products/import", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error("Ошибка импорта");
    }
    await loadProducts();
    importCsvBtn.textContent = "Готово";
  } catch (error) {
    importCsvBtn.textContent = "Ошибка";
  } finally {
    setTimeout(() => {
      importCsvBtn.textContent = "Импортировать";
      importCsvBtn.disabled = false;
    }, 1500);
  }
});

exportCsvBtn.addEventListener("click", async () => {
  exportCsvBtn.disabled = true;
  exportCsvBtn.textContent = "Экспорт...";
  try {
    const response = await fetch("/api/products/export");
    if (!response.ok) {
      throw new Error("Ошибка экспорта");
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "products.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    exportCsvBtn.textContent = "Готово";
  } catch (error) {
    exportCsvBtn.textContent = "Ошибка";
  } finally {
    setTimeout(() => {
      exportCsvBtn.textContent = "Экспорт CSV";
      exportCsvBtn.disabled = false;
    }, 1500);
  }
});

async function setDeliveryLabelForAll(label) {
  const products = window.productsCache || [];
  if (!products.length) {
    await loadProducts();
  }
  const updated = (window.productsCache || []).map((product) => ({
    id: product.id,
    delivery_label: label,
  }));
  const response = await fetch("/api/products/bulk", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ products: updated }),
  });
  if (!response.ok) {
    throw new Error("Ошибка сохранения");
  }
  await loadProducts();
}

if (setTodayBtn) {
  setTodayBtn.addEventListener("click", async () => {
    setTodayBtn.disabled = true;
    setTodayBtn.textContent = "Сохраняем...";
    try {
      await setDeliveryLabelForAll("Доставим сегодня");
      setTodayBtn.textContent = "Готово";
    } catch (error) {
      setTodayBtn.textContent = "Ошибка";
    } finally {
      setTimeout(() => {
        setTodayBtn.textContent = "Доставим сегодня для всех";
        setTodayBtn.disabled = false;
      }, 1500);
    }
  });
}

if (setTomorrowBtn) {
  setTomorrowBtn.addEventListener("click", async () => {
    setTomorrowBtn.disabled = true;
    setTomorrowBtn.textContent = "Сохраняем...";
    try {
      await setDeliveryLabelForAll("Доставим завтра");
      setTomorrowBtn.textContent = "Готово";
    } catch (error) {
      setTomorrowBtn.textContent = "Ошибка";
    } finally {
      setTimeout(() => {
        setTomorrowBtn.textContent = "Доставим завтра для всех";
        setTomorrowBtn.disabled = false;
      }, 1500);
    }
  });
}

if (createProductBtn) {
  createProductBtn.addEventListener("click", async () => {
    createProductBtn.disabled = true;
    createProductBtn.textContent = "Создаем...";
    try {
      const response = await fetch("/api/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        throw new Error("Ошибка создания");
      }
      await loadProducts();
      createProductBtn.textContent = "Создать товар";
    } catch (error) {
      createProductBtn.textContent = "Ошибка";
      setTimeout(() => {
        createProductBtn.textContent = "Создать товар";
      }, 1500);
    } finally {
      createProductBtn.disabled = false;
    }
  });
}

saveBonusBtn.addEventListener("click", async () => {
  saveBonusBtn.disabled = true;
  saveBonusBtn.textContent = "Сохраняем...";
  try {
    const payload = {
      bonus_balance: Number(bonusBalanceInput.value || 0),
      bonus_earn_rate: Number(bonusEarnRateInput.value || 0),
      bonus_value: Number(bonusValueInput.value || 0),
      service_fee_rate: Number(serviceFeeRateInput.value || 0),
    };
    const response = await fetch("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error("Ошибка сохранения");
    }
    saveBonusBtn.textContent = "Сохранено";
  } catch (error) {
    saveBonusBtn.textContent = "Ошибка";
  } finally {
    setTimeout(() => {
      saveBonusBtn.textContent = "Сохранить";
      saveBonusBtn.disabled = false;
    }, 1500);
  }
});

savePromoBtn.addEventListener("click", async () => {
  savePromoBtn.disabled = true;
  savePromoBtn.textContent = "Сохраняем...";
  try {
    const payload = {
      promo_codes: parsePromoCodes(promoCodesInput.value),
    };
    const response = await fetch("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error("Ошибка сохранения");
    }
    savePromoBtn.textContent = "Сохранено";
  } catch (error) {
    savePromoBtn.textContent = "Ошибка";
  } finally {
    setTimeout(() => {
      savePromoBtn.textContent = "Сохранить промокоды";
      savePromoBtn.disabled = false;
    }, 1500);
  }
});

loadSettings();
loadCustomers();

if (customersSearch) {
  customersSearch.addEventListener("input", () => {
    const query = customersSearch.value.trim().toLowerCase();
    if (!query) {
      renderCustomers(customersCache);
      return;
    }
    const filtered = customersCache.filter((customer) => {
      const username = (customer.username || "").toLowerCase();
      const phone = (customer.phone || "").toLowerCase();
      const userId = (customer.user_id || "").toLowerCase();
      return (
        username.includes(query) ||
        phone.includes(query) ||
        userId.includes(query)
      );
    });
    renderCustomers(filtered);
  });
}

customersList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!target.dataset.action) return;
  if (target.dataset.action !== "delete-customer") return;
  const customerId = target.dataset.id;
  if (!customerId) return;
  if (!confirm("Удалить заказчика?")) return;
  target.disabled = true;
  try {
    const response = await fetch(`/api/customers/${encodeURIComponent(customerId)}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Ошибка удаления");
    loadCustomers();
  } catch (error) {
    target.textContent = "Ошибка";
    setTimeout(() => (target.textContent = "Удалить заказчика"), 1500);
  } finally {
    target.disabled = false;
  }
});
