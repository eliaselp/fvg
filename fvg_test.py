import pandas as pd
import matplotlib.pyplot as plt
import os
from decimal import Decimal, getcontext

# Configurar la precisión (puedes aumentarla si es necesario)
getcontext().prec = 100

# Configuración de la ventana de trading
TRADING_WINDOW_START = pd.to_datetime("08:00", format="%H:%M").time()
TRADING_WINDOW_END = pd.to_datetime("16:00", format="%H:%M").time()

def limpiar_consola():
    if os.name == 'nt':  # Para Windows
        os.system('cls')
    else:  # Para macOS y Linux
        os.system('clear')

'''
from IPython.display import clear_output

def limpiar_consola():
    clear_output(wait=False)
'''


def detect_fvg(last_four_candles):
    if len(last_four_candles) < 3:
        return None
    
    # Tomamos las últimas 3 velas de las 4 proporcionadas
    candle1 = last_four_candles.iloc[-3]
    candle3 = last_four_candles.iloc[-1]
    
    # Verificar FVG alcista
    if candle1['high'] < candle3['low']:
        return 'Short'
    # Verificar FVG bajista
    elif candle1['low'] > candle3['high']:
        return 'Long'
    else:
        return None



def main():
    # Cargar los datos
    df = pd.read_csv('BTCUSD_ohlcv.csv', parse_dates=['timestamp'], index_col='timestamp')
    df.sort_index(inplace=True)
    print(df)
    input()

    # Usamos Decimal para el capital, sin límite superior práctico
    capital = Decimal("100")
    open_positions = []
    trade_history = []
    balance_history = [capital]
    
    stop_limit_candle = 10  # Número de velas para calcular el stop loss
    time_limit = True
    for i in range(900000,len(df)):
        if i < stop_limit_candle + 1:
            continue
        
        current_candle = df.iloc[i]
        # Convertir precios actuales a Decimal
        current_low   = Decimal(str(current_candle['low']))
        current_high  = Decimal(str(current_candle['high']))
        current_close = Decimal(str(current_candle['close']))
        
        # Cerrar operaciones por stop loss
        to_remove = []
        for pos in open_positions:
            if pos['direction'] == 'Long' and current_low <= pos['stop']:
                pnl = (pos['stop'] - pos['entry_price']) * pos['size']
                capital += pnl
                balance_history.append(capital)
                trade_history.append({
                    'type': 'STOP_LOSS',
                    'direction': pos['direction'],
                    'entry': pos['entry_price'],
                    'exit': pos['stop'],
                    'pnl': pnl,
                    'duration': current_candle.name - pos['entry_time']
                })
                to_remove.append(pos)
            elif pos['direction'] == 'Short' and current_high >= pos['stop']:
                pnl = (pos['entry_price'] - pos['stop']) * pos['size']
                capital += pnl
                balance_history.append(capital)
                trade_history.append({
                    'type': 'STOP_LOSS',
                    'direction': pos['direction'],
                    'entry': pos['entry_price'],
                    'exit': pos['stop'],
                    'pnl': pnl,
                    'duration': current_candle.name - pos['entry_time']
                })
                to_remove.append(pos)
        for pos in to_remove:
            open_positions.remove(pos)
        
        if time_limit == True:
            # Verificar si la vela actual no está dentro de la ventana de trading
            current_time = current_candle.name.time()
            if not (TRADING_WINDOW_START <= current_time <= TRADING_WINDOW_END):
                # Fuera de la ventana: cerrar todas las posiciones abiertas
                if open_positions:
                    for pos in open_positions:
                        exit_price = current_close
                        if pos['direction'] == 'Long':
                            pnl = (exit_price - pos['entry_price']) * pos['size']
                        else:
                            pnl = (pos['entry_price'] - exit_price) * pos['size']
                        capital += pnl
                        balance_history.append(capital)
                        trade_history.append({
                            'type': 'CLOSED_OUTSIDE_WINDOW',
                            'direction': pos['direction'],
                            'entry': pos['entry_price'],
                            'exit': exit_price,
                            'pnl': pnl,
                            'duration': current_candle.name - pos['entry_time']
                        })
                    open_positions = []
                continue  # No se abren nuevas operaciones fuera de la ventana
                
        # Detectar señal FVG
        last_four = df.iloc[i-3:i+1]
        signal = detect_fvg(last_four)
        
        if not signal:
            continue
        
        current_direction = None
        if open_positions:
            current_direction = open_positions[0]['direction']
        
        # Manejar operaciones
        if current_direction and current_direction != signal:
            # Cerrar todas las operaciones
            for pos in open_positions:
                exit_price = current_close
                if pos['direction'] == 'Long':
                    pnl = (exit_price - pos['entry_price']) * pos['size']
                else:
                    pnl = (pos['entry_price'] - exit_price) * pos['size']
                capital += pnl
                balance_history.append(capital)
                trade_history.append({
                    'type': 'CLOSE_SIGNAL',
                    'direction': pos['direction'],
                    'entry': pos['entry_price'],
                    'exit': exit_price,
                    'pnl': pnl,
                    'duration': current_candle.name - pos['entry_time']
                })
            open_positions = []
            
            # Abrir nueva operación
            entry_price = current_close
            lookback = df.iloc[max(0, i-stop_limit_candle):i+1]
            
            if signal == 'Long':
                stop_val = lookback['low'].min()
            else:
                stop_val = lookback['high'].max()
            stop = Decimal(str(stop_val))
            
            risk_amount = capital * Decimal("0.05")
            risk_per_unit = abs(entry_price - stop)
            
            if risk_per_unit == Decimal("0"):
                continue
                
            size = risk_amount / risk_per_unit
            open_positions.append({
                'direction': signal,
                'entry_price': entry_price,
                'stop': stop,
                'size': size,
                'entry_time': current_candle.name
            })
            
        elif current_direction == signal:
            # Añadir a la operación existente
            existing_stops = [pos['stop'] for pos in open_positions]
            new_stop = min(existing_stops) if signal == 'Long' else max(existing_stops)
            
            entry_price = current_close
            risk_amount = capital * Decimal("0.05")
            risk_per_unit = abs(entry_price - new_stop)
            
            if risk_per_unit == Decimal("0"):
                continue
                
            size = risk_amount / risk_per_unit
            open_positions.append({
                'direction': signal,
                'entry_price': entry_price,
                'stop': new_stop,
                'size': size,
                'entry_time': current_candle.name
            })
            
        else:
            # Nueva operación
            entry_price = current_close
            lookback = df.iloc[max(0, i-stop_limit_candle):i+1]
            
            if signal == 'Long':
                stop_val = lookback['low'].min()
            else:
                stop_val = lookback['high'].max()
            stop = Decimal(str(stop_val))
            
            risk_amount = capital * Decimal("0.05")
            risk_per_unit = abs(entry_price - stop)
            
            if risk_per_unit == Decimal("0"):
                continue
                
            size = risk_amount / risk_per_unit
            open_positions.append({
                'direction': signal,
                'entry_price': entry_price,
                'stop': stop,
                'size': size,
                'entry_time': current_candle.name
            })
        
        limpiar_consola()
        print(f"{i}/{len(df)}\nBalance: {capital}")

    # Cerrar operaciones restantes al final
    for pos in open_positions:
        exit_price = Decimal(str(df.iloc[-1]['close']))
        if pos['direction'] == 'Long':
            pnl = (exit_price - pos['entry_price']) * pos['size']
        else:
            pnl = (pos['entry_price'] - exit_price) * pos['size']
        capital += pnl
        balance_history.append(capital)
        trade_history.append({
            'type': 'FINAL_CLOSE',
            'direction': pos['direction'],
            'entry': pos['entry_price'],
            'exit': exit_price,
            'pnl': pnl,
            'duration': df.index[-1] - pos['entry_time']
        })
    
    
    # Métricas
    total_trades = len(trade_history)
    winning_trades = len([t for t in trade_history if t['pnl'] > 0])
    losing_trades = len([t for t in trade_history if t['pnl'] < 0])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    total_profit = sum(t['pnl'] for t in trade_history)
    total_loss = abs(sum(t['pnl'] for t in trade_history if t['pnl'] < 0))
    profit_factor = (total_profit / total_loss) if total_loss > 0 else 0




    # Crear un DataFrame con el historial de balance
    balance_df = pd.DataFrame(balance_history, columns=['Balance'])
    balance_df.index.name = 'Time'
    # Redondear a 2 cifras decimales
    balance_df = balance_df.round(2)
    # Exportar a CSV
    balance_df.to_csv('balance_history.csv')
    # Mostrar las primeras filas del DataFrame exportado
    print(balance_df.head())


    # Gráfico (se convierten los Decimals a float para graficar)
    plt.figure(figsize=(12, 6))
    plt.plot([float(b) for b in balance_history])
    plt.title('Evolución del balance de la cuenta')
    plt.xlabel('Tiempo')
    plt.ylabel('Balance (USD)')
    plt.grid(True)
    plt.show()
    
    # Mostrar métricas
    print(f"\n{'*'*40}")
    print(f"*{'RESULTADOS DEL BACKTEST':^38}*")
    print(f"{'*'*40}")
    print(f"Capital final: ${capital}")
    print(f"Retorno total: {((capital / Decimal('1000')) - Decimal('1')) * Decimal('100'):.2f}%")
    print(f"Operaciones totales: {total_trades}")
    print(f"Tasa de aciertos: {win_rate:.2f}%")
    print(f"Operaciones ganadoras: {winning_trades}")
    print(f"Operaciones perdedoras: {losing_trades}")
    print(f"Beneficio neto: ${total_profit}")
    print(f"Factor de beneficio: {profit_factor:.2f}")
    print(f"{'*'*40}")

if __name__ == "__main__":
    main()
