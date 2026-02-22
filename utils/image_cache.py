# -*- coding: utf-8 -*-
"""
Модуль для кеширования изображений
"""
import os
import json
import base64
import requests
from io import BytesIO

try:
    from PIL import Image
except Exception:
    Image = None


def _cache_root():
    """Возвращает корневую директорию кеша"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wb_cache")


def _cache_dir():
    """Создает и возвращает директорию кеша"""
    d = _cache_root()
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "imgs"), exist_ok=True)
    return d


def _url_cache_path():
    """Возвращает путь к файлу кеша URL"""
    return os.path.join(_cache_dir(), "image_cache.json")


def load_url_cache():
    """Загружает кеш URL из файла"""
    p = _url_cache_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_url_cache(m: dict):
    """Сохраняет кеш URL в файл"""
    try:
        with open(_url_cache_path(), "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def img_path_for(nm: str, fmt: str = "JPEG"):
    """Возвращает путь к изображению в кеше"""
    nm = str(nm).replace(".0", "")
    ext = "jpg" if fmt.upper() == "JPEG" else "png"
    return os.path.join(_cache_dir(), "imgs", f"{nm}.{ext}")


def get_cached_image_path(nm: str):
    """Проверяет, есть ли изображение в кеше и возвращает путь к нему"""
    nm = str(nm).replace(".0", "")
    
    # Проверяем различные форматы изображений
    for ext in ("jpg", "png", "jpeg", "webp", "JPG", "PNG", "JPEG", "WEBP"):
        p = os.path.join(_cache_dir(), "imgs", f"{nm}.{ext}")
        if os.path.exists(p) and os.path.getsize(p) > 0:  # Проверяем, что файл не пустой
            return p
    
    return ""


def ensure_image_cached(nm: str, url: str, fmt: str = "JPEG", timeout: int = 25) -> str:
    """Скачивает изображение по URL и сохраняет в кеш"""
    try:
        # Сначала проверяем, есть ли уже изображение в кеше
        p_exist = get_cached_image_path(nm)
        if p_exist:
            return p_exist
        
        if not url:
            return ""
        
        # Создаем путь для сохранения
        path = img_path_for(nm, fmt)
        
        # Убеждаемся, что директория существует
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Скачиваем изображение
        headers = {
            "User-Agent": "WB-Dashboard/1.0",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
        }
        
        with requests.get(url, headers=headers, timeout=timeout, stream=True) as r:
            if r.status_code != 200:
                return ""
            
            # Проверяем, что это действительно изображение
            content_type = r.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                return ""
            
            # Сохраняем файл
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            
            # Проверяем, что файл создался и не пустой
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path
            else:
                # Удаляем пустой файл
                if os.path.exists(path):
                    os.remove(path)
                return ""
                
    except Exception as e:
        # В случае ошибки удаляем частично скачанный файл
        try:
            path = img_path_for(nm, fmt)
            if os.path.exists(path):
                os.remove(path)
        except:
            pass
        return ""


def get_cache_status():
    """Возвращает информацию о состоянии кеша изображений"""
    cache_dir = os.path.join(_cache_dir(), "imgs")
    if not os.path.exists(cache_dir):
        return {"count": 0, "size": 0, "files": []}
    
    files = []
    total_size = 0
    
    for filename in os.listdir(cache_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            file_path = os.path.join(cache_dir, filename)
            file_size = os.path.getsize(file_path)
            files.append({
                "name": filename,
                "size": file_size,
                "path": file_path
            })
            total_size += file_size
    
    return {
        "count": len(files),
        "size": total_size,
        "files": files
    }


def load_image_bytes(path: str, max_w: int | None = None) -> bytes:
    """Загружает байты изображения с возможностью ресайза"""
    if not path or not os.path.exists(path):
        return b""
    if Image is None or max_w is None:
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception:
            return b""
    try:
        im = Image.open(path)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        if max_w and im.width > max_w:
            ratio = max_w / float(im.width)
            im = im.resize((int(im.width * ratio), int(im.height * ratio)))
        bio = BytesIO()
        im.save(bio, format="JPEG", quality=85)
        return bio.getvalue()
    except Exception:
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception:
            return b""


def img_data_uri(nm: str, max_w: int | None = None) -> str:
    """Создает data URI для изображения из кеша"""
    p = get_cached_image_path(nm)
    if not p:
        return ""
    try:
        data = load_image_bytes(p, max_w=max_w)
        if not data:
            return ""
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return ""


def get_cached_images_for_sku(sku: str, max_images: int = 3) -> list:
    """
    Получает пути к кешированным изображениям товара по артикулу.
    Использует уже скачанные изображения из кеша.
    
    Args:
        sku: Артикул товара
        max_images: Максимальное количество изображений (по умолчанию 3)
        
    Returns:
        Список путей к изображениям
    """
    images = []
    sku_clean = str(sku).replace(".0", "")
    
    # Проверяем основное изображение (обычно это первое фото товара)
    main_image = get_cached_image_path(sku_clean)
    if main_image and os.path.exists(main_image):
        images.append(main_image)
    
    # Если нужно больше изображений, можно искать дополнительные
    # (например, с суффиксами _1, _2 и т.д.)
    if len(images) < max_images:
        cache_dir = os.path.join(_cache_dir(), "imgs")
        if os.path.exists(cache_dir):
            # Ищем дополнительные изображения с суффиксами
            for suffix in range(1, max_images):
                for ext in ("jpg", "png", "jpeg", "webp", "JPG", "PNG", "JPEG", "WEBP"):
                    additional_path = os.path.join(cache_dir, f"{sku_clean}_{suffix}.{ext}")
                    if os.path.exists(additional_path) and additional_path not in images:
                        images.append(additional_path)
                        break
    
    return images[:max_images]


def get_url_cache_with_state(session_state):
    """Получает кеш URL с использованием session_state (для Streamlit)"""
    if "img_url_cache" not in session_state:
        session_state["img_url_cache"] = load_url_cache()
    return session_state["img_url_cache"]



























