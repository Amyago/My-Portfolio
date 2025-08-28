import pandas as pd
import json
import tempfile
import os
from monitoring import (
    check_data_quality,
    detect_data_drift,
    load_previous_metrics
)


def test_data_quality_check():
    # Тест с валидными данными
    valid_df = pd.DataFrame({
        'user_id': [1, 2, 3],
        'item_id': [101, 102, 103],
        'timestamp': pd.date_range(start='2023-01-01', periods=3)
    })
    assert check_data_quality(valid_df) == True

    # Тест с пропущенными значениями в критической колонке
    invalid_df = valid_df.copy()
    invalid_df.loc[0, 'user_id'] = None
    assert check_data_quality(invalid_df) == False

    # Тест с пустым DataFrame
    empty_df = pd.DataFrame(columns=['user_id', 'item_id', 'timestamp'])
    assert check_data_quality(empty_df) == False


def test_data_drift_detection():
    current_metrics = {
        'avg_purchase_frequency': 2.5,
        'avg_check': 1500,
        'user_count': 10000
    }

    previous_metrics = {
        'avg_purchase_frequency': 2.0,
        'avg_check': 1000,
        'user_count': 9000
    }

    # Пороги: 20% для частоты, 30% для чека, 10% для пользователей
    thresholds = {
        'avg_purchase_frequency': 0.2,
        'avg_check': 0.3,
        'user_count': 0.1
    }

    alerts = detect_data_drift(current_metrics, previous_metrics, thresholds)

    # avg_purchase_frequency: (2.5-2.0)/2.0 = 25% > 20% -> алерт
    assert alerts['avg_purchase_frequency'] == True

    # avg_check: (1500-1000)/1000 = 50% > 30% -> алерт
    assert alerts['avg_check'] == True

    # user_count: (10000-9000)/9000 = 11.1% > 10% -> алерт
    assert alerts['user_count'] == True


def test_load_previous_metrics():
    # Создаем временный файл с метриками
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_path = os.path.join(tmpdir, "monitoring_metrics.json")

        # Записываем тестовые метрики
        test_metrics = {
            'avg_purchase_frequency': 2.0,
            'avg_check': 1000,
            'user_count': 9000
        }
        with open(metrics_path, 'w') as f:
            json.dump(test_metrics, f)

        # Загружаем метрики
        loaded_metrics = load_previous_metrics(tmpdir)
        assert loaded_metrics == test_metrics

        # Проверка обработки отсутствующего файла
        os.remove(metrics_path)
        assert load_previous_metrics(tmpdir) is None
