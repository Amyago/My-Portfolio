import pytest
from selenium import webdriver

def pytest_addoption(parser):
    """Добавляет опции командной строки в pytest."""
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="Choose browser: chrome or firefox"
    )
    parser.addoption(
        "--base-url",
        action="store",
        default="https://www.wikipedia.org/",
        help="Specify the base URL for the tests"
    )
    # --- НОВАЯ ОПЦИЯ ---
    parser.addoption(
        "--env",
        action="store",
        default="prod",
        help="Specify environment: prod or test"
    )

@pytest.fixture(scope="module")
def driver(request):
    """Фикстура-фабрика для создания драйвера."""
    browser_name = request.config.getoption("browser")

    if browser_name.lower() == "chrome":
        driver = webdriver.Chrome()
    elif browser_name.lower() == "firefox":
        # Убедитесь, что у вас установлен geckodriver
        driver = webdriver.Firefox()
    else:
        raise pytest.UsageError("--browser should be chrome or firefox")

    yield driver

    driver.quit()

@pytest.fixture(scope="module")
def base_url(request):
    """Фикстура для получения базового URL из командной строки."""
    return request.config.getoption("--base-url")

# --- НОВАЯ ФИКСТУРА ---
@pytest.fixture(scope="module")
def env(request):
    """Фикстура для получения окружения из командной строки."""
    return request.config.getoption("env")
