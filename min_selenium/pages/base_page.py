from selenium.common import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.locators import LOCATORS

class BasePage:
    """
    Базовый класс, содержащий общие методы и свойства для всех страниц.
    """
    # Принимаем base_url в конструкторе
    # Принимаем env в конструкторе
    def __init__(self, driver, base_url: str, env: str):
        self.driver = driver
        self.base_url = base_url
        self.env = env  # Сохраняем окружение
        self.wait = WebDriverWait(driver, 10)

    def _get_locator(self, page_name: str, logical_name: str):
        """
        Получает физический локатор из хранилища по логическому имени и окружению.
        """
        try:
            return LOCATORS[page_name][logical_name][self.env]
        except KeyError:
            raise Exception(
                f"Локатор для '{logical_name}' на странице '{page_name}' для окружения '{self.env}' не найден!")

    def open(self, uri: str = "/"):
        """Открывает URL, состоящий из base_url и относительного пути uri."""
        url = self.base_url + uri.lstrip('/')
        self.driver.get(url)

    def get_page_title(self) -> str:
        """Возвращает заголовок текущей страницы."""
        return self.driver.title

    # --- Методы-хелперы теперь принимают page_name и logical_name ---
    def _find_visible_element(self, page_name: str, logical_name: str):
        locator = self._get_locator(page_name, logical_name)
        try:
            return self.wait.until(EC.visibility_of_element_located(locator))
        except TimeoutException:
            raise AssertionError(f"Элемент '{logical_name}' с локатором {locator} не стал видимым.")

    def _click_element(self, page_name: str, logical_name: str):
        locator = self._get_locator(page_name, logical_name)
        try:
            element = self.wait.until(EC.element_to_be_clickable(locator))
            element.click()
        except TimeoutException:
            raise AssertionError(f"Элемент '{logical_name}' с локатором {locator} не стал кликабельным.")
