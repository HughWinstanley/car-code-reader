"""
Original icons drawn on a Tk canvas (no image files, sharp at any size).

draw(canvas, name, cx, cy, size, color) where name is one of:
  engine, abs, airbag, scan, gauge, smog, vehicle, truck, suv, car, van
make_badge(canvas, letters, cx, cy, size, fill) draws a rounded monogram badge.
"""

import math

BADGE_COLORS = ["#2F6690", "#3A7D44", "#8C4A2F", "#5B4B8A", "#1F3A5F", "#9A6B12",
                "#2E7F7A", "#7A2E4F", "#4A5D6E", "#A04020"]


def badge_color(make):
    return BADGE_COLORS[sum(ord(ch) * (i + 1) for i, ch in enumerate(make)) % len(BADGE_COLORS)]


def rounded_rect(cv, x0, y0, x1, y1, r, **kw):
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
           x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return cv.create_polygon(pts, smooth=True, **kw)


def make_badge(cv, letters, cx, cy, size, fill, font):
    h = size / 2
    rounded_rect(cv, cx - h, cy - h, cx + h, cy + h, size * 0.24, fill=fill, outline="")
    # a thin inner ring gives it the feel of a stamped badge
    i = size * 0.09
    rounded_rect(cv, cx - h + i, cy - h + i, cx + h - i, cy + h - i, size * 0.17, fill="",
                 outline="#FFFFFF", width=max(1, size // 40))
    cv.create_text(cx, cy, text=letters, fill="#FFFFFF", font=font)


def _engine(cv, cx, cy, s, c):
    """A check-engine style block: engine body, valve cover, intake and exhaust stubs."""
    u = s / 10
    w = max(2, s / 22)
    body = [cx - 3 * u, cy - 1.6 * u, cx + 2.2 * u, cy - 1.6 * u, cx + 2.2 * u, cy - 0.6 * u,
            cx + 3.2 * u, cy - 0.6 * u, cx + 3.2 * u, cy + 1.8 * u, cx + 1.4 * u, cy + 1.8 * u,
            cx + 0.6 * u, cy + 2.6 * u, cx - 2.2 * u, cy + 2.6 * u, cx - 3 * u, cy + 1.8 * u]
    cv.create_polygon(body, fill="", outline=c, width=w, joinstyle="round")
    cv.create_line(cx - 1.6 * u, cy - 1.6 * u, cx - 1.6 * u, cy - 2.5 * u, cx + 0.8 * u, cy - 2.5 * u,
                   cx + 0.8 * u, cy - 1.6 * u, fill=c, width=w, joinstyle="round")
    cv.create_line(cx - 2.4 * u, cy - 2.5 * u, cx + 1.6 * u, cy - 2.5 * u, fill=c, width=w, capstyle="round")
    cv.create_line(cx - 3 * u, cy + 0.1 * u, cx - 4.2 * u, cy + 0.1 * u, fill=c, width=w, capstyle="round")
    cv.create_line(cx - 4.2 * u, cy - 0.9 * u, cx - 4.2 * u, cy + 1.1 * u, fill=c, width=w, capstyle="round")
    cv.create_line(cx + 3.2 * u, cy + 0.6 * u, cx + 4.2 * u, cy + 0.6 * u, fill=c, width=w, capstyle="round")
    cv.create_line(cx + 4.2 * u, cy - 0.6 * u, cx + 4.2 * u, cy + 1.8 * u, fill=c, width=w, capstyle="round")


def _abs(cv, cx, cy, s, c, font):
    u = s / 10
    w = max(2, s / 22)
    cv.create_oval(cx - 3 * u, cy - 3 * u, cx + 3 * u, cy + 3 * u, outline=c, width=w)
    for side in (-1, 1):  # the brake-pad brackets on either side of the disc
        x = cx + side * 3.9 * u
        start = 120 if side < 0 else -60
        cv.create_arc(x - 1.2 * u - side * 1.4 * u, cy - 3.3 * u, x + 1.2 * u - side * 1.4 * u, cy + 3.3 * u,
                      start=start, extent=120, style="arc", outline=c, width=w)
    cv.create_text(cx, cy, text="ABS", fill=c, font=font)


def _airbag(cv, cx, cy, s, c):
    """A seated person with a round airbag in front of them."""
    u = s / 10
    w = max(2, s / 18)
    cv.create_oval(cx - 3.6 * u, cy - 3.6 * u, cx - 1.6 * u, cy - 1.6 * u, fill=c, outline="")
    cv.create_line(cx - 2.8 * u, cy - 1.1 * u, cx - 2.2 * u, cy + 1.6 * u, cx + 0.6 * u, cy + 1.6 * u,
                   cx + 0.9 * u, cy + 3.6 * u, fill=c, width=w * 1.3, capstyle="round", joinstyle="round")
    cv.create_line(cx - 2.6 * u, cy - 0.2 * u, cx - 0.6 * u, cy + 0.4 * u, fill=c, width=w, capstyle="round")
    cv.create_oval(cx - 0.2 * u, cy - 3.4 * u, cx + 3.8 * u, cy + 0.6 * u, fill="", outline=c, width=w)


def _scan(cv, cx, cy, s, c):
    u = s / 10
    w = max(2, s / 18)
    cv.create_oval(cx - 3.2 * u, cy - 3.2 * u, cx + 1.4 * u, cy + 1.4 * u, outline=c, width=w)
    cv.create_line(cx + 0.9 * u, cy + 0.9 * u, cx + 3.6 * u, cy + 3.6 * u, fill=c, width=w * 1.6, capstyle="round")
    cv.create_line(cx - 2 * u, cy - 0.6 * u, cx - 1.2 * u, cy + 0.2 * u, cx + 0.4 * u, cy - 1.6 * u,
                   fill=c, width=w, capstyle="round", joinstyle="round")


def _gauge(cv, cx, cy, s, c):
    u = s / 10
    w = max(2, s / 20)
    cv.create_arc(cx - 4 * u, cy - 3 * u, cx + 4 * u, cy + 5 * u, start=0, extent=180, style="arc",
                  outline=c, width=w)
    for i in range(5):
        a = math.radians(180 - i * 45)
        cv.create_line(cx + math.cos(a) * 3 * u, cy + u - math.sin(a) * 3 * u,
                       cx + math.cos(a) * 3.8 * u, cy + u - math.sin(a) * 3.8 * u, fill=c, width=w)
    a = math.radians(55)
    cv.create_line(cx, cy + u, cx + math.cos(a) * 3 * u, cy + u - math.sin(a) * 3 * u, fill=c,
                   width=w * 1.3, capstyle="round")
    cv.create_oval(cx - 0.7 * u, cy + 0.3 * u, cx + 0.7 * u, cy + 1.7 * u, fill=c, outline="")


def _smog(cv, cx, cy, s, c):
    """Exhaust pipe with a tick mark: 'ready for the emissions test'."""
    u = s / 10
    w = max(2, s / 18)
    cv.create_line(cx - 4 * u, cy + 1.5 * u, cx - 1.2 * u, cy + 1.5 * u, fill=c, width=w * 2.2, capstyle="round")
    for i, r in enumerate((0.7, 1.0, 1.3)):
        x = cx - 0.2 * u + i * 1.5 * u
        y = cy + 1.2 * u - i * 1.2 * u
        cv.create_oval(x - r * u, y - r * u, x + r * u, y + r * u, outline=c, width=w * 0.8)
    cv.create_line(cx - 3.2 * u, cy - 2 * u, cx - 2.2 * u, cy - 1 * u, cx - 0.4 * u, cy - 3.2 * u,
                   fill=c, width=w, capstyle="round", joinstyle="round")


def _body(cv, cx, cy, s, c, kind):
    """Side view of a vehicle: truck, suv, car, van."""
    u = s / 10
    w = max(2, s / 22)
    base = cy + 1.6 * u
    if kind == "truck":
        pts = [cx - 4.4 * u, base, cx - 4.4 * u, cy - 0.2 * u, cx - 3 * u, cy - 0.4 * u, cx - 2.2 * u, cy - 2.4 * u,
               cx + 0.2 * u, cy - 2.4 * u, cx + 0.4 * u, cy - 0.2 * u, cx + 4.4 * u, cy - 0.2 * u, cx + 4.4 * u, base]
    elif kind == "suv":
        pts = [cx - 4.4 * u, base, cx - 4.4 * u, cy - 0.2 * u, cx - 3.4 * u, cy - 0.5 * u, cx - 2.4 * u, cy - 2.5 * u,
               cx + 4 * u, cy - 2.5 * u, cx + 4.4 * u, cy - 0.6 * u, cx + 4.4 * u, base]
    elif kind == "van":
        pts = [cx - 4.4 * u, base, cx - 4.4 * u, cy - 0.4 * u, cx - 3.2 * u, cy - 2.8 * u,
               cx + 4.2 * u, cy - 2.8 * u, cx + 4.4 * u, cy - 2.4 * u, cx + 4.4 * u, base]
    else:  # car
        pts = [cx - 4.4 * u, base, cx - 4.4 * u, cy + 0.1 * u, cx - 2.6 * u, cy - 0.4 * u, cx - 1.4 * u, cy - 2 * u,
               cx + 1.6 * u, cy - 2 * u, cx + 2.8 * u, cy - 0.4 * u, cx + 4.4 * u, cy, cx + 4.4 * u, base]
    cv.create_polygon(pts, fill="", outline=c, width=w, joinstyle="round")
    for x in (cx - 2.6 * u, cx + 2.6 * u):
        cv.create_oval(x - 1.1 * u, base - 1.1 * u, x + 1.1 * u, base + 1.1 * u, fill=cv["bg"], outline=c, width=w)


def draw(cv, name, cx, cy, size, color, small_font=None):
    if name == "engine":
        _engine(cv, cx, cy, size, color)
    elif name == "abs":
        _abs(cv, cx, cy, size, color, small_font)
    elif name == "airbag":
        _airbag(cv, cx, cy, size, color)
    elif name == "scan":
        _scan(cv, cx, cy, size, color)
    elif name == "gauge":
        _gauge(cv, cx, cy, size, color)
    elif name == "smog":
        _smog(cv, cx, cy, size, color)
    elif name in ("truck", "suv", "car", "van", "vehicle"):
        _body(cv, cx, cy, size, color, "truck" if name == "vehicle" else name)
