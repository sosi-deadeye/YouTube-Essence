"""
Describe here what your program does.
"""

import json
import re
import shutil
import time
from itertools import count
from pathlib import Path
from typing import Any, Optional

import pafy
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
YOUTUBE_BASE_URL = "https://www.youtube.com"
YOUTUBE_404 = "https://www.youtube.com/error?src=404"
CHANNEL_URL = re.compile(
    r"^((http|https)://)(www\.)youtube\.com/(channel/|user/|c/)[a-zA-Z0-9\-]+$"
)
PAFY_API = Path.home() / ".pafy-api.json"


def validate_channel_url(link: str) -> bool:
    """
    Validate the channel url.

    :param link:
    :return: True if channel url is valid
    """
    if link is None:
        return False
    if not CHANNEL_URL.match(link):
        print("Wrong channel URL")
        print("Try including the whole URL starting by http/https...")
        return False
    try:
        driver.get(link)
    except TimeoutException:
        print("This is taking too long, unable to proceed...")
        return False

    if driver.current_url == YOUTUBE_404:
        print("Non existent channel")
        return False
    return True


def get_channel_from_user() -> str:
    """
    Retrieve channel url from user via standard input
    :return:
    """
    channel_url = None
    while not validate_channel_url(channel_url):
        channel_url = input("Enter the channel's url: ").strip()
    return channel_url


def retrieve_all_videos(link: str) -> list[str]:
    """
    Retrieve all video links from a given youtube channel url
    """
    link += "/videos"
    try:
        driver.get(link)
        time.sleep(5)
        scroll_pause_time = 1
        screen_height = driver.execute_script("return window.screen.height;")
        for index in count(1):
            driver.execute_script(f"window.scrollTo(0, {screen_height}*{index});")
            time.sleep(scroll_pause_time)
            scroll_height = driver.execute_script(
                "return document.documentElement.scrollHeight"
            )
            if screen_height * index > scroll_height:
                break

        return [
            url
            for tag in driver.find_elements_by_css_selector("#video-title")
            if (url := tag.get_attribute("href"))
        ]
    except ConnectionRefusedError:
        print("External connection occurred. Try again later.")
        return []


def download_video(
    video_link: str, video_dir: Path, api_key: Optional[str] = None
) -> None:
    """
    :param video_link:
    :param video_dir:
    :param api_key:
    :return:

    Specifying an API key is optional, as pafy includes one. However,
    it is preferred that software calling pafy provides it’s own API key,
    and the default may be removed in the future.
    """
    try:
        if api_key is not None:
            pafy.set_api_key(api_key)
        youtube_video = pafy.new(video_link)

        stream = youtube_video.getbest(preftype="mp4")
        # https://github.com/mps-youtube/pafy/blob/develop/pafy/backend_shared.py#L630
        stream.download(video_dir)
        print(youtube_video.title, " downloaded...")
    except OSError:
        pass


def ask(question: str, choices: dict[str, Any] = None) -> Any:
    """
    Function to ask the user a question.
    The choices are the keys of the mapping.
    The return value is the mapping to the key

    :param question: Message shown to user
    :param choices: Mapping choice : return value
    :return:
    """
    if choices is None:
        choices = {"Y": True, "N": False}
    while (choice := input(question).upper()) not in choices:
        print("Invalid input:", choice)
        print("Please choose:", ", ".join(choices))
    return choices[choice]


def get_pafy_api_key() -> Optional[str]:
    """
    Function to obtain API Key for pafy
    :return:
    """
    if PAFY_API.exists():
        print("Reading pafy api_key from", PAFY_API)
        data = json.loads(PAFY_API.read_text())
    else:
        data = {"API_KEY": input("Please input pafy_api_key (leve empty for None): ")}
        print("Writing api_key to", PAFY_API)
        PAFY_API.write_text(json.dumps(data))
    return data.get("API_KEY")


def main(api_key: Optional[str] = None):
    channel_url = get_channel_from_user()
    try:
        driver.get(channel_url)
        channel_name = driver.title.removesuffix(" - YouTube")
    except TimeoutException:
        print("This is taking too long, unable to proceed...")
        return 1

    print(f"Channel {channel_name} retrieved successfully....")

    all_videos_urls = retrieve_all_videos(channel_url)
    print(f"Channel contains {len(all_videos_urls)} videos.")

    if not ask("Want to download them all or abort? Y/N "):
        print("Ciao")
    else:
        channel_directory = Path(channel_name)
        if channel_directory.exists() and ask(
            f"Channel directory {channel_directory} exists. Delete it? "
        ):
            shutil.rmtree(channel_directory)
        channel_directory.mkdir(exist_ok=True)
        for video_url in all_videos_urls:
            download_video(video_url, video_dir=channel_directory, api_key=api_key)

    print("Finished!")


if __name__ == "__main__":
    pafy_api_key = get_pafy_api_key()
    options = Options()
    options.headless = True
    chrome_exe = ChromeDriverManager().install()
    with webdriver.Chrome(executable_path=chrome_exe, options=options) as driver:
        main(api_key=pafy_api_key)
