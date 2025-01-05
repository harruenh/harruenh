import ccxt
import pandas as pd
from datetime import datetime, timedelta

# Configurar el exchange (por ejemplo, Binance)
exchange = ccxt.binance()

# Definir las criptomonedas y el par de referencia
symbols = ['BTC/USDT', 'BNB/USDT', 'XRP/USDT']

# Calcular la fecha de inicio (una semana atrás desde ahora)
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=7)

# Convertir fechas a timestamps en milisegundos
start_timestamp = int(start_date.timestamp() * 1000)
end_timestamp = int(end_date.timestamp() * 1000)

# Función para obtener datos históricos
def fetch_ohlcv(symbol, timeframe, since, until):
    all_ohlcv = []
    while since < until:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not ohlcv:
            break
        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1  # Evitar solapamiento
    return all_ohlcv

# Diccionario para almacenar los DataFrames
data_frames = {}

# Obtener y procesar los datos para cada símbolo
for symbol in symbols:
    ohlcv = fetch_ohlcv(symbol, '1h', start_timestamp, end_timestamp)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df['percentage_change'] = df['close'].pct_change() * 100
    data_frames[symbol] = df

# Combinar los DataFrames en uno solo
combined_df = pd.DataFrame(index=data_frames[symbols[0]].index)
for symbol in symbols:
    combined_df[symbol.replace('/', '_') + '_pct_change'] = data_frames[symbol]['percentage_change']

# Exportar a un archivo CSV
combined_df.to_csv('crypto_variations.csv')

print("Datos exportados a 'crypto_variations.csv'")