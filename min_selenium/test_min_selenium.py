from pages.wikipedia_home_page import WikipediaHomePage


# Тесты теперь принимают фикстуру env
def test_wikipedia_search(driver, base_url, env):
    home_page = WikipediaHomePage(driver, base_url, env)
    home_page.open()

    search_term = "Selenium"
    results_page = home_page.search_for(search_term)

    results_title = results_page.get_page_title()
    assert search_term in results_title


def test_page_title(driver, base_url, env):
    wiki_page = WikipediaHomePage(driver, base_url, env)
    wiki_page.open()

    assert wiki_page.is_title_correct(), "Заголовок главной страницы некорректен"
