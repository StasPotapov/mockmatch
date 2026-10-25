# mockmatch

[English](README.md)

[Скилл](https://code.claude.com/docs/en/skills) для [Claude Code](https://code.claude.com/docs/en/overview) и CLI `mockmatch`.
Агент делает сайт, управляет headless-браузером детерминированными командами и сверяет результат
с дизайном: фреймом [Claude Design](https://claude.ai/design), HTML-макетом или PNG. Агент читает строки
текста, а не скриншоты. Это брат [adbm](https://github.com/StasPotapov/adbm): adbm делает то же для Android.

## Зачем

- **Детерминированно.** Страницу читают и сверяют с дизайном скрипты на Python, а не модель по скриншоту.
  `mockmatch click "Sign in" --expect "Dashboard"` находит элемент по тексту и нажимает его. Затем команда
  сообщает, какие тексты появились и пропали, и проверяет следующую страницу. Одна и та же команда
  на одной и той же странице даёт один и тот же ответ.
- **Сверка с дизайном — это числа.** `mockmatch compare` отрисовывает дизайн и сайт в одной ширине
  и сопоставляет их элементы. Затем он перечисляет расхождения: `h1 "Build sites…"  font-size 48→40`,
  `missing a "Docs"`, `div box "Card"  padding 20→16  (+2 inside moved)`. Агент правит CSS по этим строкам
  и запускает сверку снова. Сравнивать два скриншота на глаз ему не нужно.
- **Модель — только там, где скрипт бессилен.** Пиксельные участки, которые строки элементов
  не объясняют (иконки, картинки, градиенты), становятся маленькими вырезками «дизайн | сайт».
  Субагент `mockmatch-eyes` на дешёвой модели смотрит только их и пишет вердикт.
- **Меньше токенов.** Скриншот 1280×900 стоит модели ~1500 токенов, страница 1280×3000 — ~5000.
  `mockmatch ui` показывает простую страницу примерно за 150 токенов, а насыщенную — примерно за 1500
  (предел задаёт `--max`). Отчёт `compare` занимает 20–40 строк.
- **Тебе проще проверить.** На каждый прогон есть одна HTML-доска: сводка, вердикт, строки расхождений,
  шторка «дизайн ◀ ▶ сайт», карта разницы и вырезки.

## Что умеет

- **Управление браузером.** Один headless Chromium на проект живёт в фоне между вызовами. Поэтому вход
  в аккаунт, открытое меню и заполненная форма сохраняются. Команды: `open`, `ui` (страница текстом
  со ссылками `@e1`), `click`, `type`, `key`, `hover`, `scroll`, `wait`, `assert`, `batch`, `goto`, `back`,
  `reload`, `view` (размер окна и тема), `tabs`, `log` (ошибки консоли, упавшие запросы и ответы 4xx/5xx),
  `style` (вычисленные стили), `eval`, `look` (скриншот 640 px для агента), `shot` (полный размер, для тебя).
- **Источники дизайна.** `pull` сохраняет отрисованный файл Claude Design локально, без токена доступа.
  Проект и файл он записывает в `design/design.json`, поэтому следующая проверка обновит дизайн из того же места.
  `frames` перечисляет варианты на холсте Claude Design и даёт готовый селектор `--frame`.
- **Сверка с дизайном.** `compare` сопоставляет элементы по `data-mockmatch`, по точному тексту, затем
  по похожему тексту и положению. В каждой паре он сравнивает шрифт, размер, начертание, высоту строки,
  межбуквенный интервал, цвет, фон, рамку, скругление, тень, внутренние отступы, прозрачность, размеры,
  x и расстояние до элемента выше. Затем он делает пиксельную сверку с участками и вырезками.
  Можно задать несколько ширин (`--width 1440,390`) и тем (`--theme light,dark`). Сайт берётся по URL
  в чистой вкладке или из живой вкладки со всем её состоянием.
- **Вердикт и доска.** `mockmatch-eyes` читает только вырезки и пишет MATCH / PROBLEM / REVIEW в `notes.md`.
  `board` собирает HTML-страницу.
- **Учёт.** `status` показывает вызовы, токены, которые `mockmatch` вывел в контекст, и грубую оценку
  сэкономленных токенов.

## Как идёт сверка с дизайном

1. **Дизайн.** Агент берёт проект и файл из `design/design.json`, из твоей ссылки `claude.ai/design/p/…`
   или из списка проектов MCP `claude_design`. Он получает ссылку превью (`render_preview`) и сохраняет
   файл командой `mockmatch pull --project … --file …`. Затем он выбирает вариант через `mockmatch frames`.
2. **Сайт.** `mockmatch open http://localhost:5173` выводит страницу дев-сервера текстом.
3. **Сверка.** `mockmatch compare --design design/page.html --frame '[id="1b"] .dv-card'` выводит строки:

   ```
   == 960: 16/17 matched, 1 missing, 1 extra, 8 differ (8 major), match 47%, pixels 10.9%
   ! missing  a "Docs"  @888,21 32x16
   ! h1 "Build sites that match the design"  @40,123  font-size 48→40  line-height 52.8→44  height 53→44
   ! div box "Deterministic Same input, sam…"  @40,368  border-radius 10→6  padding 20→16  height 87→79  (+2 inside moved)
   ```

4. **Правка и повтор** — пока не останется строк с `!`.
5. **Вердикт.** `mockmatch-eyes` оценивает оставшиеся пиксельные участки, `mockmatch board` даёт тебе страницу.

## На чём построен

| Инструмент | Лицензия | Что делает в mockmatch |
|---|---|---|
| [Playwright for Python](https://playwright.dev/python/) | Apache 2.0 | запускает Chromium, подключается по Chrome DevTools Protocol, снимает скриншоты |
| [Chromium](https://www.chromium.org) (скачивает Playwright) | BSD-подобная | отрисовывает дизайн и сайт |
| [Pillow](https://python-pillow.github.io) | MIT-CMU | пиксельная сверка, участки, вырезки, карта разницы |

## Установка

Нужен Python 3.9+. Проверено на macOS; на Linux должно работать.

**Как плагин Claude Code** (рекомендуется): скилл, агент и хук ставятся одним шагом.

```
/plugin marketplace add StasPotapov/sp-tools
/plugin install mockmatch@sp-tools
```

Скилл тогда называется `/mockmatch:mockmatch`. Затем попроси агента выполнить `mockmatch doctor --install`: он создаст venv
с Playwright, Pillow и Chromium в `~/.local/share/mockmatch`. Этот каталог лежит вне кэша плагина, поэтому
обновление его не стирает. Новая версия: `/plugin marketplace update sp-tools`,
затем `claude plugin update mockmatch@sp-tools` (в терминале).

**Claude Design.** Дизайн из Claude Design приходит через MCP `claude_design`, а у него свой вход.
`mockmatch doctor` показывает, подключён ли он и что сделать, если нет. Сначала добавь его командой
`claude mcp add --transport http -s user claude_design https://api.anthropic.com/v1/design/mcp`.
Затем войди: `/mcp` → `claude_design` → Authenticate. HTML-макеты и PNG работают без него.

**Из клона.** Выбери один способ: с обоими скилл и хук загрузятся дважды.
Скилл и агент подключаются симлинками, хук — записью в `~/.claude/settings.json`.

```bash
git clone https://github.com/StasPotapov/mockmatch.git ~/dev/mockmatch
ln -s ~/dev/mockmatch/skill ~/.claude/skills/mockmatch
ln -s ~/dev/mockmatch/skill/agents/mockmatch-eyes.md ~/.claude/agents/mockmatch-eyes.md
~/dev/mockmatch/skill/bin/mockmatch doctor --install   # venv с Playwright, Pillow и Chromium в ~/.local/share/mockmatch
```

Хук-сторож запрещает агенту читать полноразмерные скриншоты. Добавь его в `~/.claude/settings.json`,
в `hooks.PreToolUse`:

```json
{ "matcher": "Read", "hooks": [{ "type": "command",
  "command": "f=~/.claude/skills/mockmatch/hooks/mockmatch-guard.py; [ -f \"$f\" ] || exit 0; exec python3 \"$f\"" }] }
```

В проекте `build/mockmatch/` хранит прогоны, скриншоты и состояние браузера: добавь `build/` в `.gitignore`.
`mockmatch doctor` предупредит, если каталог не игнорируется.

## Тесты

```bash
~/.local/share/mockmatch/venv/bin/pip install pytest
~/.local/share/mockmatch/venv/bin/python -m pytest tests -q
```

Модульные тесты проверяют разбор цветов и стилей, сопоставление, сворачивание вложенных сдвигов и хук.
Браузерные тесты запускают `compare` на `tests/fixtures/` и управляют сессией.

## Файлы

- `skill/SKILL.md` — скилл: когда и как агент пользуется `mockmatch`.
- `skill/bin/mockmatch` — CLI, один файл на Python.
- `skill/reference/design-check.md` — подробно про `compare`; `troubleshooting.md` — симптомы и решения.
- `skill/agents/mockmatch-eyes.md` — субагент-вердикт.
- `skill/hooks/` — хук-сторож и его конфиг для плагина.
- `tests/` — pytest и HTML-фикстуры.
- `docs/alternatives.ru.md` — похожие инструменты и зачем нужен mockmatch.

## Лицензия

MIT
