import pandas as pd
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


def save_features(features: Dict[str, Any], output_dir: str) -> None:
    """
    Сохраняет сгенерированные фичи в Parquet формате.

    Args:
        features: Словарь с фичами
        output_dir: Каталог для сохранения результатов
    """
    logger.info(f"Сохранение результатов в {output_dir}")

    # Создаем каталог, если он не существует
    os.makedirs(output_dir, exist_ok=True)

    # Сохранение пользовательских фич
    user_features_dir = os.path.join(output_dir, "user_features")
    os.makedirs(user_features_dir, exist_ok=True)

    for feature_name, df in features['user_features'].items():
        if not df.empty:
            file_path = os.path.join(user_features_dir, f"{feature_name}.parquet")
            df.to_parquet(file_path, index=False)
            logger.info(f"Сохранено {len(df)} записей в {file_path}")

    # Сохранение товарных фич
    item_features_dir = os.path.join(output_dir, "item_features")
    os.makedirs(item_features_dir, exist_ok=True)

    for feature_name, df in features['item_features'].items():
        if not df.empty:
            file_path = os.path.join(item_features_dir, f"{feature_name}.parquet")
            df.to_parquet(file_path, index=False)
            logger.info(f"Сохранено {len(df)} записей в {file_path}")

    # Сохранение метрик для мониторинга
    save_monitoring_metrics(features, output_dir)


def save_monitoring_metrics(features: Dict[str, Any], output_dir: str) -> None:
    """
    Сохраняет ключевые метрики для последующего мониторинга.

    Args:
        features: Сгенерированные фичи
        output_dir: Каталог для сохранения метрик
    """
    metrics = {}

    # Собираем ключевые метрики
    if 'purchase_frequency' in features['user_features']:
        pf = features['user_features']['purchase_frequency']
        metrics['avg_purchase_frequency'] = pf['purchase_frequency'].mean()
        metrics['user_count'] = len(pf)

    if 'average_check' in features['user_features']:
        ac = features['user_features']['average_check']
        metrics['avg_check'] = ac['average_check'].mean()

    if 'popularity' in features['item_features']:
        pop = features['item_features']['popularity']
        metrics['item_count'] = len(pop)
        metrics['avg_popularity'] = pop['popularity_score'].mean()

    # Сохраняем метрики в JSON для последующего использования
    import json
    metrics_path = os.path.join(output_dir, "monitoring_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Сохранены метрики мониторинга в {metrics_path}")
