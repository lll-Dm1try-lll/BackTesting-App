# Backtester

Простой бэктестер для тестирования торговых стратегий на исторических данных.

---

## Основные возможности

- Загрузка исторических данных из CSV:
  - «классический» формат `datetime,open,high,low,close,volume`;
  - формат выгрузок с Nasdaq (`Date,Close/Last,Volume,Open,High,Low`, цены с `$` и запятыми).
- Простая модель брокера:
  - только long-позиции;
  - рыночные сделки по цене `close` или `open` в зависимости от режима;
  - процентная комиссия;
  - округление количества по шагу лота.
- Три стратегии:
  - `Buy & Hold` — один раз покупает и держит до конца периода;
  - `Moving Average Cross` — пересечение двух простых скользящих средних;
  - `Donchian Breakout` — пробой ценового канала по максимумам/минимумам за окно баров.
- Движок бэктестинга:
  - два режима исполнения ордеров:
    - `on_close` — по цене закрытия текущего бара;
    - `on_next_open` — по цене открытия следующего бара;
  - автоматический выход из позиции на последнем баре.
- Анализаторы результатов:
  - расширяемый список анализаторов (`Analyzer`-протокол);
  - встроенный `DrawdownAnalyzer` для расчёта максимальной просадки в абсолютных и относительных величинах.
- Выходные данные:
  - базовые метрики по результатам теста (начальный/конечный капитал, прибыль, % доходности, число сделок, метрики анализаторов);
  - список сделок (дата, направление, цена, количество, комиссия);
  - файл `equity_curve.csv` с кривой капитала;
  - объект `BacktestResult.series` с дополнительными временными рядами (например, `series["equity"]` как `TimeSeries`).

---

## Структура проекта

Корневая структура репозитория (упрощённо):

```text
.
├── backtester
│   ├── cli.py                 # CLI-обёртка
│   ├── core                   # ядро бэктестера
│   │   ├── analyzers.py       # анализаторы (Drawdown и др.)
│   │   ├── broker.py
│   │   ├── context.py
│   │   ├── datafeed.py
│   │   ├── engine.py
│   │   ├── enums.py
│   │   ├── errors.py
│   │   ├── result.py
│   │   ├── settings.py
│   │   ├── strategy_base.py
│   │   └── types.py
│   ├── strategies             # реализации стратегий
│   │   ├── buy_and_hold.py
│   │   ├── ma_cross.py
│   │   └── donchian_breakout.py
│   ├── data                   # примеры данных (AAPL, NVDA, sample)
│   ├── docs                   # Sphinx-документация (источники)
│   │   ├── api.rst
│   │   ├── conf.py
│   │   ├── index.rst
│   │   ├── performance.rst
│   │   ├── bpmn.png
│   │   └── uml.png
│   ├── profile_backtest.py    # запуск профилирования с cProfile
│   └── tests                  # unit-тесты
│       ├── test_analyzers.py
│       ├── test_broker.py
│       ├── test_datafeed.py
│       ├── test_donchian_strategy.py
│       ├── test_engine_strategies.py
│       └── test_result_series.py
├── pyproject.toml             # packaging-конфигурация (setuptools, wheel)
├── mypy.ini                   # настройки mypy
├── .github/workflows/ci.yml   # GitHub Actions: тесты, mypy, docs, сборка пакета
├── .github/workflows/publish.yml  # публикация wheel/sdist в GitHub Packages по тегам
└── README.md

---

## Требования

* Python 3.12 (проект разрабатывался и проверялся на 3.12).

Минимальные зависимости для разработки:

* `pytest` — для тестов;
* `mypy` — статический анализ типов;
* `sphinx` — генерация документации.

Дополнительно для сборки пакета (опционально):

* `build`, `twine` — для локальной сборки и публикации.

---

## Установка зависимостей

Из корня репозитория (простой вариант):

```bash
python -m pip install --upgrade pip
pip install pytest mypy sphinx
```

Либо, используя `pyproject.toml` и extras для разработки:

```bash
python -m pip install --upgrade pip
pip install -e .[dev]
```

(При необходимости используйте `python3` вместо `python`.)

---

## Формат входных данных

### 1. Базовый CSV-формат

Поддерживается CSV со следующими столбцами:

```text
datetime,open,high,low,close,volume
```

* `datetime` — дата/время в одном из форматов:

  * `YYYY-MM-DD`;
  * `YYYY-MM-DD HH:MM:SS`;
* остальные столбцы — числовые.

Пример:

```csv
datetime,open,high,low,close,volume
2025-01-01,1,2,0.5,1.5,1000
2025-01-02,1.5,2.5,1.0,2.0,1500
```

### 2. Формат Nasdaq

Поддерживается также формат выгрузок с Nasdaq:

```text
Date,Close/Last,Volume,Open,High,Low
```

Особенности:

* даты в американском формате `MM/DD/YYYY` (например, `11/28/2025`);
* цены и объёмы могут содержать:

  * символ `$` (`$278.85`).

Пример (эквивалентен тому, что читает код):

```csv
Date,Close/Last,Volume,Open,High,Low
11/28/2025,$278.85,20135620,$277.26,$279.00,$275.9865
```

Модуль `DataFeed` автоматически:

* находит нужные колонки (`Date`/`datetime`, `Close/Last`/`close`);
* очищает числа от `$` и запятых;
* парсит дату в `datetime`.

---

## Запуск бэктестера (CLI)

Запуск осуществляется из корня репозитория через модуль `backtester.cli`:

```bash
python -m backtester.cli --csv backtester/data/sample_data.csv --strategy ma
```

Основные аргументы:

* `--csv` — путь к CSV-файлу с данными (обязательный);
* `--strategy` — стратегия:

  * `bh` — Buy & Hold;
  * `ma` — Moving Average Cross;
  * `donchian` — Donchian Breakout (пробой ценового канала);
* `--fast`, `--slow` — параметры быстрой и медленной SMA для стратегии `ma` (по умолчанию `5` и `10`);
* `--donchian-window` — окно (в барах) для расчёта ценового канала в стратегии `donchian` (по умолчанию `20`);
* `--cash` — начальный капитал (по умолчанию `10000`);
* `--commission` — комиссия в долях (`0.001` = 0.1 %, по умолчанию `0`);
* `--mode` — режим исполнения ордеров:

  * `on_close` — по `close` текущего бара;
  * `on_next_open` — по `open` следующего бара;
* `--lot` — шаг лота (например, `1` для целых штук, `0.1` для десятых).

### Примеры

Запустить MA-стратегию на примере AAPL:

```bash
python -m backtester.cli \
  --csv backtester/data/AAPL_5Y.csv \
  --strategy ma \
  --fast 5 \
  --slow 10 \
  --cash 10000 \
  --commission 0.001 \
  --mode on_close \
  --lot 1
```

Запустить Buy & Hold на тех же данных:

```bash
python -m backtester.cli \
  --csv backtester/data/AAPL_5Y.csv \
  --strategy bh
```

Запустить Donchian Breakout на примере AAPL:

```bash
python -m backtester.cli \
  --csv backtester/data/AAPL_5Y.csv \
  --strategy donchian \
  --donchian-window 20 \
  --cash 10000 \
  --commission 0.0 \
  --mode on_close \
  --lot 1
```

### Вывод

Пример фрагмента вывода:

```text
=== METRICS ===
start_equity: 10000.0000
end_equity: 13524.2300
profit: 3524.2300
return_pct: 35.2423
trades: 132.0000
max_drawdown: 1500.0000
max_drawdown_pct: 75.0000

=== TRADES (dt, side, price, qty, commission) ===
2020-12-11T00:00:00, buy, 122.4100, 81.000000, 0.000000
...
```

Дополнительно создаётся файл `equity_curve.csv` в корне проекта:

```csv
datetime,equity
2020-12-11 00:00:00,10000.000000
2020-12-14 00:00:00,10080.000000
...
```

А также в `BacktestResult.series["equity"]` доступен тот же ряд в виде структуры `TimeSeries`.

---

## Тесты

Тесты лежат в `backtester/tests`.

Запуск всех тестов:

```bash
pytest backtester/tests
```

Тесты покрывают:

* работу брокера (покупка/продажа, влияние комиссии);
* логику движка с базовыми стратегиями (`BuyAndHold`, `MovingAverageCross`);
* загрузку данных, включая формат Nasdaq и обработку ошибок;
* поведение стратегии Donchian Breakout;
* работу анализатора просадки (`DrawdownAnalyzer`);
* согласованность `BacktestResult.series["equity"]` и `equity_curve`, а также поведение при пустом фиде.

---

## Статический анализ (mypy)

В корне репозитория лежит конфигурация `mypy.ini`.
Проверка типов:

```bash
mypy backtester
```

В проекте используются:

* аннотации типов для основных структур;
* `Protocol` для описания интерфейса стратегий (`Strategy`, `StrategyContext`) и анализаторов (`Analyzer`);
* `dataclass(slots=True)` для сущностей вроде `Bar`, `Trade`, `Action`, `BacktestSettings`, `BacktestResult`, `TimeSeries`.

---

## Документация (Sphinx)

Исходники Sphinx-документации находятся в `backtester/docs`.

Сборка HTML-доков:

```bash
sphinx-build -b html backtester/docs backtester/docs/_build/html
```

После успешной сборки основная страница будет в:

```text
backtester/docs/_build/html/index.html
```

В документации:

* краткое описание проекта;
* UML и BPMN диаграммы;
* автодокументация модулей ядра и стратегий (через `autodoc`);
* отдельный раздел по профилированию и производительности (`performance.rst`).

---

## Профилирование производительности

Для анализа производительности предусмотрен модуль `backtester.profile_backtest`.

Запуск профилирования:

```bash
python -m backtester.profile_backtest \
  --csv backtester/data/AAPL_5Y.csv \
  --strategy ma \
  --fast 5 --slow 10 \
  --cash 10000 \
  --commission 0.0 \
  --mode on_close \
  --lot 1.0 \
  --sort cumulative \
  --lines 30
```

Скрипт:

* запускает бэктест под `cProfile`;
* выводит ключевые метрики бэктеста;
* показывает top-N «тяжёлых» функций по выбранному критерию (`time` или `cumulative`).

Более подробное описание и идеи оптимизации приведены в документации (`backtester/docs/performance.rst`).

---

## Packaging и публикация (GitHub Packages)

Проект настроен как устанавливаемый Python-пакет:

* конфигурация сборки — в `pyproject.toml` (backend: `setuptools`);
* точка входа CLI:

  ```toml
  [project.scripts]
  backtester-cli = "backtester.cli:main"
  ```

Локальная сборка wheel и sdist:

```bash
python -m pip install --upgrade build
python -m build
```

Готовые артефакты появятся в директории `dist/`.

Публикация в GitHub Packages автоматизирована в workflow
`.github/workflows/publish.yml` и триггерится при пуше тегов вида `v*`:

* создаётся sdist и wheel;
* артефакты загружаются в registry GitHub Packages от имени репозитория
  с использованием `GITHUB_TOKEN`.

---

## CI (GitHub Actions)

В репозитории настроен GitHub Actions workflow: `.github/workflows/ci.yml`.

При пуше в ветки `main` и `dev`, а также при pull request:

1. Устанавливаются зависимости (`pytest`, `mypy`, `sphinx`, `build`).

2. Запускаются:

   * `pytest backtester/tests`;
   * `mypy backtester`;
   * `sphinx-build` для генерации HTML-документации;
   * `python -m build` для сборки wheel и sdist.

3. Готовые артефакты из `dist/` загружаются как build-artifacts.

Это позволяет автоматически контролировать, что:

* тесты проходят;
* типизация остаётся корректной;
* документация успешно собирается;
* пакет корректно собирается и готов к публикации.


