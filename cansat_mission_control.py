import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import math
from telemetry_simulator import TelemetrySimulator

class CanSatMissionControl:
    def __init__(self, root):
        self.root = root
        self.root.title("CANSAT MISSION CONTROL")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1f2e')
        
        # Colores del tema
        self.bg_dark = '#1a1f2e'
        self.bg_panel = '#243447'
        self.bg_card = '#2a3f5f'
        self.text_white = '#ffffff'
        self.text_gray = '#8b9bb8'
        self.blue_accent = '#4a9eff'
        self.orange_accent = '#ff8c42'
        self.green_accent = '#4ade80'
        
        # Control de misión
        self.mission_running = False
        self.mission_start_time = None
        self.elapsed_seconds = 0
        
        # Variables para datos en tiempo real
        # Inicialmente no hay datos; todo empieza en cero.
        self.pressure_value = tk.DoubleVar(value=0.0)
        # simulador externo que genera telemetría aleatoria
        self.simulator = TelemetrySimulator()
        # Aquí va la entrada de TEMPERATURA AMBIENTAL (°C)
        self.temperature_value = tk.DoubleVar(value=0.0)
        # Aquí va la entrada de ALTITUD (metros sobre el nivel del mar)
        self.altitude_value = tk.DoubleVar(value=0.0)
        # Aquí va la entrada de TASA DE CAMBIO DE ALTITUD (m/s)
        self.altitude_rate = tk.DoubleVar(value=0.0)
        # Aquí va la entrada de LATENCIA DE SEÑAL (milisegundos)
        self.signal_latency = tk.DoubleVar(value=0.0)
        
        # Datos para gráficas
        # Historicos iniciales vacíos para evitar que la línea se dibuje antes
        # de que llegue cualquier valor.
        self.velocity_time = np.linspace(-120, 0, 100)  # Últimos 120 segundos
        self.velocity_data = np.zeros_like(self.velocity_time)
        # Gráfica de G-force también arranca en cero
        self.gforce_time = np.linspace(-1.5, 4.0, 100)
        self.gforce_data = np.zeros_like(self.gforce_time)
        
        # Referencias a widgets que se actualizarán
        self.pressure_label = None
        self.temp_label = None
        self.altitude_label = None
        self.altitude_rate_label = None
        self.latency_label = None
        
        # Crear interfaz
        self.create_header()
        self.create_main_content()
        self.create_footer()

        # iniciar la simulación automáticamente para demostración
        self.toggle_mission()
        
    def create_header(self):
        """Crear barra superior con título y controles"""
        header = tk.Frame(self.root, bg=self.bg_dark, height=70)
        header.pack(fill=tk.X, padx=20, pady=(10, 0))
        header.pack_propagate(False)
        
        # Logo y título
        logo_frame = tk.Frame(header, bg=self.bg_dark)
        logo_frame.pack(side=tk.LEFT)
        
        # Icono de cohete (simulado con texto)
        rocket_label = tk.Label(logo_frame, text="🚀", font=('Arial', 30), 
                               bg=self.bg_dark, fg=self.blue_accent)
        rocket_label.pack(side=tk.LEFT, padx=(0, 15))
        
        title_frame = tk.Frame(logo_frame, bg=self.bg_dark)
        title_frame.pack(side=tk.LEFT)
        
        title = tk.Label(title_frame, text="CANSAT ", font=('Arial', 20, 'bold'), 
                        bg=self.bg_dark, fg=self.text_white)
        title.pack(side=tk.LEFT)
        
        title2 = tk.Label(title_frame, text="MISSION CONTROL", font=('Arial', 20, 'bold'), 
                         bg=self.bg_dark, fg=self.blue_accent)
        title2.pack(side=tk.LEFT)
        
        status = tk.Label(title_frame, text="● LIVE UPLINK ACTIVE", 
                         font=('Arial', 9), bg=self.bg_dark, fg=self.green_accent)
        status.pack(anchor='w')
        
        # Panel derecho - Timer y botón START
        right_panel = tk.Frame(header, bg=self.bg_dark)
        right_panel.pack(side=tk.RIGHT)
        
        timer_frame = tk.Frame(right_panel, bg=self.bg_dark)
        timer_frame.pack(side=tk.LEFT, padx=20)
        
        timer_label = tk.Label(timer_frame, text="MISSION TIMER", 
                              font=('Arial', 9), bg=self.bg_dark, fg=self.text_gray)
        timer_label.pack()
        
        # Aquí se muestra el TIEMPO DE MISIÓN (T+ HH:MM:SS)
        self.timer_display = tk.Label(timer_frame, text="T+ 00:00:00", 
                                     font=('Arial', 18, 'bold'), 
                                     bg=self.bg_dark, fg=self.text_white)
        self.timer_display.pack()
        
        # Botón START/STOP
        self.start_btn = tk.Button(right_panel, text="▶ START", 
                               font=('Arial', 11, 'bold'),
                               bg=self.green_accent, fg=self.text_white,
                               relief=tk.FLAT, padx=20, pady=8,
                               cursor='hand2',
                               command=self.toggle_mission)
        self.start_btn.pack(side=tk.LEFT)
        
    def create_main_content(self):
        """Crear contenido principal"""
        main = tk.Frame(self.root, bg=self.bg_dark)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Frame izquierdo (tarjetas y gráficas)
        left_frame = tk.Frame(main, bg=self.bg_dark)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Fila superior - Tarjetas de sensores
        top_row = tk.Frame(left_frame, bg=self.bg_dark)
        top_row.pack(fill=tk.X, pady=(0, 15))
        
        # Tarjeta de presión atmosférica
        self.create_circular_gauge(top_row, "ATMOSPHERIC", "0", "kPa", 
                                   "Pressure", self.blue_accent, 0.0, 'pressure').pack(side=tk.LEFT, padx=(0, 15))
        
        # Tarjeta de temperatura
        self.create_circular_gauge(top_row, "ENVIRONMENT", "0", "°C", 
                                   "Temperature", self.orange_accent, 0.0, 'temperature').pack(side=tk.LEFT, padx=(0, 15))
        
        # Tarjeta de altitud y latencia
        self.create_altitude_card(top_row).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Fila media - Gráficas
        middle_row = tk.Frame(left_frame, bg=self.bg_dark)
        middle_row.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Gráfica de distribución de velocidad
        self.create_velocity_graph(middle_row).pack(side=tk.LEFT, fill=tk.BOTH, 
                                                    expand=True, padx=(0, 15))
        
        # Gráfica de aceleración G-Force
        self.create_gforce_graph(middle_row).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Fila inferior - Cámaras
        bottom_row = tk.Frame(left_frame, bg=self.bg_dark)
        bottom_row.pack(fill=tk.BOTH, expand=True)
        
        self.create_camera_panel(bottom_row).pack(fill=tk.BOTH, expand=True)
        
        # Panel derecho - Log y controles
        right_frame = tk.Frame(main, bg=self.bg_dark, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(15, 0))
        right_frame.pack_propagate(False)
        
        self.create_log_panel(right_frame)
        
    def create_circular_gauge(self, parent, label_top, value, unit, label_bottom, color, fill_percent, gauge_type):
        """Crear medidor circular (presión/temperatura)"""
        card = tk.Frame(parent, bg=self.bg_panel, width=210, height=180)
        card.pack_propagate(False)
        
        # Etiqueta superior
        top_label = tk.Label(card, text=label_top, font=('Arial', 9, 'bold'), 
                            bg=self.bg_panel, fg=color)
        top_label.pack(pady=(15, 10))
        
        # Canvas para círculo
        canvas = tk.Canvas(card, width=120, height=120, bg=self.bg_panel, 
                          highlightthickness=0)
        canvas.pack()
        
        # Círculo de fondo (gris) - reducir ancho de trazo para no entrar en el área central
        arc_width = 10
        canvas.create_arc(10, 10, 110, 110, start=0, extent=359.9, 
                 outline='#3a4f6f', width=arc_width, style=tk.ARC, tags='bg_arc')
        
        # Círculo de progreso (aquí se actualiza según el VALOR DEL SENSOR)
        extent = 359.9 * fill_percent
        canvas.create_arc(10, 10, 110, 110, start=90, extent=-extent, 
                 outline=color, width=arc_width, style=tk.ARC, tags='progress_arc')
        
        # Valor central (mover un poco hacia abajo y reducir tamaño de fuente)
        value_label = tk.Label(canvas, text=value, font=('Arial', 24, 'bold'), 
                      bg=self.bg_panel, fg=self.text_white)
        value_label.place(relx=0.5, rely=0.56, anchor='center')

        # Unidad (mover hacia abajo para evitar solapamiento)
        unit_label = tk.Label(canvas, text=unit, font=('Arial', 10), 
                     bg=self.bg_panel, fg=self.text_gray)
        unit_label.place(relx=0.5, rely=0.78, anchor='center')

        # Ajustes específicos por tipo de medidor para evitar solapamiento
        if gauge_type == 'pressure':
            # Presión atmosférica: número más pequeño para caber dentro del arco
            value_label.config(font=('Arial', 20, 'bold'))
            value_label.place_configure(relx=0.5, rely=0.56)
            unit_label.config(font=('Arial', 9))
            unit_label.place_configure(relx=0.5, rely=0.80)
        else:
            # Otros (ej. temperatura) mantienen el tamaño por defecto
            value_label.config(font=('Arial', 24, 'bold'))
            value_label.place_configure(relx=0.5, rely=0.56)
            unit_label.config(font=('Arial', 10))
            unit_label.place_configure(relx=0.5, rely=0.78)
        
        # Etiqueta inferior
        bottom_label = tk.Label(card, text=label_bottom, font=('Arial', 11), 
                               bg=self.bg_panel, fg=self.text_white)
        bottom_label.pack(pady=(5, 10))
        
        # Guardar referencias para actualización
        if gauge_type == 'pressure':
            self.pressure_label = value_label
            self.pressure_canvas = canvas
            self.pressure_color = color
        elif gauge_type == 'temperature':
            self.temp_label = value_label
            self.temp_canvas = canvas
            self.temp_color = color
        
        return card
        
    def create_altitude_card(self, parent):
        """Crear tarjeta de altitud y latencia de señal"""
        card = tk.Frame(parent, bg=self.bg_panel)
        
        # Contenedor interno
        content = tk.Frame(card, bg=self.bg_panel)
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Sección izquierda - Altitud
        left_section = tk.Frame(content, bg=self.bg_panel)
        left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        alt_label = tk.Label(left_section, text="ALTITUDE (ASL)", 
                            font=('Arial', 9), bg=self.bg_panel, fg=self.text_gray)
        alt_label.pack(anchor='w')
        
        # Aquí se muestra el valor de ALTITUD actual
        alt_value_frame = tk.Frame(left_section, bg=self.bg_panel)
        alt_value_frame.pack(anchor='w', pady=(10, 5))
        
        self.altitude_label = tk.Label(alt_value_frame, text="0.0", 
                            font=('Arial', 36, 'bold'), 
                            bg=self.bg_panel, fg=self.text_white)
        self.altitude_label.pack(side=tk.LEFT)
        
        alt_unit = tk.Label(alt_value_frame, text="m", 
                           font=('Arial', 18, 'bold'), 
                           bg=self.bg_panel, fg=self.blue_accent)
        alt_unit.pack(side=tk.LEFT, padx=(5, 0), pady=(10, 0))
        
        # Tasa de cambio (aquí va la VELOCIDAD VERTICAL)
        rate_frame = tk.Frame(left_section, bg=self.bg_panel)
        rate_frame.pack(anchor='w')
        
        rate_icon = tk.Label(rate_frame, text="📈", font=('Arial', 12), 
                            bg=self.bg_panel)
        rate_icon.pack(side=tk.LEFT)
        
        self.altitude_rate_label = tk.Label(rate_frame, text="0.0 m/s", 
                             font=('Arial', 11), bg=self.bg_panel, fg=self.green_accent)
        self.altitude_rate_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Sección derecha - Latencia
        right_section = tk.Frame(content, bg=self.bg_panel)
        right_section.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(30, 0))
        
        lat_label = tk.Label(right_section, text="SIGNAL LATENCY", 
                            font=('Arial', 9), bg=self.bg_panel, fg=self.text_gray)
        lat_label.pack(anchor='w')
        
        # Aquí se muestra la LATENCIA DE SEÑAL actual
        lat_value_frame = tk.Frame(right_section, bg=self.bg_panel)
        lat_value_frame.pack(anchor='w', pady=(10, 5))
        
        self.latency_label = tk.Label(lat_value_frame, text="0", 
                            font=('Arial', 36, 'bold'), 
                            bg=self.bg_panel, fg=self.text_white)
        self.latency_label.pack(side=tk.LEFT)
        
        lat_unit = tk.Label(lat_value_frame, text="ms", 
                           font=('Arial', 18, 'bold'), 
                           bg=self.bg_panel, fg=self.blue_accent)
        lat_unit.pack(side=tk.LEFT, padx=(5, 0), pady=(10, 0))
        
        # Estado de rango
        range_frame = tk.Frame(right_section, bg=self.bg_panel)
        range_frame.pack(anchor='w')
        
        range_icon = tk.Label(range_frame, text="📡", font=('Arial', 12), 
                             bg=self.bg_panel)
        range_icon.pack(side=tk.LEFT)
        
        range_label = tk.Label(range_frame, text="Optimal Range", 
                              font=('Arial', 11), bg=self.bg_panel, fg=self.text_gray)
        range_label.pack(side=tk.LEFT, padx=(5, 0))
        
        return card
        
    def create_velocity_graph(self, parent):
        """Crear gráfica de distribución de velocidad"""
        card = tk.Frame(parent, bg=self.bg_panel)
        
        # Encabezado
        header = tk.Frame(card, bg=self.bg_panel)
        header.pack(fill=tk.X, padx=20, pady=(15, 0))
        
        title_frame = tk.Frame(header, bg=self.bg_panel)
        title_frame.pack(side=tk.LEFT)
        
        icon = tk.Label(title_frame, text="📊", font=('Arial', 14), bg=self.bg_panel)
        icon.pack(side=tk.LEFT)
        
        title = tk.Label(title_frame, text="VELOCITY DISTRIBUTION", 
                        font=('Arial', 11, 'bold'), bg=self.bg_panel, fg=self.text_white)
        title.pack(side=tk.LEFT, padx=(8, 0))
        
        # Botones de control
        btn_frame = tk.Frame(header, bg=self.bg_panel)
        btn_frame.pack(side=tk.RIGHT)
        
        live_btn = tk.Label(btn_frame, text="LIVE", font=('Arial', 9, 'bold'),
                           bg=self.blue_accent, fg=self.text_white, 
                           padx=12, pady=4)
        live_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        time_btn = tk.Label(btn_frame, text="120s", font=('Arial', 9),
                           bg='#3a4f6f', fg=self.text_gray, 
                           padx=12, pady=4)
        time_btn.pack(side=tk.LEFT)
        
        # Gráfica con matplotlib en ALTA CALIDAD
        fig = Figure(figsize=(5, 2.5), dpi=100, facecolor=self.bg_panel)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.bg_panel)
        
        # Aquí se grafican los DATOS DE VELOCIDAD en función del tiempo
        # Los datos vienen de self.velocity_data y self.velocity_time
        self.velocity_line, = ax.plot(self.velocity_time, self.velocity_data, 
                                      color=self.blue_accent, linewidth=2.5, 
                                      antialiased=True)
        ax.fill_between(self.velocity_time, self.velocity_data, 
                        alpha=0.1, color=self.blue_accent)
        
        ax.set_xlim(-120, 0)
        ax.set_ylim(0, 30)
        ax.grid(True, alpha=0.1, color=self.text_gray)
        
        # Etiquetas de tiempo - Sin superposición
        ax.set_xticks([-120, -60, 0])
        ax.set_xticklabels(['T-120s', 'T-60s', 'T-0s'], color=self.text_gray, fontsize=8)
        ax.set_yticks([])
        
        # Quitar bordes innecesarios
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(self.text_gray)
        ax.spines['bottom'].set_alpha(0.3)
        
        # Ajustar márgenes para evitar superposición
        fig.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.15)
        
        # Integrar en tkinter con alta calidad
        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        self.velocity_canvas = canvas
        self.velocity_ax = ax
        self.velocity_fig = fig
        
        return card
        
    def create_gforce_graph(self, parent):
        """Crear gráfica de aceleración G-Force"""
        card = tk.Frame(parent, bg=self.bg_panel)
        
        # Encabezado
        header = tk.Frame(card, bg=self.bg_panel)
        header.pack(fill=tk.X, padx=20, pady=(15, 0))
        
        title_frame = tk.Frame(header, bg=self.bg_panel)
        title_frame.pack(side=tk.LEFT)
        
        icon = tk.Label(title_frame, text="📈", font=('Arial', 14), bg=self.bg_panel)
        icon.pack(side=tk.LEFT)
        
        title = tk.Label(title_frame, text="G-FORCE ACCELERATION", 
                        font=('Arial', 11, 'bold'), bg=self.bg_panel, fg=self.text_white)
        title.pack(side=tk.LEFT, padx=(8, 0))
        
        # Botones de control
        btn_frame = tk.Frame(header, bg=self.bg_panel)
        btn_frame.pack(side=tk.RIGHT)
        
        live_btn = tk.Label(btn_frame, text="LIVE", font=('Arial', 9, 'bold'),
                           bg=self.orange_accent, fg=self.text_white, 
                           padx=12, pady=4)
        live_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        historic_btn = tk.Label(btn_frame, text="HISTORIC", font=('Arial', 9),
                               bg='#3a4f6f', fg=self.text_gray, 
                               padx=12, pady=4)
        historic_btn.pack(side=tk.LEFT)
        
        # Gráfica con matplotlib en ALTA CALIDAD
        fig = Figure(figsize=(5, 2.5), dpi=100, facecolor=self.bg_panel)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.bg_panel)
        
        # Aquí se grafican los DATOS DE ACELERACIÓN G-FORCE
        # Los datos vienen de self.gforce_data y self.gforce_time
        self.gforce_line, = ax.plot(self.gforce_time, self.gforce_data, 
                                    color=self.orange_accent, linewidth=2.5, 
                                    antialiased=True)
        ax.fill_between(self.gforce_time, self.gforce_data, 
                        alpha=0.15, color=self.orange_accent)
        
        ax.set_xlim(-1.5, 4.0)
        ax.set_ylim(0, 8)
        ax.grid(True, alpha=0.1, color=self.text_gray, linestyle='--')
        
        # Etiquetas - Sin superposición
        ax.set_xticks([-1.5, 0, 4.0])
        ax.set_xticklabels(['-1.50', '0.00', '+4.00'], color=self.text_gray, fontsize=8)
        ax.set_yticks([])
        
        # Quitar bordes innecesarios
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(self.text_gray)
        ax.spines['bottom'].set_alpha(0.3)
        
        # Ajustar márgenes para evitar superposición
        fig.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.15)
        
        # Integrar en tkinter con alta calidad
        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        self.gforce_canvas = canvas
        self.gforce_ax = ax
        self.gforce_fig = fig
        
        return card
        
    def create_camera_panel(self, parent):
        """Crear panel de cámaras duales"""
        card = tk.Frame(parent, bg=self.bg_panel)
        
        # Encabezado
        header = tk.Frame(card, bg=self.bg_panel)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        title_frame = tk.Frame(header, bg=self.bg_panel)
        title_frame.pack(side=tk.LEFT)
        
        icon = tk.Label(title_frame, text="📹", font=('Arial', 14), bg=self.bg_panel)
        icon.pack(side=tk.LEFT)
        
        title = tk.Label(title_frame, text="DUAL PAYLOAD OPTICS - STEREOSCOPIC DOWNLINK", 
                        font=('Arial', 11, 'bold'), bg=self.bg_panel, fg=self.text_white)
        title.pack(side=tk.LEFT, padx=(8, 0))
        
        # Info de resolución
        info = tk.Label(header, text="RES: 2x 1080p @ 60FPS  ●", 
                       font=('Arial', 9), bg=self.bg_panel, fg=self.text_gray)
        info.pack(side=tk.RIGHT)
        
        # Contenedor de cámaras
        cam_container = tk.Frame(card, bg=self.bg_panel)
        cam_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Cámara izquierda - CLICKEABLE
        # Aquí se muestra el FEED DE VIDEO de la CÁMARA IZQUIERDA
        left_cam = tk.Frame(cam_container, bg='#d4c4b0', relief=tk.FLAT, 
                           borderwidth=2, cursor='hand2')
        left_cam.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        left_cam.bind('<Button-1>', lambda e: self.open_camera_fullscreen('LEFT'))
        
        left_label = tk.Label(left_cam, text="CAM_01_LEFT", font=('Arial', 9, 'bold'),
                             bg='#b8a890', fg='#3a3a3a', padx=10, pady=5,
                             cursor='hand2')
        left_label.pack(anchor='nw', padx=8, pady=8)
        left_label.bind('<Button-1>', lambda e: self.open_camera_fullscreen('LEFT'))
        
        left_content = tk.Label(left_cam, text="[FEED DE CÁMARA IZQUIERDA]\n\n📷\n\nClick para ampliar", 
                               font=('Arial', 18), bg='#d4c4b0', fg='#8a7a6a',
                               cursor='hand2')
        left_content.pack(expand=True)
        left_content.bind('<Button-1>', lambda e: self.open_camera_fullscreen('LEFT'))
        
        # Cámara derecha - CLICKEABLE
        # Aquí se muestra el FEED DE VIDEO de la CÁMARA DERECHA
        right_cam = tk.Frame(cam_container, bg='#d4c4b0', relief=tk.FLAT, 
                            borderwidth=2, cursor='hand2')
        right_cam.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        right_cam.bind('<Button-1>', lambda e: self.open_camera_fullscreen('RIGHT'))
        
        right_label = tk.Label(right_cam, text="CAM_01_RIGHT", font=('Arial', 9, 'bold'),
                              bg='#b8a890', fg='#3a3a3a', padx=10, pady=5,
                              cursor='hand2')
        right_label.pack(anchor='ne', padx=8, pady=8)
        right_label.bind('<Button-1>', lambda e: self.open_camera_fullscreen('RIGHT'))
        
        right_content = tk.Label(right_cam, text="[FEED DE CÁMARA DERECHA]\n\n📷\n\nClick para ampliar", 
                                font=('Arial', 18), bg='#d4c4b0', fg='#8a7a6a',
                                cursor='hand2')
        right_content.pack(expand=True)
        right_content.bind('<Button-1>', lambda e: self.open_camera_fullscreen('RIGHT'))
        
        return card
    
    def open_camera_fullscreen(self, camera_name):
        """Abrir vista ampliada de la cámara seleccionada"""
        # Crear ventana nueva
        cam_window = tk.Toplevel(self.root)
        cam_window.title(f"CAM_01_{camera_name} - Vista Ampliada")
        cam_window.geometry("800x600")
        cam_window.configure(bg=self.bg_dark)
        
        # Encabezado
        header = tk.Frame(cam_window, bg=self.bg_panel, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text=f"📹  CAM_01_{camera_name}  |  VISTA AMPLIADA", 
                        font=('Arial', 16, 'bold'), bg=self.bg_panel, fg=self.text_white)
        title.pack(pady=15)
        
        # Área de video
        video_frame = tk.Frame(cam_window, bg='#d4c4b0', relief=tk.FLAT, borderwidth=3)
        video_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        video_label = tk.Label(video_frame, 
                              text=f"[FEED DE CÁMARA {camera_name}]\n\n\n📹\n\n\nAquí se mostraría el video en vivo\nde la cámara {camera_name}", 
                              font=('Arial', 20), bg='#d4c4b0', fg='#6a5a4a')
        video_label.pack(expand=True)
        
        # Botón cerrar
        close_btn = tk.Button(cam_window, text="✕ CERRAR", font=('Arial', 11, 'bold'),
                             bg='#ff4444', fg=self.text_white, relief=tk.FLAT,
                             padx=20, pady=10, cursor='hand2',
                             command=cam_window.destroy)
        close_btn.pack(pady=(0, 20))
        
    def create_log_panel(self, parent):
        """Crear panel de log de paquetes y controles"""
        # Panel de log
        log_card = tk.Frame(parent, bg=self.bg_panel, height=450)
        log_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Encabezado del log
        log_header = tk.Frame(log_card, bg=self.bg_panel)
        log_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        log_icon = tk.Label(log_header, text="📋", font=('Arial', 12), bg=self.bg_panel)
        log_icon.pack(side=tk.LEFT)
        
        log_title = tk.Label(log_header, text="LIVE PACKET LOG", 
                            font=('Arial', 11, 'bold'), 
                            bg=self.bg_panel, fg=self.text_white)
        log_title.pack(side=tk.LEFT, padx=(8, 0))
        
        menu_icon = tk.Label(log_header, text="☰", font=('Arial', 14), 
                            bg=self.bg_panel, fg=self.text_gray)
        menu_icon.pack(side=tk.RIGHT)
        
        # Área de texto del log
        log_frame = tk.Frame(log_card, bg='#1e2a3a')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Aquí se muestran los MENSAJES DEL LOG en tiempo real
        # Formato: [TIMESTAMP] TIPO Mensaje
        self.log_text = tk.Text(log_frame, bg='#1e2a3a', fg=self.text_gray,
                               font=('Consolas', 9), relief=tk.FLAT,
                               wrap=tk.WORD, padx=10, pady=10)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Tags para colorear diferentes tipos de mensajes
        self.log_text.tag_config('INFO', foreground=self.blue_accent)
        self.log_text.tag_config('STAT', foreground=self.green_accent)
        self.log_text.tag_config('WARN', foreground='#ffaa00')
        self.log_text.tag_config('DATA', foreground=self.text_gray)
        self.log_text.tag_config('RECV', foreground='#9b59b6')
        self.log_text.tag_config('timestamp', foreground='#5a6a7a')
        
        # Agregar mensajes de ejemplo
        self.add_log_message("INFO", "Packet #14205 received (24 bytes)")
        self.add_log_message("STAT", "P:101.32 T:24.84 A:1245.82")
        self.add_log_message("WARN", "Minor jitter on IMU-Z axis")
        self.add_log_message("INFO", "Frame_Synch OK - SD_Logging ACTIVE")
        self.add_log_message("STAT", "P:101.30 T:24.88 A:1258.20")
        self.add_log_message("DATA", "0x4A 0x35 0xFF 0x01 0x28 0x98 0x13")
        self.add_log_message("INFO", "Payload orientation: STABLE")
        self.add_log_message("RECV", "New Telemetry Burst Incoming...")
        
        # Input de comandos
        # Aquí se ingresan COMANDOS MANUALES para enviar al CanSat
        cmd_frame = tk.Frame(parent, bg=self.bg_panel, height=60)
        cmd_frame.pack(fill=tk.X, pady=(0, 15))
        cmd_frame.pack_propagate(False)
        
        cmd_inner = tk.Frame(cmd_frame, bg='#1e2a3a')
        cmd_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)
        
        self.cmd_entry = tk.Entry(cmd_inner, bg='#1e2a3a', fg=self.text_gray,
                                 font=('Consolas', 10), relief=tk.FLAT,
                                 insertbackground=self.blue_accent)
        self.cmd_entry.insert(0, "Send Command...")
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10))
        
        send_btn = tk.Button(cmd_inner, text="➤", font=('Arial', 14, 'bold'),
                            bg=self.blue_accent, fg=self.text_white,
                            relief=tk.FLAT, width=3, cursor='hand2',
                            command=self.send_command)
        send_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Panel de fase de misión
        phase_card = tk.Frame(parent, bg=self.bg_panel)
        phase_card.pack(fill=tk.BOTH, expand=True)
        
        phase_header = tk.Frame(phase_card, bg=self.bg_panel)
        phase_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        phase_icon = tk.Label(phase_header, text="🚀", font=('Arial', 12), bg=self.bg_panel)
        phase_icon.pack(side=tk.LEFT)
        
        phase_title = tk.Label(phase_header, text="MISSION PHASE", 
                              font=('Arial', 11, 'bold'), 
                              bg=self.bg_panel, fg=self.text_white)
        phase_title.pack(side=tk.LEFT, padx=(8, 0))
        
        # Lista de fases
        # Aquí se muestra el ESTADO DE CADA FASE de la misión
        phases_frame = tk.Frame(phase_card, bg=self.bg_panel)
        phases_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        phases = [
            ("✓", "Pre-Flight Checklist", self.green_accent, True),
            ("✓", "Ascent Phase", self.green_accent, True),
            ("⟳", "Science Deployment", self.blue_accent, False),
            ("○", "Recovery Sequence", self.text_gray, False)
        ]
        
        for icon, text, color, completed in phases:
            phase_item = tk.Frame(phases_frame, bg=self.bg_panel)
            phase_item.pack(fill=tk.X, pady=5)
            
            icon_label = tk.Label(phase_item, text=icon, font=('Arial', 12),
                                 bg=self.bg_panel, fg=color, width=2)
            icon_label.pack(side=tk.LEFT)
            
            text_label = tk.Label(phase_item, text=text, font=('Arial', 10),
                                 bg=self.bg_panel, 
                                 fg=self.text_white if completed else self.text_gray,
                                 anchor='w')
            text_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
            
    def create_footer(self):
        """Crear barra inferior"""
        footer = tk.Frame(self.root, bg=self.bg_dark, height=35)
        footer.pack(fill=tk.X, padx=20, pady=(0, 10))
        footer.pack_propagate(False)
        
        sys_label = tk.Label(footer, text="SYS_OK", font=('Arial', 9, 'bold'),
                            bg=self.bg_dark, fg=self.green_accent)
        sys_label.pack(side=tk.LEFT)
        
        build_label = tk.Label(footer, text="BUILD: v2.4.12-ALPHA",
                              font=('Arial', 9), bg=self.bg_dark, fg=self.text_gray)
        build_label.pack(side=tk.LEFT, padx=(15, 0))
        
        copy_label = tk.Label(footer, text="CANSAT INTERNATIONAL 2024",
                             font=('Arial', 9), bg=self.bg_dark, fg=self.text_gray)
        copy_label.pack(side=tk.RIGHT)
        
    def add_log_message(self, msg_type, message):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.log_text.insert(tk.END, f"{msg_type} ", msg_type)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        
    def send_command(self):
        """Enviar comando (aquí se procesaría el COMANDO ingresado)"""
        cmd = self.cmd_entry.get()
        if cmd and cmd != "Send Command...":
            self.add_log_message("INFO", f"Command sent: {cmd}")
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, "Send Command...")
            
    def toggle_mission(self):
        """Iniciar o detener la misión"""
        if not self.mission_running:
            # Iniciar misión
            self.mission_running = True
            self.mission_start_time = datetime.now()
            self.elapsed_seconds = 0
            self.start_btn.config(text="⏸ STOP", bg='#ff4444')
            
            # Iniciar simulación y actualizaciones
            self.simulator.reset()
            self.update_mission_timer()
            self.update_telemetry()
            
            self.add_log_message("INFO", "Mission START - All systems nominal")
        else:
            # Detener misión
            self.mission_running = False
            self.start_btn.config(text="▶ START", bg=self.green_accent)
            self.add_log_message("INFO", "Mission PAUSED by operator")
            
    def update_mission_timer(self):
        """Actualizar timer de misión en tiempo real"""
        if self.mission_running:
            elapsed = datetime.now() - self.mission_start_time
            self.elapsed_seconds = int(elapsed.total_seconds())
            
            hours = self.elapsed_seconds // 3600
            minutes = (self.elapsed_seconds % 3600) // 60
            seconds = self.elapsed_seconds % 60
            
            self.timer_display.config(text=f"T+ {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_mission_timer)
    
    def update_sensor_data(self):
        """Compatibilidad: actualiza sensores llamando al bucle unificado."""
        # la lógica real se ejecuta en update_telemetry
        self.update_telemetry()
    
    def update_graphs(self):
        """Compatibilidad heredada: actualiza usando el bucle unificado."""
        # el código de actualización real vive en update_telemetry
        self.update_telemetry()

    def update_telemetry(self):
        """Actualizar todos los valores (sensores + gráficas) usando el simulador.

        Este método reemplaza los dos bucles anteriores y recibe los datos de
        ``telemetry_simulator.TelemetrySimulator`` como si se tratara de paquetes
        entrantes. El bucle se reprograma con ``after`` para simular la llegada
        continua de telemetría.
        """
        if self.mission_running:
            # obtener un nuevo paquete simulado
            data = self.simulator.get_next()
            self.elapsed_seconds = self.simulator.elapsed_seconds

            # SENSORES ------------------------------------------------------
            new_pressure = data['pressure']
            self.pressure_value.set(new_pressure)
            if self.pressure_label:
                self.pressure_label.config(text=f"{new_pressure:.1f}")
            if hasattr(self, 'pressure_canvas'):
                fill = (new_pressure - 95) / 15
                fill = max(0, min(1, fill))
                self.pressure_canvas.delete('progress_arc')
                extent = 359.9 * fill
                self.pressure_canvas.create_arc(10, 10, 110, 110, start=90, extent=-extent,
                                               outline=self.pressure_color, width=12,
                                               style=tk.ARC, tags='progress_arc')

            new_temp = data['temperature']
            self.temperature_value.set(new_temp)
            if self.temp_label:
                self.temp_label.config(text=f"{new_temp:.1f}")
            if hasattr(self, 'temp_canvas'):
                fill = (new_temp - 15) / 25
                fill = max(0, min(1, fill))
                self.temp_canvas.delete('progress_arc')
                extent = 359.9 * fill
                self.temp_canvas.create_arc(10, 10, 110, 110, start=90, extent=-extent,
                                            outline=self.temp_color, width=12,
                                            style=tk.ARC, tags='progress_arc')

            new_altitude = data['altitude']
            self.altitude_value.set(new_altitude)
            if self.altitude_label:
                self.altitude_label.config(text=f"{new_altitude:,.1f}")

            new_rate = data['altitude_rate']
            self.altitude_rate.set(new_rate)
            if self.altitude_rate_label:
                sign = "+" if new_rate >= 0 else ""
                color = self.green_accent if new_rate >= 0 else '#ff6b6b'
                self.altitude_rate_label.config(text=f"{sign}{new_rate:.1f} m/s", fg=color)

            new_latency = data['latency']
            self.signal_latency.set(new_latency)
            if self.latency_label:
                self.latency_label.config(text=f"{int(new_latency)}")

            # GRÁFICAS ------------------------------------------------------
            self.velocity_time = data['velocity_time']
            self.velocity_data = data['velocity_data']
            self.velocity_line.set_data(self.velocity_time, self.velocity_data)
            # ArtistList returned by ``ax.collections`` no tiene ``clear`` en algunas
            # versiones de matplotlib, así que eliminamos manualmente cada colección.
            for col in list(self.velocity_ax.collections):
                col.remove()
            self.velocity_ax.fill_between(self.velocity_time, self.velocity_data,
                                          alpha=0.1, color=self.blue_accent)
            self.velocity_canvas.draw()

            self.gforce_time = data['gforce_time']
            self.gforce_data = data['gforce_data']
            self.gforce_line.set_data(self.gforce_time, self.gforce_data)
            for col in list(self.gforce_ax.collections):
                col.remove()
            self.gforce_ax.fill_between(self.gforce_time, self.gforce_data,
                                        alpha=0.15, color=self.orange_accent)
            x_min = self.gforce_time[0]
            x_max = self.gforce_time[-1]
            self.gforce_ax.set_xlim(x_min, x_max)
            self.gforce_canvas.draw()

            # Log de telemetría
            if self.elapsed_seconds % 3 == 0:
                self.add_log_message("DATA",
                    f"VEL:{data['new_velocity']:.1f}m/s G:{data['new_gforce']:.2f}")
            if self.elapsed_seconds % 5 == 0:
                self.add_log_message("STAT",
                    f"P:{new_pressure:.2f} T:{new_temp:.2f} A:{new_altitude:.2f}")

            # reprogramar llamada
            self.root.after(500, self.update_telemetry)


# Ejecutar aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = CanSatMissionControl(root)
    root.mainloop()
