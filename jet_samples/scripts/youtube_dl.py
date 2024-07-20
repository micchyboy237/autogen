import json
import os
import yt_dlp
from YouTubeInfoExtractor import (
    YouTubeInfoExtractor,
    parse_time,
    time_str_to_seconds,
    get_chapter_title_by_start_and_end_time,
    save_data_as_json
)


def download_audio(video_url: str, audio_dir: str, audio_format: str = 'mp3') -> str:
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': '320',
        }],
        'outtmpl': audio_dir + '/audio.%(ext)s',
    }

    print(f"Downloading audio from {video_url}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            audio_file = ydl.prepare_filename(info_dict).replace(
                'webm', audio_format).replace('m4a', audio_format)
            return audio_file
    except Exception as e:
        print(f"Failed to download audio: {e}")
        return None


def transcribe_youtube_video(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    extractor = YouTubeInfoExtractor(video_url)
    results = extractor.extract_info()
    channel_name = results.get('channel_name')
    chapters = results.get('chapters')

    model_size = 'medium'
    model = WhisperModel(model_size)
    downloader = YoutubeChapterDownloader()

    if not chapters:
        raise Exception(
            "No chapters found in this video or failed to fetch video content.")

    # snake case the channel name
    channel_name = "_".join(channel_name.split()).lower()
    audio_dir = f'data/scrapers/audio/youtube/{channel_name}/{video_id}'
    os.makedirs(audio_dir, exist_ok=True)
    info_file_name = f"{audio_dir}/info.json"

    # Check if info.json already exists
    if not os.path.exists(info_file_name):
        os.makedirs(os.path.dirname(info_file_name), exist_ok=True)

        save_data_as_json(results, info_file_name)
        print(f"Video info saved to {info_file_name}")
    else:
        print(f"Info already exists at {info_file_name}")

    chapter_audio_items = downloader.split_youtube_chapters(
        audio_dir, video_url, chapters)

    chapter_transcriptions = []

    audio_path = f"{audio_dir}/audio.mp3"

    transcription_stream = model.transcribe(audio_path)
    # Convert each chapter_start, chapter_ebd in chapter_audio_items to milliseconds
    converted_chapters = []
    for chapter in chapter_audio_items:
        converted_chapters.append({
            "chapter_title": chapter['chapter_title'],
            "chapter_start": time_str_to_seconds(chapter['chapter_start']),
            "chapter_end": time_str_to_seconds(chapter['chapter_end']),
            "chapter_file_path": chapter['chapter_file_path']
        })

    for current_segments in transcription_stream:
        for segment in current_segments:
            if not segment['text']:
                continue

            chapter_title = get_chapter_title_by_start_and_end_time(
                converted_chapters, segment['start'], segment['end'])

            transcription = {
                "id": generate_hash({
                    "video_id": video_id,
                    "start": segment['start'],
                    "end": segment['end'],
                }),
                "seek": segment['seek'],
                "start": segment['start'],
                "end": segment['end'],
                "chapter_title": chapter_title,
                "text": segment['text'],
                "info": {
                    "video_id": video_id,
                    "channel_name": results['channel_name'],
                    "video_title": results['title'],
                },
                "eval": {
                    "avg_logprob": segment['avg_logprob'],
                    "compression_ratio": segment['compression_ratio'],
                    "no_speech_prob": segment['no_speech_prob'],
                },
                "words": segment['words'],
            }

            chapter_transcriptions.append(transcription)
            # batch_items.append(transcription)

            # if len(batch_items) >= batch_size:
            #     save_data(transcription_file_path, batch_items)
            #     batch_items = []

    # if batch_items:
    #     save_data(transcription_file_path, batch_items)

    # deduplicate_all_transcriptions([transcription_file_path])


if __name__ == '__main__':
    audio_format = 'mp3'
    audio_dir = '../dataset/audio'
    video_url = 'https://www.youtube.com/watch?v=7qr6DK6P0uQ'

    audio_path = download_audio(video_url, audio_dir, audio_format)

    extractor = YouTubeInfoExtractor(video_url)
    info = extractor.extract_info()

    print(f"Info\n{json.dumps(info, indent=2)}")
