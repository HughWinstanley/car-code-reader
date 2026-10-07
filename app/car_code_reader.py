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

from obd_core import (CONN_SERIAL, CONN_WIFI, CONN_DEMO, CONN_DEMO_OLD, CONN_DEMO_SEMI, ECU_NAMES, MS, PIDS,
                      EXTENDED, decode_readiness, format_pid, format_value, list_ports, make_from_vin, open_adapter, us_value,
                      year_from_vin)
from dtc_database import decode_dtc_bytes, describe_dtc, severity, uds_status_text, why_it_matters
import icons
import j1939
import advanced
import history
import maker_codes
import obd1
import recalls
import report
import service_guides
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
    "line": "#E2E2E2", "header": "#FFFFFF", "header_hover": "#F3F3F3", "side": "#FFFFFF", "hover": "#F3F3F3",
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

# How to get each smog-check self-test to run (general drive cycles; exact steps vary by vehicle).
DRIVE_CYCLES = {
    "Catalyst": "once fully warmed up, drive at a steady 40-55 mph for about 5 minutes.",
    "Heated catalyst": "once fully warmed up, drive at a steady 40-55 mph for about 5 minutes.",
    "Oxygen sensor": "after warming up, drive at a steady 30-45 mph for 2-3 minutes, then idle for 30 seconds.",
    "Oxygen sensor heater": "let the vehicle sit off for at least 8 hours, then start it and idle for 2 minutes.",
    "Evaporative system (EVAP)": "keep the tank between 1/4 and 3/4 full, park overnight, then start it cold and "
                                 "drive normally. This one can take several days.",
    "EGR system": "after warming up, make a few gentle slow-downs from 50 mph to 20 mph without braking hard.",
    "Secondary air system": "start the engine cold (after sitting overnight) and let it idle for 2 minutes.",
    "Misfire": "runs all the time while driving.",
    "Fuel system": "runs all the time while driving.",
    "Comprehensive components": "runs all the time while driving.",
}

# The colors used for the pictures on Home; the other pages and the side menu use the same ones.
TINT = {"engine": "#E08A00", "safety": "#D9362B", "scan": "#6C4BD1", "gauge": "#0F8B8D", "smog": "#1E8A4A",
        "vehicle": "#1F6FD1", "semi": "#B4532A", "old": "#7A5A2E", "home": "#222222", "help": "#5E7488",
        "service": "#B03E6E", "history": "#2C5C9A", "battery": "#3A9A56"}
PAGE_ICON = {"Home": ("home", "home"), "Problems": ("alert", "engine"), "Live data": ("gauge", "gauge"),
             "Smog check": ("smog", "smog"), "Tests": ("scan", "scan"), "Vehicle": ("vehicle", "vehicle"),
             "Service": ("wrench", "service"), "History": ("history", "history"),
             "Help": ("help", "help")}

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
def bind_click(widget, command, also=()):
    """Standard button behavior: act when the mouse button is released over the widget, and only if it
    was also pressed there. This stops a click that changes the page from 'landing' on whatever widget
    appears under the pointer on the new page (macOS delivers that release to the new widget)."""
    targets = (widget,) + tuple(also)
    state = {"armed": False}

    def press(_e):
        state["armed"] = True

    def release(e):
        armed, state["armed"] = state["armed"], False
        if not armed:
            return
        under = widget.winfo_containing(e.x_root, e.y_root)
        if under is not None and any(str(under) == str(t) or str(under).startswith(str(t) + ".") for t in targets):
            command()

    for t in targets:
        t.bind("<ButtonPress-1>", press, add="+")
        t.bind("<ButtonRelease-1>", release, add="+")


class PillButton(tk.Canvas):
    STYLES = {
        "primary": {"fill": "#000000", "hover": "#2A2A2A", "text": "#FFFFFF", "outline": "#000000"},
        "secondary": {"fill": "#FFFFFF", "hover": "#F3F3F3", "text": "#000000", "outline": "#000000"},
        "danger": {"fill": "#FFFFFF", "hover": C["red_soft"], "text": C["red"], "outline": C["red"]},
        "onheader": {"fill": "#FFFFFF", "hover": "#F3F3F3", "text": "#000000", "outline": "#000000"},
    }

    def __init__(self, parent, text, command, kind="secondary", big=False, min_width=0):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, bd=0, cursor="hand2", takefocus=1)
        self.command, self.kind, self.big, self.min_width = command, kind, big, min_width
        self.font = F(15 if big else 13, "bold")
        self.enabled, self.hovering = True, False
        self.set_text(text)
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        bind_click(self, self._click)
        self.bind("<Return>", lambda e: self._click())
        self.bind("<space>", lambda e: self._click())
        self.bind("<FocusIn>", lambda e: self._draw())
        self.bind("<FocusOut>", lambda e: self._draw())

    def set_text(self, text):
        self.text = text
        padx, pady = (24, 12) if self.big else (15, 7)
        self.w = max(self.font.measure(text) + 2 * padx, self.min_width)
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
        bind_click(self, command)


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
        if self.state == "off":  # not connected yet: the check-engine picture from the Home page
            icons.draw(self, "engine", s / 2, s / 2, s * 0.6, TINT["engine"], halo=True)
            return
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
        self.bind("<Leave>", self._leave)

    def _leave(self, _e):
        """Moving onto a tile inside the list also counts as 'leaving' the frame, so only stop
        listening to the scroll wheel when the pointer has really left the whole list."""
        try:
            under = self.winfo_containing(*self.winfo_pointerxy())
        except (tk.TclError, KeyError):
            under = None
        if under is None or not str(under).startswith(str(self)):
            self._wheel(False)

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


class LiveGraph(tk.Canvas):
    """Line graph of up to 4 live readings over the last 90 seconds. Each line has its own scale."""
    COLORS = ["#E08A00", "#1F6FD1", "#1E8A4A", "#6C4BD1"]
    SPAN = 90.0

    def __init__(self, parent):
        super().__init__(parent, height=230, bg=C["page"], highlightthickness=0)
        self.series = {}   # key -> {"name", "unit", "points": [(t, v)]}
        self._job = None
        self.bind("<Configure>", lambda e: self.redraw())

    def set_keys(self, keys, names):
        for k in list(self.series):
            if k not in keys:
                del self.series[k]
        for k in keys:
            self.series.setdefault(k, {"name": names.get(k, str(k)), "unit": "", "points": []})
        self.redraw()

    def add(self, key, value, unit):
        if key in self.series:
            sr = self.series[key]
            sr["unit"] = unit
            sr["points"].append((time.time(), value))
            cut = time.time() - self.SPAN
            while sr["points"] and sr["points"][0][0] < cut:
                sr["points"].pop(0)
            if not self._job:
                self._job = self.after(250, self.redraw)

    def redraw(self):
        self._job = None
        self.delete("all")
        w, h = self.winfo_width(), int(self["height"])
        if w < 50:
            return
        icons.rounded_rect(self, 1, 1, w - 1, h - 1, 18, fill=C["panel"], outline=C["line"])
        left, right, top, bottom = 18, w - 18, 46, h - 28
        for i in range(5):
            y = top + (bottom - top) * i / 4
            self.create_line(left, y, right, y, fill="#EFEFEF")
        now = time.time()
        first = min((sr["points"][0][0] for sr in self.series.values() if sr["points"]), default=now)
        span = max(15.0, min(self.SPAN, now - first))  # fill the width from the start, up to 90 seconds
        self.create_text(left, h - 14, text=f"{int(span)} s ago", anchor="w", fill=C["muted"], font=F(11))
        self.create_text(right, h - 14, text="now", anchor="e", fill=C["muted"], font=F(11))
        x = left
        for i, (key, sr) in enumerate(self.series.items()):
            color = self.COLORS[i % len(self.COLORS)]
            pts = sr["points"]
            label = sr["name"]
            if pts:
                vals = [v for _, v in pts]
                lo, hi = min(vals), max(vals)
                if hi - lo < 1e-9:
                    lo, hi = lo - 1, hi + 1
                pad = (hi - lo) * 0.1
                lo, hi = lo - pad, hi + pad
                xy = []
                for t, v in pts:
                    xy += [right - (now - t) / span * (right - left), bottom - (v - lo) / (hi - lo) * (bottom - top)]
                if len(xy) >= 4:
                    self.create_line(*xy, fill=color, width=2.5, smooth=True, capstyle="round", joinstyle="round")
                label += f": {_num(pts[-1][1])} {sr['unit']}"
            self.create_oval(x, 18, x + 10, 28, fill=color, outline="")
            t = self.create_text(x + 16, 23, text=label, anchor="w", fill=C["ink"], font=F(12, "bold"))
            x = self.bbox(t)[2] + 22


def _num(v):
    return f"{v:.0f}" if abs(v) >= 100 else f"{v:.1f}" if abs(v) >= 10 else f"{v:.2f}"


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
        bind_click(self, lambda: self.command())
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
        bind_click(self, self.toggle, also=(self.body, top, self.title, self.sub, dot, pill))
        for w in (self, self.body, top, self.title, self.sub, dot, pill):
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
        about = as_sentences(info["category"])
        if info.get("factory"):
            about = (f"This is the {info['factory']} factory meaning of this code. It can differ a little by model "
                     f"and year, so double-check before buying parts. " + about)
        parts = [("Why it matters", it.get("why") or why_it_matters(it["code"], it["status"], it["module"])),
                 ("Common causes", info["causes"]),
                 ("How it failed", info["failure_type"].split(": ", 1)[-1] if info["failure_type"] else ""),
                 ("About this code", about)]
        checks = info.get("checks") or []
        for heading, text in parts:
            if heading == "About this code" and checks:
                self._steps(checks)
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
        PillButton(row, "Repair videos", lambda: self.app.lookup_online(self.item["code"], videos=True)).pack(
            side="left", padx=(10, 0))

    def _steps(self, steps):
        """'How to check it': numbered steps in colored circles, like the Help page."""
        tk.Label(self.details, text="How to check it", bg=C["panel"], fg=C["ink"], font=F(13, "bold"),
                 anchor="w").pack(fill="x", pady=(6, 2))
        box = tk.Frame(self.details, bg=C["panel"])
        box.pack(fill="x")
        box.columnconfigure(1, weight=1)
        wrap = max(300, self.body.winfo_width() - 110)
        for i, step in enumerate(steps, 1):
            dot = tk.Canvas(box, width=26, height=26, bg=C["panel"], highlightthickness=0)
            dot.grid(row=i, column=0, sticky="nw", pady=3)
            dot.create_oval(2, 2, 24, 24, fill=icons.blend("#FFFFFF", TINT["vehicle"], 0.15), outline="")
            dot.create_text(13, 13, text=str(i), fill=TINT["vehicle"], font=F(12, "bold"))
            tk.Label(box, text=step, bg=C["panel"], fg=C["ink"], font=F(13), anchor="w", justify="left",
                     wraplength=wrap).grid(row=i, column=1, sticky="w", padx=(10, 0), pady=3)


# ----------------------------------------------------------------------------
# The app
# ----------------------------------------------------------------------------
class App:
    PAGES = ["Home", "Problems", "Live data", "Smog check", "Tests", "Vehicle", "History", "Help"]

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
        self._auto_check_updates()

    AUTO_CHECK_MS = 30 * 60 * 1000  # while the app is open, look for a new version every 30 minutes

    def _auto_check_updates(self):
        """Look for a new version in the background: at start-up, then every 30 minutes."""
        if not self.update_rel:  # once one is found, the notice stays up; no need to keep asking
            def found(r):
                if r and not self.update_rel:
                    self._update_found(r, quiet=True)
            threading.Thread(target=lambda: self.ui(lambda r=updater.check(): found(r)), daemon=True).start()
        self.root.after(self.AUTO_CHECK_MS, self._auto_check_updates)

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

    def run_bg(self, work, done=None, step="Working…", on_error=None, quiet_errors=False):
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
            self.ui(lambda: self._finish(result, err, done, on_error, quiet_errors))

        threading.Thread(target=wrap, daemon=True).start()

    def _finish(self, result, err, done, on_error=None, quiet=False):
        self.busy = False
        self.set_step("")
        self._update_controls()
        if err is not None and on_error:
            on_error(err)
            if quiet:
                return
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
        tk.Frame(self.root, bg=C["line"], height=1).pack(fill="x")

        logo = tk.Canvas(head, width=36, height=36, bg=C["header"], highlightthickness=0)
        logo.pack(side="left", padx=(0, 10))
        icons.app_logo(logo, 18, 18, 34)  # drawn, not a shrunken picture, so it stays sharp
        tk.Label(head, text=APP_NAME, bg=C["header"], fg="#000000", font=F(17, "bold")).pack(side="left")
        self.disconnect_btn = PillButton(head, "Disconnect", self.disconnect, kind="onheader")
        self.vehicle_lbl = tk.Label(head, text="", bg=C["header"], fg="#000000", font=F(13, "bold"))
        self.vehicle_lbl.pack(side="right", padx=(0, 12))

        body = tk.Frame(self.root, bg=C["page"])
        body.pack(fill="both", expand=True)
        side = tk.Frame(body, bg=C["side"], width=200, pady=18)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Frame(body, bg=C["line"], width=1).pack(side="left", fill="y")
        self.nav = {}
        for name in self.PAGES:
            item = tk.Canvas(side, width=176, height=46, bg=C["side"], highlightthickness=0, cursor="hand2")
            item.pack(padx=12, pady=2, anchor="w")
            bind_click(item, lambda n=name: self.show_page(n))
            item.bind("<Enter>", lambda e, n=name: self._nav_draw(n, hover=True))
            item.bind("<Leave>", lambda e, n=name: self._nav_draw(n))
            self.nav[name] = item

        self.main = tk.Frame(body, bg=C["page"], padx=34, pady=26)
        self.main.pack(side="left", fill="both", expand=True)
        self.pages = {
            "Home": self._build_home(),
            "Choose vehicle": self._build_picker(),
            "1995 and older": self._build_obd1(),
            "Problems": self._build_problems(),
            "Live data": self._build_live(),
            "Smog check": self._build_smog(),
            "Tests": self._build_tests(),
            "Vehicle": self._build_vehicle(),
            "History": self._build_history(),
            "Help": self._build_help(),
        }

    def show_page(self, name):
        if name == "Home":
            self.refresh_home()
        self.nav_selected = "Home" if name in ("Choose vehicle", "1995 and older") else name
        for n in self.nav:
            self._nav_draw(n)
        for n, frame in self.pages.items():
            if n == name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self.current_page = name
        if name == "History" and hasattr(self, "history_area"):
            self.refresh_history()
        if name == "Service" and hasattr(self, "service_area"):
            self.refresh_service()
        if name == "Vehicle" and hasattr(self, "recall_btn"):
            make, model, year, vin, _ = self._recall_vehicle()
            if (vin or (make and model and year)) and self._recalls_for != (make, model, year, vin):
                self.check_recalls(quiet=True)

    def _nav_draw(self, name, hover=False):
        cv = self.nav[name]
        cv.delete("all")
        sel = name == getattr(self, "nav_selected", "")
        cv.surface = C["side"]
        if sel:  # looks like a Home tile with the pointer on it: white card, black edge
            icons.rounded_rect(cv, 2, 2, 174, 44, 14, fill="#FFFFFF", outline="#000000", width=2)
        elif hover:
            icons.rounded_rect(cv, 2, 2, 174, 44, 14, fill=C["hover"], outline="")
            cv.surface = C["hover"]
        icon, tint = PAGE_ICON.get(name, ("scan", "scan"))
        icons.draw(cv, icon, 26, 23, 19, TINT[tint], F(9, "bold"), halo=True)
        cv.create_text(48, 23, text=name, anchor="w", fill="#000000", font=F(14, "bold" if sel else "normal"))

    def _page_title(self, parent, title, subtitle="", icon=None):
        """Page heading. With icon=(picture, color key) it gets the same round picture as the Home tiles."""
        holder = parent
        if icon:
            holder = tk.Frame(parent, bg=C["page"])
            holder.pack(fill="x", pady=(0, 16))
            cv = tk.Canvas(holder, width=76, height=76, bg=C["page"], highlightthickness=0)
            cv.pack(side="left", padx=(0, 16))
            icons.draw(cv, icon[0], 38, 38, 46, TINT[icon[1]], F(10, "bold"), halo=True)
            holder = tk.Frame(holder, bg=C["page"])
            holder.pack(side="left", fill="x", expand=True)
        tk.Label(holder, text=title, bg=C["page"], fg=C["ink"], font=F(24 if icon else 22, "bold"),
                 anchor="w").pack(fill="x")
        if subtitle:
            sub = tk.Label(holder, text=subtitle, bg=C["page"], fg=C["muted"], font=F(13), anchor="w",
                           justify="left")
            sub.pack(fill="x", pady=(2, 0 if icon else 14))
            wrap_on_resize(sub, 20)
            return sub
        return None

    def _empty_card(self, parent, icon, title, text, button=None):
        """A friendly card for a page with nothing to show yet: a round picture, a line and a button."""
        card = RoundPanel(parent, pad=(22, 18), radius=22)
        card.pack(fill="x", pady=(4, 0))
        box = card.inner
        cv = tk.Canvas(box, width=84, height=84, bg=C["panel"], highlightthickness=0)
        cv.pack(side="left", padx=(0, 18))
        icons.draw(cv, icon[0], 42, 42, 50, TINT[icon[1]], F(10, "bold"), halo=True)
        col = tk.Frame(box, bg=C["panel"])
        col.pack(side="left", fill="x", expand=True)
        tk.Label(col, text=title, bg=C["panel"], fg=C["ink"], font=F(16, "bold"), anchor="w").pack(fill="x")
        t = tk.Label(col, text=text, bg=C["panel"], fg=C["muted"], font=F(13), anchor="w", justify="left")
        t.pack(fill="x", pady=(2, 0))
        wrap_on_resize(t, 150)
        if button:
            PillButton(col, button[0], button[1], kind="primary").pack(anchor="w", pady=(10, 0))
        return card

    # --- Home page ---------------------------------------------------------------------------
    def _build_home(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "What do you want to check?")
        self.update_bar_card = RoundPanel(page, pad=(18, 12), fill=C["amber_soft"], outline=C["amber_soft"])
        self.update_bar = self.update_bar_card.inner
        self.home_vehicle = tk.Frame(page, bg=C["page"])
        self.home_vehicle.pack(fill="x", pady=(10, 18))
        s = 64
        tint = TINT

        def art(name, key):
            return lambda cv, x, y: icons.draw(cv, name, x, y, s, tint[key], F(int(s * 0.17), "bold"), halo=True)

        def both(cv, x, y):
            red = tint["safety"]
            cv.create_oval(x - s * 1.05, y - s * 0.68, x + s * 1.05, y + s * 0.68,
                           fill=icons.blend("#FFFFFF", red, 0.13), outline="")
            icons.draw(cv, "abs", x - s * 0.46, y, s * 0.78, red, F(int(s * 0.13), "bold"))
            icons.draw(cv, "airbag", x + s * 0.46, y, s * 0.78, red)

        tile_grid(page, [
            ("Engine codes", "Check-engine and transmission codes", art("engine", "engine"),
             lambda: self.start_scan("engine")),
            ("ABS and airbag", "Brake and airbag warning lights", both, lambda: self.start_scan("safety")),
            ("Full scan", "Everything at once", art("scan", "scan"), lambda: self.start_scan("all")),
            ("Semi trucks", "Heavy-duty trucks, 9-pin port", art("semi", "semi"), self.start_semi),
            ("Live data", "Engine readings in real time", art("gauge", "gauge"), self.open_live),
            ("Smog check", "Ready for an emissions test?", art("smog", "smog"),
             lambda: self.show_page("Smog check")),
            ("1995 and older", "Read blink codes, no adapter", art("blink", "old"), lambda: self.open_obd1()),
            ("Choose vehicle", "Make, model and year", art("vehicle", "vehicle"), self.open_picker),
        ], columns=4, width=184, art=92, title_size=14)
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
            tk.Label(row, text=vehicles.support_text(ch["make"], ch["year"]) + ".", bg=C["page"], fg=C["muted"],
                     font=F(13)).pack(side="left")
            LinkLabel(row, "Change", self.open_picker).pack(side="left", padx=10)
        else:
            tk.Label(box, text="Pick your vehicle first if you like. It helps older vehicles that don't report "
                               "their make, and the app reads codes either way.", bg=C["page"], fg=C["muted"],
                     font=F(13), anchor="w", justify="left", wraplength=640).pack(side="left")
            LinkLabel(box, "Choose vehicle", self.open_picker).pack(side="left", padx=10)

    def open_live_connect(self):
        """Connect from the Live data page, then start the readings."""
        self._after_scan_hook = lambda: (self.current_page == "Live data" and not self.live_running and self.elm
                                         and self.toggle_live())
        self.connect()

    def smog_connect(self):
        self.connect()  # the scan after connecting reads the smog tests too

    def open_live(self):
        self.show_page("Live data")
        if self.elm and not self.live_running and not self.busy:
            self.toggle_live()

    def start_scan(self, kind):
        """Home-screen tiles: connect first if needed, then run that kind of scan."""
        ch = self.chosen
        if ch and int(ch["year"]) < 1996:  # OBD-I: no data port standard, use the blink-code guide
            if kind == "safety":
                messagebox.showinfo(APP_NAME, "On 1995 and older vehicles, ABS and airbag codes use separate, "
                                              "maker-specific blink procedures that this app doesn't cover yet.\n\n"
                                              "Engine codes are covered: use Engine codes or 1995 and older.")
                return
            group = vehicles.obd1_group(ch["make"])
            if not group:
                messagebox.showinfo(APP_NAME, f"1995 and older {ch['make']} vehicles use a system this app can't read.")
                return
            self.open_obd1(group)
            return
        self.scan_kind = kind
        self.show_page("Problems")
        if self.elm and self.elm.is_j1939:
            self.disconnect()
        if self.elm:
            self.scan(kind=kind)
        elif not self.busy:
            self.connect(heavy=False)

    def start_semi(self):
        """Semi trucks: connect to the J1939 network (needs a 9-pin truck cable) and read every module."""
        self.scan_kind = "all"
        self.show_page("Problems")
        if self.elm and not self.elm.is_j1939:
            self.disconnect()
        if self.elm:
            self.scan()
        elif not self.busy:
            self.connect(heavy=True)

    # --- Updates ----------------------------------------------------------------------------
    def _update_found(self, rel, quiet=False):
        self.update_rel = rel
        bar = self.update_bar
        for w in bar.winfo_children():
            w.destroy()
        if hasattr(self, "help_update_btn"):
            self.help_update_btn.pack_forget()
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
            self.update_status.configure(text=f"Version {rel['version']} is available.")
            self.help_update_btn.set_enabled(True)
            self.help_update_btn.pack(side="left", padx=(12, 0))

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
                def show():
                    self.set_step(f"Downloading update ({i + 1} of {n})…", (i + 1) / n)
                    self.update_status.configure(text=f"Downloading update ({i + 1} of {n})…")
                self.ui(show)
            updater.install(rel, progress)
            return rel["version"]

        def done(version):
            messagebox.showinfo(APP_NAME, f"Updated to version {version}. The app will restart now.")
            if self.elm:
                self.elm.close()
            self.root.destroy()
            updater.restart()

        self.help_update_btn.set_enabled(False)
        self.update_status.configure(text="Downloading update…")
        if self.current_page != "Help":  # on Help, stay put: progress shows next to the button
            self.show_page("Problems")

        def failed(err):
            self.help_update_btn.set_enabled(True)
            self.update_status.configure(text="The update didn't finish. Try again.")
        self.run_bg(work, done, "Downloading update…", on_error=failed)

    # --- 1995 and older: blink-code guide ----------------------------------------------------
    OBD1_GROUPS = [("GM", "GM", "Chevy, GMC, Buick, Cadillac, Olds, Pontiac"),
                   ("Ford", "FD", "Ford, Lincoln, Mercury"),
                   ("Chrysler", "CHR", "Chrysler, Dodge, Jeep, Plymouth"),
                   ("Toyota", "TY", "Toyota and Lexus"),
                   ("Honda", "HO", "Honda and Acura")]

    def _build_obd1(self):
        page = tk.Frame(self.main, bg=C["page"])
        top = tk.Frame(page, bg=C["page"])
        top.pack(fill="x")
        LinkLabel(top, "Back", self._obd1_back).pack(side="left")
        self.o1_title = tk.Label(page, text="", bg=C["page"], fg=C["ink"], font=F(22, "bold"), anchor="w",
                                 justify="left")
        self.o1_title.pack(fill="x", pady=(6, 0))
        wrap_on_resize(self.o1_title, 20)
        self.o1_sub = tk.Label(page, text="", bg=C["page"], fg=C["muted"], font=F(13), anchor="w", justify="left")
        self.o1_sub.pack(fill="x", pady=(2, 10))
        wrap_on_resize(self.o1_sub, 20)
        self.o1_area = ScrollArea(page, C["page"])
        self.o1_area.pack(fill="both", expand=True)
        self.o1_group = None
        self.o1_entry = tk.StringVar()
        return page

    def open_obd1(self, group=None):
        self.o1_group = group
        self.o1_entry.set("")
        self.show_page("1995 and older")
        self._obd1_fill()

    def _obd1_back(self):
        if self.o1_group:
            self.o1_group = None
            self._obd1_fill()
        else:
            self.show_page("Home")

    def _obd1_fill(self):
        self.o1_area.clear()
        inner = self.o1_area.inner
        group = self.o1_group
        if not group:
            self.o1_title.configure(text="Read codes on 1995 and older vehicles")
            self.o1_sub.configure(text="These vehicles blink their codes on the check-engine light instead of "
                                       "sending them to an adapter. Pick the make and the app shows you how.")
            spec = []
            for key, letters, makes in self.OBD1_GROUPS:
                def painter(cv, x, y, lt=letters):
                    icons.make_badge(cv, lt, x, y, 62, "#1E1E1E", F(17 if len(lt) < 3 else 14, "bold"))
                spec.append((key, makes, painter, lambda k=key: self.open_obd1(k)))
            tile_grid(inner, spec, columns=4, width=170, art=72, title_size=15)
            return
        guide = obd1.GUIDES[group]
        self.o1_title.configure(text=guide["title"])
        self.o1_sub.configure(text="Follow the steps, count the flashes, then type the codes below.")
        warn = RoundPanel(inner, pad=(18, 12), fill=C["amber_soft"], outline=C["amber_soft"])
        warn.pack(fill="x", pady=(0, 14))
        lbl = tk.Label(warn.inner, text=obd1.SAFETY, bg=C["amber_soft"], fg=C["ink"], font=F(13), anchor="w",
                       justify="left")
        lbl.pack(fill="x")
        wrap_on_resize(lbl, 10)
        steps = tk.Frame(inner, bg=C["page"])
        steps.pack(fill="x")
        steps.grid_columnconfigure(1, weight=1)
        for i, text in enumerate(guide["steps"], 1):
            num = tk.Canvas(steps, width=30, height=30, bg=C["page"], highlightthickness=0)
            num.create_oval(2, 2, 28, 28, fill="#000000", outline="")
            num.create_text(15, 15, text=str(i), fill="#FFFFFF", font=F(13, "bold"))
            num.grid(row=i, column=0, sticky="nw", pady=5)
            t = tk.Label(steps, text=text, bg=C["page"], fg=C["ink"], font=F(14), anchor="w", justify="left")
            t.grid(row=i, column=1, sticky="we", padx=(12, 0), pady=7)
            steps.bind("<Configure>", lambda e, lb=t: lb.winfo_exists() and lb.configure(
                wraplength=max(300, e.width - 60)), add="+")
        if guide["note"]:
            tk.Label(inner, text=guide["note"], bg=C["page"], fg=C["muted"], font=F(12), anchor="w",
                     justify="left").pack(fill="x", pady=(8, 0))
        row = tk.Frame(inner, bg=C["page"])
        row.pack(fill="x", pady=(18, 0))
        tk.Label(row, text="Codes you counted", bg=C["page"], fg=C["ink"], font=F(14, "bold")).pack(side="left")
        entry = ttk.Entry(row, textvariable=self.o1_entry, width=24, font=F(14))
        entry.pack(side="left", padx=10)
        entry.bind("<Return>", lambda e: self._obd1_explain())
        PillButton(row, "Explain codes", self._obd1_explain, kind="primary").pack(side="left")
        tk.Label(inner, text="Separate codes with spaces or commas, for example: 12 33 44", bg=C["page"],
                 fg=C["muted"], font=F(12), anchor="w").pack(fill="x", pady=(4, 0))
        self.o1_results = tk.Frame(inner, bg=C["page"])
        self.o1_results.pack(fill="x", pady=(14, 0))
        if self.o1_entry.get().strip():
            self._obd1_explain()

    def _obd1_explain(self):
        for w in self.o1_results.winfo_children():
            w.destroy()
        codes = obd1.parse_entry(self.o1_entry.get())
        if not codes:
            tk.Label(self.o1_results, text="Type the numbers you counted first.", bg=C["page"], fg=C["muted"],
                     font=F(13), anchor="w").pack(fill="x")
            return
        pills = {"ok": ("Not a fault", C["green_soft"], C["green"]),
                 "fault": ("Problem", C["amber_soft"], C["amber_ink"]),
                 "unknown": ("Not in list", C["off_soft"], C["muted"])}
        for code in codes:
            meaning, kind = obd1.explain(self.o1_group, code)
            card = RoundPanel(self.o1_results, pad=(20, 12), radius=16)
            card.pack(fill="x", pady=(0, 10))
            row = card.inner
            tk.Label(row, text=code, bg=C["panel"], fg=C["ink"], font=F(22, "bold"), width=4, anchor="w").pack(
                side="left")
            words, bg, fg = pills[kind]
            pill = tk.Canvas(row, bg=C["panel"], highlightthickness=0, height=26, width=F(12, "bold").measure(words) + 24)
            icons.rounded_rect(pill, 1, 1, int(pill["width"]) - 1, 25, 13, fill=bg, outline="")
            pill.create_text(int(pill["width"]) / 2, 13, text=words, fill=fg, font=F(12, "bold"))
            pill.pack(side="right")
            t = tk.Label(row, text=meaning, bg=C["panel"], fg=C["ink"], font=F(14), anchor="w", justify="left")
            t.pack(side="left", fill="x", expand=True, padx=(8, 12))
            wrap_on_resize(t, 220)
        self.o1_area.scroll_to(self.o1_results)

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
        self._pick_quiet = False
        self.pick_search.trace_add("write", lambda *a: None if self._pick_quiet else self._pick_fill())
        self.pick_area = ScrollArea(page, C["page"])
        self.pick_area.pack(fill="both", expand=True)
        self.pick_step, self.pick_make, self.pick_model = "make", None, None
        return page

    def open_picker(self):
        self.pick_step, self.pick_make, self.pick_model = "make", None, None
        self.show_page("Choose vehicle")
        self._pick_reset_search()
        self._pick_fill()

    def _pick_back(self):
        if self.pick_step == "year":
            self.pick_step = "model"
        elif self.pick_step == "model":
            self.pick_step = "make"
        else:
            self.show_page("Home")
            return
        self._pick_reset_search()
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
            for model, kind in vehicles.models(make):
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
            ys = [y for y in vehicles.model_years(self.pick_make, self.pick_model) if not q or q in str(y)]
            for i, y in enumerate(ys):
                b = PillButton(grid, str(y), lambda yr=y: self._pick_set_year(yr), big=True,
                               min_width=F(15, "bold").measure("2000") + 52)
                b.grid(row=i // 7, column=i % 7, padx=(0, 10), pady=(0, 10), sticky="w")
            older = vehicles.obd1_group(self.pick_make) and ys and min(ys) < 1996
            note = ("1995 and older: the app walks you through reading the blink codes, no adapter needed."
                    if older else "Only the years this model was sold, and that this app can read, are shown.")
            tk.Label(inner, text=note, bg=C["page"], fg=C["muted"], font=F(12), anchor="w").pack(
                fill="x", pady=(8, 0))

    def _pick_reset_search(self):
        self._pick_quiet = True
        self.pick_search.set("")
        self._pick_quiet = False

    def _pick_set_make(self, make):
        self.pick_make, self.pick_step = make, "model"
        self._pick_reset_search()
        self._pick_fill()

    def _pick_set_model(self, model, kind):
        self.pick_model, self.pick_kind, self.pick_step = model, kind, "year"
        self._pick_reset_search()
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
        LinkLabel(row, "2012 Ford", lambda: self.connect(CONN_DEMO, heavy=False)).pack(side="left", padx=(8, 0))
        tk.Label(row, text="or", bg=C["panel"], fg=C["muted"], font=F(13)).pack(side="left", padx=6)
        LinkLabel(row, "2004 GM truck", lambda: self.connect(CONN_DEMO_OLD, heavy=False)).pack(side="left")
        tk.Label(row, text="or", bg=C["panel"], fg=C["muted"], font=F(13)).pack(side="left", padx=6)
        LinkLabel(row, "semi truck", lambda: self.connect(CONN_DEMO_SEMI, heavy=True)).pack(side="left")

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
    def connect(self, kind=None, heavy=None):
        kind = kind or self.conn_kind.get()
        target = self.port_var.get().strip()
        if heavy is None:
            heavy = getattr(self, "heavy", False)
        heavy = heavy or kind == CONN_DEMO_SEMI
        self.heavy = heavy

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
            self.ui(lambda: self.set_step("Listening to the truck's network…" if heavy else
                                          "Talking to the vehicle… (finding its language can take 20 seconds)"))
            try:
                if heavy:
                    j1939.initialize(elm)
                else:
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
            if not self.live_running:
                self._live_empty()
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
        self.root.after(300, lambda: self.live_running or self._live_empty())

    def _gather_info(self, elm):
        if elm.is_j1939:
            vin = j1939.read_vin(elm)
            self._vin = vin
            year = year_from_vin(vin)
            return {
                "title": f"{year} semi truck" if year else "Semi truck",
                "vin": vin or "Not reported", "make": "-", "year": str(year) if year else "-",
                "voltage": elm.voltage(), "protocol": elm.protocol_name, "adapter": elm.version,
                "ecus": ", ".join(j1939.source_name(a) for a in elm.ecus) or "-",
            }
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

        if elm.is_j1939:
            def heavy_work():
                self.ui(lambda: self.set_step("Listening for trouble codes from every module…", 0.3))
                return j1939.read_codes(elm)

            def heavy_done(mods):
                self._scanning = False
                self._apply_j1939(mods)

            self.lamp.set("busy")
            self.run_bg(heavy_work, heavy_done, "Reading the truck's codes…")
            return

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
        self._save_history()
        self.refresh_problems()
        self.refresh_smog()
        hook, self._after_scan_hook = getattr(self, "_after_scan_hook", None), None
        if hook:
            hook()

    AFTERTREATMENT = {1761, 3031, 3216, 3226, 3242, 3246, 3251, 3364, 3719, 3720, 4364, 5246}

    def _apply_j1939(self, mods):
        items = []
        for m in mods:
            red, amber = m["lamps"].get("Red stop lamp"), m["lamps"].get("Amber warning lamp")
            for spn, fmi, oc, active in [(s, f, o, True) for s, f, o in m["active"]] + \
                                        [(s, f, o, False) for s, f, o in m["previous"]]:
                if active:
                    status = "Active now" + (f", seen {oc} times" if oc > 1 else "")
                    level = "high" if red or m["sa"] == 11 else "medium"
                else:
                    status, level = "Previously active", "past"
                if not active:
                    why = "This happened before but isn't active now. Often it's an intermittent wiring fault."
                elif red:
                    why = "The red stop lamp is on. Stop when it's safe and get this checked before driving on."
                elif m["sa"] == 11:
                    why = ("ABS may be switched off for that wheel or the whole truck. Normal air brakes still work, "
                           "but wheels can lock in a hard stop.")
                elif spn in self.AFTERTREATMENT:
                    why = ("This is in the emissions (DPF/DEF/SCR) system. If it's ignored, the engine can "
                           "reduce power and speed until it's fixed.")
                elif amber:
                    why = "The amber warning lamp is on. Get this checked soon."
                else:
                    why = "Have this checked at your next service."
                items.append({
                    "code": f"SPN {spn} FMI {fmi}", "module": m["name"], "status": status, "resp": "",
                    "level": level, "why": why,
                    "info": {"description": j1939.describe(spn, fmi), "known": spn in j1939.SPN,
                             "category": f"Heavy-duty (J1939) code from the {m['name'].lower()} module. SPN {spn} "
                                         f"is the part, FMI {fmi} is how it failed.",
                             "failure_type": "", "causes": ""}})
        items.sort(key=lambda i: LEVEL_ORDER[i["level"]])
        self.items, self.scanned = items, True
        self.modules = [{"name": m["name"], "target": m["sa"], "dtcs": m["active"], "bus": "j1939"} for m in mods]
        self.readiness = None
        self.mil_on = any(m["lamps"].get("Check engine (malfunction) lamp") for m in mods)
        self._save_history()
        self.refresh_problems()
        self.refresh_smog()
        hook, self._after_scan_hook = getattr(self, "_after_scan_hook", None), None
        if hook:
            hook()

    def _item(self, code, module, status, resp=""):
        return {"code": code, "module": module, "status": status, "resp": resp,
                "info": describe_dtc(code, self._current_make()), "level": severity(code, status, module)}

    def _current_make(self):
        """The make to use for factory code meanings: the one picked in Choose vehicle, else from the VIN."""
        ch = getattr(self, "chosen", None)
        if ch and ch.get("make"):
            return ch["make"]
        make = (getattr(self, "vehicle", None) or {}).get("make", "")
        return "" if make == "-" else make

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
            if elm.is_j1939:
                self.ui(lambda: self.set_step("Clearing codes in every module…", 0.3))
                j1939.clear_codes(elm)
                time.sleep(1.5)
                return True
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
        self._page_title(page, "Live data", icon=PAGE_ICON["Live data"], subtitle="What the engine computer sees right now. Values update about "
                                            "once a second.")
        bar = tk.Frame(page, bg=C["page"])
        bar.pack(fill="x")
        self.live_btn = PillButton(bar, "Start live data", self.toggle_live, kind="primary")
        self.live_btn.pack(side="left")
        self.freeze_btn = PillButton(bar, "Show freeze frame", self.read_freeze_frame)
        self.freeze_btn.pack(side="left", padx=10)
        self.record_btn = PillButton(bar, "Record", self.toggle_record)
        self.record_btn.pack(side="left")
        self.record_btn.set_enabled(False)
        tk.Label(bar, text="Click any reading to graph it", bg=C["page"], fg=C["muted"], font=F(12)).pack(
            side="right")
        self.page_buttons = [self.freeze_btn]
        self.graph = LiveGraph(page)
        self.graph_keys = []      # readings being graphed (up to 4)
        self.live_stats = {}      # key -> [low, high] in the units shown
        self.live_last = {}       # key -> (value, unit) latest, in the units shown
        self.recording = None     # list of rows while recording
        self.tiles_area = ScrollArea(page, C["page"])
        self.tiles_area.pack(fill="both", expand=True, pady=(16, 0))
        self.tiles = {}
        self._live_empty()
        return page

    def _live_empty(self):
        self.tiles_area.clear()
        if self.elm:
            self._empty_card(self.tiles_area.inner, PAGE_ICON["Live data"], "Ready when you are",
                             "Click Start live data to watch speed, RPM, temperatures and more, updated every "
                             "second.", ("Start live data", self.toggle_live))
        else:
            self._empty_card(self.tiles_area.inner, PAGE_ICON["Live data"], "Not connected yet",
                             "Plug the adapter in, turn the key to ON, then connect to see live readings.",
                             ("Connect", self.open_live_connect))

    def _make_tiles(self, entries):
        """entries: [(key, name)]"""
        self.tiles_area.clear()
        self.graph_keys, self.live_stats, self.live_last = [], {}, {}
        self.graph.set_keys([], {})
        self.graph.pack_forget()
        grid = tk.Frame(self.tiles_area.inner, bg=C["page"])
        grid.pack(fill="x")
        self.tiles = {}
        for i, (pid, name) in enumerate(entries):
            card = RoundPanel(grid, pad=(18, 14), radius=18)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=(0, 12), pady=(0, 12))
            tile = card.inner
            value = tk.Label(tile, text="…", bg=C["panel"], fg=C["ink"], font=F(24, "bold"), anchor="w")
            value.pack(fill="x")
            alt = tk.Label(tile, text="", bg=C["panel"], fg=C["muted"], font=F(12), anchor="w")
            alt.pack(fill="x")
            lbl = tk.Label(tile, text=name, bg=C["panel"], fg=C["ink"], font=F(13), anchor="w", justify="left",
                           wraplength=220)
            lbl.pack(fill="x")
            span = tk.Label(tile, text="", bg=C["panel"], fg=C["muted"], font=F(11), anchor="w")
            span.pack(fill="x")
            self.tiles[pid] = (value, alt, span, card, name)
            bind_click(card, lambda k=pid: self._toggle_graph(k), also=(tile, value, alt, lbl, span))
            for w in (card, tile, value, alt, lbl, span):
                w.configure(cursor="hand2")
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1, uniform="tiles")

    def _set_tile(self, pid, text, value=None, unit=None):
        if pid not in self.tiles:
            return
        main, _, alt = text.partition("(")
        self.tiles[pid][0].configure(text=main.strip())
        self.tiles[pid][1].configure(text=alt.rstrip(")").strip())
        if value is None or unit in ("s", "min", "count", "km"):
            return
        v, u = us_value(value, unit)
        self.live_last[pid] = (v, u)
        st = self.live_stats.setdefault(pid, [v, v])
        st[0], st[1] = min(st[0], v), max(st[1], v)
        self.tiles[pid][2].configure(text=f"Low {_num(st[0])} · High {_num(st[1])} {u}")
        self.graph.add(pid, v, u)

    def _toggle_graph(self, key):
        if key in self.graph_keys:
            self.graph_keys.remove(key)
        else:
            if len(self.graph_keys) >= 4:
                self.graph_keys.pop(0)
            self.graph_keys.append(key)
        for k, t in self.tiles.items():
            card = t[3]
            on = k in self.graph_keys
            card.outline = "#000000" if on else C["line"]
            card._fit()
            card.itemconfigure("card", width=2 if on else 1)
        self.graph.set_keys(self.graph_keys, {k: t[4] for k, t in self.tiles.items()})
        if self.graph_keys and not self.graph.winfo_ismapped():
            self.graph.pack(fill="x", pady=(14, 0), before=self.tiles_area)
        elif not self.graph_keys:
            self.graph.pack_forget()

    def toggle_record(self):
        if self.recording is None:
            self.recording = []
            self.record_btn.set_text("Stop recording")
            return
        rows, self.recording = self.recording, None
        self.record_btn.set_text("Record")
        if not rows:
            return
        keys = [k for k in self.tiles if any(k in r[1] for r in rows)]
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Spreadsheet (CSV)", "*.csv")],
                                            initialfile=f"drive-{datetime.datetime.now():%Y-%m-%d-%H%M}.csv")
        if not path:
            return
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            out = csv.writer(f)
            start = rows[0][0]
            units = {k: next((r[1][k][1] for r in rows if k in r[1]), "") for k in keys}
            out.writerow(["Seconds"] + [f"{self.tiles[k][4]} ({units[k]})" if units[k] else self.tiles[k][4]
                                        for k in keys])
            for t, vals in rows:
                out.writerow([f"{t - start:.1f}"] + [_num(vals[k][0]) if k in vals else "" for k in keys])
        self.step_lbl.configure(text=f"Recording saved to {path}")
        self._append_log(f"Recording saved to {path}")

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
                if elm.is_j1939:
                    self.ui(lambda: self._make_tiles(j1939.LIVE_NAMES))
                    while not self.live_stop.is_set():
                        for key, txt in j1939.read_live(elm, 1.0).items():
                            self.ui(lambda k=key, t=txt: self._set_tile(k, t))
                    return
                sup = elm.supported_pids()
                pids = [p for p in PIDS if p in sup] or [0x0C, 0x0D, 0x05]
                # factory readings for this make: keep only the ones that answer with a believable value
                extra = {}
                for did, spec in EXTENDED.get(maker_codes.family(self._current_make()), {}).items():
                    v = self._read_extended(elm, did, spec)
                    if v is not None:
                        extra[("x", did)] = (did, spec)
                tiles = [(p, PIDS[p][0]) for p in pids] + [(k, spec[0] + " (factory)") for k, (_d, spec) in
                                                           extra.items()]
                self.ui(lambda: (self._make_tiles(tiles), self.record_btn.set_enabled(True)))
                def read(pid):
                    d = elm.query_pid(1, pid)
                    if d is not None:
                        txt = format_pid(pid, d)
                        try:
                            v = PIDS[pid][1](d)
                        except (IndexError, TypeError):
                            v = None
                        self.ui(lambda p=pid, t=txt, v=v: self._set_tile(p, t, v, PIDS[p][2]))

                while not self.live_stop.is_set():
                    for pid in pids:
                        if self.live_stop.is_set():
                            break
                        read(pid)
                        for g in list(self.graph_keys):  # graphed readings are read far more often
                            if g in PIDS and g != pid and g in pids:
                                read(g)
                    for key, (did, spec) in extra.items():
                        v = self._read_extended(elm, did, spec)
                        if v is not None:
                            self.ui(lambda k=key, t=format_value(v, spec[2]), v=v, u=spec[2]:
                                    self._set_tile(k, t, v, u))
                    self.ui(self._record_tick)
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                self.ui(lambda: messagebox.showerror(APP_NAME, f"Live data stopped: {msg}"))
            finally:
                self.ui(self._live_ended)

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _read_extended(elm, did, spec):
        """One factory reading -> value, or None if it didn't answer or the number isn't believable."""
        try:
            d = elm.query_did(did)
            if not d:
                return None
            v = spec[1](d)
        except (IndexError, ValueError, TypeError):
            return None
        lo, hi = spec[3]
        return v if lo <= v <= hi else None

    def _record_tick(self):
        if self.recording is not None:
            self.recording.append((time.time(), dict(self.live_last)))

    def _live_ended(self):
        if self.recording is not None:
            self.toggle_record()
        self.record_btn.set_enabled(False)
        self.live_running = False
        self.busy = False
        self._update_controls()

    def read_freeze_frame(self):
        elm = self.elm
        if elm and elm.is_j1939:
            messagebox.showinfo(APP_NAME, "Semi trucks keep snapshot data in maker-specific formats, so the freeze "
                                          "frame isn't available here. Live data works.")
            return

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
        self._page_title(page, "Smog check", icon=PAGE_ICON["Smog check"], subtitle="Before an emissions inspection, the vehicle has to finish its own "
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
            if getattr(self, "elm", None):
                self._empty_card(inner, PAGE_ICON["Smog check"], "Not checked yet",
                                 "Click Check again to read the vehicle's self-tests.", None)
            else:
                self._empty_card(inner, PAGE_ICON["Smog check"], "Not connected yet",
                                 "Connect and scan to see whether the vehicle is ready for inspection.",
                                 ("Connect", self.smog_connect))
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
            tip = DRIVE_CYCLES.get(rows[i][0]) if supported and incomplete else None
            if tip:
                t = tk.Label(box, text="How to finish it: " + tip, bg=C["panel"], fg=C["muted"], font=F(12),
                             anchor="w", justify="left", padx=18)
                t.pack(fill="x", pady=(0, 8))
                wrap_on_resize(t, 80)

    # --- Vehicle page ---------------------------------------------------------------------------
    def _build_vehicle(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "Vehicle", "What the vehicle and adapter report about themselves.",
                         icon=PAGE_ICON["Vehicle"])
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

        # Safety recalls, from the government's free database (works without the adapter)
        rec = tk.Frame(page, bg=C["page"])
        rec.pack(fill="both", expand=True, pady=(24, 0))
        head = tk.Frame(rec, bg=C["page"])
        head.pack(fill="x")
        cv = tk.Canvas(head, width=44, height=44, bg=C["page"], highlightthickness=0)
        cv.pack(side="left", padx=(0, 10))
        icons.draw(cv, "alert", 22, 22, 26, TINT["safety"], halo=True)
        tk.Label(head, text="Safety recalls", bg=C["page"], fg=C["ink"], font=F(18, "bold")).pack(side="left")
        self.recall_btn = PillButton(head, "Check recalls", self.check_recalls, kind="primary")
        self.recall_btn.pack(side="right")
        self.recall_status = tk.Label(rec, text="Recalls are repaired free at any dealer. Pick your vehicle or "
                                                "connect, then click Check recalls.",
                                      bg=C["page"], fg=C["muted"], font=F(13), anchor="w", justify="left")
        self.recall_status.pack(fill="x", pady=(6, 4))
        wrap_on_resize(self.recall_status, 20)
        self.recall_links = tk.Frame(rec, bg=C["page"])
        self.recall_links.pack(fill="x", pady=(0, 8))
        self.recall_area = ScrollArea(rec, C["page"])
        self.recall_area.pack(fill="both", expand=True)
        self._recalls_for = None
        return page

    def _recall_vehicle(self):
        """-> (make, model, year, vin, name) of the vehicle to look up; any part may be empty."""
        ch = self.chosen or {}
        vin = (self.vehicle or {}).get("vin", "")
        vin = vin if vin and vin != "-" and len(vin) == 17 else ""
        make, model, year = ch.get("make", ""), ch.get("model", ""), str(ch.get("year", "") or "")
        name = " ".join(x for x in (year, make, model) if x) or (self.vehicle or {}).get("title", "")
        return make, model, year, vin, name

    def check_recalls(self, quiet=False):
        make, model, year, vin, name = self._recall_vehicle()
        for w in self.recall_links.winfo_children():
            w.destroy()
        if not vin and not (make and model and year):
            if not quiet:
                self.recall_status.configure(text="Pick the make, model and year first so the app knows which "
                                                  "recalls to look up.")
                LinkLabel(self.recall_links, "Choose vehicle", self.open_picker).pack(side="left")
            return
        self._recalls_for = (make, model, year, vin)
        self.recall_btn.set_enabled(False)
        self.recall_status.configure(text=f"Looking up recalls for {name or 'this vehicle'}…")

        def work():
            try:
                res, err = recalls.find(make, model, year, vin), None
            except Exception as e:  # noqa: BLE001 - offline or the database is busy
                res, err = None, e
            self.ui(lambda: self._show_recalls(name, vin, res, err))
        threading.Thread(target=work, daemon=True).start()

    def _show_recalls(self, name, vin, res, err):
        self.recall_btn.set_enabled(True)
        self.recall_area.clear()
        for w in self.recall_links.winfo_children():
            w.destroy()
        if err is not None:
            self._append_log(f"Recall lookup failed: {err}")
            self.recall_status.configure(text="Couldn't reach the recall database. Check the internet connection "
                                              "and try again.")
            return
        found, matched = res
        self.last_recalls = found
        if not matched:
            self.recall_status.configure(text=f"The recall database doesn't list {name} under that name. Check "
                                              "on the NHTSA website instead.")
        elif not found:
            self.recall_status.configure(text=f"No safety recalls found for {name}.")
        else:
            n = len(found)
            self.recall_status.configure(text=(
                f"{n} safety recall{'s' if n != 1 else ''} for {name}. Dealers repair recalls free, no matter "
                "how old the vehicle is. Many may already be fixed on yours: check your VIN to see which are "
                "still open."))
        LinkLabel(self.recall_links, "Check my VIN on nhtsa.gov",
                  lambda: webbrowser.open(recalls.lookup_page(vin))).pack(side="left")
        LinkLabel(self.recall_links, "Service bulletins", lambda: webbrowser.open(
            "https://www.google.com/search?q=" + urllib.parse.quote(f"{name} technical service bulletins"))).pack(
            side="left", padx=(16, 0))
        for r in found:
            card = RoundPanel(self.recall_area.inner, pad=(20, 14), radius=16)
            card.pack(fill="x", pady=(0, 10))
            box = card.inner
            tk.Label(box, text=r["component"] or "Recall", bg=C["panel"], fg=C["ink"], font=F(15, "bold"),
                     anchor="w", justify="left").pack(fill="x")
            tk.Label(box, text=f"Recall {r['campaign']}, reported {r['date']}", bg=C["panel"], fg=C["muted"],
                     font=F(12), anchor="w").pack(fill="x")
            if r["park_it"]:
                tk.Label(box, text="NHTSA says: don't drive it until this is repaired.", bg=C["panel"],
                         fg=C["red"], font=F(13, "bold"), anchor="w").pack(fill="x", pady=(4, 0))
            for heading, text in (("What's wrong", r["summary"]), ("Risk", r["consequence"]),
                                  ("Fix", r["remedy"])):
                if not text:
                    continue
                tk.Label(box, text=heading, bg=C["panel"], fg=C["ink"], font=F(13, "bold"), anchor="w").pack(
                    fill="x", pady=(6, 0))
                lbl = tk.Label(box, text=text, bg=C["panel"], fg=C["ink"], font=F(13), anchor="w", justify="left")
                lbl.pack(fill="x")
                wrap_on_resize(lbl, 60)

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

    # --- Tests page: battery test, self-test results, module info, code lookup -----------------------
    def _build_tests(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "Tests", "Deeper checks that professional scan tools do. They only read from the "
                                        "vehicle and never change anything.", icon=PAGE_ICON["Tests"])
        area = ScrollArea(page, C["page"])
        area.pack(fill="both", expand=True)
        box = area.inner
        self.tests_area = area
        self.last_results = {}  # what the tests found, for the report

        def section(icon, tint, title, text, button, command, needs_adapter=True):
            card = RoundPanel(box, pad=(22, 16), radius=20)
            card.pack(fill="x", pady=(0, 12))
            inner = card.inner
            top = tk.Frame(inner, bg=C["panel"])
            top.pack(fill="x")
            cv = tk.Canvas(top, width=54, height=54, bg=C["panel"], highlightthickness=0)
            cv.pack(side="left", padx=(0, 14))
            icons.draw(cv, icon, 27, 27, 32, TINT[tint], F(8, "bold"), halo=True)
            col = tk.Frame(top, bg=C["panel"])
            col.pack(side="left", fill="x", expand=True)
            tk.Label(col, text=title, bg=C["panel"], fg=C["ink"], font=F(16, "bold"), anchor="w").pack(fill="x")
            t = tk.Label(col, text=text, bg=C["panel"], fg=C["muted"], font=F(13), anchor="w", justify="left")
            t.pack(fill="x")
            wrap_on_resize(t, 260)
            btn = None
            if button:
                btn = PillButton(top, button, command, kind="primary")
                btn.pack(side="right", padx=(12, 0))
                if needs_adapter:
                    self.page_buttons.append(btn)
            out = tk.Frame(inner, bg=C["panel"])
            out.pack(fill="x")
            return out, btn

        self.batt_out, self.batt_btn = section(
            "gauge", "battery", "Battery and charging test",
            "Checks the battery at rest, how far it drops while starting, and whether the alternator charges at "
            "idle and at 2,000 rpm. Takes about a minute.", "Start test", self.battery_test)
        self.mode6_out, _ = section(
            "scan", "scan", "Self-test results and misfire counts",
            "The numbers behind each emissions self-test with its pass/fail limits, and misfire counts for each "
            "cylinder. Most 2008 and newer vehicles.", "Read results", self.read_self_tests)
        self.mod9_out, _ = section(
            "vehicle", "vehicle", "Module info",
            "Software calibration numbers for each computer, and how often each self-test has had a chance to "
            "run.", "Read info", self.read_module_info)
        self.lookup_out, _ = section(
            "alert", "engine", "Look up a code",
            "Find out what any code means, without the vehicle. Factory meanings use the vehicle you picked.",
            None, None, needs_adapter=False)
        row = tk.Frame(self.lookup_out, bg=C["panel"])
        row.pack(fill="x", pady=(12, 0))
        self.lookup_var = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.lookup_var, width=14, font=F(15))
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self.lookup_code())
        PillButton(row, "Look up", self.lookup_code, kind="primary").pack(side="left", padx=(10, 0))
        self.lookup_result = tk.Frame(self.lookup_out, bg=C["panel"])
        self.lookup_result.pack(fill="x")
        return page

    def _clear(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def _line(self, parent, text, bold=False, color=None, size=13, pady=(4, 0)):
        lbl = tk.Label(parent, text=text, bg=parent["bg"], fg=color or C["ink"], font=F(size, "bold" if bold else
                                                                                         "normal"),
                       anchor="w", justify="left")
        lbl.pack(fill="x", pady=pady)
        wrap_on_resize(lbl, 40)
        return lbl

    def _pill(self, parent, text, good):
        bg, fg = (C["green_soft"], C["green"]) if good else (C["red_soft"], C["red"])
        return tk.Label(parent, text=text, bg=bg, fg=fg, font=F(12, "bold"), padx=10, pady=3)

    # Code lookup
    def lookup_code(self):
        code = re.sub(r"[^A-Za-z0-9]", "", self.lookup_var.get()).upper()
        self._clear(self.lookup_result)
        if not re.fullmatch(r"[PCBU][0-9A-F]{4}", code):
            self._line(self.lookup_result, "Type a code like P0301, C0035, B1932 or U0100.", color=C["muted"],
                       pady=(10, 0))
            return
        info = describe_dtc(code, self._current_make())
        self._line(self.lookup_result, f"{code}: {info['description']}", bold=True, size=15, pady=(12, 2))
        if info.get("factory"):
            self._line(self.lookup_result, f"{info['factory']} factory meaning. It can differ a little by model and "
                                           "year.", color=C["muted"])
        if info["causes"]:
            self._line(self.lookup_result, "Common causes", bold=True, pady=(8, 0))
            self._line(self.lookup_result, info["causes"], pady=(0, 0))
        for i, step in enumerate(info.get("checks") or [], 1):
            if i == 1:
                self._line(self.lookup_result, "How to check it", bold=True, pady=(8, 0))
            self._line(self.lookup_result, f"{i}. {step}", pady=(2, 0))
        self._line(self.lookup_result, as_sentences(info["category"]), color=C["muted"], pady=(8, 0))
        row = tk.Frame(self.lookup_result, bg=C["panel"])
        row.pack(fill="x", pady=(10, 0))
        PillButton(row, "Search for repair info", lambda: self.lookup_online(code)).pack(side="left")
        PillButton(row, "Repair videos", lambda: self.lookup_online(code, videos=True)).pack(side="left",
                                                                                           padx=(10, 0))

    # Self-test results (mode $06)
    def read_self_tests(self):
        elm = self.elm
        if not elm:
            return
        self._clear(self.mode6_out)
        self._line(self.mode6_out, "Reading self-test results…", color=C["muted"], pady=(12, 0))

        def work():
            return advanced.self_tests(elm, lambda i, n: self.ui(
                lambda: self.set_step(f"Reading self-test results ({i + 1} of {n})…", (i + 1) / max(n, 1))))

        def done(results):
            self.last_results["self_tests"] = results
            self._show_self_tests(results)

        def failed(err):
            self._clear(self.mode6_out)
            self._line(self.mode6_out, str(err), color=C["muted"], pady=(12, 0))
        self.run_bg(work, done, "Reading self-test results…", on_error=failed, quiet_errors=True)

    def _show_self_tests(self, results):
        out = self.mode6_out
        self._clear(out)
        if not results:
            self._line(out, "The vehicle didn't report any self-test results. Some only report them after a full "
                            "drive cycle.", color=C["muted"], pady=(12, 0))
            return
        failed = [r for r in results if not r["passed"]]
        self._line(out, f"{len(results) - len(failed)} of {len(results)} test results within limits.", bold=True,
                   color=C["red"] if failed else C["green"], size=15, pady=(14, 4))
        mis = advanced.misfire_summary(results)
        if mis:
            self._line(out, "Misfires per cylinder", bold=True, pady=(8, 2))
            worst = max([1] + [v for pair in mis.values() for v in pair if v is not None])
            grid = tk.Frame(out, bg=C["panel"])
            grid.pack(fill="x")
            for i, (cyl, (cur, avg)) in enumerate(mis.items()):
                tk.Label(grid, text=f"Cylinder {cyl}", bg=C["panel"], fg=C["ink"], font=F(13)).grid(
                    row=i, column=0, sticky="w", pady=2)
                bar = tk.Canvas(grid, width=260, height=16, bg=C["panel"], highlightthickness=0)
                bar.grid(row=i, column=1, sticky="w", padx=12)
                icons.rounded_rect(bar, 1, 2, 259, 14, 6, fill=C["off_soft"], outline="")
                n = cur if cur is not None else avg or 0
                if n:
                    color = C["red"] if n >= 10 else C["amber"]
                    icons.rounded_rect(bar, 1, 2, max(14, 258 * n / worst), 14, 6, fill=color, outline="")
                txt = (f"{cur:.0f} this drive" if cur is not None else "") + \
                      (f", {avg:.0f} average" if avg is not None else "")
                tk.Label(grid, text=txt.strip(", ") or "-", bg=C["panel"], fg=C["muted"], font=F(12)).grid(
                    row=i, column=2, sticky="w")
            self._line(out, "A few counts now and then is normal. One cylinder with many more than the others "
                            "points to that cylinder's plug, coil or injector.", color=C["muted"], size=12)
        groups = {}
        for r in results:
            if r["misfire"] is None:
                groups.setdefault(r["name"], []).append(r)
        if groups:
            self._line(out, "All test results", bold=True, pady=(12, 2))
        for name, rows in groups.items():
            row = tk.Frame(out, bg=C["panel"])
            row.pack(fill="x", pady=(6, 0))
            ok = all(r["passed"] for r in rows)
            self._pill(row, "Passed" if ok else "Failed", ok).pack(side="right")
            tk.Label(row, text=name, bg=C["panel"], fg=C["ink"], font=F(14, "bold"), anchor="w").pack(side="left")
            for r in rows:
                v = lambda x: f"{x:.3f}".rstrip("0").rstrip(".") if isinstance(x, float) else str(x)  # noqa: E731
                unit = f" {r['unit']}" if r["unit"] else ""
                self._line(out, f"Test ${r['tid']:02X}: {v(r['value'])}{unit}   (allowed {v(r['low'])} to "
                                f"{v(r['high'])}{unit})", color=C["ink"] if r["passed"] else C["red"], size=12,
                           pady=(1, 0))

    # Module info (mode $09)
    def read_module_info(self):
        elm = self.elm
        if not elm:
            return

        def done(info):
            self.last_results["modules"] = info
            out = self.mod9_out
            self._clear(out)
            if not info:
                self._line(out, "The vehicle didn't report module info.", color=C["muted"], pady=(12, 0))
                return
            for ecu, d in info.items():
                name = d["name"] or ECU_NAMES.get(ecu, f"Module {ecu}")
                self._line(out, name, bold=True, size=15, pady=(14, 2))
                for cal in d["calids"]:
                    self._line(out, f"Calibration (software) ID: {cal}", pady=(1, 0))
                for cvn in d["cvns"]:
                    self._line(out, f"Calibration check number: {cvn}", pady=(1, 0))
                for label, val in d["usage"]:
                    self._line(out, f"{label}: {val}", pady=(1, 0))
            self._line(out, "Dealers and parts stores use the calibration ID to see if a software update exists. A "
                            "self-test that rarely runs can explain a 'not ready' smog check.", color=C["muted"],
                       size=12, pady=(10, 0))
        self.run_bg(lambda: advanced.module_info(elm), done, "Reading module info…")

    # Battery and charging test
    def battery_test(self):
        elm = self.elm
        if not elm:
            return
        out = self.batt_out
        self._clear(out)
        self.batt = {}

        def rpm():
            d = elm.query_pid(1, 0x0C)
            return (d[0] * 256 + d[1]) / 4 if d and len(d) >= 2 else None

        def volts():
            try:
                return float(elm.voltage().upper().rstrip("V").strip())
            except ValueError:
                return None

        def step1():
            r = rpm()
            if r and r > 300:
                return "running"
            vs = [v for v in (volts() for _ in range(5)) if v]
            return max(vs) if vs else None

        def after1(v):
            self._clear(out)
            if v == "running":
                self._line(out, "Turn the engine OFF (key ON is fine) and click Start test again. The battery is "
                                "checked at rest first.", color=C["amber_ink"], pady=(12, 0))
                return
            if v is None:
                self._line(out, "Couldn't read the voltage from the adapter.", color=C["muted"], pady=(12, 0))
                return
            self.batt["rest"] = v
            self._batt_row("Battery at rest", f"{v:.2f} V", *(
                ("Fully charged", True) if v >= 12.55 else ("Good", True) if v >= 12.35 else
                ("Half charged - charge it", False) if v >= 12.0 else ("Low - charge or replace", False)))
            self._line(out, "Now start the engine. Click Ready, then start it within 10 seconds.", bold=True,
                       pady=(10, 4))
            b = PillButton(out, "Ready", lambda: (b.destroy(), self.run_bg(step2, after2, "Start the engine now…")),
                           kind="primary")
            b.pack(anchor="w")

        def step2():
            low, end, started = 99.0, time.time() + 15, False
            while time.time() < end:
                v = volts()
                if v:
                    low = min(low, v)
                    if low < self.batt["rest"] - 0.4 and v > 13.0:
                        started = True
                        break
            return low, started

        def after2(res):
            low, started = res
            if not started:
                self._line(out, "Didn't see the engine start. If it did start, the adapter may have missed the dip; "
                                "otherwise try again.", color=C["amber_ink"])
            if low < 50:
                self.batt["crank"] = low
                self._batt_row("Lowest while starting", f"{low:.2f} V", *(
                    ("Strong", True) if low >= 10.0 else ("OK", True) if low >= 9.6 else
                    ("Weak - battery or starter", False)))
            time.sleep(0)
            self.run_bg(step3, after3, "Checking charging at idle…")

        def step3():
            time.sleep(4)
            vs = [v for v in (volts() for _ in range(6)) if v]
            return sum(vs) / len(vs) if vs else None

        def charge_verdict(v):
            return (("Charging normally", True) if 13.4 <= v <= 14.9 else
                    ("Overcharging - check the alternator", False) if v > 14.9 else
                    ("Not charging enough - check alternator, belt and cables", False))

        def after3(v):
            if v is None:
                return
            self.batt["idle"] = v
            self._batt_row("Charging at idle", f"{v:.2f} V", *charge_verdict(v))
            self._line(out, "Last step: hold the engine at about 2,000 rpm (in Park or Neutral), then click Ready.",
                       bold=True, pady=(10, 4))
            b = PillButton(out, "Ready", lambda: (b.destroy(), self.run_bg(step4, after4, "Hold about 2,000 rpm…")),
                           kind="primary")
            b.pack(anchor="w")

        def step4():
            vs, end = [], time.time() + 12
            while time.time() < end and len(vs) < 5:
                r = rpm()
                if r and r > 1500:
                    v = volts()
                    if v:
                        vs.append(v)
            return sum(vs) / len(vs) if vs else None

        def after4(v):
            if v is None:
                self._line(out, "Didn't see the engine above 1,500 rpm, so this step was skipped.",
                           color=C["muted"])
            else:
                self.batt["high"] = v
                self._batt_row("Charging at 2,000 rpm", f"{v:.2f} V", *charge_verdict(v))
            self._line(out, "Done. You can let the engine idle again. Parts stores can do a load test if anything "
                            "here looks weak.", color=C["muted"], size=12, pady=(10, 0))
            self.last_results["battery"] = dict(self.batt)

        if self.live_running:
            self.live_stop.set()
        self.run_bg(step1, after1, "Checking the battery…")

    def _batt_row(self, label, value, verdict, good):
        row = tk.Frame(self.batt_out, bg=C["panel"])
        row.pack(fill="x", pady=(10, 0))
        tk.Label(row, text=label, bg=C["panel"], fg=C["ink"], font=F(14), width=22, anchor="w").pack(side="left")
        tk.Label(row, text=value, bg=C["panel"], fg=C["ink"], font=F(16, "bold"), width=9, anchor="w").pack(
            side="left")
        self._pill(row, verdict, good).pack(side="left")
        self.batt.setdefault("verdicts", []).append((label, value, verdict, good))

    # --- History page --------------------------------------------------------------------------------
    def _save_history(self):
        v = self.vehicle or {}
        vin = v.get("vin", "")
        vin = vin if vin and vin != "-" else ""
        name = self.vehicle_lbl["text"] or v.get("title", "")
        try:
            history.add(vin, name, self.scan_kind, self.items, self.mil_on)
        except Exception as e:  # noqa: BLE001 - history must never break a scan
            self._append_log(f"Couldn't save scan history: {e}")

    def _build_history(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "History", "Every scan is saved here by vehicle, so you can see what came back "
                                          "after a repair.", icon=PAGE_ICON["History"])
        self.history_area = ScrollArea(page, C["page"])
        self.history_area.pack(fill="both", expand=True)
        return page

    def refresh_history(self):
        area = self.history_area
        area.clear()
        groups = history.by_vehicle()
        if not groups:
            self._empty_card(area.inner, PAGE_ICON["History"], "No scans saved yet",
                             "Scans are saved here automatically after each scan.", None)
            return
        for name, scans in groups:
            tk.Label(area.inner, text=name, bg=C["page"], fg=C["ink"], font=F(18, "bold"), anchor="w").pack(
                fill="x", pady=(8, 6))
            for i, sc in enumerate(scans[:15]):
                card = RoundPanel(area.inner, pad=(20, 12), radius=16)
                card.pack(fill="x", pady=(0, 8))
                box = card.inner
                top = tk.Frame(box, bg=C["panel"])
                top.pack(fill="x")
                when = datetime.datetime.fromisoformat(sc["when"]).strftime("%b %d, %Y at %I:%M %p")
                what = {"engine": "Engine codes", "safety": "ABS and airbag"}.get(sc["kind"], "Full scan")
                tk.Label(top, text=f"{when} · {what}", bg=C["panel"], fg=C["ink"], font=F(14, "bold"),
                         anchor="w").pack(side="left")
                n = len(sc["codes"])
                self._pill(top, f"{n} code{'s' if n != 1 else ''}" if n else "No codes", not n).pack(side="right")
                if i + 1 < len(scans):
                    new, gone = history.changes(sc, scans[i + 1])
                    bits = []
                    if new:
                        bits.append("New since the scan before: " + ", ".join(new))
                    if gone:
                        bits.append("Gone since the scan before: " + ", ".join(gone))
                    if bits:
                        self._line(box, ". ".join(bits) + ".", color=C["amber_ink"] if new else C["green"], size=12)
                for c in sc["codes"][:12]:
                    self._line(box, f"{c['code']}  {c['text']}  ({c['module']})", size=12, pady=(1, 0))
                if n > 12:
                    self._line(box, f"…and {n - 12} more", color=C["muted"], size=12, pady=(1, 0))
        bar = tk.Frame(area.inner, bg=C["page"])
        bar.pack(fill="x", pady=(8, 0))
        LinkLabel(bar, "Clear history", self._clear_history).pack(side="left")

    def _clear_history(self):
        if messagebox.askyesno(APP_NAME, "Delete all saved scans? This can't be undone."):
            history.clear()
            self.refresh_history()

    # --- Service page: relearns, resets and bleeding ------------------------------------------------
    def _build_service(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "Service", "Relearns, resets and brake bleeding you can do by hand. Click one to see "
                                          "the steps.", icon=PAGE_ICON["Service"])
        self.service_for = tk.Label(page, text="", bg=C["page"], fg=C["muted"], font=F(13), anchor="w")
        self.service_for.pack(fill="x", pady=(0, 10))
        self.service_area = ScrollArea(page, C["page"])
        self.service_area.pack(fill="both", expand=True)
        self._service_shown = None
        return page

    def refresh_service(self):
        make = self._current_make()
        fam = maker_codes.family(make)
        if self._service_shown == fam and self.service_area.inner.winfo_children():
            return
        self._service_shown = fam
        ch = self.chosen or {}
        name = " ".join(str(x) for x in (ch.get("year"), ch.get("make"), ch.get("model")) if x) or make
        self.service_for.configure(
            text=f"Showing guides for {name}, plus ones for most vehicles." if fam else
            "Showing guides for all vehicles. Pick your vehicle on Home to see only the ones for it.")
        self.service_area.clear()
        for g in service_guides.for_family(fam):
            self._service_card(self.service_area.inner, g)

    def _service_card(self, parent, g):
        card = RoundPanel(parent, pad=(20, 14), radius=16)
        card.pack(fill="x", pady=(0, 10))
        box = card.inner
        top = tk.Frame(box, bg=C["panel"])
        top.pack(fill="x")
        title = tk.Label(top, text=g["title"], bg=C["panel"], fg=C["ink"], font=F(15, "bold"), anchor="w")
        title.pack(side="left")
        arrow = tk.Label(top, text="Show steps", bg=C["panel"], fg=C["muted"], font=F(12, "bold"))
        arrow.pack(side="right")
        sub = tk.Label(box, text=g["applies"] + ".", bg=C["panel"], fg=C["muted"], font=F(12), anchor="w",
                       justify="left")
        sub.pack(fill="x", pady=(2, 0))
        wrap_on_resize(sub, 60)
        details = tk.Frame(box, bg=C["panel"])
        state = {"open": False}

        def toggle():
            state["open"] = not state["open"]
            arrow.configure(text="Hide steps" if state["open"] else "Show steps")
            if not state["open"]:
                details.pack_forget()
                return
            for w in details.winfo_children():
                w.destroy()
            wrap = max(300, box.winfo_width() - 60)
            tk.Label(details, text="You'll need: " + g["needs"], bg=C["panel"], fg=C["ink"], font=F(13),
                     anchor="w", justify="left", wraplength=wrap).pack(fill="x", pady=(0, 6))
            steps = tk.Frame(details, bg=C["panel"])
            steps.pack(fill="x")
            steps.columnconfigure(1, weight=1)
            for i, step in enumerate(g["steps"], 1):
                dot = tk.Canvas(steps, width=26, height=26, bg=C["panel"], highlightthickness=0)
                dot.grid(row=i, column=0, sticky="nw", pady=3)
                dot.create_oval(2, 2, 24, 24, fill=icons.blend("#FFFFFF", TINT["service"], 0.15), outline="")
                dot.create_text(13, 13, text=str(i), fill=TINT["service"], font=F(12, "bold"))
                tk.Label(steps, text=step, bg=C["panel"], fg=C["ink"], font=F(13), anchor="w", justify="left",
                         wraplength=wrap - 40).grid(row=i, column=1, sticky="w", padx=(10, 0), pady=3)
            if g.get("note"):
                tk.Label(details, text=g["note"], bg=C["amber_soft"], fg=C["ink"], font=F(13), anchor="w",
                         justify="left", wraplength=wrap - 20, padx=12, pady=8).pack(fill="x", pady=(10, 0))
            details.pack(fill="x", pady=(10, 0))

        card.toggle = toggle
        bind_click(card, toggle, also=(box, top, title, arrow, sub))
        for w in (card, box, top, title, arrow, sub):
            w.configure(cursor="hand2")

    # --- Help page --------------------------------------------------------------------------------
    def _build_help(self):
        page = tk.Frame(self.main, bg=C["page"])
        self._page_title(page, "Help", "Getting codes off your vehicle in five steps.", icon=PAGE_ICON["Help"])
        steps = [
            "Plug the adapter into the OBD port under the dashboard, near the steering column.",
            "Turn the key to ON. The engine can be off or running.",
            "On Home, click Engine codes, ABS and airbag, or Full scan. The app finds the adapter by itself.",
            "Click any problem to see what it means, how urgent it is, and what usually fixes it.",
            "To clear codes, turn the engine off and leave the key on first.",
        ]
        card = RoundPanel(page, pad=(18, 12), radius=22)
        card.pack(fill="x")
        box = card.inner
        box.columnconfigure(1, weight=1)
        colors = [TINT[k] for k in ("vehicle", "engine", "scan", "safety", "smog")]
        for i, s in enumerate(steps, 1):
            dot = tk.Canvas(box, width=34, height=34, bg=C["panel"], highlightthickness=0)
            dot.grid(row=i, column=0, sticky="nw", pady=5)
            col = colors[(i - 1) % len(colors)]
            dot.create_oval(2, 2, 32, 32, fill=icons.blend("#FFFFFF", col, 0.15), outline="")
            dot.create_text(17, 17, text=str(i), fill=col, font=F(14, "bold"))
            lbl = tk.Label(box, text=s, bg=C["panel"], fg=C["ink"], font=F(14), anchor="w", justify="left")
            lbl.grid(row=i, column=1, sticky="w", padx=(12, 0), pady=5)
            wrap_on_resize(lbl, 120)
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
        self.help_update_btn = PillButton(ver, "Update now", self.install_update, kind="primary")
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
    def lookup_online(self, code, videos=False):
        base = code.split("-")[0]
        ch = getattr(self, "chosen", None) or {}
        car = " ".join(str(x) for x in (ch.get("year"), ch.get("make"), ch.get("model")) if x) or self._current_make()
        if videos:
            webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(f"{base} {car} fix"))
            return
        q = f"{base} {car} code" if car else f"{base} code meaning"
        webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(q))

    def save_report(self):
        """Save a printable health report (a web page) and open it in the browser."""
        today = datetime.date.today().isoformat()
        path = filedialog.asksaveasfilename(defaultextension=".html", initialfile=f"vehicle-report-{today}.html",
                                            filetypes=[("Web page", "*.html")])
        if not path:
            return
        items = []
        for it in self.items:
            items.append(dict(it, words=LEVELS[it["level"]][3],
                              why=it.get("why") or why_it_matters(it["code"], it["status"], it["module"])))
        rows = None
        if self.readiness and len(self.readiness) >= 4:
            rows = decode_readiness(self.readiness)[3]
        tests = self.last_results.get("self_tests")
        data = {"vehicle": self.vehicle, "items": items, "scanned": self.scanned, "mil_on": self.mil_on,
                "readiness_rows": rows, "self_tests": tests,
                "misfires": advanced.misfire_summary(tests) if tests else None,
                "modules": self.last_results.get("modules"), "battery": self.last_results.get("battery"),
                "recalls": getattr(self, "last_recalls", None)}
        with open(path, "w", encoding="utf-8") as f:
            f.write(report.build(data))
        self.step_lbl.configure(text=f"Report saved to {path}")
        webbrowser.open("file://" + urllib.parse.quote(os.path.abspath(path)))

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
