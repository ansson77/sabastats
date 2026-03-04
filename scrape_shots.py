from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
logger = logging.getLogger(__name__)
import pandas as pd
from datetime import date

MATCH_FOLDER = 'match_folder'


def scrape_match_page(driver, url, date, team_A, team_B, save_to_csv=True) -> pd.DataFrame:
    game_id = url.split('/')[-2]
    logger.info(f'Requesting page {url}')
    driver.get(url)

    # the page renders shot locations as elements with the CSS class
    # "shot-spot".  the previous selector treated it as a tag name and used
    # `find_element` which returns a single element and throws
    # NoSuchElementError when nothing is found.  instead we query for all
    # matching elements (note the leading dot for a class selector) and wait
    # until they appear so the javascript has a chance to populate them.

    # logger.info('Getting Team names.')
    # try:
    #     team_names = WebDriverWait(driver, 5).until(
    #         EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.teamname'))
    #         )
    # except Exception as e:
    #     logger.error(f'Team names not found from {url}. Errorcode: {e}')
    #     team_A, team_B = ['A', 'B']
    
    # else:
    #     team_A = team_names[0].text
    #     team_B = team_names[1].text
    #     logger.info(f'Teamnames that were found were A: {team_A}, B: {team_B}')


    logger.info('Clicking Laukaisukartta.')
    wait = WebDriverWait(driver, 5)
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='tablist'] a.v-tab[href*='shotmap']"))
    ).click()

    logger.info('Selecting all shot-spot type elements.')
    try:
        shot_spots = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.shot-spot'))
        )
    except Exception as e:
        logger.error(f'No elements of type shot-spot found in {url}. Errorcode: {e}')
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
            'Match': game_id,
            'Team name': team_name,
            'Player number': shot_spot.text,
            'Shot outcome': shot_outcome,
            'X-coordinate': x_coordinate,
            'Y-coordinate': y_coordinate
        })
        # print(shot_spot.text, shot_spot.get_attribute('style'), shot_spot.get_attribute('class'))

    logger.info('Creating dataframe from list of dictionaries.')
    df = pd.DataFrame(shot_list)

    if save_to_csv:
        output_file = f'{MATCH_FOLDER}/{team_A}_{team_B}_{date.year}_{date.month}_{date.day}.csv'
        logger.info(f'Writing dataframe to {output_file}')
        df.to_csv(output_file)
    
    logger.info('scrape_match_page finished.')
    return df

def scrape_entire_season(driver, url='https://tulospalvelu.fliiga.com/matches/402!sb2025', season_start_year='2025'):
    logger.info(f'Starting execution of scrape_entire_season. Will scrape all matches from season {season_start_year}.')

    logger.info('Connecting to:' + url)
    driver.get(url)

    logger.info('Gathering all match elements.')
    try:
        matches = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.outerrow'))
        )
    except Exception as e:
        logger.error(f'Failed to find match elements: {e}')
        return None
    
    for match in matches:
        match_info = match.text.split('\n')
        if len(match_info) < 7:
            continue
        elif len(match_info) >7:
            date_str, _time, _venue, team_A, _score, _ja, team_B, _ottelukeskus = match_info
        else:
            date_str, _time, _venue, team_A, _score, team_B, _ottelukeskus = match_info
        print(match_info)
        date_str = date_str.split('.')
        d = date(int(date_str[2]), int(date_str[1]), int(date_str[0]))
        match_url = 'https://tulospalvelu.fliiga.com/match/' + match.get_attribute('matchid') + '/events'
        # df = scrape_match_page(driver, match_url, d, team_A, team_B, True)
        print(f'{team_A} - {team_B} {d.day}.{d.month}.{d.year}\n')




def main():
    logging.basicConfig(filename='sabastats.log', level=logging.INFO)
    logger.info(f'Starting {__name__}')

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1200")

    logger.info('Starting Chrome')
    driver = webdriver.Chrome(options=options)
    url = 'https://tulospalvelu.fliiga.com/match/868713/events'
    # scrape_match_page(driver, url)
    scrape_entire_season(driver)

    logger.info('Quitting Chrome')
    driver.quit()
    logger.info('Program finished.')
    

if __name__ == "__main__":
    main()