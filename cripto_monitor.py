import tkinter as tk
from tkinter import ttk
from binance.client import Client
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from datetime import datetime

# Configura tu API Key y Secret (dejar en blanco si solo se requiere acceso público)
API_KEY = ''
API_SECRET = ''

# Crear cliente de Binance
client = Client(API_KEY, API_SECRET)

class CryptoPriceMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Precios de Criptomonedas")

        # Variables
        self.selected_pair = tk.StringVar()
        self.price_label_var = tk.StringVar(value="Precio actual: Cargando...")
        self.update_interval = 5  # Intervalo fijo de 10 segundos
        self.price_history = []
        self.time_history = []

        # Configurar UI
        self.setup_ui()

        # Hilo para actualizar precios
        self.running = True
        self.update_thread = threading.Thread(target=self.update_price_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

    def setup_ui(self):
        # Etiqueta de selección de par
        ttk.Label(self.root, text="Selecciona un par:").pack(pady=5)

        # Combobox para seleccionar par
        self.pair_combobox = ttk.Combobox(self.root, textvariable=self.selected_pair, state="readonly")
        self.pair_combobox.pack(pady=5)

        # Botón para cargar pares
        ttk.Button(self.root, text="Cargar Pares", command=self.load_pairs).pack(pady=5)

        # Etiqueta para mostrar precio
        ttk.Label(self.root, textvariable=self.price_label_var, font=("Arial", 14)).pack(pady=20)

        # Gráfico de precios
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Historial de Precios")
        self.ax.set_xlabel("Tiempo")
        self.ax.set_ylabel("Precio")
        self.line, = self.ax.plot([], [], marker="o")

        self.canvas = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas.get_tk_widget().pack(pady=10)

    def load_pairs(self):
        try:
            exchange_info = client.get_exchange_info()
            symbols = [symbol['symbol'] for symbol in exchange_info['symbols'] if symbol['symbol'].endswith("USDT")]
            self.pair_combobox['values'] = symbols
            if symbols:
                self.selected_pair.set(symbols[0])
        except Exception as e:
            self.price_label_var.set(f"Error cargando pares: {e}")

    def update_graph(self, price):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.price_history.append(float(price))
        self.time_history.append(current_time)

        # Limitar historial a las últimas 10 entradas
        if len(self.price_history) > 10:
            self.price_history.pop(0)
            self.time_history.pop(0)

        # Convertir tiempo a índices para Matplotlib
        indices = list(range(len(self.time_history)))

        # Actualizar datos del gráfico
        self.line.set_data(indices, self.price_history)
        self.ax.set_xlim(0, len(self.time_history) - 1)
        self.ax.set_xticks(indices)
        self.ax.set_xticklabels(self.time_history, rotation=45, ha="right")
        self.ax.set_ylim(min(self.price_history) * 0.95, max(self.price_history) * 1.05)
        self.canvas.draw()

    def update_price_loop(self):
        while self.running:
            selected_pair = self.selected_pair.get()
            if selected_pair:
                try:
                    ticker = client.get_symbol_ticker(symbol=selected_pair)
                    price = ticker['price']
                    self.price_label_var.set(f"Precio actual ({selected_pair}): {price}")
                    self.update_graph(price)
                except Exception as e:
                    self.price_label_var.set(f"Error obteniendo precio: {e}")
            time.sleep(self.update_interval)

    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoPriceMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()