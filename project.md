# OpenVideoEncoder v0.3.0

## О проекте

Кроссплатформенное GUI-приложение для пакетного перекодирования видео через FFmpeg.

## Новое в v0.3.0

- **Двухпроходное кодирование** — `encode_two_pass()` с точным попаданием в целевой размер
- **Битрейт-калькулятор** — формула Коры: `(target_mb × 8388.608 × 0.98) / duration_sec − audio_kbps`
- **Автостратегия очереди** — `max_size_mb` в профиле → два прохода, иначе CRF
- **UUID для задач** — уникальные идентификаторы вместо числовых счётчиков
- **5 пресетов** — YouTube, Telegram Free, Telegram Premium, VK, YouTube Good
- **Автоочистка pass-логов** — `finally`-блок удаляет временные файлы FFmpeg
- **Новые параметры FFmpeg** — `-profile:v`, `-g`, `-bf`, `-color_primaries`, `-color_trc`, `-colorspace`, `-ar`
- **Status callback** — UI-статусы «Encoding (Pass 1/2)...» / «Encoding (Pass 2/2)...»

## Структура

```
open-video-encoder-v0.3/
├── core/
│   ├── __init__.py              # v0.3.0, экспорт битрейт-калькулятора
│   ├── analyzer.py              # VideoAnalyzer — ffprobe
│   ├── bitrate_calculator.py    # формула Коры + null-девайс
│   ├── encoder.py               # VideoEncoder + encode_two_pass
│   ├── ffmpeg.py                # run_ffmpeg — обёртка subprocess
│   ├── history.py               # история кодирования
│   ├── profiles.py              # ProfileManager
│   └── queue.py                 # JobQueue (UUID-based)
├── gui/
│   ├── __init__.py
│   ├── dialogs.py               # диалоги выбора файлов/профилей
│   ├── main_window.py           # главное окно + автостратегия
│   ├── queue_widget.py          # виджет очереди
│   └── settings.py              # константы (v0.3)
├── profiles/
│   ├── youtube_best.json        # YouTube max quality, CRF 18
│   ├── youtube_good.json        # YouTube balanced, CRF 22
│   ├── telegram_free.json       # Telegram Free, 2 GB limit
│   ├── telegram_premium.json    # Telegram Premium, 4 GB limit
│   └── vk.json                  # VK, 2 GB limit
├── tests/
│   ├── __init__.py
│   ├── test_analyzer.py
│   ├── test_bitrate_calculator.py
│   ├── test_encoder.py
│   ├── test_queue.py
│   ├── test_gui_dialogs.py
│   ├── test_gui_main_window.py
│   ├── test_gui_queue_widget.py
│   └── test_gui_settings.py
├── main.py                      # точка входа
└── project.md                   # этот файл
```

## Быстрый старт

```bash
python3 main.py
```

## Запуск тестов

```bash
python3 -m unittest discover tests/ -v
```

## Профили

Формат профиля (v0.3):

```json
{
  "video": {
    "codec": "libx264",
    "crf": 22,
    "preset": "slow",
    "profile": "high",
    "gop": 30,
    "bf": 2,
    "color_primaries": "bt709",
    "color_trc": "bt709",
    "color_space": "bt709"
  },
  "audio": {
    "codec": "aac",
    "sample_rate": 48000
  },
  "limits": {
    "max_size_mb": null
  }
}
```

- `limits.max_size_mb` = null → однопроходное CRF-кодирование
- `limits.max_size_mb` = число → двухпроходное кодирование с целевым размером