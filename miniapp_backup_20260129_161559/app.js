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
let isCartOpen = false;

const promoRules = {
  FLOWER10: { type: "percent", value: 10 },
  MOSCOW500: { type: "fixed", value: 500 },
};

const categoryFilters = document.getElementById("categoryFilters");
const colorFilters = document.getElementById("colorFilters");
const featureFilters = document.getElementById("featureFilters");
const productGrid = document.getElementById("productGrid");
const cartBar = document.getElementById("cartBar");
const cartTotal = document.getElementById("cartTotal");
const cartSheet = document.getElementById("cartSheet");
const catalogView = document.getElementById("catalogView");
const profileView = document.getElementById("profileView");
const aboutView = document.getElementById("aboutView");
const navItems = document.querySelectorAll(".bottom-nav .nav-item");
const bottomNav = document.querySelector(".bottom-nav");
const heroTitle = document.getElementById("heroTitle");
const heroSubtitle = document.getElementById("heroSubtitle");
const profileAvatar = document.getElementById("profileAvatar");
const profileName = document.getElementById("profileName");
const profileUsername = document.getElementById("profileUsername");
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
const selfRecipientToggle = document.getElementById("selfRecipientToggle");
const recipientNameInput = document.getElementById("recipientNameInput");
const recipientPhoneInput = document.getElementById("recipientPhoneInput");
const promoInput = document.getElementById("promoInput");
const submitOrderBtn = document.getElementById("submitOrderBtn");
const formHint = document.getElementById("formHint");
const toast = document.getElementById("toast");

document.getElementById("openCartBtn").addEventListener("click", () => {
  setStep(1);
  cartSheet.classList.add("open");
  bottomNav.classList.add("hidden");
  isCartOpen = true;
  updateCartBarVisibility();
});
document.getElementById("closeCartBtn").addEventListener("click", () => {
  cartSheet.classList.remove("open");
  bottomNav.classList.remove("hidden");
  isCartOpen = false;
  updateCartBarVisibility();
});

function setView(view) {
  currentView = view;
  catalogView.classList.toggle("hidden", view !== "catalog");
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
  currentUser = {
    id: user.id,
    username: user.username || "",
    name: fullName,
  };
}

navItems.forEach((btn) => {
  btn.addEventListener("click", () => {
    const view = btn.dataset.view;
    if (view === "cart") {
      setStep(1);
      cartSheet.classList.add("open");
      bottomNav.classList.add("hidden");
      isCartOpen = true;
      updateCartBarVisibility();
      return;
    }
    cartSheet.classList.remove("open");
    bottomNav.classList.remove("hidden");
    isCartOpen = false;
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
  const shouldHide = currentView !== "catalog" || isCartOpen;
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
  const promoCode = promoInput.value.trim().toUpperCase();
  state.promo = promoCode || null;
  const { discount } = applyPromo(subtotal);
  let total = subtotal + serviceFee + state.deliveryFee - discount;
  let bonus = 0;
  if (state.bonusApplied) {
    bonus = Math.min(settings.bonusValue, Math.max(total, 0));
    total -= bonus;
  }
  const bonusEarned = Math.round(subtotal * settings.bonusEarnRate);
  subtotalEl.textContent = formatRub(subtotal);
  serviceFeeEl.textContent = formatRub(serviceFee);
  deliveryFeeEl.textContent = formatRub(state.deliveryFee);
  discountEl.textContent = `- ${formatRub(discount)}`;
  bonusEl.textContent = `- ${formatRub(bonus)}`;
  bonusBalanceEl.textContent = formatRub(settings.bonusBalance);
  bonusEarnedEl.textContent = formatRub(bonusEarned);
  totalEl.textContent = formatRub(total);
  discountRow.style.display = discount > 0 ? "flex" : "none";
  bonusRow.style.display = bonus > 0 ? "flex" : "none";
  nextStepBtn.disabled = items.length === 0;
  updateCartBar();
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

async function loadCustomerData() {
  try {
    const response = await fetch(`/api/customers/${currentUser.id}`);
    const data = await response.json();
    renderAddresses(data.addresses || []);
  } catch (error) {
    renderAddresses([]);
  }
}

async function loadOrdersHistory() {
  try {
    const response = await fetch(`/api/orders?user_id=${currentUser.id}`);
    const data = await response.json();
    ordersHistory.innerHTML = "";
    if (!data.length) {
      ordersHistory.innerHTML = "<div>Пока нет заказов</div>";
      return;
    }
    data.forEach((order) => {
      const row = document.createElement("div");
      row.className = "profile-order";
      const items = (order.items || [])
        .map((item) => `${item.name} × ${item.qty}`)
        .join(", ");
      row.innerHTML = `
        <div>
          <div>Заказ №${order.id}</div>
          <div>${order.created_at || ""}</div>
          <div>${items}</div>
        </div>
        <span>${formatRub(order.total)}</span>
      `;
      ordersHistory.appendChild(row);
    });
  } catch (error) {
    ordersHistory.innerHTML = "<div>Ошибка загрузки</div>";
  }
}

function renderFilters() {
  const categories =
    settings.filters.categories.length > 0
      ? ["Все", ...settings.filters.categories]
      : ["Все", ...new Set(state.products.map((p) => p.category))];
  const colorTags =
    settings.filters.colors.length > 0
      ? ["Все", ...settings.filters.colors]
      : ["Все"];
  const featureTags =
    settings.filters.features.length > 0
      ? ["Все", ...settings.filters.features]
      : ["Все"];

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
    card.innerHTML = `
      <div class="card-image">
        <span class="badge">${product.delivery_label || "Доставим завтра"}</span>
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
    if (cartSheet.contains(target)) {
      updateCartQty(id, action);
    } else {
      updatePreviewQty(id, action);
    }
  }
});

promoInput.addEventListener("input", updateCartSheet);

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
  const phone = phoneInput.value.trim();
  if (!/^\+7\d{10}$/.test(phone)) {
    formHint.textContent = "Введите телефон в формате +7XXXXXXXXXX";
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
  const promoCode = promoInput.value.trim().toUpperCase();
  try {
    const response = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUser.id,
        username: currentUser.username,
        phone,
        items,
        promo_code: promoCode || null,
        name: nameInput.value.trim(),
        email: emailInput.value.trim(),
        address: addressInput.value.trim(),
        delivery_time: deliveryTimeInput.value.trim(),
        recipient_name: recipientNameInput.value.trim(),
        recipient_phone: recipientPhoneInput.value.trim(),
        delivery_id: state.deliveryId,
        delivery_fee: state.deliveryFee,
        bonus: state.bonusApplied ? settings.bonusValue : 0,
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Ошибка отправки");
    }
    const result = await response.json();
    showToast(`Заказ принят! №${result.order_id}`);
    cartSheet.classList.remove("open");
    state.cart = {};
    phoneInput.value = "";
    promoInput.value = "";
    state.promo = null;
    setStep(1);
    renderProducts();
    updateCartBar();
    updateCartSheet();
    loadOrdersHistory();
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
    const response = await fetch(`/api/customers/${currentUser.id}`, {
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
    const settingsResponse = await fetch("/api/settings");
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
    deliveryTimeInput.value = DEFAULT_DELIVERY_TIME;
  }

  if (window.Telegram && Telegram.WebApp) {
    const tgUser = Telegram.WebApp.initDataUnsafe?.user;
    applyProfile(tgUser);
    Telegram.WebApp.expand();
  }
  loadCustomerData();
  loadOrdersHistory();
}

init();
