# -*- coding: utf-8 -*-
"""
Utils package для WB Dashboard
"""

from .calculations import calculate_unit_economics, calculate_daily_profit
from .formatters import (
    format_thousands, format_thousands_with_spaces,
    fmt_rub, fmt_units, fmt_rub_kpi, fmt_units_kpi,
    fmt_date, parse_thousands_input, sort_df
)
from .prophet_forecast import (
    PROPHET_AVAILABLE, prepare_data_for_prophet,
    create_prophet_forecast, plot_prophet_forecast, plot_prophet_components
)
from .wb_utils import build_wb_product_url, extract_sku_from_url, extract_sku_from_filename
from .image_cache import (
    load_url_cache, save_url_cache, get_url_cache_with_state,
    get_cached_image_path, ensure_image_cached, get_cache_status,
    load_image_bytes, img_data_uri, get_cached_images_for_sku, img_path_for
)
from .image_analysis import (
    extract_dominant_colors_from_image, get_color_name_russian, analyze_style_from_image
)
from .wb_api_images import (
    get_product_image_urls_from_wb_api, get_product_name_from_wb, build_screenshot_url
)
from .file_cache import (
    save_file_cache, load_file_cache, get_file_cache_info,
    get_all_cached_files, save_file_to_cache
)
from .reports import (
    load_report_from_tovar_folder, find_and_load_reports_from_tovar
)
from .wgsn_reader import read_wgsn_files
from .data_processing import (
    read_table as read_table_base, get_file_statistics, get_analysis_period
)
from .ai_analysis import (
    analyze_combination_products_with_ai_core,
    analyze_wgsn_trends_with_ai_core,
    analyze_image_with_ai_core,
    OPENAI_AVAILABLE as OPENAI_AVAILABLE_UTILS
)

__all__ = [
    # Unit economics
    'calculate_unit_economics',
    'calculate_daily_profit',
    # Formatters
    'format_thousands',
    'format_thousands_with_spaces',
    'fmt_rub',
    'fmt_units',
    'fmt_rub_kpi',
    'fmt_units_kpi',
    'fmt_date',
    'parse_thousands_input',
    'sort_df',
    # Prophet
    'PROPHET_AVAILABLE',
    'prepare_data_for_prophet',
    'create_prophet_forecast',
    'plot_prophet_forecast',
    'plot_prophet_components',
    # WB Utils
    'build_wb_product_url',
    'extract_sku_from_url',
    'extract_sku_from_filename',
    # Image Cache
    'load_url_cache',
    'save_url_cache',
    'get_url_cache_with_state',
    'get_cached_image_path',
    'ensure_image_cached',
    'get_cache_status',
    'load_image_bytes',
    'img_data_uri',
    'get_cached_images_for_sku',
    'img_path_for',
    # Image Analysis
    'extract_dominant_colors_from_image',
    'get_color_name_russian',
    'analyze_style_from_image',
    # WB API Images
    'get_product_image_urls_from_wb_api',
    'get_product_name_from_wb',
    'build_screenshot_url',
    # File Cache
    'save_file_cache',
    'load_file_cache',
    'get_file_cache_info',
    'get_all_cached_files',
    'save_file_to_cache',
    # Reports
    'load_report_from_tovar_folder',
    'find_and_load_reports_from_tovar',
    # WGSN Reader
    'read_wgsn_files',
    # Data Processing
    'read_table_base',
    'get_file_statistics',
    'get_analysis_period',
    # AI Analysis
    'analyze_combination_products_with_ai_core',
    'analyze_wgsn_trends_with_ai_core',
    'analyze_image_with_ai_core',
    'OPENAI_AVAILABLE_UTILS',
]



























