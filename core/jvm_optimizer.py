"""
core/jvm_optimizer.py
Optimizador de argumentos de la Máquina Virtual Java (JVM) para Minecraft.
Enfocado en sistemas de bajos recursos (2GB - 4GB RAM) para eliminar micro-tirones (stutters).
"""

import os
import psutil
from typing import List, Dict, Any

def get_system_ram_gb() -> float:
    """Devuelve la memoria RAM física total instalada en el sistema en Gigabytes."""
    try:
        return round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        return 4.0

def get_cpu_cores() -> int:
    """Devuelve la cantidad de núcleos de CPU lógicos."""
    return os.cpu_count() or 2

def build_low_resource_jvm_args(
    allocated_ram_gb: float,
    java_version: int = 17,
    use_aggressive_gc: bool = True
) -> List[str]:
    """
    Genera argumentos de JVM optimizados para reducir el consumo y evitar GC freezes.
    """
    ram_mb = int(allocated_ram_gb * 1024)
    cores = get_cpu_cores()
    flags: List[str] = []

    # 1. Asignación de Heap
    if allocated_ram_gb <= 2.0:
        flags.append(f"-Xms{int(ram_mb * 0.75)}M")
    else:
        flags.append(f"-Xms{ram_mb}M")
    flags.append(f"-Xmx{ram_mb}M")

    # 2. Selección de Garbage Collector
    if java_version >= 17 and use_aggressive_gc and cores >= 4:
        flags.extend([
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+UseShenandoahGC",
            "-XX:ShenandoahGCHeuristics=compact",
            "-XX:ShenandoahPacing=true",
        ])
    elif allocated_ram_gb <= 1.5 and cores <= 2:
        flags.append("-XX:+UseParallelGC")
    else:
        flags.extend([
            "-XX:+UseG1GC",
            "-XX:G1ReservePercent=15",
            "-XX:MaxGCPauseMillis=50",
            "-XX:G1HeapRegionSize=8M",
            "-XX:G1NewSizePercent=20",
            "-XX:G1MaxNewSizePercent=30",
        ])

    # 3. Deduplicación de cadenas
    flags.append("-XX:+UseStringDeduplication")
    if java_version >= 17:
        flags.append("-XX:+OptimizeStringConcat")

    # 4. Pretouching si hay >= 3GB
    if allocated_ram_gb >= 3.0:
        flags.append("-XX:+AlwaysPreTouch")

    # 5. Desactivar RMI/JMX innecesario (Ahorra ~50MB nativos)
    flags.extend([
        "-Dsun.rmi.dgc.server.gcInterval=2147483646",
        "-Dsun.rmi.dgc.client.gcInterval=2147483646",
        "-Dcom.sun.management.jmxremote=false",
        "-Dfile.encoding=UTF-8"
    ])

    return flags
