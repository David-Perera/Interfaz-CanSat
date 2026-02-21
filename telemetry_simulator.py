"""Módulo que genera paquetes de telemetría aleatorios.

La idea es imitar la llegada de datos desde el CanSat. Cada llamada a
``get_next`` mueve la simulación en el tiempo y devuelve un diccionario con
los valores más recientes (sensores, velocidad, g-force y arreglos históricos)
como si se tratara de un "paquete" entrante.

Este módulo está separado para cumplir con el requisito del usuario de
"transmitir datos random como si fuesen recibidos" y permite que la lógica de
simulación no viva directamente en la interfaz gráfica.
"""

import numpy as np
import random

class TelemetrySimulator:
    def __init__(self):
        # contador de segundos simulados (float para pasos fraccionarios)
        self.elapsed_seconds = 0.0

        # vectores históricos que se usan en las gráficas
        self.velocity_time = np.linspace(-120, 0, 100)
        self.velocity_data = np.zeros_like(self.velocity_time)

        self.gforce_time = np.linspace(-1.5, 4.0, 100)
        self.gforce_data = np.zeros_like(self.gforce_time)

    def reset(self):
        """Reiniciar simulación a valores iniciales."""
        self.elapsed_seconds = 0.0
        self.velocity_time = np.linspace(-120, 0, 100)
        self.velocity_data = np.zeros_like(self.velocity_time)
        self.gforce_time = np.linspace(-1.5, 4.0, 100)
        self.gforce_data = np.zeros_like(self.gforce_time)

    def get_next(self, dt: float = 0.5) -> dict:
        """Avanzar la simulación ``dt`` segundos y retornar un paquete de datos.

        Los campos devueltos son los que necesita la interfaz para actualizar
        sensores y gráficas.
        """
        self.elapsed_seconds += dt

        # sensores
        pressure = 101.3 + np.sin(self.elapsed_seconds / 10) * 2 + np.random.normal(0, 0.1)
        temperature = 24.8 + np.sin(self.elapsed_seconds / 15 + 1) * 3 + np.random.normal(0, 0.2)
        altitude = 1245.8 + self.elapsed_seconds * 2.5 + np.sin(self.elapsed_seconds / 8) * 50
        altitude_rate = 12.4 + np.sin(self.elapsed_seconds / 7) * 8
        latency = 24 + np.random.normal(0, 3)
        latency = max(10, min(100, latency))

        # velocidad
        # no rotamos el eje temporal: permanecerá constante para evitar que los
        # valores se "borren" al desplazar ceros repetidos.
        new_velocity = 15 + 10 * np.sin(self.elapsed_seconds / 20) + np.random.normal(0, 1)
        new_velocity = max(0, new_velocity)
        self.velocity_data = np.roll(self.velocity_data, -1)
        self.velocity_data[-1] = new_velocity

        # g-force
        self.gforce_time = np.roll(self.gforce_time, -1)
        self.gforce_time[-1] = self.gforce_time[-2] + 0.055
        new_gforce = 2 + 3 * np.exp(-((self.elapsed_seconds % 30 - 15)**2) / 50) + np.random.normal(0, 0.3)
        new_gforce = max(0, new_gforce)
        self.gforce_data = np.roll(self.gforce_data, -1)
        self.gforce_data[-1] = new_gforce

        return {
            'pressure': pressure,
            'temperature': temperature,
            'altitude': altitude,
            'altitude_rate': altitude_rate,
            'latency': latency,
            'velocity_time': self.velocity_time.copy(),
            'velocity_data': self.velocity_data.copy(),
            'gforce_time': self.gforce_time.copy(),
            'gforce_data': self.gforce_data.copy(),
            'new_velocity': new_velocity,
            'new_gforce': new_gforce,
        }
