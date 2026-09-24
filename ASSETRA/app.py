from datetime import datetime
import os
import secrets
import string
import sqlite3

from db import get_db, init_db
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("ASSETRA_SECRET_KEY", "dev-secret-change-me")

STATUSES = ["Available", "Assigned", "In Repair", "Retired", "Lost"]
CONDITIONS = ["New", "Good", "Fair", "Poor", "Damaged"]
CATEGORIES = [
    "Laptop",
    "Desktop",
    "Monitor",
    "Printer",
    "Tool",
    "Equipment",
    "Furniture",
    "Other",
]

# --- Permissions Configuration ---
PERMISSIONS = {
    "superadmin": {"*"},
    "admin": {"asset:add", "asset:delete"},  # Removed "user:manage" from admin
    "user": {"asset:add"},
}


def can(role, action):
  perms = PERMISSIONS.get(role, set())
  return "*" in perms or action in perms


def current_account():
  uid = session.get("uid")
  if not uid:
    return None
  conn = get_db()
  acc = conn.execute("SELECT * FROM accounts WHERE id = ?", (uid,)).fetchone()
  conn.close()
  return acc if acc and acc["is_active"] else None


def require(action=None):
  """Login required. If `action` is given, role must also be allowed to do it."""

  def decorator(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
      acc = current_account()
      if not acc:
        return redirect(url_for("login"))
      if action and not can(acc["role"], action):
        flash("You don't have permission to do that.", "error")
        return redirect(url_for("dashboard"))
      g.account = acc
      return fn(*args, **kwargs)

    return wrapper

  return decorator


def generate_password(length=12):
  chars = string.ascii_letters + string.digits
  return "".join(secrets.choice(chars) for _ in range(length))


@app.context_processor
def inject_globals():
  acc = current_account()
  return {"current_year": datetime.now().year, "me": acc, "can": can}


def log_history(conn, asset_id, action, details=None, performed_by="System"):
  conn.execute(
      "INSERT INTO asset_history (asset_id, action, details, performed_by)"
      " VALUES (?, ?, ?, ?)",
      (asset_id, action, details, performed_by),
  )


def get_lookup_lists(conn):
  locations = conn.execute("SELECT * FROM locations ORDER BY name").fetchall()
  employees = conn.execute(
      "SELECT * FROM employees WHERE active = 1 ORDER BY full_name"
  ).fetchall()
  return locations, employees


# ---------- Auth Routes ----------
@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    conn = get_db()
    acc = conn.execute(
        "SELECT * FROM accounts WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if (
        acc
        and acc["is_active"]
        and check_password_hash(acc["password_hash"], password)
    ):
      session.clear()
      session["uid"] = acc["id"]
      flash("Logged in successfully.", "success")
      return redirect(url_for("dashboard"))
    flash("Invalid username or password.", "error")
  return render_template("login.html")


@app.route("/logout")
def logout():
  session.clear()
  flash("Logged out successfully.", "info")
  return redirect(url_for("login"))


# ---------- Dashboard & Assets ----------
@app.route("/")
@require()
def dashboard():
  conn = get_db()
  total = conn.execute("SELECT COUNT(*) c FROM assets").fetchone()["c"]
  by_status = conn.execute(
      "SELECT status, COUNT(*) c FROM assets GROUP BY status"
  ).fetchall()
  by_category = conn.execute(
      "SELECT category, COUNT(*) c FROM assets GROUP BY category ORDER BY c DESC"
  ).fetchall()
  recent_activity = conn.execute(
      """SELECT h.*, a.name AS asset_name, a.asset_tag
           FROM asset_history h JOIN assets a ON a.id = h.asset_id
           ORDER BY h.timestamp DESC LIMIT 8"""
  ).fetchall()
  needs_attention = conn.execute(
      "SELECT * FROM assets WHERE status IN ('In Repair','Lost') ORDER BY"
      " updated_at DESC LIMIT 6"
  ).fetchall()

  account_count = conn.execute("SELECT COUNT(*) c FROM accounts").fetchone()["c"]
  conn.close()

  status_map = {row["status"]: row["c"] for row in by_status}
  stats = {"accounts": account_count, "assets": total}

  return render_template(
      "dashboard.html",
      total=total,
      stats=stats,
      status_map=status_map,
      statuses=STATUSES,
      by_category=by_category,
      recent_activity=recent_activity,
      needs_attention=needs_attention,
  )


@app.route("/assets")
@require()
def asset_list():
  q = request.args.get("q", "").strip()
  status = request.args.get("status", "")
  category = request.args.get("category", "")
  location_id = request.args.get("location_id", "")

  conn = get_db()
  sql = """
        SELECT a.*, l.name AS location_name, e.full_name AS employee_name
        FROM assets a
        LEFT JOIN locations l ON l.id = a.location_id
        LEFT JOIN employees e ON e.id = a.assigned_employee_id
        WHERE 1=1
    """
  params = []
  if q:
    sql += (
        " AND (a.name LIKE ? OR a.asset_tag LIKE ? OR a.serial_number LIKE ?"
        " OR e.full_name LIKE ?)"
    )
    like = f"%{q}%"
    params += [like, like, like, like]
  if status:
    sql += " AND a.status = ?"
    params.append(status)
  if category:
    sql += " AND a.category = ?"
    params.append(category)
  if location_id:
    sql += " AND a.location_id = ?"
    params.append(location_id)
  sql += " ORDER BY a.updated_at DESC"

  assets = conn.execute(sql, params).fetchall()
  locations, employees = get_lookup_lists(conn)
  conn.close()
  return render_template(
      "asset_list.html",
      assets=assets,
      q=q,
      status=status,
      category=category,
      location_id=location_id,
      statuses=STATUSES,
      categories=CATEGORIES,
      locations=locations,
  )


@app.route("/api/assets/search")
@require()
def api_asset_search():
  q = request.args.get("q", "").strip()
  conn = get_db()
  like = f"%{q}%"
  rows = conn.execute(
      """SELECT id, asset_tag, name, status FROM assets
           WHERE name LIKE ? OR asset_tag LIKE ? OR serial_number LIKE ?
           ORDER BY updated_at DESC LIMIT 10""",
      (like, like, like),
  ).fetchall()
  conn.close()
  return jsonify([dict(r) for r in rows])


@app.route("/assets/new", methods=["GET", "POST"])
@require("asset:add")
def asset_new():
  conn = get_db()
  if request.method == "POST":
    asset_tag = request.form.get("asset_tag", "").strip()
    name = request.form.get("name", "").strip()

    if not asset_tag or not name:
      flash("Asset name and Asset ID are required.", "error")
      locations, employees = get_lookup_lists(conn)
      conn.close()
      return render_template(
          "asset_form.html",
          asset=None,
          locations=locations,
          employees=employees,
          categories=CATEGORIES,
          conditions=CONDITIONS,
          statuses=STATUSES,
          form=request.form,
      )

    try:
      cur = conn.execute(
          """INSERT INTO assets
                   (asset_tag, name, category, serial_number, location_id,
                    assigned_employee_id, condition, status, purchase_date, purchase_cost,
                    vendor, warranty_expiry, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (
              asset_tag,
              name,
              request.form.get("category") or "Other",
              request.form.get("serial_number", "").strip() or None,
              request.form.get("location_id") or None,
              request.form.get("assigned_employee_id") or None,
              request.form.get("condition") or "Good",
              (
                  "Assigned"
                  if request.form.get("assigned_employee_id")
                  else "Available"
              ),
              request.form.get("purchase_date") or None,
              request.form.get("purchase_cost") or None,
              request.form.get("vendor", "").strip() or None,
              request.form.get("warranty_expiry") or None,
              request.form.get("notes", "").strip() or None,
          ),
      )
    except sqlite3.IntegrityError:
      flash(
          f"Asset ID “{asset_tag}” is already in use — choose a different one.",
          "error",
      )
      locations, employees = get_lookup_lists(conn)
      conn.close()
      return render_template(
          "asset_form.html",
          asset=None,
          locations=locations,
          employees=employees,
          categories=CATEGORIES,
          conditions=CONDITIONS,
          statuses=STATUSES,
          form=request.form,
      )

    asset_id = cur.lastrowid
    log_history(
        conn,
        asset_id,
        "Created",
        f"Asset {asset_tag} registered by {g.account['username']}",
    )
    conn.commit()
    conn.close()
    flash(f"Asset {asset_tag} created.", "success")
    return redirect(url_for("asset_detail", asset_id=asset_id))

  locations, employees = get_lookup_lists(conn)
  conn.close()
  return render_template(
      "asset_form.html",
      asset=None,
      locations=locations,
      employees=employees,
      categories=CATEGORIES,
      conditions=CONDITIONS,
      statuses=STATUSES,
      form=None,
  )


@app.route("/assets/<int:asset_id>")
@require()
def asset_detail(asset_id):
  conn = get_db()
  asset = conn.execute(
      """SELECT a.*, l.name AS location_name,
                  e.full_name AS employee_name, e.email AS employee_email
           FROM assets a
           LEFT JOIN locations l ON l.id = a.location_id
           LEFT JOIN employees e ON e.id = a.assigned_employee_id
           WHERE a.id = ?""",
      (asset_id,),
  ).fetchone()
  if asset is None:
    abort(404)
  history = conn.execute(
      "SELECT * FROM asset_history WHERE asset_id = ? ORDER BY timestamp DESC",
      (asset_id,),
  ).fetchall()
  maintenance = conn.execute(
      "SELECT * FROM maintenance_records WHERE asset_id = ? ORDER BY service_date"
      " DESC",
      (asset_id,),
  ).fetchall()
  locations, employees = get_lookup_lists(conn)
  conn.close()
  scan_url = request.url_root.rstrip("/") + url_for(
      "asset_detail", asset_id=asset_id
  )
  return render_template(
      "asset_detail.html",
      asset=asset,
      history=history,
      maintenance=maintenance,
      locations=locations,
      employees=employees,
      statuses=STATUSES,
      conditions=CONDITIONS,
      scan_url=scan_url,
  )


@app.route("/assets/<int:asset_id>/label")
@require()
def asset_label(asset_id):
  conn = get_db()
  asset = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
  conn.close()
  if asset is None:
    abort(404)
  scan_url = request.url_root.rstrip("/") + url_for(
      "asset_detail", asset_id=asset_id
  )
  return render_template("asset_label.html", asset=asset, scan_url=scan_url)


@app.route("/assets/labels")
@require()
def asset_labels_batch():
  ids = request.args.getlist("ids")
  if not ids:
    flash("Select at least one asset to print labels for.", "error")
    return redirect(url_for("asset_list"))

  conn = get_db()
  placeholders = ",".join("?" for _ in ids)
  rows = conn.execute(
      f"SELECT * FROM assets WHERE id IN ({placeholders}) ORDER BY name", ids
  ).fetchall()
  conn.close()
  if not rows:
    abort(404)

  labels = [
      {
          "id": r["id"],
          "name": r["name"],
          "asset_tag": r["asset_tag"],
          "scan_url": request.url_root.rstrip("/")
          + url_for("asset_detail", asset_id=r["id"]),
      }
      for r in rows
  ]
  return render_template("asset_label_batch.html", labels=labels)


@app.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
@require("asset:add")
def asset_edit(asset_id):
  conn = get_db()
  asset = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
  if asset is None:
    abort(404)

  if request.method == "POST":
    asset_tag = request.form.get("asset_tag", "").strip()
    name = request.form.get("name", "").strip()

    if not asset_tag or not name:
      flash("Asset name and Asset ID are required.", "error")
      locations, employees = get_lookup_lists(conn)
      conn.close()
      return render_template(
          "asset_form.html",
          asset=asset,
          locations=locations,
          employees=employees,
          categories=CATEGORIES,
          conditions=CONDITIONS,
          statuses=STATUSES,
          form=request.form,
      )

    try:
      conn.execute(
          """UPDATE assets SET asset_tag=?, name=?, category=?, serial_number=?,
                   location_id=?, condition=?, purchase_date=?, purchase_cost=?, vendor=?,
                   warranty_expiry=?, notes=?, updated_at=datetime('now')
                   WHERE id=?""",
          (
              asset_tag,
              name,
              request.form.get("category") or "Other",
              request.form.get("serial_number", "").strip() or None,
              request.form.get("location_id") or None,
              request.form.get("condition") or "Good",
              request.form.get("purchase_date") or None,
              request.form.get("purchase_cost") or None,
              request.form.get("vendor", "").strip() or None,
              request.form.get("warranty_expiry") or None,
              request.form.get("notes", "").strip() or None,
              asset_id,
          ),
      )
    except sqlite3.IntegrityError:
      flash(
          f"Asset ID “{asset_tag}” is already in use — choose a different one.",
          "error",
      )
      locations, employees = get_lookup_lists(conn)
      conn.close()
      return render_template(
          "asset_form.html",
          asset=asset,
          locations=locations,
          employees=employees,
          categories=CATEGORIES,
          conditions=CONDITIONS,
          statuses=STATUSES,
          form=request.form,
      )

    log_history(
        conn,
        asset_id,
        "Edited",
        f"Asset details updated by {g.account['username']}",
    )
    conn.commit()
    conn.close()
    flash("Asset updated.", "success")
    return redirect(url_for("asset_detail", asset_id=asset_id))

  locations, employees = get_lookup_lists(conn)
  conn.close()
  return render_template(
      "asset_form.html",
      asset=asset,
      locations=locations,
      employees=employees,
      categories=CATEGORIES,
      conditions=CONDITIONS,
      statuses=STATUSES,
      form=None,
  )


@app.route("/assets/<int:asset_id>/assign", methods=["POST"])
@require("asset:add")
def asset_assign(asset_id):
  conn = get_db()
  employee_id = request.form.get("assigned_employee_id") or None
  if employee_id:
    emp = conn.execute(
        "SELECT full_name FROM employees WHERE id=?", (employee_id,)
    ).fetchone()
    conn.execute(
        "UPDATE assets SET assigned_employee_id=?, status='Assigned',"
        " updated_at=datetime('now') WHERE id=?",
        (employee_id, asset_id),
    )
    log_history(conn, asset_id, "Assigned", f"Assigned to {emp['full_name']}")
    flash(f"Asset assigned to {emp['full_name']}.", "success")
  else:
    conn.execute(
        "UPDATE assets SET assigned_employee_id=NULL, status='Available',"
        " updated_at=datetime('now') WHERE id=?",
        (asset_id,),
    )
    log_history(conn, asset_id, "Unassigned", "Asset returned / unassigned")
    flash("Asset unassigned.", "success")
  conn.commit()
  conn.close()
  return redirect(url_for("asset_detail", asset_id=asset_id))


@app.route("/assets/<int:asset_id>/transfer", methods=["POST"])
@require("asset:add")
def asset_transfer(asset_id):
  conn = get_db()
  new_loc = request.form.get("location_id") or None

  old = conn.execute(
      "SELECT location_id FROM assets WHERE id=?", (asset_id,)
  ).fetchone()
  loc_name = lambda lid: (
      conn.execute("SELECT name FROM locations WHERE id=?", (lid,)).fetchone()
      or {"name": "Unassigned"}
  )["name"] if lid else "Unassigned"

  details = (
      f"Location: {loc_name(old['location_id'])} → {loc_name(new_loc)}"
  )

  conn.execute(
      "UPDATE assets SET location_id=?, updated_at=datetime('now') WHERE id=?",
      (new_loc, asset_id),
  )
  log_history(conn, asset_id, "Transferred", details)
  conn.commit()
  conn.close()
  flash("Asset transferred.", "success")
  return redirect(url_for("asset_detail", asset_id=asset_id))


@app.route("/assets/<int:asset_id>/status", methods=["POST"])
@require("asset:add")
def asset_status(asset_id):
  conn = get_db()
  new_status = request.form.get("status")
  new_condition = request.form.get("condition")
  old = conn.execute(
      "SELECT status, condition FROM assets WHERE id=?", (asset_id,)
  ).fetchone()

  conn.execute(
      "UPDATE assets SET status=?, condition=?, updated_at=datetime('now')"
      " WHERE id=?",
      (new_status, new_condition, asset_id),
  )
  if old["status"] != new_status:
    log_history(
        conn, asset_id, "Status Change", f"{old['status']} → {new_status}"
    )
  if old["condition"] != new_condition:
    log_history(
        conn,
        asset_id,
        "Condition Change",
        f"{old['condition']} → {new_condition}",
    )
  conn.commit()
  conn.close()
  flash("Status updated.", "success")
  return redirect(url_for("asset_detail", asset_id=asset_id))


@app.route("/assets/<int:asset_id>/maintenance", methods=["POST"])
@require("asset:add")
def asset_maintenance_add(asset_id):
  conn = get_db()
  conn.execute(
      """INSERT INTO maintenance_records (asset_id, service_date, description, cost, performed_by)
           VALUES (?,?,?,?,?)""",
      (
          asset_id,
          request.form["service_date"],
          request.form["description"].strip(),
          request.form.get("cost") or None,
          request.form.get("performed_by", "").strip() or None,
      ),
  )
  log_history(
      conn, asset_id, "Maintenance", request.form["description"].strip()
  )
  conn.commit()
  conn.close()
  flash("Maintenance record added.", "success")
  return redirect(url_for("asset_detail", asset_id=asset_id))


@app.route("/assets/<int:asset_id>/delete", methods=["POST"])
@require("asset:delete")
def asset_delete(asset_id):
  conn = get_db()
  conn.execute("DELETE FROM assets WHERE id=?", (asset_id,))
  conn.commit()
  conn.close()
  flash("Asset deleted.", "success")
  return redirect(url_for("asset_list"))


@app.route("/employees", methods=["GET", "POST"])
@require()
def employees():
  conn = get_db()
  if request.method == "POST":
    conn.execute(
        "INSERT INTO employees (full_name, email, location_id) VALUES (?,?,?)",
        (
            request.form["full_name"].strip(),
            request.form.get("email", "").strip() or None,
            request.form.get("location_id") or None,
        ),
    )
    conn.commit()
    flash("Employee added.", "success")
    conn.close()
    return redirect(url_for("employees"))

  rows = conn.execute(
      """SELECT e.*, l.name AS location_name,
                  (SELECT COUNT(*) FROM assets a WHERE a.assigned_employee_id = e.id) AS asset_count
           FROM employees e LEFT JOIN locations l ON l.id = e.location_id
           WHERE e.active = 1 ORDER BY e.full_name"""
  ).fetchall()
  locations = conn.execute("SELECT * FROM locations ORDER BY name").fetchall()
  conn.close()
  return render_template(
      "employee_list.html", employees=rows, locations=locations
  )


@app.route("/settings", methods=["GET", "POST"])
@require("user:manage")
def settings():
  conn = get_db()
  if request.method == "POST":
    name = request.form.get("name", "").strip()
    if name:
      conn.execute("INSERT OR IGNORE INTO locations (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    flash("Location added.", "success")
    return redirect(url_for("settings"))

  locations = conn.execute("SELECT * FROM locations ORDER BY name").fetchall()
  conn.close()
  return render_template("settings.html", locations=locations)


# ---------- User Management Routes ----------
@app.route("/users", methods=["GET"])
@require("user:manage")
def users():
  conn = get_db()
  accounts = conn.execute("SELECT * FROM accounts ORDER BY id").fetchall()
  conn.close()
  new_creds = session.pop("new_creds", None)
  return render_template("users.html", accounts=accounts, new_creds=new_creds)


@app.route("/users", methods=["POST"])
@require("user:manage")
def create_account():
  username = request.form.get("username", "").strip()
  role = request.form.get("role")

  if g.account["role"] != "superadmin":
    flash("Only the superadmin can create accounts.", "error")
    return redirect(url_for("users"))
  if role not in ("admin", "user"):
    flash("Invalid role.", "error")
    return redirect(url_for("users"))

  conn = get_db()
  existing = conn.execute(
      "SELECT id FROM accounts WHERE username = ?", (username,)
  ).fetchone()
  if not username or existing:
    flash("Username is empty or already taken.", "error")
    conn.close()
    return redirect(url_for("users"))

  pw = generate_password()
  pw_hash = generate_password_hash(pw)
  conn.execute(
      "INSERT INTO accounts (username, role, password_hash) VALUES (?, ?, ?)",
      (username, role, pw_hash),
  )
  conn.commit()
  conn.close()

  session["new_creds"] = {"username": username, "password": pw, "role": role}
  flash(f"User {username} created successfully.", "success")
  return redirect(url_for("users"))


@app.route("/users/<int:uid>/reset", methods=["POST"])
@require("user:manage")
def reset_password(uid):
  conn = get_db()
  acc = conn.execute("SELECT * FROM accounts WHERE id = ?", (uid,)).fetchone()
  if not acc:
    conn.close()
    abort(404)

  pw = generate_password()
  pw_hash = generate_password_hash(pw)
  conn.execute(
      "UPDATE accounts SET password_hash = ? WHERE id = ?", (pw_hash, uid)
  )
  conn.commit()
  conn.close()

  session["new_creds"] = {
      "username": acc["username"],
      "password": pw,
      "role": acc["role"],
  }
  flash(f"Password reset for {acc['username']}.", "success")
  return redirect(url_for("users"))


@app.route("/users/<int:uid>/toggle", methods=["POST"])
@require("user:manage")
def toggle_account(uid):
  conn = get_db()
  acc = conn.execute("SELECT * FROM accounts WHERE id = ?", (uid,)).fetchone()
  if not acc:
    conn.close()
    abort(404)

  new_active = 0 if acc["is_active"] else 1
  conn.execute(
      "UPDATE accounts SET is_active = ? WHERE id = ?", (new_active, uid)
  )
  conn.commit()
  conn.close()
  flash(f"Account status updated for {acc['username']}.", "success")
  return redirect(url_for("users"))


@app.route("/users/<int:uid>/delete", methods=["POST"])
@require("user:manage")
def delete_account(uid):
  if uid == g.account["id"]:
    flash("You cannot delete your own account.", "error")
    return redirect(url_for("users"))

  conn = get_db()
  conn.execute("DELETE FROM accounts WHERE id = ?", (uid,))
  conn.commit()
  conn.close()
  flash("Account deleted.", "success")
  return redirect(url_for("users"))


# ---------- User Settings Route ----------
@app.route("/user/settings", methods=["GET", "POST"])
def user_settings():
  acc = current_account()
  if not acc:
    return redirect(url_for("login"))

  if request.method == "POST":
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not check_password_hash(acc["password_hash"], current_password):
      flash("Current password is incorrect.", "error")
    elif not new_password or new_password != confirm_password:
      flash("New passwords do not match or are empty.", "error")
    else:
      new_hash = generate_password_hash(new_password)
      conn = get_db()
      conn.execute(
          "UPDATE accounts SET password_hash = ? WHERE id = ?",
          (new_hash, acc["id"]),
      )
      conn.commit()
      conn.close()
      flash("Password updated successfully.", "success")
      return redirect(url_for("user_settings"))

  return render_template("user_settings.html", me=acc)


def bootstrap():
  """Ensure initial superadmin account exists."""
  init_db(seed=True)
  conn = get_db()
  sa = conn.execute(
      "SELECT * FROM accounts WHERE role = 'superadmin'"
  ).fetchone()
  if not sa:
    pw = os.environ.get("SUPERADMIN_PASSWORD") or generate_password()
    pw_hash = generate_password_hash(pw)
    conn.execute(
        "INSERT INTO accounts (username, role, password_hash) VALUES (?, ?, ?)",
        ("superadmin", "superadmin", pw_hash),
    )
    conn.commit()
    print(
        f"\n*** Superadmin created. username: superadmin password: {pw} ***\n"
    )
  conn.close()


if __name__ == "__main__":
  bootstrap()
  app.run(debug=True, host="0.0.0.0", port=5000)