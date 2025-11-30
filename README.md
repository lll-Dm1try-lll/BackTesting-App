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
- Две стратегии:
  - `Buy & Hold` — один раз покупает и держит до конца периода;
  - `Moving Average Cross` — пересечение двух простых скользящих средних.
- Движок бэктестинга:
  - два режима исполнения ордеров:
    - `on_close` — по цене закрытия текущего бара;
    - `on_next_open` — по цене открытия следующего бара;
  - автоматический выход из позиции на последнем баре.
- Выходные данные:
  - базовые метрики по результатам теста (начальный/конечный капитал, прибыль, % доходности, число сделок);
  - список сделок (дата, направление, цена, количество, комиссия);
  - файл `equity_curve.csv` с кривой капитала.

---

## Структура проекта

Корневая структура репозитория (упрощённо):

```text
.
├── backtester
│   ├── cli.py                # CLI-обёртка
│   ├── core                  # ядро бэктестера
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
│   ├── strategies            # реализации стратегий
│   │   ├── buy_and_hold.py
│   │   └── ma_cross.py
│   ├── data                  # примеры данных (AAPL, NVDA, sample)
│   ├── docs                  # Sphinx-документация (источники)
│   │   ├── api.rst
│   │   ├── conf.py
│   │   ├── index.rst
│   │   ├── bpmn.png
│   │   └── uml.png
│   └── tests                 # unit-тесты
│       ├── test_broker.py
│       ├── test_datafeed.py
│       └── test_engine_strategies.py
├── mypy.ini                  # настройки mypy
├── .github/workflows/ci.yml  # GitHub Actions: тесты, mypy, docs
└── README.md                
````

---

## Требования

* Python 3.12 (проект разрабатывался и проверялся на 3.12).

Минимальные зависимости для разработки:

* `pytest` — для тестов;
* `mypy` — статический анализ типов;
* `sphinx` — генерация документации.

---

## Установка зависимостей

Из корня репозитория:

```bash
python -m pip install --upgrade pip
pip install pytest mypy sphinx
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
* `--fast`, `--slow` — параметры быстрой и медленной SMA для стратегии `ma` (по умолчанию `5` и `10`);
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

### Вывод

Пример фрагмента вывода:

```text
=== METRICS ===
start_equity: 10000.0000
end_equity: 13524.2300
profit: 3524.2300
return_pct: 35.2423
trades: 132.0000

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

---

## Тесты

Тесты лежат в `backtester/tests`.

Запуск всех тестов:

```bash
pytest backtester/tests
```

Тесты проверяют:

* работу брокера (покупка/продажа, влияние комиссии);
* логику движка с двумя стратегиями;
* загрузку данных, включая формат Nasdaq и обработку ошибок.

---

## Статический анализ (mypy)

В корне репозитория лежит конфигурация `mypy.ini`.
Проверка типов:

```bash
mypy backtester
```

В проекте используются:

* аннотации типов для основных структур;
* `Protocol` для описания интерфейса стратегий (`Strategy`, `StrategyContext`);
* `dataclass(slots=True)` для сущностей вроде `Bar`, `Trade`, `Action`, `BacktestSettings`, `BacktestResult`.

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
* автодокументация модулей ядра и стратегий (через `autodoc`).

---

## CI (GitHub Actions)

В репозитории настроен GitHub Actions workflow: `.github/workflows/ci.yml`.

При пуше в ветки `main` и `dev`, а также при pull request:

1. Устанавливаются зависимости (`pytest`, `mypy`, `sphinx`).
2. Запускаются:

   * `pytest backtester/tests`;
   * `mypy backtester`;
   * `sphinx-build` для генерации HTML-документации.

Это позволяет автоматически контролировать, что:

* тесты проходят;
* типизация остаётся корректной;
* документация продолжает успешно собираться.
---