import pandas as pd
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def check_data_quality(df: pd.DataFrame, critical_columns: list = None) -> bool:
    """
    Проверяет качество данных на наличие критических проблем.

    Args:
        df: DataFrame для проверки
        critical_columns: Список критических колонок, которые не должны содержать NaN

    Returns:
        True, если данные прошли проверку, иначе False
    """
    if df is None or not isinstance(df, pd.DataFrame):
        logger.error("Передан невалидный DataFrame для проверки качества данных")
        return False

    if df.empty:
        logger.error("DataFrame пустой")
        return False

    if critical_columns is None:
        critical_columns = ['user_id', 'item_id', 'timestamp']

    is_valid = True

    # Проверка критических колонок на наличие NaN
    for col in critical_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                percent = null_count / len(df) * 100
                logger.warning(
                    f"Найдены пропущенные значения в критической колонке '{col}': {null_count} ({percent:.2f}%)")
                is_valid = False

    # Проверка на аномально низкий объем данных
    if len(df) < 1000:  # Примерный порог для тестовых данных
        logger.warning(f"Аномально низкий объем данных: {len(df)} записей")
        is_valid = False

    return is_valid


def load_previous_metrics(output_dir: str) -> Optional[Dict[str, Any]]:
    """
    Загружает предыдущие метрики из файла.

    Args:
        output_dir: Каталог с сохраненными метриками

    Returns:
        Словарь с предыдущими метриками или None
    """
    metrics_path = os.path.join(output_dir, "monitoring_metrics.json")
    if not os.path.exists(metrics_path):
        logger.info("Предыдущие метрики не найдены")
        return None

    try:
        with open(metrics_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке предыдущих метрик: {str(e)}")
        return None


def detect_data_drift(current_metrics: Dict[str, Any],
                      previous_metrics: Optional[Dict[str, Any]],
                      thresholds: Dict[str, float] = None) -> Dict[str, bool]:
    """
    Обнаруживает дрейф данных путем сравнения текущих и предыдущих метрик.

    Args:
        current_metrics: Текущие метрики
        previous_metrics: Предыдущие метрики
        thresholds: Пороги изменений для каждой метрики

    Returns:
        Словарь с результатами проверки для каждой метрики
    """
    if previous_metrics is None:
        logger.info("Невозможно проверить дрейф данных: отсутствуют предыдущие метрики")
        return {}

    if thresholds is None:
        thresholds = {
            'avg_purchase_frequency': 0.2,  # 20%
            'avg_check': 0.3,  # 30%
            'user_count': 0.1,  # 10%
            'item_count': 0.1,  # 10%
            'avg_popularity': 0.25  # 25%
        }

    alerts = {}

    for metric, threshold in thresholds.items():
        if metric in current_metrics and metric in previous_metrics:
            current_val = current_metrics[metric]
            previous_val = previous_metrics[metric]

            # Избегаем деления на ноль
            if previous_val == 0:
                change = float('inf') if current_val > 0 else 0
            else:
                change = abs(current_val - previous_val) / previous_val

            if change > threshold:
                logger.warning(f"Обнаружен дрейф данных в метрике '{metric}': "
                               f"изменение {change:.2%} (порог {threshold:.0%})")
                alerts[metric] = True
            else:
                alerts[metric] = False

    return alerts


def send_alerts(alerts: Dict[str, bool], current_metrics: Dict[str, Any],
                previous_metrics: Optional[Dict[str, Any]]) -> None:
    """
    Отправляет алерты при обнаружении аномалий.

    Args:
        alerts: Словарь с результатами проверки
        current_metrics: Текущие метрики
        previous_metrics: Предыдущие метрики
    """
    if not any(alerts.values()):
        return

    logger.warning("===== ОБНАРУЖЕНЫ АНОМАЛИИ В ДАННЫХ =====")

    for metric, is_alert in alerts.items():
        if is_alert:
            current_val = current_metrics.get(metric, 'N/A')
            previous_val = previous_metrics.get(metric, 'N/A') if previous_metrics else 'N/A'
            logger.warning(f"Аномалия в метрике '{metric}': "
                           f"Текущее значение: {current_val}, Предыдущее значение: {previous_val}")

    # В реальной системе здесь могла бы быть отправка уведомления в Slack или по email
    # Например: send_slack_alert("Data Pipeline Alert", anomaly_message)
