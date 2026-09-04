"""
Assetra Print Helper (Configurable Label Size Edition)
=====================================================
A local HTTPS server that bridges your web app to your local USB TSPL 
printer (Xprinter XP-365B). 

Run:
    sudo python3 print_helper.py
"""

import datetime
import os
import sys

from flask import Flask, jsonify, request
import usb.core
import usb.util

app = Flask(__name__)

# ---------------------------------------------------------------- Defaults
VENDOR_ID = 0x1fc9
PRODUCT_ID = 0x2016

DEFAULT_WIDTH_MM = 50
DEFAULT_HEIGHT_MM = 30
DOTS_PER_MM = 8  # 203 dpi

QR_CELL_WIDTH = 5
QR_MARGIN_LEFT = 16
TEXT_FONT = "3"
TEXT_HEIGHT_DOTS = 24
GAP_QR_TO_TEXT_DOTS = 20

# Multi-origin CORS support
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


# ---------------------------------------------------------------- TSPL Building

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


# ---------------------------------------------------------------- USB Printing

def find_printer():
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        raise RuntimeError(f"No printer found with VID={VENDOR_ID:04x} PID={PRODUCT_ID:04x}.")
    return dev


def send_data(dev, data: bytes):
    reattach = False
    if dev.is_kernel_driver_active(0):
        try:
            dev.detach_kernel_driver(0)
            reattach = True
        except usb.core.USBError as e:
            raise RuntimeError(f"Could not detach kernel driver: {e}")

    try:
        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]

        ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_OUT,
        )
        if ep_out is None:
            raise RuntimeError("Could not find an OUT endpoint on printer device.")

        ep_out.write(data)

    finally:
        # Cleans up USB handles and prevents [Errno 16] Resource Busy
        usb.util.dispose_resources(dev)
        if reattach:
            try:
                dev.attach_kernel_driver(0)
            except usb.core.USBError:
                pass


# ---------------------------------------------------------------- Routes

@app.route("/health")
def health():
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is not None:
        return jsonify({"ok": True, "connected": True})
    return jsonify({"ok": False, "error": "Printer not found"}), 503


@app.route("/print", methods=["POST", "OPTIONS"])
def print_route():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    label_text = (data.get("label_text") or "").strip()
    qr_data = (data.get("qr_data") or "").strip() or label_text
    width_mm = float(data.get("width_mm") or DEFAULT_WIDTH_MM)
    height_mm = float(data.get("height_mm") or DEFAULT_HEIGHT_MM)

    if not label_text:
        return jsonify({"ok": False, "error": "label_text is required"}), 400

    try:
        dev = find_printer()
        tspl = build_qr_label(label_text, qr_data, width_mm, height_mm)
        send_data(dev, tspl.encode("utf-8"))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({
        "ok": True,
        "label_text": label_text,
        "qr_data": qr_data,
        "width_mm": width_mm,
        "height_mm": height_mm,
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
    except ImportError:
        print("Install cryptography: pip install cryptography --break-system-packages")
        sys.exit(1)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "assetra-print-helper")])
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
    return (cert_path, key_path)


if __name__ == "__main__":
    ssl_context = get_ssl_context()
    print("[print_helper] Running on https://0.0.0.0:5050")
    app.run(host="0.0.0.0", port=5050, ssl_context=ssl_context, debug=False)