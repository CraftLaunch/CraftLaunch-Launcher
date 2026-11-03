"""
main.py
Punto de entrada principal para el Launcher Nativo de Minecraft.
Ejecuta la interfaz de escritorio liviana en CustomTkinter o Tkinter estándar.

Uso en tu computadora:
  python main.py
"""

import sys
import os

# Asegurar que el directorio raíz del launcher esté en el PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.launcher_engine import MinecraftEngine
from core.auth_manager import AuthManager
from ui.launcher_window import create_launcher_window

def main():
    print("==================================================")
    print("  CraftLaunch: Minecraft Native Low-Spec Launcher ")
    print("==================================================")
    
    # 1. Instanciar núcleo del motor y gestor de autenticación
    engine = MinecraftEngine()
    auth = AuthManager()

    # 2. Inicializar y lanzar la ventana de escritorio nativa (Tkinter/CustomTkinter)
    window = create_launcher_window(engine, auth)
    window.run()

if __name__ == "__main__":
    main()
