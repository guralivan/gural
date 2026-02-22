const state = {
  products: [],
  category: "Все",
  colorTag: "Все",
  featureTag: "Все",
  cart: {},
  promo: null,
  deliveryId: "mkad",
  deliveryFee: 500,
  bonusApplied: false,
  bonusAppliedAmount: 0,
  userBonusBalance: 0,
  previewQty: {},
};

const placeholderImage =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'><rect width='100%25' height='100%25' fill='%23f0f0f0'/><text x='50%25' y='50%25' fill='%23999' font-size='24' font-family='Arial' text-anchor='middle' dominant-baseline='middle'>Фото</text></svg>";

const settings = {
  serviceFeeRate: 0.1,
  bonusValue: 300,
  bonusBalance: 500,
  bonusEarnRate: 0.01,
  filters: {
    categories: [],
    colors: [],
    features: [],
  },
};

const DEFAULT_DELIVERY_TIME = "2026-01-30T10:00";
let currentUser = { id: "guest", username: "", name: "Пользователь" };
let currentView = "catalog";
const API_BASE = window.API_BASE || "";

let promoRules = {
  FLOWER10: { type: "percent", value: 10 },
  MOSCOW500: { type: "fixed", value: 500 },
};

const categoryFilters = document.getElementById("categoryFilters");
const colorFilters = document.getElementById("colorFilters");
const featureFilters = document.getElementById("featureFilters");
const productGrid = document.getElementById("productGrid");
const cartBar = document.getElementById("cartBar");
const cartTotal = document.getElementById("cartTotal");
const catalogView = document.getElementById("catalogView");
const cartView = document.getElementById("cartView");
const profileView = document.getElementById("profileView");
const aboutView = document.getElementById("aboutView");
const navItems = document.querySelectorAll(".bottom-nav .nav-item");
const heroTitle = document.getElementById("heroTitle");
const heroSubtitle = document.getElementById("heroSubtitle");
const profileAvatar = document.getElementById("profileAvatar");
const profileName = document.getElementById("profileName");
const profileUsername = document.getElementById("profileUsername");
const profileBonusValue = document.getElementById("profileBonusValue");
const addressesList = document.getElementById("addressesList");
const addressInputProfile = document.getElementById("addressInputProfile");
const addAddressBtn = document.getElementById("addAddressBtn");
const ordersHistory = document.getElementById("ordersHistory");
const savedAddresses = document.getElementById("savedAddresses");
const cartList = document.getElementById("cartList");
const subtotalEl = document.getElementById("subtotal");
const discountEl = document.getElementById("discount");
const totalEl = document.getElementById("total");
const discountRow = document.getElementById("discountRow");
const serviceFeeEl = document.getElementById("serviceFee");
const deliveryFeeEl = document.getElementById("deliveryFee");
const bonusEl = document.getElementById("bonus");
const bonusRow = document.getElementById("bonusRow");
const bonusBalanceEl = document.getElementById("bonusBalance");
const bonusEarnedEl = document.getElementById("bonusEarned");
const deliveryGrid = document.getElementById("deliveryGrid");
const deliveryNote = document.getElementById("deliveryNote");
const bonusToggle = document.getElementById("bonusToggle");
const sheetTitle = document.getElementById("sheetTitle");
const cartStep = document.getElementById("cartStep");
const checkoutStep = document.getElementById("checkoutStep");
const nextStepBtn = document.getElementById("nextStepBtn");
const backStepBtn = document.getElementById("backStepBtn");
const nameInput = document.getElementById("nameInput");
const phoneInput = document.getElementById("phoneInput");
const emailInput = document.getElementById("emailInput");
const addressInput = document.getElementById("addressInput");
const deliveryTimeInput = document.getElementById("deliveryTimeInput");
const deliveryTimeHint = document.getElementById("deliveryTimeHint");
const selfRecipientToggle = document.getElementById("selfRecipientToggle");
const recipientFields = document.getElementById("recipientFields");
const recipientNameInput = document.getElementById("recipientNameInput");
const recipientPhoneInput = document.getElementById("recipientPhoneInput");
const promoInput = document.getElementById("promoInput");
const applyPromoBtn = document.getElementById("applyPromoBtn");
const promoStatus = document.getElementById("promoStatus");
const submitOrderBtn = document.getElementById("submitOrderBtn");
const formHint = document.getElementById("formHint");
const toast = document.getElementById("toast");
const offerRow = document.getElementById("offerRow");
const offerLink = document.getElementById("offerLink");

document.getElementById("openCartBtn").addEventListener("click", () => {
  setStep(1);
  setView("cart");
});

function setView(view) {
  currentView = view;
  catalogView.classList.toggle("hidden", view !== "catalog");
  cartView.classList.toggle("hidden", view !== "cart");
  profileView.classList.toggle("hidden", view !== "profile");
  aboutView.classList.toggle("hidden", view !== "about");
  navItems.forEach((btn) => btn.classList.remove("active"));
  navItems.forEach((btn) => {
    if (btn.dataset.view === view) btn.classList.add("active");
  });
  updateCartBarVisibility();
}

function applyProfile(user) {
  if (!user) return;
  const firstName = user.first_name || "";
  const lastName = user.last_name || "";
  const fullName = `${firstName} ${lastName}`.trim() || "Пользователь";
  profileName.textContent = fullName;
  profileUsername.textContent = user.username ? `@${user.username}` : "—";
  profileAvatar.textContent = (firstName || fullName).charAt(0).toUpperCase();
  const userKey = user.username ? `@${user.username}` : `tg:${user.id}`;
  currentUser = {
    id: userKey,
    username: user.username || "",
    name: fullName,
  };
  if (nameInput && !nameInput.value.trim()) {
    nameInput.value = fullName;
  }
}

navItems.forEach((btn) => {
  btn.addEventListener("click", () => {
    const view = btn.dataset.view;
    if (view === "cart") {
      setStep(1);
      setView("cart");
      return;
    }
    setView(view);
  });
});

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2000);
}

function formatRub(value) {
  return `${Math.round(value)} ₽`;
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

function toLocalInputValue(date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(
    date.getDate()
  )}T${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}


function getNextDeliverySlot(now = new Date()) {
  const start = new Date(now);
  if (start.getHours() >= 19) {
    start.setDate(start.getDate() + 1);
    start.setHours(10, 0, 0, 0);
  } else {
    start.setHours(start.getHours() + 5);
  }
  const end = new Date(start);
  end.setHours(end.getHours() + 2);
  return { start, end };
}

function updateDeliveryNote() {
  if (!deliveryNote) return;
  const { start, end } = getNextDeliverySlot();
  const dateLabel = start.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
  });
  const timeRange = `${pad2(start.getHours())}:${pad2(
    start.getMinutes()
  )} - ${pad2(end.getHours())}:${pad2(end.getMinutes())}`;
  deliveryNote.textContent = `Ближайшая доступная доставка: ${dateLabel}, ${timeRange}`;
}

function updateDeliveryTimeHint() {
  if (!deliveryTimeInput) return;
  const { start, end } = getNextDeliverySlot();
  deliveryTimeInput.min = toLocalInputValue(start);
  if (deliveryTimeHint) {
    const dateLabel = start.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
    });
    const timeRange = `${pad2(start.getHours())}:${pad2(
      start.getMinutes()
    )} - ${pad2(end.getHours())}:${pad2(end.getMinutes())}`;
    deliveryTimeHint.textContent = `Ближайшая доставка: ${dateLabel}, ${timeRange}`;
  }
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    throw new Error("API недоступен");
  }
  return response;
}
function applyPromo(subtotal) {
  if (!state.promo) return { discount: 0, total: subtotal };
  const rule = promoRules[state.promo];
  if (!rule) return { discount: 0, total: subtotal };
  let discount = 0;
  if (rule.type === "percent") {
    discount = (subtotal * rule.value) / 100;
  } else {
    discount = rule.value;
  }
  discount = Math.min(discount, subtotal);
  return { discount, total: subtotal - discount };
}

function updateCartBarVisibility() {
  const shouldHide = currentView !== "catalog";
  cartBar.classList.toggle("hidden", shouldHide);
  if (!shouldHide) {
    updateCartBar();
  }
}

function updateCartBar() {
  const subtotal = Object.values(state.cart).reduce(
    (sum, item) => sum + item.price * item.qty,
    0
  );
  cartTotal.textContent = formatRub(subtotal);
}

function updateCartSheet() {
  cartList.innerHTML = "";
  const items = Object.values(state.cart);
  if (items.length === 0) {
    cartList.innerHTML = "<div>Корзина пуста</div>";
  } else {
    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "cart-item";
      row.innerHTML = `
        <img src="${item.image || placeholderImage}" alt="${item.name}" />
        <div class="cart-item-info">
          <div class="cart-item-title">${item.name}</div>
          <div class="cart-item-price">${formatRub(item.price)}</div>
        </div>
        <div class="qty">
          <button data-action="dec" data-id="${item.id}">-</button>
          <span>${item.qty}</span>
          <button data-action="inc" data-id="${item.id}">+</button>
        </div>
        <button class="cart-remove" data-action="remove" data-id="${item.id}">✕</button>
      `;
      cartList.appendChild(row);
    });
  }
  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  const serviceFee = Math.round(subtotal * settings.serviceFeeRate);
  const { discount } = applyPromo(subtotal);
  let total = subtotal + serviceFee + state.deliveryFee - discount;
  let bonus = 0;
  if (state.bonusApplied) {
    bonus = Math.min(state.userBonusBalance, Math.max(total, 0));
    total -= bonus;
  }
  const bonusEarned = Math.round(subtotal * settings.bonusEarnRate);
  state.bonusAppliedAmount = bonus;
  subtotalEl.textContent = formatRub(subtotal);
  serviceFeeEl.textContent = formatRub(serviceFee);
  deliveryFeeEl.textContent = formatRub(state.deliveryFee);
  discountEl.textContent = `- ${formatRub(discount)}`;
  bonusEl.textContent = `- ${formatRub(bonus)}`;
  bonusBalanceEl.textContent = formatRub(state.userBonusBalance);
  bonusEarnedEl.textContent = formatRub(bonusEarned);
  totalEl.textContent = formatRub(total);
  discountRow.style.display = discount > 0 ? "flex" : "none";
  bonusRow.style.display = bonus > 0 ? "flex" : "none";
  nextStepBtn.disabled = items.length === 0;
  if (state.userBonusBalance <= 0) {
    state.bonusApplied = false;
    bonusToggle.checked = false;
  }
  bonusToggle.disabled = state.userBonusBalance <= 0;
  updateCartBar();
  if (applyPromoBtn) {
    applyPromoBtn.disabled = items.length === 0;
  }
}

function renderAddresses(addresses) {
  addressesList.innerHTML = "";
  savedAddresses.innerHTML = "";
  if (!addresses.length) {
    addressesList.innerHTML = "<div>Адресов пока нет</div>";
    return;
  }
  addresses.forEach((address) => {
    const row = document.createElement("div");
    row.className = "profile-address";
    row.innerHTML = `
      <span>${address}</span>
      <button data-address="${address}">Выбрать</button>
    `;
    addressesList.appendChild(row);
    const option = document.createElement("option");
    option.value = address;
    savedAddresses.appendChild(option);
  });
}

function updateProfileBonus() {
  if (!profileBonusValue) return;
  profileBonusValue.textContent = Math.round(state.userBonusBalance || 0);
}

async function loadCustomerData() {
  if (currentUser.id === "guest") {
    state.userBonusBalance = 0;
    renderAddresses([]);
    updateCartSheet();
    updateProfileBonus();
    return;
  }
  try {
    const response = await apiFetch(`/api/customers/${currentUser.id}`);
    const data = await response.json();
    renderAddresses(data.addresses || []);
    if (data.phone && !phoneInput.value) {
      phoneInput.value = data.phone;
    }
    if (typeof data.bonus_balance === "number") {
      state.userBonusBalance = data.bonus_balance;
    } else {
      state.userBonusBalance = settings.bonusBalance;
    }
  } catch (error) {
    state.userBonusBalance = settings.bonusBalance;
    renderAddresses([]);
  }
  updateCartSheet();
  updateProfileBonus();
}

async function loadOrdersHistory() {
  try {
    const response = await apiFetch(`/api/orders?user_id=${currentUser.id}`);
    const data = await response.json();
    ordersHistory.innerHTML = "";
    if (!data.length) {
      ordersHistory.innerHTML = "<div>Пока нет заказов</div>";
      return;
    }
    const sortedOrders = [...data].sort((a, b) => (b.id || 0) - (a.id || 0));
    sortedOrders.forEach((order) => {
      const row = document.createElement("div");
      row.className = "profile-order";
      const itemsHtml = (order.items || [])
        .map((item) => {
          const product = state.products.find((p) => p.id === item.id);
          const image = product?.image || placeholderImage;
          return `
            <div class="order-item">
              <img src="${image}" alt="${item.name}" />
              <div>
                <div>${item.name}</div>
                <div>${item.qty} шт.</div>
              </div>
            </div>
          `;
        })
        .join("");
      row.innerHTML = `
        <div>
          <div>Заказ №${order.id}</div>
          <div>${order.created_at || ""}</div>
          <div>Статус: ${order.status || "—"}</div>
          <div class="order-items">${itemsHtml}</div>
        </div>
        <div class="order-actions">
          <span>${formatRub(order.total)}</span>
          <button class="order-delete" data-order-id="${order.id}">Удалить</button>
        </div>
      `;
      ordersHistory.appendChild(row);
    });
  } catch (error) {
    ordersHistory.innerHTML = "<div>Ошибка загрузки</div>";
  }
}

ordersHistory.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) return;
  const orderId = target.dataset.orderId;
  if (!orderId) return;
  if (!confirm("Удалить заказ из истории?")) return;
  apiFetch(`/api/orders/${orderId}`, { method: "DELETE" })
    .then(() => loadOrdersHistory())
    .catch(() => showToast("Не удалось удалить"));
});

function renderFilters() {
  const categories =
    settings.filters.categories.length > 0
      ? ["Все", ...settings.filters.categories]
      : ["Все", ...new Set(state.products.map((p) => p.category))];

  const allTags = [
    ...new Set(state.products.flatMap((p) => (p.tags || []).map(String))),
  ];
  const colorSet = new Set([
    "Красные",
    "Розовые",
    "Белые",
    "Зеленые",
    "Желтые",
    "Фиолетовые",
    "Синие",
    "Оранжевые",
  ]);

  const defaultColors = allTags.filter((tag) => colorSet.has(tag));
  const defaultFeatures = allTags.filter((tag) => !colorSet.has(tag));
  const fallbackColors = ["Красные", "Розовые", "Белые", "Зеленые"];
  const fallbackFeatures = [
    "Сеты",
    "Высокие",
    "Ароматные",
    "Стойкие",
    "Пионовидные",
  ];

  const colorTags =
    settings.filters.colors.length > 0
      ? ["Все", ...settings.filters.colors]
      : [
          "Все",
          ...(defaultColors.length
            ? defaultColors
            : allTags.length
              ? allTags
              : fallbackColors),
        ];
  const featureTags =
    settings.filters.features.length > 0
      ? ["Все", ...settings.filters.features]
      : [
          "Все",
          ...(defaultFeatures.length
            ? defaultFeatures
            : allTags.length
              ? allTags
              : fallbackFeatures),
        ];

  categoryFilters.innerHTML = "";
  colorFilters.innerHTML = "";
  featureFilters.innerHTML = "";

  categories.forEach((cat) => {
    const chip = document.createElement("button");
    chip.className = `chip ${cat === state.category ? "active" : ""}`;
    chip.textContent = cat;
    chip.addEventListener("click", () => {
      state.category = cat;
      renderFilters();
      renderProducts();
    });
    categoryFilters.appendChild(chip);
  });

  colorTags.forEach((tag) => {
    const chip = document.createElement("button");
    chip.className = `chip ${tag === state.colorTag ? "active" : ""}`;
    chip.textContent = tag;
    chip.addEventListener("click", () => {
      state.colorTag = tag;
      renderFilters();
      renderProducts();
    });
    colorFilters.appendChild(chip);
  });

  featureTags.forEach((tag) => {
    const chip = document.createElement("button");
    chip.className = `chip ${tag === state.featureTag ? "active" : ""}`;
    chip.textContent = tag;
    chip.addEventListener("click", () => {
      state.featureTag = tag;
      renderFilters();
      renderProducts();
    });
    featureFilters.appendChild(chip);
  });
}

function setStep(step) {
  if (step === 1) {
    cartStep.classList.remove("hidden");
    checkoutStep.classList.add("hidden");
    sheetTitle.textContent = "Корзина";
    formHint.textContent = "";
  } else {
    cartStep.classList.add("hidden");
    checkoutStep.classList.remove("hidden");
    sheetTitle.textContent = "Оформление";
  }
}

function renderProducts() {
  productGrid.innerHTML = "";
  const filtered = state.products.filter((p) => {
    const byCategory = state.category === "Все" || p.category === state.category;
    const byColor =
      state.colorTag === "Все" || (p.tags || []).includes(state.colorTag);
    const byFeature =
      state.featureTag === "Все" || (p.tags || []).includes(state.featureTag);
    return byCategory && byColor && byFeature;
  });

  filtered.forEach((product) => {
    const minQty = Number(product.min_qty || 1);
    const cartQty = state.cart[product.id]?.qty || 0;
    const previewQty =
      state.previewQty[product.id] ?? (cartQty > 0 ? cartQty : minQty);
    const image = product.image || placeholderImage;
    const card = document.createElement("div");
    card.className = "card";
    const label = product.delivery_label || "Доставим завтра";
    const badgeClass =
      label.toLowerCase().includes("сегодня") ? "badge today" : "badge";
    card.innerHTML = `
      <div class="card-image">
        <span class="${badgeClass}">${label}</span>
        <img src="${image}" alt="${product.name}" />
        <button class="card-cart" aria-label="Добавить в корзину" data-action="add" data-id="${product.id}">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2Zm10 0c-1.1 0-1.99.9-1.99 2S15.9 22 17 22s2-.9 2-2-.9-2-2-2ZM7.2 14h9.9c.75 0 1.4-.41 1.75-1.03l3.24-5.88a1 1 0 0 0-.87-1.48H6.2L5.27 2H2v2h1.6l2.52 9.24c.2.76.89 1.28 1.68 1.28Z"/>
          </svg>
        </button>
      </div>
      <div class="card-title">${product.name}</div>
      <div class="card-desc">${product.description || ""}</div>
      <div class="card-footer">
        <div class="price">${formatRub(product.price * previewQty)}</div>
        <div class="qty">
          <button data-action="dec" data-id="${product.id}">-</button>
          <span>${previewQty}</span>
          <button data-action="inc" data-id="${product.id}">+</button>
        </div>
      </div>
    `;
    productGrid.appendChild(card);
  });
}

function updatePreviewQty(id, action) {
  const product = state.products.find((p) => p.id === id);
  if (!product) return;
  const minQty = Number(product.min_qty || 1);
  const current = state.previewQty[id] ?? minQty;
  let next = current;
  if (action === "inc") {
    next = current + minQty;
  } else if (action === "dec") {
    next = current - minQty;
    if (next < minQty) next = minQty;
  }
  state.previewQty[id] = next;
  renderProducts();
}

function addToCart(id) {
  const product = state.products.find((p) => p.id === id);
  if (!product) return;
  const minQty = Number(product.min_qty || 1);
  const previewQty = state.previewQty[id] ?? minQty;
  state.cart[id] = { ...product, qty: previewQty };
  state.previewQty[id] = previewQty;
  renderProducts();
  updateCartBar();
  updateCartSheet();
}

function updateCartQty(id, action) {
  const product = state.products.find((p) => p.id === id);
  if (!product) return;
  if (action === "remove") {
    delete state.cart[id];
    state.previewQty[id] = Number(product.min_qty || 1);
    renderProducts();
    updateCartBar();
    updateCartSheet();
    return;
  }
  const current = state.cart[id]?.qty || 0;
  const minQty = Number(product.min_qty || 1);
  let next = current;
  if (action === "inc") {
    next = current + minQty;
  } else if (action === "dec") {
    next = current - minQty;
    if (next < minQty) next = 0;
  }
  if (next <= 0) {
    delete state.cart[id];
    state.previewQty[id] = minQty;
  } else {
    state.cart[id] = { ...product, qty: next };
    state.previewQty[id] = next;
  }
  renderProducts();
  updateCartBar();
  updateCartSheet();
}

document.addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  const action = target.dataset.action;
  const id = target.dataset.id;
  if (action && id) {
    if (action === "add") {
      addToCart(id);
      return;
    }
    if (cartView.contains(target)) {
      updateCartQty(id, action);
    } else {
      updatePreviewQty(id, action);
    }
  }
});

if (applyPromoBtn) {
  applyPromoBtn.addEventListener("click", () => {
    const promoCode = promoInput.value.trim().toUpperCase();
    if (!promoCode) {
      state.promo = null;
      promoStatus.textContent = "";
      updateCartSheet();
      return;
    }
    const rule = promoRules[promoCode];
    if (!rule) {
      state.promo = null;
      promoStatus.textContent = "Промокод не найден";
      updateCartSheet();
      return;
    }
    state.promo = promoCode;
    promoStatus.textContent = "Промокод применен";
    updateCartSheet();
  });
}

deliveryGrid.addEventListener("click", (event) => {
  const card = event.target.closest(".delivery-card");
  if (!card) return;
  deliveryGrid.querySelectorAll(".delivery-card").forEach((el) => {
    el.classList.remove("active");
  });
  card.classList.add("active");
  state.deliveryId = card.dataset.id;
  state.deliveryFee = Number(card.dataset.fee || 0);
  updateCartSheet();
});

bonusToggle.addEventListener("change", () => {
  state.bonusApplied = bonusToggle.checked;
  updateCartSheet();
});

function syncRecipient() {
  if (!selfRecipientToggle.checked) return;
  recipientNameInput.value = nameInput.value;
  recipientPhoneInput.value = phoneInput.value;
}

function toggleRecipientFields() {
  const disabled = selfRecipientToggle.checked;
  recipientNameInput.disabled = disabled;
  recipientPhoneInput.disabled = disabled;
  recipientFields.classList.toggle("hidden", disabled);
  if (disabled) {
    syncRecipient();
  }
}

selfRecipientToggle.addEventListener("change", () => {
  toggleRecipientFields();
});

nameInput.addEventListener("input", syncRecipient);
phoneInput.addEventListener("input", syncRecipient);

nextStepBtn.addEventListener("click", () => {
  if (Object.keys(state.cart).length === 0) {
    formHint.textContent = "Добавьте хотя бы один товар";
    return;
  }
  formHint.textContent = "";
  setStep(2);
});

backStepBtn.addEventListener("click", () => {
  formHint.textContent = "";
  setStep(1);
});

submitOrderBtn.addEventListener("click", async () => {
  const rawPhone = phoneInput.value.trim();
  const phoneDigits = rawPhone.replace(/\D/g, "");
  let normalizedPhone = "";
  if (phoneDigits.length === 11 && phoneDigits.startsWith("8")) {
    normalizedPhone = `+7${phoneDigits.slice(1)}`;
  } else if (phoneDigits.length === 11 && phoneDigits.startsWith("7")) {
    normalizedPhone = `+7${phoneDigits.slice(1)}`;
  } else if (phoneDigits.length === 10) {
    normalizedPhone = `+7${phoneDigits}`;
  }
  if (!/^\+7\d{10}$/.test(normalizedPhone)) {
    formHint.textContent = "Введите телефон в формате +7 или 8XXXXXXXXXX";
    return;
  }
  if (Object.keys(state.cart).length === 0) {
    formHint.textContent = "Добавьте хотя бы один товар";
    return;
  }
  formHint.textContent = "";
  submitOrderBtn.disabled = true;
  submitOrderBtn.textContent = "Отправляем...";
  const items = Object.values(state.cart).map((item) => ({
    id: item.id,
    qty: item.qty,
  }));
  try {
    const response = await apiFetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUser.id,
        username: currentUser.username,
        phone: normalizedPhone,
        items,
        promo_code: state.promo || null,
        name: nameInput.value.trim(),
        email: emailInput.value.trim(),
        address: addressInput.value.trim(),
        delivery_time: deliveryTimeInput.value.trim(),
        recipient_name: recipientNameInput.value.trim(),
        recipient_phone: recipientPhoneInput.value.trim(),
        delivery_id: state.deliveryId,
        delivery_fee: state.deliveryFee,
        bonus: state.bonusApplied ? state.bonusAppliedAmount : 0,
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Ошибка отправки");
    }
    const result = await response.json();
    showToast(`Заказ принят! №${result.order_id}`);
    state.cart = {};
    phoneInput.value = "";
    promoInput.value = "";
    promoStatus.textContent = "";
    state.promo = null;
    setStep(1);
    renderProducts();
    updateCartBar();
    updateCartSheet();
    loadOrdersHistory();
    setView("catalog");
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (error) {
    formHint.textContent = error.message || "Не удалось отправить заказ";
  } finally {
    submitOrderBtn.disabled = false;
    submitOrderBtn.textContent = "Оформить заказ";
  }
});

addressesList.addEventListener("click", (event) => {
  const target = event.target;
  if (target.tagName !== "BUTTON") return;
  const address = target.dataset.address;
  if (address) {
    addressInput.value = address;
    showToast("Адрес выбран");
  }
});

addAddressBtn.addEventListener("click", async () => {
  const address = addressInputProfile.value.trim();
  if (!address) return;
  try {
    const existing = Array.from(
      addressesList.querySelectorAll(".profile-address span")
    ).map((el) => el.textContent);
    const response = await apiFetch(`/api/customers/${currentUser.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        addresses: [...existing, address],
        name: currentUser.name,
        username: currentUser.username,
      }),
    });
    if (response.ok) {
      addressInputProfile.value = "";
      loadCustomerData();
    }
  } catch (error) {
    // ignore
  }
});

async function init() {
  const response = await fetch("data/products.json");
  state.products = await response.json();
  try {
    const settingsResponse = await apiFetch("/api/settings");
    if (settingsResponse.ok) {
      const data = await settingsResponse.json();
      settings.serviceFeeRate = Number(data.service_fee_rate ?? 0.1);
      settings.bonusValue = Number(data.bonus_value ?? 300);
      settings.bonusBalance = Number(data.bonus_balance ?? 500);
      settings.bonusEarnRate = Number(data.bonus_earn_rate ?? 0.01);
      const themeColor = data.theme_color || "#94a36a";
      document.documentElement.style.setProperty("--accent", themeColor);
      document.body.style.setProperty("--accent", themeColor);
      heroTitle.textContent = data.hero_title || heroTitle.textContent;
      heroSubtitle.textContent = data.hero_subtitle || heroSubtitle.textContent;
      if (data.filters) {
        settings.filters = {
          categories: data.filters.categories || [],
          colors: data.filters.colors || [],
          features: data.filters.features || [],
        };
      }
      if (Array.isArray(data.promo_codes)) {
        promoRules = data.promo_codes.reduce((acc, item) => {
          if (!item || !item.code) return acc;
          acc[item.code.toUpperCase()] = {
            type: item.type === "percent" ? "percent" : "fixed",
            value: Number(item.value || 0),
          };
          return acc;
        }, {});
      }
      if (offerLink && typeof data.offer_link === "string") {
        const link = data.offer_link.trim();
        if (link) {
          offerLink.href = link;
          offerLink.classList.remove("hidden");
        } else {
          offerLink.classList.add("hidden");
        }
      }
      if (offerLink) {
        const linkTitle =
          typeof data.offer_link_title === "string"
            ? data.offer_link_title.trim()
            : "";
        const fallbackText =
          typeof data.offer_text === "string" ? data.offer_text.trim() : "";
        const text = linkTitle || fallbackText;
        if (text) {
          offerLink.textContent = text;
        }
      }
      if (offerRow && typeof data.offer_enabled === "boolean") {
        offerRow.classList.toggle("hidden", !data.offer_enabled);
      }
    }
  } catch (error) {
    // ignore
  }
  renderFilters();
  renderProducts();
  updateCartBar();
  updateCartSheet();
  toggleRecipientFields();
  setView("catalog");
  if (!deliveryTimeInput.value) {
    const { start } = getNextDeliverySlot();
    deliveryTimeInput.value = toLocalInputValue(start);
  }
  updateDeliveryNote();
  updateDeliveryTimeHint();

  if (window.Telegram && Telegram.WebApp) {
    const tgUser = Telegram.WebApp.initDataUnsafe?.user;
    applyProfile(tgUser);
    Telegram.WebApp.expand();
  }
  loadCustomerData();
  loadOrdersHistory();
}

if (deliveryTimeInput) {
  deliveryTimeInput.addEventListener("change", () => {
    updateDeliveryTimeHint();
  });
}

init();
