import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_views(file_path: str) -> pd.DataFrame:
    """
    Загружает данные о просмотрах из CSV файла.

    Args:
        file_path: Путь к файлу с данными о просмотрах

    Returns:
        DataFrame с данными о просмотрах

    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если отсутствуют необходимые колонки
    """
    try:
        logger.info(f"Загрузка данных о просмотрах из {file_path}")
        df = pd.read_csv(file_path)

        # Проверка наличия необходимых колонок
        required_columns = ['user_id', 'item_id', 'timestamp']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Отсутствуют необходимые колонки в данных о просмотрах: {missing}")

        # Добавляем тип события
        df['event_type'] = 'view'
        return df

    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных о просмотрах: {str(e)}")
        raise


def load_purchases(file_path: str) -> pd.DataFrame:
    """Загружает данные о покупках из CSV файла"""
    # Аналогично load_views, но с дополнительными колонками (amount, category)
    try:
        logger.info(f"Загрузка данных о покупках из {file_path}")
        df = pd.read_csv(file_path)

        required_columns = ['user_id', 'item_id', 'timestamp', 'amount']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Отсутствуют необходимые колонки в данных о покупках: {missing}")

        df['event_type'] = 'purchase'
        # Проверка на отрицательные значения суммы
        if (df['amount'] < 0).any():
            logger.warning("Обнаружены отрицательные значения суммы покупок")

        return df

    except Exception as e:
        logger.error(f"Ошибка при загрузке данных о покупках: {str(e)}")
        raise


def load_cart(file_path: str) -> pd.DataFrame:
    """Загружает данные о добавлениях в корзину из CSV файла"""
    # Аналогично предыдущим функциям
    try:
        logger.info(f"Загрузка данных о корзине из {file_path}")
        df = pd.read_csv(file_path)

        required_columns = ['user_id', 'item_id', 'timestamp']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Отсутствуют необходимые колонки в данных корзины: {missing}")

        df['event_type'] = 'cart'
        return df

    except Exception as e:
        logger.error(f"Ошибка при загрузке данных корзины: {str(e)}")
        raise


def load_all_data(data_paths: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """
    Загружает все типы данных и возвращает их в виде словаря.

    Args:
        data_paths: Словарь с путями к файлам для каждого типа данных

    Returns:
        Словарь с загруженными DataFrame
    """
    data = {}
    try:
        data['views'] = load_views(data_paths['views'])
        data['purchases'] = load_purchases(data_paths['purchases'])
        data['cart'] = load_cart(data_paths['cart'])
        return data
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {str(e)}")
        raise
