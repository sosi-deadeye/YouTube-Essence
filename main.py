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

options = Options()
options.headless = True
# driver = webdriver.Chrome(executable_path=ChromeDriverManager.install(), chrome_options=options)
driver = webdriver.Firefox(
    executable_path=GeckoDriverManager().install(), options=options
)
channel_url = ""
channelName = ""


def make_soup(url):
    try:
        response = requests.get(url)
        return BeautifulSoup(response.content, "html.parser")
    except:
        print("An error occurred. Cannot proceed...")
        exit(-1)


def validate_channel_url(link):
    global driver

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
        exit(-1)

    if driver.current_url == "https://www.youtube.com/error?src=404":
        print("Non existent channel")
        return False
    return True


def get_channel_from_user():
    global channel_url
    channel_url = input("Enter the channel's url: ").strip()
    while not validate_channel_url(channel_url):
        channel_url = input("Enter the channel's url: ").strip()
    return channel_url


def retrieve_all_videos(link):
    global driver
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
        print("External connection occured. Try again later.")
        exit(-1)


def download_video(video_link):
    try:

        # Specifying an API key is optional
        # , as pafy includes one. However,
        # it is prefered that software calling pafy provides it’s own API key,
        # and the default may be removed in the future.
        pafy.set_api_key(yourApiKey)
        youtube_video = pafy.new(video_link)

        stream = youtube_video.getbest(preftype="mp4")
        stream.download()
        print(youtube_video.title, " downloaded...")
    except OSError:  # if the video is labeled as private, then an error would occur and we won't be able to extract it
        pass


def main():
    global channel_url
    global channelName
    global driver
    channel_url = get_channel_from_user().strip("/")
    try:
        channelName = make_soup(channel_url).get("title")

    except TimeoutException:
        print("This is taking too long, unable to proceed...")
        exit(-1)

    channelName = driver.title.replace("- YouTube", "").strip()
    print("Channel ", channelName, " retrieved successfully....")
    all_videos_urls = retrieve_all_videos(channel_url)

    print("Channel contains ", len(all_videos_urls), " videos.")
    user_choice = input("Want to download them all or abort? Y/N ")

    while user_choice.upper() not in ["Y", "N"]:
        user_choice = input("Wrong choice. Download all or abort ? Y/N ")

    if user_choice.upper() == "N":
        print("Ciao")
        exit(0)
    else:
        if os.path.exists(channelName):
            shutil.rmtree(channelName)  # delete directory with its contents
        os.mkdir(channelName)
        os.chdir(channelName)
        for videoUrl in all_videos_urls:
            download_video(videoUrl)

        driver.quit()

        print("Finished!")


main()
