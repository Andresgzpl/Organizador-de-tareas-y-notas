"""
Andrés Task Manager — Premium UI
================================
Gestor personal de tareas y notas con una interfaz desktop oscura inspirada
en productos SaaS modernos.

La aplicación conserva la lógica original de tareas, notas y persistencia
JSON. La capa visual se ha rediseñado con Tkinter/ttk y componentes Canvas
reutilizables, sin dependencias externas.

Ejecución:
    python app_premium.py
"""

from __future__ import annotations

import json
import uuid
import tkinter as tk
import tkinter.font as tkfont
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional


# ======================================================================
# TEMA VISUAL
# ======================================================================


class Theme:
    """Sistema visual centralizado para la interfaz premium."""

    BG = "#08080D"
    SIDEBAR = "#0B0B12"
    SURFACE = "#13131D"
    SURFACE_HOVER = "#181824"
    SURFACE_ALT = "#1A1A27"
    INPUT = "#171722"
    BORDER = "#292938"
    BORDER_SOFT = "#20202D"
    BORDER_ACTIVE = "#6040A8"

    TEXT = "#F7F5FC"
    TEXT_SOFT = "#D7D5E2"
    TEXT_MUTED = "#A3A1B2"
    TEXT_DIM = "#6F6D80"

    PRIMARY = "#7C3AED"
    PRIMARY_HOVER = "#8B5CF6"
    PRIMARY_ACTIVE = "#6D28D9"
    PRIMARY_SOFT = "#25173B"
    PRIMARY_SOFT_HOVER = "#30204A"
    ACCENT = "#A855F7"
    LAVENDER = "#C4B5FD"
    LAVENDER_LIGHT = "#DDD6FE"

    SUCCESS = "#34D399"
    SUCCESS_SOFT = "#123128"
    WARNING = "#FBBF24"
    WARNING_SOFT = "#342A12"
    DANGER = "#FB7185"
    DANGER_HOVER = "#F43F5E"
    DANGER_SOFT = "#351820"

    SELECT_BG = "#2B1B46"
    SHADOW = "#050508"

    FONT_FAMILY = "Segoe UI"
    FONT = (FONT_FAMILY, 10)
    FONT_BOLD = (FONT_FAMILY, 10, "bold")
    FONT_SMALL = (FONT_FAMILY, 9)
    FONT_SMALL_BOLD = (FONT_FAMILY, 9, "bold")
    FONT_TINY = (FONT_FAMILY, 8)
    FONT_TITLE = (FONT_FAMILY, 24, "bold")
    FONT_HERO = (FONT_FAMILY, 20, "bold")
    FONT_HEADING = (FONT_FAMILY, 14, "bold")
    FONT_CARD_VALUE = (FONT_FAMILY, 23, "bold")
    FONT_BUTTON = (FONT_FAMILY, 10, "bold")


PRIORITIES = ["Alta", "Media", "Baja"]
PRIORITY_ORDER = {"Alta": 0, "Media": 1, "Baja": 2}
PRIORITY_COLORS = {
    "Alta": Theme.DANGER,
    "Media": Theme.WARNING,
    "Baja": Theme.SUCCESS,
}


# ======================================================================
# HELPERS GRÁFICOS
# ======================================================================


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    **kwargs,
):
    """Dibuja un rectángulo suavemente redondeado en un Canvas."""
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    return canvas.create_polygon(
        points,
        smooth=True,
        splinesteps=36,
        **kwargs,
    )


class ModernButton(tk.Canvas):
    """Botón Canvas redondeado con hover, pressed y foco de teclado."""

    STYLES = {
        "primary": {
            "bg": Theme.PRIMARY,
            "hover": Theme.PRIMARY_HOVER,
            "pressed": Theme.PRIMARY_ACTIVE,
            "fg": "#FFFFFF",
            "border": Theme.PRIMARY,
        },
        "secondary": {
            "bg": Theme.SURFACE_ALT,
            "hover": "#222233",
            "pressed": "#27273A",
            "fg": Theme.TEXT_SOFT,
            "border": Theme.BORDER,
        },
        "ghost": {
            "bg": Theme.SURFACE,
            "hover": Theme.SURFACE_HOVER,
            "pressed": Theme.SURFACE_ALT,
            "fg": Theme.TEXT_SOFT,
            "border": Theme.BORDER_SOFT,
        },
        "danger": {
            "bg": Theme.DANGER_SOFT,
            "hover": "#45202A",
            "pressed": "#501E2A",
            "fg": Theme.DANGER,
            "border": "#5A2632",
        },
    }

    def __init__(
        self,
        master,
        text: str,
        command: Callable[[], None],
        *,
        style: str = "secondary",
        icon: str = "",
        width: Optional[int] = None,
        height: int = 40,
        radius: int = 11,
        font=None,
        padx: int = 16,
    ):
        self.text = text
        self.command = command
        self.kind = style if style in self.STYLES else "secondary"
        self.icon = icon
        self.radius = radius
        self._hovered = False
        self._pressed = False
        self._focused = False
        self._enabled = True
        self._font = font or Theme.FONT_BUTTON

        font_obj = tkfont.Font(font=self._font)
        measured = font_obj.measure(text)
        icon_space = font_obj.measure(icon + " ") if icon else 0
        request_width = width or max(92, measured + icon_space + padx * 2)

        try:
            parent_bg = master.cget("bg")
        except tk.TclError:
            parent_bg = Theme.BG

        super().__init__(
            master,
            width=request_width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            relief="flat",
            cursor="hand2",
            takefocus=True,
        )

        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Return>", self._on_keyboard)
        self.bind("<space>", self._on_keyboard)
        self.after_idle(self._draw)

    def _palette(self):
        return self.STYLES[self.kind]

    def _draw(self):
        self.delete("all")
        width = max(2, self.winfo_width())
        height = max(2, self.winfo_height())
        palette = self._palette()

        if not self._enabled:
            fill = Theme.SURFACE
            fg = Theme.TEXT_DIM
            border = Theme.BORDER_SOFT
        elif self._pressed:
            fill = palette["pressed"]
            fg = palette["fg"]
            border = palette["border"]
        elif self._hovered:
            fill = palette["hover"]
            fg = palette["fg"]
            border = Theme.BORDER_ACTIVE if self.kind != "primary" else palette["hover"]
        else:
            fill = palette["bg"]
            fg = palette["fg"]
            border = palette["border"]

        if self._focused and self._enabled:
            draw_rounded_rect(
                self,
                1,
                1,
                width - 1,
                height - 1,
                self.radius + 1,
                fill=Theme.PRIMARY_SOFT,
                outline=Theme.LAVENDER,
                width=1,
            )
            inset = 3
        else:
            inset = 1

        draw_rounded_rect(
            self,
            inset,
            inset,
            width - inset,
            height - inset,
            self.radius,
            fill=fill,
            outline=border,
            width=1,
        )

        label = f"{self.icon}  {self.text}" if self.icon else self.text
        self.create_text(
            width / 2,
            height / 2,
            text=label,
            fill=fg,
            font=self._font,
            anchor="center",
        )

    def _on_enter(self, _event):
        if self._enabled:
            self._hovered = True
            self._draw()

    def _on_leave(self, _event):
        self._hovered = False
        self._pressed = False
        self._draw()

    def _on_press(self, _event):
        if self._enabled:
            self.focus_set()
            self._pressed = True
            self._draw()

    def _on_release(self, event):
        if not self._enabled:
            return
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        was_pressed = self._pressed
        self._pressed = False
        self._draw()
        if was_pressed and inside:
            self.command()

    def _on_focus_in(self, _event):
        self._focused = True
        self._draw()

    def _on_focus_out(self, _event):
        self._focused = False
        self._draw()

    def _on_keyboard(self, _event):
        if self._enabled:
            self.command()
            return "break"
        return None

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()


class NavButton(tk.Canvas):
    """Entrada reutilizable para la navegación lateral."""

    def __init__(self, master, text, icon, command, width=198, height=46):
        self.text = text
        self.icon = icon
        self.command = command
        self.active = False
        self.hovered = False

        super().__init__(
            master,
            width=width,
            height=height,
            bg=Theme.SIDEBAR,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=True,
        )
        self.bind("<Configure>", lambda _e: self.draw())
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda _e: self.command())
        self.bind("<Return>", lambda _e: self.command())
        self.bind("<space>", lambda _e: self.command())
        self.bind("<FocusIn>", lambda _e: self.draw())
        self.bind("<FocusOut>", lambda _e: self.draw())
        self.after_idle(self.draw)

    def _set_hover(self, value):
        self.hovered = value
        self.draw()

    def set_active(self, active):
        self.active = active
        self.draw()

    def draw(self):
        self.delete("all")
        width = max(2, self.winfo_width())
        height = max(2, self.winfo_height())

        if self.active:
            fill = Theme.PRIMARY_SOFT
            outline = Theme.BORDER_ACTIVE
            icon_fg = Theme.LAVENDER_LIGHT
            text_fg = Theme.TEXT
        elif self.hovered or self.focus_get() == self:
            fill = Theme.SURFACE_HOVER
            outline = Theme.BORDER_SOFT
            icon_fg = Theme.LAVENDER
            text_fg = Theme.TEXT_SOFT
        else:
            fill = Theme.SIDEBAR
            outline = Theme.SIDEBAR
            icon_fg = Theme.TEXT_MUTED
            text_fg = Theme.TEXT_MUTED

        draw_rounded_rect(
            self,
            2,
            2,
            width - 2,
            height - 2,
            12,
            fill=fill,
            outline=outline,
            width=1,
        )

        if self.active:
            draw_rounded_rect(
                self,
                4,
                12,
                8,
                height - 12,
                2,
                fill=Theme.ACCENT,
                outline=Theme.ACCENT,
            )

        self.create_text(25, height / 2, text=self.icon, fill=icon_fg,
                         font=(Theme.FONT_FAMILY, 14, "bold"), anchor="center")
        self.create_text(47, height / 2, text=self.text, fill=text_fg,
                         font=Theme.FONT_BOLD if self.active else Theme.FONT,
                         anchor="w")


class RoundedSurface(tk.Canvas):
    """Panel redondeado que expone un Frame interior para componer widgets."""

    def __init__(
        self,
        master,
        *,
        fill=Theme.SURFACE,
        border=Theme.BORDER_SOFT,
        radius=16,
        padding=18,
        height=120,
        shadow=True,
        hoverable=False,
    ):
        self.fill_color = fill
        self.border_color = border
        self.radius = radius
        self.padding = padding
        self.shadow = shadow
        self.hoverable = hoverable
        self.hovered = False

        try:
            parent_bg = master.cget("bg")
        except tk.TclError:
            parent_bg = Theme.BG

        super().__init__(
            master,
            bg=parent_bg,
            height=height,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.content = tk.Frame(self, bg=fill)
        self._content_window = self.create_window(
            padding,
            padding,
            anchor="nw",
            window=self.content,
        )

        self.bind("<Configure>", self._redraw)
        if hoverable:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event):
        self.hovered = True
        self._redraw()

    def _on_leave(self, _event):
        self.hovered = False
        self._redraw()

    def _redraw(self, _event=None):
        width = max(2, self.winfo_width())
        height = max(2, self.winfo_height())
        self.delete("surface")

        if self.shadow:
            draw_rounded_rect(
                self,
                4,
                6,
                width - 4,
                height - 2,
                self.radius,
                fill=Theme.SHADOW,
                outline=Theme.SHADOW,
                tags="surface",
            )

        outline = Theme.BORDER_ACTIVE if self.hovered else self.border_color
        draw_rounded_rect(
            self,
            2,
            2,
            width - 4,
            height - 5,
            self.radius,
            fill=self.fill_color,
            outline=outline,
            width=1,
            tags="surface",
        )
        self.tag_lower("surface")

        usable_w = max(1, width - self.padding * 2 - 5)
        usable_h = max(1, height - self.padding * 2 - 7)
        self.coords(self._content_window, self.padding, self.padding)
        self.itemconfigure(self._content_window, width=usable_w, height=usable_h)


class StatCard(tk.Canvas):
    """Tarjeta compacta de estadística con hover y acento visual."""

    def __init__(self, master, label, icon, accent, *, height=118):
        self.label = label
        self.icon = icon
        self.accent = accent
        self.value = "0"
        self.meta = ""
        self.hovered = False

        try:
            parent_bg = master.cget("bg")
        except tk.TclError:
            parent_bg = Theme.BG

        super().__init__(
            master,
            bg=parent_bg,
            height=height,
            highlightthickness=0,
            bd=0,
            cursor="arrow",
        )
        self.bind("<Configure>", lambda _e: self.draw())
        self.bind("<Enter>", lambda _e: self._hover(True))
        self.bind("<Leave>", lambda _e: self._hover(False))
        self.after_idle(self.draw)

    def _hover(self, value):
        self.hovered = value
        self.draw()

    def set_value(self, value, meta=""):
        self.value = str(value)
        self.meta = meta
        self.draw()

    def draw(self):
        self.delete("all")
        width = max(2, self.winfo_width())
        height = max(2, self.winfo_height())
        outline = Theme.BORDER_ACTIVE if self.hovered else Theme.BORDER_SOFT

        draw_rounded_rect(
            self,
            2,
            2,
            width - 3,
            height - 4,
            16,
            fill=Theme.SURFACE,
            outline=outline,
            width=1,
        )
        # Halo/chip de acento
        draw_rounded_rect(
            self,
            18,
            17,
            52,
            51,
            10,
            fill=Theme.PRIMARY_SOFT if self.accent in (Theme.PRIMARY, Theme.ACCENT) else Theme.SURFACE_ALT,
            outline=Theme.BORDER_SOFT,
            width=1,
        )
        self.create_text(35, 34, text=self.icon, fill=self.accent,
                         font=(Theme.FONT_FAMILY, 14, "bold"))

        self.create_text(64, 25, text=self.label, fill=Theme.TEXT_MUTED,
                         font=Theme.FONT_SMALL, anchor="w")
        self.create_text(18, 78, text=self.value, fill=Theme.TEXT,
                         font=Theme.FONT_CARD_VALUE, anchor="w")
        if self.meta:
            self.create_text(width - 18, 84, text=self.meta, fill=self.accent,
                             font=Theme.FONT_SMALL_BOLD, anchor="e")


class ModernEntry(tk.Canvas):
    """Entry visualmente consistente con borde redondeado y focus morado."""

    def __init__(
        self,
        master,
        *,
        textvariable=None,
        width=240,
        height=40,
        show=None,
    ):
        self._focused = False
        try:
            parent_bg = master.cget("bg")
        except tk.TclError:
            parent_bg = Theme.BG

        super().__init__(
            master,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
        )
        self.entry = tk.Entry(
            self,
            textvariable=textvariable,
            bg=Theme.INPUT,
            fg=Theme.TEXT,
            insertbackground=Theme.LAVENDER_LIGHT,
            selectbackground=Theme.PRIMARY,
            selectforeground="#FFFFFF",
            relief="flat",
            bd=0,
            font=Theme.FONT,
            show=show or "",
        )
        self._entry_window = self.create_window(
            12,
            height / 2,
            anchor="w",
            window=self.entry,
        )
        self.bind("<Configure>", self._draw)
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.after_idle(self._draw)

    def _focus_in(self, _event):
        self._focused = True
        self._draw()

    def _focus_out(self, _event):
        self._focused = False
        self._draw()

    def _draw(self, _event=None):
        tk.Canvas.delete(self, "field")
        width = max(2, self.winfo_width())
        height = max(2, self.winfo_height())
        draw_rounded_rect(
            self,
            1,
            1,
            width - 1,
            height - 1,
            10,
            fill=Theme.INPUT,
            outline=Theme.ACCENT if self._focused else Theme.BORDER,
            width=1,
            tags="field",
        )
        self.tag_lower("field")
        self.coords(self._entry_window, 12, height / 2)
        self.itemconfigure(self._entry_window, width=max(1, width - 24), height=max(22, height - 12))

    def get(self):
        return self.entry.get()

    def insert(self, index, value):
        self.entry.insert(index, value)

    def delete(self, first, last=None):
        self.entry.delete(first, last)

    def focus_set(self):
        self.entry.focus_set()


class DonutChart(tk.Canvas):
    """Indicador circular del progreso de tareas."""

    def __init__(self, master, size=154):
        self.progress = 0.0
        super().__init__(
            master,
            width=size,
            height=size,
            bg=Theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self.bind("<Configure>", lambda _e: self.draw())
        self.after_idle(self.draw)

    def set_progress(self, value):
        self.progress = max(0.0, min(1.0, float(value)))
        self.draw()

    def draw(self):
        self.delete("all")
        width = max(40, self.winfo_width())
        height = max(40, self.winfo_height())
        size = min(width, height) - 24
        x1 = (width - size) / 2
        y1 = (height - size) / 2
        x2 = x1 + size
        y2 = y1 + size
        line_width = max(9, int(size * 0.09))

        self.create_arc(x1, y1, x2, y2, start=90, extent=-359.9,
                        style="arc", outline=Theme.SURFACE_ALT, width=line_width)
        if self.progress > 0:
            self.create_arc(x1, y1, x2, y2, start=90,
                            extent=-359.9 * self.progress, style="arc",
                            outline=Theme.ACCENT, width=line_width)
        pct = int(round(self.progress * 100))
        self.create_text(width / 2, height / 2 - 5, text=f"{pct}%",
                         fill=Theme.TEXT, font=(Theme.FONT_FAMILY, 22, "bold"))
        self.create_text(width / 2, height / 2 + 23, text="completado",
                         fill=Theme.TEXT_MUTED, font=Theme.FONT_SMALL)


class PriorityBreakdown(tk.Canvas):
    """Barras simples para visualizar la distribución de pendientes."""

    def __init__(self, master, height=126):
        self.counts = {"Alta": 0, "Media": 0, "Baja": 0}
        super().__init__(master, height=height, bg=Theme.SURFACE,
                         highlightthickness=0, bd=0)
        self.bind("<Configure>", lambda _e: self.draw())
        self.after_idle(self.draw)

    def set_counts(self, counts):
        self.counts = {key: int(counts.get(key, 0)) for key in PRIORITIES}
        self.draw()

    def draw(self):
        self.delete("all")
        width = max(120, self.winfo_width())
        max_count = max(max(self.counts.values()), 1)
        rows = [("Alta", 24), ("Media", 62), ("Baja", 100)]

        for label, y in rows:
            count = self.counts[label]
            color = PRIORITY_COLORS[label]
            self.create_text(0, y, text=label, anchor="w", fill=Theme.TEXT_MUTED,
                             font=Theme.FONT_SMALL)
            self.create_text(width - 2, y, text=str(count), anchor="e",
                             fill=Theme.TEXT_SOFT, font=Theme.FONT_SMALL_BOLD)
            track_x1 = 54
            track_x2 = max(track_x1 + 20, width - 34)
            track_y1 = y - 5
            track_y2 = y + 5
            draw_rounded_rect(self, track_x1, track_y1, track_x2, track_y2, 5,
                              fill=Theme.SURFACE_ALT, outline=Theme.SURFACE_ALT)
            if count:
                bar_x2 = track_x1 + (track_x2 - track_x1) * (count / max_count)
                draw_rounded_rect(self, track_x1, track_y1, bar_x2, track_y2, 5,
                                  fill=color, outline=color)


class HeroPanel(tk.Canvas):
    """Banner de bienvenida con fondo morado oscuro y acciones rápidas."""

    def __init__(self, master, new_task_command, new_note_command, height=144):
        self.greeting = "Buenas tardes"
        self.summary = "Organiza tus prioridades con calma y claridad."
        self.new_task_command = new_task_command
        self.new_note_command = new_note_command

        super().__init__(
            master,
            height=height,
            bg=Theme.BG,
            highlightthickness=0,
            bd=0,
        )
        self.primary_btn = ModernButton(
            self,
            "Nueva tarea",
            new_task_command,
            style="primary",
            icon="+",
            width=132,
        )
        self.secondary_btn = ModernButton(
            self,
            "Nueva nota",
            new_note_command,
            style="secondary",
            icon="≡",
            width=124,
        )
        self.primary_window = self.create_window(0, 0, window=self.primary_btn, anchor="e")
        self.secondary_window = self.create_window(0, 0, window=self.secondary_btn, anchor="e")
        self.bind("<Configure>", lambda _e: self.draw())
        self.after_idle(self.draw)

    def set_content(self, greeting, summary):
        self.greeting = greeting
        self.summary = summary
        self.draw()

    def draw(self):
        # Conservar los widgets embebidos: borrar solo los elementos decorativos.
        self.delete("hero_art")
        width = max(300, self.winfo_width())
        height = max(120, self.winfo_height())

        draw_rounded_rect(
            self,
            2,
            2,
            width - 3,
            height - 4,
            18,
            fill="#17101F",
            outline=Theme.BORDER_ACTIVE,
            width=1,
            tags="hero_art",
        )
        # Capas de iluminación discretas (sin neon fuerte).
        self.create_oval(width - 330, -120, width + 50, 230,
                         fill="#251640", outline="", tags="hero_art")
        self.create_oval(width - 240, -92, width + 120, 190,
                         fill="#1D1530", outline="", tags="hero_art")
        self.create_arc(width - 300, -95, width + 80, 210, start=115, extent=95,
                        style="arc", outline="#6D3BB3", width=2, tags="hero_art")
        self.create_arc(width - 255, -70, width + 75, 185, start=118, extent=86,
                        style="arc", outline="#3B255E", width=1, tags="hero_art")

        self.create_text(24, 27, text="HOY", fill=Theme.LAVENDER,
                         font=Theme.FONT_TINY, anchor="w", tags="hero_art")
        self.create_text(24, 58, text=self.greeting, fill=Theme.TEXT,
                         font=Theme.FONT_HERO, anchor="w", tags="hero_art")
        self.create_text(24, 91, text=self.summary, fill=Theme.TEXT_MUTED,
                         font=Theme.FONT, anchor="w", tags="hero_art")

        self.coords(self.primary_window, width - 22, height / 2 - 23)
        self.coords(self.secondary_window, width - 22, height / 2 + 25)
        self.tag_lower("hero_art")


# ======================================================================
# APLICACIÓN PRINCIPAL
# ======================================================================


class TaskManagerApp:
    """Gestor personal de tareas y notas con persistencia local en JSON."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Andrés Task Manager")
        self.root.geometry("1240x800")
        self.root.minsize(1020, 650)
        self.root.configure(bg=Theme.BG)

        self.data_folder = Path.home() / "AndresTaskManager"
        self.data_folder.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_folder / "datos.json"

        self.data = self.load_data()
        self._sort_state = {}
        self._status_reset_job = None
        self.nav_buttons = {}
        self.pages = {}

        self.setup_styles()
        self.build_menu()
        self.build_interface()
        self.refresh_all()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Control-n>", lambda _e: self.open_task_dialog())
        self.root.bind("<Control-s>", lambda _e: self.save_data(notify=True))
        self.root.bind("<Control-1>", lambda _e: self.show_page("dashboard"))
        self.root.bind("<Control-2>", lambda _e: self.show_page("tasks"))
        self.root.bind("<Control-3>", lambda _e: self.show_page("notes"))

    # ------------------------------------------------------------------
    # PERSISTENCIA DE DATOS
    # ------------------------------------------------------------------

    @staticmethod
    def default_data():
        return {"tasks": [], "notes": []}

    def load_data(self):
        if not self.data_file.exists():
            return self.default_data()

        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                loaded = json.load(file)
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning(
                "Aviso",
                "No se pudieron leer los datos guardados.\n"
                "Se ha creado una estructura nueva.",
            )
            return self.default_data()

        data = self.default_data()
        for key in data:
            if key in loaded and isinstance(loaded[key], list):
                data[key] = loaded[key]
        return data

    def save_data(self, notify=False):
        try:
            tmp_file = self.data_file.with_suffix(".tmp")
            with open(tmp_file, "w", encoding="utf-8") as file:
                json.dump(self.data, file, ensure_ascii=False, indent=2)
            tmp_file.replace(self.data_file)
            self.set_status(f"Cambios guardados · {self.current_time_short()}")
        except OSError as error:
            self.show_message(
                "Error al guardar",
                f"No se pudieron guardar los datos:\n{error}",
                kind="danger",
            )
            return

        if notify:
            self.set_status(f"Guardado manualmente · {self.current_time_short()}")

    def on_close(self):
        self.save_data()
        self.root.destroy()

    # ------------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------------

    @staticmethod
    def generate_id():
        return str(uuid.uuid4())

    @staticmethod
    def current_date():
        return date.today().isoformat()

    @staticmethod
    def current_datetime():
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def current_time_short():
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def is_valid_date(text):
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    @staticmethod
    def greeting_for_hour(hour):
        if hour < 12:
            return "Buenos días"
        if hour < 20:
            return "Buenas tardes"
        return "Buenas noches"

    def fit_dialog(self, dialog, min_width=460, min_height=300):
        """Ajusta y centra un diálogo sobre la ventana principal."""
        dialog.update_idletasks()
        width = max(dialog.winfo_reqwidth(), min_width)
        height = max(dialog.winfo_reqheight(), min_height)

        x = self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2

        dialog.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
        dialog.minsize(width, height)
        dialog.resizable(True, True)
        self.animate_dialog(dialog)

    def animate_dialog(self, dialog):
        """Entrada corta y discreta para ventanas modales."""
        try:
            dialog.attributes("-alpha", 0.90)
        except tk.TclError:
            return

        def step(alpha=0.90):
            if not dialog.winfo_exists():
                return
            alpha = min(1.0, alpha + 0.025)
            try:
                dialog.attributes("-alpha", alpha)
            except tk.TclError:
                return
            if alpha < 1.0:
                dialog.after(22, step, alpha)

        dialog.after(20, step)

    # ------------------------------------------------------------------
    # ESTILOS TTK
    # ------------------------------------------------------------------

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            ".",
            background=Theme.BG,
            foreground=Theme.TEXT,
            font=Theme.FONT,
            borderwidth=0,
        )

        style.configure(
            "Premium.Treeview",
            background=Theme.SURFACE,
            fieldbackground=Theme.SURFACE,
            foreground=Theme.TEXT_SOFT,
            rowheight=38,
            borderwidth=0,
            relief="flat",
            font=Theme.FONT,
        )
        style.map(
            "Premium.Treeview",
            background=[("selected", Theme.SELECT_BG)],
            foreground=[("selected", "#FFFFFF")],
        )
        style.configure(
            "Premium.Treeview.Heading",
            background=Theme.SURFACE_ALT,
            foreground=Theme.TEXT_MUTED,
            font=Theme.FONT_SMALL_BOLD,
            borderwidth=0,
            relief="flat",
            padding=(10, 10),
        )
        style.map(
            "Premium.Treeview.Heading",
            background=[("active", "#222232")],
            foreground=[("active", Theme.TEXT)],
        )

        style.configure(
            "Premium.TCombobox",
            fieldbackground=Theme.INPUT,
            background=Theme.INPUT,
            foreground=Theme.TEXT,
            arrowcolor=Theme.LAVENDER,
            bordercolor=Theme.BORDER,
            lightcolor=Theme.BORDER,
            darkcolor=Theme.BORDER,
            selectbackground=Theme.PRIMARY,
            selectforeground="#FFFFFF",
            padding=(8, 7),
        )
        style.map(
            "Premium.TCombobox",
            fieldbackground=[("readonly", Theme.INPUT), ("focus", Theme.INPUT)],
            foreground=[("readonly", Theme.TEXT)],
            bordercolor=[("focus", Theme.ACCENT)],
        )

        style.configure(
            "Premium.Vertical.TScrollbar",
            background=Theme.SURFACE_ALT,
            troughcolor=Theme.SURFACE,
            bordercolor=Theme.SURFACE,
            arrowcolor=Theme.TEXT_DIM,
            relief="flat",
        )
        style.map(
            "Premium.Vertical.TScrollbar",
            background=[("active", Theme.BORDER_ACTIVE)],
        )

        self.root.option_add("*TCombobox*Listbox.background", Theme.SURFACE_ALT)
        self.root.option_add("*TCombobox*Listbox.foreground", Theme.TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", Theme.PRIMARY)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")

    def style_text_widget(self, widget):
        widget.configure(
            background=Theme.INPUT,
            foreground=Theme.TEXT,
            insertbackground=Theme.LAVENDER_LIGHT,
            selectbackground=Theme.PRIMARY,
            selectforeground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
            borderwidth=0,
            padx=12,
            pady=10,
        )

    def style_toplevel(self, dialog):
        dialog.configure(bg=Theme.BG)

    # ------------------------------------------------------------------
    # MENÚ Y DIÁLOGOS DEL SISTEMA
    # ------------------------------------------------------------------

    def build_menu(self):
        menu_kwargs = {
            "bg": Theme.SIDEBAR,
            "fg": Theme.TEXT_SOFT,
            "activebackground": Theme.PRIMARY_SOFT,
            "activeforeground": Theme.TEXT,
            "bd": 0,
            "relief": "flat",
        }
        menu_bar = tk.Menu(self.root, **menu_kwargs)

        file_menu = tk.Menu(menu_bar, tearoff=0, **menu_kwargs)
        file_menu.add_command(
            label="Guardar ahora",
            accelerator="Ctrl+S",
            command=lambda: self.save_data(notify=True),
        )
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.on_close)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0, **menu_kwargs)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)

        self.root.config(menu=menu_bar)

    def _modal_shell(self, title, subtitle, min_width=500, min_height=320):
        dialog = tk.Toplevel(self.root)
        self.style_toplevel(dialog)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()

        outer = tk.Frame(dialog, bg=Theme.BG)
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        card = tk.Frame(
            outer,
            bg=Theme.SURFACE,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            bd=0,
        )
        card.pack(fill="both", expand=True)

        header = tk.Frame(card, bg=Theme.SURFACE)
        header.pack(fill="x", padx=24, pady=(22, 10))
        tk.Label(header, text=title, bg=Theme.SURFACE, fg=Theme.TEXT,
                 font=Theme.FONT_HEADING).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, bg=Theme.SURFACE,
                     fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL).pack(
                anchor="w", pady=(5, 0)
            )

        body = tk.Frame(card, bg=Theme.SURFACE)
        body.pack(fill="both", expand=True, padx=24, pady=(8, 18))

        footer = tk.Frame(card, bg=Theme.SURFACE)
        footer.pack(fill="x", padx=24, pady=(0, 22))

        dialog._premium_min_size = (min_width, min_height)  # type: ignore[attr-defined]
        return dialog, body, footer

    def show_message(self, title, message, kind="info"):
        subtitle = {
            "danger": "La operación no pudo completarse.",
            "warning": "Revisa la información antes de continuar.",
        }.get(kind, "Información de Andrés Task Manager")
        dialog, body, footer = self._modal_shell(title, subtitle, 470, 250)

        accent = {
            "danger": Theme.DANGER,
            "warning": Theme.WARNING,
        }.get(kind, Theme.LAVENDER)

        chip = tk.Canvas(body, width=42, height=42, bg=Theme.SURFACE,
                         highlightthickness=0, bd=0)
        chip.pack(anchor="w", pady=(0, 12))
        draw_rounded_rect(chip, 2, 2, 40, 40, 12,
                          fill=Theme.PRIMARY_SOFT, outline=Theme.BORDER_ACTIVE)
        chip.create_text(21, 21, text="!" if kind != "info" else "i",
                         fill=accent, font=(Theme.FONT_FAMILY, 14, "bold"))

        tk.Label(
            body,
            text=message,
            justify="left",
            wraplength=430,
            bg=Theme.SURFACE,
            fg=Theme.TEXT_SOFT,
            font=Theme.FONT,
        ).pack(fill="x", anchor="w")

        ModernButton(footer, "Aceptar", dialog.destroy, style="primary", width=104).pack(side="right")
        self.fit_dialog(dialog, 470, 250)

    def ask_confirmation(self, title, message):
        result = {"value": False}
        dialog, body, footer = self._modal_shell(
            title,
            "Esta acción no se puede deshacer.",
            500,
            270,
        )

        tk.Label(body, text=message, justify="left", wraplength=450,
                 bg=Theme.SURFACE, fg=Theme.TEXT_SOFT,
                 font=Theme.FONT).pack(anchor="w", fill="x", pady=(6, 0))

        def confirm():
            result["value"] = True
            dialog.destroy()

        ModernButton(footer, "Eliminar", confirm, style="danger", width=108).pack(side="right")
        ModernButton(footer, "Cancelar", dialog.destroy, style="secondary", width=108).pack(
            side="right", padx=(0, 8)
        )
        self.fit_dialog(dialog, 500, 270)
        self.root.wait_window(dialog)
        return result["value"]

    def show_about(self):
        dialog, body, footer = self._modal_shell(
            "Acerca de",
            "Productividad local, simple y privada.",
            520,
            330,
        )

        logo = tk.Canvas(body, width=54, height=54, bg=Theme.SURFACE,
                         highlightthickness=0, bd=0)
        logo.pack(anchor="w", pady=(0, 14))
        draw_rounded_rect(logo, 2, 2, 52, 52, 15,
                          fill=Theme.PRIMARY_SOFT, outline=Theme.ACCENT, width=1)
        logo.create_text(27, 27, text="A", fill=Theme.LAVENDER_LIGHT,
                         font=(Theme.FONT_FAMILY, 20, "bold"))

        tk.Label(body, text="Andrés Task Manager", bg=Theme.SURFACE,
                 fg=Theme.TEXT, font=(Theme.FONT_FAMILY, 16, "bold")).pack(anchor="w")
        tk.Label(body, text="Gestor personal de tareas y notas con datos locales en JSON.",
                 bg=Theme.SURFACE, fg=Theme.TEXT_MUTED,
                 font=Theme.FONT, wraplength=450, justify="left").pack(
            anchor="w", pady=(7, 12)
        )
        tk.Label(body, text="Archivo de datos", bg=Theme.SURFACE,
                 fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL_BOLD).pack(anchor="w")
        tk.Label(body, text=str(self.data_file), bg=Theme.SURFACE,
                 fg=Theme.LAVENDER, font=Theme.FONT_SMALL,
                 wraplength=450, justify="left").pack(anchor="w", pady=(4, 0))

        ModernButton(footer, "Cerrar", dialog.destroy, style="primary", width=104).pack(side="right")
        self.fit_dialog(dialog, 520, 330)

    # ------------------------------------------------------------------
    # ESTRUCTURA GENERAL / NAVEGACIÓN
    # ------------------------------------------------------------------

    def build_interface(self):
        shell = tk.Frame(self.root, bg=Theme.BG)
        shell.pack(fill="both", expand=True)

        sidebar = tk.Frame(shell, bg=Theme.SIDEBAR, width=232)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.build_sidebar(sidebar)

        main = tk.Frame(shell, bg=Theme.BG)
        main.pack(side="left", fill="both", expand=True)

        content = tk.Frame(main, bg=Theme.BG)
        content.pack(fill="both", expand=True, padx=24, pady=(22, 12))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        for name in ("dashboard", "tasks", "notes"):
            page = tk.Frame(content, bg=Theme.BG)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

        self.build_dashboard()
        self.build_tasks_tab()
        self.build_notes_tab()
        self.build_status_bar(main)
        self.show_page("dashboard")

    def build_sidebar(self, parent):
        brand = tk.Frame(parent, bg=Theme.SIDEBAR)
        brand.pack(fill="x", padx=18, pady=(24, 28))

        logo = tk.Canvas(brand, width=46, height=46, bg=Theme.SIDEBAR,
                         highlightthickness=0, bd=0)
        logo.pack(side="left")
        draw_rounded_rect(logo, 2, 2, 44, 44, 13,
                          fill=Theme.PRIMARY_SOFT, outline=Theme.ACCENT, width=1)
        draw_rounded_rect(logo, 8, 8, 38, 38, 10,
                          fill="#171021", outline=Theme.BORDER_ACTIVE, width=1)
        logo.create_text(23, 23, text="A", fill=Theme.LAVENDER_LIGHT,
                         font=(Theme.FONT_FAMILY, 17, "bold"))

        title_wrap = tk.Frame(brand, bg=Theme.SIDEBAR)
        title_wrap.pack(side="left", padx=(11, 0), fill="y")
        tk.Label(title_wrap, text="ANDRÉS", bg=Theme.SIDEBAR,
                 fg=Theme.TEXT, font=(Theme.FONT_FAMILY, 13, "bold")).pack(anchor="w")
        tk.Label(title_wrap, text="TASK MANAGER", bg=Theme.SIDEBAR,
                 fg=Theme.TEXT_DIM, font=(Theme.FONT_FAMILY, 7, "bold")).pack(
            anchor="w", pady=(2, 0)
        )

        tk.Label(parent, text="ESPACIO", bg=Theme.SIDEBAR, fg=Theme.TEXT_DIM,
                 font=(Theme.FONT_FAMILY, 8, "bold")).pack(anchor="w", padx=22, pady=(0, 8))

        nav = tk.Frame(parent, bg=Theme.SIDEBAR)
        nav.pack(fill="x", padx=16)

        items = [
            ("dashboard", "Inicio", "⌂"),
            ("tasks", "Tareas", "✓"),
            ("notes", "Notas", "≡"),
        ]
        for name, text, icon in items:
            button = NavButton(nav, text, icon, lambda n=name: self.show_page(n))
            button.pack(fill="x", pady=3)
            self.nav_buttons[name] = button

        spacer = tk.Frame(parent, bg=Theme.SIDEBAR)
        spacer.pack(fill="both", expand=True)

        utility = tk.Frame(parent, bg=Theme.SIDEBAR)
        utility.pack(fill="x", padx=16, pady=(0, 16))
        tk.Frame(utility, bg=Theme.BORDER_SOFT, height=1).pack(fill="x", pady=(0, 12))

        save_nav = NavButton(utility, "Guardar", "↓", lambda: self.save_data(notify=True))
        save_nav.pack(fill="x", pady=3)
        about_nav = NavButton(utility, "Acerca de", "i", self.show_about)
        about_nav.pack(fill="x", pady=3)

        profile = tk.Frame(parent, bg=Theme.SURFACE, highlightthickness=1,
                           highlightbackground=Theme.BORDER_SOFT)
        profile.pack(fill="x", padx=16, pady=(0, 18))
        avatar = tk.Canvas(profile, width=34, height=34, bg=Theme.SURFACE,
                           highlightthickness=0, bd=0)
        avatar.pack(side="left", padx=(10, 8), pady=10)
        draw_rounded_rect(avatar, 1, 1, 33, 33, 11,
                          fill=Theme.PRIMARY_SOFT, outline=Theme.BORDER_ACTIVE)
        avatar.create_text(17, 17, text="A", fill=Theme.LAVENDER_LIGHT,
                           font=(Theme.FONT_FAMILY, 11, "bold"))
        profile_text = tk.Frame(profile, bg=Theme.SURFACE)
        profile_text.pack(side="left", fill="x", expand=True)
        tk.Label(profile_text, text="Espacio personal", bg=Theme.SURFACE,
                 fg=Theme.TEXT_SOFT, font=Theme.FONT_SMALL_BOLD).pack(anchor="w")
        tk.Label(profile_text, text="Datos guardados localmente", bg=Theme.SURFACE,
                 fg=Theme.TEXT_DIM, font=Theme.FONT_TINY).pack(anchor="w", pady=(2, 0))

    def show_page(self, name):
        page = self.pages.get(name)
        if page is None:
            return
        page.tkraise()
        for key, button in self.nav_buttons.items():
            button.set_active(key == name)

    def build_page_header(self, parent, eyebrow, title, subtitle, action=None):
        header = tk.Frame(parent, bg=Theme.BG)
        header.pack(fill="x", pady=(0, 18))

        text = tk.Frame(header, bg=Theme.BG)
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=eyebrow.upper(), bg=Theme.BG,
                 fg=Theme.LAVENDER, font=Theme.FONT_TINY).pack(anchor="w")
        tk.Label(text, text=title, bg=Theme.BG, fg=Theme.TEXT,
                 font=Theme.FONT_TITLE).pack(anchor="w", pady=(3, 1))
        tk.Label(text, text=subtitle, bg=Theme.BG, fg=Theme.TEXT_MUTED,
                 font=Theme.FONT).pack(anchor="w")

        if action:
            action.pack(side="right", anchor="e")
        return header

    def build_status_bar(self, parent):
        top_line = tk.Frame(parent, bg=Theme.BORDER_SOFT, height=1)
        top_line.pack(fill="x", padx=24)

        bar = tk.Frame(parent, bg=Theme.BG)
        bar.pack(fill="x", padx=24, pady=(8, 12))
        self.status_dot = tk.Canvas(bar, width=12, height=12, bg=Theme.BG,
                                    highlightthickness=0, bd=0)
        self.status_dot.pack(side="left")
        self.status_dot.create_oval(3, 3, 9, 9, fill=Theme.SUCCESS, outline="")
        self.status_label = tk.Label(bar, text="Todo listo", bg=Theme.BG,
                                     fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL)
        self.status_label.pack(side="left", padx=(4, 0))

        self.clock_label = tk.Label(bar, text="", bg=Theme.BG,
                                    fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL)
        self.clock_label.pack(side="right")
        self.update_clock()

    def set_status(self, text):
        if not hasattr(self, "status_label"):
            return
        self.status_label.config(text=text, fg=Theme.TEXT_SOFT)
        if self._status_reset_job:
            self.root.after_cancel(self._status_reset_job)
        self._status_reset_job = self.root.after(
            3200,
            lambda: self.status_label.config(text="Todo listo", fg=Theme.TEXT_MUTED),
        )

    def update_clock(self):
        if hasattr(self, "clock_label"):
            self.clock_label.config(text=datetime.now().strftime("%d %b %Y  ·  %H:%M"))
        self.root.after(30000, self.update_clock)

    # ------------------------------------------------------------------
    # DASHBOARD
    # ------------------------------------------------------------------

    def build_dashboard(self):
        page = self.pages["dashboard"]

        self.build_page_header(
            page,
            "Panel principal",
            "Tu espacio de enfoque",
            "Tareas, notas y progreso en una única vista.",
        )

        self.hero = HeroPanel(page, self.open_task_dialog, self.open_note_dialog)
        self.hero.pack(fill="x", pady=(0, 16))

        stats = tk.Frame(page, bg=Theme.BG)
        stats.pack(fill="x", pady=(0, 16))
        for col in range(4):
            stats.grid_columnconfigure(col, weight=1, uniform="stats")

        self.pending_card = StatCard(stats, "Pendientes", "○", Theme.LAVENDER)
        self.completed_card = StatCard(stats, "Completadas", "✓", Theme.SUCCESS)
        self.overdue_card = StatCard(stats, "Vencidas", "!", Theme.DANGER)
        self.notes_card = StatCard(stats, "Notas", "≡", Theme.ACCENT)
        for col, card in enumerate(
            (self.pending_card, self.completed_card, self.overdue_card, self.notes_card)
        ):
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0 if col == 0 else 6, 0 if col == 3 else 6))

        lower = tk.Frame(page, bg=Theme.BG)
        lower.pack(fill="both", expand=True)
        lower.grid_columnconfigure(0, weight=3, uniform="lower")
        lower.grid_columnconfigure(1, weight=2, uniform="lower")
        lower.grid_rowconfigure(0, weight=1)

        tasks_panel = RoundedSurface(lower, height=370, radius=17, padding=18)
        tasks_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        task_body = tasks_panel.content

        heading = tk.Frame(task_body, bg=Theme.SURFACE)
        heading.pack(fill="x", pady=(0, 12))
        tk.Label(heading, text="Prioridades pendientes", bg=Theme.SURFACE,
                 fg=Theme.TEXT, font=Theme.FONT_HEADING).pack(side="left")
        tk.Label(heading, text="Doble clic para editar", bg=Theme.SURFACE,
                 fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL).pack(side="right")

        tree_wrap = tk.Frame(task_body, bg=Theme.SURFACE)
        tree_wrap.pack(fill="both", expand=True)
        columns = ("title", "priority", "category", "due")
        self.priority_tree = ttk.Treeview(
            tree_wrap,
            columns=columns,
            show="headings",
            style="Premium.Treeview",
            height=7,
        )
        for col, text, width in (
            ("title", "Tarea", 280),
            ("priority", "Prioridad", 90),
            ("category", "Categoría", 130),
            ("due", "Fecha límite", 110),
        ):
            self.priority_tree.heading(col, text=text)
            self.priority_tree.column(col, width=width, minwidth=80, stretch=True)

        self.tag_tree(self.priority_tree)
        self.priority_tree.pack(side="left", fill="both", expand=True)
        self.priority_tree.bind(
            "<Double-1>", lambda _e: self.edit_task_from_tree(self.priority_tree)
        )
        scroll = ttk.Scrollbar(
            tree_wrap,
            orient="vertical",
            command=self.priority_tree.yview,
            style="Premium.Vertical.TScrollbar",
        )
        self.priority_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        insight_panel = RoundedSurface(lower, height=370, radius=17, padding=18)
        insight_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        insight = insight_panel.content

        tk.Label(insight, text="Progreso general", bg=Theme.SURFACE,
                 fg=Theme.TEXT, font=Theme.FONT_HEADING).pack(anchor="w")
        tk.Label(insight, text="Relación entre tareas completadas y totales.",
                 bg=Theme.SURFACE, fg=Theme.TEXT_MUTED,
                 font=Theme.FONT_SMALL).pack(anchor="w", pady=(4, 8))

        self.progress_ring = DonutChart(insight, size=145)
        self.progress_ring.pack(fill="x", pady=(2, 2))

        divider = tk.Frame(insight, bg=Theme.BORDER_SOFT, height=1)
        divider.pack(fill="x", pady=(4, 10))
        tk.Label(insight, text="Pendientes por prioridad", bg=Theme.SURFACE,
                 fg=Theme.TEXT_SOFT, font=Theme.FONT_SMALL_BOLD).pack(anchor="w")
        self.priority_breakdown = PriorityBreakdown(insight, height=118)
        self.priority_breakdown.pack(fill="x", expand=True, pady=(4, 0))

    def tag_tree(self, tree):
        tree.tag_configure("alta", foreground=PRIORITY_COLORS["Alta"])
        tree.tag_configure("media", foreground=PRIORITY_COLORS["Media"])
        tree.tag_configure("baja", foreground=PRIORITY_COLORS["Baja"])
        tree.tag_configure("vencida", foreground=Theme.DANGER)
        tree.tag_configure("completada", foreground=Theme.TEXT_DIM)

    def refresh_dashboard(self):
        tasks = self.data["tasks"]
        today = self.current_date()

        pending = [task for task in tasks if not task["completed"]]
        completed = [task for task in tasks if task["completed"]]
        overdue = [
            task for task in pending
            if task.get("due_date") and task["due_date"] < today
        ]

        total = len(tasks)
        completion = len(completed) / total if total else 0.0
        pending_count = len(pending)

        self.pending_card.set_value(pending_count, "por hacer")
        self.completed_card.set_value(len(completed), f"{int(completion * 100)}%")
        self.overdue_card.set_value(len(overdue), "atención" if overdue else "al día")
        self.notes_card.set_value(len(self.data["notes"]), "guardadas")
        self.progress_ring.set_progress(completion)

        priority_counts = {
            priority: sum(1 for task in pending if task.get("priority") == priority)
            for priority in PRIORITIES
        }
        self.priority_breakdown.set_counts(priority_counts)

        if pending_count == 0 and total:
            summary = "No tienes tareas pendientes. Tu lista está al día."
        elif pending_count == 0:
            summary = "Empieza creando una tarea o una nota para organizar tu día."
        elif overdue:
            summary = f"Tienes {pending_count} tareas pendientes y {len(overdue)} requieren atención."
        else:
            summary = f"Tienes {pending_count} tareas pendientes. Todo está dentro de plazo."
        greeting = f"{self.greeting_for_hour(datetime.now().hour)}, Andrés"
        self.hero.set_content(greeting, summary)

        for item in self.priority_tree.get_children():
            self.priority_tree.delete(item)

        ordered = sorted(
            pending,
            key=lambda task: (
                PRIORITY_ORDER.get(task.get("priority"), 3),
                task.get("due_date") or "9999",
            ),
        )
        for task in ordered[:12]:
            due_date = task.get("due_date", "")
            is_overdue = due_date and due_date < today
            tag = "vencida" if is_overdue else task.get("priority", "Media").lower()
            self.priority_tree.insert(
                "",
                "end",
                iid=task["id"],
                values=(
                    task.get("title", ""),
                    task.get("priority", ""),
                    task.get("category", ""),
                    due_date,
                ),
                tags=(tag,),
            )

    # ------------------------------------------------------------------
    # TAREAS
    # ------------------------------------------------------------------

    def build_tasks_tab(self):
        page = self.pages["tasks"]
        action = ModernButton(
            page,
            "Nueva tarea",
            self.open_task_dialog,
            style="primary",
            icon="+",
            width=132,
        )
        self.build_page_header(
            page,
            "Organización",
            "Tareas",
            "Busca, filtra y actualiza tus prioridades desde una sola lista.",
            action,
        )

        toolbar = RoundedSurface(page, height=132, radius=16, padding=16, shadow=False)
        toolbar.pack(fill="x", pady=(0, 14))
        body = toolbar.content

        actions = tk.Frame(body, bg=Theme.SURFACE)
        actions.pack(fill="x")
        ModernButton(actions, "Editar", lambda: self.edit_task_from_tree(self.tasks_tree),
                     style="secondary", width=94).pack(side="left")
        ModernButton(actions, "Completar / reabrir", self.toggle_selected_task,
                     style="secondary", icon="✓", width=168).pack(side="left", padx=(8, 0))
        ModernButton(actions, "Eliminar", self.delete_selected_task,
                     style="danger", width=100).pack(side="left", padx=(8, 0))

        filters = tk.Frame(body, bg=Theme.SURFACE)
        filters.pack(fill="x", pady=(14, 0))

        tk.Label(filters, text="Buscar", bg=Theme.SURFACE, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL).pack(side="left", padx=(0, 7))
        self.task_search_var = tk.StringVar()
        self.task_search_var.trace_add("write", lambda *_: self.refresh_tasks())
        search_entry = ModernEntry(filters, textvariable=self.task_search_var, width=245, height=38)
        search_entry.pack(side="left", padx=(0, 16))

        tk.Label(filters, text="Estado", bg=Theme.SURFACE, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL).pack(side="left", padx=(0, 7))
        self.task_status_var = tk.StringVar(value="Todas")
        status_combo = ttk.Combobox(
            filters,
            textvariable=self.task_status_var,
            state="readonly",
            width=13,
            values=["Todas", "Pendientes", "Completadas"],
            style="Premium.TCombobox",
        )
        status_combo.pack(side="left", padx=(0, 16))
        status_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tasks())

        tk.Label(filters, text="Prioridad", bg=Theme.SURFACE, fg=Theme.TEXT_DIM,
                 font=Theme.FONT_SMALL).pack(side="left", padx=(0, 7))
        self.task_priority_var = tk.StringVar(value="Todas")
        priority_combo = ttk.Combobox(
            filters,
            textvariable=self.task_priority_var,
            state="readonly",
            width=10,
            values=["Todas"] + PRIORITIES,
            style="Premium.TCombobox",
        )
        priority_combo.pack(side="left")
        priority_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tasks())

        panel = RoundedSurface(page, height=440, radius=17, padding=18)
        panel.pack(fill="both", expand=True)
        table_body = panel.content

        table_head = tk.Frame(table_body, bg=Theme.SURFACE)
        table_head.pack(fill="x", pady=(0, 12))
        tk.Label(table_head, text="Todas las tareas", bg=Theme.SURFACE,
                 fg=Theme.TEXT, font=Theme.FONT_HEADING).pack(side="left")
        self.tasks_count_label = tk.Label(table_head, text="0 elementos", bg=Theme.SURFACE,
                                          fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL)
        self.tasks_count_label.pack(side="right")

        tree_wrap = tk.Frame(table_body, bg=Theme.SURFACE)
        tree_wrap.pack(fill="both", expand=True)
        columns = ("title", "priority", "category", "due", "status")
        self.tasks_tree = ttk.Treeview(
            tree_wrap,
            columns=columns,
            show="headings",
            style="Premium.Treeview",
        )
        headings = {
            "title": "Tarea",
            "priority": "Prioridad",
            "category": "Categoría",
            "due": "Fecha límite",
            "status": "Estado",
        }
        widths = {
            "title": 330,
            "priority": 105,
            "category": 145,
            "due": 125,
            "status": 115,
        }
        for col in columns:
            self.tasks_tree.heading(
                col,
                text=headings[col],
                command=lambda c=col: self.sort_tree(self.tasks_tree, c),
            )
            self.tasks_tree.column(col, width=widths[col], minwidth=85, stretch=True)

        self.tag_tree(self.tasks_tree)
        self.tasks_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(
            tree_wrap,
            orient="vertical",
            command=self.tasks_tree.yview,
            style="Premium.Vertical.TScrollbar",
        )
        self.tasks_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        self.tasks_tree.bind("<Double-1>", lambda _e: self.edit_task_from_tree(self.tasks_tree))
        self.tasks_tree.bind("<Delete>", lambda _e: self.delete_selected_task())

    def sort_tree(self, tree, col):
        key, reverse = self._sort_state.get(id(tree), (None, False))
        reverse = not reverse if key == col else False
        self._sort_state[id(tree)] = (col, reverse)

        items = [(tree.set(iid, col), iid) for iid in tree.get_children("")]
        items.sort(key=lambda pair: pair[0].lower(), reverse=reverse)
        for index, (_, iid) in enumerate(items):
            tree.move(iid, "", index)

    def _field_label(self, parent, text):
        tk.Label(parent, text=text, bg=Theme.SURFACE, fg=Theme.TEXT_MUTED,
                 font=Theme.FONT_SMALL_BOLD).pack(anchor="w", pady=(0, 6))

    def open_task_dialog(self, task=None):
        is_edit = task is not None
        title = "Editar tarea" if is_edit else "Nueva tarea"
        subtitle = (
            "Actualiza la información de esta tarea."
            if is_edit
            else "Define qué quieres hacer y cuándo debe estar listo."
        )
        dialog, body, footer = self._modal_shell(title, subtitle, 570, 560)

        self._field_label(body, "Título")
        title_entry = ModernEntry(body, width=500, height=42)
        title_entry.pack(fill="x", pady=(0, 14))

        self._field_label(body, "Descripción")
        description_text = tk.Text(body, height=6, wrap="word", font=Theme.FONT)
        self.style_text_widget(description_text)
        description_text.pack(fill="both", expand=True, pady=(0, 14))

        row = tk.Frame(body, bg=Theme.SURFACE)
        row.pack(fill="x", pady=(0, 14))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)

        left_col = tk.Frame(row, bg=Theme.SURFACE)
        left_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(left_col, text="Prioridad", bg=Theme.SURFACE,
                 fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL_BOLD).pack(anchor="w", pady=(0, 6))
        priority_var = tk.StringVar(value="Media")
        priority_combo = ttk.Combobox(
            left_col,
            textvariable=priority_var,
            values=PRIORITIES,
            state="readonly",
            style="Premium.TCombobox",
        )
        priority_combo.pack(fill="x")

        right_col = tk.Frame(row, bg=Theme.SURFACE)
        right_col.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        tk.Label(right_col, text="Fecha límite · AAAA-MM-DD", bg=Theme.SURFACE,
                 fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL_BOLD).pack(anchor="w", pady=(0, 6))
        due_entry = ModernEntry(right_col, width=240, height=42)
        due_entry.pack(fill="x")

        self._field_label(body, "Categoría")
        category_entry = ModernEntry(body, width=500, height=42)
        category_entry.pack(fill="x")

        if is_edit:
            title_entry.insert(0, task.get("title", ""))
            description_text.insert("1.0", task.get("description", ""))
            priority_var.set(task.get("priority", "Media"))
            category_entry.insert(0, task.get("category", ""))
            due_entry.insert(0, task.get("due_date", ""))
        else:
            due_entry.insert(0, self.current_date())

        def save():
            task_title = title_entry.get().strip()
            due_date = due_entry.get().strip()

            if not task_title:
                self.show_message("Título requerido", "Debes introducir un título para la tarea.", "warning")
                return
            if due_date and not self.is_valid_date(due_date):
                self.show_message("Fecha incorrecta", "Utiliza el formato AAAA-MM-DD.", "warning")
                return

            description = description_text.get("1.0", "end").strip()
            category = category_entry.get().strip()
            priority = priority_var.get()

            if is_edit:
                task.update(
                    title=task_title,
                    description=description,
                    priority=priority,
                    category=category,
                    due_date=due_date,
                )
            else:
                self.data["tasks"].append({
                    "id": self.generate_id(),
                    "title": task_title,
                    "description": description,
                    "priority": priority,
                    "category": category,
                    "due_date": due_date,
                    "completed": False,
                    "created_at": self.current_datetime(),
                    "completed_at": None,
                })

            self.save_data()
            self.refresh_all()
            dialog.destroy()
            self.set_status("Tarea actualizada" if is_edit else "Nueva tarea creada")

        ModernButton(footer, "Guardar", save, style="primary", width=112).pack(side="right")
        ModernButton(footer, "Cancelar", dialog.destroy, style="secondary", width=112).pack(
            side="right", padx=(0, 8)
        )

        self.fit_dialog(dialog, 570, 560)
        title_entry.focus_set()

    def refresh_tasks(self):
        if not hasattr(self, "tasks_tree"):
            return
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        search = self.task_search_var.get().strip().lower()
        status_filter = self.task_status_var.get()
        priority_filter = self.task_priority_var.get()
        today = self.current_date()
        visible = 0

        for task in self.data["tasks"]:
            title = task.get("title", "")
            category = task.get("category", "")
            if search and search not in title.lower() and search not in category.lower():
                continue
            if status_filter == "Pendientes" and task.get("completed"):
                continue
            if status_filter == "Completadas" and not task.get("completed"):
                continue
            if priority_filter != "Todas" and task.get("priority") != priority_filter:
                continue

            due_date = task.get("due_date", "")
            completed = bool(task.get("completed"))
            is_overdue = due_date and due_date < today and not completed
            status_text = "Completada" if completed else "Pendiente"

            if completed:
                tag = "completada"
            elif is_overdue:
                tag = "vencida"
            else:
                tag = task.get("priority", "Media").lower()

            self.tasks_tree.insert(
                "",
                "end",
                iid=task["id"],
                values=(title, task.get("priority", ""), category, due_date, status_text),
                tags=(tag,),
            )
            visible += 1

        self.tasks_count_label.config(text=f"{visible} elemento{'s' if visible != 1 else ''}")

    def get_task_by_id(self, task_id):
        return next((task for task in self.data["tasks"] if task["id"] == task_id), None)

    def get_selected_task(self, tree):
        selection = tree.selection()
        if not selection:
            self.show_message("Selecciona una tarea", "Selecciona una tarea de la lista para continuar.")
            return None
        return self.get_task_by_id(selection[0])

    def edit_task_from_tree(self, tree):
        task = self.get_selected_task(tree)
        if task:
            self.open_task_dialog(task)

    def toggle_selected_task(self):
        task = self.get_selected_task(self.tasks_tree)
        if not task:
            return

        task["completed"] = not task["completed"]
        task["completed_at"] = self.current_datetime() if task["completed"] else None
        self.save_data()
        self.refresh_all()
        self.set_status("Tarea completada" if task["completed"] else "Tarea reabierta")

    def delete_selected_task(self):
        task = self.get_selected_task(self.tasks_tree)
        if not task:
            return
        if not self.ask_confirmation(
            "Eliminar tarea",
            f"¿Quieres eliminar definitivamente “{task.get('title', '')}”?",
        ):
            return

        self.data["tasks"] = [item for item in self.data["tasks"] if item["id"] != task["id"]]
        self.save_data()
        self.refresh_all()
        self.set_status("Tarea eliminada")

    # ------------------------------------------------------------------
    # NOTAS
    # ------------------------------------------------------------------

    def build_notes_tab(self):
        page = self.pages["notes"]
        action = ModernButton(
            page,
            "Nueva nota",
            self.open_note_dialog,
            style="primary",
            icon="+",
            width=128,
        )
        self.build_page_header(
            page,
            "Biblioteca personal",
            "Notas",
            "Captura ideas, referencias y contexto sin salir de tu espacio de trabajo.",
            action,
        )

        toolbar = RoundedSurface(page, height=90, radius=16, padding=16, shadow=False)
        toolbar.pack(fill="x", pady=(0, 14))
        body = toolbar.content

        ModernButton(body, "Abrir", self.edit_note_from_tree,
                     style="secondary", width=92).pack(side="left")
        ModernButton(body, "Eliminar", self.delete_selected_note,
                     style="danger", width=100).pack(side="left", padx=(8, 0))

        self.note_search_var = tk.StringVar()
        self.note_search_var.trace_add("write", lambda *_: self.refresh_notes())
        search_wrap = tk.Frame(body, bg=Theme.SURFACE)
        search_wrap.pack(side="right")
        tk.Label(search_wrap, text="Buscar", bg=Theme.SURFACE,
                 fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL).pack(side="left", padx=(0, 7))
        ModernEntry(search_wrap, textvariable=self.note_search_var,
                    width=255, height=38).pack(side="left")

        panel = RoundedSurface(page, height=490, radius=17, padding=18)
        panel.pack(fill="both", expand=True)
        table_body = panel.content

        header = tk.Frame(table_body, bg=Theme.SURFACE)
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="Todas las notas", bg=Theme.SURFACE,
                 fg=Theme.TEXT, font=Theme.FONT_HEADING).pack(side="left")
        self.notes_count_label = tk.Label(header, text="0 elementos", bg=Theme.SURFACE,
                                          fg=Theme.TEXT_DIM, font=Theme.FONT_SMALL)
        self.notes_count_label.pack(side="right")

        tree_wrap = tk.Frame(table_body, bg=Theme.SURFACE)
        tree_wrap.pack(fill="both", expand=True)
        columns = ("title", "category", "updated")
        self.notes_tree = ttk.Treeview(
            tree_wrap,
            columns=columns,
            show="headings",
            style="Premium.Treeview",
        )
        for col, text, width in (
            ("title", "Título", 390),
            ("category", "Categoría", 190),
            ("updated", "Última edición", 170),
        ):
            self.notes_tree.heading(
                col,
                text=text,
                command=lambda c=col: self.sort_tree(self.notes_tree, c),
            )
            self.notes_tree.column(col, width=width, minwidth=110, stretch=True)

        self.notes_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(
            tree_wrap,
            orient="vertical",
            command=self.notes_tree.yview,
            style="Premium.Vertical.TScrollbar",
        )
        self.notes_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        self.notes_tree.bind("<Double-1>", lambda _e: self.edit_note_from_tree())
        self.notes_tree.bind("<Delete>", lambda _e: self.delete_selected_note())

    def open_note_dialog(self, note=None):
        is_edit = note is not None
        title = "Editar nota" if is_edit else "Nueva nota"
        subtitle = (
            "Actualiza el contenido y su contexto."
            if is_edit
            else "Guarda una idea con el contexto suficiente para recuperarla después."
        )
        dialog, body, footer = self._modal_shell(title, subtitle, 650, 600)

        top = tk.Frame(body, bg=Theme.SURFACE)
        top.pack(fill="x", pady=(0, 14))
        top.grid_columnconfigure(0, weight=3)
        top.grid_columnconfigure(1, weight=2)

        left = tk.Frame(top, bg=Theme.SURFACE)
        left.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(left, text="Título", bg=Theme.SURFACE, fg=Theme.TEXT_MUTED,
                 font=Theme.FONT_SMALL_BOLD).pack(anchor="w", pady=(0, 6))
        title_entry = ModernEntry(left, width=350, height=42)
        title_entry.pack(fill="x")

        right = tk.Frame(top, bg=Theme.SURFACE)
        right.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        tk.Label(right, text="Categoría", bg=Theme.SURFACE, fg=Theme.TEXT_MUTED,
                 font=Theme.FONT_SMALL_BOLD).pack(anchor="w", pady=(0, 6))
        category_entry = ModernEntry(right, width=220, height=42)
        category_entry.pack(fill="x")

        self._field_label(body, "Contenido")
        content_text = tk.Text(body, wrap="word", font=Theme.FONT, width=60, height=17)
        self.style_text_widget(content_text)
        content_text.pack(fill="both", expand=True)

        if is_edit:
            title_entry.insert(0, note.get("title", ""))
            category_entry.insert(0, note.get("category", ""))
            content_text.insert("1.0", note.get("content", ""))

        def save():
            note_title = title_entry.get().strip()
            if not note_title:
                self.show_message("Título requerido", "Introduce un título para guardar la nota.", "warning")
                return

            category = category_entry.get().strip()
            content = content_text.get("1.0", "end").strip()

            if is_edit:
                note.update(
                    title=note_title,
                    category=category,
                    content=content,
                    updated_at=self.current_datetime(),
                )
            else:
                self.data["notes"].append({
                    "id": self.generate_id(),
                    "title": note_title,
                    "category": category,
                    "content": content,
                    "created_at": self.current_datetime(),
                    "updated_at": self.current_datetime(),
                })

            self.save_data()
            self.refresh_all()
            dialog.destroy()
            self.set_status("Nota actualizada" if is_edit else "Nueva nota creada")

        ModernButton(footer, "Guardar", save, style="primary", width=112).pack(side="right")
        ModernButton(footer, "Cancelar", dialog.destroy, style="secondary", width=112).pack(
            side="right", padx=(0, 8)
        )
        self.fit_dialog(dialog, 650, 600)
        title_entry.focus_set()

    def refresh_notes(self):
        if not hasattr(self, "notes_tree"):
            return
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)

        search = self.note_search_var.get().strip().lower()
        visible = 0
        notes = sorted(
            self.data["notes"],
            key=lambda note: note.get("updated_at", ""),
            reverse=True,
        )
        for note in notes:
            title = note.get("title", "")
            category = note.get("category", "")
            if search and search not in title.lower() and search not in category.lower():
                continue
            self.notes_tree.insert(
                "",
                "end",
                iid=note["id"],
                values=(title, category, note.get("updated_at", "")),
            )
            visible += 1

        self.notes_count_label.config(text=f"{visible} elemento{'s' if visible != 1 else ''}")

    def get_note_by_id(self, note_id):
        return next((note for note in self.data["notes"] if note["id"] == note_id), None)

    def get_selected_note(self):
        selection = self.notes_tree.selection()
        if not selection:
            self.show_message("Selecciona una nota", "Selecciona una nota de la lista para continuar.")
            return None
        return self.get_note_by_id(selection[0])

    def edit_note_from_tree(self):
        note = self.get_selected_note()
        if note:
            self.open_note_dialog(note)

    def delete_selected_note(self):
        note = self.get_selected_note()
        if not note:
            return
        if not self.ask_confirmation(
            "Eliminar nota",
            f"¿Quieres eliminar definitivamente “{note.get('title', '')}”?",
        ):
            return

        self.data["notes"] = [item for item in self.data["notes"] if item["id"] != note["id"]]
        self.save_data()
        self.refresh_all()
        self.set_status("Nota eliminada")

    # ------------------------------------------------------------------
    # ACTUALIZACIÓN GLOBAL
    # ------------------------------------------------------------------

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_tasks()
        self.refresh_notes()


# ======================================================================
# PUNTO DE ENTRADA
# ======================================================================


def main():
    root = tk.Tk()
    TaskManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
