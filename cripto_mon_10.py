import tkinter as tk
from tkinter import ttk
from binance.client import Client
import threading
import time

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
        self.selected_pairs = []
        self.price_labels = []
        self.previous_prices = {}
        self.update_interval = 10  # Intervalo fijo de 10 segundos

        # Configurar UI
        self.setup_ui()

        # Hilo para actualizar precios
        self.running = True
        self.update_thread = threading.Thread(target=self.update_price_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

    def setup_ui(self):
        # Etiqueta de selección de pares
        ttk.Label(self.root, text="Selecciona hasta 10 pares:").pack(pady=5)

        # Lista de selección de pares
        self.pair_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, height=15)
        self.pair_listbox.pack(pady=5)

        # Botón para cargar pares
        ttk.Button(self.root, text="Cargar Pares", command=self.load_pairs).pack(pady=5)

        # Botón para confirmar selección
        ttk.Button(self.root, text="Confirmar Selección", command=self.confirm_selection).pack(pady=5)

        # Contenedor para etiquetas de precios
        self.prices_frame = ttk.Frame(self.root)
        self.prices_frame.pack(pady=10)

    def load_pairs(self):
        try:
            exchange_info = client.get_exchange_info()
            symbols = [symbol['symbol'] for symbol in exchange_info['symbols'] if symbol['symbol'].endswith("USDT")]
            self.pair_listbox.delete(0, tk.END)
            for symbol in symbols:
                self.pair_listbox.insert(tk.END, symbol)
        except Exception as e:
            ttk.Label(self.root, text=f"Error cargando pares: {e}", foreground="red").pack()

    def confirm_selection(self):
        selected_indices = self.pair_listbox.curselection()
        self.selected_pairs = [self.pair_listbox.get(i) for i in selected_indices][:10]  # Limitar a 10 pares

        # Limpiar etiquetas existentes
        for label in self.price_labels:
            label.destroy()
        self.price_labels = []

        # Crear etiquetas para los pares seleccionados
        for pair in self.selected_pairs:
            label = ttk.Label(self.prices_frame, text=f"{pair}: Cargando...", font=("Arial", 12))
            label.pack(anchor="w", pady=2)
            self.price_labels.append(label)

    def update_price_loop(self):
        while self.running:
            for i, pair in enumerate(self.selected_pairs):
                try:
                    ticker = client.get_symbol_ticker(symbol=pair)
                    price = float(ticker['price'])

                    # Calcular variación porcentual
                    previous_price = self.previous_prices.get(pair, price)
                    change_percentage = ((price - previous_price) / previous_price) * 100 if previous_price else 0
                    self.previous_prices[pair] = price

                    # Actualizar etiqueta con precio y variación
                    self.price_labels[i].config(text=f"{pair}: {price:.2f} ({change_percentage:.2f}%)")
                except Exception as e:
                    self.price_labels[i].config(text=f"{pair}: Error")
            time.sleep(self.update_interval)

    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoPriceMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
