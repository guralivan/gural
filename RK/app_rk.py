# -*- coding: utf-8 -*-
"""
Приложение эффективной рекламы маркетплейса (RK).
Объединяет загрузку Excel (отчёт «По дням»), аналитику по дням, калькулятор метрик и планировщик.
"""
from __future__ import division
import io
import json
import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Путь к папке для сохранения загруженных файлов (рядом с app_rk.py)
RK_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(RK_DIR, "uploads")
LAST_UPLOAD_PATH = os.path.join(UPLOADS_DIR, "last_upload.xlsx")

from calc import (
    parse_excel,
    calculate_period,
    calculate_organic,
    breakeven_cpl,
    planner,
    evaluate_day,
    filter_days_by_period,
    aggregate_daily_kpis,
    aggregate_by_type,
    get_recommendations,
    aggregate_for_calculator,
    day_for_calculator,
)

st.set_page_config(page_title="Реклама маркетплейса RK", layout="wide", initial_sidebar_state="expanded")

# Session state для загруженных данных
if "rk_days" not in st.session_state:
    st.session_state.rk_days = []
if "rk_details" not in st.session_state:
    st.session_state.rk_details = {}
if "rk_filename" not in st.session_state:
    st.session_state.rk_filename = None

# Загрузка сохранённого состояния калькулятора (для аналитики и дефолтов виджетов)
CALC_STATE_PATH = os.path.join(UPLOADS_DIR, "calculator_state.json")
if "rk_calc_loaded" not in st.session_state:
    st.session_state.rk_calc_loaded = False
if not st.session_state.rk_calc_loaded and os.path.isfile(CALC_STATE_PATH):
    try:
        with open(CALC_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            st.session_state["rk_calc_" + k] = v
        st.session_state.rk_calc_loaded = True
    except Exception:
        st.session_state.rk_calc_loaded = True


def _fmt_cur(v):
    if v is None or (isinstance(v, float) and (v != v)):
        return "— ₽"
    return f"{int(round(v)):,} ₽".replace(",", " ")


def _fmt_cur2(v, decimals=2):
    """Валюта с копейками (для безубыточного CPL)."""
    if v is None or (isinstance(v, float) and (v != v)):
        return "— ₽"
    return f"{v:,.{decimals}f} ₽".replace(",", " ")


def _fmt_pct(v):
    if v is None or (isinstance(v, float) and (v != v)):
        return "—%"
    return f"{v:.1f}%"


def _fmt_num(v, decimals=0):
    if v is None or (isinstance(v, float) and (v != v)):
        return "—"
    return f"{v:,.{decimals}f}".replace(",", " ")


# --- Сайдбар: загрузка файла ---
st.sidebar.header("📁 Данные")
uploaded = st.sidebar.file_uploader(
    "Загрузить Excel отчёт (раздел «По дням»)",
    type=["xlsx", "xls"],
    key="rk_upload",
)
if uploaded:
    try:
        days, details = parse_excel(uploaded)
        st.session_state.rk_days = days
        st.session_state.rk_details = details
        st.session_state.rk_filename = uploaded.name
        # Сохраняем файл на диск
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        ext = ".xlsx" if (uploaded.name or "").lower().endswith(".xlsx") else ".xls"
        path = os.path.join(UPLOADS_DIR, "last_upload" + ext)
        with open(path, "wb") as f:
            f.write(uploaded.getvalue())
        st.sidebar.success(f"Загружено: {uploaded.name}, дней: {len(days)}")
    except Exception as e:
        st.sidebar.error(f"Ошибка: {e}")
        st.session_state.rk_days = []
        st.session_state.rk_details = {}
        st.session_state.rk_filename = None
else:
    # Подгрузка последнего сохранённого файла, если нет новой загрузки
    if not st.session_state.rk_days and os.path.isdir(UPLOADS_DIR):
        for name in ("last_upload.xlsx", "last_upload.xls"):
            path = os.path.join(UPLOADS_DIR, name)
            if os.path.isfile(path):
                try:
                    with open(path, "rb") as f:
                        days, details = parse_excel(f)
                    st.session_state.rk_days = days
                    st.session_state.rk_details = details
                    st.session_state.rk_filename = name
                    break
                except Exception:
                    pass
    if st.session_state.rk_filename:
        st.sidebar.info(f"Текущий файл: {st.session_state.rk_filename}")
    else:
        st.sidebar.info("Загрузите xlsx/xls с отчётом WB «По дням»")

# --- Табы ---
tab_analytics, tab_calc, tab_planner = st.tabs(["📊 Аналитика по дням", "🧮 Калькулятор метрик", "🎯 Планировщик продаж"])

# ========== Вкладка: Аналитика по дням ==========
with tab_analytics:
    st.header("Аналитика по дням")
    days_all = st.session_state.rk_days
    details_all = st.session_state.rk_details

    if not days_all:
        st.info("Загрузите Excel-отчёт в боковой панели, чтобы увидеть аналитику по дням.")
    else:
        period_options = {"all": "Весь период", "last7": "Последние 7 дней", "last14": "Последние 14 дней", "last30": "Последние 30 дней", "custom": "Произвольный"}
        period_select = st.selectbox("Период", list(period_options.keys()), format_func=lambda x: period_options[x], key="period_select")
        target_cpl = int(st.session_state.get("rk_breakeven_cpl", 500))
        start_date = end_date = None
        if period_select == "custom":
            start_date = st.date_input("Дата начала", value=datetime.now().date() - timedelta(days=30), key="start_date")
            end_date = st.date_input("Дата окончания", value=datetime.now().date(), key="end_date")
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

        filtered = filter_days_by_period(days_all, period=period_select, start_date=start_date, end_date=end_date)
        # Галочки: исключить ближайший день и/или дни без рекламы из расчёта
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            exclude_last_day = st.checkbox(
                "Исключить ближайший день из расчёта (данные за текущий день часто неполные)",
                value=False,
                key="rk_exclude_last_day",
            )
        with col_ex2:
            exclude_no_ad_days = st.checkbox(
                "Исключить дни без рекламы из расчёта",
                value=False,
                key="rk_exclude_no_ad_days",
            )
        if exclude_last_day and filtered:
            def _parse_date(d):
                s = (d.get("date") or "")
                parts = s.split(".")
                if len(parts) != 3:
                    return None
                try:
                    return datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
                except (ValueError, IndexError):
                    return None
            dates_parsed = [(d, _parse_date(d)) for d in filtered]
            max_dt = max((dt for _, dt in dates_parsed if dt is not None), default=None)
            if max_dt is not None:
                filtered = [d for d, dt in dates_parsed if dt != max_dt]
        if exclude_no_ad_days and filtered:
            filtered = [d for d in filtered if (d.get("cost") or 0) > 0]
        # Тумблер: за последние 7 дней заказы подгружаются с задержкой — конверсия корзина→заказ и доли РК/органика по заказам неверные. Можно не использовать их и брать параметры из калькулятора.
        use_conversions_last7 = st.checkbox(
            "Учитывать фактические конверсии за последние 7 дней (данные по заказам могут быть неполными)",
            value=False,
            key="rk_use_conversions_last7",
        )
        st.caption("Если выключено: за последние 7 дней целевой CPL считается по параметрам из калькулятора (Корзина→Заказ %, доля рекламы), т.к. заказы в отчёте подгружаются с задержкой.")
        today = datetime.now().date()
        param_cart_to_order = st.session_state.get("rk_calc_cart_to_order_now", 30)
        param_organic_share = st.session_state.get("rk_calc_organic_share", 50)
        param_ad_share = 100 - param_organic_share
        param_ad_carts_share = st.session_state.get("rk_calc_ad_carts_share", 50)
        if param_ad_share <= 0:
            param_ad_share = 50
        # Целевой CPL с органикой = прибыль × (корзина→заказ) × (выкуп) × (ad_carts_share/ad_share). По каждому дню — конверсии и доли из данных дня (или из параметров для последних 7 дней).
        profit = st.session_state.get("rk_calc_profit_now", 500)
        purchase_rate = st.session_state.get("rk_calc_purchase_rate", 20)
        targets = []
        for d in filtered:
            s = (d.get("date") or "")
            parts = s.split(".")
            dt_day = None
            if len(parts) == 3:
                try:
                    dt_day = datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
                except (ValueError, IndexError):
                    pass
            is_last7 = dt_day and (today - dt_day).days <= 7
            use_params = is_last7 and not use_conversions_last7
            carts_total = d.get("carts_total") or 0
            carts_rk = d.get("carts_rk") or 0
            orders = d.get("orders") or 0
            orders_rk = d.get("orders_rk") or 0
            if use_params:
                # Для последних 7 дней при выключенном тумблере — конверсии и доли из параметров (калькулятор).
                if carts_total > 0:
                    cart_to_order_total_d = param_cart_to_order
                    ad_carts_share_d = param_ad_carts_share
                    ad_share_d = param_ad_share
                    targets.append(breakeven_cpl(profit, cart_to_order_total_d, purchase_rate, ad_carts_share_d, ad_share_d))
                else:
                    targets.append(target_cpl)
            elif carts_total > 0 and orders > 0:
                cart_to_order_total_d = orders / carts_total * 100
                ad_carts_share_d = carts_rk / carts_total * 100
                ad_share_d = orders_rk / orders * 100
                targets.append(breakeven_cpl(profit, cart_to_order_total_d, purchase_rate, ad_carts_share_d, ad_share_d))
            else:
                targets.append(target_cpl)
        filtered = [evaluate_day(d, t) for d, t in zip(filtered, targets)]
        avg_target_cpl = (sum(targets) / len(targets)) if targets else target_cpl
        # Сортировка по дате (новые сверху)
        def _sort_key(d):
            s = d.get("date") or "00.00.0000"
            parts = s.split(".")
            if len(parts) != 3:
                return (0, 0, 0)
            return (int(parts[2]), int(parts[1]), int(parts[0]))
        filtered.sort(key=_sort_key, reverse=True)

        st.caption(f"Показано дней: {len(filtered)} ({period_options.get(period_select, period_select)})")
        with st.expander("Как считается целевой CPL по каждому дню"):
            st.markdown("""
**Формула (CPL с органикой, как в калькуляторе):**  
Целевой CPL = Прибыль × (Корзина→Заказ % / 100) × (Выкуп % / 100) × (Рекл. корзин % / Рекл. заказов %)

Условие безубыточности: выручка = реклама; в пересчёте на общую корзину — та же логика, что и CPL с органикой (ad_cost / total_carts).

- **Прибыль** и **% выкупа** — из калькулятора.
- **Корзина→Заказ %**, **доля рекламных корзин**, **доля рекламных заказов** — по каждому дню из отчёта; для последних 7 дней при выключенном тумблере выше — из параметров калькулятора (заказы подгружаются с задержкой).

Итог: безубыточный уровень в руб./общую корзину. Сравниваем с CPL с органикой по дню. Эффективность = (Целевой CPL − Фактический CPL) / Целевой CPL × 100%.
""")
        with st.expander("📖 Почему целевой CPL считаем от прибыли и почему он не зависит от CTR"):
            st.markdown("""
**Что такое целевой (безубыточный) CPL**  
Целевой CPL — это ответ на вопрос: «Сколько максимум можно платить за одну корзину (в рублях), чтобы выйти в ноль?» То есть это **порог в рублях за корзину**, а не за клик или показ.

**Почему он считается от прибыли**  
С одной корзины мы в среднем получаем выручку только после того, как корзина превратилась в заказ (конверсия корзина→заказ), заказ выкупили (доля выкупа), и мы считаем это в деньгах с учётом доли рекламы. В деньгах это даёт **прибыль с одной корзины**. В точке безубыточности: расход на рекламу = прибыль от продаж; в пересчёте на одну корзину: сколько мы платим за корзину = сколько мы с неё зарабатываем. Поэтому целевой CPL = прибыль с одной корзины. В формулу входят только прибыль с единицы, корзина→заказ, выкуп и доли рекламы.

**Почему не зависит от CTR и конверсий до корзины**  
Целевой CPL отвечает только на вопрос: «Какой расход на одну корзину я ещё могу себе позволить?» Он не говорит, **как** мы получили эту корзину. CTR и клик→корзина определяют, сколько корзин мы получаем с показов и сколько мы за них **фактически платим** (фактический CPL). Целевой CPL задаёт **лимит**: «больше этой суммы за корзину платить нельзя».

**Пример**  
Допустим, с одной корзины мы в среднем зарабатываем 500 ₽ прибыли (с учётом конверсий). Тогда целевой CPL = 500 ₽. Как мы получили корзину — с CTR 0,1% или 1%, с CPM 100 или 500 — не меняет того, что с этой корзины мы по-прежнему получаем в среднем 500 ₽. Меняется только **фактический CPL**: при плохом CTR мы платим за корзину 800 ₽ (минус), при хорошем — 300 ₽ (плюс).
""")

        if filtered:
            kpis = aggregate_daily_kpis(filtered, avg_target_cpl)
            st.subheader("KPI: реклама и органика")
            trans_ratio = (kpis.get("totalTransitions", 0) / kpis.get("totalTransitionsAll", 1) * 100) if kpis.get("totalTransitionsAll") else 0
            total_orders_all_kpi = kpis.get("totalOrders", 0) or (kpis.get("totalOrdersRk", 0) + kpis.get("totalOrdersOrganic", 0))
            kpi_rows = [
                ("Показы", _fmt_num(kpis.get("totalShows", 0)), _fmt_num(kpis.get("totalShowsOrganic", 0)), f"РК {kpis.get('showsRatio', 0):.0f}% / Орг {kpis.get('organicRatio', 0):.0f}%"),
                ("Переходы", _fmt_num(kpis.get("totalTransitions", 0)), _fmt_num(kpis.get("totalTransitionsOrganic", 0)), f"РК {trans_ratio:.0f}% / Орг {100 - trans_ratio:.0f}%"),
                ("CTR (%)", _fmt_pct(kpis.get("avgCtrRk")), _fmt_pct(kpis.get("avgCtrOrganic")), "—"),
                ("CTR общий (%)", _fmt_pct(kpis.get("avgCtrTotal")), "—", "—"),
                ("Корзины", str(int(kpis.get("totalCartsRk", 0))), str(int(kpis.get("totalCartsOrganic", 0))), f"РК {kpis.get('cartsRatio', 0):.0f}% / Орг {100 - kpis.get('cartsRatio', 0):.0f}%"),
                ("Клик → Корзина (%)", _fmt_pct(kpis.get("avgClickToCartRk")), _fmt_pct(kpis.get("avgClickToCartOrganic")), "—"),
                ("Корзина → Заказ (%)", _fmt_pct(kpis.get("avgCartToOrderRk")), _fmt_pct(kpis.get("avgCartToOrderOrganic")), "—"),
                ("Заказы", str(int(kpis.get("totalOrdersRk", 0))), str(int(kpis.get("totalOrdersOrganic", 0))), f"РК {kpis.get('ordersRatio', 0):.0f}% / Орг {100 - kpis.get('ordersRatio', 0):.0f}%"),
                ("Бюджет", _fmt_cur(kpis.get("totalCost")), "—", f"ср. {_fmt_cur(kpis.get('avgCost'))} / день"),
                ("CPM", _fmt_cur(kpis.get("avgCpm")), "—", "—"),
                ("CPC", _fmt_cur(kpis.get("avgCpc")), "—", "—"),
                ("CPL РК", _fmt_cur(kpis.get("avgCplRk")), "—", "—"),
                ("CPL общий", _fmt_cur(kpis.get("avgCplTotal")), "—", "—"),
                ("Эфф.%", f"{int(round(kpis.get('totalEfficiency', 0)))}%", "—", "—"),
                ("Рейтинг (0–100)", f"{int(round(kpis.get('avgRatingScore', 0)))}", "—", "—"),
            ]
            kpi_df = pd.DataFrame(kpi_rows, columns=["Метрика", "Реклама (РК)", "Органика", "Соотношение"])
            st.table(kpi_df)

            # Окупаемость рекламы с учётом органики: заказы РК + органика, прибыль, ROMI
            st.subheader("Окупаемость рекламы")
            total_cost = kpis.get("totalCost") or 0
            total_orders_rk = kpis.get("totalOrdersRk") or 0
            total_orders_organic = kpis.get("totalOrdersOrganic") or 0
            total_orders_all = total_orders_rk + total_orders_organic
            sales_rk = total_orders_rk * (purchase_rate / 100.0)
            sales_organic = total_orders_organic * (purchase_rate / 100.0)
            net_profit_from_ads = sales_rk * profit
            net_profit_organic = sales_organic * profit
            net_profit_total = net_profit_from_ads + net_profit_organic
            net_after_ads = net_profit_total - total_cost
            romi_pct = (net_profit_from_ads / total_cost * 100) if total_cost > 0 else 0
            romi_with_organic = (net_profit_total / total_cost * 100) if total_cost > 0 else 0
            col_oa0a, col_oa0b, col_oa0c = st.columns(3)
            with col_oa0a:
                st.metric("Заказы РК", int(total_orders_rk))
            with col_oa0b:
                st.metric("Заказы органика", int(total_orders_organic))
            with col_oa0c:
                st.metric("Заказы всего", int(total_orders_all))
            st.caption("Продажи = Заказы × (Выкуп % / 100). Прибыль и % выкупа — из калькулятора.")
            col_oa1, col_oa2, col_oa3, col_oa4 = st.columns(4)
            with col_oa1:
                st.metric("Расходы на рекламу", _fmt_cur(total_cost))
            with col_oa2:
                st.metric("Прибыль от РК", _fmt_cur(net_profit_from_ads))
            with col_oa3:
                st.metric("Прибыль от органики", _fmt_cur(net_profit_organic))
            with col_oa4:
                st.metric("Прибыль всего", _fmt_cur(net_profit_total))
            col_oa5, col_oa6 = st.columns(2)
            with col_oa5:
                st.metric("Итого за вычетом рекламы", _fmt_cur(net_after_ads))
            with col_oa6:
                st.metric("ROMI (с учётом органики), %", f"{romi_with_organic:.1f}%")
            st.caption("**Окупаемость с учётом органики:** общая прибыль (РК + органика) минус расход на рекламу. ROMI > 100% — общий результат с рекламой в плюсе. Отдельно ROMI только по рекламе: " + f"{romi_pct:.1f}%.")
            # Окупаемость по марже: ДРРп < маржа % — реклама окупается
            margin_pct = st.number_input("Маржа, %", min_value=0.0, max_value=100.0, value=25.0, step=0.5, key="rk_margin_pct", help="При марже X% реклама окупается, если ДРР от продаж (ДРРп) < X%.")
            avg_drr_sale = (sum((d.get("drr2") or d.get("drr_rk") or 0) for d in filtered) / len(filtered)) if filtered else 0
            payback_by_margin = avg_drr_sale < margin_pct
            st.markdown(f"**Окупаемость по марже:** при марже **{margin_pct}%** реклама окупается, если ДРРп < {margin_pct}%. Средний ДРРп за период: **{avg_drr_sale:.1f}%**. {'✅ Реклама окупается по марже.' if payback_by_margin else '⚠️ Реклама не окупается по марже (ДРРп ≥ маржа).'}")

            st.subheader("Таблица по дням")
            margin_for_table = st.session_state.get("rk_margin_pct", 25.0) or 25.0
            if not isinstance(margin_for_table, (int, float)):
                margin_for_table = 25.0
            table_data = []
            for d in filtered:
                def _pct(x):
                    v = d.get(x, 0) or 0
                    return f"{v:.1f}%"
                cpl_total = d.get("cplTotal", 0) or 0
                eff_val = d.get("efficiency", 0) or 0
                drr_p = d.get("drr2") or d.get("drr_rk") or 0
                drr_eff = ((margin_for_table - drr_p) / margin_for_table * 100) if margin_for_table > 0 else 0
                total_shows_d = (d.get("shows", 0) or 0) + (d.get("organicShows", 0) or 0)
                shows_rk = d.get("shows", 0) or 0
                shows_org = d.get("organicShows", 0) or 0
                pct_shows_rk = (shows_rk / total_shows_d * 100) if total_shows_d > 0 else 0
                pct_shows_org = (shows_org / total_shows_d * 100) if total_shows_d > 0 else 0
                table_data.append({
                    "Дата": d.get("date"),
                    "Показы РК": int(shows_rk),
                    "Показы орг": int(shows_org),
                    "Показы РК %": f"{pct_shows_rk:.1f}%",
                    "Показы орг %": f"{pct_shows_org:.1f}%",
                    "Переходы РК": int(d.get("transitions", 0)),
                    "Переходы орг": int(d.get("organicTransitions", 0)),
                    "CTR РК %": _pct("ctrRk"),
                    "CTR орг %": _pct("ctrOrganic"),
                    "CTR общий %": _pct("ctrTotal"),
                    "Корзины РК": int(d.get("carts_rk", 0)),
                    "Корзины орг": int(d.get("organicCarts", 0)),
                    "Клик→Корз РК %": _pct("clickToCartRk"),
                    "Клик→Корз орг %": _pct("clickToCartOrganic"),
                    "Клик→Корз общая %": _pct("clickToCartTotal"),
                    "Корз→Заказ РК %": _pct("cartToOrderRk"),
                    "Корз→Заказ орг %": _pct("cartToOrderOrganic"),
                    "Корз→Заказ общая %": _pct("cartToOrderTotal"),
                    "Заказы РК": int(d.get("orders_rk", 0)),
                    "Заказы орг": int(d.get("organicOrders", 0)),
                    "Заказы общие": int(d.get("orders", 0)),
                    "CPM ₽": int(d.get("cpm", 0)),
                    "CPL РК ₽": (f"{(d.get('cpl_rk') or 0):.1f}".rstrip("0").rstrip(".") or "0"),
                    "CPL общий ₽": f"{cpl_total:.1f}",
                    "Целевой CPL ₽": f"{(d.get('targetCpl') or 0):.2f}",
                    "Эфф.% (CPL)": int(round(eff_val)),
                    "ДРРз %": f"{(d.get('drr1') or d.get('drr_rk') or 0):.1f}",
                    "ДРРп %": f"{(d.get('drr2') or d.get('drr_rk') or 0):.1f}",
                    "Эфф.% (ДРР)": int(round(drr_eff)),
                })
            df = pd.DataFrame(table_data)
            # Цвет в обоих столбцах эффективности: отрицательный — красный, положительный — зелёный
            def eff_color(v):
                if v is None or (isinstance(v, float) and (v != v)):
                    return ""
                x = float(v) if isinstance(v, (int, float)) else 0
                mag = min(100, abs(x))
                alpha = 0.2 + 0.6 * (mag / 100)
                if x < 0:
                    return f"background-color: rgba(239, 68, 68, {alpha:.2f});"
                return f"background-color: rgba(34, 197, 94, {alpha:.2f});"
            styled = df.style.applymap(eff_color, subset=["Эфф.% (CPL)", "Эфф.% (ДРР)"])
            st.dataframe(styled, use_container_width=True, hide_index=True)
            st.caption("**Эфф.% (CPL):** (Целевой CPL − CPL общий) / Целевой CPL × 100%. **Эфф.% (ДРР):** (Маржа − ДРРп) / Маржа × 100%; положительно, когда ДРРп < маржи.")

            # KPI за текущий и предыдущий день: заказы — оценка по конверсии или факт из отчёта
            use_orders_estimate = st.checkbox(
                "Использовать оценку заказов по конверсии (текущий/предыдущий день)",
                value=True, key="rk_use_orders_estimate",
                help="Включено: заказы считаются по конверсии корзина→заказ (заказы в отчёт WB попадают с задержкой). Выключено: показываются фактические заказы из отчёта."
            )
            cart_to_order_pct = st.number_input(
                "Конверсия корзина→заказ, % (для оценки заказов за текущий/предыдущий день)",
                min_value=1.0, max_value=100.0, value=20.0, step=0.5, key="rk_day_cart_to_order",
                help="Заказы в отчёт попадают с задержкой. Для текущего и вчерашнего дня заказы считаются по этой конверсии из корзин.",
                disabled=not use_orders_estimate
            )
            def _day_kpi_block(d, label, conv_pct, use_estimate, profit_val, purchase_rate_val):
                carts_total_d = d.get("carts_total") or 0
                carts_rk_d = d.get("carts_rk", 0) or 0
                carts_org_d = d.get("organicCarts") or max(0, carts_total_d - carts_rk_d)
                orders_d = d.get("orders") or 0
                orders_rk_d = d.get("orders_rk", 0) or 0
                orders_org_d = d.get("organicOrders") or max(0, orders_d - orders_rk_d)
                cpl_total_d = d.get("cplTotal") or 0
                if use_estimate:
                    ord_rk, ord_org, ord_total = carts_rk_d * (conv_pct / 100.0), carts_org_d * (conv_pct / 100.0), carts_total_d * (conv_pct / 100.0)
                    suf = " (оценка)"
                    # Целевой CPL и Эфф.% пересчитываем по заданной конверсии (одна конверсия для РК и орг. → доля заказов = доля корзин)
                    ad_carts_share_d = (carts_rk_d / carts_total_d * 100) if carts_total_d > 0 else 50.0
                    ad_share_d = ad_carts_share_d  # при одной конверсии
                    target_cpl_d = breakeven_cpl(profit_val, conv_pct, purchase_rate_val, ad_carts_share_d, ad_share_d)
                    eff_d = ((target_cpl_d - cpl_total_d) / target_cpl_d * 100) if target_cpl_d > 0 else 0
                    cart_to_order_rk_show = conv_pct
                else:
                    ord_rk, ord_org, ord_total = orders_rk_d, orders_org_d, orders_d
                    suf = ""
                    target_cpl_d = d.get("targetCpl") or 0
                    eff_d = d.get("efficiency") or 0
                    cart_to_order_rk_show = d.get("cartToOrderRk") or 0
                shows_rk_d = d.get("shows", 0) or 0
                shows_org_d = d.get("organicShows", 0) or 0
                total_shows_d = shows_rk_d + shows_org_d
                pct_rk_shows = (shows_rk_d / total_shows_d * 100) if total_shows_d > 0 else 0
                pct_org_shows = (shows_org_d / total_shows_d * 100) if total_shows_d > 0 else 0
                st.markdown(f"### {d.get('date', '—')} ({label})")
                r1a, r1b, r1c, r1d = st.columns(4)
                with r1a:
                    st.metric("Показы РК", int(d.get("shows", 0)))
                with r1b:
                    st.metric("Корзины РК", int(carts_rk_d))
                with r1c:
                    st.metric("Корзины органика", int(carts_org_d))
                with r1d:
                    st.metric("Корзины всего", int(carts_total_d))
                r2a, r2b = st.columns(2)
                with r2a:
                    st.metric("Реклама (показы), %", f"{pct_rk_shows:.1f}%")
                with r2b:
                    st.metric("Органика (показы), %", f"{pct_org_shows:.1f}%")
                r3a, r3b, r3c = st.columns(3)
                with r3a:
                    st.metric(f"Заказы РК{suf}", f"{ord_rk:.1f}" if use_estimate else int(ord_rk))
                with r3b:
                    st.metric(f"Заказы органика{suf}", f"{ord_org:.1f}" if use_estimate else int(ord_org))
                with r3c:
                    st.metric(f"Заказы всего{suf}", f"{ord_total:.1f}" if use_estimate else int(ord_total))
                r4a, r4b = st.columns(2)
                with r4a:
                    st.metric("CPL общий", _fmt_cur(cpl_total_d))
                    st.metric("Целевой CPL", f"{target_cpl_d:.2f} ₽")
                with r4b:
                    st.metric("Эфф.% (CPL)", f"{int(round(eff_d))}%")
                r5a, r5b = st.columns(2)
                with r5a:
                    st.metric("CPM", _fmt_cur(d.get("cpm", 0)))
                with r5b:
                    st.metric("CTR (общий)", f"{(d.get('ctrTotal') or 0):.2f}%")
                r6a, r6b, r6c, r6d = st.columns(4)
                with r6a:
                    st.metric("Клик→Корзина (общ.)", f"{(d.get('clickToCartTotal') or 0):.1f}%")
                with r6b:
                    st.metric("Корзина→Заказ (задана)", f"{conv_pct:.1f}%")
                with r6c:
                    st.metric("Корзина→Заказ (РК)", f"{cart_to_order_rk_show:.1f}%")
                with r6d:
                    st.metric("Корзина→Заказ (орг.)", f"{(d.get('cartToOrderOrganic') or 0):.1f}%")
                st.caption("При включённой оценке: задана конверсия используется для заказов, Целевой CPL и Эфф.% пересчитываются по ней; РК и орг. из отчёта — при выключенной оценке.")
            if len(filtered) >= 1:
                st.subheader("KPI за текущий и предыдущий день")
                st.caption("При включённой оценке заказы считаются по конверсии корзина→заказ (задержка в отчёте WB). Снимите галочку — показываются фактические заказы из отчёта.")
                cols_day = st.columns(2 if len(filtered) >= 2 else 1)
                with cols_day[0]:
                    _day_kpi_block(filtered[0], "текущий", cart_to_order_pct, use_orders_estimate, profit, purchase_rate)
                if len(filtered) >= 2:
                    with cols_day[1]:
                        _day_kpi_block(filtered[1], "предыдущий", cart_to_order_pct, use_orders_estimate, profit, purchase_rate)

            recs_period = get_recommendations(filtered, avg_target_cpl, profit=profit, purchase_rate=purchase_rate)
            rec_today = []
            rec_yesterday = []
            if len(filtered) >= 2:
                day_now = filtered[0]
                day_prev = filtered[1]
                cpl_now = day_now.get("cplTotal") or 0
                cpl_prev = day_prev.get("cplTotal") or 0
                eff_now = day_now.get("efficiency") or 0
                eff_prev = day_prev.get("efficiency") or 0
                if cpl_prev > 0 and cpl_now < cpl_prev:
                    rec_today.append(f"CPL ({cpl_now:.1f} ₽) ниже вчерашнего ({cpl_prev:.1f} ₽) — эффективность выросла.")
                elif cpl_prev > 0 and cpl_now > cpl_prev:
                    rec_today.append(f"CPL ({cpl_now:.1f} ₽) выше вчерашнего ({cpl_prev:.1f} ₽) — стоит обратить внимание.")
                if eff_now > eff_prev:
                    rec_today.append(f"Эфф.% (CPL) сегодня ({int(round(eff_now))}%) выше, чем вчера ({int(round(eff_prev))}%).")
                elif eff_now < eff_prev:
                    rec_today.append(f"Эфф.% (CPL) сегодня ({int(round(eff_now))}%) ниже, чем вчера ({int(round(eff_prev))}%).")
                # Вчера: цифры + вывод
                rec_yesterday.append(f"Показатели: CPL общий {cpl_prev:.1f} ₽, целевой {day_prev.get('targetCpl', 0):.2f} ₽, Эфф.% {int(round(eff_prev))}%, заказов {day_prev.get('orders', 0)} (РК: {day_prev.get('orders_rk', 0)}, органика: {day_prev.get('organicOrders', 0)}).")
                if eff_prev > 0:
                    rec_yesterday.append("**Вывод:** реклама вчера была эффективной — CPL ниже целевого, можно сохранять или умеренно увеличивать бюджет.")
                elif eff_prev < 0:
                    rec_yesterday.append("**Вывод:** реклама вчера была неэффективной — CPL выше целевого; стоит снизить ставки или пересмотреть таргетинг.")
                else:
                    rec_yesterday.append("**Вывод:** CPL вчера на уровне целевого — реклама на границе безубыточности.")
            st.subheader("💡 Рекомендации")
            st.markdown("**Сегодня**")
            if rec_today:
                for r in rec_today:
                    st.markdown(f"- {r}")
            else:
                st.caption("Нет рекомендаций по сравнению с вчера (нужно минимум 2 дня в выборке).")
            st.markdown("**Вчера**")
            if rec_yesterday:
                for r in rec_yesterday:
                    st.markdown(f"- {r}")
            else:
                st.caption("Нет данных за вчера.")
            st.markdown("**Период**")
            if recs_period:
                for r in recs_period:
                    st.markdown(f"- {r}")
            else:
                st.caption("Нет общих рекомендаций по периоду.")

            # Сравнение типов рекламы (ниже рекомендаций)
            dates_in_period = [d["date"] for d in filtered]
            by_type = aggregate_by_type(details_all, dates_in_period=dates_in_period)
            st.subheader("Сравнение типов рекламы")
            type_cols = st.columns(max(len(by_type), 1))
            for idx, (tkey, t) in enumerate(by_type.items()):
                with type_cols[idx]:
                    name = "Поиск" if tkey == "search" else "Полки" if tkey == "shelf" else "Каталог" if tkey == "catalog" else tkey
                    st.markdown(f"**{name}**")
                    st.caption(f"Показы: {_fmt_num(t['shows'])}")
                    st.caption(f"Затраты: {_fmt_cur(t['cost'])}")
                    st.caption(f"CPM: {_fmt_cur(t['cpm'])} · CPC: {_fmt_cur(t['cpc'])}")
                    st.caption(f"Корзины: {int(t['carts'])} · CPL: {_fmt_cur(t['cpl'])} · CTR: {_fmt_pct(t['ctr'])}")

            # Лучшие / худшие дни по CPL — внизу, свёрнуты
            valid_cpl = [d for d in filtered if (d.get("cplTotal") or 0) > 0]
            if valid_cpl:
                best = sorted(valid_cpl, key=lambda x: x["cplTotal"])[:5]
                worst = sorted(valid_cpl, key=lambda x: x["cplTotal"], reverse=True)[:5]
                with st.expander("🏆 Лучшие и ⚠️ Худшие дни по CPL", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**🏆 Лучшие дни по CPL**")
                        for d in best:
                            st.text(f"{d['date']} — CPL {d['cplTotal']:.1f} ₽, заказов {d.get('orders', 0)}, {d.get('rating', '')}")
                    with c2:
                        st.markdown("**⚠️ Худшие дни по CPL**")
                        for d in worst:
                            st.text(f"{d['date']} — CPL {d['cplTotal']:.1f} ₽, заказов {d.get('orders', 0)}, {d.get('rating', '')}")

# ========== Вкладка: Калькулятор метрик ==========
with tab_calc:
    st.header("Калькулятор метрик Wildberries")
    st.caption("Безубыточный CPL с органикой = Прибыль × (Корзина→Заказ) × (Выкуп) × (Рекл. корзин % / Рекл. заказов %). Сравниваем с CPL с органикой.")
    prefill = st.session_state.get("rk_prefill") or {}

    # Выбор даты: подставить в калькулятор данные по конверсиям, CPM, CTR за выбранный день
    if st.session_state.rk_days:
        dates = [d.get("date") for d in st.session_state.rk_days if d.get("date")]
        if dates:
            col_dt, col_btn_agg, col_btn_day = st.columns([2, 1, 1])
            with col_dt:
                selected_date = st.selectbox("Выберите дату для подстановки в текущий период", options=dates, key="calc_date_select", index=min(len(dates) - 1, 0))
            with col_btn_agg:
                if st.button("📥 Вся выгрузка (средние)", key="btn_prefill"):
                    agg = aggregate_for_calculator(st.session_state.rk_days)
                    if agg:
                        st.session_state.rk_prefill = agg
                        for k, v in agg.items():
                            st.session_state["rk_calc_" + k] = v
                        st.session_state["rk_calc_ctr_now"] = agg.get("ctr")
                        st.session_state["rk_calc_click_to_cart_now"] = agg.get("click_to_cart")
                        st.session_state["rk_calc_cart_to_order_now"] = agg.get("cart_to_order")
                        st.session_state["cpm"] = int(agg.get("cpm", 0)) or 320
                        st.session_state["organic_share"] = int(round(agg.get("organic_share", 50)))
                        st.session_state["organic_carts_share"] = int(round(agg.get("organic_carts_share", 50)))
                        st.session_state["ctr_now"] = float(agg.get("ctr", 0)) or 6.0
                        st.session_state["click_to_cart_now"] = float(agg.get("click_to_cart", 0)) or 6.0
                        st.session_state["cart_to_order_now"] = float(agg.get("cart_to_order", 0)) or 15.0
                        st.rerun()
            with col_btn_day:
                if st.button("📅 Данные по выбранной дате", key="btn_prefill_day"):
                    day = next((d for d in st.session_state.rk_days if d.get("date") == selected_date), None)
                    if day:
                        prefill_day = day_for_calculator(day)
                        st.session_state.rk_prefill = prefill_day
                        for k, v in prefill_day.items():
                            st.session_state["rk_calc_" + k] = v
                        st.session_state["rk_calc_ctr_now"] = prefill_day.get("ctr")
                        st.session_state["rk_calc_click_to_cart_now"] = prefill_day.get("click_to_cart")
                        st.session_state["rk_calc_cart_to_order_now"] = prefill_day.get("cart_to_order")
                        # Streamlit хранит значение виджета в session_state[key]; без этого поля не обновляются
                        st.session_state["cpm"] = int(prefill_day.get("cpm", 0)) or 320
                        st.session_state["organic_share"] = int(round(prefill_day.get("organic_share", 50)))
                        st.session_state["organic_carts_share"] = int(round(prefill_day.get("organic_carts_share", 50)))
                        st.session_state["ctr_now"] = float(prefill_day.get("ctr", 0)) or 6.0
                        st.session_state["click_to_cart_now"] = float(prefill_day.get("click_to_cart", 0)) or 6.0
                        st.session_state["cart_to_order_now"] = float(prefill_day.get("cart_to_order", 0)) or 15.0
                        st.rerun()

    def _d(key, prefill_key, default):
        v = st.session_state.get("rk_calc_" + key)
        if v is not None:
            return int(v) if isinstance(default, int) else float(v)
        if prefill_key is None:
            return default
        p = prefill.get(prefill_key, default)
        return int(p) if isinstance(default, int) else float(p)

    # Базовые настройки
    with st.expander("⚙️ Базовые настройки", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            cpm = st.number_input("CPM (₽ за 1000 показов)", min_value=1, value=_d("cpm", "cpm", 320), step=1, key="cpm")
        with c2:
            purchase_rate = st.number_input("Процент выкупа (%)", min_value=1, max_value=100, value=_d("purchase_rate", None, 20), step=1, key="purchase_rate")
        with c3:
            impressions = st.number_input("Кол-во показов для расчёта", min_value=100, value=_d("impressions", None, 1000), step=100, key="impressions")

    with st.expander("🌱 Распределение трафика", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            organic_share = st.number_input("Органические продажи (%)", min_value=0, max_value=100, value=_d("organic_share", "organic_share", 50), step=1, key="organic_share")
            organic_carts_share = st.number_input("Органические корзины (%)", min_value=0, max_value=100, value=_d("organic_carts_share", "organic_carts_share", 50), step=1, key="organic_carts_share")
        ad_share = 100 - organic_share
        ad_carts_share = 100 - organic_carts_share
        st.caption(f"Рекламные продажи: {ad_share}% · Рекламные корзины: {ad_carts_share}%")

    with st.expander("❄️ Текущий период", expanded=True):
        pc1, pc2 = st.columns(2)
        with pc1:
            price_now = st.number_input("Цена товара (₽)", min_value=1, value=_d("price_now", None, 6200), step=100, key="price_now")
            duration_now = st.number_input("Длительность периода (дней)", min_value=1, value=_d("duration_now", None, 70), step=1, key="duration_now")
        with pc2:
            ctr_now = st.number_input("CTR (%)", min_value=0.1, value=_d("ctr_now", "ctr", 6.0), step=0.1, key="ctr_now")
            click_to_cart_now = st.number_input("Клик → Корзина (%)", min_value=0.1, value=_d("click_to_cart_now", "click_to_cart", 6.0), step=0.1, key="click_to_cart_now")
        cart_to_order_now = st.number_input("Корзина → Заказ (%)", min_value=0.1, value=_d("cart_to_order_now", "cart_to_order", 15.0), step=0.1, key="cart_to_order_now")

    with st.expander("☀️ В сезон (прогноз)", expanded=True):
        ps1, ps2 = st.columns(2)
        with ps1:
            price_season = st.number_input("Цена товара (₽)", min_value=1, value=_d("price_season", None, 7500), step=100, key="price_season")
            duration_season = st.number_input("Длительность сезона (дней)", min_value=1, value=_d("duration_season", None, 60), step=1, key="duration_season")
        with ps2:
            ctr_season = st.number_input("CTR (%)", min_value=0.1, value=_d("ctr_season", None, 8.0), step=0.1, key="ctr_season")
            click_to_cart_season = st.number_input("Клик → Корзина (%)", min_value=0.1, value=_d("click_to_cart_season", None, 9.0), step=0.1, key="click_to_cart_season")
        cart_to_order_season = st.number_input("Корзина → Заказ (%)", min_value=0.1, value=_d("cart_to_order_season", None, 35.0), step=0.1, key="cart_to_order_season")

    profit_now = st.number_input("❄️ Чистая прибыль с единицы (текущий период, до вычета рекламы) ₽", min_value=0, value=_d("profit_now", None, 600), step=100, key="profit_now")
    profit_season = st.number_input("☀️ Чистая прибыль с единицы (сезон) ₽", min_value=0, value=_d("profit_season", None, 1800), step=100, key="profit_season")

    if cpm > 0 and impressions > 0:
        now = calculate_period(cpm, impressions, ctr_now, click_to_cart_now, cart_to_order_now, price_now, purchase_rate, ad_share, ad_carts_share)
        season = calculate_period(cpm, impressions, ctr_season, click_to_cart_season, cart_to_order_season, price_season, purchase_rate, ad_share, ad_carts_share)
        ad_cost = cpm * (impressions / 1000.0)
        now_organic = calculate_organic(now["purchases"], price_now, profit_now, ad_share, ad_cost, now)
        season_organic = calculate_organic(season["purchases"], price_season, profit_season, ad_share, ad_cost, season)
        be_now = breakeven_cpl(profit_now, cart_to_order_now, purchase_rate, ad_carts_share, ad_share)
        be_season = breakeven_cpl(profit_season, cart_to_order_season, purchase_rate, ad_carts_share, ad_share)
        st.session_state["rk_breakeven_cpl"] = round(be_now)
        st.session_state["rk_calc_profit_now"] = profit_now
        st.session_state["rk_calc_purchase_rate"] = purchase_rate
        st.session_state["rk_calc_ad_carts_share"] = ad_carts_share
        calc_state = {
            "cpm": cpm, "purchase_rate": purchase_rate, "impressions": impressions,
            "organic_share": organic_share, "organic_carts_share": organic_carts_share, "ad_carts_share": ad_carts_share,
            "price_now": price_now, "duration_now": duration_now,
            "ctr_now": ctr_now, "click_to_cart_now": click_to_cart_now, "cart_to_order_now": cart_to_order_now,
            "price_season": price_season, "duration_season": duration_season,
            "ctr_season": ctr_season, "click_to_cart_season": click_to_cart_season, "cart_to_order_season": cart_to_order_season,
            "profit_now": profit_now, "profit_season": profit_season,
        }
        for k, v in calc_state.items():
            st.session_state["rk_calc_" + k] = v
        try:
            os.makedirs(UPLOADS_DIR, exist_ok=True)
            with open(CALC_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(calc_state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ❄️ Текущий период")
            st.metric("CPC (стоимость клика)", _fmt_cur(now["cpc"]))
            st.metric("Кликов с показов", _fmt_num(now["clicks"], 1))
            st.metric("Корзин", _fmt_num(now["carts"], 1))
            st.metric("CPL", _fmt_cur(now["cpl"]))
            be_cpl_col1, cpl_org_col1 = st.columns(2)
            with be_cpl_col1:
                st.metric("💰 Безубыточный CPL", _fmt_cur2(be_now))
            with cpl_org_col1:
                st.metric("CPL с органикой", _fmt_cur(now["cplOrganic"]))
            st.caption("Сравнение: если CPL с органикой ниже безубыточного — в плюсе, выше — в минусе.")
            st.metric("Заказов (реклама)", _fmt_num(now["orders"], 2))
            st.metric("CPO", _fmt_cur(now["cpo"]))
            st.metric("ДРР от заказа", _fmt_pct(now["drrOrder"]))
            st.metric("Выкупов (реклама)", _fmt_num(now["purchases"], 2))
            st.metric("Стоимость выкупа (реклама)", _fmt_cur(now["purchaseCost"]))
            st.metric("ДРР от продажи (реклама)", _fmt_pct(now["drrSale"]))
            st.metric("Всего выкупов (с органикой)", _fmt_num(now_organic["totalPurchases"], 2))
            st.metric("Затраты на рекламу", _fmt_cur(now_organic["adCost"]))
            st.metric("Стоимость выкупа (с органикой)", _fmt_cur(now_organic["purchaseTotalCost"]))
            st.metric("ДРР от продажи (с органикой)", _fmt_pct(now_organic["drrSaleOrganic"]))
            st.metric("ROMI", _fmt_pct(now_organic["romi"]))
            st.metric("Чистая прибыль на единицу", _fmt_cur(now_organic["netProfitPerUnit"]))
        with col2:
            st.markdown("### ☀️ В сезон")
            st.metric("CPC (стоимость клика)", _fmt_cur(season["cpc"]))
            st.metric("Кликов с показов", _fmt_num(season["clicks"], 1))
            st.metric("Корзин", _fmt_num(season["carts"], 1))
            st.metric("CPL", _fmt_cur(season["cpl"]))
            be_cpl_col2, cpl_org_col2 = st.columns(2)
            with be_cpl_col2:
                st.metric("💰 Безубыточный CPL", _fmt_cur2(be_season))
            with cpl_org_col2:
                st.metric("CPL с органикой", _fmt_cur(season["cplOrganic"]))
            st.caption("Сравнение: если CPL с органикой ниже безубыточного — в плюсе.")
            st.metric("Заказов (реклама)", _fmt_num(season["orders"], 2))
            st.metric("CPO", _fmt_cur(season["cpo"]))
            st.metric("ДРР от заказа", _fmt_pct(season["drrOrder"]))
            st.metric("Выкупов (реклама)", _fmt_num(season["purchases"], 2))
            st.metric("Стоимость выкупа (реклама)", _fmt_cur(season["purchaseCost"]))
            st.metric("ДРР от продажи (реклама)", _fmt_pct(season["drrSale"]))
            st.metric("Всего выкупов (с органикой)", _fmt_num(season_organic["totalPurchases"], 2))
            st.metric("Затраты на рекламу", _fmt_cur(season_organic["adCost"]))
            st.metric("Стоимость выкупа (с органикой)", _fmt_cur(season_organic["purchaseTotalCost"]))
            st.metric("ДРР от продажи (с органикой)", _fmt_pct(season_organic["drrSaleOrganic"]))
            st.metric("ROMI", _fmt_pct(season_organic["romi"]))
            st.metric("Чистая прибыль на единицу", _fmt_cur(season_organic["netProfitPerUnit"]))

        with st.expander("🔍 Проверка формулы безубыточного CPL"):
            st.markdown("**Формула (CPL с органикой):** Безубыточный CPL = Прибыль × (Корзина→Заказ % / 100) × (Выкуп % / 100) × (Рекл. корзин % / Рекл. заказов %).")
            st.latex(r"\text{Безубыточный CPL} = \text{Прибыль} \times \frac{\text{Корз}\to\text{Заказ \%}}{100} \times \frac{\text{Выкуп \%}}{100} \times \frac{\text{Рекл. корзин \%}}{\text{Рекл. заказов \%}}")
            step1 = profit_now * (cart_to_order_now / 100.0)
            step2 = step1 * (purchase_rate / 100.0)
            ratio = (ad_carts_share / ad_share) if ad_share > 0 else 1.0
            step3 = step2 * ratio
            st.markdown(f"**Текущий период (по шагам):**")
            st.markdown(f"1. Прибыль × Корзина→Заказ % = {profit_now:.0f} × {cart_to_order_now}% = **{step1:.2f}** ₽")
            st.markdown(f"2. × Выкуп % = {step1:.2f} × {purchase_rate}% = **{step2:.2f}** ₽")
            st.markdown(f"3. × (Рекл. корзин % / Рекл. заказов %) = {step2:.2f} × ({ad_carts_share}% / {ad_share}%) = **{step3:.2f}** ₽ → **{be_now:.2f}** ₽")
            st.markdown(f"**Итог:** Безубыточный CPL = **{be_now:.2f}** ₽. CPL с органикой = **{now['cplOrganic']:.2f}** ₽ → {'✅ ниже, в плюсе' if now['cplOrganic'] < be_now else '⚠️ выше, в минусе'}.")

        # Сохраняем для планировщика
        st.session_state._calc_now = now
        st.session_state._calc_season = season
        st.session_state._cpm = cpm
        st.session_state._duration_now = duration_now
        st.session_state._duration_season = duration_season
        st.session_state._ad_share = ad_share
        st.session_state._ad_carts_share = ad_carts_share
        st.session_state._cart_to_order_now = cart_to_order_now
        st.session_state._cart_to_order_season = cart_to_order_season
    else:
        st.warning("Заполните CPM и кол-во показов.")

# ========== Вкладка: Планировщик продаж ==========
with tab_planner:
    st.header("Планировщик продаж")
    st.caption("Цель: сколько товаров нужно ПРОДАТЬ (выкупить). Расчёт заказов, корзин, показов и бюджета.")
    target_sales = st.number_input("Сколько товаров нужно ПРОДАТЬ (выкупить)", min_value=1, value=100, step=1, key="target_sales")
    if st.session_state.get("_calc_now") and st.session_state.get("_calc_season"):
        now = st.session_state._calc_now
        season = st.session_state._calc_season
        pl = planner(
            target_sales=target_sales,
            purchase_rate_pct=purchase_rate,
            ad_share_pct=ad_share,
            ad_carts_share_pct=ad_carts_share,
            cart_to_order_now_pct=cart_to_order_now,
            cart_to_order_season_pct=cart_to_order_season,
            total_orders_per_1000_now=now["totalOrdersPer1000"],
            total_orders_per_1000_season=season["totalOrdersPer1000"],
            cpm=st.session_state._cpm,
            duration_now=st.session_state._duration_now,
            duration_season=st.session_state._duration_season,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### ❄️ Текущий период")
            st.metric("Нужно рекламных показов всего", _fmt_num(pl["impressionsNeededNow"], 0))
            st.metric("Бюджет всего", _fmt_cur(pl["budgetNow"]))
            st.metric("Тратить в день на рекламу", _fmt_cur(pl["dailyBudgetNow"]))
            st.metric("ЗАКАЗОВ в день (нужно)", _fmt_num(pl["dailyOrdersNow"], 1))
            st.metric("Рекламных заказов в день", _fmt_num(pl["dailyAdOrdersNow"], 1))
            st.metric("Органических заказов в день", _fmt_num(pl["dailyOrganicOrdersNow"], 1))
            st.metric("КОРЗИН в день всего", _fmt_num(pl["dailyCartsNow"], 1))
            st.metric("Показов в день", _fmt_num(pl["impressionsPerDayNow"], 0))
            st.metric("Показов в неделю", _fmt_num(pl["impressionsPerWeekNow"], 0))
        with c2:
            st.markdown("### ☀️ В сезон")
            st.metric("Нужно рекламных показов всего", _fmt_num(pl["impressionsNeededSeason"], 0))
            st.metric("Бюджет всего", _fmt_cur(pl["budgetSeason"]))
            st.metric("Тратить в день на рекламу", _fmt_cur(pl["dailyBudgetSeason"]))
            st.metric("ЗАКАЗОВ в день (нужно)", _fmt_num(pl["dailyOrdersSeason"], 1))
            st.metric("Рекламных заказов в день", _fmt_num(pl["dailyAdOrdersSeason"], 1))
            st.metric("Органических заказов в день", _fmt_num(pl["dailyOrganicOrdersSeason"], 1))
            st.metric("КОРЗИН в день всего", _fmt_num(pl["dailyCartsSeason"], 1))
            st.metric("Показов в день", _fmt_num(pl["impressionsPerDaySeason"], 0))
            st.metric("Показов в неделю", _fmt_num(pl["impressionsPerWeekSeason"], 0))
        st.info(f"Для продажи {int(target_sales)} товаров нужно получить {int(pl['targetOrders'])} заказов (при выкупе {purchase_rate}%).")
    else:
        st.info("Сначала откройте вкладку «Калькулятор метрик» и введите параметры (CPM, конверсии, период). Тогда здесь появятся расчёты планировщика.")
