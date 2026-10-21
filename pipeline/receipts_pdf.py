"""Receipt PDFs in four layouts, English and Spanish, so reading them is not trivial.

Layouts: `saas` (emailed invoice, EN), `es` (comprobante, ES, comma decimals), `pos`
(narrow restaurant ticket) and `travel` (airline e-ticket or hotel folio).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

MONTHS_EN = [
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
]


def en_amount(cents: int) -> str:
    return f"{cents // 100:,}.{cents % 100:02d}"


def es_amount(cents: int) -> str:
    return f"{cents // 100:,}".replace(",", ".") + f",{cents % 100:02d}"


def _canvas(path: Path, size) -> Canvas:
    c = Canvas(str(path), pagesize=size, pageCompression=1)
    c.setAuthor("Card to Ledger AR synthetic data")
    c.setTitle("Synthetic receipt")
    return c


def render(r: dict, path: Path) -> None:
    {"saas": _saas, "es": _es, "pos": _pos, "travel": _travel}[r["layout"]](r, path)


def _rows(c: Canvas, x: float, y: float, rows, size=10, gap=5.2 * mm, right=None) -> float:
    for row in rows:
        if isinstance(row, tuple):
            label, value = row
            c.setFont("Helvetica", size)
            c.drawString(x, y, label)
            c.drawRightString(right, y, value)
        else:
            c.setFont("Helvetica", size)
            c.drawString(x, y, row)
        y -= gap
    return y


def _saas(r: dict, path: Path) -> None:
    c = _canvas(path, A4)
    w, h = A4
    sym = {"USD": "$", "EUR": "€", "USDC": ""}.get(r["currency"], "")
    unit = f" {r['currency']}"
    d: date = r["date"]
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, h - 25 * mm, r["vendor"])
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, h - 31 * mm, r["address"])
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, h - 48 * mm, "Invoice" if r.get("kind") == "invoice" else "Receipt")
    y = _rows(
        c, 20 * mm, h - 58 * mm,
        [
            f"Invoice number   {r['number']}",
            f"Date paid   {MONTHS_EN[d.month - 1]} {d.day}, {d.year}",
            "Bill to   Andes Labs SRL, Buenos Aires, Argentina",
        ],
    )
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Description")
    c.drawRightString(w - 20 * mm, y, "Amount")
    y -= 6 * mm
    y = _rows(c, 20 * mm, y, [(desc, f"{sym}{en_amount(a)}") for desc, a in r["items"]],
              right=w - 20 * mm)
    y -= 3 * mm
    y = _rows(
        c, 20 * mm, y,
        [
            ("Subtotal", f"{sym}{en_amount(r['total_cents'])}"),
            ("Total", f"{sym}{en_amount(r['total_cents'])}"),
        ],
        right=w - 20 * mm,
    )
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y - 2 * mm, "Amount paid")
    c.drawRightString(w - 20 * mm, y - 2 * mm, f"{sym}{en_amount(r['total_cents'])}{unit}")
    if r.get("footer"):
        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, 20 * mm, r["footer"])
    c.save()


def _es(r: dict, path: Path) -> None:
    c = _canvas(path, A4)
    w, h = A4
    d: date = r["date"]
    sym, moneda = {
        "USD": ("US$", "Dólares estadounidenses (USD)"),
        "ARS": ("$", "Pesos argentinos (ARS)"),
        "USDC": ("USDC", "USD Coin (USDC)"),
        "EUR": ("€", "Euros (EUR)"),
    }[r["currency"]]
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 22 * mm, "COMPROBANTE DE PAGO")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, h - 36 * mm, r["vendor"])
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, h - 41 * mm, r["address"])
    y = _rows(
        c, 20 * mm, h - 55 * mm,
        [
            f"N° {r['number']}",
            f"Fecha: {d.day:02d}/{d.month:02d}/{d.year}",
            "Cliente: Andes Labs SRL",
        ],
    )
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Descripción")
    c.drawRightString(w - 20 * mm, y, "Importe")
    y -= 6 * mm
    y = _rows(c, 20 * mm, y, [(desc, f"{sym} {es_amount(a)}") for desc, a in r["items"]],
              right=w - 20 * mm)
    y -= 4 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "TOTAL")
    c.drawRightString(w - 20 * mm, y, f"{sym} {es_amount(r['total_cents'])}")
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, y - 8 * mm, f"Moneda: {moneda}")
    c.save()


def _pos(r: dict, path: Path) -> None:
    width = 80 * mm
    lines = 14 + len(r["items"])
    height = (lines * 5 + 30) * mm
    c = _canvas(path, (width, height))
    d: date = r["date"]
    x0, x1 = 5 * mm, width - 5 * mm
    y = height - 10 * mm
    c.setFont("Courier-Bold", 10)
    c.drawCentredString(width / 2, y, r["vendor"].upper())
    y -= 5 * mm
    c.setFont("Courier", 8)
    c.drawCentredString(width / 2, y, r["address"])
    y -= 8 * mm
    c.drawString(x0, y, f"{d.isoformat()} {r.get('time', '13:05')}")
    c.drawRightString(x1, y, f"CHK {r['number']}")
    y -= 7 * mm
    for desc, a in r["items"]:
        c.drawString(x0, y, desc)
        c.drawRightString(x1, y, en_amount(a))
        y -= 5 * mm
    y -= 2 * mm
    c.drawString(x0, y, "SUBTOTAL")
    c.drawRightString(x1, y, en_amount(r["subtotal_cents"]))
    y -= 5 * mm
    c.drawString(x0, y, "TAX")
    c.drawRightString(x1, y, en_amount(r["tax_cents"]))
    y -= 5 * mm
    if r.get("tip_blank"):
        # Printed before the tip was added: the card charge will be higher.
        c.setFont("Courier-Bold", 9)
        c.drawString(x0, y, "TOTAL")
        c.drawRightString(x1, y, en_amount(r["total_cents"]))
        y -= 7 * mm
        c.setFont("Courier", 8)
        c.drawString(x0, y, "TIP:     ____________")
        y -= 6 * mm
        c.drawString(x0, y, "TOTAL:   ____________")
    else:
        c.drawString(x0, y, "TIP")
        c.drawRightString(x1, y, en_amount(r["tip_cents"]))
        y -= 6 * mm
        c.setFont("Courier-Bold", 9)
        c.drawString(x0, y, "TOTAL")
        c.drawRightString(x1, y, en_amount(r["total_cents"]))
    y -= 8 * mm
    c.setFont("Courier", 8)
    c.drawString(x0, y, f"VISA ****{r['card_last4']}")
    y -= 5 * mm
    c.drawCentredString(width / 2, y, "THANK YOU")
    c.save()


def _travel(r: dict, path: Path) -> None:
    c = _canvas(path, A4)
    w, h = A4
    d: date = r["date"]
    mon = MONTHS_EN[d.month - 1][:3].upper()
    c.setFont("Helvetica-Bold", 15)
    c.drawString(20 * mm, h - 24 * mm, r["vendor"])
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, h - 30 * mm, r["address"])
    if r.get("kind") == "flight":
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, h - 44 * mm, "ELECTRONIC TICKET RECEIPT")
        rows = [
            f"Ticket number   {r['number']}",
            f"Issue date   {d.day:02d}{mon}{str(d.year)[2:]}",
            f"Passenger   {r['passenger']}",
            f"Route   {r['route']}",
        ]
        y = _rows(c, 20 * mm, h - 56 * mm, rows)
        y -= 4 * mm
        y = _rows(
            c, 20 * mm, y,
            [(desc, f"USD {en_amount(a)}") for desc, a in r["items"]]
            + [("Total", f"USD {en_amount(r['total_cents'])}")],
            right=w - 20 * mm,
        )
        _rows(c, 20 * mm, y - 4 * mm, [f"Form of payment   CC VI XXXX{r['card_last4']}"])
    else:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, h - 44 * mm, "GUEST FOLIO")
        a: date = r["arrival"]
        amon = MONTHS_EN[a.month - 1][:3].upper()
        rows = [
            f"Guest   {r['passenger']}      Room {r['room']}",
            f"Folio No.   {r['number']}",
            f"Arrival   {a.day:02d}-{amon}-{a.year}      Departure   {d.day:02d}-{mon}-{d.year}",
        ]
        y = _rows(c, 20 * mm, h - 56 * mm, rows)
        y -= 4 * mm
        y = _rows(c, 20 * mm, y, [(desc, en_amount(a_)) for desc, a_ in r["items"]],
                  right=w - 20 * mm)
        y = _rows(
            c, 20 * mm, y - 2 * mm,
            [
                ("Total charges", en_amount(r["total_cents"])),
                ("Payments", "-" + en_amount(r["total_cents"])),
                ("Balance", "0.00"),
            ],
            right=w - 20 * mm,
        )
        _rows(c, 20 * mm, y - 2 * mm, ["All amounts in USD"])
    c.save()
