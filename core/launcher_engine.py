import os
import subprocess
import threading
import sys
from typing import Dict, Any, Callable, Optional
import minecraft_launcher_lib

class MinecraftEngine:
    def __init__(self):
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        
    def is_version_installed(self, version: str) -> bool:
        version_dir = os.path.join(self.minecraft_directory, "versions", version)
        return os.path.exists(version_dir)
        
    def install_version(self, version: str, callback_dict: Optional[Any] = None) -> None:
        callback = callback_dict if isinstance(callback_dict, dict) else None
        minecraft_launcher_lib.install.install_minecraft_version(
            version, 
            self.minecraft_directory, 
            callback=callback
        )
        
    def _find_java_path(self) -> str:
        posibles_rutas = [
            r"C:\Program Files\Eclipse Foundation",
            r"C:\Program Files\Eclipse Adoptium",
            r"C:\Program Files\Java",
            r"C:\Program Files (x86)\Java"
        ]
        
        for base in posibles_rutas:
            if os.path.exists(base):
                for root, dirs, files in os.walk(base):
                    if "javaw.exe" in files:
                        ruta_final = os.path.join(root, "javaw.exe")
                        print(f"[OptiLauncher] Java detectado en: {ruta_final}")
                        return ruta_final
        
        print("[OptiLauncher] Alerta: No se detectó Java nativo en Archivos de Programa. Usando comando por defecto.")
        return "javaw"

    def launch(self, *args, **kwargs) -> None:
        # Extrae de forma segura las variables sin importar el orden posicional
        # Busca tanto en argumentos por nombre (kwargs) como desempaquetando un diccionario si vino en args
        data = kwargs
        if args and isinstance(args[0], dict):
            data = args[0]
        elif len(args) >= 4:
            # Si vinieron sueltos en el orden original
            data = {
                'version': args[0],
                'username': args[1],
                'uuid_str': args[2],
                'token_str': args[3]
            }
            if len(args) >= 5: data['ram_gb'] = args[4]
            if len(args) >= 6: data['progress_callback'] = args[5]

        version = data.get('version', data.get('version_id', '1.20.4'))
        username = data.get('username', data.get('player_name', 'JeroTorres'))
        uuid_str = data.get('uuid_str', data.get('uuid', '00000000000000000000000000000000'))
        token_str = data.get('token_str', data.get('token', '00000000000000000000000000000000'))
        ram_gb = data.get('ram_gb', data.get('ram', data.get('ram_size', 3)))
        progress_callback = data.get('progress_callback', data.get('callback', None))
        
        def run():
            try:
                cb_dict = None
                if progress_callback and hasattr(progress_callback, 'get') and callable(progress_callback.get):
                    cb_dict = progress_callback
                elif progress_callback and isinstance(progress_callback, dict):
                    cb_dict = progress_callback
                else:
                    def status_cb(txt):
                        if callable(progress_callback): progress_callback(f"Descargando: {txt}", 20)
                    def progress_cb(prog):
                        if callable(progress_callback): progress_callback("Descargando componentes...", int(prog))
                    def max_cb(max_val): pass
                    cb_dict = {"setStatus": status_cb, "setProgress": progress_cb, "setMax": max_cb}
                
                if callable(progress_callback):
                    try: progress_callback("Verificando archivos...", 10)
                    except: pass
                
                self.install_version(version, cb_dict)

                options = {
                    "username": username,
                    "uuid": uuid_str,
                    "token": token_str,
                    "jvmArguments": [
                        f"-Xmx{ram_gb}G", 
                        "-Xms1G", 
                        "-XX:+UseG1GC", 
                        "-XX:MaxGCPauseMillis=50",
                        "-XX:+UnlockExperimentalVMOptions",
                        "-XX:+AlwaysPreTouch"
                    ]
                }

                options["executablePath"] = self._find_java_path()

                if callable(progress_callback):
                    try: progress_callback("Iniciando Minecraft Java...", 95)
                    except: pass
                
                cmd = minecraft_launcher_lib.command.get_minecraft_command(version, self.minecraft_directory, options)
                
                if callable(progress_callback):
                    try: progress_callback("¡Juego iniciado!", 100)
                    except: pass
                
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            except Exception as e:
                print(f"[OptiLauncher Error] Ocurrió un problema: {str(e)}")

        threading.Thread(target=run, daemon=True).start()




