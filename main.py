import os
import re
import shutil
import time

import pafy
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
YOUTUBE_BASE_URL = "https://www.youtube.com/"


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
    link = link.strip("/") + "/videos"
    try:
        driver.get(link)
        time.sleep(5)
        scroll_pause_time = 1
        screen_height = driver.execute_script(
            "return window.screen.height;"
        )  # get the screen height of the web
        i = 1

        while True:

            # scroll one screen height each time
            driver.execute_script(
                "window.scrollTo(0, {screen_height}*{i});".format(
                    screen_height=screen_height, i=i
                )
            )
            i += 1
            time.sleep(scroll_pause_time)
            # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
            scroll_height = driver.execute_script(
                "return document.documentElement.scrollHeight"
            )

            # Break the loop when the height we need to scroll to is larger than the total scroll height
            if screen_height * i > scroll_height:
                break

        videos_page_soup = BeautifulSoup(driver.page_source, "html.parser")

        all_as = videos_page_soup.findAll("a", attrs={"id": "thumbnail"})
        videos_urls = []
        for A in all_as:
            try:
                videos_urls.append(YOUTUBE_BASE_URL.strip("/") + A["href"])

            except KeyError:
                pass

        return videos_urls
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


def main():
    options = Options()
    options.headless = True
    # driver = webdriver.Chrome(executable_path=ChromeDriverManager.install(), chrome_options=options)
    driver = webdriver.Firefox(
        executable_path=GeckoDriverManager().install(), options=options
    )
    channel_url = ""
    channelName = ""

    channel_url = get_channel_from_user()
    try:
        channel_name = make_soup(channel_url).get("title")
    except TimeoutException:
        print("This is taking too long, unable to proceed...")
        return 1

    channel_name = driver.title.replace("- YouTube", "").strip()
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
            download_video(video_url)

    driver.quit()
    print("Finished!")


if __name__ == "__main__":
    main()
