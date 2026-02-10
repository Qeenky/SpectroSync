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
        self.base_phase = 0.0  # Базовая фаза, которая постоянно увеличивается
        self.base_phase_speed = 10.0  # Скорость движения волны
        self.time = 0.0  # Внутреннее время для автономных эффектов

        # Автономные осцилляторы для плавного движения
        self.autonomous_amplitude = 1.0
        self.autonomous_frequency = 1.0
        self.autonomous_phase_mod = 0.0

        # Для плавного изменения частоты
        self.current_frequency = 1.0
        self.target_frequency = 1.0
        self.frequency_smoothness = 0.03  # Плавность изменения частоты

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

    def update_autonomous_motion(self, dt, powers):
        """Обновляет автономное движение волны"""
        self.time += dt
        self.base_phase += self.base_phase_speed * dt
        self.autonomous_amplitude = 1.0 + 0.3 * np.sin(self.time * 0.3)
        self.autonomous_phase_mod = 0.5 * np.sin(self.time * 0.08)
        self.target_frequency = 1.0 + powers['mids'] * 2.0
        self.current_frequency += (self.target_frequency - self.current_frequency) * self.frequency_smoothness
        self.current_frequency += 0.1 * np.sin(self.time * 0.15)

    def generate_wave(self, time_sec, length=1000):
        powers = self.get_powers_at_time(time_sec)

        # TODO: Сделать параметром
        dt = 1 / 60.0  # предполагаем 60 FPS
        self.update_autonomous_motion(dt, powers)

        x = np.linspace(0, 4 * np.pi, length)

        amplitude_mod = 1.0 + powers['lows'] * 3.0  # Сильное влияние на высоту

        final_amplitude = self.autonomous_amplitude * amplitude_mod
        final_frequency = max(0.5, min(3.0, self.current_frequency))  # Ограничиваем частоту

        phase = self.base_phase + self.autonomous_phase_mod + time_sec * 0.5

        base_wave = final_amplitude * np.sin(final_frequency * x + phase)

        harmonic_amp = powers['mids'] * 0.6  # Увеличил для большего эффекта
        harmonic_phase = phase * 1.5 + np.sin(self.time * 0.3)
        harmonic = harmonic_amp * np.sin(2 * final_frequency * x + harmonic_phase)

        detail_amp = powers['highs'] * 0.4  # Увеличил для большего эффекта

        noise_freq = 8 + powers['highs'] * 6  # Частота шума зависит от highs
        detail = detail_amp * np.sin(noise_freq * x + self.time * 3) * 0.7

        smooth_noise = np.convolve(np.random.randn(length), np.ones(3) / 3, mode='same') # Добавляем немного сглаженного случайного шума
        detail += detail_amp * smooth_noise * 0.2

        wave = base_wave + harmonic + detail

        # Динамическая огибающая
        envelope_width = 2.0 + powers['lows'] * 1.5  # Bass влияет на ширину
        envelope = np.exp(-(x - 2 * np.pi) ** 2 / (envelope_width * np.pi) ** 2)
        wave = wave * envelope

        # Автономное "дыхание" волны
        breath_intensity = 0.15 + powers['mids'] * 0.1  # Mids усиливают дыхание
        breath = breath_intensity * np.sin(self.time * 0.4) * np.sin(x * 0.5)
        wave += breath

        # Добавляем "пульсацию" от bass
        pulse = powers['lows'] * 0.3 * np.sin(x * 0.8 + self.time * 1.0)
        wave += pulse

        return x, wave, powers

    def clamp_color_value(self, value):
        """Ограничивает значение цвета между 0 и 1"""
        return max(0.0, min(1.0, float(value)))

    def get_wave_color(self, powers):
        l, m, h = powers['lows'], powers['mids'], powers['highs']

        # Автономное изменение цвета + влияние частот
        color_time = self.time * 0.15
        r_mod = 0.1 * np.sin(color_time)
        g_mod = 0.1 * np.sin(color_time + 2.1)
        b_mod = 0.1 * np.sin(color_time + 4.2)

        # Цвет динамически меняется от частот
        # Bass - доминирует в спокойные моменты
        # Mids - добавляет активности
        # Highs - добавляет яркости

        total_power = l + m + h

        if total_power > 1.0:  # Активная музыка
            r = 0.7 + l * 0.3 + m * 0.1 + r_mod
            g = 0.3 + m * 0.5 + h * 0.1 + g_mod
            b = 0.2 + h * 0.6 + l * 0.1 + b_mod
            alpha = 0.9
        elif total_power > 0.5:  # Средняя активность
            r = 0.5 + l * 0.4 + r_mod
            g = 0.4 + m * 0.4 + g_mod
            b = 0.3 + h * 0.4 + b_mod
            alpha = 0.8
        else:  # Спокойная музыка
            r = 0.3 + l * 0.6 + r_mod
            g = 0.2 + m * 0.3 + g_mod
            b = 0.1 + h * 0.2 + b_mod
            alpha = 0.7 + l * 0.2  # Bass делает волну более заметной

        # Ограничиваем значения между 0 и 1
        r = self.clamp_color_value(r)
        g = self.clamp_color_value(g)
        b = self.clamp_color_value(b)
        alpha = self.clamp_color_value(alpha)

        return (r, g, b, alpha)

    def create_wave_animation(self, duration_sec=10, fps=30, output_file='waves.mp4'):
        """Создаёт анимацию волн."""
        fig, ax = plt.subplots(figsize=(14, 7), facecolor='black')
        ax.set_facecolor('black')

        waves = []
        for i in range(3):
            wave_line, = ax.plot([], [], linewidth=3.0 - i * 0.7, alpha=0.95 - i * 0.2)
            waves.append(wave_line)

        ax.set_xlim(0, 4 * np.pi)
        ax.set_ylim(-7, 7)  # Увеличил для большей динамики
        ax.axis('off')

        text = ax.text(0.02, 0.96, '', transform=ax.transAxes,
                       color='white', fontsize=10, fontfamily='monospace',
                       bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))

        def init():
            for wave in waves:
                wave.set_data([], [])
            text.set_text('')
            return waves + [text]

        def update(frame):
            time_sec = frame / fps

            x, base_wave, powers = self.generate_wave(time_sec)

            for i, wave_line in enumerate(waves):
                # Разные фазовые сдвиги для слоев
                phase_shift = i * 1.0 + self.autonomous_phase_mod * (i + 1)
                # Разная форма для каждого слоя
                layer_factor = 1.0 - i * 0.25
                frequency_factor = 1.0 + i * 0.1

                layer_wave = (base_wave * layer_factor *
                              np.sin(frequency_factor * x * 0.2 + phase_shift))

                color = self.get_wave_color(powers)

                # Динамические цвета для слоев
                r = self.clamp_color_value(color[0] * (1.0 - i * 0.15))
                g = self.clamp_color_value(color[1] * (1.0 - i * 0.1))
                b = self.clamp_color_value(color[2] * (1.0 + i * 0.2))
                a = self.clamp_color_value(color[3] * (0.95 - i * 0.15))

                layer_color = (r, g, b, a)

                wave_line.set_data(x, layer_wave)
                wave_line.set_color(layer_color)

            info = (f"Time: {time_sec:.1f}s | Freq: {self.current_frequency:.2f}\n"
                    f"Bass: {powers['lows']:.2f} | Mids: {powers['mids']:.2f} | Highs: {powers['highs']:.2f}\n"
                    f"Total: {sum(powers.values()):.2f}")
            text.set_text(info)

            return waves + [text]

        total_frames = int(duration_sec * fps)
        ani = animation.FuncAnimation(fig, update, frames=total_frames,
                                      init_func=init, blit=True, interval=1000 / fps)

        writer = FFMpegWriter(fps=fps, metadata=dict(artist='SpectroSync'))
        ani.save(output_file, writer=writer, dpi=150)
        plt.close()

        return ani

    def render_with_audio(self, temp_output_path='temp_video.mp4', duration_sec=5, fps=30, output_path='output.mp4'):
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
a._set_audio_path("C:\\Users\\Qeenky\\Desktop\\SpectroSync\\input_data\\music.mp3")  # absolute path
a._precompute_all_powers()

viz = WaveVisualizer(a)

visual = viz.render_with_audio(duration_sec=80, output_path='overdose4.mp4', fps=60)