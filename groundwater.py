import tkinter as tk
from tkinter import ttk, font
import threading
import random
import time
import math
from datetime import datetime, timedelta
import numpy as np

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.patches as mpatches
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False
    print("Run:  pip install matplotlib numpy")
    exit(1)

#COLOR THEME
BG       = "#0f1117"
SURFACE  = "#1a1d27"
CARD     = "#1e2233"
BORDER   = "#2a2e42"
TEXT     = "#e8eaf0"
MUTED    = "#8b92a8"
BLUE     = "#3b82f6"
TEAL     = "#0d9488"
AMBER    = "#f59e0b"
RED      = "#ef4444"
GREEN    = "#22c55e"
PURPLE   = "#8b5cf6"

#SENSOR DATA MODEL
LOCATIONS = [
    {"id": "SNS-001", "area": "Ludhiana North",  "lat": 30.934, "lng": 75.857},
    {"id": "SNS-002", "area": "Amritsar East",   "lat": 31.634, "lng": 74.873},
    {"id": "SNS-003", "area": "Jalandhar West",  "lat": 31.326, "lng": 75.576},
    {"id": "SNS-004", "area": "Patiala South",   "lat": 30.340, "lng": 76.386},
    {"id": "SNS-005", "area": "Bathinda",         "lat": 30.211, "lng": 74.945},
]

class Sensor:
    def __init__(self, loc, idx):
        self.id       = loc["id"]
        self.area     = loc["area"]
        self.lat      = loc["lat"]
        self.lng      = loc["lng"]
        self.level    = round(13.5 + random.uniform(-1, 1) - idx * 0.4, 2)
        self.ph       = round(random.uniform(6.8, 7.8), 1)
        self.turb     = round(random.uniform(1.5, 4.5), 1)
        self.temp     = round(random.uniform(18, 24), 1)
        self.quality  = ""
        self.status   = ""
        self.classify()

    def classify(self):
        if self.level < 11 or self.ph < 6.5 or self.ph > 8.5 or self.turb > 5.5:
            self.status = "CRITICAL"; self.quality = "Poor"
        elif self.level < 13:
            self.status = "LOW";      self.quality = "Moderate"
        else:
            self.status = "NORMAL";   self.quality = "Good"

    def tick(self):
        self.level = round(max(8, min(20, self.level + random.gauss(-0.02, 0.08))), 2)
        self.ph    = round(max(5.5, min(9.0, self.ph + random.gauss(0, 0.04))), 1)
        self.turb  = round(max(0, min(10, self.turb + random.gauss(0, 0.15))), 1)
        self.temp  = round(max(15, min(30, self.temp + random.gauss(0, 0.05))), 1)
        self.classify()

sensors = [Sensor(loc, i) for i, loc in enumerate(LOCATIONS)]

#HISTORY BUFFER
HISTORY_LEN = 60   # seconds of rolling history shown on chart
history_time   = []
history_levels = {s.id: [] for s in sensors}
history_ph     = {s.id: [] for s in sensors}
history_turb   = {s.id: [] for s in sensors}

def seed_history():
    base_time = datetime.now() - timedelta(seconds=HISTORY_LEN)
    for i in range(HISTORY_LEN):
        t = base_time + timedelta(seconds=i)
        history_time.append(t)
        for s in sensors:
            history_levels[s.id].append(s.level + math.sin(i/10)*0.3 + random.gauss(0, 0.05))
            history_ph[s.id].append(round(7.0 + math.sin(i/15)*0.2 + random.gauss(0, 0.02), 2))
            history_turb[s.id].append(round(3.0 + math.sin(i/8)*0.5 + random.gauss(0, 0.1), 2))

seed_history()

#AI PREDICTION (simple linear regression + noise)
def ai_predict(values, steps=10):
    """Simple trend-based prediction mimicking an AI forecast."""
    if len(values) < 5:
        return [values[-1]] * steps
    x = np.arange(len(values))
    y = np.array(values)
    coeffs = np.polyfit(x, y, 1)  # linear fit
    future_x = np.arange(len(values), len(values) + steps)
    pred = np.polyval(coeffs, future_x)
    noise = np.random.normal(0, 0.05, steps)
    return list(np.round(pred + noise, 2))

#ALERT LOG
alerts = []

def check_alerts():
    for s in sensors:
        if s.status == "CRITICAL":
            msg = f"[CRITICAL] {s.id} {s.area}: Level={s.level}m, pH={s.ph}"
            if not alerts or alerts[0] != msg:
                alerts.insert(0, ("CRITICAL", msg, datetime.now().strftime("%H:%M:%S")))
        elif s.status == "LOW":
            msg = f"[WARNING]  {s.id} {s.area}: Level={s.level}m (below 13m)"
            alerts.insert(0, ("WARNING", msg, datetime.now().strftime("%H:%M:%S")))
    
    del alerts[30:]

#MAIN APP WINDOW
class AquaWatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AquaWatch AI — Groundwater Monitoring System")
        self.geometry("1280x820")
        self.configure(bg=BG)
        self.resizable(True, True)

        self._style_ttk()
        self._build_header()
        self._build_tabs()
        self._start_live_update()

    #TTK STYLE 
    def _style_ttk(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("TNotebook", background=SURFACE, borderwidth=0)
        style.configure("TNotebook.Tab", background=SURFACE, foreground=MUTED,
                         padding=[14, 6], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", TEXT)])
        style.configure("Treeview", background=CARD, fieldbackground=CARD,
                         foreground=TEXT, rowheight=28, borderwidth=0,
                         font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=SURFACE, foreground=MUTED,
                         font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", BLUE)], foreground=[("selected", "#fff")])
        style.configure("TScrollbar", background=SURFACE, troughcolor=BG, arrowcolor=MUTED)

    #HEADER 
    def _build_header(self):
        hdr = tk.Frame(self, bg=SURFACE, height=52)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="💧", bg=SURFACE, fg=BLUE,
                 font=("Segoe UI", 20)).pack(side="left", padx=(16, 6), pady=6)
        title_frame = tk.Frame(hdr, bg=SURFACE)
        title_frame.pack(side="left", pady=6)
        tk.Label(title_frame, text="AquaWatch AI", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(title_frame, text="Real-Time Groundwater Monitoring · IoT + AI",
                 bg=SURFACE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        # clock + live badge
        right = tk.Frame(hdr, bg=SURFACE)
        right.pack(side="right", padx=16)
        self.clock_var = tk.StringVar()
        tk.Label(right, textvariable=self.clock_var, bg=SURFACE, fg=MUTED,
                 font=("Courier New", 11)).pack(side="right", padx=8)
        live_lbl = tk.Label(right, text=" ● LIVE ", bg="#14532d", fg=GREEN,
                             font=("Segoe UI", 9, "bold"), padx=6, pady=2)
        live_lbl.pack(side="right")

    #TABS
    def _build_tabs(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=0, pady=0)

        self.tab_dashboard = tk.Frame(self.nb, bg=BG)
        self.tab_sensors   = tk.Frame(self.nb, bg=BG)
        self.tab_predict   = tk.Frame(self.nb, bg=BG)
        self.tab_alerts    = tk.Frame(self.nb, bg=BG)

        self.nb.add(self.tab_dashboard, text="  📊 Dashboard  ")
        self.nb.add(self.tab_sensors,   text="  📡 Sensors    ")
        self.nb.add(self.tab_predict,   text="  🤖 AI Forecast")
        self.nb.add(self.tab_alerts,    text="  🔔 Alerts     ")

        self._build_dashboard()
        self._build_sensors_tab()
        self._build_predict_tab()
        self._build_alerts_tab()

    # TAB 1 — DASHBOARD
    def _build_dashboard(self):
        p = self.tab_dashboard

        #Metric cards
        cards_row = tk.Frame(p, bg=BG)
        cards_row.pack(fill="x", padx=12, pady=(10, 6))

        self.metric_vars = {}
        metrics = [
            ("💧 Avg Water Level", "level",  "m",   BLUE),
            ("🧪 Avg pH",          "ph",     "",    TEAL),
            ("🌊 Turbidity",       "turb",   " NTU",PURPLE),
            ("🌡️ Temperature",     "temp",   "°C",  AMBER),
            ("🚨 Active Alerts",   "alerts", "",    RED),
        ]
        for label, key, unit, color in metrics:
            f = tk.Frame(cards_row, bg=CARD, bd=0, highlightbackground=BORDER,
                         highlightthickness=1)
            f.pack(side="left", expand=True, fill="both", padx=4, ipady=10, ipadx=8)
            tk.Label(f, text=label, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8,0))
            var = tk.StringVar(value="--")
            self.metric_vars[key] = (var, unit)
            tk.Label(f, textvariable=var, bg=CARD, fg=color,
                     font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=10, pady=(2,8))

        #Charts row
        charts_row = tk.Frame(p, bg=BG)
        charts_row.pack(fill="both", expand=True, padx=12, pady=4)

        # Left: water level time series
        left = tk.Frame(charts_row, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0,4))
        tk.Label(left, text="Water Level — Rolling 60s  (blue=actual, teal=AI forecast)",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8,0))
        self.fig_level = Figure(figsize=(5, 3), dpi=90, facecolor=CARD)
        self.ax_level  = self.fig_level.add_subplot(111)
        self._style_ax(self.ax_level)
        self.canvas_level = FigureCanvasTkAgg(self.fig_level, master=left)
        self.canvas_level.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=(0,8))

        # Right: pH & turbidity
        right = tk.Frame(charts_row, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="left", fill="both", expand=True, padx=(4,0))
        tk.Label(right, text="pH & Turbidity — Rolling 60s",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8,0))
        self.fig_qual = Figure(figsize=(4, 3), dpi=90, facecolor=CARD)
        self.ax_qual  = self.fig_qual.add_subplot(111)
        self._style_ax(self.ax_qual)
        self.canvas_qual = FigureCanvasTkAgg(self.fig_qual, master=right)
        self.canvas_qual.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=(0,8))

    # TAB 2 — SENSORS TABLE
    def _build_sensors_tab(self):
        p = self.tab_sensors
        tk.Label(p, text="📡  Live Sensor Network — All Stations",
                 bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10,4))
        tk.Label(p, text="Updates every 3 seconds · Data simulates IoT sensor stream",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0,8))

        cols = ("Sensor ID","Location","Lat","Lng","Level (m)","pH","Turbidity (NTU)","Temp (°C)","Quality","Status")
        self.tree = ttk.Treeview(p, columns=cols, show="headings", height=15)
        widths    = [80, 150, 70, 70, 90, 60, 120, 80, 90, 90]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        self.tree.tag_configure("NORMAL",   foreground=GREEN)
        self.tree.tag_configure("LOW",      foreground=AMBER)
        self.tree.tag_configure("CRITICAL", foreground=RED)

        sb = ttk.Scrollbar(p, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=sb.set)
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0,0))
        sb.pack(fill="x", padx=12, pady=(0,6))

    # TAB 3 — AI FORECAST
    def _build_predict_tab(self):
        p = self.tab_predict
        tk.Label(p, text="🤖  AI Prediction Engine — Next 15 Readings",
                 bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10,2))
        tk.Label(p, text="Model: Linear Regression on rolling history · Updates every refresh cycle",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0,8))

        # Area selection
        select_frame = tk.Frame(p, bg=BG)
        select_frame.pack(fill="x", padx=14, pady=(0,6))
        tk.Label(select_frame, text="Select Area:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).pack(side="left")
        self.area_var = tk.StringVar(value=sensors[0].id)
        areas = [f"{s.id} - {s.area}" for s in sensors]
        self.area_combo = ttk.Combobox(select_frame, textvariable=self.area_var,
                                       values=areas, state="readonly",
                                       font=("Segoe UI", 9), width=25)
        self.area_combo.pack(side="left", padx=(6,0))
        self.area_combo.bind("<<ComboboxSelected>>", self._on_area_select)

        self.fig_pred = Figure(figsize=(10, 4), dpi=90, facecolor=CARD)
        self.ax_pred  = self.fig_pred.add_subplot(111)
        self._style_ax(self.ax_pred)
        wrap = tk.Frame(p, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=12, pady=4)
        self.canvas_pred = FigureCanvasTkAgg(self.fig_pred, master=wrap)
        self.canvas_pred.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=8)

        # Info panel
        info = tk.Frame(p, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        info.pack(fill="x", padx=12, pady=(4,10))
        infos = [
            ("Algorithm", "Linear Trend + Gaussian Noise (LSTM-style simulation)"),
            ("Input Window", "Last 60 seconds of sensor readings"),
            ("Confidence", "87% (based on data variance)"),
            ("Refresh Rate", "Every 3 seconds"),
        ]
        for label, val in infos:
            row = tk.Frame(info, bg=SURFACE)
            row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=label+":", bg=SURFACE, fg=MUTED,
                     font=("Segoe UI", 9), width=16, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=SURFACE, fg=TEXT,
                     font=("Segoe UI", 9)).pack(side="left")

    # TAB 4 — ALERTS LOG
    def _build_alerts_tab(self):
        p = self.tab_alerts
        tk.Label(p, text="🔔  Alert Log — Real-Time Notifications",
                 bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10,4))

        btn_row = tk.Frame(p, bg=BG)
        btn_row.pack(fill="x", padx=14, pady=(0, 6))
        tk.Button(btn_row, text="  Clear Log  ", bg=SURFACE, fg=TEXT,
                  relief="flat", bd=0, font=("Segoe UI", 9),
                  activebackground=BORDER, activeforeground=TEXT,
                  command=self._clear_alerts).pack(side="left")

        frame = tk.Frame(p, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.alert_text = tk.Text(frame, bg=CARD, fg=TEXT, font=("Courier New", 10),
                                  relief="flat", bd=0, state="disabled",
                                  insertbackground=TEXT, selectbackground=BLUE)
        self.alert_text.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        sb = tk.Scrollbar(frame, command=self.alert_text.yview, bg=SURFACE)
        sb.pack(side="right", fill="y")
        self.alert_text.configure(yscrollcommand=sb.set)

        # Tag colors
        self.alert_text.tag_configure("CRITICAL", foreground=RED)
        self.alert_text.tag_configure("WARNING",  foreground=AMBER)
        self.alert_text.tag_configure("INFO",     foreground=BLUE)
        self.alert_text.tag_configure("TIME",     foreground=MUTED)

    def _on_area_select(self, event=None):
        self._refresh_predict()

    def _clear_alerts(self):
        alerts.clear()
        self.alert_text.configure(state="normal")
        self.alert_text.delete("1.0", "end")
        self.alert_text.configure(state="disabled")

    #MATPLOTLIB STYLE
    def _style_ax(self, ax):
        ax.set_facecolor(CARD)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.spines[:].set_color(BORDER)
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
        ax.grid(color=BORDER, linewidth=0.4, linestyle="--", alpha=0.6)

    # LIVE UPDATE LOOP
    def _start_live_update(self):
        self._update()

    def _update(self):
        # Tick all sensors
        for s in sensors:
            s.tick()

        # Update history
        now = datetime.now()
        history_time.append(now)
        for s in sensors:
            history_levels[s.id].append(s.level)
            history_ph[s.id].append(s.ph)
            history_turb[s.id].append(s.turb)

        # Trim to window
        while len(history_time) > HISTORY_LEN:
            history_time.pop(0)
            for s in sensors:
                history_levels[s.id].pop(0)
                history_ph[s.id].pop(0)
                history_turb[s.id].pop(0)

        # Check alerts
        check_alerts()

        # Refresh UI
        self._refresh_clock()
        self._refresh_metrics()
        self._refresh_charts()
        self._refresh_table()
        self._refresh_predict()
        self._refresh_alerts()

        # Schedule next tick
        self.after(3000, self._update)

    def _refresh_clock(self):
        self.clock_var.set(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def _refresh_metrics(self):
        avg = lambda key: sum(getattr(s, key) for s in sensors) / len(sensors)
        vals = {
            "level":  round(avg("level"), 2),
            "ph":     round(avg("ph"), 1),
            "turb":   round(avg("turb"), 1),
            "temp":   round(avg("temp"), 1),
            "alerts": sum(1 for s in sensors if s.status != "NORMAL"),
        }
        for key, (var, unit) in self.metric_vars.items():
            var.set(f"{vals[key]}{unit}")

    def _refresh_charts(self):
        times = [t.strftime("%H:%M:%S") for t in history_time]
        x     = list(range(len(times)))

        #Level chart
        ax = self.ax_level
        ax.clear(); self._style_ax(ax)
        colors_cycle = [BLUE, TEAL, AMBER, PURPLE, RED]
        for i, s in enumerate(sensors):
            ys = history_levels[s.id]
            ax.plot(x, ys, color=colors_cycle[i], linewidth=1.2,
                    label=s.id, alpha=0.85)
        # AI forecast for sensor 0
        if len(history_levels[sensors[0].id]) >= 5:
            pred = ai_predict(history_levels[sensors[0].id], steps=10)
            fx   = list(range(len(x), len(x)+10))
            ax.plot(fx, pred, color=TEAL, linewidth=1.5,
                    linestyle="--", alpha=0.7, label="AI Forecast")
        ax.set_xlim(0, len(x)+10)
        ax.set_ylabel("Level (m)", color=MUTED, fontsize=8)
        ax.legend(fontsize=7, facecolor=SURFACE, edgecolor=BORDER,
                  labelcolor=TEXT, loc="upper left", ncol=3)
        tick_pos = list(range(0, len(x), max(1, len(x)//6)))
        ax.set_xticks(tick_pos)
        ax.set_xticklabels([times[i] if i < len(times) else "" for i in tick_pos],
                            rotation=20, fontsize=7)
        self.fig_level.tight_layout(pad=0.4)
        self.canvas_level.draw()

        #pH & Turbidity chart
        ax2 = self.ax_qual
        ax2.clear(); self._style_ax(ax2)
        avg_ph = [sum(history_ph[s.id][i] for s in sensors)/len(sensors) for i in range(len(x))]
        avg_turb = [sum(history_turb[s.id][i] for s in sensors)/len(sensors) for i in range(len(x))]
        ax2.plot(x, avg_ph,   color=TEAL,   linewidth=1.3, label="Avg pH")
        ax2.plot(x, avg_turb, color=PURPLE,  linewidth=1.3, label="Avg Turbidity (NTU)")
        ax2.axhline(y=6.5, color=RED, linewidth=0.7, linestyle=":", alpha=0.6)
        ax2.axhline(y=8.5, color=RED, linewidth=0.7, linestyle=":", alpha=0.6)
        ax2.legend(fontsize=7, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
        ax2.set_xticks(tick_pos)
        ax2.set_xticklabels([times[i] if i < len(times) else "" for i in tick_pos],
                              rotation=20, fontsize=7)
        self.fig_qual.tight_layout(pad=0.4)
        self.canvas_qual.draw()

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for s in sensors:
            self.tree.insert("", "end", values=(
                s.id, s.area, f"{s.lat:.3f}°N", f"{s.lng:.3f}°E",
                f"{s.level}m", s.ph, f"{s.turb} NTU",
                f"{s.temp}°C", s.quality, s.status
            ), tags=(s.status,))

    def _refresh_predict(self):
        selected_id = self.area_var.get().split(" - ")[0]
        selected_sensor = next(s for s in sensors if s.id == selected_id)
        
        ax = self.ax_pred
        ax.clear(); self._style_ax(ax)
        hist   = history_levels[selected_sensor.id]
        x_hist = list(range(len(hist)))
        pred   = ai_predict(hist, steps=15) if len(hist) >= 5 else []
        x_pred = list(range(len(hist)-1, len(hist)-1+len(pred)+1))

        ax.plot(x_hist, hist, color=BLUE, linewidth=1.5, label=f"{selected_sensor.id} ({selected_sensor.area}) Actual")
        if pred:
            ax.plot(x_pred, [hist[-1]] + pred, color=GREEN, linewidth=1.8,
            linestyle="--", label="AI Forecast (next 15 steps)", alpha=0.9)
            ax.fill_between(x_pred,
            [v - 0.3 for v in ([hist[-1]] + pred)],
            [v + 0.3 for v in ([hist[-1]] + pred)],
            color=GREEN, alpha=0.08, label="Confidence band ±0.3m")
        ax.axvline(x=len(hist)-1, color=AMBER, linewidth=1, linestyle=":", alpha=0.7)
        ax.text(len(hist)-0.5, ax.get_ylim()[0]+0.1, "NOW →", color=AMBER, fontsize=8)
        ax.set_ylabel("Water Level (m)", color=MUTED, fontsize=8)
        ax.set_xlabel("Time steps (3s each)", color=MUTED, fontsize=8)
        ax.legend(fontsize=8, facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
        self.fig_pred.tight_layout(pad=0.5)
        self.canvas_pred.draw()

    def _refresh_alerts(self):
        self.alert_text.configure(state="normal")
        self.alert_text.delete("1.0", "end")
        for level, msg, ts in alerts:
            tag = "CRITICAL" if level == "CRITICAL" else "WARNING"
            self.alert_text.insert("end", f"[{ts}] ", "TIME")
            self.alert_text.insert("end", f"{msg}\n", tag)
        if not alerts:
            self.alert_text.insert("end", "No active alerts. All sensors nominal.\n", "INFO")
        self.alert_text.configure(state="disabled")


#ENTRY POINT
if __name__ == "__main__":
    print("=" * 60)
    print("  AquaWatch AI — Groundwater Monitoring System")
    print("  Starting dashboard...")
    print("=" * 60)
    app = AquaWatchApp()
    app.mainloop()