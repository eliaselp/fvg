capital_inicial = 100
stop_limit_candle = 24 #El mejor testeado en 2024 es de 24 velas
time_limit = True



### CONFIG COINEX ###
access_id = "CA67B0440BB547499F0BF8A632741AF0"
secret_key = "5BBFB51795FDCFB32777F34F113720EC9C2598905DBD679F"
simbol="BTCUSDT"
size=50
temporalidad="1hour"
'''
 ["1min", "3min", "5min", "15min", "30min", "1hour", "2hour", "4hour", "6hour", "12hour" , "1day", "3day", "1week"]
'''

















#tamanio_ventana = 7
#name_dataset = "BTCUSD_ohlcv__1h.csv"
incluir_precio_actual = False
notificar_monitoreo = True
tiempo_espera = 10




#### API ELIAS IA ####
url_base = "https://yungia.pythonanywhere.com/"
#url_base = "http://localhost:8000"
uid = 'e1be501d'
api_private_key_sign = '''-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg/fLVwKjgNzVe+mgf
oKvuJtbmm279IWlsd2QbMe5LweChRANCAATsZlFSCuxBk+ZLZnu4kcUhVXCaSZFs
F5eA7WP2aCbPCZ82OaQOXCrO+3mp7FPJr6fSpoSBFeb/l9J1LYfZ+bAG
-----END PRIVATE KEY-----
'''
api_public_key_auth = '''-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE7GZRUgrsQZPmS2Z7uJHFIVVwmkmR
bBeXgO1j9mgmzwmfNjmkDlwqzvt5qexTya+n0qaEgRXm/5fSdS2H2fmwBg==
-----END PUBLIC KEY-----
'''

