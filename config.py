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
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQghnJr1DuQVo68tbXu
7Z89GIC8reoOax2tjMzeQsskyFmhRANCAAQcexSx4PzjcHJ1blGN2JG37fzS/2JC
hwcS3lggBx7Rgg15AJXt1DdnlJSjfjQCInLtmam0qEqC+JLzmQsuGQcE
-----END PRIVATE KEY-----
'''
api_public_key_auth = '''-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEHHsUseD843BydW5RjdiRt+380v9i
QocHEt5YIAce0YINeQCV7dQ3Z5SUo340AiJy7ZmptKhKgviS85kLLhkHBA==
-----END PUBLIC KEY-----
'''

