from src.creators.analizator import Analizator
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
import numpy as np
import subprocess, os

class Animator:
    def __init__(self):
        self.frames = range(0)
        self.powers = []

    def _set_frames(self, frames: int):
        self.frames = range(frames)

    def _set_power(self, analizator_obj: object[Analizator], frames: int):
        self._set_frames(frames)
        if self.frames == range(0):
            return
        self.powers = [analizator_obj._get_lows_power(i) for i in self.frames]

    def _create_simple_liner_graphic(self, analizator_obj: object[Analizator], frames: int):
        self._set_power(analizator_obj, frames)
        if self.frames == range(0) or self.powers == []:
            return
        plt.figure(figsize=(10, 4))
        plt.plot(self.frames, self.powers, 'b-', linewidth=2)
        plt.title(f"Мощность низких частот во времени ( первые {frames} кадров )")
        plt.xlabel("№ кадра (frame_index)")
        plt.ylabel("Мощность")
        plt.grid(True, alpha=0.3)
        plt.show()


class WaveVisualizer:
    def __init__(self, Analizator):
        self.analyzer = Analizator
        self.precompute_bands()

    def precompute_bands(self):
        spec = self.analyzer.spectrogram

        self.lows = spec[:30, :].mean(axis=0)
        self.mids = spec[30:80, :].mean(axis=0)
        self.highs = spec[80:128, :].mean(axis=0)

        self.lows_norm = self.lows / self.lows.max()
        self.mids_norm = self.mids / self.mids.max()
        self.highs_norm = self.highs / self.highs.max()

    def get_powers_at_time(self, time_sec):
        frame_idx = int(time_sec * self.analyzer.sr / 512)
        if frame_idx >= len(self.lows):
            frame_idx = len(self.lows) - 1

        return {
            'lows': self.lows_norm[frame_idx],
            'mids': self.mids_norm[frame_idx],
            'highs': self.highs_norm[frame_idx]
        }

    def generate_wave(self, time_sec, length=1000):
        powers = self.get_powers_at_time(time_sec)

        x = np.linspace(0, 4 * np.pi, length)

        amplitude = 1.0 + powers['lows'] * 3  # Амплитуда: 1..4
        frequency = 1.0 + powers['mids'] * 2  # Частота: 1..3

        base_wave = amplitude * np.sin(frequency * x)

        harmonic_amp = powers['mids'] * 0.5
        harmonic = harmonic_amp * np.sin(2 * frequency * x + time_sec * 2)

        detail_amp = powers['highs'] * 0.3
        detail = detail_amp * np.random.randn(length) * np.sin(8 * x)

        wave = base_wave + harmonic + detail

        envelope = np.exp(-(x - 2 * np.pi) ** 2 / (2 * np.pi) ** 2)
        wave = wave * envelope

        return x, wave, powers

    def get_wave_color(self, powers):
        l, m, h = powers['lows'], powers['mids'], powers['highs']

        if l > 0.7:
            r = 0.8 + l * 0.2
            g = 0.3 + m * 0.4
            b = 0.1 + h * 0.2
            return (r, g, b, 0.9)
        elif m > 0.6:
            r = 0.4 + h * 0.3
            g = 0.3 + m * 0.3
            b = 0.7 + l * 0.2
            return (r, g, b, 0.8)
        else:
            r = 0.2 + h * 0.3
            g = 0.6 + m * 0.3
            b = 0.5 + l * 0.3
            return (r, g, b, 0.7)

    def create_wave_animation(self, duration_sec=10, fps=30, output_file='waves.mp4'):
        """Создаёт анимацию волн."""
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='black')
        ax.set_facecolor('black')

        waves = []
        for i in range(3):
            wave_line, = ax.plot([], [], linewidth=2.5 - i * 0.5, alpha=0.9 - i * 0.2)
            waves.append(wave_line)

        ax.set_xlim(0, 4 * np.pi)
        ax.set_ylim(-5, 5)
        ax.axis('off')

        text = ax.text(0.02, 0.95, '', transform=ax.transAxes,
                       color='white', fontsize=10, fontfamily='monospace')

        def init():
            for wave in waves:
                wave.set_data([], [])
            text.set_text('')
            return waves + [text]

        def update(frame):
            time_sec = frame / fps

            x, base_wave, powers = self.generate_wave(time_sec)

            for i, wave_line in enumerate(waves):
                phase_shift = i * 0.5 * time_sec
                layer_wave = base_wave * (1.0 - i * 0.2) * np.sin(x + phase_shift)

                color = self.get_wave_color(powers)
                layer_color = (color[0] * (1 - i * 0.1),
                               color[1] * (1 - i * 0.05),
                               color[2] * (1 + i * 0.1),
                               color[3])

                wave_line.set_data(x, layer_wave)
                wave_line.set_color(layer_color)

            info = (f"Time: {time_sec:.1f}s\n"
                    f"Lows: {powers['lows']:.2f}\n"
                    f"Mids: {powers['mids']:.2f}\n"
                    f"Highs: {powers['highs']:.2f}")
            text.set_text(info)

            return waves + [text]

        total_frames = int(duration_sec * fps)
        ani = animation.FuncAnimation(fig, update, frames=total_frames,
                            init_func=init, blit=True, interval=1000 / fps)

        writer = FFMpegWriter(fps=fps, metadata=dict(artist='SpectroSync'))
        ani.save(output_file, writer=writer, dpi=150)
        plt.close()

        return ani

    def render_with_audio(self, temp_output_path ='temp_video.mp4', duration_sec=5, fps=30, output_path='output.mp4'):
        temp_video = temp_output_path
        temp_audio = 'temp_audio.mp3'

        self.create_wave_animation(duration_sec, fps, temp_output_path)
        self._extract_audio_segment(duration_sec, temp_audio)
        self._combine_video_audio(temp_video, temp_audio, output_path)

        os.remove(temp_video)
        os.remove(temp_audio)

    def _extract_audio_segment(self, duration_sec, output_path):
        cmd = [
            'ffmpeg',
            '-i', self.analyzer.audio_path,
            '-t', str(duration_sec),
            '-acodec', 'copy',
            output_path,
            '-y'
        ]
        subprocess.run(cmd, check=True)

    def _combine_video_audio(self, video_path, audio_path, output_path):
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            output_path,
            '-y'
        ]
        subprocess.run(cmd, check=True)


a = Analizator()
a._set_audio_path("C:\\Users\\Qeenky\\Desktop\\SpectroSync\\input_data\\music.mp3") #absolute path
a._precompute_all_powers()

viz = WaveVisualizer(a)

visual = viz.render_with_audio(duration_sec=120, output_path='waves_audio.mp4', fps=165)