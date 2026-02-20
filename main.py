from src import SimpleMediaRepository, FFmpegVideoCreator, VideoConfig



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
    #FFmpegVideoCreator.create_video(creator, config)
    FFmpegVideoCreator.overlay_videos(self=creator,
                                      main_video="output_data\\ser2.mp4",
                                      overlay_video="src\\creators\\tp1.mov",
                                      output_video="output_data\\my_video_overlay4.mp4")
if __name__ == "__main__":
    main()