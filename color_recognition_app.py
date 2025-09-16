import streamlit as st
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import webcolors
from collections import Counter
import io

# Настройка страницы
st.set_page_config(
    page_title="Распознавание цветов одежды",
    page_icon="🎨",
    layout="wide"
)

def closest_color(requested_color):
    """Находит ближайший цвет из стандартной палитры"""
    min_colors = {}
    # Используем правильный API для новой версии webcolors
    try:
        # Получаем все CSS3 цвета
        css3_colors = webcolors.CSS3_NAMES_TO_HEX
    except AttributeError:
        # Расширенная палитра цветов для лучшего распознавания
        css3_colors = {
            'red': '#FF0000', 'green': '#008000', 'blue': '#0000FF',
            'white': '#FFFFFF', 'black': '#000000', 'yellow': '#FFFF00',
            'orange': '#FFA500', 'purple': '#800080', 'pink': '#FFC0CB',
            'brown': '#A52A2A', 'gray': '#808080', 'grey': '#808080',
            'navy': '#000080', 'maroon': '#800000', 'lime': '#00FF00',
            'aqua': '#00FFFF', 'teal': '#008080', 'olive': '#808000',
            'silver': '#C0C0C0', 'fuchsia': '#FF00FF', 'crimson': '#DC143C',
            'darkred': '#8B0000', 'lightblue': '#ADD8E6', 'darkblue': '#00008B',
            'lightgreen': '#90EE90', 'darkgreen': '#006400', 'gold': '#FFD700',
            'beige': '#F5F5DC', 'tan': '#D2B48C', 'khaki': '#F0E68C',
            'violet': '#EE82EE', 'indigo': '#4B0082', 'turquoise': '#40E0D0',
            'coral': '#FF7F50', 'salmon': '#FA8072', 'lightgray': '#D3D3D3',
            'darkgray': '#A9A9A9', 'lightpink': '#FFB6C1', 'hotpink': '#FF69B4'
        }
    
    for name, hex_value in css3_colors.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(hex_value)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    return min_colors[min(min_colors.keys())]

def get_color_name(rgb):
    """Получает название цвета по RGB значениям"""
    try:
        return webcolors.rgb_to_name(rgb)
    except ValueError:
        return closest_color(rgb)

def extract_dominant_colors(image, num_colors=5):
    """Извлекает доминирующие цвета из изображения"""
    # Преобразуем изображение в массив numpy
    data = np.array(image)
    
    # Изменяем форму массива для кластеризации
    data = data.reshape((-1, 3))
    
    # Применяем K-means кластеризацию
    kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
    kmeans.fit(data)
    
    # Получаем центры кластеров (доминирующие цвета)
    colors = kmeans.cluster_centers_.astype(int)
    
    # Подсчитываем количество пикселей в каждом кластере
    labels = kmeans.labels_
    label_counts = Counter(labels)
    
    # Сортируем цвета по частоте
    color_freq = [(colors[i], label_counts[i]) for i in range(num_colors)]
    color_freq.sort(key=lambda x: x[1], reverse=True)
    
    return color_freq

def extract_dominant_colors_from_array(data, num_colors=5):
    """Извлекает доминирующие цвета из массива пикселей"""
    # Применяем K-means кластеризацию
    kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
    kmeans.fit(data)
    
    # Получаем центры кластеров (доминирующие цвета)
    colors = kmeans.cluster_centers_.astype(int)
    
    # Подсчитываем количество пикселей в каждом кластере
    labels = kmeans.labels_
    label_counts = Counter(labels)
    
    # Сортируем цвета по частоте
    color_freq = [(colors[i], label_counts[i]) for i in range(num_colors)]
    color_freq.sort(key=lambda x: x[1], reverse=True)
    
    return color_freq

def detect_clothing_region(image):
    """Улучшенное выделение области с одеждой"""
    # Конвертируем в HSV для лучшего выделения кожи
    hsv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2HSV)
    
    # Расширенные диапазоны для кожи (разные оттенки)
    skin_ranges = [
        ([0, 20, 70], [20, 255, 255]),      # Светлая кожа
        ([0, 30, 60], [25, 255, 255]),      # Средняя кожа
        ([0, 40, 50], [30, 255, 255]),      # Темная кожа
        ([160, 20, 70], [180, 255, 255])    # Розоватые оттенки
    ]
    
    # Создаем комбинированную маску для кожи
    skin_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lower, upper in skin_ranges:
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        skin_mask = cv2.bitwise_or(skin_mask, mask)
    
    # Морфологические операции для улучшения маски
    kernel = np.ones((5,5), np.uint8)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
    
    # Инвертируем маску, чтобы получить область без кожи
    clothing_mask = cv2.bitwise_not(skin_mask)
    
    return clothing_mask

def analyze_image_colors(image):
    """Улучшенный анализ цветов на изображении"""
    # Извлекаем доминирующие цвета
    dominant_colors = extract_dominant_colors(image, num_colors=8)
    
    # Пытаемся выделить область одежды
    clothing_mask = detect_clothing_region(image)
    
    # Применяем маску к изображению
    image_array = np.array(image)
    clothing_pixels = image_array[clothing_mask > 0]
    
    if len(clothing_pixels) > 0:
        # Анализируем цвета только в области одежды
        # Проверяем форму массива и правильно формируем для анализа
        if clothing_pixels.ndim == 1:
            # Если массив одномерный, преобразуем в двумерный
            clothing_pixels_reshaped = clothing_pixels.reshape(-1, 3)
        elif clothing_pixels.ndim == 2 and clothing_pixels.shape[1] == 3:
            # Если уже правильная форма, используем как есть
            clothing_pixels_reshaped = clothing_pixels
        else:
            # В других случаях используем общие цвета
            clothing_colors = dominant_colors[:5]
            return dominant_colors, clothing_colors
        
        # Фильтруем слишком темные и слишком светлые пиксели
        # Это помогает исключить тени и блики
        brightness = np.mean(clothing_pixels_reshaped, axis=1)
        filtered_pixels = clothing_pixels_reshaped[(brightness > 30) & (brightness < 220)]
        
        if len(filtered_pixels) > 100:  # Минимум пикселей для анализа
            clothing_colors = extract_dominant_colors_from_array(filtered_pixels, num_colors=5)
        else:
            clothing_colors = dominant_colors[:5]
    else:
        # Если не удалось выделить одежду, используем общие цвета
        clothing_colors = dominant_colors[:5]
    
    return dominant_colors, clothing_colors

def create_color_palette(colors, title):
    """Создает визуализацию палитры цветов"""
    fig, ax = plt.subplots(figsize=(12, 2))
    
    # Создаем полосы цветов
    color_strips = []
    color_names = []
    percentages = []
    
    total_pixels = sum([freq for _, freq in colors])
    
    for color, freq in colors:
        color_strips.append([color/255.0])
        color_name = get_color_name(tuple(color))
        color_names.append(f"{color_name}\n({freq} пикселей)")
        percentages.append(f"{freq/total_pixels*100:.1f}%")
    
    # Отображаем цвета
    for i, (color_strip, name, pct) in enumerate(zip(color_strips, color_names, percentages)):
        ax.barh(0, 1, left=i, color=color_strip, edgecolor='black', linewidth=1)
        ax.text(i + 0.5, 0, f"{name}\n{pct}", ha='center', va='center', 
                fontsize=8, fontweight='bold')
    
    ax.set_xlim(0, len(colors))
    ax.set_ylim(-0.5, 0.5)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_yticks([])
    ax.set_xticks([])
    
    plt.tight_layout()
    return fig

def main():
    st.title("🎨 Распознавание цветов одежды")
    st.markdown("Загрузите фотографию, и мы определим основные цвета одежды на ней!")
    
    # Загрузка изображения
    uploaded_file = st.file_uploader(
        "Выберите изображение", 
        type=['png', 'jpg', 'jpeg'],
        help="Поддерживаются форматы: PNG, JPG, JPEG"
    )
    
    if uploaded_file is not None:
        # Отображаем загруженное изображение
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📸 Загруженное изображение")
            st.image(image, width='stretch')
            
            # Показываем маску для отладки
            if st.checkbox("🔍 Показать маску одежды"):
                clothing_mask = detect_clothing_region(image)
                # Конвертируем маску в изображение для отображения
                mask_image = (clothing_mask * 255).astype(np.uint8)
                st.image(mask_image, caption="Область одежды (белое)", width='stretch')
        
        with col2:
            st.subheader("🔍 Анализ цветов")
            
            # Показываем прогресс
            with st.spinner("Анализируем цвета..."):
                dominant_colors, clothing_colors = analyze_image_colors(image)
            
            st.success("Анализ завершен!")
            
            # Настройки анализа
            st.subheader("⚙️ Настройки")
            num_colors = st.slider("Количество цветов для анализа", 3, 10, 5)
            
            if st.button("🔄 Обновить анализ"):
                dominant_colors, clothing_colors = analyze_image_colors(image)
        
        # Результаты анализа
        st.subheader("🎨 Результаты анализа")
        
        # Общие доминирующие цвета
        st.write("**Все доминирующие цвета на изображении:**")
        fig1 = create_color_palette(dominant_colors[:num_colors], "Общие цвета")
        st.pyplot(fig1)
        
        # Цвета одежды
        st.write("**Цвета одежды (исключая кожу):**")
        fig2 = create_color_palette(clothing_colors[:num_colors], "Цвета одежды")
        st.pyplot(fig2)
        
        # Детальная информация о цветах
        st.subheader("📊 Детальная информация")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Топ-5 общих цветов:**")
            for i, (color, freq) in enumerate(dominant_colors[:5], 1):
                color_name = get_color_name(tuple(color))
                st.write(f"{i}. **{color_name}** - RGB({color[0]}, {color[1]}, {color[2]})")
        
        with col2:
            st.write("**Топ-5 цветов одежды:**")
            for i, (color, freq) in enumerate(clothing_colors[:5], 1):
                color_name = get_color_name(tuple(color))
                st.write(f"{i}. **{color_name}** - RGB({color[0]}, {color[1]}, {color[2]})")
        
        # Экспорт результатов
        st.subheader("💾 Экспорт результатов")
        
        # Создаем отчет
        report = f"""
# Отчет по анализу цветов одежды

## Основные цвета:
"""
        for i, (color, freq) in enumerate(dominant_colors[:5], 1):
            color_name = get_color_name(tuple(color))
            report += f"{i}. {color_name} - RGB({color[0]}, {color[1]}, {color[2]})\n"
        
        report += "\n## Цвета одежды:\n"
        for i, (color, freq) in enumerate(clothing_colors[:5], 1):
            color_name = get_color_name(tuple(color))
            report += f"{i}. {color_name} - RGB({color[0]}, {color[1]}, {color[2]})\n"
        
        st.download_button(
            label="📥 Скачать отчет",
            data=report,
            file_name="color_analysis_report.txt",
            mime="text/plain"
        )
    
    else:
        # Инструкции для пользователя
        st.info("👆 Загрузите изображение выше, чтобы начать анализ")
        
        st.markdown("""
        ## 🚀 Как использовать:
        
        1. **Загрузите фотографию** - нажмите на область загрузки и выберите изображение
        2. **Дождитесь анализа** - программа автоматически проанализирует цвета
        3. **Изучите результаты** - посмотрите на палитру цветов и их названия
        4. **Настройте параметры** - измените количество анализируемых цветов
        5. **Скачайте отчет** - сохраните результаты анализа
        
        ## 🎯 Особенности:
        
        - **Умное выделение одежды** - программа пытается исключить цвет кожи
        - **Точные названия цветов** - использует стандартную палитру CSS
        - **Визуальная палитра** - наглядное отображение найденных цветов
        - **Детальная статистика** - количество пикселей и процентное соотношение
        
        ## 💡 Советы для лучших результатов:
        
        - Используйте фотографии с хорошим освещением
        - Одежда должна быть хорошо видна на фото
        - Избегайте слишком темных или слишком светлых изображений
        """)

if __name__ == "__main__":
    main()
