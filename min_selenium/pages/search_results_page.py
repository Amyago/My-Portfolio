from pages.base_page import BasePage
from pages.search_results_page import SearchResultsPage
from selenium.webdriver.support import expected_conditions as EC


class WikipediaHomePage(BasePage):
    PAGE_NAME = "home_page"  # Логическое имя самой страницы
    PAGE_TITLE_TEXT = "Wikipedia"  # Это остается для проверок

    # --- Локаторы заменены на логические имена ---
    SEARCH_INPUT = "search_input"
    SEARCH_BUTTON = "search_button"

    def __init__(self, driver, base_url, env):
        super().__init__(driver, base_url, env)

    def open(self):
        super().open("/")
        self.wait.until(EC.title_contains(self.PAGE_TITLE_TEXT))
        return self

    def search_for(self, text: str) -> SearchResultsPage:
        # --- Используем хелперы с логическими именами ---
        search_field = self._find_visible_element(self.PAGE_NAME, self.SEARCH_INPUT)
        search_field.clear()
        search_field.send_keys(text)
        self._click_element(self.PAGE_NAME, self.SEARCH_BUTTON)
        # Передаем env дальше, если потребуется
        return SearchResultsPage(self.driver, self.base_url, self.env, text)

    def is_title_correct(self) -> bool:
        return self.PAGE_TITLE_TEXT in self.get_page_title()
