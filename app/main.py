from pathlib import Path
import re
from struct import error as StructError
from struct import unpack

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


BASE_DIR = Path(__file__).resolve().parent

# Local HTTP review must keep working, so this policy has no
# upgrade-insecure-requests. HSTS is added only for HTTPS responses.
CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'none'",
        "script-src 'self'",
        "style-src 'self' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self'",
        "connect-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com",
    )
)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                headers["Permissions-Policy"] = (
                    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
                    "magnetometer=(), microphone=(), payment=(), usb=()"
                )
                headers["Cross-Origin-Opener-Policy"] = "same-origin"
                headers["X-Permitted-Cross-Domain-Policies"] = "none"
                if scope.get("scheme") == "https":
                    headers["Strict-Transport-Security"] = "max-age=15552000"
            await send(message)

        await self.app(scope, receive, send_with_headers)


app = FastAPI(
    title="Карина — художница",
    description="Портфолио художницы Карины из Ульяновска",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(SecurityHeadersMiddleware)
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static", follow_symlink=False),
    name="static",
)
templates = Jinja2Templates(directory=BASE_DIR / "templates")
IMAGE_ROOT = BASE_DIR / "static" / "images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ORDINALS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "pervii": 1,
    "pervyi": 1,
    "vtoroi": 2,
    "tretii": 3,
    "chetvertii": 4,
    "chetvertyi": 4,
    "piatii": 5,
    "pyatyi": 5,
    "shestoi": 6,
    "sedmoi": 7,
    "vosmoi": 8,
}

# Новая работа появляется в галерее сама: файл нужно положить в папку раздела.
# Папка paintings на сайте не используется.
SECTIONS = [
    {"id": "zhivopis", "number": "02", "title": "Живопись", "folder": "jivo"},
    {"id": "portret", "number": "03", "title": "Портрет", "folder": "portret"},
    {"id": "grafika", "number": "04", "title": "Графика", "folder": "grafika"},
    {"id": "pastel", "number": "05", "title": "Пастель", "folder": "pastel"},
]

PRICES = [
    {"title": "Живопись", "amount": "от 15 000 ₽"},
    {"title": "Портрет", "amount": "от 5 000 ₽"},
]


MAX_IMAGE_HEADER_SCAN = 2 * 1024 * 1024


def stays_inside(path: Path, root: Path) -> bool:
    """Reject symlinks and paths that resolve outside root."""
    if path.is_symlink():
        return False
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(32)
            if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
                width, height = unpack(">II", header[16:24])
                return _sane_size(width, height)
            if not header.startswith(b"\xff\xd8"):
                return None

            handle.seek(2)
            while handle.tell() < MAX_IMAGE_HEADER_SCAN:
                marker_prefix = handle.read(1)
                if not marker_prefix:
                    return None
                if marker_prefix != b"\xff":
                    continue

                marker = handle.read(1)
                while marker == b"\xff":
                    marker = handle.read(1)
                    if not marker:
                        return None
                if not marker:
                    return None

                code = marker[0]
                if code in (0xC0, 0xC1, 0xC2):
                    handle.read(3)
                    size_bytes = handle.read(4)
                    if len(size_bytes) < 4:
                        return None
                    height, width = unpack(">HH", size_bytes)
                    return _sane_size(width, height)
                if code in (0xD9, 0xDA):
                    return None
                if code in (0x01, 0xD8) or 0xD0 <= code <= 0xD7:
                    continue

                length_bytes = handle.read(2)
                if len(length_bytes) < 2:
                    return None
                segment_length = unpack(">H", length_bytes)[0]
                if segment_length < 2:
                    return None
                handle.seek(segment_length - 2, 1)
    except (OSError, StructError):
        return None
    return None


def _sane_size(width: int, height: int) -> tuple[int, int] | None:
    if 0 < width <= 20000 and 0 < height <= 20000:
        return width, height
    return None


def work_sort_key(path: Path) -> tuple:
    stem = path.stem.lower()
    if stem in ORDINALS:
        return (0, ORDINALS[stem], stem)
    digits = re.search(r"\d+", stem)
    if digits:
        return (0, int(digits.group()), stem)
    return (1, 0, stem)


def load_galleries() -> list[dict]:
    galleries = []
    for section in SECTIONS:
        folder_name = section["folder"]
        folder = IMAGE_ROOT / folder_name
        files = []
        if (
            Path(folder_name).name == folder_name
            and folder.is_dir()
            and stays_inside(folder, IMAGE_ROOT)
        ):
            files = sorted(
                (
                    path
                    for path in folder.iterdir()
                    if path.is_file()
                    and stays_inside(path, folder)
                    and not path.name.startswith(".")
                    and path.suffix.lower() in IMAGE_EXTENSIONS
                ),
                key=work_sort_key,
            )

        images = []
        for index, path in enumerate(files, start=1):
            width, height = image_size(path) or (4, 5)
            images.append(
                {
                    "src": f"/static/images/{section['folder']}/{path.name}",
                    "alt": f"{section['title']}, работа {index}",
                    "number": f"{index:02d}",
                    "width": width,
                    "height": height,
                    "ratio": f"{width / height:.5f}",
                }
            )
        galleries.append({**section, "images": images})
    return galleries


def context(request: Request, page: str, **extra):
    return {
        "request": request,
        "page": page,
        "sections": load_galleries(),
        "prices": PRICES,
        **extra,
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=context(request, "home"),
    )


@app.get("/works", include_in_schema=False)
async def works():
    return RedirectResponse(url="/#works", status_code=302)


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context=context(request, "contact"),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
