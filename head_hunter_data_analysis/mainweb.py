# --- ИМПОРТ БИБЛИОТЕК ---

# Импортируем ключевые компоненты из фреймворка Flask:
# Flask - основной класс для создания веб-приложения.
# render_template - функция для генерации HTML-страниц из шаблонов.
# request - объект для доступа к данным входящего HTTP-запроса (например, данным из формы).
from flask import Flask, render_template, request

# Импортируем библиотеку для выполнения HTTP-запросов к внешним API (в нашем случае, hh.ru).
import requests
# Импортируем библиотеку для работы с форматом JSON.
import json


# --- БЛОК СУЩЕСТВУЮЩЕЙ БИЗНЕС-ЛОГИКИ ---
# Эти функции скопированы из десктопной версии. Они не зависят от интерфейса (веб или десктоп).

def search_vacancies_logic(query_text, area_id, filter_by_rating, min_rating, page_num=0):
    """Основная функция, которая отправляет запрос к API hh.ru и обрабатывает ответ."""
    # URL API для поиска вакансий.
    url = "https://api.hh.ru/vacancies"
    # Словарь с параметрами для GET-запроса. Flask передаст их в URL (например, ?text=python&area=1).
    # Мы уменьшили per_page до 20, так как на веб-странице лучше отображать меньше элементов, чем в десктопной таблице.
    params = {"text": query_text, "area": area_id, "experience": "noExperience", "employment": "full",
              "schedule": "remote", "per_page": 20, "page": page_num, "order_by": "publication_time"}
    # Заголовок User-Agent, обязательный для API hh.ru, чтобы идентифицировать наше приложение.
    headers = {"User-Agent": "MyVacancyParser/WEB_1.0 (alexamyago@gmail.com)"}
    # Используем блок try...except для обработки возможных ошибок сети или API.
    try:
        # Выполняем GET-запрос к API с нашими параметрами и заголовками.
        response = requests.get(url, params=params, headers=headers)
        # Эта строка вызовет ошибку (исключение), если сервер вернул код статуса, указывающий на проблему (например, 404, 500).
        response.raise_for_status()
        # Преобразуем ответ в формате JSON в словарь Python.
        initial_data = response.json()
        # Безопасно извлекаем общее количество страниц (если ключа 'pages' нет, вернется 0).
        total_pages = initial_data.get('pages', 0)
        # Безопасно извлекаем список вакансий.
        initial_vacancies = initial_data.get('items', [])

        # Если фильтр по рейтингу в форме не был отмечен...
        if not filter_by_rating:
            # ...просто обрабатываем каждую вакансию и создаем итоговый список.
            processed_vacancies = [process_vacancy_item(item) for item in initial_vacancies]
        else:
            # Если фильтр включен, выполняем более сложную логику.
            processed_vacancies = []
            employer_ratings_cache = {}  # Кэш, чтобы не запрашивать рейтинг одной компании дважды.
            # Проходим по каждой вакансии из первоначального списка.
            for item in initial_vacancies:
                employer_id = item.get('employer', {}).get('id')  # Безопасно получаем ID компании.
                if not employer_id: continue  # Если ID нет, пропускаем вакансию.
                if employer_id in employer_ratings_cache:
                    rating = employer_ratings_cache[employer_id]  # Используем кэшированное значение.
                else:
                    # Если рейтинга в кэше нет, делаем дополнительный запрос к API.
                    try:
                        emp_resp = requests.get(f"https://api.hh.ru/employers/{employer_id}", headers=headers)
                        emp_resp.raise_for_status()
                        rating = emp_resp.json().get('rating', 0)  # Безопасно получаем рейтинг.
                    except requests.exceptions.RequestException:
                        rating = 0  # В случае ошибки присваиваем рейтинг 0.
                    employer_ratings_cache[employer_id] = rating  # Сохраняем результат в кэш.
                # Если рейтинг компании соответствует условию, добавляем вакансию в результат.
                if rating is not None and rating >= min_rating:
                    processed_vacancies.append(process_vacancy_item(item, rating))

        # Возвращаем словарь с результатами, который будет легко использовать в HTML-шаблоне.
        return {'vacancies': processed_vacancies, 'pages': total_pages, 'found': initial_data.get('found', 0)}
    # Если произошла ошибка сети или ошибка при разборе JSON...
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        # ...возвращаем словарь с описанием ошибки.
        return {'error': f"Ошибка: {e}"}


def process_vacancy_item(item, rating=None):
    """Вспомогательная функция для форматирования данных одной вакансии в удобный словарь."""
    # Обрабатываем зарплату, чтобы представить ее в виде красивой строки.
    salary = item.get('salary');
    salary_text = "Не указана"
    if salary:
        s_from, s_to, curr = salary.get('from'), salary.get('to'), salary.get('currency', '')
        if s_from and s_to:
            salary_text = f"{s_from} - {s_to} {curr}"
        elif s_from:
            salary_text = f"от {s_from} {curr}"
        elif s_to:
            salary_text = f"до {s_to} {curr}"
    # Получаем имя работодателя.
    emp_name = item.get('employer', {}).get('name', 'N/A')
    # Если рейтинг был получен, добавляем его к имени.
    if rating is not None: emp_name = f"{emp_name} (★{rating:.1f})"
    # Возвращаем готовый словарь.
    return {'name': item.get('name', 'N/A'), 'employer': emp_name, 'salary': salary_text,
            'url': item.get('alternate_url', '')}


# --- НАСТРОЙКА И ЛОГИКА ВЕБ-ПРИЛОЖЕНИЯ FLASK ---

# Создаем экземпляр приложения Flask. `__name__` помогает Flask определить корневой путь проекта.
app = Flask(__name__)

# Выносим словарь городов в глобальную константу для удобства доступа.
AREA_MAP = {'Москва': '1', 'Санкт-Петербург': '2', 'Россия': '113'}


# Декоратор `@app.route` связывает URL-адрес ('/') с функцией `index`.
# `methods=['GET', 'POST']` разрешает этой функции обрабатывать как обычную загрузку страницы (GET), так и отправку данных из формы (POST).
@app.route('/', methods=['GET', 'POST'])
def index():
    # Инициализируем переменные. `results` будет хранить результаты поиска.
    results = None
    # `search_params` будет хранить параметры, введенные пользователем, чтобы "запомнить" их.
    search_params = {}

    # Проверяем, был ли запрос сделан методом POST (то есть, была ли отправлена форма поиска).
    if request.method == 'POST':
        # `request.form.get()` - это безопасный способ получить данные из отправленной формы.
        # Если поля нет, он вернет None или значение по умолчанию.
        query = request.form.get('query', 'python')  # Получаем значение из поля с `name="query"`.
        area_name = request.form.get('area', 'Москва')  # Получаем значение из поля с `name="area"`.
        # Для чекбокса: если он отмечен, `request.form.get('filter_enabled')` вернет 'on'. Мы сравниваем это значение.
        filter_enabled = request.form.get('filter_enabled') == 'on'
        # Получаем значение рейтинга и преобразуем его в число с плавающей точкой.
        min_rating = float(request.form.get('min_rating', 4.0))
        # Получаем номер страницы и преобразуем его в целое число.
        page = int(request.form.get('page', 0))

        # Сохраняем все полученные параметры в словарь. Это нужно, чтобы снова отобразить их в форме на странице результатов.
        search_params = {
            'query': query,
            'area': area_name,
            'filter_enabled': filter_enabled,
            'min_rating': min_rating,
            'page': page
        }

        # Вызываем нашу основную функцию-парсер, передавая ей данные из формы.
        results = search_vacancies_logic(query, AREA_MAP[area_name], filter_enabled, min_rating, page)

    # `render_template` генерирует HTML-страницу из файла `index.html` (который Flask ищет в папке `templates`).
    # Мы передаем в шаблон переменные, которые сможем использовать внутри HTML.
    return render_template('index.html',
                           areas=AREA_MAP.keys(),  # Передаем список названий городов для выпадающего меню.
                           results=results,  # Передаем результаты поиска (или None, если поиска еще не было).
                           search_params=search_params)  # Передаем параметры поиска для заполнения полей формы.


# Стандартная конструкция в Python. Этот код выполнится только тогда, когда файл `app.py` запускается напрямую.
if __name__ == '__main__':
    # `app.run()` запускает встроенный веб-сервер Flask, который начинает слушать запросы.
    # `debug=True` включает режим отладки: сервер будет автоматически перезагружаться при изменениях в коде,
    # и в браузере будут отображаться подробные страницы с ошибками.
    app.run(debug=True)
