from src import SimpleMediaRepository, FFmpegVideoCreator, VideoConfig
from src.creators.thumbnail_creator import create_thumbnail_bar_video
from src.creators.red_images import *


def main():
    blur_video_background("input_data\\backv.mp4", "temp_files\\background_blurred.mp4", blur_strength=5)

    repo = SimpleMediaRepository()
    repo.set_video_input("temp_files\\background_blurred.mp4")
    repo.set_audio("input_data\\Нервы - Муза.mp3")

    creator = FFmpegVideoCreator(repo)

    config = VideoConfig(
        output_path="temp_files\\temp_background.mp4",
        resolution=(1920, 1080),
        fps=60,
        video_codec="libx264",
        audio_codec="aac"
    )

    creator.create_video(config)
    audio_duration = float(creator._get_audio_duration(repo.get_audio().path))

    create_thumbnail_bar_video(
        "input_data\\thumbnail.png",
        "temp_files\\temp_thumb.mov",
        audio_duration=audio_duration,
        fps=60,
        dpi=150
    )

    add_gradient_to_video(audio_duration, "temp_files\\temp_gradient.mov")

    create_text_video(repo.get_audio().path,
                      "temp_files\\temp_text.mov")

    creator.overlay_videos(
        main_video="temp_files\\temp_background.mp4",
        overlay_video="temp_files\\temp_gradient.mov",
        output_video="temp_files\\temp_background_final.mp4",
        overlay_width=1920,
        overlay_height=1080,
    )

    creator.overlay_videos(
        main_video="temp_files\\temp_background_final.mp4",
        overlay_video="src\\creators\\tp1.mov",
        output_video="temp_files\\temp_overlay.mp4",
        overlay_width=1920,
        overlay_height=270,
        custom_x=0,
        custom_y=810,
    )


    creator.overlay_videos(
        main_video="temp_files\\temp_overlay.mp4",
        overlay_video="temp_files\\temp_thumb.mov",
        output_video="temp_files\\temp_overlay2.mp4",
        custom_x=150,
        custom_y=250,
        overlay_width=400,
        overlay_height=410
    )

    creator.overlay_videos(
        main_video="temp_files\\temp_overlay2.mp4",
        overlay_video="temp_files\\temp_text.mov",
        output_video="output_data\\final_video.mp4",
        custom_x=0,
        custom_y=0,
        overlay_width=1920,
        overlay_height=1080
    )


if __name__ == "__main__":
    main()