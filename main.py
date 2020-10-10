import os
import re
import shutil
import time
from urllib.parse import urljoin

import pafy
import requests
from itertools import count
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options

# from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager

CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
YOUTUBE_BASE_URL = "https://www.youtube.com"


def make_soup(url):
    try:
        response = requests.get(url)
        return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"An error occurred. Cannot proceed... {repr(e)}")


def validate_channel_url(link):
    if link is None:
        return False
    if (
        re.match(
            r"^((http|https)://)(www\.)youtube\.com/(channel/|user/|c/)[a-zA-Z0-9\-]+$",
            link,
        )
        is None
    ):
        print("Wrong channel URL")
        print("Try including the whole URL starting by http/https...")
        return False
    try:
        driver.get(link)
    except TimeoutException:
        print("This is taking too long, unable to proceed...")
        driver.quit()

    if driver.current_url == "https://www.youtube.com/error?src=404":
        print("Non existent channel")
        return False
    return True


def get_channel_from_user():
    channel_url = None
    while not validate_channel_url(channel_url):
        channel_url = input("Enter the channel's url: ").strip()
    return channel_url


def retrieve_all_videos(link):
    link = urljoin(link, "videos")
    try:
        driver.get(link)
        time.sleep(5)
        scroll_pause_time = 1
        screen_height = driver.execute_script(
            "return window.screen.height;"
        )

        for i in count(1):
            driver.execute_script(
                "window.scrollTo(0, {screen_height}*{i});".format(
                    screen_height=screen_height, i=i
                )
            )
            time.sleep(scroll_pause_time)
            scroll_height = driver.execute_script(
                "return document.documentElement.scrollHeight"
            )
            if screen_height * i > scroll_height:
                break

        videos_page_soup = BeautifulSoup(driver.page_source, "html.parser")
        all_a_tags = videos_page_soup.findAll("a", attrs={"id": "thumbnail"})
        return [
            urljoin(YOUTUBE_BASE_URL, href)
            for tag in all_a_tags
            if (href := tag.get("href"))
        ]
    except ConnectionRefusedError:
        print("External connection occurred. Try again later.")


def download_video(video_link, api_key=None):
    """
    :param video_link:
    :param api_key:
    :return:

    Specifying an API key is optional
    , as pafy includes one. However,
    it is preferred that software calling pafy provides it’s own API key,
    and the default may be removed in the future.
    """
    try:
        if api_key is not None:
            pafy.set_api_key(api_key)
        youtube_video = pafy.new(video_link)

        stream = youtube_video.getbest(preftype="mp4")
        stream.download()
        print(youtube_video.title, " downloaded...")
    except OSError:
        pass


def main(api_key=None):
    channel_url = get_channel_from_user()
    try:
        channel_name = make_soup(channel_url).get("title")
    except TimeoutException:
        print("This is taking too long, unable to proceed...")
        return 1

    print("Channel ", channel_name, " retrieved successfully....")
    all_videos_urls = retrieve_all_videos(channel_url)

    print("Channel contains ", len(all_videos_urls), " videos.")
    user_choice = input("Want to download them all or abort? Y/N ")

    while user_choice.upper() not in ["Y", "N"]:
        user_choice = input("Wrong choice. Download all or abort ? Y/N ")

    if user_choice.upper() == "N":
        print("Ciao")
    else:
        if os.path.exists(channel_name):
            shutil.rmtree(channel_name)
        os.mkdir(channel_name)
        os.chdir(channel_name)
        for video_url in all_videos_urls:
            download_video(video_url, api_key=None)

    driver.quit()
    print("Finished!")


if __name__ == "__main__":
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(
        executable_path=ChromeDriverManager().install(), options=options
    )
    # todo: ApyKey from json file
    #       testing
    main()
