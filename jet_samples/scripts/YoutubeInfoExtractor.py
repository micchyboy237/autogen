import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import timedelta


class YouTubeInfoExtractor:
    def __init__(self, video_url):
        self.video_url = video_url

    def extract_info(self):
        chrome_options = Options()
        # Add headless option to run Chrome in the background
        chrome_options.add_argument("--headless")
        with webdriver.Chrome(options=chrome_options) as driver:
            driver.get(self.video_url)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".ytd-watch-info-text #tooltip"))
                )
                chapters = []
                chapter_elements = driver.find_elements(
                    By.CSS_SELECTOR, "#details #endpoint")
                duration_element = driver.find_element(
                    By.CSS_SELECTOR, ".ytp-time-display .ytp-time-duration")
                end_str = duration_element.get_attribute('textContent').strip()
                # Total video duration in seconds
                video_duration = parse_time(end_str)

                for i, chapter in enumerate(chapter_elements):
                    # parent_element is one up from chapter
                    parent_element = chapter.find_element(By.XPATH, "..")
                    title_element = chapter.find_element(By.TAG_NAME, "h4")
                    if title_element:
                        title = title_element.get_attribute('title')
                        time_element = parent_element.find_element(
                            By.ID, "time")
                        start_time_str = time_element.get_attribute(
                            'textContent')
                        start_time = parse_time(start_time_str)

                        # Determine chapter end time
                        if i < len(chapter_elements) - 1:
                            # For all but the last chapter, end time is the start time of the next chapter
                            next_chapter_element = chapter_elements[i + 1]
                            next_parent_element = next_chapter_element.find_element(
                                By.XPATH, "..")
                            next_time_element = next_parent_element.find_element(
                                By.ID, "time")
                            next_start_time_str = next_time_element.get_attribute(
                                'textContent')
                            # Decrement by 1 second to avoid overlap
                            end_time = parse_time(next_start_time_str) - 1

                        # Check if chapter title already exists
                        if title not in [c['chapter_title'] for c in chapters]:
                            chapters.append({
                                'chapter_start': str(timedelta(seconds=start_time)),
                                'chapter_end': str(timedelta(seconds=end_time)),
                                'chapter_title': title
                            })

                # Replace the last chapter's end time with the video duration
                duration = str(timedelta(seconds=video_duration))
                if chapters:
                    chapters[-1]['chapter_end'] = duration

                video_id = driver.find_element(
                    By.CSS_SELECTOR, "meta[content='7qr6DK6P0uQ'").get_attribute('content').strip()
                video_title = driver.find_element(
                    By.CSS_SELECTOR, ".ytp-title").get_attribute('textContent').strip()
                video_info_strings = driver.find_element(
                    By.CSS_SELECTOR, ".ytd-watch-info-text #tooltip").get_attribute('textContent').strip()
                view_count, date_posted, trending_description = [
                    info.strip() for info in video_info_strings.strip().split('•')]

                channel_name = driver.find_element(
                    By.CSS_SELECTOR, "#header-text #title").get_attribute('textContent').strip()
                subscriber_count = driver.find_element(
                    By.CSS_SELECTOR, "#header-text #subtitle").get_attribute('textContent').strip()
                subscriber_count = parse_subscriber_count(
                    subscriber_count)
                return {
                    "id": video_id,
                    'title': video_title,
                    'duration': duration,
                    'channel_name': channel_name,
                    'subscriber_count': subscriber_count,
                    'view_count': view_count,
                    'trending_description': trending_description,
                    'chapters': chapters,
                    'date_posted': date_posted,
                }
            except TimeoutException:
                print("Timeout waiting for chapters to load.")
                return {}


def parse_subscriber_count(subscriber_str):
    # Remove the word 'subscribers' and strip extra whitespace
    num_part = subscriber_str.split()[0].strip()
    multiplier = 1

    if 'K' in num_part:
        multiplier = 1000
        num_part = num_part.replace('K', '')
    elif 'M' in num_part:
        multiplier = 1000000
        num_part = num_part.replace('M', '')

    # Convert the number part to float and multiply by the multiplier, then convert to int
    return int(float(num_part) * multiplier)


def parse_time(time_str):
    parts = time_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def time_str_to_seconds(time_str):
    """Converts a time string in HH:MM:SS or MM:SS format to seconds."""
    parts = time_str.split(":")
    # Convert time parts to integers: hours, minutes, and seconds
    parts = [int(part) for part in parts]
    if len(parts) == 3:  # HH:MM:SS format
        hours, minutes, seconds = parts
    elif len(parts) == 2:  # MM:SS format
        hours = 0  # Assume 0 hours if not provided
        minutes, seconds = parts
    else:  # Handle unexpected format
        raise ValueError(f"Unexpected time format: {time_str}")

    # Calculate total seconds
    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    return total_seconds


def get_chapter_title_by_start_and_end_time(chapters, start_time, end_time):
    for chapter in chapters:
        start_time = int(start_time)
        end_time = int(end_time)
        chapter_start = int(chapter['chapter_start'])
        chapter_end = int(chapter['chapter_end'])
        if end_time >= chapter_start and end_time <= chapter_end:
            return chapter['chapter_title']
    return None


def save_data_as_json(data, file_name):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Saved to {file_name}")


if __name__ == "__main__":
    video_url = 'https://www.youtube.com/watch?v=7qr6DK6P0uQ'

    extractor = YouTubeInfoExtractor(video_url)
    info = extractor.extract_info()

    print(f"Results\n{json.dumps(info, indent=2)}")
