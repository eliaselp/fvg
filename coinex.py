import hashlib
import time
from urllib.parse import urlparse
import requests
import config
import pandas as pd

class RequestsClient(object):
    __HEADERS = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "X-COINEX-KEY": "",
        "X-COINEX-SIGN": "",
        "X-COINEX-TIMESTAMP": "",
    }

    def __init__(self,access_id = config.access_id,secret_key = config.secret_key):
        self.access_id = access_id
        self.secret_key = secret_key
        self.url = "https://api.coinex.com/v2"
        self.headers = self.__HEADERS.copy()

    # Generate your signature string
    def __gen_sign(self, method, request_path, body, timestamp):
        prepared_str = f"{method}{request_path}{body}{timestamp}{self.secret_key}"
        signed_str = hashlib.sha256(prepared_str.encode("utf-8")).hexdigest().lower()
        return signed_str

    def __get_common_headers(self, signed_str, timestamp):
        headers = self.__HEADERS.copy()
        headers["X-COINEX-KEY"] = self.access_id
        headers["X-COINEX-SIGN"] = signed_str
        headers["X-COINEX-TIMESTAMP"] = timestamp
        headers["Content-Type"] = "application/json; charset=utf-8"
        return headers

    def __request(self, method, url, params={}, data=""):
        req = urlparse(url)
        request_path = req.path

        timestamp = str(int(time.time() * 1000))
        if method.upper() == "GET":
            # If params exist, query string needs to be added to the request path
            if params:
                query_params = []
                for item in params:
                    if params[item] is None:
                        continue
                    query_params.append(item + "=" + str(params[item]))
                query_string = "?{0}".format("&".join(query_params))
                request_path = request_path + query_string

            signed_str = self.__gen_sign(
                method, request_path, body="", timestamp=timestamp
            )
            response = requests.get(
                url,
                params=params,
                headers=self.__get_common_headers(signed_str, timestamp),
            )

        else:
            signed_str = self.__gen_sign(
                method, request_path, body=data, timestamp=timestamp
            )
            response = requests.post(
                url, data, headers=self.__get_common_headers(signed_str, timestamp)
            )

        if response.status_code != 200:
            raise ValueError(response.text)
        return response


    ###################################################################
    def get_data(self):
        request_path = "/futures/kline"
        params = {
            "market":config.simbol,
            "limit":config.size,
            "period":config.temporalidad
        }
        response = self.__request(
            "GET",
            "{url}{request_path}".format(url=self.url, request_path=request_path),
            params=params,
        )
        data=response.json().get("data")
        ohlcv_df = pd.DataFrame(data)
        # Convertir las columnas de precios y volumen a numérico
        ohlcv_df['close'] = pd.to_numeric(ohlcv_df['close'])
        ohlcv_df['high'] = pd.to_numeric(ohlcv_df['high'])
        ohlcv_df['low'] = pd.to_numeric(ohlcv_df['low'])
        ohlcv_df['open'] = pd.to_numeric(ohlcv_df['open'])
        ohlcv_df['volume'] = pd.to_numeric(ohlcv_df['volume'])

        self.current_price = ohlcv_df['close'].iloc[-1]
        ohlcv_df = ohlcv_df.drop('market', axis=1)
        ohlcv_df = ohlcv_df.drop('created_at', axis=1)
        ohlcv_df = ohlcv_df.drop('value', axis=1)

        precio_actual = int(ohlcv_df['close'].iloc[-1])
        maximo = int(ohlcv_df['high'].iloc[-1])
        minimo = int(ohlcv_df['low'].iloc[-1])
        
        if config.incluir_precio_actual==False:
            ohlcv_df = ohlcv_df.drop(ohlcv_df.index[-1])

        
        # Reorganizar las columnas
        column_order = ['open', 'high', 'low', 'close', 'volume']
        ohlcv_df= ohlcv_df[column_order]
        return ohlcv_df,[precio_actual,maximo,minimo]
    