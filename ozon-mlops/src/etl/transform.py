import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


def merge_data(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Объединяет данные из разных источников в единый DataFrame.

    Args:
        data: Словарь с DataFrame для каждого типа событий

    Returns:
        Объединенный DataFrame со всеми событиями
    """
    logger.info("Начало объединения данных")

    # Приведение временных меток к единому формату
    for name, df in data.items():
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Объединение данных
    all_data = pd.concat([
        data['views'],
        data['purchases'],
        data['cart']
    ], ignore_index=True)

    # Сортировка по времени
    all_data = all_data.sort_values('timestamp')

    # Удаление дубликатов
    initial_count = len(all_data)
    all_data = all_data.drop_duplicates()
    duplicates_count = initial_count - len(all_data)
    if duplicates_count > 0:
        logger.info(f"Удалено {duplicates_count} дубликатов записей")

    # Обработка пропущенных значений
    if 'category' in all_data.columns:
        unknown_count = all_data['category'].isna().sum()
        all_data['category'] = all_data['category'].fillna('unknown')
        if unknown_count > 0:
            logger.warning(f"Заполнено {unknown_count} пропущенных значений категории")

    logger.info(f"Объединено {len(all_data)} записей из всех источников")
    return all_data


def calculate_purchase_frequency(purchases: pd.DataFrame,
                                 time_window: str = '30D') -> pd.DataFrame:
    """
    Рассчитывает частоту покупок пользователей за указанный период.

    Args:
        purchases: DataFrame с данными о покупках
        time_window: Окно времени для анализа (по умолчанию 30 дней)

    Returns:
        DataFrame с частотой покупок для каждого пользователя
    """
    if purchases.empty:
        logger.warning("Нет данных о покупках для расчета частоты")
        return pd.DataFrame(columns=['user_id', 'purchase_frequency'])

    # Определение временного диапазона
    end_date = purchases['timestamp'].max()
    start_date = end_date - pd.Timedelta(time_window)

    # Фильтрация по временному окну
    recent_purchases = purchases[purchases['timestamp'] >= start_date]

    # Расчет частоты
    frequency = recent_purchases.groupby('user_id').size().reset_index(name='purchase_frequency')
    return frequency


def calculate_average_check(purchases: pd.DataFrame) -> pd.DataFrame:
    """Рассчитывает средний чек для каждого пользователя"""
    if purchases.empty:
        logger.warning("Нет данных о покупках для расчета среднего чека")
        return pd.DataFrame(columns=['user_id', 'average_check'])

    avg_check = purchases.groupby('user_id')['amount'].mean().reset_index(name='average_check')
    return avg_check


def calculate_time_since_last_action(all_data: pd.DataFrame) -> pd.DataFrame:
    """Рассчитывает время с последнего действия для каждого пользователя"""
    if all_data.empty:
        logger.warning("Нет данных для расчета времени с последнего действия")
        return pd.DataFrame(columns=['user_id', 'hours_since_last_action'])

    last_action = all_data.groupby('user_id')['timestamp'].max().reset_index()
    last_action['hours_since_last_action'] = (pd.Timestamp.now() - last_action['timestamp']).dt.total_seconds() / 3600
    return last_action[['user_id', 'hours_since_last_action']]


def calculate_item_popularity(purchases: pd.DataFrame) -> pd.DataFrame:
    """Рассчитывает популярность товаров на основе покупок"""
    if purchases.empty:
        logger.warning("Нет данных о покупках для расчета популярности товаров")
        return pd.DataFrame(columns=['item_id', 'popularity_score'])

    popularity = purchases.groupby('item_id').size().reset_index(name='popularity_score')
    return popularity


def calculate_category_preferences(purchases: pd.DataFrame) -> pd.DataFrame:
    """Определяет предпочтительные категории для каждого пользователя"""
    if purchases.empty:
        logger.warning("Нет данных о покупках для расчета категорийных предпочтений")
        return pd.DataFrame(columns=['user_id', 'top_category'])

    # Подсчет количества покупок в каждой категории для пользователя
    user_category = purchases.groupby(['user_id', 'category']).size().reset_index(name='count')

    # Определение самой популярной категории для каждого пользователя
    idx = user_category.groupby('user_id')['count'].idxmax()
    top_categories = user_category.loc[idx, ['user_id', 'category']].rename(columns={'category': 'top_category'})

    return top_categories


def generate_features(all_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Генерирует все необходимые фичи для рекомендательной системы.

    Args:
        all_data: Объединенный DataFrame со всеми событиями

    Returns:
        Словарь с DataFrame для различных типов фич
    """
    logger.info("Начало генерации фич")

    # Разделение данных по типу события
    purchases = all_data[all_data['event_type'] == 'purchase'].copy()
    views = all_data[all_data['event_type'] == 'view'].copy()
    cart = all_data[all_data['event_type'] == 'cart'].copy()

    # Расчет пользовательских фич
    user_features = {}

    if not purchases.empty:
        user_features['purchase_frequency'] = calculate_purchase_frequency(purchases)
        user_features['average_check'] = calculate_average_check(purchases)
        user_features['category_preferences'] = calculate_category_preferences(purchases)

    user_features['time_since_last_action'] = calculate_time_since_last_action(all_data)

    # Расчет товарных фич
    item_features = {}
    if not purchases.empty:
        item_features['popularity'] = calculate_item_popularity(purchases)

    logger.info("Генерация фич завершена")
    return {
        'user_features': user_features,
        'item_features': item_features
    }
