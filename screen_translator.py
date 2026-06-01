#!/usr/bin/env python3
"""
Screen Translator
─────────────────
Hotkey  Ctrl+Shift+Space
  1. Arrastra para seleccionar una región de pantalla
  2. Groq (Llama 4 Scout) extrae y traduce el texto al español
  3. La traducción aparece en una ventana flotante

Dependencias:
    pip install groq mss Pillow keyboard

Variable de entorno requerida:
    set GROQ_API_KEY=<tu_api_key>      (Windows cmd)
    $env:GROQ_API_KEY="<tu_api_key>"   (PowerShell)
"""

import os
import io
import sys
import base64
import queue
import threading
import tkinter as tk
from PIL import Image, ImageTk
import mss
import keyboard
from groq import Groq

# ── Configuración ─────────────────────────────────────────────────────────────
HOTKEY = "ctrl+shift+space"
MODEL  = "meta-llama/llama-4-scout-17b-16e-instruct"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    sys.exit("❌  Falta GROQ_API_KEY.\n"
             "    Windows cmd   : set GROQ_API_KEY=<tu_key>\n"
             "    PowerShell    : $env:GROQ_API_KEY='<tu_key>'")

client = Groq(api_key=GROQ_API_KEY)
_trigger_queue: queue.Queue = queue.Queue()


# ── Captura de pantalla ───────────────────────────────────────────────────────
def grab_screen() -> Image.Image:
    """Captura el monitor primario en resolución física."""
    with mss.MSS() as sct:
        # monitors[1] = monitor primario; [0] = todos los monitores combinados
        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


# ── Traducción vía Groq ───────────────────────────────────────────────────────
def translate_image(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
                {
                    "type": "text",
                    "text": (
                        "Extract all visible text from this image and translate it to Spanish. "
                        "Return only the translated text, no extra commentary or explanations."
                    ),
                },
            ],
        }],
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()


# ── Selector de región ────────────────────────────────────────────────────────
def select_region(root: tk.Tk, screenshot: Image.Image) -> tuple | None:
    """
    Pantalla congelada con overlay semitransparente para seleccionar región.
    Devuelve (x1, y1, x2, y2) en píxeles físicos, o None si se cancela.
    """
    result  = [None]
    start   = [0, 0]      # coordenadas lógicas del punto de inicio del drag
    rect_id = [None]

    ov = tk.Toplevel(root)
    ov.overrideredirect(True)
    ov.attributes("-topmost", True)

    lw = ov.winfo_screenwidth()   # ancho lógico (post-DPI-scaling)
    lh = ov.winfo_screenheight()  # alto lógico
    ov.geometry(f"{lw}x{lh}+0+0")

    # Factor de escala lógico → físico (para el crop real)
    ratio_x = screenshot.width  / lw
    ratio_y = screenshot.height / lh

    tk_img = ImageTk.PhotoImage(screenshot.resize((lw, lh), Image.LANCZOS))

    cv = tk.Canvas(ov, cursor="cross", highlightthickness=0)
    cv.pack(fill=tk.BOTH, expand=True)
    cv.create_image(0, 0, anchor="nw", image=tk_img)
    # Overlay oscuro semitransparente
    cv.create_rectangle(0, 0, lw, lh, fill="black", stipple="gray25", outline="")
    cv.create_text(
        lw // 2, 36,
        text="Arrastra para seleccionar  ·  ESC para cancelar",
        fill="white", font=("Segoe UI", 13, "bold"),
    )

    def on_press(e):
        start[0], start[1] = e.x, e.y

    def on_drag(e):
        if rect_id[0]:
            cv.delete(rect_id[0])
        rect_id[0] = cv.create_rectangle(
            start[0], start[1], e.x, e.y,
            outline="#00e676", width=2,
        )

    def on_release(e):
        x1 = min(start[0], e.x)
        y1 = min(start[1], e.y)
        x2 = max(start[0], e.x)
        y2 = max(start[1], e.y)
        if (x2 - x1) > 5 and (y2 - y1) > 5:
            # Convertir coords lógicas → físicas para el crop
            result[0] = (
                int(x1 * ratio_x), int(y1 * ratio_y),
                int(x2 * ratio_x), int(y2 * ratio_y),
            )
        ov.destroy()

    cv.bind("<ButtonPress-1>",   on_press)
    cv.bind("<B1-Motion>",       on_drag)
    cv.bind("<ButtonRelease-1>", on_release)
    ov.bind("<Escape>", lambda _: ov.destroy())

    root.wait_window(ov)   # event loop sigue corriendo, pero bloqueamos aquí
    return result[0]


# ── Ventanas auxiliares ───────────────────────────────────────────────────────
def make_loading_window(root: tk.Tk) -> tk.Toplevel:
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg="#1e1e2e")
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    w, h = 240, 64
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
    tk.Label(
        win, text="⏳  Traduciendo…",
        bg="#1e1e2e", fg="#cdd6f4",
        font=("Segoe UI", 13),
    ).pack(expand=True)
    win.update()
    return win


def show_result_window(root: tk.Tk, text: str) -> None:
    win = tk.Toplevel(root)
    win.title("Traducción")
    win.attributes("-topmost", True)
    win.configure(bg="#1e1e2e", padx=14, pady=12)
    win.resizable(True, True)

    tk.Label(
        win, text="📋  Traducción al español",
        bg="#1e1e2e", fg="#89b4fa",
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w", pady=(0, 6))

    frame = tk.Frame(win, bg="#1e1e2e")
    frame.pack(fill=tk.BOTH, expand=True)

    txt = tk.Text(
        frame, wrap=tk.WORD,
        bg="#313244", fg="#cdd6f4",
        font=("Segoe UI", 11), relief=tk.FLAT,
        padx=10, pady=8, height=12, width=55,
    )
    sb = tk.Scrollbar(frame, command=txt.yview)
    txt.configure(yscrollcommand=sb.set)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    txt.insert(tk.END, text)
    txt.configure(state=tk.DISABLED)

    tk.Button(
        win, text="✕  Cerrar", command=win.destroy,
        bg="#f38ba8", fg="#1e1e2e",
        font=("Segoe UI", 10, "bold"),
        relief=tk.FLAT, padx=12, pady=5, cursor="hand2",
    ).pack(pady=(10, 0))


# ── Aplicación principal ──────────────────────────────────────────────────────
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()   # ventana raíz oculta; solo la usamos como ancla
        self._busy = False

        keyboard.add_hotkey(HOTKEY, lambda: _trigger_queue.put(True))
        self.root.after(100, self._poll)

    def _poll(self):
        """Revisa la cola cada 100 ms para detectar el hotkey."""
        try:
            _trigger_queue.get_nowait()
            if not self._busy:
                self._busy = True
                # Descarta presses extra acumulados
                while not _trigger_queue.empty():
                    _trigger_queue.get_nowait()
                # Pequeño delay para que las teclas se suelten antes del screenshot
                self.root.after(80, self._capture_and_translate)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _capture_and_translate(self):
        screenshot = grab_screen()
        sel = select_region(self.root, screenshot)

        if not sel:
            self._busy = False
            return

        cropped = screenshot.crop(sel)
        loading = make_loading_window(self.root)

        def worker():
            try:
                result = translate_image(cropped)
            except Exception as exc:
                result = f"❌  Error al contactar Groq:\n{exc}"
            # Toda interacción con tkinter debe ocurrir en el hilo principal
            self.root.after(0, loading.destroy)
            self.root.after(0, lambda: show_result_window(self.root, result))
            self.root.after(0, self._release)

        threading.Thread(target=worker, daemon=True).start()

    def _release(self):
        self._busy = False

    def run(self):
        print("✅  Screen Translator activo")
        print(f"   Hotkey : {HOTKEY}")
        print(f"   Modelo : {MODEL}")
        print("   Ctrl+C para salir\n")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    App().run()
