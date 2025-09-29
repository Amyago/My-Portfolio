from selenium.webdriver.common.by import By

LOCATORS = {
    "home_page": {
        "search_input": {
            "prod": (By.ID, "searchInput"),
            "test": (By.ID, "searchInput")
        },
        "search_button": {
            "prod": (By.CSS_SELECTOR, "button[type='submit']"),
            "test": (By.CSS_SELECTOR, "button[type='submit']")
        }
    }
}
