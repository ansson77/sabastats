import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    # robots_res = requests.get('http://tulospalvelu.fliiga.com/robots.txt')
    # print(robots_res.status_code, "\n")
    # print(robots_res.content)

    # res = requests.get("https://tulospalvelu.fliiga.com/match/868713/shotmap")
    # soup = BeautifulSoup(res.content, 'html.parser')
    # print(res.status_code, "\n")
    # # print(res.content)
    # print(soup.prettify())

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1200")

    driver = webdriver.Chrome(options=options)
    driver.get('https://tulospalvelu.fliiga.com/match/868713/shotmap')
    driver.implicitly_wait(5.0)

    # soup = BeautifulSoup(driver.page_source, 'html.parser')
    # the page renders shot locations as elements with the CSS class
    # "shot-spot".  the previous selector treated it as a tag name and used
    # `find_element` which returns a single element and throws
    # NoSuchElementError when nothing is found.  instead we query for all
    # matching elements (note the leading dot for a class selector) and wait
    # until they appear so the javascript has a chance to populate them.


    try:
        shot_spots = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.shot-spot'))
        )
    except Exception:
        shot_spots = []

    for shot_spot in shot_spots:
        print(shot_spot.text)


    driver.quit()


if __name__ == "__main__":
    main()