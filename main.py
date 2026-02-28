from src import SimpleMediaRepository, FFmpegVideoCreator, VideoConfig
from src.creators.thumbnail_creator import create_thumbnail_video, create_bar_video
from src.creators.red_images import *
from src.creators.analizator import Analizator
from src.creators.animation import WaveVisualizer
import os


def main():
    print(os.listdir("input_data"))
    for i in os.listdir("input_data"):
        background_path = None
        thumbnail_path = None
        audio_path = None

        print(os.listdir("input_data\\" + i))
        if os.path.isfile(f"input_data\\{i}\\background.jpg"):
            background_path = f"input_data\\{i}\\background.jpg"
        elif os.path.isfile(f"input_data\\{i}\\background.mp4"):
            background_path = f"input_data\\{i}\\background.mp4"
        elif os.path.isfile(f"input_data\\{i}\\background.png"):
            background_path = f"input_data\\{i}\\background.png"
        if os.path.isfile(f"input_data\\{i}\\thumbnail.jpg"):
            thumbnail_path = f"input_data\\{i}\\thumbnail.jpg"
        elif os.path.isfile(f"input_data\\{i}\\thumbnail.png"):
            thumbnail_path = f"input_data\\{i}\\thumbnail.png"

        for g in os.listdir("input_data\\" + i):
            if ".mp3" in g:
                audio_path = f"input_data\\{i}\\{g}"
                audio_name = g[:-4]

        if None not in [background_path, thumbnail_path, audio_path]:
            try:
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
                repo = SimpleMediaRepository()
                repo.set_audio(audio_path)

                creator = FFmpegVideoCreator(repo)

                if background_path[-4:] == ".mp4":
                    blur_video_background(background_path, "temp_files\\background_blurred.mp4", blur_strength=5)
                    repo.set_video_input("temp_files\\background_blurred.mp4")
                    print("background blurred (.mp4)")

                    config = VideoConfig(
                        output_path="temp_files\\temp_background.mp4",
                        resolution=(1920, 1080),
                        fps=60,
                        video_codec="libx264",
                        audio_codec="aac"
                    )
                    creator.create_video(config)

                elif background_path[-4:] in (".jpg", ".png"):
                    blur_background_image(background_path, "temp_files\\background_blurred.jpg")
                    cmd = [
                        'ffmpeg',
                        '-loop', '1',
                        '-i', "temp_files\\background_blurred.jpg",
                        '-i', audio_path,
                        '-c:v', 'libx264',
                        '-c:a', 'aac',
                        '-t', str(int(a._get_audio_duration())),
                        '-pix_fmt', 'yuv420p',
                        '-shortest',
                        '-y',
                        "temp_files\\temp_background.mp4"
                    ]
                    subprocess.run(cmd, check=True)
                    repo.set_video_input("temp_files\\temp_background.mp4")
                    print("background blurred (.jpg) -> video created")
                else:
                    raise Exception("Отсутствует background (.jpg, .mp4)")

                audio_duration = float(creator._get_audio_duration(repo.get_audio().path))

                create_thumbnail_video(
                    thumbnail_path,
                    "temp_files\\temp_thumb.mov",
                    audio_duration=audio_duration,
                    fps=60,
                    dpi=150
                )
                create_bar_video(audio_path, "temp_files\\temp_bar_video.mov", fps=60, bar_color="yellow")


                add_gradient_to_video(audio_duration, "temp_files\\temp_gradient.mov", direction="bottom")
                mode = 1
                if mode == 1:
                    # Наложение градиента на фон
                    creator.overlay_videos(
                        main_video="temp_files\\temp_background.mp4",
                        overlay_video="temp_files\\temp_gradient.mov",
                        output_video="temp_files\\temp_background_final.mp4",
                        overlay_width=1920,
                        overlay_height=1080,
                    )

                    # Наложение волн
                    creator.overlay_videos(
                        main_video="temp_files\\temp_background_final.mp4",
                        overlay_video="temp_files\\tp1.mov",
                        output_video="temp_files\\temp_overlay.mp4",
                        overlay_width=1920,
                        overlay_height=270,
                        custom_x=0,
                        custom_y=810,
                    )

                    # Наложение тумбы
                    creator.overlay_videos(
                        main_video="temp_files\\temp_overlay.mp4",
                        overlay_video="temp_files\\temp_thumb.mov",
                        output_video=f"temp_files\\temp_thumb_back.mp4",
                        custom_x=150,
                        custom_y=300,
                        overlay_width=400,
                        overlay_height=400
                    )

                    creator.overlay_videos(
                        main_video="temp_files\\temp_thumb_back.mp4",
                        overlay_video="temp_files\\temp_bar_video.mov",
                        output_video=f"output_data\\{audio_name}.mp4",
                        custom_x=550,
                        custom_y=200,
                        overlay_width=600,
                        overlay_height=600
                    )

                    print(f"✅ Видео создано: output_data\\{audio_name}.mp4")
                elif mode == 2:
                    # # Наложение тумбы
                    # creator.overlay_videos(
                    #     main_video="temp_files\\temp_background.mp4",
                    #     overlay_video="temp_files\\temp_thumb.mov",
                    #     output_video=f"temp_files\\temp_thumb_back.mp4",
                    #     custom_x=703,
                    #     custom_y=20,
                    #     overlay_width=514,
                    #     overlay_height=756
                    # )

                    # Наложение градиента на фон
                    creator.overlay_videos(
                        main_video="temp_files\\temp_background.mp4",
                        overlay_video="temp_files\\temp_gradient.mov",
                        output_video="temp_files\\temp_background_grad.mp4",
                        overlay_width=1920,
                        overlay_height=1080,
                    )

                    # Наложение тумбы
                    creator.overlay_videos(
                        main_video="temp_files\\temp_background_grad.mp4",
                        overlay_video="temp_files\\temp_thumb.mov",
                        output_video=f"temp_files\\temp_background_final.mp4",
                        custom_x=703,
                        custom_y=20,
                        overlay_width=514,
                        overlay_height=756
                    )

                    # Наложение волн
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
                        overlay_video="temp_files\\temp_bar_video.mov",
                        output_video=f"output_data\\{audio_name}.mp4",
                        overlay_width=600,
                        overlay_height=600,
                        custom_x=660,
                        custom_y=470,
                    )

            except Exception as e:
                print(f"❌ Ошибка при обработке {i}: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()