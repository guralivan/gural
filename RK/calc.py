# -*- coding: utf-8 -*-
"""
Общая логика расчётов для приложения эффективной рекламы маркетплейса (RK).
Парсинг Excel, формулы калькулятора, оценка по дням. Без UI.
"""
from __future__ import division
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

try:
    import pandas as pd
except ImportError:
    pd = None

# Индексы столбцов в отчёте WB "По дням" (как в Аналитка рекламы по дням.html)
COLUMN_INDICES = {
    "date": 0,
    "shows": 1,
    "cpm": 2,
    "transitions": 3,
    "ctr": 4,
    "cpc": 5,
    "cost": 6,
    "carts_rk": 7,
    "cpl_rk": 8,
    "orders_rk": 9,
    "cpo": 10,
    "orders_rk2": 11,
    "cro_rk": 12,
    "drr_rk": 13,
    "totalViews": 14,
    "totalTransitions": 15,
    "totalCtr": 16,
    "totalCarts": 17,
    "totalOrders": 18,
    "totalRevenue": 19,
    "avgPrice": 20,
    "drr1": 21,
    "drr2": 22,
    "cps": 23,
}


def _parse_number(value) -> float:
    if value is None or (isinstance(value, float) and (value != value)):  # NaN
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).replace(",", ".").replace(" ", "")
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_excel_date(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        try:
            # Excel serial date
            d = datetime(1899, 12, 30) + timedelta(days=int(value))
            return d.strftime("%d.%m.%Y")
        except Exception:
            return str(value)
    s = str(value).strip()
    if "/" in s:
        s = s.split("/")[0].strip()
    if " " in s:
        s = s.split(" ")[0].strip()
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", s)
    if m:
        d, mo, y = m.groups()
        d = d.zfill(2)
        mo = mo.zfill(2)
        if len(y) == 2:
            y = "20" + y
        return f"{d}.{mo}.{y}"
    return s


def parse_excel(file_or_path) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict]]]:
    """
    Парсит Excel-отчёт WB с разделом «По дням».
    :return: (список дней [{"date", "shows", "cpm", ...}], details по дате -> список по типам рекламы)
    """
    if pd is None:
        raise ImportError("pandas required for parse_excel")
    if hasattr(file_or_path, "read"):
        df_raw = pd.read_excel(file_or_path, header=None)
    else:
        df_raw = pd.read_excel(file_or_path, header=None)
    rows = df_raw.values.tolist()

    start_row = -1
    for i, row in enumerate(rows):
        if row is None or len(row) == 0:
            continue
        cell = str(row[0]).strip() if row[0] is not None else ""
        if "По дням" in cell:
            start_row = i + 1
            break
    if start_row == -1:
        raise ValueError('Не найден раздел "По дням"')

    ci = COLUMN_INDICES
    parsed = []
    details = {}

    i = start_row
    while i < len(rows):
        row = rows[i]
        if row is None or len(row) == 0:
            i += 1
            continue
        cell_value = str(row[0]).strip() if row[0] is not None else ""
        if cell_value in ("Графики", "За период", "По дням"):
            i += 1
            continue
        if re.search(r"\d{1,2}\.\d{1,2}\.\d{2,4}", cell_value):
            date_str = _parse_excel_date(row[0])
            def get_col(idx):
                if idx < len(row) and row[idx] is not None:
                    return _parse_number(row[idx])
                return 0.0
            day_data = {
                "date": date_str,
                "shows": get_col(ci["shows"]),
                "totalShows": get_col(ci["totalViews"]),
                "cpm": get_col(ci["cpm"]),
                "cpc": get_col(ci["cpc"]),
                "cost": get_col(ci["cost"]),
                "carts_rk": get_col(ci["carts_rk"]),
                "carts_total": get_col(ci["totalCarts"]),
                "orders_rk": get_col(ci["orders_rk"]),
                "orders": get_col(ci["totalOrders"]),
                "cpl_rk": get_col(ci["cpl_rk"]),
                "transitions": get_col(ci["transitions"]),
                "totalTransitions": get_col(ci["totalTransitions"]),
                "drr_rk": get_col(ci["drr_rk"]),
                "drr1": get_col(ci["drr1"]),
                "drr2": get_col(ci["drr2"]),
            }
            parsed.append(day_data)

            day_details = []
            j = i + 1
            while j < len(rows):
                next_row = rows[j]
                if next_row is None or len(next_row) == 0:
                    j += 1
                    continue
                next_val = str(next_row[0]).strip() if next_row[0] is not None else ""
                if re.search(r"\d{1,2}\.\d{1,2}\.\d{2,4}", next_val):
                    break
                if next_val.startswith("поиск") or next_val.startswith("полки") or next_val.startswith("каталог"):
                    share = 0
                    share_m = re.search(r"\|\s*(\d+)%|(\d+)%", next_val)
                    if share_m:
                        share = int(share_m.group(1) or share_m.group(2) or 0)
                    typ = next_val.split(" ")[0].replace("|", "").strip()
                    day_details.append({
                        "type": typ,
                        "share": share,
                        "shows": _parse_number(next_row[1]) if len(next_row) > 1 else 0,
                        "cpm": _parse_number(next_row[2]) if len(next_row) > 2 else 0,
                        "transitions": _parse_number(next_row[3]) if len(next_row) > 3 else 0,
                        "ctr": _parse_number(next_row[4]) if len(next_row) > 4 else 0,
                        "cpc": _parse_number(next_row[5]) if len(next_row) > 5 else 0,
                        "cost": _parse_number(next_row[6]) if len(next_row) > 6 else 0,
                        "carts": _parse_number(next_row[7]) if len(next_row) > 7 else 0,
                        "cpl": _parse_number(next_row[8]) if len(next_row) > 8 else 0,
                        "orders": _parse_number(next_row[9]) if len(next_row) > 9 else 0,
                        "cpo": _parse_number(next_row[10]) if len(next_row) > 10 else 0,
                    })
                j += 1
            if day_details:
                details[date_str] = day_details
            i = j
        else:
            i += 1

    return parsed, details


# --- Формулы калькулятора (из Расчёт рекламы.html) ---

def calculate_period(
    cpm: float,
    impressions: float,
    ctr_pct: float,
    click_to_cart_pct: float,
    cart_to_order_pct: float,
    price: float,
    purchase_rate_pct: float,
    ad_share_pct: float,
    ad_carts_share_pct: float,
) -> Dict[str, float]:
    """Расчёт метрик для одного периода (сейчас или сезон)."""
    if cpm <= 0 or impressions <= 0:
        return _empty_period()
    ctr = ctr_pct / 100.0
    click_to_cart = click_to_cart_pct / 100.0
    cart_to_order = cart_to_order_pct / 100.0
    purchase_rate = purchase_rate_pct / 100.0
    ad_share = ad_share_pct / 100.0
    ad_carts_share = ad_carts_share_pct / 100.0

    # CPC = стоимость клика = Затраты / Клики = (CPM * impressions/1000) / (impressions * ctr) = CPM / (1000 * ctr)
    cpc = (cpm / (ctr * 1000.0)) if ctr > 0 else 0
    clicks = impressions * ctr
    carts = clicks * click_to_cart if click_to_cart else 0
    cpl = (cpm * (impressions / 1000.0) / carts) if carts > 0 else 0
    orders = carts * cart_to_order if cart_to_order else 0
    cpo = (cpm * (impressions / 1000.0) / orders) if orders > 0 else 0
    purchases = orders * purchase_rate
    purchase_cost = (cpm * (impressions / 1000.0) / purchases) if purchases > 0 else 0
    drr_order = (cpo / price * 100) if price > 0 else 0
    drr_sale = (purchase_cost / price * 100) if price > 0 else 0
    total_orders_per_1000 = (orders / ad_share) if ad_share > 0 else 0
    total_carts = (carts / ad_carts_share) if ad_carts_share > 0 else 0
    cpl_organic = (cpm * (impressions / 1000.0) / total_carts) if total_carts > 0 else 0

    return {
        "cpc": cpc,
        "clicks": clicks,
        "carts": carts,
        "cpl": cpl,
        "orders": orders,
        "cpo": cpo,
        "purchases": purchases,
        "purchaseCost": purchase_cost,
        "drrOrder": drr_order,
        "drrSale": drr_sale,
        "totalOrdersPer1000": total_orders_per_1000,
        "cplOrganic": cpl_organic,
    }


def _empty_period() -> Dict[str, float]:
    return {
        "cpc": 0, "clicks": 0, "carts": 0, "cpl": 0, "orders": 0, "cpo": 0,
        "purchases": 0, "purchaseCost": 0, "drrOrder": 0, "drrSale": 0,
        "totalOrdersPer1000": 0, "cplOrganic": 0,
    }


def breakeven_cpl(
    profit: float,
    cart_to_order_pct: float,
    purchase_rate_pct: float,
    ad_carts_share_pct: float = 50.0,
    ad_share_pct: float = 50.0,
) -> float:
    """
    Безубыточный CPL с органикой: руб/общая корзина (как CPL с органикой = ad_cost/total_carts).
    Условие: выручка = ad_cost => (total_purchases/total_carts)*profit = ad_cost/total_carts.
    total_purchases/total_carts = cart_to_order * purchase_rate * (ad_carts_share/ad_share).
    Итого: breakeven = profit * (cart_to_order/100) * (purchase_rate/100) * (ad_carts_share_pct/ad_share_pct).
    """
    if ad_share_pct <= 0:
        return 0.0
    return (
        profit
        * (cart_to_order_pct / 100.0)
        * (purchase_rate_pct / 100.0)
        * (ad_carts_share_pct / ad_share_pct)
    )


def calculate_organic(
    period_purchases: float,
    price: float,
    profit: float,
    ad_share_pct: float,
    ad_cost: float,
    period_data: Dict[str, float],
) -> Dict[str, float]:
    """Расчёт с учётом органики: всего выкупов, ROMI, стоимость выкупа с органикой, чистая прибыль на единицу."""
    ad_share = ad_share_pct / 100.0
    if ad_share <= 0:
        return _empty_organic(period_data)
    total_purchases = period_purchases / ad_share
    revenue = total_purchases * profit
    romi = ((revenue - ad_cost) / ad_cost * 100) if ad_cost > 0 else 0
    purchase_total_cost = (ad_cost / total_purchases) if total_purchases > 0 else 0
    net_profit_per_unit = profit - purchase_total_cost
    drr_sale_organic = (ad_cost / total_purchases / price * 100) if (total_purchases > 0 and price > 0) else 0
    return {
        "totalPurchases": total_purchases,
        "organicPurchases": total_purchases - period_purchases,
        "adCost": ad_cost,
        "revenue": revenue,
        "romi": romi,
        "purchaseTotalCost": purchase_total_cost,
        "netProfitPerUnit": net_profit_per_unit,
        "drrSaleOrganic": drr_sale_organic,
        "drrOrder": period_data.get("drrOrder", 0),
        "drrSale": period_data.get("drrSale", 0),
    }


def _empty_organic(period_data: Dict) -> Dict[str, float]:
    return {
        "totalPurchases": 0, "organicPurchases": 0, "adCost": 0, "revenue": 0,
        "romi": 0, "purchaseTotalCost": 0, "netProfitPerUnit": 0, "drrSaleOrganic": 0,
        "drrOrder": period_data.get("drrOrder", 0), "drrSale": period_data.get("drrSale", 0),
    }


def planner(
    target_sales: float,
    purchase_rate_pct: float,
    ad_share_pct: float,
    ad_carts_share_pct: float,
    cart_to_order_now_pct: float,
    cart_to_order_season_pct: float,
    total_orders_per_1000_now: float,
    total_orders_per_1000_season: float,
    cpm: float,
    duration_now: float,
    duration_season: float,
) -> Dict[str, Any]:
    """Планировщик: из целевых выкупов → заказы, корзины, показы, бюджет (сейчас и сезон)."""
    target_orders = target_sales / (purchase_rate_pct / 100.0) if purchase_rate_pct else 0
    ad_share = ad_share_pct / 100.0
    ad_carts_share = ad_carts_share_pct / 100.0

    impressions_needed_now = (target_orders / total_orders_per_1000_now * 1000) if total_orders_per_1000_now > 0 else 0
    impressions_needed_season = (target_orders / total_orders_per_1000_season * 1000) if total_orders_per_1000_season > 0 else 0
    budget_now = (impressions_needed_now / 1000.0) * cpm
    budget_season = (impressions_needed_season / 1000.0) * cpm

    ad_orders_now = target_orders * ad_share
    organic_orders_now = target_orders - ad_orders_now
    ad_orders_season = target_orders * ad_share
    organic_orders_season = target_orders - ad_orders_season

    cart_to_order_now = cart_to_order_now_pct / 100.0
    cart_to_order_season = cart_to_order_season_pct / 100.0
    total_carts_needed_now = (target_orders / cart_to_order_now) if cart_to_order_now > 0 else 0
    total_carts_needed_season = (target_orders / cart_to_order_season) if cart_to_order_season > 0 else 0
    ad_carts_now = total_carts_needed_now * ad_carts_share
    organic_carts_now = total_carts_needed_now - ad_carts_now
    ad_carts_season = total_carts_needed_season * ad_carts_share
    organic_carts_season = total_carts_needed_season - ad_carts_season

    duration_now = max(duration_now, 1)
    duration_season = max(duration_season, 1)
    return {
        "targetOrders": target_orders,
        "impressionsNeededNow": impressions_needed_now,
        "impressionsNeededSeason": impressions_needed_season,
        "budgetNow": budget_now,
        "budgetSeason": budget_season,
        "dailyBudgetNow": budget_now / duration_now,
        "dailyBudgetSeason": budget_season / duration_season,
        "dailyOrdersNow": target_orders / duration_now,
        "dailyAdOrdersNow": ad_orders_now / duration_now,
        "dailyOrganicOrdersNow": organic_orders_now / duration_now,
        "dailyOrdersSeason": target_orders / duration_season,
        "dailyAdOrdersSeason": ad_orders_season / duration_season,
        "dailyOrganicOrdersSeason": organic_orders_season / duration_season,
        "dailyCartsNow": total_carts_needed_now / duration_now,
        "dailyAdCartsNow": ad_carts_now / duration_now,
        "dailyOrganicCartsNow": organic_carts_now / duration_now,
        "dailyCartsSeason": total_carts_needed_season / duration_season,
        "dailyAdCartsSeason": ad_carts_season / duration_season,
        "dailyOrganicCartsSeason": organic_carts_season / duration_season,
        "impressionsPerDayNow": impressions_needed_now / duration_now,
        "impressionsPerWeekNow": impressions_needed_now / (duration_now / 7.0) if duration_now else 0,
        "impressionsPerDaySeason": impressions_needed_season / duration_season,
        "impressionsPerWeekSeason": impressions_needed_season / (duration_season / 7.0) if duration_season else 0,
        "adOrdersNow": ad_orders_now,
        "organicOrdersNow": organic_orders_now,
        "adOrdersSeason": ad_orders_season,
        "organicOrdersSeason": organic_orders_season,
    }


# --- Оценка дня (из Аналитка рекламы по дням.html) ---

RATING_LABELS = ("Критично", "Плохо", "Средне", "Хорошо", "Отлично")


def evaluate_day(day: Dict[str, Any], target_cpl: float) -> Dict[str, Any]:
    """Дополняет данные дня: CPL общий, эффективность, конверсии, рейтинг."""
    carts_total = day.get("carts_total") or 0
    cost = day.get("cost") or 0
    cpl_total = (cost / carts_total) if carts_total > 0 else 0
    efficiency = ((target_cpl - cpl_total) / target_cpl * 100) if target_cpl > 0 else 0

    shows = day.get("shows") or 0
    transitions = day.get("transitions") or 0
    carts_rk = day.get("carts_rk") or 0
    orders_rk = day.get("orders_rk") or 0
    total_shows = day.get("totalShows") or 0
    total_transitions = day.get("totalTransitions") or 0
    orders = day.get("orders") or 0

    ctr_rk = (transitions / shows * 100) if shows > 0 else 0
    show_to_cart_rk = (carts_rk / shows * 100) if shows > 0 else 0
    click_to_cart_rk = (carts_rk / transitions * 100) if transitions > 0 else 0
    cart_to_order_rk = (orders_rk / carts_rk * 100) if carts_rk > 0 else 0

    ctr_total = (total_transitions / total_shows * 100) if total_shows > 0 else 0
    show_to_cart_total = (carts_total / total_shows * 100) if total_shows > 0 else 0
    click_to_cart_total = (carts_total / total_transitions * 100) if total_transitions > 0 else 0
    cart_to_order_total = (orders / carts_total * 100) if carts_total > 0 else 0

    organic_shows = max(0, total_shows - shows)
    organic_transitions = max(0, total_transitions - transitions)
    organic_carts = max(0, carts_total - carts_rk)
    organic_orders = max(0, orders - orders_rk)
    ctr_organic = (organic_transitions / organic_shows * 100) if organic_shows > 0 else 0
    click_to_cart_organic = (organic_carts / organic_transitions * 100) if organic_transitions > 0 else 0
    cart_to_order_organic = (organic_orders / organic_carts * 100) if organic_carts > 0 else 0

    score = 0
    if cpl_total > 0:
        if cpl_total <= target_cpl * 0.7:
            score += 40
        elif cpl_total <= target_cpl:
            score += 30
        elif cpl_total <= target_cpl * 1.5:
            score += 15
    if orders >= 5:
        score += 30
    elif orders >= 2:
        score += 20
    elif orders >= 1:
        score += 10
    if carts_total >= 10:
        score += 30
    elif carts_total >= 5:
        score += 20
    elif carts_total >= 1:
        score += 10
    score = min(score, 100)

    if score >= 80:
        rating = "Отлично"
    elif score >= 60:
        rating = "Хорошо"
    elif score >= 40:
        rating = "Средне"
    elif score >= 20:
        rating = "Плохо"
    else:
        rating = "Критично"

    out = dict(day)
    out.update({
        "cplTotal": cpl_total,
        "targetCpl": target_cpl,
        "efficiency": efficiency,
        "score": score,
        "rating": rating,
        "ctrRk": ctr_rk,
        "showToCartRk": show_to_cart_rk,
        "clickToCartRk": click_to_cart_rk,
        "cartToOrderRk": cart_to_order_rk,
        "ctrTotal": ctr_total,
        "showToCartTotal": show_to_cart_total,
        "clickToCartTotal": click_to_cart_total,
        "cartToOrderTotal": cart_to_order_total,
        "organicShows": organic_shows,
        "organicTransitions": organic_transitions,
        "organicCarts": organic_carts,
        "organicOrders": organic_orders,
        "ctrOrganic": ctr_organic,
        "clickToCartOrganic": click_to_cart_organic,
        "cartToOrderOrganic": cart_to_order_organic,
    })
    return out


def aggregate_daily_kpis(
    days: List[Dict[str, Any]], target_cpl: float
) -> Dict[str, Any]:
    """Суммы и средние по списку дней для KPI-карточек."""
    if not days:
        return {}
    total_cost = sum(d.get("cost") or 0 for d in days)
    total_shows = sum(d.get("shows") or 0 for d in days)
    total_shows_all = sum(d.get("totalShows") or 0 for d in days)
    total_orders = sum(d.get("orders") or 0 for d in days)
    total_orders_rk = sum(d.get("orders_rk") or 0 for d in days)
    total_carts = sum(d.get("carts_total") or 0 for d in days)
    total_carts_rk = sum(d.get("carts_rk") or 0 for d in days)
    total_trans = sum(d.get("transitions") or 0 for d in days)
    total_trans_all = sum(d.get("totalTransitions") or 0 for d in days)
    n = len(days)
    avg_cost = total_cost / n
    avg_cpm = (total_cost / total_shows * 1000) if total_shows > 0 else 0
    avg_cpc = (total_cost / total_trans) if total_trans > 0 else 0
    cpl_days = [d for d in days if (d.get("cplTotal") or 0) > 0]
    avg_cpl_total = sum(d["cplTotal"] for d in cpl_days) / len(cpl_days) if cpl_days else 0
    cpl_rk_days = [d for d in days if (d.get("cpl_rk") or 0) > 0]
    avg_cpl_rk = sum(d["cpl_rk"] for d in cpl_rk_days) / len(cpl_rk_days) if cpl_rk_days else 0
    shows_ratio = (total_shows / total_shows_all * 100) if total_shows_all > 0 else 0
    organic_ratio = 100 - shows_ratio
    carts_ratio = (total_carts_rk / total_carts * 100) if total_carts > 0 else 0
    orders_ratio = (total_orders_rk / total_orders * 100) if total_orders > 0 else 0
    avg_ctr_rk = (total_trans / total_shows * 100) if total_shows > 0 else 0
    avg_show_to_cart_rk = (total_carts_rk / total_shows * 100) if total_shows > 0 else 0
    avg_click_to_cart_rk = (total_carts_rk / total_trans * 100) if total_trans > 0 else 0
    avg_cart_to_order_rk = (total_orders_rk / total_carts_rk * 100) if total_carts_rk > 0 else 0
    avg_ctr_total = (total_trans_all / total_shows_all * 100) if total_shows_all > 0 else 0
    avg_show_to_cart_total = (total_carts / total_shows_all * 100) if total_shows_all > 0 else 0
    avg_click_to_cart_total = (total_carts / total_trans_all * 100) if total_trans_all > 0 else 0
    avg_cart_to_order_total = (total_orders / total_carts * 100) if total_carts > 0 else 0
    total_conv = (total_orders / total_shows_all * 100) if total_shows_all > 0 else 0
    total_efficiency = (sum(d.get("efficiency", 0) for d in days) / n) if n else 0
    rating_scores = {"Отлично": 5, "Хорошо": 4, "Средне": 3, "Плохо": 2, "Критично": 1}
    avg_rating = sum(rating_scores.get(d.get("rating", ""), 1) for d in days) / n if n else 0
    avg_rating_score = sum(d.get("score", 0) for d in days) / n if n else 0

    total_shows_organic = total_shows_all - total_shows
    total_trans_organic = total_trans_all - total_trans
    total_carts_organic = total_carts - total_carts_rk
    total_orders_organic = total_orders - total_orders_rk
    avg_ctr_organic = (total_trans_organic / total_shows_organic * 100) if total_shows_organic > 0 else 0
    avg_click_to_cart_organic = (total_carts_organic / total_trans_organic * 100) if total_trans_organic > 0 else 0
    avg_cart_to_order_organic = (total_orders_organic / total_carts_organic * 100) if total_carts_organic > 0 else 0

    return {
        "totalCost": total_cost,
        "avgCost": avg_cost,
        "totalShows": total_shows,
        "totalShowsAll": total_shows_all,
        "totalShowsOrganic": total_shows_organic,
        "totalTransitions": total_trans,
        "totalTransitionsAll": total_trans_all,
        "totalTransitionsOrganic": total_trans_organic,
        "totalCarts": total_carts,
        "totalCartsRk": total_carts_rk,
        "totalCartsOrganic": total_carts_organic,
        "totalOrders": total_orders,
        "totalOrdersRk": total_orders_rk,
        "totalOrdersOrganic": total_orders_organic,
        "avgCpm": avg_cpm,
        "avgCpc": avg_cpc,
        "avgCplTotal": avg_cpl_total,
        "avgCplRk": avg_cpl_rk,
        "showsRatio": shows_ratio,
        "organicRatio": organic_ratio,
        "cartsRatio": carts_ratio,
        "ordersRatio": orders_ratio,
        "avgCtrRk": avg_ctr_rk,
        "avgShowToCartRk": avg_show_to_cart_rk,
        "avgClickToCartRk": avg_click_to_cart_rk,
        "avgCartToOrderRk": avg_cart_to_order_rk,
        "avgCtrOrganic": avg_ctr_organic,
        "avgClickToCartOrganic": avg_click_to_cart_organic,
        "avgCartToOrderOrganic": avg_cart_to_order_organic,
        "avgCtrTotal": avg_ctr_total,
        "avgShowToCartTotal": avg_show_to_cart_total,
        "avgClickToCartTotal": avg_click_to_cart_total,
        "avgCartToOrderTotal": avg_cart_to_order_total,
        "totalConv": total_conv,
        "totalEfficiency": total_efficiency,
        "avgRating": avg_rating,
        "avgRatingScore": avg_rating_score,
    }


def aggregate_by_type(
    details: Dict[str, List[Dict]], dates_in_period: Optional[List[str]] = None
) -> Dict[str, Dict[str, float]]:
    """Агрегат по типам рекламы (поиск, полки, каталог) из details. Если dates_in_period задан — только эти даты."""
    by_type = {}
    for date_key, rows in details.items():
        if dates_in_period is not None and date_key not in dates_in_period:
            continue
        for r in rows:
            typ = (r.get("type") or "").lower()
            if "поиск" in typ:
                key = "search"
            elif "полки" in typ:
                key = "shelf"
            elif "каталог" in typ:
                key = "catalog"
            else:
                key = typ or "other"
            if key not in by_type:
                by_type[key] = {"shows": 0, "cost": 0, "cpm": 0, "cpc": 0, "carts": 0, "cpl": 0, "ctr": 0, "transitions": 0, "count": 0}
            t = by_type[key]
            t["shows"] += r.get("shows") or 0
            t["cost"] += r.get("cost") or 0
            t["carts"] += r.get("carts") or 0
            t["transitions"] += r.get("transitions") or 0
            t["count"] += 1
    for key in by_type:
        t = by_type[key]
        if t["shows"] > 0:
            t["cpm"] = t["cost"] / t["shows"] * 1000
        trans = t.get("transitions") or 0
        t["cpc"] = (t["cost"] / trans) if trans > 0 else 0
        t["ctr"] = (trans / t["shows"] * 100) if t["shows"] > 0 else 0
        t["cpl"] = (t["cost"] / t["carts"]) if t["carts"] > 0 else 0
    return by_type


def filter_days_by_period(
    days: List[Dict[str, Any]],
    period: str = "all",
    last_n_days: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Фильтрация дней: all, last7, last14, last30, custom (тогда start_date, end_date в формате YYYY-MM-DD)."""
    if not days:
        return []
    if period == "all":
        return days

    def parse_dt(d: Dict) -> datetime:
        s = d.get("date") or ""
        parts = s.split(".")
        if len(parts) != 3:
            return datetime.min
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        return datetime(year, month, day)

    dates_parsed = [(d, parse_dt(d)) for d in days]
    max_dt = max(p[1] for p in dates_parsed)
    if period == "last7":
        start_dt = max_dt - timedelta(days=7)
    elif period == "last14":
        start_dt = max_dt - timedelta(days=14)
    elif period == "last30":
        start_dt = max_dt - timedelta(days=30)
    elif period == "custom" and start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            return [d for d, dt in dates_parsed if start_dt <= dt <= end_dt]
        except ValueError:
            return days
    else:
        return days
    if period in ("last7", "last14", "last30"):
        return [d for d, dt in dates_parsed if start_dt <= dt <= max_dt]
    return days


def get_recommendations(
    days: List[Dict[str, Any]],
    target_cpl: float,
    profit: float = 0,
    purchase_rate: float = 0,
) -> List[str]:
    """Подробные рекомендации: ROMI, CPL vs целевой, эффективность, лучшие/худшие дни."""
    if not days:
        return []
    recs = []
    n = len(days)
    total_cost = sum(d.get("cost") or 0 for d in days)
    total_orders_rk = sum(d.get("orders_rk") or 0 for d in days)

    # ROMI (если есть расход на рекламу и заданы profit, purchase_rate)
    if total_cost > 0 and purchase_rate is not None:
        net_profit_ads = total_orders_rk * (purchase_rate / 100.0) * profit
        romi = net_profit_ads / total_cost * 100
        if romi < 100:
            recs.append(
                f"Реклама за период не окупается (ROMI {romi:.0f}%). Рекомендуется снизить ставки или пересмотреть таргетинг."
            )
        else:
            recs.append(f"Реклама за период окупается (ROMI {romi:.0f}%).")

    # Эффективность: последние дни vs среднее
    avg_score = sum(d.get("score") or 0 for d in days) / n
    recent_n = min(7, n)
    recent_avg = sum(d.get("score") or 0 for d in days[:recent_n]) / recent_n if recent_n else 0
    if recent_avg > avg_score:
        recs.append("В последнюю неделю эффективность выше среднего.")
    else:
        recs.append("В последнюю неделю эффективность ниже среднего.")

    # CPL vs целевой: доля дней выше целевого
    valid = [d for d in days if (d.get("cplTotal") or 0) > 0]
    if valid:
        above_target = [d for d in valid if d["cplTotal"] > target_cpl]
        pct_above = len(above_target) / len(valid) * 100
        if pct_above > 50:
            recs.append(
                f"Более половины дней ({pct_above:.0f}%) с CPL выше целевого — стоит проанализировать ставки и креативы в эти дни."
            )
        best = sorted(valid, key=lambda x: x["cplTotal"])[:5]
        worst = sorted(valid, key=lambda x: x["cplTotal"], reverse=True)[:5]
        best_avg = sum(d["cplTotal"] for d in best) / len(best)
        worst_avg = sum(d["cplTotal"] for d in worst) / len(worst)
        if best_avg < target_cpl:
            recs.append(f"В лучшие дни CPL {best_avg:.1f} ₽ — отличный результат, можно масштабировать в похожие периоды.")
        if worst_avg > target_cpl * 1.5:
            recs.append(f"В худшие дни CPL превышает {worst_avg:.1f} ₽ — рассмотреть снижение бюджета в подобные периоды.")

    # Дни с отрицательной эффективностью
    neg_eff = [d for d in days if (d.get("efficiency") or 0) < 0]
    if neg_eff:
        dates_str = ", ".join(d.get("date", "") for d in neg_eff[:7])
        if len(neg_eff) > 7:
            dates_str += " …"
        recs.append(f"Обратить внимание на дни с отрицательной Эфф.%: {dates_str}.")

    return recs


def day_for_calculator(day: Dict[str, Any]) -> Dict[str, float]:
    """
    По одному дню возвращает данные для подстановки в калькулятор «Текущий период».
    Все конверсии общие (Всего по товару). Органика/реклама — из % переходов и % корзин (органика = 100 - реклама).
    """
    shows = day.get("shows") or 0
    cost = day.get("cost") or 0
    total_shows = day.get("totalShows") or 0
    total_trans = day.get("totalTransitions") or 0
    carts_rk = day.get("carts_rk") or 0
    carts_total = day.get("carts_total") or 0
    orders = day.get("orders") or 0
    transitions = day.get("transitions") or 0

    organic_trans = max(0, total_trans - transitions)
    organic_carts = max(0, carts_total - carts_rk)

    cpm = (cost / shows * 1000) if shows > 0 else 0
    ctr = (total_trans / total_shows * 100) if total_shows > 0 else 0
    click_to_cart = (carts_total / total_trans * 100) if total_trans > 0 else 0
    cart_to_order = (orders / carts_total * 100) if carts_total > 0 else 0
    organic_share = (organic_trans / total_trans * 100) if total_trans > 0 else 50
    organic_carts_share = (organic_carts / carts_total * 100) if carts_total > 0 else 50
    return {
        "cpm": cpm,
        "ctr": ctr,
        "click_to_cart": click_to_cart,
        "cart_to_order": cart_to_order,
        "organic_share": organic_share,
        "organic_carts_share": organic_carts_share,
    }


def aggregate_for_calculator(
    days: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    По списку дней (из Excel) считает средние для подстановки в калькулятор «Текущий период»:
    cpm, ctr, click_to_cart, cart_to_order, ad_share (реклама показов), ad_carts_share, ad_share_orders.
    """
    if not days:
        return {}
    total_shows = sum(d.get("shows") or 0 for d in days)
    total_shows_all = sum(d.get("totalShows") or 0 for d in days)
    total_trans = sum(d.get("transitions") or 0 for d in days)
    total_carts = sum(d.get("carts_rk") or 0 for d in days)
    total_carts_all = sum(d.get("carts_total") or 0 for d in days)
    total_orders_rk = sum(d.get("orders_rk") or 0 for d in days)
    total_orders = sum(d.get("orders") or 0 for d in days)
    total_cost = sum(d.get("cost") or 0 for d in days)

    avg_cpm = (total_cost / total_shows * 1000) if total_shows > 0 else 0
    ctr = (total_trans / total_shows * 100) if total_shows > 0 else 0
    click_to_cart = (total_carts / total_trans * 100) if total_trans > 0 else 0
    cart_to_order = (total_orders_rk / total_carts * 100) if total_carts > 0 else 0
    ad_share_shows = (total_shows / total_shows_all * 100) if total_shows_all > 0 else 50
    ad_carts_share = (total_carts / total_carts_all * 100) if total_carts_all > 0 else 50
    ad_share_orders = (total_orders_rk / total_orders * 100) if total_orders > 0 else 50
    return {
        "cpm": avg_cpm,
        "ctr": ctr,
        "click_to_cart": click_to_cart,
        "cart_to_order": cart_to_order,
        "ad_share": ad_share_orders,
        "ad_carts_share": ad_carts_share,
        "organic_share": 100 - ad_share_orders,
        "organic_carts_share": 100 - ad_carts_share,
    }
