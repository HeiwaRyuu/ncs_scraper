## Selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
## Functionalities
import pandas as pd
import time
import datetime as dt
import dateutil.relativedelta as relativedelta
import numpy as np
import os
from send_wpp_msg import generate_send_wpp_msg
from send_email_all_songs import send_mail
## Credentials
import config
## Multithread
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_hour_minute():
    now = dt.datetime.now()
    if now.minute < 60:
        hour = now.hour
        minute = now.minute + 1
    else:
        if hour < 24:
            hour = now.hour + 1
            minute = 0
        else:
            hour = 0
            minute = 0

    return hour, minute


def fetch_channel(url):
    split_lst = url.split('/')
    channel_name = split_lst[3]

    if '@' in channel_name:
        channel_name = channel_name.replace('@','')

    return channel_name


def parse_release_date_to_date(row):
    date_dict = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sept':9, 'Oct':10, 'Nov':11, 'Dec':12}
    date_str = row['release_date']

    if "Premiered on" in date_str:
        date_str = date_str[len("Premiered on")+1:]


    splt_date_info = date_str.split(' ')

    print(f"date_str -> {date_str}")
    year = int(splt_date_info[2])
    month = int(date_dict[splt_date_info[1]])
    day = int(splt_date_info[0])

    date = dt.datetime(year, month, day)

    row['birthday'] = date

    return row


def find_all(string, find_str):
    string = string[:]
    start = 0
    positions = []
    while True:
        pos = string.find(find_str, start)
        if pos == -1:
            return positions
        if not positions:
            positions.append(pos)
        else:
            if pos != positions[-1]:
                positions.append(pos)
        start += 1


def fetch_aria_label_info(position, string):
    string = string[:]
    if position != -1:
        cut_str = string[:position]
        spaces_pos_list = find_all(cut_str, " ")
        start_index = spaces_pos_list[-2]
        end_index = position
        result_str  = string[(start_index + 1):(end_index - 1)] ## +1 and -1 to remove spaces
        result_str = result_str.replace(',', '')
        result_str = result_str.replace('.', '')
    else:
        result_str = np.nan

    return float(result_str)


def calculate_pos(string, lst):
    for check in lst:
        position = string.find(check)
        if position != -1:
            return position
    return position


def treat_aria_label(row, channel_name):
    by_str = f'by {channel_name}'
    start = row['aria_label'].find(by_str)+ len(by_str)
    string = row['aria_label'][start:]
    
    print(f"string -> {string}")
    years_pos = calculate_pos(string, ['year', 'years'])
    months_pos = calculate_pos(string, ['month', 'months'])
    weeks_pos = calculate_pos(string, ['week', 'weeks'])
    days_pos = calculate_pos(string, ['day', 'days'])
    hours_pos = calculate_pos(string, ['hour', 'hours'])
    minutes_pos = calculate_pos(string, ['minute', 'minutes'])
    seconds_pos = calculate_pos(string, ['second', 'seconds'])
    views_pos = calculate_pos(string, ['view', 'views'])

    years = fetch_aria_label_info(years_pos, string)
    months = fetch_aria_label_info(months_pos, string)
    weeks = fetch_aria_label_info(weeks_pos, string)
    days = fetch_aria_label_info(days_pos, string)
    hours = fetch_aria_label_info(hours_pos, string)
    minutes = fetch_aria_label_info(minutes_pos, string)
    seconds = fetch_aria_label_info(seconds_pos, string)
    views = fetch_aria_label_info(views_pos, string)

    row['years'] = years
    row['months'] = months
    row['weeks'] = weeks
    row['days'] = days
    row['hours'] = hours
    row['minutes'] = minutes
    row['seconds'] = seconds
    row['views'] = views

    return row

def calculate_posted_date(row):
    today = dt.datetime.today()
    date = today

    if row['seconds'] == row['seconds']:
        date = date - relativedelta.relativedelta(seconds=row['seconds'])
    if row['hours'] == row['hours']:
        date = date - relativedelta.relativedelta(hours=row['hours'])
    if row['days'] == row['days']:
        date = date - relativedelta.relativedelta(days=row['days'])
    if row['weeks'] == row['weeks']:
        date = date - relativedelta.relativedelta(days=(row['weeks']*14))
    if row['months'] == row['months']:
        date = date - relativedelta.relativedelta(months=row['months'])
    if row['years'] == row['years']:
        date = date - relativedelta.relativedelta(years=row['years'])

    row['calculated_release_date'] = date

    return row

def filter_to_birthday(df):

    return df


def generate_dataframe(list_of_titles, list_of_urls, list_of_aria_lables, channel_name, filename):
    previous_urls = 'None'
    ## Creating a URL release date with only those which have not been updated yet
    print("Searching for previous dataframe...")
    try:
        df_previous = pd.read_excel(filename)
        previous_urls = list(set(list_of_urls) - set(df_previous['url'].tolist()))
    except:
        df_previous = pd.DataFrame()
        print("There is no previous dataframe for the Channel Name, we will be updating the release date for the whole channel...")

    data_dict = {'title':list_of_titles, 'url':list_of_urls, 'aria_label':list_of_aria_lables}
    df = pd.DataFrame(data_dict)
    df = df.dropna(subset=['url'])
    ## Parsing aria_label and adding infos to the columns
    df = df.apply(lambda row: treat_aria_label(row, channel_name), axis=1)
    ## Calculating release date based on approx youtube info to compare with the correct release date
    df = df.apply(lambda row: calculate_posted_date(row), axis=1)
    ## Creating a list of urls to use in the multitrhead scraper
    ## If None, there is no previous dataframe, fetch everything
    if previous_urls == 'None':
        url_list = df['url'].to_list()
    ## If not None and theres Data, fetch missing Data
    elif previous_urls and previous_urls != 'None':
        url_list = previous_urls
    ## If not None, and No Data, already up to date, don't need to fetch anything
    else:
        url_list = []

    print(f"url_list -> {url_list}")

    if url_list:
        ## Using an aux dataframe so we can merge the information in the correct order
        df_aux = return_df_release_date(url_list)
        df_aux = pd.merge(df_aux, df, on=['url'], how='left')
        columns = ['title', 'release_date', 'url']
        print(df_aux)
        df_aux = df_aux[columns]
        ## Just checking the output
        # df_aux.to_excel('df_aux_check.xlsx', index=False)

        df = df[df['url'].isin(df_aux['url'].to_list())].copy()
        try:
            df = df.drop(columns=['release_date'])
        except Exception as e:
            print(f"Excessão ao dropar coluna release_date -> {e}")
            
        df_res = pd.merge(df, df_aux, on=['url'], how='left')

        # df_previous.to_excel('dataframe_completo_antes_do_concat.xlsx', index=False)
        # df_res.to_excel('df_res.xlsx', index=False)
    
        if not df_previous.empty:
            try:
                df_previous = pd.concat([df_res, df_previous], ignore_index=True)
            except:
                df_previous['release_date'] = ''
                df_previous = pd.concat([df_res, df_previous], ignore_index=True)

            df_previous = df_previous.drop_duplicates(subset=['url'], keep='first')

            df = df_previous.copy()
        else:
            df = df_res.copy()
    else:
        df_aux = pd.DataFrame()

    ## Parsing the release dfate string into actual date values
    df = df.apply(lambda row: parse_release_date_to_date(row), axis=1)

    return df, df_aux

def fetch_channel_videos_infos(url):
    ## Defining options for the driver
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--start-maximized")
    options.add_argument("--headless")

    # Context manager
    with webdriver.Chrome(options=options) as browser:
        browser.get(url)
        delay = 3 # seconds
        ## Waiting until video contents show up
        WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.ID, 'video-title-link')))

        ## Scrolling to the end of page
        SCROLL_PAUSE_TIME = 0.5
        # Get scroll height -> using document.documentElement.scrollHeight instead of document.body.scrollHeight because it returns 0 on youtube beacause of some floating web elements
        last_height = browser.execute_script("return document.documentElement.scrollHeight")
        while True:
            # Scroll down to bottom
            height = browser.execute_script("return document.documentElement.scrollHeight")
            browser.execute_script(f"window.scrollTo(0, {str(height)});")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = browser.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                print("Reached end of page...")
                break
            last_height = new_height

        
        elements = browser.find_elements(By.ID, "video-title-link")

        list_of_titles, list_of_urls, list_of_aria_lables = ([] for _ in range (3))

        print("Adding element infos to the lists...")
        for element in elements:
            list_of_titles.append(element.get_attribute('title'))
            list_of_urls.append(element.get_attribute('href'))
            list_of_aria_lables.append(element.get_attribute('aria-label'))

        print('Closing browser...')
        browser.close()

    return list_of_titles, list_of_urls, list_of_aria_lables

def collect_songs(url, channel_name, filename):
    print("Generating dataframe...")
    list_of_titles, list_of_urls, list_of_aria_lables = fetch_channel_videos_infos(url)
    df, df_new = generate_dataframe(list_of_titles, list_of_urls, list_of_aria_lables, channel_name, filename)
    ## Exporting to excel
    df.to_excel(filename, index=False)
    
    print("Finished collecting data... Scraping Script Ended with SUCCESS state!")

    return filename, df_new


def fetch_release_date(url):
    max_tries = 5

    while max_tries >= 1:
        try:
            ## Defining options for the driver
            options = webdriver.ChromeOptions()
            options.add_argument("start-maximized")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--proxy-server='direct://'")
            options.add_argument("--proxy-bypass-list=*")
            options.add_argument("--start-maximized")
            options.add_argument("--headless")
            # Context manager
            with webdriver.Chrome(options=options) as browser:
                browser.get(url)
                delay = 10 # seconds
                ## Waiting until video contents show up
                element = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.XPATH, "/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[3]/div[1]")))
                print(f"element.text -> {element.text}")
                element.click()

                element = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.XPATH, "/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[3]/div[1]/div/div/yt-formatted-string/span[3]")))
                print(f"element.text -> {element.text}")

                release_date = element.text

                browser.close()

                return [release_date, url]
        except Exception as e:
            print(f"Excessão ao coletar: {url} ->\nExcessão == {e}")
            max_tries -= 1
        
    release_date = None
    return [release_date, url]


def return_df_release_date(url_list):
    try:
        url_list_aux = []
        date_list = []
        future_list = []
        list_count = len(url_list)
        if list_count != 0:
            with ThreadPoolExecutor(max_workers=5) as executor:
                for index in range(list_count):
                    future_list.append(executor.submit(fetch_release_date, url_list[index]))
                for future in as_completed(future_list):
                    return_value = future.result()
                    print(f"return_value -> {return_value}\nok")
                    date_list.append(return_value[0])
                    url_list_aux.append(return_value[1])
    except Exception as e:
        print(f'Exception on collecting release date -> {e}')
    dict_data = {'release_date':date_list, 'url':url_list_aux}
    df_aux = pd.DataFrame(dict_data)
    df_aux = df_aux.dropna(subset=['url'])

    return df_aux


def fetch_date_from_filename(filename):
    filename = "nocopyrightsounds-2023-03-22.xlsx"
    start = len("nocopyrightsounds-")
    end = filename.find(".xlsx")
    date_str = filename[start:end]
    date_infos = date_str.split('-')
    year = int(date_infos[0])
    month = int(date_infos[1])
    day = int(date_infos[2])

    date = dt.datetime(year, month, day)

    return date

 

def main():
    start = time.time()

    date = dt.datetime.today().date()
    url="https://www.youtube.com/@NoCopyrightSounds/videos"
    channel_name = fetch_channel(url=url)
    filename = f"{channel_name.lower()}.xlsx"
    filename, df_new = collect_songs(url=url, channel_name=channel_name, filename=filename)
    ## Sending Email
    recipients = ['vitor.carvalho.ufu@gmail.com']
    send_mail(filename=filename, recipients=recipients, channel_name=channel_name, date=date)
    ## Sending Whatsapp Message
    generate_send_wpp_msg(df=df_new)

    end = time.time() - start
    print(f'script time -> {end}')


if __name__ == "__main__":
    main()