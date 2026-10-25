# CDPM — Chrome DevTools Protocol Matrix

[English](README.md)

[Скилл](https://code.claude.com/docs/en/skills) для [Claude Code](https://code.claude.com/docs/en/overview) и CLI `cdpm`.
Агент делает сайт, управляет headless-браузером детерминированными командами и сверяет результат
с дизайном: фреймом [Claude Design](https://claude.ai/design), HTML-макетом или PNG. Агент читает строки
текста, а не скриншоты. Это брат [adbm](https://github.com/StasPotapov/adbm): adbm делает то же для Android.

## Зачем

- **Детерминированно.** Страницу читают и сверяют с дизайном скрипты на Python, а не модель по скриншоту.
  `cdpm click "Sign in" --expect "Dashboard"` находит элемент по тексту и нажимает его. Затем команда
  сообщает, какие тексты появились и пропали, и проверяет следующую страницу. Одна и та же команда
  на одной и той же странице даёт один и тот же ответ.
- **Сверка с дизайном — это числа.** `cdpm compare` отрисовывает дизайн и сайт в одной ширине
  и сопоставляет их элементы. Затем он перечисляет расхождения: `h1 "Build sites…"  font-size 48→40`,
  `missing a "Docs"`, `div box "Card"  padding 20→16  (+2 inside moved)`. Агент правит CSS по этим строкам
  и запускает сверку снова. Сравнивать два скриншота на глаз ему не нужно.
- **Модель — только там, где скрипт бессилен.** Пиксельные участки, которые строки элементов
  не объясняют (иконки, картинки, градиенты), становятся маленькими вырезками «дизайн | сайт».
  Субагент `cdpm-eyes` на дешёвой модели смотрит только их и пишет вердикт.
- **Меньше токенов.** Скриншот 1280×900 стоит модели ~1500 токенов, страница 1280×3000 — ~5000.
  `cdpm ui` показывает простую страницу примерно за 150 токенов, а насыщенную — примерно за 1500
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
  `frames` перечисляет варианты на холсте Claude Design и даёт готовый селектор `--frame`.
- **Сверка с дизайном.** `compare` сопоставляет элементы по `data-cdpm`, по точному тексту, затем
  по похожему тексту и положению. В каждой паре он сравнивает шрифт, размер, начертание, высоту строки,
  межбуквенный интервал, цвет, фон, рамку, скругление, тень, внутренние отступы, прозрачность, размеры,
  x и расстояние до элемента выше. Затем он делает пиксельную сверку с участками и вырезками.
  Можно задать несколько ширин (`--width 1440,390`) и тем (`--theme light,dark`). Сайт берётся по URL
  в чистой вкладке или из живой вкладки со всем её состоянием.
- **Вердикт и доска.** `cdpm-eyes` читает только вырезки и пишет MATCH / PROBLEM / REVIEW в `notes.md`.
  `board` собирает HTML-страницу.
- **Учёт.** `status` показывает вызовы, токены, которые `cdpm` вывел в контекст, и грубую оценку
  сэкономленных токенов.

## Как идёт сверка с дизайном

1. **Дизайн.** Агент получает ссылку превью на файл Claude Design (`render_preview` из MCP `claude_design`).
   Затем он сохраняет дизайн командой `cdpm pull` и выбирает вариант через `cdpm frames`.
2. **Сайт.** `cdpm open http://localhost:5173` выводит страницу дев-сервера текстом.
3. **Сверка.** `cdpm compare --design design/page.html --frame '[id="1b"] .dv-card'` выводит строки:

   ```
   == 960: 16/17 matched, 1 missing, 1 extra, 8 differ (8 major), match 47%, pixels 10.9%
   ! missing  a "Docs"  @888,21 32x16
   ! h1 "Build sites that match the design"  @40,123  font-size 48→40  line-height 52.8→44  height 53→44
   ! div box "Deterministic Same input, sam…"  @40,368  border-radius 10→6  padding 20→16  height 87→79  (+2 inside moved)
   ```

4. **Правка и повтор** — пока не останется строк с `!`.
5. **Вердикт.** `cdpm-eyes` оценивает оставшиеся пиксельные участки, `cdpm board` даёт тебе страницу.

## На чём построен

| Инструмент | Лицензия | Что делает в CDPM |
|---|---|---|
| [Playwright for Python](https://playwright.dev/python/) | Apache 2.0 | запускает Chromium, подключается по Chrome DevTools Protocol, снимает скриншоты |
| [Chromium](https://www.chromium.org) (скачивает Playwright) | BSD-подобная | отрисовывает дизайн и сайт |
| [Pillow](https://python-pillow.github.io) | MIT-CMU | пиксельная сверка, участки, вырезки, карта разницы |

## Установка

Нужен Python 3.9+. Проверено на macOS; на Linux должно работать.

**Из клона.** Скилл и агент подключаются симлинками, хук — записью в `~/.claude/settings.json`.

```bash
git clone https://github.com/StasPotapov/cdpm.git ~/dev/cdpm
ln -s ~/dev/cdpm/skill ~/.claude/skills/cdpm
ln -s ~/dev/cdpm/skill/agents/cdpm-eyes.md ~/.claude/agents/cdpm-eyes.md
~/dev/cdpm/skill/bin/cdpm doctor --install   # venv с Playwright, Pillow и Chromium в ~/.local/share/cdpm
```

Хук-сторож запрещает агенту читать полноразмерные скриншоты. Добавь его в `~/.claude/settings.json`,
в `hooks.PreToolUse`:

```json
{ "matcher": "Read", "hooks": [{ "type": "command",
  "command": "f=~/.claude/skills/cdpm/hooks/cdpm-guard.py; [ -f \"$f\" ] || exit 0; exec python3 \"$f\"" }] }
```

**Как плагин Claude Code.** Репозиторий — ещё и плагин (`.claude-plugin/`): скилл, агент и хук ставятся
одним шагом. Затем попроси агента выполнить `cdpm doctor --install`.

В проекте `build/cdpm/` хранит прогоны, скриншоты и состояние браузера: добавь `build/` в `.gitignore`.
`cdpm doctor` предупредит, если каталог не игнорируется.

## Тесты

```bash
~/.local/share/cdpm/venv/bin/pip install pytest
~/.local/share/cdpm/venv/bin/python -m pytest tests -q
```

Модульные тесты проверяют разбор цветов и стилей, сопоставление, сворачивание вложенных сдвигов и хук.
Браузерные тесты запускают `compare` на `tests/fixtures/` и управляют сессией.

## Файлы

- `skill/SKILL.md` — скилл: когда и как агент пользуется `cdpm`.
- `skill/bin/cdpm` — CLI, один файл на Python.
- `skill/reference/design-check.md` — подробно про `compare`; `troubleshooting.md` — симптомы и решения.
- `skill/agents/cdpm-eyes.md` — субагент-вердикт.
- `skill/hooks/` — хук-сторож и его конфиг для плагина.
- `tests/` — pytest и HTML-фикстуры.
- `docs/alternatives.md` — похожие инструменты и зачем нужен cdpm.

## Лицензия

MIT
