# --- ИМПОРТ НЕОБХОДИМЫХ БИБЛИОТЕК ---

import sys  # Обычно используется для системных функций, но здесь не критичен.
import requests  # Для выполнения HTTP-запросов к API HeadHunter.
import json  # Для работы с данными в формате JSON, которые возвращает API.
import webbrowser  # Для открытия URL-адресов в браузере пользователя по умолчанию (для ссылок на вакансии).
import csv  # Для сохранения результатов в формате CSV (таблицы).
import threading  # Для создания и управления фоновыми потоками, чтобы GUI не "зависал" во время сетевых запросов.
import queue  # Для безопасной передачи данных из фонового потока в основной поток GUI.
import tkinter as tk  # Основная стандартная библиотека для GUI в Python.
from tkinter import ttk, filedialog, \
    Menu  # ttk - для стилизованных виджетов (как Treeview), filedialog - для диалогов сохранения/открытия, Menu - для верхнего меню.
import customtkinter as ctk  # Современная обертка над Tkinter для создания красивого интерфейса.


# --- БЛОК БИЗНЕС-ЛОГИКИ (не зависит от GUI) ---
# Эти функции выполняют основную работу по получению и обработке данных.

def search_vacancies_logic(query_text, area_id, filter_by_rating, min_rating, page_num=0):
    """
    Основная функция, которая отправляет запрос к API hh.ru и обрабатывает ответ.
    Она не знает о существовании GUI и просто возвращает данные.
    """
    # URL конечной точки API для поиска вакансий.
    url = "https://api.hh.ru/vacancies"
    # Параметры запроса, собранные из аргументов функции.
    params = {"text": query_text, "area": area_id, "experience": "noExperience", "employment": "full",
              "schedule": "remote", "per_page": 50, "page": page_num, "order_by": "publication_time"}
    # Заголовок User-Agent обязателен для API hh.ru, чтобы идентифицировать ваше приложение.
    headers = {"User-Agent": "MyVacancyParser/CTK_1.0 (alexamyago@gmail.com)"}
    try:
        # Выполняем GET-запрос с указанными параметрами и заголовками.
        response = requests.get(url, params=params, headers=headers)
        # Если API вернул ошибку (например, 404 или 500), эта строка вызовет исключение.
        response.raise_for_status()
        # Преобразуем тело ответа из JSON-строки в словарь Python.
        initial_data = response.json()
        # Извлекаем общее количество страниц с результатами.
        total_pages = initial_data.get('pages', 0)
        # Извлекаем список вакансий на текущей странице.
        initial_vacancies = initial_data.get('items', [])

        # Если фильтр по рейтингу не включен, просто обрабатываем каждую вакансию и возвращаем результат.
        if not filter_by_rating:
            processed_vacancies = [process_vacancy_item(item) for item in initial_vacancies]
        else:
            # Если фильтр включен, процесс усложняется.
            processed_vacancies = []
            # Создаем кэш, чтобы не запрашивать рейтинг одной и той же компании несколько раз.
            employer_ratings_cache = {}
            for item in initial_vacancies:
                # Получаем ID компании.
                employer_id = item.get('employer', {}).get('id')
                # Если у вакансии нет ID компании, пропускаем ее.
                if not employer_id: continue
                # Проверяем, запрашивали ли мы уже рейтинг этой компании.
                if employer_id in employer_ratings_cache:
                    rating = employer_ratings_cache[employer_id]
                else:
                    # Если нет, делаем дополнительный запрос к API для получения деталей о компании.
                    try:
                        emp_resp = requests.get(f"https://api.hh.ru/employers/{employer_id}", headers=headers)
                        emp_resp.raise_for_status()
                        # Извлекаем рейтинг. Если его нет, считаем его равным 0.
                        rating = emp_resp.json().get('rating', 0)
                    except requests.exceptions.RequestException:
                        rating = 0  # В случае ошибки запроса также считаем рейтинг 0.
                    # Сохраняем полученный рейтинг в кэш.
                    employer_ratings_cache[employer_id] = rating
                # Если рейтинг компании соответствует заданному минимуму, обрабатываем и добавляем вакансию.
                if rating is not None and rating >= min_rating:
                    processed_vacancies.append(process_vacancy_item(item, rating))

        # Возвращаем словарь с полной информацией: список вакансий, кол-во страниц, общее кол-во найденных.
        return {'vacancies': processed_vacancies, 'pages': total_pages, 'found': initial_data.get('found', 0)}
    # Обрабатываем возможные ошибки сети или разбора JSON.
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        # В случае ошибки возвращаем словарь с ключом 'error'.
        return {'error': f"Ошибка: {e}"}


def process_vacancy_item(item, rating=None):
    """Вспомогательная функция для форматирования данных одной вакансии в удобный словарь."""
    # Обработка информации о зарплате.
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
    # Обработка имени компании.
    emp_name = item.get('employer', {}).get('name', 'N/A')
    # Если был передан рейтинг, добавляем его к имени компании для наглядности.
    if rating is not None: emp_name = f"{emp_name} (★{rating:.1f})"
    # Возвращаем аккуратно собранный словарь с нужными нам полями.
    return {'name': item.get('name', 'N/A'), 'employer': emp_name, 'salary': salary_text,
            'url': item.get('alternate_url', '')}


# --- ОСНОВНОЙ КЛАСС ПРИЛОЖЕНИЯ (GUI) ---

class App(ctk.CTk):
    """Главный класс приложения. Наследуется от ctk.CTk, что делает его основным окном."""

    def __init__(self):
        # Вызываем конструктор родительского класса, чтобы инициализировать окно.
        super().__init__()

        # --- Настройка окна и темы ---
        self.title("Поиск вакансий на hh.ru")  # Заголовок окна.
        self.geometry("900x700")  # Начальный размер окна (ширина x высота).
        ctk.set_appearance_mode("System")  # Устанавливает тему (Светлая/Темная) в соответствии с настройками ОС.
        ctk.set_default_color_theme("blue")  # Устанавливает цветовую схему для акцентов (кнопки, чекбоксы).

        # --- Переменные состояния приложения ---
        self.area_map = {'Москва': '1', 'Санкт-Петербург': '2',
                         'Россия': '113'}  # Словарь для сопоставления названий городов с их ID в API.
        self.current_vacancies = []  # Список для хранения вакансий с текущей отображаемой страницы.
        self.current_page = 0  # Номер текущей страницы (начинается с 0).
        self.total_pages = 0  # Общее количество страниц, полученное от API.
        self.current_query_params = {}  # Словарь для хранения параметров последнего поиска (для пагинации).

        # --- Очередь для безопасного обмена данными между потоками ---
        # Рабочий поток будет класть сюда результат, а основной поток GUI - забирать.
        self.result_queue = queue.Queue()

        # --- Создание верхнего меню ("Файл" -> "Сохранить как...") ---
        self.create_menu()

        # --- Создание и размещение виджетов ---
        # Основной фрейм-контейнер, чтобы виджеты имели отступы от краев окна.
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Фрейм для элементов управления (поля ввода, кнопки).
        controls_frame = ctk.CTkFrame(container)
        controls_frame.pack(fill="x", padx=5, pady=5)

        # Виджеты размещаются с помощью сетки (.grid), что позволяет выравнивать их в строки и столбцы.
        ctk.CTkLabel(controls_frame, text="Ключевые слова:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.query_input = ctk.CTkEntry(controls_frame, width=300)  # Поле для ввода текста запроса.
        self.query_input.insert(0, "data AND python NOT aston")  # Устанавливаем текст по умолчанию.
        self.query_input.grid(row=0, column=1, padx=5, pady=5,
                              sticky="ew")  # sticky="ew" растягивает виджет по горизонтали.

        ctk.CTkLabel(controls_frame, text="Город:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.area_combo = ctk.CTkComboBox(controls_frame,
                                          values=list(self.area_map.keys()))  # Выпадающий список для выбора города.
        self.area_combo.set("Москва")  # Устанавливаем значение по умолчанию.
        self.area_combo.grid(row=0, column=3, padx=5, pady=5)

        # Чекбокс для включения/выключения фильтрации по рейтингу.
        self.filter_checkbox = ctk.CTkCheckBox(controls_frame, text="Фильтр по рейтингу (медленно)",
                                               command=self.toggle_rating_spinbox)
        self.filter_checkbox.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # Поле для ввода минимального рейтинга. Изначально неактивно.
        self.rating_spinbox = ctk.CTkEntry(controls_frame, width=60, state="disabled")
        self.rating_spinbox.insert(0, "4.0")
        self.rating_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Главная кнопка поиска.
        self.search_button = ctk.CTkButton(controls_frame, text="Найти вакансии", command=self.start_new_search)
        self.search_button.grid(row=0, column=4, rowspan=2, padx=10, pady=5,
                                sticky="ns")  # rowspan=2 - кнопка занимает две строки по высоте.

        # Настраиваем сетку так, чтобы второй столбец (с полем ввода) растягивался при изменении размера окна.
        controls_frame.grid_columnconfigure(1, weight=1)

        # --- Создание таблицы для результатов (используем стандартный ttk.Treeview) ---
        style = ttk.Style()  # Создаем объект для стилизации стандартных виджетов.
        style.theme_use("default")  # Используем тему по умолчанию как основу.
        # Настраиваем цвета Treeview, чтобы они соответствовали темной теме CustomTkinter.
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", borderwidth=0)
        style.map('Treeview', background=[('selected', '#2a2d2e')],
                  foreground=[('selected', '#1f6aa5')])  # Цвет выделенной строки.
        style.configure("Treeview.Heading", background="#565b5e", foreground="white",
                        relief="flat")  # Стиль заголовков.
        style.map("Treeview.Heading", background=[('active', '#3484D0')])  # Цвет заголовка при наведении.

        # Фрейм-контейнер для таблицы.
        tree_frame = ctk.CTkFrame(container)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Создаем сам виджет таблицы. show="headings" скрывает первый пустой столбец.
        self.tree = ttk.Treeview(tree_frame, columns=("Должность", "Компания", "Зарплата"), show="headings")
        # Устанавливаем текст для каждого заголовка.
        self.tree.heading("Должность", text="Должность")
        self.tree.heading("Компания", text="Компания")
        self.tree.heading("Зарплата", text="Зарплата")
        # Задаем начальную ширину столбцов.
        self.tree.column("Должность", width=400)
        self.tree.column("Компания", width=250)
        self.tree.column("Зарплата", width=150)

        # Размещаем таблицу внутри ее фрейма.
        self.tree.pack(side="left", fill="both", expand=True)
        # Привязываем событие "двойной клик левой кнопкой мыши" к функции открытия URL.
        self.tree.bind("<Double-1>", self.open_vacancy_url)

        # --- Виджеты пагинации (переключения страниц) ---
        pagination_frame = ctk.CTkFrame(container)
        pagination_frame.pack(fill="x", padx=5, pady=5)

        self.prev_button = ctk.CTkButton(pagination_frame, text="<< Предыдущая", command=self.load_prev_page,
                                         state="disabled")
        self.prev_button.pack(side="left", padx=10)  # side="left" прижимает кнопку к левому краю фрейма.
        self.next_button = ctk.CTkButton(pagination_frame, text="Следующая >>", command=self.load_next_page,
                                         state="disabled")
        self.next_button.pack(side="right", padx=10)  # side="right" - к правому.
        self.page_info_label = ctk.CTkLabel(pagination_frame, text="Страница 0 из 0")
        self.page_info_label.pack(side="top")  # pack без side размещает по центру.

        # --- Статус-бар внизу окна для сообщений пользователю ---
        self.status_bar = ctk.CTkLabel(self, text="Готово",
                                       anchor="w")  # anchor="w" (west) прижимает текст к левому краю.
        self.status_bar.pack(side="bottom", fill="x", padx=10)

        # --- Запуск периодической проверки очереди результатов ---
        # Это ключевой механизм для работы с потоками в Tkinter.
        self.process_queue()

    def create_menu(self):
        """Создает и настраивает верхнее меню окна."""
        menu_bar = Menu(self)  # Создаем сам объект меню.
        file_menu = Menu(menu_bar, tearoff=0)  # Создаем выпадающий пункт "Файл". tearoff=0 убирает пунктирную линию.
        # Добавляем команду "Сохранить как..." и делаем ее неактивной по умолчанию.
        self.save_menu_item = file_menu.add_command(label="Сохранить как...", command=self.save_results,
                                                    state="disabled")
        menu_bar.add_cascade(label="Файл", menu=file_menu)  # Добавляем пункт "Файл" в главное меню.
        self.config(menu=menu_bar)  # Применяем созданное меню к окну.

    def toggle_rating_spinbox(self):
        """Включает/выключает поле для ввода рейтинга в зависимости от состояния чекбокса."""
        state = "normal" if self.filter_checkbox.get() else "disabled"
        self.rating_spinbox.configure(state=state)

    def start_new_search(self):
        """Запускает совершенно новый поиск (всегда с первой страницы)."""
        # Собираем все параметры поиска с виджетов и сохраняем их.
        self.current_query_params = {
            'query': self.query_input.get(),
            'area_id': self.area_map[self.area_combo.get()],
            'filter_enabled': bool(self.filter_checkbox.get()),
            'min_rating': float(self.rating_spinbox.get()) if self.filter_checkbox.get() else 0.0
        }
        # Вызываем метод для загрузки данных для нулевой (первой) страницы.
        self.fetch_page(0)

    # Методы-обертки для кнопок пагинации.
    def load_next_page(self):
        self.fetch_page(self.current_page + 1)

    def load_prev_page(self):
        self.fetch_page(self.current_page - 1)

    def fetch_page(self, page_num):
        """Общий метод для запроса данных для любой страницы."""
        self.set_controls_enabled(False)  # Блокируем все кнопки, чтобы избежать повторных нажатий.
        self.status_bar.configure(text=f"Загрузка страницы {page_num + 1}...")  # Обновляем статус.
        params = self.current_query_params

        # Создаем и запускаем новый поток для выполнения сетевого запроса.
        # daemon=True означает, что поток завершится автоматически при закрытии программы.
        threading.Thread(
            target=self.worker_task,  # Функция, которая будет выполняться в потоке.
            args=(params['query'], params['area_id'], params['filter_enabled'], params['min_rating'], page_num),
            # Аргументы для функции.
            daemon=True
        ).start()

    def worker_task(self, query, area_id, filter_enabled, min_rating, page):
        """Эта функция выполняется в отдельном, фоновом потоке."""
        # Вызываем "тяжелую" функцию, которая делает сетевые запросы.
        result = search_vacancies_logic(query, area_id, filter_enabled, min_rating, page)
        # Кладем полученный результат (словарь) в очередь. Это потокобезопасная операция.
        self.result_queue.put((result, page))

    def process_queue(self):
        """Проверяет очередь на наличие новых результатов. Выполняется в основном потоке GUI."""
        try:
            # Пытаемся получить элемент из очереди без блокировки.
            # Если очередь пуста, get_nowait() вызовет исключение queue.Empty.
            result, page_num = self.result_queue.get_nowait()
            # Если мы что-то получили, вызываем метод для обработки этих результатов.
            self.process_results(result, page_num)
        except queue.Empty:
            # Если очередь пуста, ничего не делаем.
            pass
        finally:
            # Планируем повторный вызов этой же функции через 100 миллисекунд.
            # Это создает бесконечный цикл, который не блокирует GUI.
            self.after(100, self.process_queue)

    def process_results(self, result_data, page_num):
        """Обрабатывает полученные данные и обновляет GUI."""
        # Если в результате есть ключ 'error', показываем ошибку.
        if 'error' in result_data:
            self.status_bar.configure(text=result_data['error'])
            self.set_controls_enabled(True)  # Разблокируем кнопки.
            return

        # Обновляем переменные состояния приложения.
        self.current_page = page_num
        self.total_pages = result_data['pages']
        self.current_vacancies = result_data['vacancies']

        # Полностью очищаем таблицу от старых данных.
        for i in self.tree.get_children(): self.tree.delete(i)
        # Заполняем таблицу новыми данными.
        for vacancy in self.current_vacancies:
            # Вставляем новую строку. В iid (item id) мы хитро сохраняем URL для быстрого доступа по двойному клику.
            self.tree.insert("", "end", values=(vacancy['name'], vacancy['employer'], vacancy['salary']),
                             iid=vacancy['url'])

        # Обновляем статус-бар и элементы управления пагинацией.
        self.status_bar.configure(
            text=f"Найдено всего: {result_data['found']}. Отображена страница {self.current_page + 1}")
        self.update_pagination_controls()

    def update_pagination_controls(self):
        """Обновляет состояние кнопок, текста пагинации и меню."""
        self.set_controls_enabled(True)  # Сначала разблокируем все кнопки.
        # Затем настроим состояние кнопок "вперед/назад" в зависимости от текущей страницы.
        self.prev_button.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
        # Обновляем текст с номером страницы.
        self.page_info_label.configure(text=f"Страница {self.current_page + 1} из {self.total_pages}")

        # Активируем или деактивируем пункт меню "Сохранить как...".
        state = "normal" if self.current_vacancies else "disabled"
        # Этот сложный вызов получает доступ к меню окна и изменяет состояние его первого элемента.
        self.nametowidget(self.winfo_toplevel()).children['!menu'].children['!menu'].entryconfigure(0, state=state)

    def set_controls_enabled(self, enabled):
        """Вспомогательная функция для одновременного включения/выключения всех кнопок."""
        state = "normal" if enabled else "disabled"
        self.search_button.configure(state=state)
        self.prev_button.configure(state=state)
        self.next_button.configure(state=state)
        # Дополнительная проверка: если страниц всего одна или нет, кнопки пагинации всегда выключены.
        if self.total_pages <= 1:
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")

    def open_vacancy_url(self, event):
        """Обработчик события двойного клика по строке в таблице."""
        # Получаем id выделенной строки (в котором мы сохранили URL).
        item_id = self.tree.focus()
        # Если строка выделена и в id есть URL, открываем его в браузере.
        if item_id:
            webbrowser.open(item_id)

    def save_results(self):
        """Открывает диалог сохранения и записывает текущие результаты в файл."""
        # Вызываем стандартный диалог сохранения файла.
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")])
        # Если пользователь нажал "Отмена", file_path будет пустым.
        if not file_path: return

        try:
            # Если пользователь выбрал сохранение в CSV.
            if file_path.endswith('.csv'):
                # Открываем файл на запись. encoding='utf-8-sig' нужен для правильного отображения кириллицы в Excel.
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    # Создаем DictWriter, который может записывать словари в CSV.
                    writer = csv.DictWriter(f, fieldnames=self.current_vacancies[0].keys())
                    writer.writeheader()  # Записываем заголовки (ключи словаря).
                    writer.writerows(self.current_vacancies)  # Записываем все строки данных.
            # Если пользователь выбрал сохранение в JSON.
            elif file_path.endswith('.json'):
                # Открываем файл на запись.
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Записываем данные в JSON. ensure_ascii=False для кириллицы, indent=4 для красивого форматирования.
                    json.dump(self.current_vacancies, f, ensure_ascii=False, indent=4)
            # Сообщаем пользователю об успехе.
            self.status_bar.configure(text=f"Результаты сохранены в {file_path}")
        except Exception as e:
            # Сообщаем об ошибке.
            self.status_bar.configure(text=f"Ошибка сохранения: {e}")


# --- ТОЧКА ВХОДА В ПРОГРАММУ ---
if __name__ == "__main__":
    # Создаем экземпляр нашего главного класса приложения.
    app = App()
    # Запускаем главный цикл обработки событий Tkinter.
    # Эта строка заставляет окно появиться и реагировать на действия пользователя.
    # Программа будет находиться в этом цикле до тех пор, пока окно не будет закрыто.
    app.mainloop()
