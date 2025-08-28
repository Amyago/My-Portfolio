import pytest
import pandas as pd
from datetime import datetime, timedelta
from etl.transform import (
    calculate_purchase_frequency,
    calculate_average_check,
    calculate_time_since_last_action,
    calculate_item_popularity,
    calculate_category_preferences
)


# Фикстура для тестовых данных о покупках
@pytest.fixture
def sample_purchases():
    dates = [
        datetime.now() - timedelta(days=5),
        datetime.now() - timedelta(days=10),
        datetime.now() - timedelta(days=35),
        datetime.now() - timedelta(days=2)
    ]

    return pd.DataFrame({
        'user_id': [1, 1, 2, 1],
        'item_id': [101, 102, 201, 103],
        'timestamp': dates,
        'amount': [1000, 1500, 2000, 500],
        'category': ['electronics', 'electronics', 'books', 'clothing']
    })


# Фикстура для тестовых данных со всеми событиями
@pytest.fixture
def sample_all_data():
    now = datetime.now()
    return pd.DataFrame({
        'user_id': [1, 1, 2, 2, 3],
        'item_id': [101, 102, 201, 202, 301],
        'timestamp': [
            now - timedelta(hours=1),
            now - timedelta(days=2),
            now - timedelta(days=5),
            now - timedelta(weeks=1),
            now - timedelta(hours=30)
        ],
        'event_type': ['view', 'purchase', 'cart', 'purchase', 'view']
    })


def test_calculate_purchase_frequency(sample_purchases):
    # Тест за 30 дней (должно быть 2 покупки для user_id=1)
    freq = calculate_purchase_frequency(sample_purchases, '30D')
    assert len(freq) == 2  # 2 пользователя с покупками за 30 дней
    assert freq[freq['user_id'] == 1]['purchase_frequency'].values[0] == 2
    assert freq[freq['user_id'] == 2]['purchase_frequency'].values[0] == 1


def test_calculate_average_check(sample_purchases):
    avg_check = calculate_average_check(sample_purchases)
    assert len(avg_check) == 2  # 2 пользователя
    assert avg_check[avg_check['user_id'] == 1]['average_check'].values[0] == 1000  # (1000+1500+500)/3
    assert avg_check[avg_check['user_id'] == 2]['average_check'].values[0] == 2000


def test_calculate_time_since_last_action(sample_all_data):
    result = calculate_time_since_last_action(sample_all_data)
    assert len(result) == 3  # 3 пользователя

    # Проверка для user_id=1 (последнее действие 1 час назад)
    hours_1 = result[result['user_id'] == 1]['hours_since_last_action'].values[0]
    assert 0.9 <= hours_1 <= 1.1  # Должно быть около 1 часа

    # Проверка для user_id=2 (последнее действие 1 неделя назад)
    hours_2 = result[result['user_id'] == 2]['hours_since_last_action'].values[0]
    assert 167 <= hours_2 <= 169  # Должно быть около 168 часов (7 дней)


def test_calculate_item_popularity(sample_purchases):
    popularity = calculate_item_popularity(sample_purchases)
    assert len(popularity) == 4  # 4 уникальных товара
    assert popularity[popularity['item_id'] == 101]['popularity_score'].values[0] == 1


def test_calculate_category_preferences(sample_purchases):
    preferences = calculate_category_preferences(sample_purchases)
    assert len(preferences) == 2  # 2 пользователя

    # Пользователь 1 чаще покупает в категории electronics
    assert preferences[preferences['user_id'] == 1]['top_category'].values[0] == 'electronics'

    # Пользователь 2 покупает только в категории books
    assert preferences[preferences['user_id'] == 2]['top_category'].values[0] == 'books'


def test_empty_purchases():
    empty_df = pd.DataFrame(columns=['user_id', 'item_id', 'timestamp', 'amount', 'category'])

    # Все функции должны обрабатывать пустой DataFrame без ошибок
    assert calculate_purchase_frequency(empty_df).empty
    assert calculate_average_check(empty_df).empty
    assert calculate_item_popularity(empty_df).empty
    assert calculate_category_preferences(empty_df).empty
