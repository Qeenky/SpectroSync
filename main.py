from src import SimpleMediaRepository, FFmpegVideoCreator, VideoConfig
from src.creators.thumbnail_creator import create_thumbnail_bar_video
from src.creators.red_images import *
from src.creators.analizator import Analizator
from src.creators.animation import WaveVisualizer

def main():
    # Data_input
    audio_name = "Pepel Nahudi - шрамы"
    audio_path = f"input_data\\{audio_name}.mp3"


    # Создание волны
    a = Analizator()
    a._set_audio_path(audio_path)
    a._precompute_all_powers()

    viz = WaveVisualizer(a)
    viz.create_wave_animation(
        duration_sec=int(a._get_audio_duration()),
        output_file='temp_files\\tp1.mov',
        fps=60
    )

    # Подготовка фона
    blur_video_background("input_data\\backv.mp4", "temp_files\\background_blurred.mp4", blur_strength=5)

    repo = SimpleMediaRepository()
    repo.set_video_input("temp_files\\background_blurred.mp4")
    repo.set_audio(audio_path)

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
        "input_data\\thumbnail.jpg",
        "temp_files\\temp_thumb.mov",
        audio_path=repo.get_audio().path,
        fps=60,
        dpi=150
    )

    add_gradient_to_video(audio_duration, "temp_files\\temp_gradient.mov", direction="bottom")



    creator.overlay_videos(
        main_video="temp_files\\temp_background.mp4",
        overlay_video="temp_files\\temp_gradient.mov",
        output_video="temp_files\\temp_background_final.mp4",
        overlay_width=1920,
        overlay_height=1080,
    )

    creator.overlay_videos(
        main_video="temp_files\\temp_background_final.mp4",
        overlay_video="temp_files\\tp1.mov",
        output_video="temp_files\\temp_overlay.mp4",
        overlay_width=1920,
        overlay_height=270,
        custom_x=0,
        custom_y=810,
    )


    creator.overlay_videos(
        main_video="temp_files\\temp_overlay.mp4",
        overlay_video="temp_files\\temp_thumb.mov",
        output_video=f"output_data\\{audio_name}.mp4",
        custom_x=150,
        custom_y=250,
        overlay_width=1000,
        overlay_height=400
    )



if __name__ == "__main__":
    main()