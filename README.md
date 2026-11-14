# Портфолио Карины

Кинематографичное портфолио художницы Карины на FastAPI, Jinja2, CSS и JavaScript.

## Что внутри

- главная страница с блоком «Обо мне» и четырьмя галереями работ;
- старый адрес `/works` открывает галерею на главной;
- страница контактов с телефоном, Telegram и VK;
- полноэкранная кинематографичная главная, переходы между страницами, параллакс, интерактивный курсор и индикатор прокрутки;
- адаптивное меню, анимации и доступная разметка;
- health-check и базовые автотесты.

## Запуск в VS Code

1. Откройте папку `portfolio-fastapi` в VS Code.
2. Откройте встроенный терминал и создайте окружение:

```bash
python -m venv .venv
```

3. Активируйте его:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

4. Установите зависимости и запустите сайт:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --no-server-header
```

5. Откройте `http://127.0.0.1:8000`.

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
```

## Что заменить перед публикацией

- имя и описание в шаблонах;
- почту и ссылки на соцсети в `app/templates/base.html` и `contact.html`;
- тексты и цены `PRICES` в `app/main.py`;
- новые изображения — в папку своего раздела: `jivo`, `portret`, `grafika` или `pastel` внутри `app/static/images`. Папка `paintings` на сайте не показывается;
- добавьте портрет сестры как `app/static/images/portrait.jpg` — он появится в отдельном вертикальном кадре без искажения пропорций.
