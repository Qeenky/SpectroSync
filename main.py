from src import SimpleMediaRepository, FFmpegVideoCreator, VideoConfig
from src.creators.thumbnail_creator import create_thumbnail_bar_video


def main():
    repo = SimpleMediaRepository()
    repo.set_image("src\\creators\\1.jpg")
    repo.set_audio("input_data\\tp.mp3")

    creator = FFmpegVideoCreator(repo)
    config = VideoConfig(
        output_path="output_data\\ser2.mp4",
        resolution=(1920, 1080),
        fps=30,
        video_codec="libx264",
        audio_codec="aac"
    )


    # FFmpegVideoCreator.create_video(creator, config)
    #
    #
    # FFmpegVideoCreator.overlay_videos(
    #     self=creator,
    #     main_video="output_data\\ser2.mp4",
    #     overlay_video="src\\creators\\tp1.mov",
    #     output_video="output_data\\my_video_overlay4.mp4"
    # )

    audio_duration = float(FFmpegVideoCreator._get_audio_duration(creator, repo.get_audio().path))
    create_thumbnail_bar_video(
        "input_data\\thumbnail.png",
        "output_data\\thumb_video.mov",
        audio_duration=audio_duration,
        fps=30,
        dpi=150
    )

    FFmpegVideoCreator.overlay_videos(
        self=creator,
        main_video="output_data\\my_video_overlay4.mp4",
        overlay_video="output_data\\thumb_video.mov",
        output_video="output_data\\final_video.mp4",
        custom_x=150,
        custom_y=250,
        overlay_width=400,
        overlay_height=410
    )



if __name__ == "__main__":
    main()