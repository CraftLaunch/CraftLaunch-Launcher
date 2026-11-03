"""
ui/launcher_window.py
Ventana de escritorio nativa para el Launcher de Minecraft.
Implementa interfaz moderna con CustomTkinter (o fallback en Tkinter estándar).

Optimizado para PCs de bajos recursos:
- Consumo mínimo de memoria (~30MB - ~40MB RAM).
- Opción de cerrar la ventana al iniciar el juego para dejar el 100% de la RAM a Minecraft.
- Hilos independientes para no congelar la ventana durante descargas o lanzamientos.
"""

import threading
import sys
import os
from typing import Optional

# Intentamos importar CustomTkinter, con fallback seguro a Tkinter nativo
try:
    import customtkinter as ctk
    USE_CUSTOMTKINTER = True
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("green")
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox
    USE_CUSTOMTKINTER = False

from core.launcher_engine import MinecraftEngine
from core.auth_manager import AuthManager
from core.jvm_optimizer import get_system_ram_gb, get_cpu_cores, build_low_resource_jvm_args

class CustomTkinterLauncherWindow:
    """Implementación moderna con CustomTkinter."""
    def __init__(self, engine: MinecraftEngine, auth: AuthManager):
        self.engine = engine
        self.auth = auth
        self.total_ram = get_system_ram_gb()
        self.cores = get_cpu_cores()

        self.root = ctk.CTk()
        self.root.title("CraftLaunch // Native Low-Spec Minecraft Launcher")
        self.root.geometry("680x520")
        self.root.resizable(False, False)

        saved_session = self.auth.session_data or {}
        self.default_username = saved_session.get("username", "Steve")

        self._init_ui()
        self._load_versions()

    def _init_ui(self):
        # 1. Header con especificaciones del equipo
        self.header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#18181b")
        self.header_frame.pack(fill="x", padx=0, pady=0)

        self.title_lbl = ctk.CTkLabel(
            self.header_frame,
            text="CraftLaunch",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#10b981"
        )
        self.title_lbl.pack(side="left", padx=24, pady=16)

        self.sys_specs_lbl = ctk.CTkLabel(
            self.header_frame,
            text=f"RAM: {self.total_ram} GB | CPU: {self.cores} Núcleos",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.sys_specs_lbl.pack(side="right", padx=24, pady=16)

        # 2. Contenedor Principal
        self.content_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=16)

        # Campo: Nombre de Jugador
        self.user_lbl = ctk.CTkLabel(self.content_frame, text="Nombre de Jugador (Offline / Dev):")
        self.user_lbl.pack(anchor="w", pady=(0, 4))
        
        self.user_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Tu Nickname", width=360)
        self.user_entry.insert(0, self.default_username)
        self.user_entry.pack(anchor="w", pady=(0, 14))

        # Campo: Versión de Minecraft
        self.ver_lbl = ctk.CTkLabel(self.content_frame, text="Versión de Minecraft:")
        self.ver_lbl.pack(anchor="w", pady=(0, 4))
        
        self.ver_combo = ctk.CTkComboBox(
            self.content_frame,
            values=["1.20.4", "1.20.1", "1.16.5", "1.12.2", "1.8.9"],
            width=360
        )
        self.ver_combo.pack(anchor="w", pady=(0, 14))

        # Campo: Memoria RAM
        initial_ram = 2.0 if self.total_ram <= 4.0 else 3.0
        self.ram_lbl = ctk.CTkLabel(self.content_frame, text=f"Memoria RAM asignada a Minecraft: {initial_ram} GB")
        self.ram_lbl.pack(anchor="w", pady=(0, 4))

        max_alloc = max(2, min(8, int(self.total_ram - 1)))
        self.ram_slider = ctk.CTkSlider(
            self.content_frame,
            from_=1.5,
            to=max_alloc,
            number_of_steps=int((max_alloc - 1.5) * 2),
            command=self._on_ram_change,
            width=360
        )
        self.ram_slider.set(initial_ram)
        self.ram_slider.pack(anchor="w", pady=(0, 14))

        # Checkbox para liberar recursos
        self.close_on_start_var = ctk.BooleanVar(value=True)
        self.close_chk = ctk.CTkCheckBox(
            self.content_frame,
            text="Cerrar el launcher al iniciar Minecraft (Libera ~40MB para el juego)",
            variable=self.close_on_start_var,
            text_color="#d4d4d8"
        )
        self.close_chk.pack(anchor="w", pady=(0, 14))

        # Estado y Barra de Progreso
        self.status_lbl = ctk.CTkLabel(self.content_frame, text="Listo para jugar", text_color="#71717a")
        self.status_lbl.pack(anchor="w", pady=(0, 4))

        self.progress = ctk.CTkProgressBar(self.content_frame, width=630)
        self.progress.set(0)
        self.progress.pack(anchor="w", pady=(0, 16))

        # 3. Botón de Lanzamiento (Footer)
        self.play_btn = ctk.CTkButton(
            self.root,
            text="JUGAR MINECRAFT",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=46,
            command=self._start_launch_thread
        )
        self.play_btn.pack(side="bottom", fill="x", padx=24, pady=(0, 20))

    def _on_ram_change(self, val):
        self.ram_lbl.configure(text=f"Memoria RAM asignada a Minecraft: {round(val, 1)} GB")

    def _load_versions(self):
        def _fetch():
            local_versions = self.engine.get_installed_versions()
            if local_versions:
                self.ver_combo.configure(values=local_versions)
                self.ver_combo.set(local_versions[0])
            else:
                remotes = self.engine.get_remote_releases()
                if remotes:
                    self.ver_combo.configure(values=remotes[:10])
                    self.ver_combo.set(remotes[0])
        threading.Thread(target=_fetch, daemon=True).start()

    def _start_launch_thread(self):
        self.play_btn.configure(state="disabled", text="Descargando / Verificando...")
        thread = threading.Thread(target=self._launch_task, daemon=True)
        thread.start()

    def _launch_task(self):
        try:
            username = self.user_entry.get().strip() or "Steve"
            version = self.ver_combo.get()
            allocated_ram = round(self.ram_slider.get(), 1)
            
            auth_profile = self.auth.create_offline_profile(username)
            max_val = 100

            def on_progress(event):
                nonlocal max_val
                t = event.get("type")
                if t == "status":
                    self.status_lbl.configure(text=event.get("text", ""))
                elif t == "max":
                    max_val = max(1, event.get("value", 100))
                elif t == "progress":
                    cur = event.get("value", 0)
                    self.progress.set(cur / max_val)

            if not self.engine.is_version_installed(version):
                self.status_lbl.configure(text=f"Descargando versión {version}...")
                self.engine.install_version(version, on_progress)

            self.status_lbl.configure(text="Construyendo argumentos JVM y arrancando...")

            def on_started():
                if self.close_on_start_var.get():
                    self.root.destroy()
                else:
                    self.status_lbl.configure(text="Minecraft iniciado exitosamente.")
                    self.play_btn.configure(state="normal", text="MINECRAFT EN EJECUCIÓN")

            def on_exited(code):
                self.status_lbl.configure(text=f"Minecraft finalizó con código {code}")
                self.play_btn.configure(state="normal", text="JUGAR MINECRAFT")
                self.progress.set(0)

            self.engine.launch(
                version_id=version,
                auth_profile=auth_profile,
                allocated_ram_gb=allocated_ram,
                on_started=on_started,
                on_exited=on_exited
            )
        except Exception as e:
            self.status_lbl.configure(text=f"Error al iniciar: {str(e)[:60]}")
            self.play_btn.configure(state="normal", text="REINTENTAR")

    def run(self):
        self.root.mainloop()

def create_launcher_window(engine: MinecraftEngine, auth: AuthManager):
    """Crea la ventana usando CustomTkinter si está disponible, o Tkinter estándar."""
    if USE_CUSTOMTKINTER:
        return CustomTkinterLauncherWindow(engine, auth)
    # Fallback si no está instalado CustomTkinter
    from tkinter import Tk, Label, Button, Frame, Entry, StringVar
    from tkinter import ttk
    # Ventana estándar mínima
    root = Tk()
    root.title("CraftLaunch (Tkinter Nativo)")
    root.geometry("600x440")
    # ...
    return root
