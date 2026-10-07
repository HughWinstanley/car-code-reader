"""
The vehicle health report: one printable page (HTML) with everything the app found.
Open it in any browser; use Print to get paper or a PDF.
"""

import datetime

LEVEL_COLORS = {"high": ("#D9362B", "#FDECEA"), "medium": ("#B26A00", "#FFF4E0"), "low": ("#1F6FD1", "#E8F1FC"),
                "past": ("#6B6B6B", "#F1F1F1")}

CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;color:#111;background:#fff;
margin:0;padding:32px;max-width:860px;margin:auto;line-height:1.45}
h1{font-size:28px;margin:0 0 4px} h2{font-size:19px;margin:30px 0 10px;padding-bottom:6px;border-bottom:2px solid #111}
.muted{color:#666} .grid{display:grid;grid-template-columns:200px 1fr;gap:4px 16px}
.card{border:1px solid #E2E2E2;border-radius:14px;padding:14px 18px;margin:10px 0;break-inside:avoid}
.pill{display:inline-block;border-radius:999px;padding:2px 10px;font-size:13px;font-weight:600}
.code{font-weight:700;font-size:16px} ol{margin:6px 0 0 18px;padding:0} li{margin:2px 0}
table{border-collapse:collapse;width:100%} td,th{text-align:left;padding:5px 8px;border-bottom:1px solid #eee;
font-size:14px} .good{color:#1E8A4A;font-weight:600} .bad{color:#D9362B;font-weight:600}
.head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px}
@media print{body{padding:0}.noprint{display:none}}
"""


def e(text):
    """Make text safe to put in the page (the app's own built-in Python doesn't include the html module)."""
    t = str(text if text is not None else "")
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build(d):
    """d: dict with vehicle, items, mil_on, readiness_rows, self_tests, misfires, modules, battery, recalls."""
    v = d.get("vehicle") or {}
    out = [f"<!doctype html><html><head><meta charset='utf-8'><title>Vehicle report - {e(v.get('title', ''))}"
           f"</title><style>{CSS}</style></head><body>"]
    out.append(f"<div class='head'><div><h1>Vehicle health report</h1><div class='muted'>"
               f"{datetime.datetime.now():%B %d, %Y at %I:%M %p} · Car Code Reader</div></div>"
               f"<button class='noprint' onclick='window.print()' style='font-size:15px;padding:8px 18px;"
               f"border-radius:999px;border:0;background:#111;color:#fff;cursor:pointer'>Print or save as PDF</button>"
               f"</div>")
    out.append("<h2>Vehicle</h2><div class='grid'>")
    for label, key in (("Vehicle", "title"), ("VIN", "vin"), ("Battery", "voltage"), ("Protocol", "protocol"),
                       ("Computers answering", "ecus")):
        if v.get(key) and v.get(key) != "-":
            out.append(f"<div class='muted'>{label}</div><div><b>{e(v[key])}</b></div>")
    if d.get("mil_on") is not None:
        out.append(f"<div class='muted'>Check-engine light</div><div><b class='{'bad' if d['mil_on'] else 'good'}'>"
                   f"{'ON' if d['mil_on'] else 'Off'}</b></div>")
    out.append("</div>")

    items = d.get("items") or []
    active = [i for i in items if i["level"] != "past"]
    out.append(f"<h2>Problems found ({len(active)} active{', ' + str(len(items) - len(active)) + ' past' if len(items) > len(active) else ''})</h2>")
    if not d.get("scanned"):
        out.append("<p class='muted'>No scan was run.</p>")
    elif not items:
        out.append("<p class='good'>No trouble codes found.</p>")
    for it in items:
        fg, bg = LEVEL_COLORS[it["level"]]
        info = it["info"]
        out.append(f"<div class='card'><div class='head'><div><span class='code'>{e(it['code'])}</span> "
                   f"&nbsp;{e(info['description'])}</div><span class='pill' style='color:{fg};background:{bg}'>"
                   f"{e(it['words'])}</span></div>"
                   f"<div class='muted'>{e(it['module'])} · {e(it['status'])}"
                   f"{' · ' + e(info['factory']) + ' factory meaning' if info.get('factory') else ''}</div>")
        if it.get("why"):
            out.append(f"<p><b>Why it matters:</b> {e(it['why'])}</p>")
        if info.get("causes"):
            out.append(f"<p><b>Common causes:</b> {e(info['causes'])}</p>")
        if info.get("checks"):
            out.append("<b>How to check it:</b><ol>" + "".join(f"<li>{e(s)}</li>" for s in info["checks"]) +
                       "</ol>")
        out.append("</div>")

    rows = d.get("readiness_rows")
    if rows:
        out.append("<h2>Smog check self-tests</h2><table><tr><th>Self-test</th><th>Status</th></tr>")
        for name, supported, incomplete in rows:
            st = ("<span class='muted'>Not on this vehicle</span>" if not supported else
                  "<span class='bad'>Still running</span>" if incomplete else "<span class='good'>Done</span>")
            out.append(f"<tr><td>{e(name)}</td><td>{st}</td></tr>")
        out.append("</table>")

    mis = d.get("misfires")
    if mis:
        out.append("<h2>Misfires per cylinder</h2><table><tr><th>Cylinder</th><th>This or last drive</th>"
                   "<th>10-drive average</th></tr>")
        for cyl, (cur, avg) in mis.items():
            out.append(f"<tr><td>{cyl}</td><td>{'' if cur is None else f'{cur:.0f}'}</td>"
                       f"<td>{'' if avg is None else f'{avg:.0f}'}</td></tr>")
        out.append("</table>")
    tests = [r for r in (d.get("self_tests") or []) if r["misfire"] is None]
    if tests:
        out.append("<h2>Self-test results</h2><table><tr><th>Test</th><th>Result</th><th>Allowed</th><th></th></tr>")
        for r in tests:
            u = f" {r['unit']}" if r["unit"] else ""
            out.append(f"<tr><td>{e(r['name'])} (${r['tid']:02X})</td><td>{r['value']:.4g}{e(u)}</td>"
                       f"<td>{r['low']:.4g} to {r['high']:.4g}{e(u)}</td><td class='{'good' if r['passed'] else 'bad'}'>"
                       f"{'Pass' if r['passed'] else 'Fail'}</td></tr>")
        out.append("</table>")

    batt = d.get("battery")
    if batt and batt.get("verdicts"):
        out.append("<h2>Battery and charging test</h2><table>")
        for label, value, verdict, good in batt["verdicts"]:
            out.append(f"<tr><td>{e(label)}</td><td><b>{e(value)}</b></td><td class='{'good' if good else 'bad'}'>"
                       f"{e(verdict)}</td></tr>")
        out.append("</table>")

    mods = d.get("modules")
    if mods:
        out.append("<h2>Module info</h2>")
        for ecu, m in mods.items():
            out.append(f"<div class='card'><b>{e(m['name'] or ecu)}</b>")
            for c in m["calids"]:
                out.append(f"<div>Calibration ID: {e(c)}</div>")
            for c in m["cvns"]:
                out.append(f"<div>Calibration check number: {e(c)}</div>")
            for label, val in m["usage"]:
                out.append(f"<div class='muted'>{e(label)}: {e(val)}</div>")
            out.append("</div>")

    rec = d.get("recalls")
    if rec is not None:
        out.append(f"<h2>Safety recalls ({len(rec)})</h2>")
        if not rec:
            out.append("<p class='muted'>None found in the NHTSA database.</p>")
        for r in rec:
            out.append(f"<div class='card'><b>{e(r['component'])}</b><div class='muted'>Recall {e(r['campaign'])}, "
                       f"{e(r['date'])}</div><p>{e(r['summary'])}</p><p><b>Fix:</b> {e(r['remedy'])}</p></div>")
        if rec:
            out.append("<p class='muted'>Check which recalls are still open on this vehicle at nhtsa.gov/recalls "
                       "with the VIN. Dealers repair recalls free.</p>")

    out.append("<p class='muted' style='margin-top:30px'>This report lists what the vehicle's computers reported. "
               "Code meanings and steps are general guidance; confirm with a test before replacing parts.</p>")
    out.append("</body></html>")
    return "".join(out)
