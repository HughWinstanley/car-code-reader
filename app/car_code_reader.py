#!/usr/bin/env python3
"""
Car Code Reader
===============
Plug an OBD-II adapter into a car or truck, click Scan, and see what's wrong in plain English:
check-engine codes on any 1996+ vehicle, plus ABS, airbag and body modules on most Fords and GMs.

Requires Python 3.8+ (with Tk) and pyserial:   pip install pyserial
Run:                                             python car_code_reader.py
"""

import datetime
import os
import queue
import re
import sys
import threading
import time
import urllib.parse
import webbrowser
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

from obd_core import (CONN_SERIAL, CONN_WIFI, CONN_DEMO, CONN_DEMO_OLD, ECU_NAMES, MS, PIDS,
                      decode_readiness, format_pid, list_ports, make_from_vin, open_adapter,
                      year_from_vin)
from dtc_database import decode_dtc_bytes, describe_dtc, severity, uds_status_text, why_it_matters
import icons
import updater
import vehicles
from version import VERSION

APP_NAME = "Car Code Reader"
IS_MAC = sys.platform == "darwin"
HERE = os.path.dirname(os.path.abspath(__file__))
CONN_AUTO = "Find my adapter automatically"

# --- Palette: white paper, black ink. Color is kept only for status (red, amber, green) --------
C = {
    "page": "#FFFFFF", "panel": "#FFFFFF", "raised": "#F3F3F3", "ink": "#000000", "muted": "#6B6B6B",
    "line": "#E2E2E2", "header": "#000000", "header_hover": "#2A2A2A", "side": "#FFFFFF", "hover": "#F3F3F3",
    "black": "#000000",
    "amber": "#E39A12", "amber_ink": "#8A5A00", "amber_soft": "#FFF3DC",
    "red": "#D9362B", "red_soft": "#FDE6E4",
    "green": "#1E8A4A", "green_soft": "#E2F3E8",
    "blue": "#000000", "blue_soft": "#EFEFEF",
    "off": "#A3A3A3", "off_soft": "#F1F1F1", "steel": "#000000",
}
LEVELS = {  # urgency -> (bar color, pill background, pill text color, words)
    "high": (C["red"], C["red_soft"], C["red"], "Fix soon"),
    "medium": (C["amber"], C["amber_soft"], C["amber_ink"], "Get it checked"),  # noqa: E241
    "low": (C["blue"], C["blue_soft"], C["blue"], "Low priority"),
    "past": (C["off"], C["off_soft"], C["muted"], "Past problem"),
}
LEVEL_ORDER = {"high": 0, "medium": 1, "low": 2, "past": 3}

_FONTS = {}


def F(size, weight="normal"):
    """System font at a given size (cached)."""
    key = (size, weight)
    if key not in _FONTS:
        family = tkfont.nametofont("TkDefaultFont").actual("family")
        _FONTS[key] = tkfont.Font(family=family, size=size, weight=weight)
    return _FONTS[key]


# ----------------------------------------------------------------------------
# Small custom widgets (they look the same on Mac, Windows and Linux)
# ----------------------------------------------------------------------------
class PillButton(tk.Canvas):
    STYLES = {
        "primary": {"fill": "#000000", "hover": "#2A2A2A", "text": "#FFFFFF", "outline": "#000000"},
        "secondary": {"fill": "#FFFFFF", "hover": "#F3F3F3", "text": "#000000", "outline": "#000000"},
        "danger": {"fill": "#FFFFFF", "hover": C["red_soft"], "text": C["red"], "outline": C["red"]},
        "onheader": {"fill": "#000000", "hover": "#2A2A2A", "text": "#FFFFFF", "outline": "#FFFFFF"},
    }

    def __init__(self, parent, text, command, kind="secondary", big=False):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, bd=0, cursor="hand2", takefocus=1)
        self.command, self.kind, self.big = command, kind, big
        self.font = F(15 if big else 13, "bold")
        self.enabled, self.hovering = True, False
        self.set_text(text)
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<ButtonRelease-1>", lambda e: self._click())
        self.bind("<Return>", lambda e: self._click())
        self.bind("<space>", lambda e: self._click())
        self.bind("<FocusIn>", lambda e: self._draw())
        self.bind("<FocusOut>", lambda e: self._draw())

    def set_text(self, text):
        self.text = text
        padx, pady = (24, 12) if self.big else (15, 7)
        self.w = self.font.measure(text) + 2 * padx
        self.h = self.font.metrics("linespace") + 2 * pady
        self.configure(width=self.w, height=self.h)
        self._draw()

    def set_enabled(self, on):
        self.enabled = bool(on)
        self.configure(cursor="hand2" if on else "arrow")
        self._draw()

    def _hover(self, on):
        self.hovering = on
        self._draw()

    def _click(self):
        if self.enabled and self.command:
            self.command()

    def _draw(self):
        self.delete("all")
        st = self.STYLES[self.kind]
        if not self.enabled:
            fill, text, outline = (C["off_soft"], C["off"], C["line"])
        else:
            fill = st["hover"] if self.hovering else st["fill"]
            text, outline = st["text"], st["outline"]
        r, w, h = self.h / 2, self.w - 2, self.h - 2
        pts = [1 + r, 1, w - r, 1, w, 1, w, 1 + r, w, h - r, w, h, w - r, h, 1 + r, h, 1, h, 1, h - r, 1, 1 + r, 1, 1]
        self.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=1)
        if self.focus_displayof() == self and self.enabled:
            self.create_polygon(pts, smooth=True, fill="", outline=C["amber"], width=2)
        self.create_text(self.w / 2, self.h / 2, text=self.text, fill=text, font=self.font)


class LinkLabel(tk.Label):
    def __init__(self, parent, text, command, size=13):
        under = tkfont.Font(font=F(size, "bold"))
        under.configure(underline=True)
        self._fonts = (F(size, "bold"), under)
        super().__init__(parent, text=text, fg="#000000", bg=parent["bg"], font=self._fonts[1], cursor="hand2")
        self.bind("<Button-1>", lambda e: command())


class Lamp(tk.Canvas):
    """The dashboard warning light: gray (not connected), amber/red (problems), green (all clear)."""
    STATES = {
        "off": ("#D4D4D4", "#F1F1F1", "?"), "busy": ("#000000", "#EFEFEF", "…"),
        "ok": (C["green"], C["green_soft"], "✓"), "warn": (C["amber"], C["amber_soft"], "!"),
        "bad": (C["red"], C["red_soft"], "!"),
    }

    def __init__(self, parent, size=104):
        super().__init__(parent, width=size, height=size, bg=parent["bg"], highlightthickness=0)
        self.size, self.state, self._pulse, self._job = size, "off", False, None
        self.set("off")

    def set(self, state):
        self.state = state
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        self._draw()
        if state == "busy":
            self._tick()

    def _tick(self):
        self._pulse = not self._pulse
        self._draw()
        self._job = self.after(550, self._tick)

    def _draw(self):
        self.delete("all")
        core, _soft, glyph = self.STATES[self.state]
        s = self.size
        if self.state != "off" and (self.state != "busy" or self._pulse):
            icons.glow(self, s / 2, s / 2, s / 2 - 1, core, steps=14, strength=0.6)
        m = s * 0.2
        self.create_oval(m, m, s - m, s - m, fill=core, outline="")
        self.create_oval(m + s * 0.08, m + s * 0.05, s - m - s * 0.08, s / 2, fill=icons.blend(core, "#FFFFFF", 0.25),
                         outline="")
        self.create_oval(m + s * 0.04, m + s * 0.04, s - m - s * 0.04, s - m - s * 0.04, fill="", outline="")
        self.create_text(s / 2, s / 2 + 1, text=glyph, fill="#FFFFFF",
                         font=F(int(s * 0.28), "bold"))


class ScrollArea(tk.Frame):
    """A vertically scrolling frame (mouse wheel / trackpad aware)."""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", lambda e: self._update())
        self.canvas.bind("<Configure>", lambda e: (self.canvas.itemconfigure(self._win, width=e.width),
                                                   self._update()))
        self.bind("<Enter>", lambda e: self._wheel(True))
        self.bind("<Leave>", lambda e: self._wheel(False))

    def _update(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        needed = self.inner.winfo_reqheight() > self.canvas.winfo_height() + 2
        if needed and not self.bar.winfo_ismapped():
            self.bar.pack(side="right", fill="y", before=self.canvas)
        elif not needed and self.bar.winfo_ismapped():
            self.bar.pack_forget()
            self.canvas.yview_moveto(0)

    def scroll_to(self, widget):
        self.inner.update_idletasks()
        self._update()
        total = max(1, self.inner.winfo_reqheight())
        self.canvas.yview_moveto(max(0.0, widget.winfo_y() - 8) / total)

    def _wheel(self, on):
        if on:
            self.bind_all("<MouseWheel>", self._on_wheel)
            self.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))
            self.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))
        else:
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                self.unbind_all(seq)

    def _on_wheel(self, e):
        if not self.bar.winfo_ismapped():
            return
        step = -e.delta if IS_MAC else -e.delta // 120 * 3
        self.canvas.yview_scroll(int(step), "units")

    def clear(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self.canvas.yview_moveto(0)


def wrap_on_resize(label, margin):
    def resize(e):
        if label.winfo_exists():
            label.configure(wraplength=max(200, e.width - margin))
    label.master.bind("<Configure>", resize, add="+")


def is_safety_module(name):
    n = name.lower()
    return any(k in n for k in ("abs", "brake", "airbag", "restraint", "sdm", "rcm"))


def friendly_module(name):
    """'Engine (ECM/PCM)' -> 'Engine'; keeps '(second network)'."""
    return re.sub(r" \((?!second network)[^)]*\)", "", name).replace(" / ", " and ")


def as_sentences(text):
    parts = [p.strip() for p in text.split("·") if p.strip()]
    return " ".join(p[0].upper() + p[1:] + ("" if p.endswith(".") else ".") for p in parts)


class RoundPanel(tk.Canvas):
    """A rounded card. Put widgets in .inner; the card grows to fit them."""

    def __init__(self, parent, pad=(20, 16), radius=18, fill=None, outline=None, **kw):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, bd=0, height=20, **kw)
        self.fill, self.outline, self.radius = fill or C["panel"], outline or C["line"], radius
        self.padx, self.pady = pad
        self.inner = tk.Frame(self, bg=self.fill)
        self._win = self.create_window(self.padx, self.pady, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._fit, add="+")
        self.bind("<Configure>", self._fit, add="+")

    def _fit(self, _e=None):
        w = self.winfo_width()
        if w > 2 * self.padx:
            self.itemconfigure(self._win, width=w - 2 * self.padx)
        h = self.inner.winfo_reqheight() + 2 * self.pady
        if int(float(self["height"])) != h:
            self.configure(height=h)
        self.delete("card")
        icons.rounded_rect(self, 1, 1, max(w, 4) - 1, h - 1, self.radius, fill=self.fill, outline=self.outline,
                           tags="card")
        self.tag_lower("card")


class Tile(tk.Canvas):
    """A rounded card drawn on one canvas: a picture, a title and one line under it. Click to use."""

    def __init__(self, parent, title, subtitle, painter, command, width=210, art=96, title_size=15):
        super().__init__(parent, width=width, height=art + 80, bg=parent["bg"], highlightthickness=0, bd=0,
                         cursor="hand2", takefocus=1)
        self.surface = C["panel"]
        self.command = command
        longest = max((F(title_size, "bold").measure(w) for w in title.split()), default=0)
        while longest > width - 28 and title_size > 10:  # shrink rather than break a word in two
            title_size -= 1
            longest = max(F(title_size, "bold").measure(w) for w in title.split())
        top = 16
        painter(self, width / 2, top + art / 2)
        t = self.create_text(width / 2, top + art + 8, text=title, fill=C["ink"], font=F(title_size, "bold"),
                             width=width - 24, justify="center", anchor="n")
        y = self.bbox(t)[3] + 4
        if subtitle:
            st = self.create_text(width / 2, y, text=subtitle, fill=C["muted"], font=F(12), width=width - 28,
                                  justify="center", anchor="n")
            y = self.bbox(st)[3]
        self.h = y + 18
        self.configure(height=self.h)
        self.w = width
        self.card = None
        self.set_height(self.h)
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Return>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfigure(self.card, outline="#000000", width=2))
        # (set_height draws the card)
        self.bind("<Leave>", lambda e: self.itemconfigure(self.card, outline=C["line"], width=1))
        self.bind("<FocusIn>", lambda e: self.itemconfigure(self.card, outline="#000000", width=2))
        self.bind("<FocusOut>", lambda e: self.itemconfigure(self.card, outline=C["line"], width=1))


def _tile_set_height(self, h):
    self.h = h
    self.configure(height=h)
    if self.card:
        self.delete(self.card)
    self.card = icons.rounded_rect(self, 1, 1, self.w - 1, h - 1, 22, fill=C["panel"], outline=C["line"])
    self.tag_lower(self.card)


Tile.set_height = _tile_set_height


def tile_grid(parent, tiles_spec, columns, width, **kw):
    """Lay out Tile widgets in a grid. tiles_spec: [(title, subtitle, painter, command), ...]"""
    grid = tk.Frame(parent, bg=C["page"])
    grid.pack(fill="x", anchor="w")
    tiles = []
    for i, (title, sub, painter, cmd) in enumerate(tiles_spec):
        t = Tile(grid, title, sub, painter, cmd, width=width, **kw)
        t.grid(row=i // columns, column=i % columns, sticky="n", padx=(0, 16), pady=(0, 16))
        tiles.append(t)
    for r in range(0, len(tiles), columns):  # every card in a row gets the same height
        row = tiles[r:r + columns]
        tallest = max(t.h for t in row)
        for t in row:
            if t.h != tallest:
                t.set_height(tallest)
    return grid


class ProblemRow(RoundPanel):
    """One problem as a rounded card: urgency dot and pill, plain title, where it was found.
    Click to expand the details."""

    def __init__(self, parent, item, app):
        super().__init__(parent, pad=(20, 14), radius=16)
        self.item, self.app, self.open = item, app, False
        dot_color, pill_bg, pill_fg, words = LEVELS[item["level"]]
        self.body = self.inner
        top = tk.Frame(self.body, bg=C["panel"])
        top.pack(fill="x")
        dot = tk.Canvas(top, width=18, height=22, bg=C["panel"], highlightthickness=0)
        dot.surface = C["panel"]
        icons.glow(dot, 9, 11, 9, dot_color, steps=6, strength=0.5)
        dot.create_oval(5, 7, 13, 15, fill=dot_color, outline="")
        dot.pack(side="left", padx=(0, 10), anchor="n", pady=(2, 0))
        pill = tk.Canvas(top, bg=C["panel"], highlightthickness=0, height=26,
                         width=F(12, "bold").measure(words) + 24)
        icons.rounded_rect(pill, 1, 1, int(pill["width"]) - 1, 25, 13, fill=pill_bg, outline="")
        pill.create_text(int(pill["width"]) / 2, 13, text=words, fill=pill_fg, font=F(12, "bold"))
        pill.pack(side="right", anchor="n")
        self.title = tk.Label(top, text=item["info"]["description"], bg=C["panel"], fg=C["ink"],
                              font=F(15, "bold"), anchor="w", justify="left")
        self.title.pack(side="left", fill="x", expand=True)
        wrap_on_resize(self.title, 210)
        self.sub = tk.Label(self.body, text=f"{item['module']}, code {item['code']}. {item['status']}.",
                            bg=C["panel"], fg=C["muted"], font=F(12), anchor="w")
        self.sub.pack(fill="x", pady=(2, 0), padx=(28, 0))
        self.details = tk.Frame(self.body, bg=C["panel"])
        for w in (self, self.body, top, self.title, self.sub, dot, pill):
            w.bind("<Button-1>", lambda e: self.toggle())
            w.configure(cursor="hand2")

    def toggle(self):
        self.open = not self.open
        if self.open:
            self._fill_details()
            self.details.pack(fill="x", pady=(10, 2), padx=(28, 0))
        else:
            self.details.pack_forget()

    def _fill_details(self):
        for w in self.details.winfo_children():
            w.destroy()
        it, info = self.item, self.item["info"]
        parts = [("Why it matters", why_it_matters(it["code"], it["status"], it["module"])),
                 ("Common causes", info["causes"]),
                 ("How it failed", info["failure_type"].split(": ", 1)[-1] if info["failure_type"] else ""),
                 ("About this code", as_sentences(info["category"]))]
        for heading, text in parts:
            if not text:
                continue
            tk.Label(self.details, text=heading, bg=C["panel"], fg=C["ink"], font=F(13, "bold"),
                     anchor="w").pack(fill="x", pady=(6, 0))
            lbl = tk.Label(self.details, text=text, bg=C["panel"], fg=C["ink"], font=F(13), anchor="w",
                           justify="left")
            lbl.pack(fill="x")
            lbl.configure(wraplength=max(300, self.body.winfo_width() - 70))
        row = tk.Frame(self.details, bg=C["panel"])
        row.pack(fill="x", pady=(10, 0))
        PillButton(row, "Search for repair info", lambda: self.app.lookup_online(self.item["code"])).pack(side="left")


# ----------------------------------------------------------------------------
# The app
# ----------------------------------------------------------------------------
class App:
    PAGES = ["Home", "Problems", "Live data", "Smog check", "Vehicle", "Help"]

    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.geometry("1120x740")
        root.minsize(900, 600)
        root.configure(bg=C["page"])
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Lamp.Horizontal.TProgressbar", troughcolor=C["raised"], background="#000000",
                        bordercolor=C["page"], lightcolor="#000000", darkcolor="#000000", thickness=6)
        style.configure("Vertical.TScrollbar", background="#D6D6D6", troughcolor=C["page"], bordercolor=C["page"],
                        arrowcolor=C["muted"], lightcolor=C["raised"], darkcolor=C["raised"], gripcount=0)
        style.map("Vertical.TScrollbar", background=[("active", C["hover"])])
        for w in ("TEntry", "TCombobox"):
            style.configure(w, fieldbackground=C["raised"], foreground=C["ink"], background=C["raised"],
                            bordercolor=C["line"], lightcolor=C["raised"], darkcolor=C["raised"],
                            insertcolor=C["ink"], arrowcolor=C["muted"], padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", C["raised"]), ("disabled", C["panel"])],
                  foreground=[("disabled", C["muted"])])
        root.option_add("*TCombobox*Listbox.background", C["raised"])
        root.option_add("*TCombobox*Listbox.foreground", C["ink"])
        root.option_add("*TCombobox*Listbox.selectBackground", "#000000")
        root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
        self.elm = None
        self.q = queue.Queue()
        self.busy = False
        self.live_running = False
        self.live_stop = threading.Event()
        self.scan_stop = threading.Event()
        self.vehicle = {}
        self.items, self.modules, self.readiness, self.scanned = [], [], None, False
        self.mil_on = None
        self.chosen = None          # {"make", "model", "year", "kind", "family"} from the vehicle picker
        self.scan_kind = "all"      # "all", "engine" or "safety" (ABS and airbag)
        self.conn_kind = tk.StringVar(value=CONN_AUTO)
        self.port_var = tk.StringVar()
        self._icon = None
        icon = os.path.join(HERE, "icon.png")
        if os.path.exists(icon):
            try:
                self._icon = tk.PhotoImage(file=icon)
                root.iconphoto(True, self._icon)
            except tk.TclError:
                self._icon = None
        self._build()
        self.show_page("Home")
        self.refresh_problems()
        root.after(50, self._drain)
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.update_rel = None
        threading.Thread(target=lambda: self.ui(lambda r=updater.check(): self._update_found(r, quiet=True)),
                         daemon=True).start()

    # --- threading ---------------------------------------------------------------------
    def ui(self, fn):
        self.q.put(fn)

    def _drain(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        self.root.after(50, self._drain)

    def log(self, text):
        self.ui(lambda: self._append_log(text))

    def run_bg(self, work, done=None, step="Working…"):
        if self.busy:
            return
        self.busy = True
        self.set_step(step)
        self._update_controls()

        def wrap():
            try:
                result, err = work(), None
            except Exception as e:  # noqa: BLE001 - every failure is shown to the user
                result, err = None, e
            self.ui(lambda: self._finish(result, err, done))

        threading.Thread(target=wrap, daemon=True).start()

    def _finish(self, result, err, done):
        self.busy = False
        self.set_step("")
        self._update_controls()
        if err is not None:
            self._append_log(f"ERROR: {err}")
            self.refresh_problems()
            hint = ("\n\nIf the adapter was unplugged or the key was turned off, click Disconnect and connect "
                    "again." if self.elm else "")
            messagebox.showerror(APP_NAME, f"{err}{hint}")
        elif done:
            done(result)

    # --- layout --------------------------------------------------------------------------
    def _build(self):
        head = tk.Frame(self.root, bg=C["header"], padx=20, pady=14)
        head.pack(fill="x")

        if self._icon is not None:
            small = self._icon.subsample(max(1, self._icon.width() // 34))
            self._small_icon = small
            tk.Label(head, image=small, bg=C["header"]).pack(side="left", padx=(0, 10))
        tk.Label(head, text=APP_NAME, bg=C["header"], fg="#FFFFFF", font=F(17, "bold")).pack(side="left")
        self.disconnect_btn = PillButton(head, "Disconnect", self.disconnect, kind="onheader")
        self.vehicle_lbl = tk.Label(head, text="", bg=C["header"], fg="#FFFFFF", font=F(13, "bold"))
        self.vehicle_lbl.pack(side="right", padx=(0, 12))

        body = tk.Frame(self.root, bg=C["page"])
        body.pack(fill="both", expand=True)
        side = tk.Frame(body, bg=C["side"], width=200, pady=18)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Frame(body, bg=C["line"], width=1).pack(side="left", fill="y")
        self.nav = {}
        for name in self.PAGES:
            item = tk.Canvas(side, width=176, height=42, bg=C["side"], highlightthickness=0, cursor="hand2")
            item.pack(padx=12, pady=2, anchor="w")
            item.bind("<Button-1>", lambda e, n=name: self.show_page(n))
            item.bind("<Enter>", lambda e, n=name: self._nav_draw(n, hover=True))
            item.bind("<Leave>", lambda e, n=name: self._nav_draw(n))
            self.nav[name] = item

        self.main = tk.Frame(body, bg=C["page"], padx=34, pady=26)
        self.main.pack(side="left", fill="both", expand=True)
        self.pages = {
            "Home": self._build_home(),
            "Choose vehicle": self._build_picker(),
            "Problems": self._build_problems(),
            "Live data": self._build_live(),
            "Smog check": self._build_smog(),
            "Vehicle": self._build_vehicle(),
            "Help": self._build_help(),
        }

    def show_page(self, name):
        if name == "Home":
            self.refresh_home()
        self.nav_selected = "Home" if name == "Choose vehicle" else name
        for n in self.nav:
            self._nav_draw(n)
        for n, frame in self.pages.items():
            if n == name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self.current_page = name

    def _nav_draw(self, name, hover=False):
        cv = self.nav[name]
        cv.delete("all")
        sel = name == getattr(self, "nav_selected", "")
        if sel or hover:
            icons.rounded_rect(cv, 0, 1, 175, 41, 21, fill="#000000" if sel else C["hover"], outline="")
        cv.create_text(20, 21, text=name, anchor="w", fill="#FFFFFF" if sel else "#000000",
                       font=F(14, "bold" if sel else "normal"))

    def _page_title(self, parent, title, subtitle=""):
        tk.Label(parent, text=title, bg=C["page"], fg=C["ink"], font=F(22, "bold"), anchor="w").pack(fill="x")
        if subtitle:
            sub = tk.Label(parent, text=subtitle, bg=C["page"], fg=C["muted"], font=F(13), anchor="w",
                           justify="left")
            sub.pack(fill="x", pady=(2, 14))
            wrap_on_resize(sub, 20)
            return sub
        return None

    # --- Home page ---------------------------------------------------------------------------
    def _build_home(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "What do you want to check?")
        self.update_bar_card = RoundPanel(page, pad=(18, 12), fill=C["amber_soft"], outline=C["amber_soft"])
        self.update_bar = self.update_bar_card.inner
        self.home_vehicle = tk.Frame(page, bg=C["page"])
        self.home_vehicle.pack(fill="x", pady=(10, 18))
        s = 64
        tint = {"engine": "#E08A00", "safety": "#D9362B", "scan": "#6C4BD1", "gauge": "#0F8B8D",
                "smog": "#1E8A4A", "vehicle": "#1F6FD1"}

        def art(name, key):
            return lambda cv, x, y: icons.draw(cv, name, x, y, s, tint[key], F(int(s * 0.17), "bold"), halo=True)

        def both(cv, x, y):
            red = tint["safety"]
            cv.create_oval(x - s * 1.15, y - s * 0.72, x + s * 1.15, y + s * 0.72,
                           fill=icons.blend("#FFFFFF", red, 0.13), outline="")
            icons.draw(cv, "abs", x - s * 0.5, y, s * 0.85, red, F(int(s * 0.14), "bold"))
            icons.draw(cv, "airbag", x + s * 0.5, y, s * 0.85, red)

        tile_grid(page, [
            ("Engine codes", "Check-engine and transmission codes", art("engine", "engine"),
             lambda: self.start_scan("engine")),
            ("ABS and airbag", "Brake and airbag warning lights", both, lambda: self.start_scan("safety")),
            ("Full scan", "Everything at once", art("scan", "scan"), lambda: self.start_scan("all")),
            ("Live data", "Engine readings in real time", art("gauge", "gauge"), self.open_live),
            ("Smog check", "Ready for an emissions test?", art("smog", "smog"),
             lambda: self.show_page("Smog check")),
            ("Choose vehicle", "Make, model and year", art("vehicle", "vehicle"), self.open_picker),
        ], columns=3, width=236, art=100)
        return page

    def refresh_home(self):
        box = self.home_vehicle
        for w in box.winfo_children():
            w.destroy()
        ch = self.chosen
        if ch:
            cv = tk.Canvas(box, width=70, height=70, bg=C["page"], highlightthickness=0)
            cv.pack(side="left", padx=(0, 14))
            letters = vehicles.MAKES[ch["make"]][0]
            icons.make_badge(cv, letters, 35, 35, 56, "#1E1E1E",
                             F(16 if len(letters) < 3 else 13, "bold"))
            txt = tk.Frame(box, bg=C["page"])
            txt.pack(side="left")
            tk.Label(txt, text=f"{ch['year']} {ch['make']} {ch['model']}", bg=C["page"], fg=C["ink"],
                     font=F(17, "bold"), anchor="w").pack(fill="x")
            row = tk.Frame(txt, bg=C["page"])
            row.pack(fill="x")
            tk.Label(row, text=vehicles.support_text(ch["make"]) + ".", bg=C["page"], fg=C["muted"],
                     font=F(13)).pack(side="left")
            LinkLabel(row, "Change", self.open_picker).pack(side="left", padx=10)
        else:
            tk.Label(box, text="Pick your vehicle first if you like. It helps older vehicles that don't report "
                               "their make, and the app reads codes either way.", bg=C["page"], fg=C["muted"],
                     font=F(13), anchor="w", justify="left", wraplength=640).pack(side="left")
            LinkLabel(box, "Choose vehicle", self.open_picker).pack(side="left", padx=10)

    def open_live(self):
        self.show_page("Live data")
        if self.elm and not self.live_running and not self.busy:
            self.toggle_live()

    def start_scan(self, kind):
        """Home-screen tiles: connect first if needed, then run that kind of scan."""
        self.scan_kind = kind
        self.show_page("Problems")
        if self.elm:
            self.scan(kind=kind)
        elif not self.busy:
            self.connect()

    # --- Updates ----------------------------------------------------------------------------
    def _update_found(self, rel, quiet=False):
        self.update_rel = rel
        bar = self.update_bar
        for w in bar.winfo_children():
            w.destroy()
        if not rel:
            self.update_bar_card.pack_forget()
            if not quiet:
                self.update_status.configure(text=f"You have the latest version ({VERSION}).")
            return
        notes = (rel.get("notes") or "").strip()
        tk.Label(bar, text=f"Version {rel['version']} is ready to install.", bg=C["amber_soft"], fg=C["ink"],
                 font=F(14, "bold"), anchor="w").pack(side="left")
        if notes:
            tk.Label(bar, text=notes, bg=C["amber_soft"], fg=C["ink"], font=F(13), anchor="w",
                     wraplength=420, justify="left").pack(side="left", padx=(10, 0))
        PillButton(bar, "Update now", self.install_update, kind="primary").pack(side="right")
        self.update_bar_card.pack(fill="x", pady=(8, 0), before=self.home_vehicle)
        if hasattr(self, "update_status"):
            self.update_status.configure(text=f"Version {rel['version']} is available. Use Update now on Home.")

    def check_updates(self):
        self.update_status.configure(text="Checking…")
        threading.Thread(target=lambda: self.ui(lambda r=updater.check(): self._update_found(r)),
                         daemon=True).start()

    def install_update(self):
        rel = self.update_rel
        if not rel or self.busy:
            return
        if self.live_running:
            self.live_stop.set()

        def work():
            def progress(i, n, name):
                self.ui(lambda: self.set_step(f"Downloading update ({i + 1} of {n})…", (i + 1) / n))
            updater.install(rel, progress)
            return rel["version"]

        def done(version):
            messagebox.showinfo(APP_NAME, f"Updated to version {version}. The app will restart now.")
            if self.elm:
                self.elm.close()
            self.root.destroy()
            updater.restart()

        self.show_page("Problems")
        self.run_bg(work, done, "Downloading update…")

    # --- Vehicle picker -----------------------------------------------------------------------
    def _build_picker(self):
        page = tk.Frame(self.main, bg=C["page"])
        top = tk.Frame(page, bg=C["page"])
        top.pack(fill="x")
        self.pick_back = LinkLabel(top, "Back", self._pick_back)
        self.pick_back.pack(side="left")
        self.pick_title = tk.Label(page, text="", bg=C["page"], fg=C["ink"], font=F(22, "bold"), anchor="w")
        self.pick_title.pack(fill="x", pady=(6, 0))
        self.pick_trail = tk.Label(page, text="", bg=C["page"], fg=C["muted"], font=F(13), anchor="w",
                                   justify="left")
        self.pick_trail.pack(fill="x")
        wrap_on_resize(self.pick_trail, 20)
        bar = tk.Frame(page, bg=C["page"])
        bar.pack(fill="x", pady=(10, 12))
        tk.Label(bar, text="Search", bg=C["page"], fg=C["ink"], font=F(13)).pack(side="left")
        self.pick_search = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.pick_search, width=28, font=F(13))
        entry.pack(side="left", padx=8)
        self.pick_search.trace_add("write", lambda *a: self._pick_fill())
        self.pick_area = ScrollArea(page, C["page"])
        self.pick_area.pack(fill="both", expand=True)
        self.pick_step, self.pick_make, self.pick_model = "make", None, None
        return page

    def open_picker(self):
        self.pick_step, self.pick_make, self.pick_model = "make", None, None
        self.show_page("Choose vehicle")
        self.pick_search.set("")
        self._pick_fill()

    def _pick_back(self):
        if self.pick_step == "year":
            self.pick_step = "model"
        elif self.pick_step == "model":
            self.pick_step = "make"
        else:
            self.show_page("Home")
            return
        self.pick_search.set("")
        self._pick_fill()

    def _pick_fill(self):
        self.pick_area.clear()
        inner = self.pick_area.inner
        q = self.pick_search.get().strip().lower()
        step = self.pick_step
        if step == "make":
            self.pick_title.configure(text="Choose the make")
            self.pick_trail.configure(text="Ford and GM brands get engine, ABS and airbag. Every other make gets "
                                           "engine codes, and ABS and airbag on many newer models.")
            spec = []
            for make in sorted(vehicles.MAKES, key=lambda m: (vehicles.family_of(m) not in ("Ford", "GM"), m)):
                if q and q not in make.lower():
                    continue
                letters = vehicles.MAKES[make][0]

                def painter(cv, x, y, mk=make, lt=letters):
                    icons.make_badge(cv, lt, x, y, 64, "#1E1E1E", F(17 if len(lt) < 3 else 14, "bold"))
                spec.append((make, vehicles.support_text(make), painter, lambda mk=make: self._pick_set_make(mk)))
            tile_grid(inner, spec, columns=5, width=150, art=70, title_size=14)
        elif step == "model":
            make = self.pick_make
            self.pick_title.configure(text=f"Choose the {make} model")
            self.pick_trail.configure(text=make)
            spec = []
            for model, kind in vehicles.MAKES[make][2]:
                if q and q not in model.lower():
                    continue
                body = {"t": "truck", "s": "suv", "c": "car", "v": "van"}[kind]
                spec.append((model, "", lambda cv, x, y, b=body: icons.draw(cv, b, x, y, 62, C["steel"]),
                             lambda m=model, k=kind: self._pick_set_model(m, k)))
            spec.append(("Other model", "Not in the list", lambda cv, x, y: icons.draw(
                cv, "car", x, y, 62, C["off"]), lambda: self._pick_set_model("", "c")))
            tile_grid(inner, spec, columns=5, width=150, art=56, title_size=14)
        else:
            self.pick_title.configure(text="Choose the year")
            self.pick_trail.configure(text=f"{self.pick_make} {self.pick_model}".strip())
            grid = tk.Frame(inner, bg=C["page"])
            grid.pack(fill="x", anchor="w")
            ys = [y for y in vehicles.years() if not q or q in str(y)]
            for i, y in enumerate(ys):
                b = PillButton(grid, str(y), lambda yr=y: self._pick_set_year(yr), big=True)
                b.grid(row=i // 7, column=i % 7, padx=(0, 10), pady=(0, 10), sticky="w")
            tk.Label(inner, text="1995 and older vehicles mostly use OBD-I, which this kind of adapter can't read.",
                     bg=C["page"], fg=C["muted"], font=F(12), anchor="w").pack(fill="x", pady=(8, 0))

    def _pick_set_make(self, make):
        self.pick_make, self.pick_step = make, "model"
        self.pick_search.set("")
        self._pick_fill()

    def _pick_set_model(self, model, kind):
        self.pick_model, self.pick_kind, self.pick_step = model, kind, "year"
        self.pick_search.set("")
        self._pick_fill()

    def _pick_set_year(self, year):
        make = self.pick_make
        self.chosen = {"make": make, "model": self.pick_model, "year": year, "kind": self.pick_kind,
                       "family": vehicles.family_of(make)}
        self._apply_chosen()
        self.show_page("Home")

    def _apply_chosen(self):
        """Use the picked vehicle wherever the vehicle itself didn't tell us (old ones often don't)."""
        ch = self.chosen
        if not ch:
            return
        if self.elm and not make_from_vin(getattr(self, "_vin", "")):
            self.elm.make = ch["family"]
        name = f"{ch['year']} {ch['make']} {ch['model']}".strip()
        self.vehicle_lbl.configure(text=name)
        if self.vehicle:
            if self.vehicle.get("year", "-") == "-":
                self.vehicle["year"] = str(ch["year"])
            self.vehicle["title"] = name
            self.vehicle["make"] = self.vehicle.get("make") if self.vehicle.get("make", "-") != "-" else ch["make"]
            self._show_info(self.vehicle)
        self.refresh_smog()

    # --- Problems page ----------------------------------------------------------------------
    def _build_problems(self):
        page = tk.Frame(self.main, bg=C["page"])
        hero = tk.Frame(page, bg=C["page"])
        hero.pack(fill="x")
        self.lamp = Lamp(hero)
        self.lamp.pack(side="left", padx=(0, 22))
        text = tk.Frame(hero, bg=C["page"])
        text.pack(side="left", fill="both", expand=True)
        self.headline = tk.Label(text, text="", bg=C["page"], fg=C["ink"], font=F(28, "bold"), anchor="w",
                                 justify="left")
        self.headline.pack(fill="x", pady=(10, 2))
        self.subline = tk.Label(text, text="", bg=C["page"], fg=C["muted"], font=F(14), anchor="w",
                                justify="left")
        self.subline.pack(fill="x")
        wrap_on_resize(self.subline, 10)
        self.actions = tk.Frame(text, bg=C["page"])
        self.actions.pack(fill="x", pady=(14, 0))
        self.scan_btn = PillButton(self.actions, "Scan for problems", self.scan, kind="primary", big=True)
        self.clear_btn = PillButton(self.actions, "Clear codes", self.clear_codes, kind="danger", big=True)
        self.report_btn = PillButton(self.actions, "Save report", self.save_report, big=True)
        self.stop_btn = PillButton(self.actions, "Stop", self.scan_stop.set, big=True)
        self.connect_btn = PillButton(self.actions, "Connect", lambda: self.connect(), kind="primary", big=True)

        prog = tk.Frame(page, bg=C["page"])
        prog.pack(fill="x", pady=(16, 0))
        self.progress = ttk.Progressbar(prog, mode="determinate", style="Lamp.Horizontal.TProgressbar")
        self.step_lbl = tk.Label(prog, text="", bg=C["page"], fg=C["muted"], font=F(12), anchor="w")
        self.step_lbl.pack(fill="x")

        self.list = ScrollArea(page, C["page"])
        self.list.pack(fill="both", expand=True, pady=(8, 0))
        return page

    def set_step(self, text, fraction=None):
        self.step_lbl.configure(text=text)
        if fraction is None:
            self.progress.pack_forget()
        else:
            if not self.progress.winfo_ismapped():
                self.progress.pack(fill="x", before=self.step_lbl, pady=(0, 4))
            self.progress.configure(maximum=1.0, value=fraction)

    def refresh_problems(self):
        """Redraw the lamp, headline, buttons and list from the current state."""
        for b in (self.scan_btn, self.clear_btn, self.report_btn, self.stop_btn, self.connect_btn):
            b.pack_forget()
        self.list.clear()
        inner = self.list.inner
        if not self.elm:
            self.lamp.set("busy" if self.busy else "off")
            self.headline.configure(text="Let's check your vehicle")
            self.subline.configure(text="Plug the adapter into the port under the dashboard, near the steering "
                                        "column. Turn the key to ON. The engine can be off or running.")
            self.connect_btn.pack(side="left")
            self._connect_panel(inner)
            self._update_controls()
            return
        self.scan_btn.pack(side="left")
        if self.scanned and self.items:
            self.clear_btn.pack(side="left", padx=(10, 0))
        if self.scanned:
            self.report_btn.pack(side="left", padx=(10, 0))
        what = {"engine": "Engine codes: ", "safety": "ABS and airbag: "}.get(self.scan_kind, "")
        self.scan_btn.set_text({"engine": "Scan engine again", "safety": "Scan ABS and airbag again"}.get(
            self.scan_kind, "Scan for problems"))
        if not self.scanned:
            self.lamp.set("busy" if self.busy else "off")
            self.headline.configure(text="Ready to scan")
            self.subline.configure(text="Scanning checks the engine and transmission, plus ABS, airbag and other "
                                        "modules the vehicle lets us reach. It takes about half a minute.")
        else:
            active = [i for i in self.items if i["level"] != "past"]
            high = [i for i in active if i["level"] == "high"]
            if self.scan_kind == "safety" and not self.modules:
                self.lamp.set("off")
                self.headline.configure(text="ABS and airbag modules didn't answer")
            elif not self.items:
                self.lamp.set("ok")
                self.headline.configure(text=what + "no problems found" if what else "No problems found")
            else:
                self.lamp.set("bad" if high else "warn" if active else "ok")
                n = len(active)
                head = f"{n} problem{'s' if n != 1 else ''} found" if n else "No active problems"
                self.headline.configure(text=what + head.lower() if what else head)
            light = ""
            if self.scan_kind == "safety" and not self.modules:
                light = ("This vehicle didn't let us reach its ABS or airbag module. Try a deep scan below, or "
                         "pick the vehicle on the Home page so the app knows where to look. ")
            elif self.mil_on is not None and self.scan_kind != "safety":
                light = "The check-engine light is on. " if self.mil_on else "The check-engine light is off. "
            past = len(self.items) - len([i for i in self.items if i["level"] != "past"])
            extra = f"{past} past problem{'s' if past != 1 else ''} also listed. " if past else ""
            self.subline.configure(text=light + extra + ("Click a problem for what it means and what usually "
                                                         "fixes it." if self.items else ""))
        for item in self.items:
            ProblemRow(inner, item, self).pack(fill="x", pady=(0, 10))
        if self.scanned and self.scan_kind != "engine":
            self._modules_note(inner)
        self._update_controls()

    def _connect_panel(self, parent):
        card = RoundPanel(parent, pad=(24, 18))
        card.pack(fill="x", pady=(6, 0))
        box = card.inner
        tk.Label(box, text="No adapter yet?", bg=C["panel"], fg=C["ink"], font=F(15, "bold"),
                 anchor="w").pack(fill="x")
        row = tk.Frame(box, bg=C["panel"])
        row.pack(fill="x", pady=(4, 0))
        tk.Label(row, text="Try everything with a pretend vehicle:", bg=C["panel"], fg=C["muted"],
                 font=F(13)).pack(side="left")
        LinkLabel(row, "2012 Ford", lambda: self.connect(CONN_DEMO)).pack(side="left", padx=(8, 0))
        tk.Label(row, text="or", bg=C["panel"], fg=C["muted"], font=F(13)).pack(side="left", padx=6)
        LinkLabel(row, "2004 GM truck", lambda: self.connect(CONN_DEMO_OLD)).pack(side="left")

        opts = tk.Frame(parent, bg=C["page"])
        opts.pack(fill="x", pady=(14, 0))
        self.opts_body = tk.Frame(opts, bg=C["page"])
        self.opts_link = LinkLabel(opts, "Connection options", self._toggle_options)
        self.opts_link.pack(anchor="w")
        tk.Label(self.opts_body, text="How the adapter connects", bg=C["page"], fg=C["ink"],
                 font=F(13, "bold")).grid(row=0, column=0, sticky="w", pady=(8, 2))
        kinds = ttk.Combobox(self.opts_body, textvariable=self.conn_kind, state="readonly", width=34,
                             values=[CONN_AUTO, CONN_SERIAL, CONN_WIFI, CONN_DEMO, CONN_DEMO_OLD])
        kinds.grid(row=1, column=0, sticky="w")
        kinds.bind("<<ComboboxSelected>>", lambda e: self._fill_ports())
        tk.Label(self.opts_body, text="Port or address", bg=C["page"], fg=C["ink"],
                 font=F(13, "bold")).grid(row=2, column=0, sticky="w", pady=(10, 2))
        self.port_box = ttk.Combobox(self.opts_body, textvariable=self.port_var, width=44)
        self.port_box.grid(row=3, column=0, sticky="w")
        PillButton(self.opts_body, "Refresh", self._fill_ports).grid(row=3, column=1, padx=8)
        tk.Label(self.opts_body, justify="left", bg=C["page"], fg=C["muted"], font=F(12), text=(
            "USB adapters show up as something like /dev/cu.usbserial-… on a Mac or COM3 on Windows.\n"
            "Pair Bluetooth adapters in your computer's settings first (PIN 1234 or 0000).\n"
            "For Wi-Fi adapters, join the adapter's Wi-Fi network first.")).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._fill_ports()

    def _toggle_options(self):
        if self.opts_body.winfo_ismapped():
            self.opts_body.pack_forget()
        else:
            self.opts_body.pack(fill="x", anchor="w")

    def _fill_ports(self):
        kind = self.conn_kind.get()
        if kind == CONN_WIFI:
            self.port_box.configure(values=["192.168.0.10:35000"], state="normal")
            self.port_var.set("192.168.0.10:35000")
        elif kind in (CONN_SERIAL, CONN_AUTO):
            ports = [f"{d} — {desc}" for d, desc in list_ports()]
            self.port_box.configure(values=ports, state="normal" if kind == CONN_SERIAL else "disabled")
            if kind == CONN_AUTO:
                self.port_var.set(f"{len(ports)} port(s) found - all will be tried" if ports else
                                  "No USB or Bluetooth ports found - Wi-Fi will be tried")
            elif self.port_var.get() not in ports:
                self.port_var.set(ports[0] if ports else "")
        else:
            self.port_box.configure(values=[], state="disabled")
            self.port_var.set("Pretend vehicle - nothing to choose")

    def _modules_note(self, parent):
        names = []
        for m in self.modules:
            n = friendly_module(m["name"] + (" (second network)" if m.get("bus") == MS else ""))
            if n not in names:
                names.append(n)
        box = tk.Frame(parent, bg=C["page"])
        box.pack(fill="x", pady=(14, 0))
        if names:
            text = "Modules that answered: " + ", ".join(names) + "."
        elif self.elm and self.elm.can_scan_modules:
            text = "Only the engine computer answered. Some vehicles hide other modules."
        else:
            text = ("This vehicle's protocol only lets us read engine and transmission codes "
                    f"({self.elm.protocol_name if self.elm else 'unknown'}).")
        lbl = tk.Label(box, text=text, bg=C["page"], fg=C["muted"], font=F(12), anchor="w", justify="left")
        lbl.pack(fill="x")
        wrap_on_resize(lbl, 10)
        if self.elm and self.elm.can_scan_modules:
            row = tk.Frame(box, bg=C["page"])
            row.pack(fill="x", pady=(4, 0))
            tk.Label(row, text="Missing a module, like ABS or airbag?", bg=C["page"], fg=C["muted"],
                     font=F(12)).pack(side="left")
            LinkLabel(row, "Run a deep scan", lambda: self.scan(deep=True), size=12).pack(side="left", padx=6)
            tk.Label(row, text="(checks every address, 1 to 3 minutes)", bg=C["page"], fg=C["muted"],
                     font=F(12)).pack(side="left")

    def _update_controls(self):
        idle = bool(self.elm) and not self.busy
        self.connect_btn.set_enabled(not self.busy)
        for b in (self.scan_btn, self.clear_btn, self.report_btn):
            b.set_enabled(idle)
        self.stop_btn.set_enabled(self.busy and getattr(self, "_scanning", False))
        if getattr(self, "_scanning", False) and self.busy:
            if not self.stop_btn.winfo_ismapped():
                self.stop_btn.pack(side="left", padx=(10, 0))
        else:
            self.stop_btn.pack_forget()
        if self.elm:
            if not self.disconnect_btn.winfo_ismapped():
                self.disconnect_btn.pack(side="right", before=self.vehicle_lbl)
        else:
            self.disconnect_btn.pack_forget()
        self.disconnect_btn.set_enabled(not self.busy or self.live_running)
        for b in getattr(self, "page_buttons", []):
            b.set_enabled(idle)
        if hasattr(self, "live_btn"):
            self.live_btn.set_enabled(self.live_running or idle)
            self.live_btn.set_text("Stop" if self.live_running else "Start live data")

    # --- connect -----------------------------------------------------------------------------
    def connect(self, kind=None):
        kind = kind or self.conn_kind.get()
        target = self.port_var.get().strip()

        def work():
            if kind == CONN_AUTO:
                elm, tried = None, []
                for device, _desc in list_ports():
                    self.ui(lambda d=device: self.set_step(f"Looking for the adapter on {d}…"))
                    try:
                        elm = open_adapter(CONN_SERIAL, device, self.log)
                        break
                    except Exception as e:  # noqa: BLE001
                        tried.append(f"{device}: {e}".split("\n")[0])
                if elm is None:
                    self.ui(lambda: self.set_step("Looking for a Wi-Fi adapter…"))
                    try:
                        elm = open_adapter(CONN_WIFI, "192.168.0.10:35000", self.log)
                    except Exception:  # noqa: BLE001
                        raise ConnectionError(
                            "Couldn't find an OBD adapter.\n\n"
                            "• USB: check the cable is plugged into the computer.\n"
                            "• Bluetooth: pair the adapter in your computer's Bluetooth settings first.\n"
                            "• Wi-Fi: join the adapter's Wi-Fi network first.\n\n"
                            "Then click Connect again, or pick the port yourself under Connection options.")
            else:
                elm = open_adapter(kind, target, self.log)
            self.ui(lambda: self.set_step("Talking to the vehicle… (finding its language can take 20 seconds)"))
            try:
                elm.initialize()
                info = self._gather_info(elm)
            except Exception:
                elm.close()
                raise
            return elm, info

        def done(res):
            self.elm, info = res
            self._show_info(info)
            self._apply_chosen()
            self.scanned, self.items, self.modules = False, [], []
            self.refresh_problems()
            self.scan(kind=self.scan_kind)  # straight into the scan that was asked for

        self.lamp.set("busy")
        if getattr(self, "current_page", "") in ("Home", "Choose vehicle"):
            self.show_page("Problems")
        self.run_bg(work, done, "Looking for the adapter…")

    def disconnect(self):
        self.live_stop.set()
        self.scan_stop.set()
        if self.elm:
            self.elm.close()
        self.elm = None
        self.vehicle, self.items, self.modules, self.readiness, self.scanned = {}, [], [], None, False
        self.vehicle_lbl.configure(text="")
        self._show_info({})
        self.refresh_problems()
        self.refresh_smog()

    def _gather_info(self, elm):
        vin = elm.read_vin()
        self._vin = vin
        make = make_from_vin(vin)
        elm.make = make
        year = year_from_vin(vin)
        return {
            "title": " ".join(str(x) for x in (year, make) if x) or "Your vehicle",
            "vin": vin or "Not reported (common on older vehicles)",
            "make": make or "-",
            "year": str(year) if year else "-",
            "voltage": elm.voltage(),
            "protocol": elm.protocol_name or "-",
            "adapter": elm.version,
            "ecus": ", ".join(ECU_NAMES.get(e, e) for e in elm.ecus) or "-",
        }

    # --- scan / clear ------------------------------------------------------------------------
    def scan(self, deep=False, kind=None):
        if not self.elm:
            return
        elm = self.elm
        kind = kind or self.scan_kind
        self.scan_kind = kind
        self.scan_stop.clear()
        self._scanning = True

        def work():
            obd, ready, modules = [], None, []
            if kind in ("all", "engine"):
                self.ui(lambda: self.set_step("Reading engine and transmission codes…", 0.05))
                for mode, label in (("03", "Stored"), ("07", "Pending"), ("0A", "Permanent")):
                    for ecu, code in elm.read_dtcs(mode):
                        obd.append((code, ECU_NAMES.get(ecu, f"Module {ecu}"), label))
                self.ui(lambda: self.set_step("Checking the check-engine light and smog tests…", 0.12))
                ready = elm.query_pid(1, 1)
            if kind in ("all", "safety") and elm.can_scan_modules:
                targets = elm.module_targets(deep)
                if kind == "safety":
                    targets = [t for t in targets if is_safety_module(t[1])] or targets

                def progress(i, n, name):
                    self.ui(lambda: self.set_step(f"Checking {name}…", 0.15 + 0.85 * (i + 1) / n))
                modules = elm.module_scan(targets, progress, self.scan_stop)
            return obd, ready, modules

        def done(res):
            self._scanning = False
            obd, ready, modules = res
            if kind == "safety":
                modules = [m for m in modules if is_safety_module(m["name"])]
            self._apply_scan(obd, ready, modules)

        self.lamp.set("busy")
        self.run_bg(work, done, "Starting the scan…")

    def _apply_scan(self, obd, ready, modules):
        merged, seen = {}, set()

        def add(code, module, status, resp=""):
            key = (code.split("-")[0], module)
            if key in merged:  # same code from the same module (e.g. stored + permanent): one row
                it = merged[key]
                if status not in it["status"]:
                    it["status"] += f", {status.lower()}"
                    it["level"] = min(it["level"], severity(code, status, module), key=LEVEL_ORDER.get)
            else:
                merged[key] = self._item(code, module, status, resp)

        for code, module, status in obd:
            add(code, friendly_module(module), status)
            seen.add(code)
        for m in modules:
            for code, st in m["dtcs"]:
                status = st if isinstance(st, str) else uds_status_text(st)
                if code.split("-")[0] in seen and code.startswith("P"):
                    continue  # already listed from the engine computer
                add(code, friendly_module(m["name"] + (" (second network)" if m.get("bus") == MS else "")),
                    status, m.get("resp", ""))
        items = sorted(merged.values(), key=lambda i: LEVEL_ORDER[i["level"]])
        self.items, self.modules, self.scanned = items, modules, True
        if self.scan_kind != "safety":
            self.readiness = ready
            self.mil_on = bool(ready[0] & 0x80) if ready else None
        self.refresh_problems()
        self.refresh_smog()
        hook, self._after_scan_hook = getattr(self, "_after_scan_hook", None), None
        if hook:
            hook()

    @staticmethod
    def _item(code, module, status, resp=""):
        return {"code": code, "module": module, "status": status, "resp": resp,
                "info": describe_dtc(code), "level": severity(code, status, module)}

    def clear_codes(self):
        if not messagebox.askyesno(APP_NAME, (
                "Clear all codes and turn off the warning lights?\n\n"
                "• Turn the engine OFF and leave the key ON first.\n"
                "• This also resets the smog-check self-tests. The vehicle will fail an emissions test "
                "until it's driven for a few days.\n"
                "• If a problem isn't fixed, its code and light will come back."), icon="warning"):
            return
        elm = self.elm
        before = {i["code"] for i in self.items if i["level"] != "past"}
        targets = [(m["target"], m["name"], m.get("bus", "hs")) for m in self.modules if m["dtcs"]]
        self._scanning = False

        def work():
            self.ui(lambda: self.set_step("Clearing engine codes…", 0.2))
            elm.clear_obd()
            if targets:
                self.ui(lambda: self.set_step("Clearing module codes…", 0.5))
                elm.module_clear(targets)
            time.sleep(1)
            return True

        def done(_):
            def after_rescan():
                still = {i["code"] for i in self.items if i["level"] != "past"} & before
                if still:
                    self.subline.configure(text=f"Codes cleared, but {len(still)} came straight back. That "
                                                "problem is still there and needs fixing.")
                else:
                    self.subline.configure(text="Codes cleared. If a problem returns after some driving, "
                                                "it still needs fixing.")
            self._after_scan_hook = after_rescan
            self.scan()

        self.run_bg(work, done, "Clearing codes…")

    # --- Live data page ----------------------------------------------------------------------
    def _build_live(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "Live data", "What the engine computer sees right now. Values update about "
                                            "once a second.")
        bar = tk.Frame(page, bg=C["page"])
        bar.pack(fill="x")
        self.live_btn = PillButton(bar, "Start live data", self.toggle_live, kind="primary")
        self.live_btn.pack(side="left")
        self.freeze_btn = PillButton(bar, "Show freeze frame", self.read_freeze_frame)
        self.freeze_btn.pack(side="left", padx=10)
        self.page_buttons = [self.freeze_btn]
        self.tiles_area = ScrollArea(page, C["page"])
        self.tiles_area.pack(fill="both", expand=True, pady=(16, 0))
        self.tiles = {}
        self._live_empty()
        return page

    def _live_empty(self):
        self.tiles_area.clear()
        tk.Label(self.tiles_area.inner, text="Connect to the vehicle, then click Start live data.",
                 bg=C["page"], fg=C["muted"], font=F(13), anchor="w").pack(fill="x")

    def _make_tiles(self, pids):
        self.tiles_area.clear()
        grid = tk.Frame(self.tiles_area.inner, bg=C["page"])
        grid.pack(fill="x")
        self.tiles = {}
        for i, pid in enumerate(pids):
            card = RoundPanel(grid, pad=(18, 14), radius=18)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=(0, 12), pady=(0, 12))
            tile = card.inner
            value = tk.Label(tile, text="…", bg=C["panel"], fg=C["ink"], font=F(24, "bold"), anchor="w")
            value.pack(fill="x")
            alt = tk.Label(tile, text="", bg=C["panel"], fg=C["muted"], font=F(12), anchor="w")
            alt.pack(fill="x")
            tk.Label(tile, text=PIDS[pid][0], bg=C["panel"], fg=C["ink"], font=F(13), anchor="w", justify="left",
                     wraplength=220).pack(fill="x")
            self.tiles[pid] = (value, alt)
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1, uniform="tiles")

    def _set_tile(self, pid, text):
        if pid not in self.tiles:
            return
        main, _, alt = text.partition("(")
        self.tiles[pid][0].configure(text=main.strip())
        self.tiles[pid][1].configure(text=alt.rstrip(")").strip())

    def toggle_live(self):
        if self.live_running:
            self.live_stop.set()
            return
        if not self.elm:
            return
        elm = self.elm
        self.live_stop.clear()
        self.live_running = True
        self.busy = True
        self._update_controls()

        def worker():
            try:
                sup = elm.supported_pids()
                pids = [p for p in PIDS if p in sup] or [0x0C, 0x0D, 0x05]
                self.ui(lambda: self._make_tiles(pids))
                while not self.live_stop.is_set():
                    for pid in pids:
                        if self.live_stop.is_set():
                            break
                        d = elm.query_pid(1, pid)
                        if d is not None:
                            txt = format_pid(pid, d)
                            self.ui(lambda p=pid, t=txt: self._set_tile(p, t))
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                self.ui(lambda: messagebox.showerror(APP_NAME, f"Live data stopped: {msg}"))
            finally:
                self.ui(self._live_ended)

        threading.Thread(target=worker, daemon=True).start()

    def _live_ended(self):
        self.live_running = False
        self.busy = False
        self._update_controls()

    def read_freeze_frame(self):
        elm = self.elm

        def work():
            first = elm.query_pid(2, 2, b"\x00")
            if not first or first[:2] == b"\x00\x00":
                return None
            rows = [("Code that saved this snapshot", decode_dtc_bytes(first[0], first[1]))]
            for pid in PIDS:
                d = elm.query_pid(2, pid, b"\x00")
                if d:
                    rows.append((PIDS[pid][0], format_pid(pid, d)))
            return rows

        def done(rows):
            card = RoundPanel(self.tiles_area.inner, pad=(22, 16))
            card.pack(fill="x", pady=(14, 0))
            box = card.inner
            tk.Label(box, text="Freeze frame", bg=C["panel"], fg=C["ink"], font=F(15, "bold"),
                     anchor="w").grid(row=0, column=0, columnspan=2, sticky="w")
            if not rows:
                tk.Label(box, text="No snapshot stored. One is saved when the check-engine light comes on.",
                         bg=C["panel"], fg=C["muted"], font=F(13)).grid(row=1, column=0, sticky="w", pady=(4, 0))
                return
            tk.Label(box, text="A snapshot of the engine at the moment the check-engine light came on.",
                     bg=C["panel"], fg=C["muted"], font=F(12)).grid(row=1, column=0, columnspan=2, sticky="w")
            for i, (name, value) in enumerate(rows):
                tk.Label(box, text=name, bg=C["panel"], fg=C["ink"], font=F(13), anchor="w").grid(
                    row=i + 2, column=0, sticky="w", pady=2)
                tk.Label(box, text=value, bg=C["panel"], fg=C["ink"], font=F(13, "bold"), anchor="w").grid(
                    row=i + 2, column=1, sticky="w", padx=(24, 0))
            self.tiles_area.scroll_to(card)

        self.run_bg(work, done, "Reading the freeze frame…")

    # --- Smog check page -----------------------------------------------------------------------
    def _build_smog(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "Smog check", "Before an emissions inspection, the vehicle has to finish its own "
                                             "self-tests. Here's where they stand.")
        bar = tk.Frame(page, bg=C["page"])
        bar.pack(fill="x")
        self.smog_btn = PillButton(bar, "Check again", self.check_readiness)
        self.smog_btn.pack(side="left")
        self.page_buttons.append(self.smog_btn)
        self.smog_area = ScrollArea(page, C["page"])
        self.smog_area.pack(fill="both", expand=True, pady=(16, 0))
        self.refresh_smog()
        return page

    def check_readiness(self):
        def done(d):
            self.readiness = d
            self.mil_on = bool(d[0] & 0x80) if d else self.mil_on
            self.refresh_smog()
        self.run_bg(lambda: self.elm.query_pid(1, 1), done, "Checking smog tests…")

    def refresh_smog(self):
        if not hasattr(self, "smog_area"):
            return
        self.smog_area.clear()
        inner = self.smog_area.inner
        d = self.readiness
        if not d or len(d) < 4:
            tk.Label(inner, text="Connect and scan to see whether the vehicle is ready for inspection.",
                     bg=C["page"], fg=C["muted"], font=F(13), anchor="w").pack(fill="x")
            return
        mil_on, count, diesel, rows = decode_readiness(d)
        year = self.vehicle.get("year", "-")
        allowed = 2 if year.isdigit() and int(year) <= 2000 else 1
        not_ready = [r for r in rows if r[1] and r[2]]
        if mil_on:
            verdict, color, why = ("Not ready: the check-engine light is on", C["red"],
                                   "Vehicles with the check-engine light on fail inspection. Fix the problem first.")
        elif len(not_ready) > allowed:
            verdict, color, why = (f"Not ready yet: {len(not_ready)} self-tests still running", C["amber_ink"],
                                   f"Most inspections allow {allowed} unfinished test{'s' if allowed > 1 else ''}. "
                                   "Drive normally for a few days, with some city and highway, then check again.")
        else:
            verdict, color, why = ("Ready for inspection", C["green"],
                                   "The check-engine light is off and enough self-tests have finished.")
        tk.Label(inner, text=verdict, bg=C["page"], fg=color, font=F(20, "bold"), anchor="w").pack(fill="x")
        w = tk.Label(inner, text=why, bg=C["page"], fg=C["ink"], font=F(13), anchor="w", justify="left")
        w.pack(fill="x", pady=(2, 14))
        wrap_on_resize(w, 20)
        card = RoundPanel(inner, pad=(4, 8))
        card.pack(fill="x")
        box = card.inner
        for i, (name, supported, incomplete) in enumerate(rows):
            if i:
                tk.Frame(box, bg=C["line"], height=1).pack(fill="x")
            row = tk.Frame(box, bg=C["panel"], padx=18, pady=9)
            row.pack(fill="x")
            name = {"Comprehensive components": "General sensors and parts",
                    "Misfire": "Misfire detection"}.get(name, name)
            tk.Label(row, text=name, bg=C["panel"], fg=C["ink"] if supported else C["muted"], font=F(14),
                     anchor="w").pack(side="left")
            if not supported:
                pill = ("Not on this vehicle", C["off_soft"], C["muted"])
            elif incomplete:
                pill = ("Still running", C["amber_soft"], C["amber_ink"])
            else:
                pill = ("Done", C["green_soft"], C["green"])
            tk.Label(row, text=pill[0], bg=pill[1], fg=pill[2], font=F(12, "bold"), padx=10, pady=3).pack(
                side="right")

    # --- Vehicle page ---------------------------------------------------------------------------
    def _build_vehicle(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "Vehicle", "What the vehicle and adapter report about themselves.")
        card = RoundPanel(page, pad=(24, 18))
        card.pack(fill="x")
        box = card.inner
        self.info_vars = {}
        fields = (("title", "Vehicle"), ("vin", "VIN"), ("voltage", "Battery"), ("protocol", "Language it speaks"),
                  ("ecus", "Computers answering"), ("adapter", "Adapter"))
        for i, (key, label) in enumerate(fields):
            tk.Label(box, text=label, bg=C["panel"], fg=C["muted"], font=F(13), anchor="w").grid(
                row=i, column=0, sticky="nw", pady=5)
            v = tk.StringVar(value="-")
            tk.Label(box, textvariable=v, bg=C["panel"], fg=C["ink"], font=F(14, "bold"), anchor="w",
                     justify="left", wraplength=560).grid(row=i, column=1, sticky="w", padx=(28, 0), pady=5)
            self.info_vars[key] = v
        bar = tk.Frame(page, bg=C["page"])
        bar.pack(fill="x", pady=(14, 0))
        self.info_btn = PillButton(bar, "Refresh", self.refresh_info)
        self.info_btn.pack(side="left")
        self.page_buttons.append(self.info_btn)
        return page

    def _show_info(self, info):
        self.vehicle = info
        volts = info.get("voltage", "")
        try:
            v = float(volts.rstrip("Vv"))
            note = (" (charging, engine running)" if v >= 13.4 else " (good)" if v >= 12.4 else
                    " (low, battery may be weak)")
            volts = f"{v:.1f} volts{note}"
        except ValueError:
            pass
        shown = dict(info, voltage=volts or "-")
        for k, var in self.info_vars.items():
            var.set(shown.get(k, "-"))
        self.vehicle_lbl.configure(text=info.get("title", ""))

    def refresh_info(self):
        self.run_bg(lambda: self._gather_info(self.elm), self._show_info, "Reading vehicle info…")

    # --- Help page --------------------------------------------------------------------------------
    def _build_help(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "Help")
        steps = [
            "Plug the adapter into the OBD port under the dashboard, near the steering column.",
            "Turn the key to ON. The engine can be off or running.",
            "On Home, click Engine codes, ABS and airbag, or Full scan. The app finds the adapter by itself.",
            "Click any problem to see what it means, how urgent it is, and what usually fixes it.",
            "To clear codes, turn the engine off and leave the key on first.",
        ]
        box = tk.Frame(page, bg=C["page"])
        box.pack(fill="x")
        for i, s in enumerate(steps, 1):
            tk.Label(box, text=f"{i}.", bg=C["page"], fg=C["ink"], font=F(14, "bold")).grid(
                row=i, column=0, sticky="nw", pady=3)
            tk.Label(box, text=s, bg=C["page"], fg=C["ink"], font=F(14), anchor="w", justify="left").grid(
                row=i, column=1, sticky="w", padx=(8, 0), pady=3)
        tips = tk.Label(page, bg=C["page"], fg=C["muted"], font=F(13), anchor="w", justify="left", text=(
            "Best adapter: OBDLink EX (USB). It reaches every OBD-II language plus Ford's second network.\n"
            "Something not working right? Open the adapter log below, copy it, and send it to whoever "
            "maintains this app."))
        tips.pack(fill="x", pady=(16, 10))
        wrap_on_resize(tips, 20)
        ver = tk.Frame(page, bg=C["page"])
        ver.pack(fill="x", pady=(0, 12))
        tk.Label(ver, text=f"Version {VERSION}", bg=C["page"], fg=C["ink"], font=F(13, "bold")).pack(side="left")
        if updater.base_url():
            LinkLabel(ver, "Check for updates", self.check_updates).pack(side="left", padx=12)
        self.update_status = tk.Label(ver, text="", bg=C["page"], fg=C["muted"], font=F(13))
        self.update_status.pack(side="left")
        bar = tk.Frame(page, bg=C["page"])
        bar.pack(fill="x")
        self.log_toggle = PillButton(bar, "Show adapter log", self._toggle_log)
        self.log_toggle.pack(side="left")
        PillButton(bar, "Copy log", self._copy_log).pack(side="left", padx=10)
        self.log_box = ScrolledText(page, height=14, font=("Menlo" if IS_MAC else "Courier", 11), relief="flat",
                                    highlightbackground=C["line"], highlightthickness=1, bg=C["panel"],
                                    fg=C["ink"], insertbackground=C["ink"])
        return page

    def _toggle_log(self):
        if self.log_box.winfo_ismapped():
            self.log_box.pack_forget()
            self.log_toggle.set_text("Show adapter log")
        else:
            self.log_box.pack(fill="both", expand=True, pady=(12, 0))
            self.log_toggle.set_text("Hide adapter log")

    def _copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_box.get("1.0", "end"))

    def _append_log(self, text):
        self.log_box.insert("end", text + "\n")
        if int(self.log_box.index("end-1c").split(".")[0]) > 4000:
            self.log_box.delete("1.0", "1000.0")
        self.log_box.see("end")

    # --- misc ------------------------------------------------------------------------------------
    def lookup_online(self, code):
        base = code.split("-")[0]
        make = self.vehicle.get("make", "")
        q = f"{base} {make} code" if make and make != "-" else f"{base} code meaning"
        webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(q))

    def save_report(self):
        today = datetime.date.today().isoformat()
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"vehicle-report-{today}.txt",
                                            filetypes=[("Text file", "*.txt")])
        if not path:
            return
        v = self.vehicle
        lines = [f"Vehicle report, {datetime.datetime.now():%B %d, %Y %I:%M %p}", "=" * 60,
                 f"Vehicle:  {v.get('title', '-')}", f"VIN:      {v.get('vin', '-')}",
                 f"Battery:  {v.get('voltage', '-')}", ""]
        if self.mil_on is not None:
            lines.append(f"Check-engine light: {'ON' if self.mil_on else 'off'}")
        lines += ["", "PROBLEMS", "-" * 60]
        if not self.items:
            lines.append("None found.")
        for it in self.items:
            lines += [f"[{LEVELS[it['level']][3]}] {it['code']}  {it['info']['description']}",
                      f"    Found in: {it['module']}   Status: {it['status']}",
                      f"    {why_it_matters(it['code'], it['status'], it['module'])}", ""]
        if self.modules:
            lines += ["Modules that answered: " + ", ".join(m["name"] for m in self.modules)]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        self.step_lbl.configure(text=f"Report saved to {path}")

    def _on_close(self):
        self.live_stop.set()
        self.scan_stop.set()
        if self.elm:
            self.elm.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
