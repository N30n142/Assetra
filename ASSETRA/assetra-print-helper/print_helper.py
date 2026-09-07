"""
Assetra Print Helper (v2 -- configurable label size + multi-printer support)
=============================================================================
A tiny local HTTPS server that runs next to your TSPL label printer(s) and
prints QR labels on request. Your PythonAnywhere-hosted Assetra site calls
this directly from the browser (browser -> your LAN -> this server), since
PythonAnywhere itself has no way to reach a USB printer on your desk.

WHAT'S CONFIGURABLE NOW
------------------------
- Label size (width/height in mm) -- passed per print request, with a
  fallback default below. No more hardcoded 50x30mm.
- Which printer to use -- auto-detects ANY connected TSPL-speaking printer
  from a small known-VID list (Xprinter, TSC -- the common TSPL brands).
  If more than one is plugged in, pass "vendor_id"/"product_id" explicitly
  in the request to pick one, or use GET /printers to list what's found.

WHAT'S STILL PRINTER-LANGUAGE SPECIFIC
----------------------------------------
This only works with printers that speak TSPL (the command language your
Xprinter XP-365B uses -- also used by TSC and many similar "TT/thermal
label" printers). A completely different printer language (e.g. Zebra's
ZPL, or a standard ESC/POS receipt printer) needs a different builder
function entirely -- that's a separate driver, not a config tweak. If you
add a non-TSPL printer later, tell me and I'll add a second code path.

Install (on the machine physically connected to the printer(s)):
    pip install flask pyusb cryptography --break-system-packages

Run:
    python3 print_helper.py

Then find this machine's LAN IP (`ip addr` on Linux) and point the site's
PRINT_HELPER_URL at:
    https://<this-machine-LAN-IP>:5050

First browser visit to that address will show a "not secure" warning
(self-signed cert) -- accept it once, then fetch() calls work normally.

Endpoints:
    GET  /printers
        Lists every currently-connected known TSPL printer (vendor_id,
        product_id, and a guessed friendly name).
    GET  /health
        Same, but returns ok:false with an error if none are found.
    POST /print
        JSON body:
        {
          "label_text": "AST-00001",        (required)
          "qr_data": "https://.../assets/1", (optional, defaults to label_text)
          "width_mm": 50,                    (optional, default DEFAULT_WIDTH_MM)
          "height_mm": 30,                   (optional, default DEFAULT_HEIGHT_MM)
          "vendor_id": "1fc9",               (optional hex string, to force a printer)
          "product_id": "2016"               (optional hex string, to force a printer)
        }
"""

import os
import sys

from flask import Flask, request, jsonify

import usb.core
import usb.util

app = Flask(__name__)

# ---------------------------------------------------------------- Defaults
# Used only when a print request doesn't specify its own size -- change
# these if your most common label stock isn't 50x30mm.

DEFAULT_WIDTH_MM = 50
DEFAULT_HEIGHT_MM = 30
DOTS_PER_MM = 8  # 203 dpi -- true for most TSPL thermal printers incl. XP-365B

QR_CELL_WIDTH = 5
QR_MARGIN_LEFT = 16
TEXT_FONT = "3"
TEXT_HEIGHT_DOTS = 24
GAP_QR_TO_TEXT_DOTS = 20

# ---------------------------------------------------------------- Known TSPL printers
# USB vendor IDs for brands that commonly speak TSPL. Xprinter and TSC are
# the two you're most likely to run into. Add more (vendor_id, name) pairs
# here as you pick up other TSPL-speaking hardware.

KNOWN_TSPL_VENDORS = {
    0x1fc9: "Xprinter",
    0x1203: "TSC",
}

# Allowed origins set: includes both PythonAnywhere host and local development host
ALLOWED_ORIGINS = {
    "https://etheldreder4.pythonanywhere.com",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
}


@app.after_request
def add_cors_headers(resp):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


# ---------------------------------------------------------------- TSPL building

def estimate_qr_modules(qr_data: str) -> int:
    data_len = len(qr_data)
    if data_len <= 25:
        return 25
    elif data_len <= 47:
        return 29
    elif data_len <= 77:
        return 33
    else:
        return 37


def build_qr_label(label_text: str, qr_data: str, width_mm: float, height_mm: float) -> str:
    width_dots = width_mm * DOTS_PER_MM
    height_dots = height_mm * DOTS_PER_MM

    modules = estimate_qr_modules(qr_data)
    qr_size = modules * QR_CELL_WIDTH

    qr_x = QR_MARGIN_LEFT
    qr_y = max(0, (height_dots - qr_size) // 2)

    text_x = qr_x + qr_size + GAP_QR_TO_TEXT_DOTS
    text_y = max(0, (height_dots - TEXT_HEIGHT_DOTS) // 2)

    # If the QR (plus margin) is wider than the label itself, shrink the
    # cell width so it still fits rather than printing off the edge.
    cell_width = QR_CELL_WIDTH
    if qr_x + qr_size > width_dots:
        cell_width = max(1, int((width_dots - qr_x) / modules))
        qr_size = modules * cell_width
        text_x = qr_x + qr_size + GAP_QR_TO_TEXT_DOTS

    return f"""SIZE {width_mm} mm, {height_mm} mm
GAP 2 mm, 0 mm
DIRECTION 1
CLS
QRCODE {qr_x},{qr_y},M,{cell_width},A,0,"{qr_data}"
TEXT {text_x},{text_y},"{TEXT_FONT}",0,1,1,"{label_text}"
PRINT 1
"""


# ---------------------------------------------------------------- USB printing

def list_printers():
    """Return every connected USB device whose vendor ID is a known TSPL brand."""
    found = []
    for dev in usb.core.find(find_all=True):
        if dev.idVendor in KNOWN_TSPL_VENDORS:
            found.append({
                "vendor_id": f"{dev.idVendor:04x}",
                "product_id": f"{dev.idProduct:04x}",
                "brand": KNOWN_TSPL_VENDORS[dev.idVendor],
            })
    return found


def find_printer(vendor_id=None, product_id=None):
    """
    Find a printer to print to.
    - If vendor_id/product_id are given, look for that exact device.
    - Otherwise, auto-pick the first connected device matching any known
      TSPL vendor.
    """
    if vendor_id and product_id:
        dev = usb.core.find(idVendor=int(vendor_id, 16), idProduct=int(product_id, 16))
        if dev is None:
            raise RuntimeError(
                f"No device found with VID={vendor_id} PID={product_id}. "
                "Check it's connected and powered on."
            )
        return dev

    for dev in usb.core.find(find_all=True):
        if dev.idVendor in KNOWN_TSPL_VENDORS:
            return dev

    raise RuntimeError(
        "No known TSPL printer found. Check it's connected and powered on, "
        "or pass vendor_id/product_id explicitly if it's a brand not yet "
        "in KNOWN_TSPL_VENDORS."
    )


def send_data(dev, data: bytes):
    if dev.is_kernel_driver_active(0):
        try:
            dev.detach_kernel_driver(0)
        except usb.core.USBError as e:
            raise RuntimeError(f"Could not detach kernel driver: {e}")

    dev.set_configuration()
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]

    ep_out = usb.util.find_descriptor(
        intf,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
        == usb.util.ENDPOINT_OUT,
    )
    if ep_out is None:
        raise RuntimeError("Could not find an OUT endpoint on this device.")

    ep_out.write(data)


def print_label(label_text, qr_data, width_mm, height_mm, vendor_id=None, product_id=None):
    dev = find_printer(vendor_id, product_id)
    label = build_qr_label(label_text, qr_data, width_mm, height_mm)
    send_data(dev, label.encode("utf-8"))
    return label


# ---------------------------------------------------------------- Routes

@app.route("/printers")
def printers_route():
    return jsonify({"printers": list_printers()})


@app.route("/health")
def health():
    found = list_printers()
    if found:
        return jsonify({"ok": True, "printers": found})
    return jsonify({"ok": False, "error": "No known TSPL printer connected."}), 503


@app.route("/print", methods=["POST", "OPTIONS"])
def print_route():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    label_text = (data.get("label_text") or "").strip()
    qr_data = (data.get("qr_data") or "").strip() or label_text
    width_mm = float(data.get("width_mm") or DEFAULT_WIDTH_MM)
    height_mm = float(data.get("height_mm") or DEFAULT_HEIGHT_MM)
    vendor_id = data.get("vendor_id")
    product_id = data.get("product_id")

    if not label_text:
        return jsonify({"ok": False, "error": "label_text is required"}), 400

    try:
        tspl = print_label(label_text, qr_data, width_mm, height_mm, vendor_id, product_id)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({
        "ok": True,
        "label_text": label_text,
        "qr_data": qr_data,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "tspl": tspl,
    })


# ---------------------------------------------------------------- Entrypoint

def get_ssl_context():
    cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert.pem")
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "key.pem")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        return (cert_path, key_path)

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        import datetime
    except ImportError:
        print(
            "\n[print_helper] 'cryptography' not installed -- can't auto-generate "
            "a self-signed cert.\nInstall it with:\n"
            "    pip install cryptography --break-system-packages\n"
        )
        sys.exit(1)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "assetra-print-helper")]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    print(f"[print_helper] Generated self-signed cert at {cert_path}")
    return (cert_path, key_path)


if __name__ == "__main__":
    ssl_context = get_ssl_context()
    print("[print_helper] Starting on https://0.0.0.0:5050")
    print(f"[print_helper] Allowing browser requests from: {ALLOWED_ORIGINS}")
    print(f"[print_helper] Connected TSPL printers right now: {list_printers()}")
    app.run(host="0.0.0.0", port=5050, ssl_context=ssl_context, debug=False)