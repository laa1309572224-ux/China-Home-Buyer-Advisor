import json
import re
import sqlite3
import sys
import urllib.request
from contextlib import contextmanager
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
DB = ROOT / "home_buyer.db"
ALLOWED_HOSTS = {"lianjia.com", "ke.com"}


@contextmanager
def db():
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY, source_url TEXT UNIQUE, title TEXT NOT NULL,
            city TEXT DEFAULT '', district TEXT DEFAULT '', community TEXT DEFAULT '',
            total_price REAL NOT NULL, unit_price REAL NOT NULL, area REAL NOT NULL,
            rooms TEXT DEFAULT '', year INTEGER, subway_minutes REAL,
            commute_minutes REAL, school_score REAL, risk_score REAL DEFAULT 50,
            notes TEXT DEFAULT '', updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS price_history (
            listing_id INTEGER NOT NULL, observed_at TEXT NOT NULL, total_price REAL NOT NULL,
            UNIQUE(listing_id, observed_at), FOREIGN KEY(listing_id) REFERENCES listings(id)
        );
    """)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def save_listing(item):
    required = ("title", "total_price", "unit_price", "area")
    if any(item.get(key) in (None, "") for key in required):
        raise ValueError("缺少必填字段：title、total_price、unit_price、area")
    numeric = {key: float(item[key]) for key in ("total_price", "unit_price", "area")}
    if min(numeric.values()) <= 0:
        raise ValueError("价格和面积必须大于 0")
    today = date.today().isoformat()
    fields = ["source_url", "title", "city", "district", "community", "total_price",
              "unit_price", "area", "rooms", "year", "subway_minutes", "commute_minutes",
              "school_score", "risk_score", "notes", "updated_at"]
    values = [item.get(k, "") for k in fields]
    values[5:8] = [numeric["total_price"], numeric["unit_price"], numeric["area"]]
    values[-1] = today
    with db() as conn:
        existing = conn.execute("SELECT id FROM listings WHERE source_url=? AND source_url<>''",
                                (item.get("source_url", ""),)).fetchone()
        if existing:
            assignments = ",".join(f"{f}=?" for f in fields[1:])
            conn.execute(f"UPDATE listings SET {assignments} WHERE id=?", values[1:] + [existing["id"]])
            listing_id = existing["id"]
        else:
            marks = ",".join("?" for _ in fields)
            listing_id = conn.execute(f"INSERT INTO listings ({','.join(fields)}) VALUES ({marks})", values).lastrowid
        conn.execute("INSERT OR REPLACE INTO price_history VALUES (?,?,?)",
                     (listing_id, today, numeric["total_price"]))
    return listing_id


def score(item, prefs):
    budget = max(float(prefs.get("budget", 300)), 1)
    max_commute = max(float(prefs.get("max_commute", 45)), 1)
    age = max(date.today().year - int(item["year"] or date.today().year), 0)
    parts = {
        "预算": max(0, 100 - max(float(item["total_price"]) - budget, 0) / budget * 160),
        "通勤": max(0, 100 - max(float(item["commute_minutes"] or max_commute) - max_commute, 0) * 3),
        "楼龄": max(0, 100 - age * 2),
        "教育": float(item["school_score"] or 50),
        "风险": 100 - float(item["risk_score"] or 50),
    }
    weights = {"预算": .32, "通勤": .26, "楼龄": .14, "教育": .14, "风险": .14}
    total = round(sum(parts[k] * weights[k] for k in parts), 1)
    decision = "优先看房" if total >= 80 else "保留比较" if total >= 65 else "谨慎考虑"
    return {"score": total, "decision": decision, "parts": {k: round(v, 1) for k, v in parts.items()}}


def collect(url):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not parsed.scheme == "https" or not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
        raise ValueError("只支持 https 链家或贝壳房源链接")
    request = urllib.request.Request(url, headers={"User-Agent": "HomeBuyerAdvisor/1.0 (+personal research)"})
    with urllib.request.urlopen(request, timeout=12) as response:
        html = response.read(2_000_000).decode("utf-8", "ignore")
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    amount = re.search(r'"totalPrice"\s*:\s*"?([\d.]+)', html)
    unit = re.search(r'"unitPrice"\s*:\s*"?([\d.]+)', html)
    area = re.search(r'(?:建筑面积|area)[^\d]{0,40}([\d.]+)\s*(?:㎡|平米)', html, re.I)
    return {
        "source_url": url,
        "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else "待补充房源",
        "total_price": float(amount.group(1)) if amount else None,
        "unit_price": float(unit.group(1)) if unit else None,
        "area": float(area.group(1)) if area else None,
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            raise ValueError("请求体过大")
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        if self.path == "/api/listings":
            with db() as conn:
                rows = [dict(row) for row in conn.execute("SELECT * FROM listings ORDER BY updated_at DESC, id DESC")]
                for row in rows:
                    row["history"] = [dict(x) for x in conn.execute(
                        "SELECT observed_at,total_price FROM price_history WHERE listing_id=? ORDER BY observed_at", (row["id"],))]
            return self.send_json(rows)
        if self.path == "/api/health":
            return self.send_json({"ok": True})
        return super().do_GET()

    def do_POST(self):
        try:
            body = self.read_json()
            if self.path == "/api/listings":
                return self.send_json({"id": save_listing(body)}, 201)
            if self.path == "/api/import":
                items = body if isinstance(body, list) else body.get("listings", [])
                return self.send_json({"imported": len([save_listing(x) for x in items])}, 201)
            if self.path == "/api/collect":
                return self.send_json(collect(body.get("url", "")))
            if self.path == "/api/score":
                prefs = body.get("preferences", {})
                with db() as conn:
                    rows = [dict(r) for r in conn.execute("SELECT * FROM listings")]
                return self.send_json([{**row, **score(row, prefs)} for row in rows])
            self.send_error(404)
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json({"error": str(error)}, 400)
        except Exception as error:
            self.send_json({"error": f"操作失败：{error}"}, 502)


def seed():
    with db() as conn:
        if conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]:
            return
    for item in json.loads((ROOT / "sample_data.json").read_text(encoding="utf-8")):
        save_listing(item)


if __name__ == "__main__":
    seed()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    print(f"购房决策助手：http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
