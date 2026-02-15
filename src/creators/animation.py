from src.creators.analizator import Analizator
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
import numpy as np
import subprocess, os



class WaveVisualizer:
    def __init__(self, Analizator: object[Analizator]):
        self.analyzer = Analizator

        # Получаем частоты
        self.analyzer._precompute_all_powers()
        self.lows = self.analyzer.low_bands
        self.mids = self.analyzer.medium_bands
        self.highs = self.analyzer.high_bands
        self.lows_norm = self.lows / (self.lows.max() + 0.01)
        self.mids_norm = self.mids / (self.mids.max() + 0.01)
        self.highs_norm = self.highs / (self.highs.max() + 0.01)


        # Параметры автономной динамической волны
        self.base_phase = 0.0
        self.base_phase_speed = 7.0
        self.time = 0.0

        # Автономные осцилляторы
        self.autonomous_amplitude = 0.0
        self.autonomous_frequency = 0.7 * 10
        self.autonomous_phase_mod = 1.0

        # Для плавного изменения частоты
        self.current_frequency = 1.0
        self.target_frequency = 1.0

        self.current_bass_freq = 0.5
        self.current_melody_freq = 1.0
        self.current_vocal_freq = 2.0

        self.target_bass_freq = 0.5
        self.target_melody_freq = 1.0
        self.target_vocal_freq = 2.0

        self.frequency_smoothness = 0.02

        # Индивидуальные фазы для каждой волны
        self.bass_phase = 0.0
        self.melody_phase = 2.1
        self.vocal_phase = 4.2

    def get_powers_at_time(self, time_sec):
        frame_idx = int(time_sec * self.analyzer.sr / 512)
        if frame_idx >= len(self.lows):
            frame_idx = len(self.lows) - 1

        return {
            'lows': self.lows_norm[frame_idx],
            'mids': self.mids_norm[frame_idx],
            'highs': self.highs_norm[frame_idx]
        }

    def update_autonomous_motion(self, dt, powers):
        """Обновляет автономное движение волны"""
        self.time += dt
        self.base_phase += self.base_phase_speed * dt
        self.autonomous_amplitude = 1.0 + 0.3 * np.sin(self.time * 0.3)
        self.autonomous_phase_mod = 15 * (np.sin(self.time * 0.08)) ** 2

        # Каждая волна теперь имеет свою целевую частоту!
        self.target_bass_freq = 0.1 + powers['lows'] * 8.0
        self.target_melody_freq = 0.2 + powers['mids'] * 6.0
        self.target_vocal_freq = 0.4 + powers['highs'] * 10.0

        # Плавное обновление каждой частоты
        self.current_bass_freq += (self.target_bass_freq - self.current_bass_freq) * self.frequency_smoothness
        self.current_melody_freq += (self.target_melody_freq - self.current_melody_freq) * self.frequency_smoothness
        self.current_vocal_freq += (self.target_vocal_freq - self.current_vocal_freq) * self.frequency_smoothness

        self.bass_phase += self.current_bass_freq * dt * 2 * np.pi
        self.melody_phase += self.current_melody_freq * dt * 2 * np.pi
        self.vocal_phase += self.current_vocal_freq * dt * 2 * np.pi


    def clamp_color_value(self, value):
        """Ограничивает значение цвета между 0 и 1"""
        return max(0.0, min(1.0, float(value)))

    def get_gradient_color(self, power, wave_type, time_offset=0):
        """Создает эффект градиента во времени"""
        t = self.time + time_offset

        if wave_type == 'bass':
            # Красный → Фиолетовый → Синий
            r = 0.5 + 0.5 * np.sin(t * 0.3)
            g = 0.2 + 0.3 * np.sin(t * 0.3 + 2.1)
            b = 0.3 + 0.5 * np.sin(t * 0.3 + 4.2)
        elif wave_type == 'melody':
            # Зеленый → Желтый → Оранжевый
            r = 0.3 + 0.6 * np.sin(t * 0.4)
            g = 0.5 + 0.4 * np.sin(t * 0.4 + 1.5)
            b = 0.1 + 0.2 * np.sin(t * 0.4 + 3.0)
        else:
            # Синий → Голубой → Бирюзовый
            r = 0.1 + 0.3 * np.sin(t * 0.5)
            g = 0.3 + 0.5 * np.sin(t * 0.5 + 1.8)
            b = 0.6 + 0.3 * np.sin(t * 0.5 + 3.6)

        # Применяем мощность
        r *= (0.7 + power * 0.5)
        g *= (0.7 + power * 0.5)
        b *= (0.7 + power * 0.5)

        alpha = 0.7 + power * 0.3

        return (self.clamp_color_value(r),
                self.clamp_color_value(g),
                self.clamp_color_value(b),
                self.clamp_color_value(alpha))

    def get_accent_color(self, base_color, power):
        """Добавляет случайные цветовые акценты на пиках"""
        r, g, b, a = base_color

        # На пиках добавляем случайный оттенок
        if power > 0.8:
            accent = np.random.choice(['r', 'g', 'b'])
            if accent == 'r':
                r = min(1.0, r + 0.3)
            elif accent == 'g':
                g = min(1.0, g + 0.3)
            else:
                b = min(1.0, b + 0.3)

        return (r, g, b, a)

    def generate_bass_wave(self, x, power):
        """Генерирует волну для баса"""
        # Басовые частоты - медленные, мощные
        freq = max(0.3, min(1.5, self.current_bass_freq))
        phase = self.base_phase + self.autonomous_phase_mod * 0.5 + self.bass_phase

        # Амплитуда сильно зависит от баса
        amp = self.autonomous_amplitude * (0.5 + power * 4.0)

        # Чистая синусоида для баса
        wave = amp * np.sin(freq * x + phase)

        # Огибающая
        envelope = np.exp(-(x - 2 * np.pi) ** 2 / (4 * np.pi) ** 2)
        wave *= envelope

        return wave

    def generate_melody_wave(self, x, power):
        """Генерирует волну для мелодии"""
        freq = max(0.8, min(2.5, self.current_melody_freq))
        phase = self.base_phase * 1.5 + self.autonomous_phase_mod + self.melody_phase

        amp = self.autonomous_amplitude * (0.3 + power * 4) * 2

        wave = (amp * 0.7 * np.sin(freq * x + phase) +
                amp * 0.3 * np.sin(2 * freq * x + phase * 1.5))

        envelope = np.exp(-(x - 2 * np.pi) ** 2 / (3 * np.pi) ** 2)
        wave *= envelope

        return wave

    def generate_vocal_wave(self, x, power):
        """Генерирует волну для вокала"""
        freq = max(1.5, min(5.0, self.current_vocal_freq))
        phase = self.base_phase * 2.0 + self.autonomous_phase_mod * 1.5 + self.vocal_phase

        amp = self.autonomous_amplitude * (0.2 + power * 4) * 2

        # Много гармоник для вокала
        wave = amp * np.sin(freq * x + phase)

        # Добавляем немного шума для текстуры
        noise = np.random.randn(len(x)) * 0.05 * power
        wave += noise

        envelope = np.exp(-(x - 2 * np.pi) ** 2 / (2 * np.pi) ** 2)
        wave *= envelope

        return wave

    def generate_waves(self, time_sec, length=1920):
        """Генерирует три волны с общей автономной динамикой"""
        dt = 1 / 60.0
        powers = self.get_powers_at_time(time_sec)

        self.update_autonomous_motion(dt, powers)

        x = np.linspace(0, 4 * np.pi, length)

        bass_wave = self.generate_bass_wave(x, powers['lows'])
        melody_wave = self.generate_melody_wave(x, powers['mids'])
        vocal_wave = self.generate_vocal_wave(x, powers['highs'])

        bass_color = self.get_gradient_color(powers['lows'], "bass")
        melody_color = self.get_gradient_color(powers['mids'], "melody")
        vocal_color = self.get_gradient_color(powers['highs'], "vocal")

        bass_color = self.get_accent_color(bass_color, powers['lows'])
        melody_color = self.get_accent_color(melody_color, powers['mids'])
        vocal_color = self.get_accent_color(vocal_color, powers['highs'])

        waves_data = [
            {'y': bass_wave, 'color': bass_color, 'width': 3.0, 'name': 'BASS'},
            {'y': melody_wave, 'color': melody_color, 'width': 2.0, 'name': 'MELODY'},
            {'y': vocal_wave, 'color': vocal_color, 'width': 1.5, 'name': 'VOCAL'}
        ]

        return x, waves_data, powers

    def create_wave_animation(self, duration_sec=10, fps=30, output_file='waves.mp4', dpi=150):
        """Создаёт анимацию с тремя независимыми волнами"""
        figsize_width = 1920 / dpi
        figsize_height = 270 / dpi

        fig, ax = plt.subplots(figsize=(figsize_width, figsize_height), facecolor='black', dpi=dpi)
        ax.set_facecolor('black')

        # Убираем все отступы
        plt.subplots_adjust(left=0, right=1, bottom=0, top=1)

        bass_line, = ax.plot([], [], linewidth=4.0)
        melody_line, = ax.plot([], [], linewidth=2.5)
        vocal_line, = ax.plot([], [], linewidth=1.5)

        waves = [bass_line, melody_line, vocal_line]

        # Устанавливаем границы точно по краям
        ax.set_xlim(0, 4 * np.pi)
        ax.set_ylim(-8, 8)
        ax.axis('off')

        # Убираем тики и всё остальное
        ax.set_xticks([])
        ax.set_yticks([])
        ax.margins(0)

        def init():
            for wave in waves:
                wave.set_data([], [])
            return waves

        def update(frame):
            time_sec = frame / fps
            x, waves_data, powers = self.generate_waves(time_sec, 1920)

            for i, (wave_line, wave_data) in enumerate(zip(waves, waves_data)):
                wave_line.set_data(x, wave_data['y'])
                color = wave_data['color']
                wave_line.set_color(color[:3])
                wave_line.set_alpha(color[3])
                wave_line.set_linewidth(wave_data['width'])

            return waves

        total_frames = int(duration_sec * fps)
        ani = animation.FuncAnimation(fig, update, frames=total_frames,
                                      init_func=init, blit=False,
                                      interval=1000 / fps)

        writer = FFMpegWriter(fps=fps, metadata=dict(artist='SpectroSync'))
        ani.save(output_file, writer=writer, dpi=dpi)
        plt.close()

        return ani

    def render_with_audio(self, temp_output_path='temp_video.mp4',
                          duration_sec=5, fps=30, output_path='output.mp4'):
        """Рендерит видео с аудио"""
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


# Использование
a = Analizator()
a._set_audio_path("C:\\Users\\Qeenky\\Desktop\\SpectroSync\\input_data\\music.mp3")
a._precompute_all_powers()

viz = WaveVisualizer(a)
visual = viz.create_wave_animation(
    duration_sec=int(a._get_audio_duration()),
    output_file='ff1.mp4',
    fps=60
)