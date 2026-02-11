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

        # Параметры автономной динамической волны
        self.base_phase = 0.0
        self.base_phase_speed = 10.0
        self.time = 0.0

        # Автономные осцилляторы
        self.autonomous_amplitude = 1.0
        self.autonomous_frequency = 0.7
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

        self.color_palettes = {
            'neon': {
                'bass': [(1.0, 0.2, 0.2), (0.9, 0.1, 0.5), (1.0, 0.4, 0.0)],  # Красный → Розовый → Оранжевый
                'melody': [(0.2, 1.0, 0.2), (0.1, 0.9, 0.5), (0.0, 1.0, 0.8)],  # Зеленый → Мятный → Бирюзовый
                'vocal': [(0.2, 0.2, 1.0), (0.5, 0.1, 0.9), (0.8, 0.0, 1.0)]  # Синий → Фиолетовый → Пурпурный
            },
            'sunset': {
                'bass': [(1.0, 0.4, 0.2), (1.0, 0.6, 0.0), (1.0, 0.3, 0.3)],  # Закатные тона
                'melody': [(1.0, 0.8, 0.2), (1.0, 0.9, 0.4), (1.0, 0.7, 0.1)],  # Золотистые
                'vocal': [(1.0, 0.5, 0.5), (1.0, 0.4, 0.6), (1.0, 0.3, 0.7)]  # Розовые
            },
            'ocean': {
                'bass': [(0.1, 0.3, 0.8), (0.2, 0.4, 0.9), (0.0, 0.2, 0.7)],  # Глубокий синий
                'melody': [(0.2, 0.7, 0.9), (0.3, 0.8, 1.0), (0.1, 0.6, 0.8)],  # Бирюзовый
                'vocal': [(0.4, 0.9, 0.9), (0.5, 1.0, 1.0), (0.3, 0.8, 0.8)]  # Морская волна
            },
            'fire': {
                'bass': [(1.0, 0.1, 0.0), (1.0, 0.3, 0.0), (1.0, 0.0, 0.0)],  # Красный
                'melody': [(1.0, 0.5, 0.0), (1.0, 0.6, 0.0), (1.0, 0.4, 0.0)],  # Оранжевый
                'vocal': [(1.0, 0.9, 0.0), (1.0, 1.0, 0.0), (1.0, 0.8, 0.0)]  # Желтый
            },
            'forest': {
                'bass': [(0.2, 0.5, 0.2), (0.1, 0.4, 0.1), (0.3, 0.6, 0.2)],  # Темно-зеленый
                'melody': [(0.3, 0.7, 0.3), (0.4, 0.8, 0.3), (0.2, 0.6, 0.2)],  # Зеленый
                'vocal': [(0.5, 0.9, 0.4), (0.6, 1.0, 0.5), (0.4, 0.8, 0.3)]  # Салатовый
            },
            'candy': {
                'bass': [(1.0, 0.5, 0.8), (0.9, 0.4, 0.7), (1.0, 0.6, 0.9)],  # Розовый
                'melody': [(0.6, 0.8, 1.0), (0.5, 0.7, 0.9), (0.7, 0.9, 1.0)],  # Голубой
                'vocal': [(1.0, 0.9, 0.5), (0.9, 0.8, 0.4), (1.0, 1.0, 0.6)]  # Желтый
            }
        }

        self.current_palette = 'neon'  # Стартовая палитра

    def precompute_bands(self):
        spec = self.analyzer.spectrogram

        # Разделяем частоты
        self.lows = spec[:20, :].mean(axis=0)
        self.mids = spec[20:70, :].mean(axis=0)
        self.highs = spec[70:128, :].mean(axis=0)

        # Нормализация
        self.lows_norm = self.lows / (self.lows.max() + 0.01)
        self.mids_norm = self.mids / (self.mids.max() + 0.01)
        self.highs_norm = self.highs / (self.highs.max() + 0.01)

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
        self.autonomous_phase_mod = 15 * np.sin(self.time * 0.08)

        # Каждая волна теперь имеет свою целевую частоту!
        # Bass frequency - зависит от баса
        self.target_bass_freq = 0.5 + powers['lows'] * 1.5
        # Melody frequency - зависит от мидов
        self.target_melody_freq = 1.0 + powers['mids'] * 2.0
        # Vocal frequency - зависит от высоких
        self.target_vocal_freq = 2.0 + powers['highs'] * 3.0

        # Плавное обновление каждой частоты
        self.current_bass_freq += (self.target_bass_freq - self.current_bass_freq) * self.frequency_smoothness
        self.current_melody_freq += (self.target_melody_freq - self.current_melody_freq) * self.frequency_smoothness
        self.current_vocal_freq += (self.target_vocal_freq - self.current_vocal_freq) * self.frequency_smoothness

        # Добавляем автономные колебания (индивидуальные)
        self.current_bass_freq += 0.05 * np.sin(self.time * 0.2)
        self.current_melody_freq += 0.08 * np.sin(self.time * 0.25)
        self.current_vocal_freq += 0.12 * np.sin(self.time * 0.3)


    def clamp_color_value(self, value):
        """Ограничивает значение цвета между 0 и 1"""
        return max(0.0, min(1.0, float(value)))

    def get_bass_color(self, power):
        """Цвет для бас-волны с палитрой"""
        palette = self.color_palettes[self.current_palette]['bass']

        # Выбираем цвет из палитры на основе мощности
        if power > 0.7:
            r, g, b = palette[0]  # Яркий цвет
            alpha = 0.95
        elif power > 0.3:
            r, g, b = palette[1]  # Средний цвет
            alpha = 0.85
        else:
            r, g, b = palette[2]  # Приглушенный цвет
            alpha = 0.7 + power * 0.2

        # Автономные модуляции
        mod = 0.1 * np.sin(self.time * 0.5)
        r = self.clamp_color_value(r + mod * 0.5)
        g = self.clamp_color_value(g + mod * 0.3)
        b = self.clamp_color_value(b + mod * 0.2)

        return (r, g, b, self.clamp_color_value(alpha))

    def get_melody_color(self, power):
        """Цвет для мелодии с палитрой"""
        palette = self.color_palettes[self.current_palette]['melody']

        if power > 0.7:
            r, g, b = palette[0]
            alpha = 0.9
        elif power > 0.3:
            r, g, b = palette[1]
            alpha = 0.8
        else:
            r, g, b = palette[2]
            alpha = 0.6 + power * 0.2

        mod = 0.1 * np.sin(self.time * 0.5 + 2.1)
        r = self.clamp_color_value(r + mod * 0.3)
        g = self.clamp_color_value(g + mod * 0.5)
        b = self.clamp_color_value(b + mod * 0.4)

        return (r, g, b, self.clamp_color_value(alpha))

    def get_vocal_color(self, power):
        """Цвет для вокала с палитрой"""
        palette = self.color_palettes[self.current_palette]['vocal']

        if power > 0.7:
            r, g, b = palette[0]
            alpha = 0.85
        elif power > 0.3:
            r, g, b = palette[1]
            alpha = 0.75
        else:
            r, g, b = palette[2]
            alpha = 0.6 + power * 0.2

        mod = 0.1 * np.sin(self.time * 0.5 + 4.2)
        r = self.clamp_color_value(r + mod * 0.4)
        g = self.clamp_color_value(g + mod * 0.3)
        b = self.clamp_color_value(b + mod * 0.6)

        return (r, g, b, self.clamp_color_value(alpha))

    def get_dynamic_color(self, base_color, power, frequency_type):
        """Динамическое изменение цвета на основе частоты и мощности"""
        r, g, b = base_color

        # Модуляция на основе текущей частоты волны
        if frequency_type == 'bass':
            freq_mod = 0.2 * np.sin(self.current_bass_freq * self.time)
        elif frequency_type == 'melody':
            freq_mod = 0.2 * np.sin(self.current_melody_freq * self.time)
        else:
            freq_mod = 0.2 * np.sin(self.current_vocal_freq * self.time)

        # Модуляция на основе мощности
        power_mod = power * 0.3

        # Модуляция на основе битов (если есть детекция)
        beat_mod = 0.0
        if hasattr(self, 'is_beat') and self.is_beat:
            beat_mod = 0.4

        r = self.clamp_color_value(r + freq_mod + power_mod + beat_mod)
        g = self.clamp_color_value(g + freq_mod * 0.7 + power_mod * 0.5)
        b = self.clamp_color_value(b + freq_mod * 0.5 + power_mod * 0.3)

        return (r, g, b)

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

    def generate_waves(self, time_sec, length=1000):
        """Генерирует три волны с общей автономной динамикой"""
        dt = 1 / 60.0
        powers = self.get_powers_at_time(time_sec)

        # Обновляем общее автономное движение
        self.update_autonomous_motion(dt, powers)

        x = np.linspace(0, 4 * np.pi, length)

        # Генерируем каждую волну с её мощностью
        bass_wave = self.generate_bass_wave(x, powers['lows'])
        melody_wave = self.generate_melody_wave(x, powers['mids'])
        vocal_wave = self.generate_vocal_wave(x, powers['highs'])

        # Получаем цвета
        bass_color = self.get_bass_color(powers['lows'])
        melody_color = self.get_melody_color(powers['mids'])
        vocal_color = self.get_vocal_color(powers['highs'])

        waves_data = [
            {'y': bass_wave, 'color': bass_color, 'width': 3.0, 'name': 'BASS'},
            {'y': melody_wave, 'color': melody_color, 'width': 2.0, 'name': 'MELODY'},
            {'y': vocal_wave, 'color': vocal_color, 'width': 1.5, 'name': 'VOCAL'}
        ]

        return x, waves_data, powers

    def create_wave_animation(self, duration_sec=10, fps=30, output_file='waves.mp4'):
        """Создаёт анимацию с тремя независимыми волнами"""
        fig, ax = plt.subplots(figsize=(14, 7), facecolor='black')
        ax.set_facecolor('black')

        # Создаем три линии
        bass_line, = ax.plot([], [], linewidth=4.0)
        melody_line, = ax.plot([], [], linewidth=2.5)
        vocal_line, = ax.plot([], [], linewidth=1.5)

        waves = [bass_line, melody_line, vocal_line]

        ax.set_xlim(0, 4 * np.pi)
        ax.set_ylim(-8, 8)
        ax.axis('off')

        # Текстовая информация
        info_text = ax.text(0.02, 0.96, '', transform=ax.transAxes,
                            color='white', fontsize=10, fontfamily='monospace',
                            bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))

        # Легенда
        legend_elements = [
            plt.Line2D([0], [0], color='#ff4444', lw=4, label='BASS'),
            plt.Line2D([0], [0], color='#44ff44', lw=2.5, label='MELODY'),
            plt.Line2D([0], [0], color='#4444ff', lw=1.5, label='VOCAL')
        ]
        legend = ax.legend(handles=legend_elements, loc='upper right',
                           facecolor='black', edgecolor='white',
                           labelcolor='white', fontsize=9)

        palette_text = ax.text(0.02, 0.86, '', transform=ax.transAxes,
                               color='white', fontsize=8, fontfamily='monospace',
                               bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))

        def init():
            for wave in waves:
                wave.set_data([], [])
            info_text.set_text('')
            return waves + [info_text, legend]

        def update(frame):
            time_sec = frame / fps
            x, waves_data, powers = self.generate_waves(time_sec)

            # TODO: Изменить цветовые гаммы
            if powers['highs'] > 0.9 and powers['lows'] < 0.2:
                viz.current_palette = 'ocean'  # Вокал доминирует
            elif powers['lows'] > 0.8:
                viz.current_palette = 'ocean'  # Басс доминирует
            elif powers['mids'] > 0.8:
                viz.current_palette = 'ocean'  # Мелодия доминирует
            elif sum(powers.values()) > 2.0:
                viz.current_palette = 'ocean'  # Вся музыка мощная

            # Обновляем каждую линию
            for i, (wave_line, wave_data) in enumerate(zip(waves, waves_data)):
                wave_line.set_data(x, wave_data['y'])
                color = wave_data['color']
                wave_line.set_color(color[:3])
                wave_line.set_alpha(color[3])
                wave_line.set_linewidth(wave_data['width'])

            # Информация с уровнями
            bass_bar = '▬' * int(powers['lows'] * 20) + '─' * (20 - int(powers['lows'] * 20))
            melody_bar = '▬' * int(powers['mids'] * 20) + '─' * (20 - int(powers['mids'] * 20))
            vocal_bar = '▬' * int(powers['highs'] * 20) + '─' * (20 - int(powers['highs'] * 20))

            info = (f"Time: {time_sec:.1f}s | "
                    f"Bass: {self.current_bass_freq:.2f}Hz | "
                    f"Mel: {self.current_melody_freq:.2f}Hz | "
                    f"Voc: {self.current_vocal_freq:.2f}Hz\n"
                    f"BASS:   [{bass_bar}] {powers['lows']:.2f}\n"
                    f"MELODY: [{melody_bar}] {powers['mids']:.2f}\n"
                    f"VOCAL:  [{vocal_bar}] {powers['highs']:.2f}")
            info_text.set_text(info)
            palette_text.set_text(f"Palette: {viz.current_palette.upper()}")

            return waves + [info_text, legend, palette_text]

        total_frames = int(duration_sec * fps)
        ani = animation.FuncAnimation(fig, update, frames=total_frames,
                                      init_func=init, blit=False,
                                      interval=1000 / fps)

        writer = FFMpegWriter(fps=fps, metadata=dict(artist='SpectroSync'))
        ani.save(output_file, writer=writer, dpi=150)
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
visual = viz.render_with_audio(
    duration_sec=int(a._get_audio_duration()),
    output_path='fendi5.mp4',
    fps=60
)