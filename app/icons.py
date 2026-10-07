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
    kw.setdefault("splinesteps", 36)  # many steps = smooth corners on high-resolution screens
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
    """A shield emblem: soft shadow, a steel rim, a dark field with a glossy upper half, and the monogram."""
    h = size / 2

    def shield(inset):
        l, r = cx - h * 0.86 + inset, cx + h * 0.86 - inset
        t, b = cy - h * 0.9 + inset, cy + h - inset * 1.3
        return [l, t + size * 0.06, l + (r - l) * 0.5, t - size * 0.03, r, t + size * 0.06,
                r, cy + h * 0.2, cx, b, l, cy + h * 0.2]

    bg = _bg(cv)
    shadow = [x + (size * 0.03 if i % 2 else 0) for i, x in enumerate(shield(0))]
    cv.create_polygon(shadow, smooth=True, fill=blend(bg, "#000000", 0.12), outline="")
    cv.create_polygon(shield(0), smooth=True, fill=blend(fill, "#FFFFFF", 0.55), outline="")   # steel rim
    inner = shield(size * 0.07)
    cv.create_polygon(inner, smooth=True, fill=fill, outline="")
    # gloss: the same shape, squashed into the top half
    top = min(inner[1::2])
    gloss = [v if i % 2 == 0 else top + (v - top) * 0.45 for i, v in enumerate(inner)]
    cv.create_polygon(gloss, smooth=True, fill=blend(fill, "#FFFFFF", 0.14), outline="")
    cv.create_text(cx, cy + size * 0.03, text=letters, fill="#FFFFFF", font=font)


# --- Feature icons ----------------------------------------------------------------------
def _engine(cv, cx, cy, s, c):
    u = s / 10
    w = max(2, s / 26)
    dark = blend(c, _bg(cv), 0.85)  # fins in the background color, so they read on any fill
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
    """A tailpipe puffing exhaust, with a round check badge: 'passes the emissions test'."""
    u = s / 10
    w = max(2, s / 16)
    bg = _bg(cv)
    py = cy + 2.0 * u
    cv.create_line(cx - 4.4 * u, py, cx - 1.4 * u, py, fill=c, width=w * 2, capstyle="butt")
    cv.create_oval(cx - 1.75 * u, py - 0.85 * u, cx - 0.95 * u, py + 0.85 * u, fill=bg, outline=c, width=w * 0.7)
    for px, dy, r in ((0.3, 0.0, 0.55), (1.6, -0.4, 0.75), (3.2, -0.9, 0.95)):
        cv.create_oval(cx + (px - r) * u, py + (dy - r) * u, cx + (px + r) * u, py + (dy + r) * u,
                       fill=bg, outline=c, width=w * 0.6)
    bx, by, br = cx - 1.2 * u, cy - 2.2 * u, 1.9 * u
    cv.create_oval(bx - br, by - br, bx + br, by + br, fill=c, outline="")
    cv.create_line(bx - 0.9 * u, by + 0.05 * u, bx - 0.2 * u, by + 0.8 * u, bx + 1.0 * u, by - 0.7 * u,
                   fill=bg, width=w * 0.9, capstyle="round", joinstyle="round")


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


def _semi(cv, cx, cy, s, c):
    """Tractor-trailer side view."""
    u = s / 10
    bg = _bg(cv)
    base = cy + 1.4 * u
    cv.create_rectangle(cx - 4.8 * u, cy - 2.6 * u, cx + 1.2 * u, base - 0.3 * u, fill=c, outline="")  # trailer
    cab = [cx + 1.6 * u, base - 0.3 * u, cx + 1.6 * u, cy - 1.9 * u, cx + 3.3 * u, cy - 1.9 * u,
           cx + 4.6 * u, cy - 0.4 * u, cx + 4.6 * u, base - 0.3 * u]
    cv.create_polygon(cab, fill=c, outline=c, width=2, joinstyle="round")
    cv.create_polygon([cx + 2.2 * u, cy - 0.5 * u, cx + 2.2 * u, cy - 1.4 * u, cx + 3.1 * u, cy - 1.4 * u,
                       cx + 3.9 * u, cy - 0.5 * u], fill=blend(bg, c, 0.25), outline="")
    cv.create_line(cx + 1.6 * u, cy - 2.6 * u, cx + 1.6 * u, cy - 1.9 * u, fill=c, width=max(2, s / 28))  # stack
    for x in (cx - 3.9 * u, cx - 2.7 * u, cx + 2.4 * u, cx + 3.8 * u):
        r = 0.6 * u
        cv.create_oval(x - r - 0.15 * u, base - r - 0.15 * u, x + r + 0.15 * u, base + r + 0.15 * u, fill=bg,
                       outline="")
        cv.create_oval(x - r, base - r, x + r, base + r, fill="#1A1F25", outline="")


def _blink(cv, cx, cy, s, c):
    """A check-engine light giving off flashes: reading blink codes."""
    u = s / 10
    _engine(cv, cx, cy + 0.8 * u, s * 0.72, c)
    w = max(2, s / 22)
    for ang in (-150, -120, -90, -60, -30):
        a = math.radians(ang)
        x0, y0 = cx + math.cos(a) * 3.2 * u, cy + 0.4 * u + math.sin(a) * 3.2 * u
        x1, y1 = cx + math.cos(a) * 4.4 * u, cy + 0.4 * u + math.sin(a) * 4.4 * u
        cv.create_line(x0, y0, x1, y1, fill=c, width=w, capstyle="round")


def _home(cv, cx, cy, s, c):
    """A house."""
    u = s / 10
    w = max(2, s / 14)
    cv.create_polygon(cx - 4.4 * u, cy - 0.4 * u, cx, cy - 4.4 * u, cx + 4.4 * u, cy - 0.4 * u,
                      fill="", outline=c, width=w, joinstyle="round")
    cv.create_rectangle(cx - 3 * u, cy - 1.2 * u, cx + 3 * u, cy + 3.8 * u, fill=c, outline="")
    cv.create_rectangle(cx - 0.9 * u, cy + 1 * u, cx + 0.9 * u, cy + 3.8 * u, fill=_bg(cv), outline="")


def _alert(cv, cx, cy, s, c):
    """A warning triangle with an exclamation mark."""
    u = s / 10
    cv.create_polygon(cx, cy - 4.2 * u, cx + 4.6 * u, cy + 3.6 * u, cx - 4.6 * u, cy + 3.6 * u,
                      fill=c, outline=c, width=max(2, s / 12), joinstyle="round")
    bg = _bg(cv)
    cv.create_line(cx, cy - 1.6 * u, cx, cy + 1.1 * u, fill=bg, width=max(2, s / 11), capstyle="round")
    r = max(1.2, s / 22)
    cv.create_oval(cx - r, cy + 2.3 * u - r, cx + r, cy + 2.3 * u + r, fill=bg, outline="")


def _help(cv, cx, cy, s, c, font=None):
    """A question mark in a ring."""
    r = s * 0.42
    cv.create_oval(cx - r, cy - r, cx + r, cy + r, fill=c, outline="")
    cv.create_text(cx, cy + s * 0.02, text="?", fill=_bg(cv), font=font or ("Helvetica", max(8, int(s * 0.5)), "bold"))


def draw(cv, name, cx, cy, size, color, small_font=None, halo=False):
    if halo:  # a soft disc behind the icon
        r = size * 0.72
        cv.create_oval(cx - r, cy - r, cx + r, cy + r, fill=blend(_bg(cv), color, 0.13), outline="")
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
    elif name == "semi":
        _semi(cv, cx, cy, size, color)
    elif name == "blink":
        _blink(cv, cx, cy, size, color)
    elif name == "home":
        _home(cv, cx, cy, size, color)
    elif name == "alert":
        _alert(cv, cx, cy, size, color)
    elif name == "help":
        _help(cv, cx, cy, size, color, small_font)
    elif name in ("truck", "suv", "car", "van", "vehicle"):
        _body(cv, cx, cy, size, color, "truck" if name == "vehicle" else name)
