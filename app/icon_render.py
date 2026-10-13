"""
Anti-aliased icon rendering.

The icons in icons.py are drawn with Tk canvas primitives. Tk's canvas has no
anti-aliasing on Windows, so at native (high-DPI) resolution the shapes look jagged
and "pixely". This module runs the SAME icons.draw() code against a Pillow-backed
canvas shim at 4x resolution, then downsamples with LANCZOS, giving smooth edges.
The result is shown as an ordinary PhotoImage, so nothing else about the UI changes.

If Pillow isn't available (older install), HAVE_PIL is False and callers fall back
to drawing the vector icon straight onto the Tk canvas as before.
"""

import os

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    HAVE_PIL = True
except Exception:  # noqa: BLE001 - Pillow not bundled in this build
    HAVE_PIL = False

SS = 4  # supersampling factor; drawn this many times larger, then shrunk for clean edges

_FONT_CACHE = {}


def _font_path():
    if "path" in _FONT_CACHE:
        return _FONT_CACHE["path"]
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    _FONT_CACHE["path"] = path
    return path


def _rgba(h):
    h = (h or "").lstrip("#")
    if len(h) != 6:
        return None
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def _flatten(args):
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        return list(args[0])
    return list(args)


def _font_size(font):
    """Pull a pixel size out of whatever font value icons.py passed (tuple or Tk Font)."""
    try:
        if isinstance(font, (list, tuple)) and len(font) >= 2:
            return abs(int(font[1]))
        if hasattr(font, "cget"):
            return abs(int(font.cget("size")))
    except Exception:  # noqa: BLE001
        pass
    return 0


class _Canvas:
    """Just enough of the Tk canvas API for icons.py to draw into a Pillow image."""

    def __init__(self, size, surface):
        self.surface = surface
        self.img = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def __getitem__(self, _k):
        return self.surface

    def _xy(self, coords):
        return [c * SS for c in coords]

    def _pairs(self, coords):
        s = self._xy(coords)
        return list(zip(s[0::2], s[1::2]))

    def create_polygon(self, *args, **kw):
        pts = self._pairs(_flatten(args))
        fill, outline = kw.get("fill", ""), kw.get("outline", "")
        w = max(1, int(round(kw.get("width", 1) * SS)))
        if fill != "":
            self.d.polygon(pts, fill=_rgba(fill))
        if outline != "":
            self.d.line(pts + [pts[0]], fill=_rgba(outline), width=w, joint="curve")

    def create_oval(self, x0, y0, x1, y1, **kw):
        xy = self._xy([x0, y0, x1, y1])
        fill, outline = kw.get("fill", ""), kw.get("outline", "")
        self.d.ellipse(xy, fill=(_rgba(fill) if fill != "" else None),
                       outline=(_rgba(outline) if outline != "" else None),
                       width=max(1, int(round(kw.get("width", 1) * SS))) if outline != "" else 1)

    def create_rectangle(self, x0, y0, x1, y1, **kw):
        xy = self._xy([x0, y0, x1, y1])
        fill, outline = kw.get("fill", ""), kw.get("outline", "")
        self.d.rectangle(xy, fill=(_rgba(fill) if fill != "" else None),
                         outline=(_rgba(outline) if outline != "" else None),
                         width=max(1, int(round(kw.get("width", 1) * SS))) if outline != "" else 1)

    def create_line(self, *args, **kw):
        pts = self._pairs(_flatten(args))
        fill = _rgba(kw.get("fill", "#000000"))
        w = max(1, int(round(kw.get("width", 1) * SS)))
        self.d.line(pts, fill=fill, width=w, joint="curve")
        if kw.get("capstyle") == "round" or kw.get("joinstyle") == "round":
            r = w / 2.0
            for (x, y) in pts:
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def create_arc(self, x0, y0, x1, y1, **kw):
        xy = self._xy([x0, y0, x1, y1])
        a, e = kw.get("start", 0), kw.get("extent", 90)
        lo, hi = min(a, a + e), max(a, a + e)
        ps, pe = (-hi) % 360, (-lo) % 360
        if pe <= ps:
            pe += 360
        self.d.arc(xy, ps, pe, fill=_rgba(kw.get("outline", "#000000")),
                   width=max(1, int(round(kw.get("width", 1) * SS))))

    def create_text(self, x, y, **kw):
        text = kw.get("text", "")
        if not text:
            return
        size = _font_size(kw.get("font")) or 12
        path = _font_path()
        try:
            font = ImageFont.truetype(path, int(size * SS)) if path else ImageFont.load_default()
        except Exception:  # noqa: BLE001
            font = ImageFont.load_default()
        self.d.text((x * SS, y * SS), text, fill=_rgba(kw.get("fill", "#000000")), font=font, anchor="mm")


def photo(painter, box, surface):
    """Render `painter(canvas, box/2, box/2)` to a smooth, anti-aliased PhotoImage of `box` px.
    Returns None if Pillow is unavailable (caller then draws the vector icon instead)."""
    if not HAVE_PIL:
        return None
    try:
        cv = _Canvas(box, surface)
        painter(cv, box / 2.0, box / 2.0)
        small = cv.img.resize((box, box), Image.LANCZOS)
        return ImageTk.PhotoImage(small)
    except Exception:  # noqa: BLE001 - never let an icon take down the UI
        return None
