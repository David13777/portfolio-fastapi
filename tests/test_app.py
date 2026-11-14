import starlette
from fastapi.testclient import TestClient

from app.main import app, load_galleries


def test_pages_and_health():
    with TestClient(app) as client:
        home = client.get("/")
        assert home.status_code == 200
        assert "Карина" in home.text
        assert "Тишина" in home.text
        for title in ("Живопись", "Портрет", "Графика", "Пастель"):
            assert title in home.text
        assert "от 15 000 ₽" in home.text
        assert "от 5 000 ₽" in home.text
        assert home.text.index(">01 /</span> Обо мне") < home.text.index("<dt>02</dt>")
        assert "<dt>01</dt>" not in home.text
        assert home.text.index("<dt>02</dt><dd>живопись</dd>") < home.text.index("<dt>05</dt><dd>пастель</dd>")
        assert ">02</span>" in home.text and ">06 /</span> Цены" in home.text
        assert "paintings/" not in home.text
        assert home.text.index("/static/images/jivo/pervii.jpg") < home.text.index("/static/images/jivo/vtoroi.jpg")
        assert home.text.index("/static/images/portret/one.jpg") < home.text.index("/static/images/portret/two.jpg")
        assert home.text.index("/static/images/portret/two.jpg") < home.text.index("/static/images/portret/six.jpg")
        assert 'width="952"' in home.text
        assert client.get("/static/images/jivo/pervii.jpg").status_code == 200
        assert client.get("/static/images/portret/one.jpg").status_code == 200
        assert client.get("/static/images/grafika/graf1.jpg").status_code == 200
        assert client.get("/static/images/pastel/past1.jpg").status_code == 200

        works = client.get("/works", follow_redirects=False)
        assert works.status_code == 302
        assert works.headers["location"] == "/#works"

        contact = client.get("/contact")
        assert contact.status_code == 200
        assert "tel:+79677745380" in contact.text
        assert "https://t.me/+79677745380" in contact.text
        assert 'rel="noopener noreferrer"' in contact.text
        assert "contact-band" in contact.text
        assert "contact-form" not in contact.text
        assert 'style="--ratio:' not in home.text
        assert 'data-ratio="' in home.text
        assert client.get("/health").json() == {"status": "ok"}


def test_gallery_order_and_sources():
    by_id = {section["id"]: section for section in load_galleries()}
    assert [image["src"].rsplit("/", 1)[-1] for image in by_id["zhivopis"]["images"]] == [
        "pervii.jpg",
        "vtoroi.jpg",
        "tretii.jpg",
        "chetvertii.jpg",
        "piatii.jpg",
        "shestoi.jpg",
    ]
    assert [image["src"].rsplit("/", 1)[-1] for image in by_id["portret"]["images"]] == [
        "one.jpg",
        "two.jpg",
        "three.jpg",
        "four.jpg",
        "five.jpg",
        "six.jpg",
    ]
    assert [image["src"].rsplit("/", 1)[-1] for image in by_id["grafika"]["images"]] == [
        "graf1.jpg",
        "graf2.jpg",
        "graf3.jpg",
        "graf4.jpg",
        "graf5.jpg",
    ]
    assert len(by_id["pastel"]["images"]) == 3
    assert all(
        "paintings" not in image["src"]
        for section in load_galleries()
        for image in section["images"]
    )


def test_security_headers_and_closed_docs():
    version = tuple(int(part) for part in starlette.__version__.split(".")[:2])
    assert version >= (1, 3)

    with TestClient(app) as client:
        home = client.get("/")
        policy = home.headers["content-security-policy"]
        assert "default-src 'self'" in policy
        assert "frame-ancestors 'none'" in policy
        assert "unsafe-inline" not in policy
        assert "upgrade-insecure-requests" not in policy
        assert home.headers["x-content-type-options"] == "nosniff"
        assert home.headers["x-frame-options"] == "DENY"
        assert home.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert home.headers["cross-origin-opener-policy"] == "same-origin"
        assert "camera=()" in home.headers["permissions-policy"]
        assert "strict-transport-security" not in home.headers
        assert "server" not in home.headers

        static = client.get("/static/css/style.css")
        assert static.status_code == 200
        assert static.headers["x-content-type-options"] == "nosniff"

        for path in ("/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 404

        escaped = client.get("/static/images/%2e%2e/%2e%2e/%2e%2e/main.py")
        assert escaped.status_code == 404
        assert b"FastAPI" not in escaped.content
        unc = client.get("/static/%5C%5C127.0.0.1%5Cshare%5Csecret")
        assert unc.status_code == 404

        ranges = ",".join(f"{index}-{index}" for index in range(0, 400, 2))
        ranged = client.get("/static/css/style.css", headers={"Range": f"bytes={ranges}"})
        assert ranged.status_code in (200, 206, 416)

    with TestClient(app, base_url="https://portfolio.test") as client:
        secure = client.get("/")
        assert secure.headers["strict-transport-security"] == "max-age=15552000"

