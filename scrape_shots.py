import requests
from bs4 import BeautifulSoup
from selenium import webdriver


def main():
    # robots_res = requests.get('http://tulospalvelu.fliiga.com/robots.txt')
    # print(robots_res.status_code, "\n")
    # print(robots_res.content)

    # res = requests.get("https://tulospalvelu.fliiga.com/match/868713/shotmap")
    # soup = BeautifulSoup(res.content, 'html.parser')
    # print(res.status_code, "\n")
    # # print(res.content)
    # print(soup.prettify())


    driver = webdriver.Chrome()
    driver.get('https://tulospalvelu.fliiga.com/match/868713/shotmap')

    print(driver.title)
    driver.implicitly_wait(1.5)

    driver.quit()


if __name__ == "__main__":
    main()