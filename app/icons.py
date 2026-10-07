"""
Original icons drawn on a Tk canvas (no image files, sharp at any size).

draw(canvas, name, cx, cy, size, color) where name is one of:
  engine, abs, airbag, scan, gauge, smog, vehicle, truck, suv, car, van
make_badge(canvas, letters, cx, cy, size, fill, font) draws a two-tone emblem with a monogram.
Tk has no gradients, so soft glows and shading are built from stacked shapes in blended colors.
"""

import math

BADGE_COLORS = ["#2F7BC0", "#3A9A56", "#C0622F", "#7A5CC8", "#2C5C9A", "#C8901E",
                "#2E9C94", "#B03E6E", "#5E7488", "#D0502A"]


def badge_color(make):
    return BADGE_COLORS[sum(ord(ch) * (i + 1) for i, ch in enumerate(make)) % len(BADGE_COLORS)]


def _bg(cv):
    return getattr(cv, "surface", None) or cv["bg"]


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def blend(c1, c2, t):
    """Mix two hex colors: t=0 gives c1, t=1 gives c2."""
    a, b = _rgb(c1), _rgb(c2)
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def rounded_rect(cv, x0, y0, x1, y1, r, **kw):
    r = max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
           x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return cv.create_polygon(pts, smooth=True, **kw)


def glow(cv, cx, cy, radius, color, steps=10, strength=0.55):
    """A soft halo: rings fading from the canvas background toward `color`."""
    bg = _bg(cv)
    for i in range(steps):
        t = (i + 1) / steps
        r = radius * (1 - 0.55 * t)
        cv.create_oval(cx - r, cy - r, cx + r, cy + r, outline="", fill=blend(bg, color, strength * t ** 1.6))


# --- Make emblems -----------------------------------------------------------------------
def make_badge(cv, letters, cx, cy, size, fill, font):
    """A shield-shaped emblem: lit from the top, a bright rim, a pressed inner field and the monogram."""
    h = size / 2
    top, bottom, left, right = cy - h * 0.92, cy + h, cx - h * 0.86, cx + h * 0.86

    def shield(inset):
        l, r, t, b = left + inset, right - inset, top + inset, bottom - inset * 1.25
        return [l + (r - l) * 0.18, t, cx, t - size * 0.02, r - (r - l) * 0.18, t, r, t + size * 0.08,
                r, cy + h * 0.18, r - (r - l) * 0.12, cy + h * 0.55, cx, b, l + (r - l) * 0.12, cy + h * 0.55,
                l, cy + h * 0.18, l, t + size * 0.08]

    bg = _bg(cv)
    cv.create_polygon(shield(-size * 0.05), smooth=True, fill=blend(bg, fill, 0.25), outline="")  # soft shadow
    rim = blend(fill, "#FFFFFF", 0.45)
    cv.create_polygon(shield(0), smooth=True, fill=rim, outline="")
    # inner field: horizontal bands from light (top) to deep (bottom)
    bands = 9
    inner = shield(size * 0.06)
    xs, ys = inner[0::2], inner[1::2]
    y0, y1 = min(ys), max(ys)
    cv.create_polygon(inner, smooth=True, fill=blend(fill, "#000000", 0.25), outline="")
    for i in range(bands):
        t = i / bands
        clip = y0 + (y1 - y0) * t
        pts = []
        for x, y in zip(xs, ys):
            pts += [x, max(y, clip) if y < clip else y]
        cv.create_polygon(pts, smooth=True, outline="",
                          fill=blend(blend(fill, "#FFFFFF", 0.22), blend(fill, "#000000", 0.28), t))
    # highlight sweep across the top
    cv.create_arc(left + size * 0.12, top + size * 0.05, right - size * 0.12, cy + h * 0.2, start=25, extent=130,
                  style="arc", outline=blend(fill, "#FFFFFF", 0.6), width=max(1, size / 34))
    cv.create_text(cx + 1, cy + size * 0.02 + 1, text=letters, fill=blend(fill, "#000000", 0.55), font=font)
    cv.create_text(cx, cy + size * 0.02, text=letters, fill="#FFFFFF", font=font)


# --- Feature icons ----------------------------------------------------------------------
def _engine(cv, cx, cy, s, c):
    u = s / 10
    w = max(2, s / 26)
    dark = blend(c, "#000000", 0.45)
    body = [cx - 3 * u, cy - 1.4 * u, cx + 2.2 * u, cy - 1.4 * u, cx + 2.2 * u, cy - 0.5 * u,
            cx + 3.3 * u, cy - 0.5 * u, cx + 3.3 * u, cy + 1.9 * u, cx + 1.4 * u, cy + 1.9 * u,
            cx + 0.6 * u, cy + 2.7 * u, cx - 2.2 * u, cy + 2.7 * u, cx - 3 * u, cy + 1.9 * u]
    cv.create_polygon(body, fill=c, outline=c, width=w, joinstyle="round")
    cv.create_rectangle(cx - 1.7 * u, cy - 2.4 * u, cx + 0.9 * u, cy - 1.4 * u, fill=c, outline="")
    cv.create_line(cx - 2.6 * u, cy - 2.5 * u, cx + 1.8 * u, cy - 2.5 * u, fill=c, width=w * 1.4, capstyle="round")
    for i in range(3):  # cooling fins
        x = cx - 1.8 * u + i * 1.3 * u
        cv.create_line(x, cy - 0.4 * u, x, cy + 1.6 * u, fill=dark, width=w, capstyle="round")
    cv.create_line(cx - 3 * u, cy + 0.2 * u, cx - 4.2 * u, cy + 0.2 * u, fill=c, width=w * 1.4, capstyle="round")
    cv.create_line(cx - 4.3 * u, cy - 0.8 * u, cx - 4.3 * u, cy + 1.2 * u, fill=c, width=w * 1.4, capstyle="round")
    cv.create_line(cx + 3.3 * u, cy + 0.7 * u, cx + 4.3 * u, cy + 0.7 * u, fill=c, width=w * 1.4, capstyle="round")


def _abs(cv, cx, cy, s, c, font):
    u = s / 10
    w = max(2, s / 18)
    cv.create_oval(cx - 3 * u, cy - 3 * u, cx + 3 * u, cy + 3 * u, outline=c, width=w * 1.2)
    cv.create_oval(cx - 2.2 * u, cy - 2.2 * u, cx + 2.2 * u, cy + 2.2 * u, outline="",
                   fill=blend(_bg(cv), c, 0.18))
    for side in (-1, 1):
        x = cx + side * 2.5 * u
        start = 125 if side < 0 else -55
        cv.create_arc(x - 2.3 * u, cy - 4 * u, x + 2.3 * u, cy + 4 * u, start=start, extent=110, style="arc",
                      outline=c, width=w * 1.2)
    cv.create_text(cx, cy, text="ABS", fill=c, font=font)


def _airbag(cv, cx, cy, s, c):
    u = s / 10
    w = max(2, s / 14)
    cv.create_oval(cx - 0.4 * u, cy - 3.6 * u, cx + 4 * u, cy + 0.8 * u, fill=blend(_bg(cv), c, 0.3), outline=c,
                   width=w * 0.7)
    cv.create_arc(cx + 0.4 * u, cy - 3 * u, cx + 3.2 * u, cy - 0.2 * u, start=100, extent=80, style="arc",
                  outline=blend(c, "#FFFFFF", 0.5), width=max(1, w * 0.4))
    cv.create_oval(cx - 3.8 * u, cy - 3.8 * u, cx - 1.6 * u, cy - 1.6 * u, fill=c, outline="")
    cv.create_line(cx - 2.9 * u, cy - 1.1 * u, cx - 2.3 * u, cy + 1.6 * u, cx + 0.6 * u, cy + 1.6 * u,
                   cx + 0.9 * u, cy + 3.6 * u, fill=c, width=w, capstyle="round", joinstyle="round")
    cv.create_line(cx - 2.6 * u, cy - 0.1 * u, cx - 0.8 * u, cy + 0.5 * u, fill=c, width=w * 0.7, capstyle="round")


def _scan(cv, cx, cy, s, c):
    u = s / 10
    w = max(2, s / 15)
    cv.create_oval(cx - 3.4 * u, cy - 3.4 * u, cx + 1.4 * u, cy + 1.4 * u, fill=blend(_bg(cv), c, 0.2),
                   outline=c, width=w)
    cv.create_arc(cx - 2.6 * u, cy - 2.6 * u, cx + 0.6 * u, cy + 0.6 * u, start=100, extent=70, style="arc",
                  outline=blend(c, "#FFFFFF", 0.55), width=max(1, w * 0.5))
    cv.create_line(cx + 0.9 * u, cy + 0.9 * u, cx + 3.8 * u, cy + 3.8 * u, fill=c, width=w * 1.8, capstyle="round")


def _gauge(cv, cx, cy, s, c, colors=("#3DDC84", "#F2A93B", "#FF5A4E")):
    u = s / 10
    w = max(3, s / 11)
    box = (cx - 4 * u, cy - 3 * u, cx + 4 * u, cy + 5 * u)
    for i, col in enumerate(colors):  # green, amber, red zones
        cv.create_arc(*box, start=180 - i * 60, extent=-58, style="arc", outline=col, width=w)
    a = math.radians(48)
    cv.create_line(cx, cy + u, cx + math.cos(a) * 3.1 * u, cy + u - math.sin(a) * 3.1 * u, fill=c,
                   width=max(2, s / 18), capstyle="round")
    cv.create_oval(cx - 0.8 * u, cy + 0.2 * u, cx + 0.8 * u, cy + 1.8 * u, fill=c, outline="")


def _smog(cv, cx, cy, s, c):
    """A leaf with a vein and a check mark: 'clean enough to pass'."""
    u = s / 10
    w = max(2, s / 18)
    leaf = [cx - 3.6 * u, cy + 3.2 * u, cx - 3.4 * u, cy - 1.6 * u, cx + 0.2 * u, cy - 3.8 * u,
            cx + 3.8 * u, cy - 3.6 * u, cx + 3.4 * u, cy + 0.4 * u, cx + 0.8 * u, cy + 3.4 * u]
    cv.create_polygon(leaf, smooth=True, fill=blend(_bg(cv), c, 0.35), outline=c, width=w)
    cv.create_line(cx - 3.6 * u, cy + 3.2 * u, cx + 2.6 * u, cy - 2.6 * u, fill=c, width=w * 0.8, capstyle="round")
    cv.create_line(cx - 1.4 * u, cy + 0.6 * u, cx - 0.2 * u, cy + 1.8 * u, cx + 2 * u, cy - 0.8 * u,
                   fill="#FFFFFF", width=w * 1.1, capstyle="round", joinstyle="round")


def _body(cv, cx, cy, s, c, kind):
    """Filled side-view silhouette with windows cut out and hubbed wheels."""
    u = s / 10
    base = cy + 1.4 * u
    bg = _bg(cv)
    glass = blend(bg, c, 0.25)
    if kind == "truck":
        shell = [cx - 4.6 * u, base, cx - 4.6 * u, cy - 0.1 * u, cx - 3.2 * u, cy - 0.4 * u, cx - 2.2 * u, cy - 2.4 * u,
                 cx + 0.3 * u, cy - 2.4 * u, cx + 0.5 * u, cy - 0.3 * u, cx + 4.6 * u, cy - 0.3 * u, cx + 4.6 * u, base]
        windows = [[cx - 2.9 * u, cy - 0.5 * u, cx - 2 * u, cy - 1.9 * u, cx - 0.1 * u, cy - 1.9 * u,
                    cx - 0.1 * u, cy - 0.5 * u]]
    elif kind == "suv":
        shell = [cx - 4.6 * u, base, cx - 4.6 * u, cy - 0.1 * u, cx - 3.6 * u, cy - 0.5 * u, cx - 2.5 * u, cy - 2.6 * u,
                 cx + 4.1 * u, cy - 2.6 * u, cx + 4.6 * u, cy - 0.6 * u, cx + 4.6 * u, base]
        windows = [[cx - 3.2 * u, cy - 0.6 * u, cx - 2.2 * u, cy - 2.1 * u, cx + 0.4 * u, cy - 2.1 * u,
                    cx + 0.4 * u, cy - 0.6 * u],
                   [cx + 0.8 * u, cy - 0.6 * u, cx + 0.8 * u, cy - 2.1 * u, cx + 3.7 * u, cy - 2.1 * u,
                    cx + 4 * u, cy - 0.6 * u]]
    elif kind == "van":
        shell = [cx - 4.6 * u, base, cx - 4.6 * u, cy - 0.4 * u, cx - 3.3 * u, cy - 2.9 * u,
                 cx + 4.4 * u, cy - 2.9 * u, cx + 4.6 * u, cy - 2.4 * u, cx + 4.6 * u, base]
        windows = [[cx - 3.9 * u, cy - 0.6 * u, cx - 2.9 * u, cy - 2.4 * u, cx - 1.4 * u, cy - 2.4 * u,
                    cx - 1.4 * u, cy - 0.6 * u],
                   [cx - 1 * u, cy - 0.6 * u, cx - 1 * u, cy - 2.4 * u, cx + 3.9 * u, cy - 2.4 * u,
                    cx + 3.9 * u, cy - 0.6 * u]]
    else:  # car
        shell = [cx - 4.6 * u, base, cx - 4.6 * u, cy + 0.1 * u, cx - 2.7 * u, cy - 0.4 * u, cx - 1.4 * u, cy - 2.1 * u,
                 cx + 1.6 * u, cy - 2.1 * u, cx + 2.9 * u, cy - 0.4 * u, cx + 4.6 * u, cy, cx + 4.6 * u, base]
        windows = [[cx - 2.1 * u, cy - 0.5 * u, cx - 1.1 * u, cy - 1.7 * u, cx + 0.1 * u, cy - 1.7 * u,
                    cx + 0.1 * u, cy - 0.5 * u],
                   [cx + 0.5 * u, cy - 0.5 * u, cx + 0.5 * u, cy - 1.7 * u, cx + 1.4 * u, cy - 1.7 * u,
                    cx + 2.3 * u, cy - 0.5 * u]]
    cv.create_polygon(shell, smooth=(kind == "car"), fill=c, outline=c, width=max(2, s / 30), joinstyle="round")
    for win in windows:
        cv.create_polygon(win, fill=glass, outline="")
    cv.create_line(cx - 4.2 * u, cy + 0.5 * u, cx + 4.2 * u, cy + 0.5 * u, fill=blend(c, "#FFFFFF", 0.35),
                   width=max(1, s / 60))
    for x in (cx - 2.7 * u, cx + 2.7 * u):
        r = 1.25 * u
        cv.create_oval(x - r - 0.25 * u, base - r - 0.25 * u, x + r + 0.25 * u, base + r + 0.25 * u, fill=bg,
                       outline="")
        cv.create_oval(x - r, base - r, x + r, base + r, fill="#1A1F25", outline=blend(c, "#000000", 0.3), width=1)
        cv.create_oval(x - 0.5 * u, base - 0.5 * u, x + 0.5 * u, base + 0.5 * u, fill=blend(c, "#FFFFFF", 0.4),
                       outline="")


def draw(cv, name, cx, cy, size, color, small_font=None, halo=False):
    if halo:
        glow(cv, cx, cy, size * 0.78, color)
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
