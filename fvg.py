import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import time
import pickle
from datetime import datetime
#from decimal import Decimal, getcontext

import config
import monitor
from coinex import RequestsClient

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

class FVG_BOT():
    def __init__(self):
        self.cliente_coinex = RequestsClient()
        self.last_data=""
        self.analisis = 0
        self.tendencia = None
        self.opr_win = 0
        self.opr_loss = 0

        self.public_key_temp_api = None


        self.capital = config.capital_inicial
        self.open_positions = []
        self.trade_history = []
        self.balance_history = [config.capital_inicial]
        
        self.stop_limit_candle = config.stop_limit_candle  # Número de velas para calcular el stop loss
        self.time_limit = config.time_limit


       
        self.current_low   = None
        self.current_high  = None
        self.current_close = None
        




    def start(self):
        self.public_key_temp_api = monitor.post_action(valor=self.capital ,numero_analisis=1,public_key_temp_api=self.public_key_temp_api)
        while(True):
            error = None
            try:
                df,vela_actual= self.cliente_coinex.get_data()
                if self.last_data != str(df):
                    self.analisis += 1

                    self.last_data = str(df)

                    self.current_close = vela_actual[0]
                    self.current_high = int(df['high'].iloc[-1])
                    self.current_low = int(df['low'].iloc[-1])


                    self.check_stoploss()


                    if self.time_limit == True:
                        # Verificar si la vela actual no está dentro de la ventana de trading
                        current_time = datetime.now().time()
                        if not (TRADING_WINDOW_START <= current_time <= TRADING_WINDOW_END):
                            # Fuera de la ventana: cerrar todas las posiciones abiertas
                            self.close_all_position(motivo='CLOSED_OUTSIDE_WINDOW')
                            continue  # No se abren nuevas operaciones fuera de la ventana
                    
                    # Detectar señal FVG
                    last_four = df.iloc[-4:]
                    signal = self.detect_fvg(last_four)
                    
                    if not signal:
                        continue
                    
                    current_direction = None
                    self.tendencia = None
                    if self.open_positions:
                        current_direction = self.open_positions[0]['direction']
                        self.tendencia = current_direction
                    
                    # Manejar operaciones
                    operation = None
                    if current_direction and current_direction != signal:
                        # Cerrar todas las operaciones
                        self.close_all_position(motivo='CLOSE_SIGNAL')
                        operation = self.open_new_operation(lookback=df.iloc[-self.stop_limit_candle:], signal=signal, )
                    elif current_direction == signal:
                        # Añadir a la operación existente
                        existing_stops = [pos['stop'] for pos in self.open_positions]
                        new_stop = min(existing_stops) if signal == 'Long' else max(existing_stops)
                        
                        entry_price = self.current_close
                        risk_amount = self.capital * 0.05
                        risk_per_unit = abs(entry_price - new_stop)
                        
                        if not (risk_per_unit == "0" or risk_amount > 2):    
                            size = risk_amount / risk_per_unit
                            self.open_positions.append({
                                'direction': signal,
                                'entry_price': entry_price,
                                'stop': new_stop,
                                'size': size,
                            })
                    else:
                        self.open_new_operation(lookback=df.iloc[-self.stop_limit_candle:],signal=signal)    
            except Exception as e:
                error = str(e)
            ##<########## 
            s = self.print_data() 
            self.public_key_temp_api = monitor.update_text_code(mensaje=s,public_key_temp_api=self.public_key_temp_api)
            limpiar_consola(s)
            if error:
                print(error)
            print()      

            
            tiempo_espera=config.tiempo_espera
            for i in range(tiempo_espera, 0, -1):
                sys.stdout.write("\rTiempo restante: {:02d}:{:02d} ".format(i // 60, i % 60))
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
            sys.stdout.flush()




    
    def open_new_operation(self,lookback,signal):
        entry_price = self.current_close
        
        stop = 0
        if signal == 'Long':
            stop = lookback['low'].min()
        else:
            stop = lookback['high'].max()
        
        risk_amount = self.capital * 0.05
        risk_per_unit = abs(entry_price - stop)
        
        if risk_per_unit == 0 or risk_amount > 2:
            return None
            
        size = risk_amount / risk_per_unit
        self.open_positions.append({
            'direction': signal,
            'entry_price': entry_price,
            'stop': stop,
            'size': size,
        })
        return {
            'direction': signal,
            'entry_price': entry_price,
            'stop': stop,
            'size': size,
        }
    
    def check_stoploss(self):
        # Cerrar operaciones por stop loss
        to_remove = []
        for pos in self.open_positions:
            if pos['direction'] == 'Long' and self.current_low <= pos['stop']:
                pnl = (pos['stop'] - pos['entry_price']) * pos['size']
                self.capital += pnl
                self.public_key_temp_api = monitor.post_action(valor=self.capital ,numero_analisis=self.analisis,public_key_temp_api=self.public_key_temp_api)
                if pnl > 0:
                    self.opr_win += 1
                else:
                    self.opr_loss += 1
                
                self.balance_history.append(self.capital)
                self.trade_history.append({
                    'type': 'STOP_LOSS',
                    'direction': pos['direction'],
                    'entry': pos['entry_price'],
                    'exit': pos['stop'],
                    'pnl': pnl,
                })
                to_remove.append(pos)
            elif pos['direction'] == 'Short' and self.current_high >= pos['stop']:
                pnl = (pos['entry_price'] - pos['stop']) * pos['size']
                self.capital += pnl
                self.public_key_temp_api = monitor.post_action(valor=self.capital ,numero_analisis=self.analisis,public_key_temp_api=self.public_key_temp_api)
                if pnl > 0:
                    self.opr_win += 1
                else:
                    self.opr_loss += 1
                
                self.balance_history.append(self.capital)
                self.trade_history.append({
                    'type': 'STOP_LOSS',
                    'direction': pos['direction'],
                    'entry': pos['entry_price'],
                    'exit': pos['stop'],
                    'pnl': pnl,
                })
                to_remove.append(pos)
        for pos in to_remove:
            self.open_positions.remove(pos)

    def close_all_position(self,motivo):
        if self.open_positions:
            for pos in self.open_positions:
                exit_price = self.current_close
                if pos['direction'] == 'Long':
                    pnl = (exit_price - pos['entry_price']) * pos['size']
                else:
                    pnl = (pos['entry_price'] - exit_price) * pos['size']
                if pnl > 0:
                    self.opr_win += 1
                else:
                    self.opr_loss += 1
                
                self.capital += pnl
                self.public_key_temp_api = monitor.post_action(valor=self.capital ,numero_analisis=self.analisis,public_key_temp_api=self.public_key_temp_api)
                self.balance_history.append(self.capital)
                self.trade_history.append({
                    'type': motivo,
                    'direction': pos['direction'],
                    'entry': pos['entry_price'],
                    'exit': exit_price,
                    'pnl': pnl,
                })
            self.open_positions = []

    def detect_fvg(self,last_four_candles):
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

    def print_data(self):
        s = f"[#] Analisis: f{self.analisis}\n"
        s+= f"[#] Tendencia actual: {self.tendencia}\n"
        s+= f"[#] Precio actual: {self.current_close}\n"
        s+= f"[#] Ganancia: {self.capital}\n"
        s+= f"[#] Opr. Ganadas: {self.opr_win}\n"
        s+= f"[#] Opr. Perdidas: {self.opr_loss}\n"
        total_profit = sum(t['pnl'] for t in self.trade_history)
        total_loss = abs(sum(t['pnl'] for t in self.trade_history if t['pnl'] < 0))
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        s+= f"[#] Total Profit {total_profit}\n"
        s+= f"[#] Total Loss: {total_loss}\n"
        s+= f"[#] Profit factor: {profit_factor}\n"

        s+= f"\n\n\n"
        total = 0
        s+= f"{'*'*40}\n"
        for opr in self.open_positions:
            profit = (opr['entry_price'] - self.current_close) * opr['size'] if opr['direction'] == 'Short' else (self.current_close - opr['entry_price']) * opr['size']
            total += profit
            s+= f"[+] Entry_price: {opr['entry_price']} | Profit: {profit}\n"
        f"{'*'*40}\n"
        return s


    #LISTO
    def save_state(self):
        with open('00_data.pkl', 'wb') as file:
            pickle.dump(self, file)

    #LISTO
    @staticmethod
    def load_state():
        if os.path.exists('00_data.pkl'):
            with open('00_data.pkl', 'rb') as file:
                return pickle.load(file)
        else:
            return None
