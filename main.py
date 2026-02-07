from src import SimpleMediaRepository, FFmpegVideoCreator, VideoConfig



def main():
    repo = SimpleMediaRepository()
    repo.set_image("input_data\\background.jpg")
    repo.set_audio("input_data\\music.mp3")

    creator = FFmpegVideoCreator(repo)
    config = VideoConfig(
        output_path="output_data\\my_video.mp4",
        resolution=(1920, 1080),
        fps=30,
        video_codec="libx264",
        audio_codec="aac"
    )


if __name__ == "__main__":
    main()