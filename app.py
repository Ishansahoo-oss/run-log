import sqlite3
from flask import Flask, g, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")
DB_FILE = "runs.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                distance_km REAL NOT NULL,
                minutes REAL NOT NULL,
                note TEXT DEFAULT ''
            )"""
        )


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/runs")
def list_runs():
    rows = get_db().execute(
        "SELECT * FROM runs ORDER BY run_date DESC, id DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/runs")
def add_run():
    data = request.get_json(silent=True) or {}
    try:
        run_date = str(data["run_date"])
        distance = float(data["distance_km"])
        minutes = float(data["minutes"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Enter a date, a distance and a time."), 400
    if distance <= 0 or minutes <= 0:
        return jsonify(error="Distance and time must be greater than zero."), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO runs (run_date, distance_km, minutes, note) VALUES (?, ?, ?, ?)",
        (run_date, distance, minutes, str(data.get("note", ""))[:200]),
    )
    db.commit()
    return jsonify(id=cur.lastrowid), 201


@app.delete("/api/runs/<int:run_id>")
def delete_run(run_id):
    db = get_db()
    db.execute("DELETE FROM runs WHERE id = ?", (run_id,))
    db.commit()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
