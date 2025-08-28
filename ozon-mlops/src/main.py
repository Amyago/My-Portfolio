import argparse
import logging
import os
import sys
from datetime import datetime
from etl.extract import load_all_data
from etl.transform import merge_data, generate_features
from etl.load import save_features
from monitoring.monitoring import (
    check_data_quality,
    load_previous_metrics,
    detect_data_drift,
    send_alerts
)

# Настройка базового логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("etl_pipeline")


def main(input_dir: str, output_dir: str, config_path: str = None):
    """
    Основная функция ETL-пайплайна.

    Args:
        input_dir: Каталог с сырыми данными
        output_dir: Каталог для сохранения обработанных данных
        config_path: Путь к конфигурационному файлу (опционально)
    """
    start_time = datetime.now()
    logger.info("===== ЗАПУСК ETL-ПАЙПЛАЙНА ДЛЯ РЕКОМЕНДАТЕЛЬНОЙ СИСТЕМЫ =====")

    try:
        # 1. Загрузка данных
        logger.info("Этап 1: Загрузка данных")
        data_paths = {
            'views': os.path.join(input_dir, 'views.csv'),
            'purchases': os.path.join(input_dir, 'purchases.csv'),
            'cart': os.path.join(input_dir, 'cart.csv')
        }
        raw_data = load_all_data(data_paths)

        # 2. Проверка качества сырых данных
        logger.info("Этап 2: Проверка качества данных")
        for name, df in raw_data.items():
            if not check_data_quality(df):
                logger.error(f"Данные {name} не прошли проверку качества")
                # В реальной системе здесь могло бы быть решение о продолжении или прерывании
                # Например, можно продолжить с предупреждением или остановить пайплайн

        # 3. Объединение и трансформация данных
        logger.info("Этап 3: Объединение и трансформация данных")
        all_data = merge_data(raw_data)
        features = generate_features(all_data)

        # 4. Проверка качества сгенерированных фич
        logger.info("Этап 4: Проверка качества сгенерированных фич")
        # Проверяем пользовательские фичи
        for feature_name, df in features['user_features'].items():
            if not df.empty:
                check_data_quality(df, critical_columns=['user_id'])

        # 5. Мониторинг и обнаружение аномалий
        logger.info("Этап 5: Мониторинг и обнаружение аномалий")
        previous_metrics = load_previous_metrics(output_dir)
        current_metrics = {}

        # Собираем текущие метрики из сгенерированных фич
        if 'purchase_frequency' in features['user_features']:
            pf = features['user_features']['purchase_frequency']
            current_metrics['user_count'] = len(pf)
            current_metrics['avg_purchase_frequency'] = pf['purchase_frequency'].mean()

        if 'average_check' in features['user_features']:
            ac = features['user_features']['average_check']
            current_metrics['avg_check'] = ac['average_check'].mean()

        if 'popularity' in features['item_features']:
            pop = features['item_features']['popularity']
            current_metrics['item_count'] = len(pop)
            current_metrics['avg_popularity'] = pop['popularity_score'].mean()

        # Обнаружение дрейфа данных
        alerts = detect_data_drift(current_metrics, previous_metrics)
        send_alerts(alerts, current_metrics, previous_metrics)

        # 6. Сохранение результатов
        logger.info("Этап 6: Сохранение результатов")
        save_features(features, output_dir)

        # Завершение
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"ETL-пайплайн успешно завершен за {duration:.2f} секунд")
        logger.info("===============================================")

    except Exception as e:
        logger.exception("Критическая ошибка в ETL-пайплайне")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ETL pipeline for Ozon recommendation system')
    parser.add_argument('--input-dir', type=str, required=True,
                        help='Каталог с сырыми данными (CSV файлы)')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Каталог для сохранения обработанных данных')
    parser.add_argument('--config', type=str, default=None,
                        help='Путь к конфигурационному файлу (опционально)')

    args = parser.parse_args()

    main(args.input_dir, args.output_dir, args.config)
