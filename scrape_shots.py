from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
logger = logging.getLogger(__name__)
import pandas as pd


def main():
    # robots_res = requests.get('http://tulospalvelu.fliiga.com/robots.txt')
    # print(robots_res.status_code, "\n")
    # print(robots_res.content)

    # res = requests.get("https://tulospalvelu.fliiga.com/match/868713/shotmap")
    # soup = BeautifulSoup(res.content, 'html.parser')
    # print(res.status_code, "\n")
    # # print(res.content)
    # print(soup.prettify())

    logging.basicConfig(filename='sabastats.log', level=logging.INFO)
    logger.info(f'Starting {__name__}')

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1200")

    logger.info('Starting Chrome')
    driver = webdriver.Chrome(options=options)
    url = 'https://tulospalvelu.fliiga.com/match/868713/events'
    logger.info(f'Requesting page {url}')
    driver.get(url)

    # the page renders shot locations as elements with the CSS class
    # "shot-spot".  the previous selector treated it as a tag name and used
    # `find_element` which returns a single element and throws
    # NoSuchElementError when nothing is found.  instead we query for all
    # matching elements (note the leading dot for a class selector) and wait
    # until they appear so the javascript has a chance to populate them.

    # Click the Laukaisukartta button first to get the correct page.
    logger.info('Clicking Laukaisukartta.')
    wait = WebDriverWait(driver, 5)
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='tablist'] a.v-tab[href*='shotmap']"))
    ).click()

    logger.info('Getting Team names.')
    try:
        team_names = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located(By.CSS_SELECTOR, '.teamname')
        )
    except Exception:
        logger.error(f'Team names not found {url}')
        team_names = ['A', 'B']
    
    team_A, team_B = team_names

    logger.info('Selecting all shot-spot type elements.')
    try:
        shot_spots = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.shot-spot'))
        )
    except Exception:
        logger.error(f'No elements of type shot-spot found in {url}.')
        shot_spots = []

    shot_list = []

    for shot_spot in shot_spots:
        if shot_spot.text == 'XX':
            continue

        shot_spot_class = shot_spot.get_attribute('class').split()
        shot_outcome = shot_spot_class[2]
        shot_team = shot_spot_class[1]

        if shot_team == 'team_A':
            team_name = team_A
        elif shot_team == 'team_B':
            team_name = team_B
        else:
            logger.error('Failed to parse team A or B from shot-spot class.')
            team_name = 'Unkown'

        spot_style = shot_spot.get_attribute('style').split()
        x_coordinate = float(spot_style[1][:-2])
        y_coordinate = float(spot_style[3][:-2])
        # Origin is top left, coordinates as percentages of field size.
        # Style is in format: 'left: XX.XX%; top: YY.YY%;'

        shot_list.append({
            'Match': url,
            'Team name': team_name,
            'Player number': shot_spot.text,
            'Shot outcome': shot_outcome,
            'X-coordinate': x_coordinate,
            'Y-coordinate': y_coordinate
        })
        print(shot_spot.text, shot_spot.get_attribute('style'), shot_spot.get_attribute('class'))

    df = pd.DataFrame(shot_list)
    

    logger.info('Quitting Chrome')
    driver.quit()
    logger.info('Program finished.')

if __name__ == "__main__":
    main()