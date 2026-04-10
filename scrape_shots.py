from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import logging
logger = logging.getLogger(__name__)
from datetime import date
import csv
import pandas as pd

MATCH_FOLDER = 'match_folder'

def analyse_goal_popup(driver, shot_spot):
    logger.info('Shot was a goal, analyse the shot target.')

    print('\n')
    return [0,0]




def scrape_match_page(driver, url, date, team_A, team_B, save_to_file=True):
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
    shot_spots = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.shot-spot'))
    )

    shot_list = []
    shot_popup_set = set()

    for shot_spot in shot_spots:
        if shot_spot.text == 'XX':
            continue

        shot_spot_class = shot_spot.get_attribute('class').split()
        shot_outcome = shot_spot_class[2]
        if shot_outcome == 'shot_goal':
            driver.execute_script("""
                const el = arguments[0];
                for (const type of ['mouseenter','mouseover','mousemove']) {
                    const evt = new MouseEvent(type, {bubbles: true, cancelable: true, view: window});
                    el.dispatchEvent(evt);
                }
                """, shot_spot)
            shot_popups = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".shot-goal-placement")))
            for popup in shot_popups:
                if popup not in shot_popup_set:
                    shot_popup = popup
                    shot_popup_set.add(popup)
                    break
            popup_style = shot_popup.get_attribute('style')
            popup_style = popup_style.split(':')
            shot_x = float(popup_style[1][:-7])
            shot_y = float(popup_style[2][:-3])
        else:
            shot_x, shot_y = [-1, -1]

        shot_team = shot_spot_class[1]

        spot_style = shot_spot.get_attribute('style').split()
        x_coordinate = float(spot_style[1][:-2]) * 0.4
        y_coordinate = float(spot_style[3][:-2]) * 0.2
        # Origin is top left, coordinates as percentages of field size.
        # Style is in format: 'left: XX.XX%; top: YY.YY%;'

        if shot_team == 'team_A':
            team_name = team_A
        elif shot_team == 'team_B':
            team_name = team_B
            # Mirror all shots.
            x_coordinate = 40 - x_coordinate
            y_coordinate = 20 - y_coordinate
        else:
            logger.error('Failed to parse team A or B from shot-spot class.')
            team_name = 'Unkown'

        shot_list.append({
            'Match': game_id,
            'date': date,
            'Team name': team_name,
            'Player number': shot_spot.text,
            'Shot outcome': shot_outcome,
            'X': x_coordinate,
            'Y': y_coordinate,
            'Goal_X': shot_x,
            'Goal_Y': shot_y
        })
        # print(shot_spot.text, shot_spot.get_attribute('style'), shot_spot.get_attribute('class'))

    logger.info('Creating dataframe from list of dictionaries.')

    output_file = f'{MATCH_FOLDER}/{date.year}-{date.year + 1}/{team_A}_{team_B}_{date.year}_{date.month}_{date.day}'
    match save_to_file:
        case 'parquet':
            output_file = output_file + '.parquet'
            logger.info(f'Writing dataframe to parquet file {output_file}')
            pd.DataFrame(shot_list).to_parquet(output_file)
        case False:
            logger.info('Not saving the dataframe to any file.')
        case _:
            keys = shot_list[0].keys()
            output_file = output_file + '.csv'
            logger.info(f'Writing dataframe to csv {output_file}')
            with open(output_file, 'w') as f:
                dict_writer = csv.DictWriter(f, keys)
                dict_writer.writeheader()
                dict_writer.writerows(shot_list)
    
    logger.info('scrape_match_page finished.')



def scrape_entire_season(driver, url='https://tulospalvelu.fliiga.com/matches/402!sb2025'):
    logger.info(f'Starting execution of scrape_entire_season.')

    logger.info('Connecting to:' + url)
    driver.get(url)

    logger.info('Gathering all match elements.')
    matches = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.outerrow'))
    )
    
    for match in matches:
        match_info = match.text.split('\n')
        if len(match_info) > 7:
            date_str, _time, _venue, team_A, score, _ja, team_B, _ottelukeskus = match_info
        else:
            date_str, _time, _venue, team_A, score, team_B, _ottelukeskus = match_info

        if len(score) <= 1:
            continue

        # print(match_info)

        if len(date_str) < 9:
            date_str = date_str.split()[1][:-1].split('.')
            d = date(date.today().year, int(date_str[1]), int(date_str[0]))
        else:
            date_str = date_str.split('.')
            d = date(int(date_str[2]), int(date_str[1]), int(date_str[0]))

        match_url = 'https://tulospalvelu.fliiga.com/match/' + match.get_attribute('matchid') + '/events'
        scrape_match_page(driver, match_url, d, team_A, team_B, True)
        # print(f'{team_A} - {team_B} {d.day}.{d.month}.{d.year}\n')





def main():
    logging.basicConfig(filename='sabastats.log', level=logging.INFO)
    logger.info(f'Starting {__name__}')

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1200")

    logger.info('Starting Chrome')
    driver = webdriver.Chrome(options=options)
    url = 'https://tulospalvelu.fliiga.com/match/868713/events'
    scrape_match_page(driver, url, date(2025, 1, 1), 'a', 'b', 'parquet') # For testing.
    # scrape_entire_season(driver)

    logger.info('Quitting Chrome')
    driver.quit()
    logger.info('Program finished.')
    

if __name__ == "__main__":
    main()