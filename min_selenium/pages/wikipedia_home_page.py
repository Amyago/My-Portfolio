from pages.base_page import BasePage
from selenium.webdriver.support import expected_conditions as EC


class SearchResultsPage(BasePage):

    # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
    # 1. Добавляем 'env: str' в сигнатуру конструктора.
    def __init__(self, driver, base_url: str, env: str, search_term: str):
        # 2. Передаем 'env' в конструктор родительского класса.
        super().__init__(driver, base_url, env)
        # Уникальная логика для этой страницы: дождаться загрузки
        self.wait.until(EC.title_contains(search_term))
