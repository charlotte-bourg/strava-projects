import pytest
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture
def browser():
    # Initialize Selenium WebDriver
    driver = webdriver.Chrome(ChromeDriverManager(chrome_type='google').install())
    yield driver
    # Teardown: close the browser window after tests
    driver.quit()

def test_home_page(browser):
    # Open the home page of your Flask app
    browser.get('http://localhost:5000')

    # Example: Verify page title
    assert browser.title == 'Your Flask App Title'

    # Example: Find an element and verify its text
    welcome_message = browser.find_element_by_css_selector('h1').text
    assert welcome_message == 'Welcome to Your Flask App'

    # TODO more assertions 