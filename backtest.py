from binance.client import Client
import pandas as pd
import talib 
from datetime import datetime
import numpy as np

# symbol = str(input("İşlem yapmak istediğiniz coinin adını  giriniz (örn : BTCUSDT) : "))
# interval = int(input("Zaman dilimini seçiniz : 1- 5 dakika \n 2- 15 dakika \n 3- 30 dakika \n 4- 1 saat \n 5- 4 saat \n 6- 1 gün \n"))
# if interval == 1:
#     interval = Client.KLINE_INTERVAL_5MINUTE
# if interval == 2:
#     interval = Client.KLINE_INTERVAL_15MINUTE
# if interval == 3:
#     interval = Client.KLINE_INTERVAL_30MINUTE
# if interval == 4:
#     interval = Client.KLINE_INTERVAL_1HOUR
# if interval == 5:
#     interval = Client.KLINE_INTERVAL_4HOUR
# if interval == 6:
#     interval = Client.KLINE_INTERVAL_1DAY
# if interval == None:
#     interval == Client.KLINE_INTERVAL_15MINUTE

# Kullanıcıdan TP ve SL seviyelerini yüzdelik olarak veya ATR ile girmesini isteyin
# tp_level = float(input("Kar Alma Seviyesini (%) veya ATR cinsinden girin: "))
# sl_level = float(input("Zararı Durdurma Seviyesini (%) veya ATR cinsinden girin: "))


api_key = None
api_secret = None

client = Client(api_key, api_secret)
klines = client.futures_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_15MINUTE,limit = 500)
    
df = pd.DataFrame(klines, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])

df["open"] = pd.to_numeric(df["open"])
df["high"] = pd.to_numeric(df["high"])
df["low"] = pd.to_numeric(df["low"])
df["close"] = pd.to_numeric(df["close"])
df["volume"] = pd.to_numeric(df["volume"])
df["timestamp"] = df["timestamp"].apply(lambda x: datetime.fromtimestamp(x / 1000).strftime('%Y-%m-%d %H:%M'))

# Mum Bilgileri
open = df["open"]
high = df["high"]
low = df["low"]
close = df["close"]
vol = df["volume"]
timestamp = df["timestamp"]

# RSI 
df["rsi"] = talib.RSI(close, timeperiod=14)
rsi = df["rsi"]

# Bollinger Bantları
df["upper_band"], df["middle_band"], df["lower_band"] = talib.BBANDS(close, timeperiod=20)
upper_band = df["upper_band"]
lower_band = df["lower_band"]

# ATR (Average True Range) hesaplaması
df["atr"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=14)
atr = df["atr"]

# MACD 

macd, signal, hist = talib.MACD(df["close"], fastperiod=12, slowperiod=26, signalperiod=9)

# Başlangıç Değişkenleri
cuzdan = 1000
odenen_komisyon = 0
kaldirac = 10
komisyon_orani = 0.002
long_position = False
short_position = False
long_entry_price = 0.0
short_entry_price = 0.0
successful_trades = 0
unsuccessful_trades = 0
tp_level = 2
sl_level = 2



# Long işlem sonucu kar ya da zarar hesaplayan fonksiyon
def long_kar_zarar_hesapla(index, long_entry_price, long_exit_price, cuzdan, kaldirac, komisyon_orani):
    if cuzdan > 0:
        coin_miktar = (cuzdan * kaldirac) / (close[index] * (1 + komisyon_orani)) # 100 dolar ile 10 dolar olan coinden 10 tane // coin_miktar = 1000 / 10 * (1.002)
        long_kar_zarar = (long_exit_price - long_entry_price) * coin_miktar
        cuzdan += long_kar_zarar
        return cuzdan, long_kar_zarar
    else:
        uyari = "Bakiyeniz Sıfırlanmıştır!"
        return uyari
    
# Short işlem sonucu kar ya da zarar hesaplayan fonksiyon    
def short_kar_zarar_hesapla(index, short_entry_price, short_exit_price, cuzdan, kaldirac, komisyon_orani):
    if cuzdan > 0:
        coin_miktar = (cuzdan * kaldirac) / (close[index] * (1 + komisyon_orani))
        short_kar_zarar = (short_entry_price - short_exit_price) * coin_miktar
        cuzdan += short_kar_zarar
        return cuzdan, short_kar_zarar
    else:
        uyari = "Bakiyeniz Sıfırlanmıştır!"
        return uyari

for i in range(len(close)):
    if i > 0:
        # Long İşlem koşulu ve işleme girme
        long_condition = ( close[i-1]<lower_band[i-1] ) and ( rsi[i-1]<30 ) and ( hist[i] > hist[i-1] or rsi[i] > rsi[i-1]) and close[i] >= lower_band[i]
        long_condition2 = ( low[i-1]<lower_band[i-1]) and ( rsi[i-1]<30 ) and (hist[i] > hist[i-1] or rsi[i] > rsi[i-1])
        long_condition3 = (close[i-1]<lower_band[i-1]) and (close[i]>lower_band[i]) and close[i]>open[i] 
        if(not long_position and not short_position) and (long_condition or long_condition2 or long_condition3):
            odenen_komisyon = cuzdan*komisyon_orani
            cuzdan = cuzdan - odenen_komisyon
            long_entry_price = close[i]
            print(timestamp[i],"tarihinde long girildi giriş fiyatı :",long_entry_price,"cüzdan : ",cuzdan,"ödenen komisyon :",odenen_komisyon)
            long_position = True
            # Long için tp ve sl fiyatlarını belirleme
            if tp_level < 1:
                long_tp_level_price = long_entry_price * (1 + tp_level)
            else:
                long_tp_level_price = long_entry_price + tp_level * atr[i]

            if sl_level < 1:
                long_sl_level_price = long_entry_price * (1 - sl_level)
            else:
                long_sl_level_price = long_entry_price - sl_level * atr[i]
        # Long TP ve SL
        if long_position and (close[i] >= long_tp_level_price):
            cuzdan, long_kar_zarar = long_kar_zarar_hesapla(i, long_entry_price, close[i], cuzdan, kaldirac, komisyon_orani)
            print(timestamp[i], "Tarihinde Long işlem Kar Alma Seviyesine Ulaşıldı - İşlem Kapatılıyor Fiyat :",close[i],"Kar :",long_kar_zarar)
            successful_trades += 1
            long_position = False
        if long_position and (close[i] <= long_sl_level_price):
            cuzdan, long_kar_zarar = long_kar_zarar_hesapla(i, long_entry_price, close[i], cuzdan, kaldirac, komisyon_orani)
            print(timestamp[i], "Tarihinde Long işlem Zararı Durdurma Seviyesine Ulaşıldı - İşlem Kapatılıyor Fiyat :",close[i],"Zarar :",long_kar_zarar)
            unsuccessful_trades += 1
            long_position = False
        if long_position and close[i]>=upper_band[i]:
            cuzdan, long_kar_zarar = long_kar_zarar_hesapla(i, long_entry_price, close[i], cuzdan, kaldirac, komisyon_orani)
            print(timestamp[i], "Tarihinde Long işlem Bollinger Üst Bandının Seviyesine Geldi - İşlem Kapatılıyor Fiyat :",close[i],"Kar :",long_kar_zarar)
            if long_entry_price < close[i]:
                successful_trades += 1
            else:
                unsuccessful_trades
            long_position = False
        if long_position and close[i]<lower_band[i]:
            cuzdan, long_kar_zarar = long_kar_zarar_hesapla(i, long_entry_price, close[i], cuzdan, kaldirac, komisyon_orani)
            print(timestamp[i], "Tarihinde Long işlem Bollinger alt Bandının Seviyesine Geldi - İşlem Kapatılıyor Fiyat :",close[i],"Kar :",long_kar_zarar)
            if long_entry_price < close[i]:
                successful_trades += 1
            else:
                unsuccessful_trades
            long_position = False    
        # Short işleme girme koşulu ve işleme girme
        short_condition = ( close[i-1]>upper_band[i-1] ) and ( rsi[i-1]>70 ) and ( hist[i]<hist[i-1] or rsi[i]<rsi[i-1]) and close[i] <= upper_band[i]
        short_condition2 = ( high[i-1]>upper_band[i-1] ) and ( rsi[i-1]>70 ) and ( hist[i]<hist[i-1] or rsi[i]<rsi[i-1] )
        short_condition3 = (close[i-1]>upper_band[i-1]) and (close[i]<upper_band[i]) and close[i]<open[i] and (hist[i]<hist[i-1] or rsi[i]<rsi[i-1]) 
        if (not short_position and not long_position) and (short_condition or short_condition2 or short_condition3):
            odenen_komisyon = cuzdan*komisyon_orani
            cuzdan = cuzdan - odenen_komisyon
            short_entry_price = close[i]
            print(timestamp[i],"tarihinde short girildi giriş fiyatı :",short_entry_price,"cüzdan : ",cuzdan,"ödenen komisyon :",odenen_komisyon)
            short_position = True
            # Long için tp ve sl fiyatlarını belirleme
            if tp_level < 1:
                short_tp_level_price = short_entry_price * (1 - tp_level)
            else:
                short_tp_level_price = short_entry_price - tp_level * atr[i]

            if sl_level < 1:
                short_sl_level_price = short_entry_price * (1 + sl_level)
            else:
                short_sl_level_price = short_entry_price + sl_level * atr[i]
        # Short TP ve SL
        if short_position and close[i] <= short_tp_level_price:
                cuzdan, short_kar_zarar = short_kar_zarar_hesapla(i, short_entry_price, close[i], cuzdan, kaldirac, komisyon_orani)
                print(timestamp[i], "Tarihinde Short işlem Kar Alma Seviyesine Ulaşıldı - İşlem Kapatılıyor Fiyat :",close[i],"kar :",short_kar_zarar)
                successful_trades += 1
                short_position = False
        if short_position and close[i] >= short_sl_level_price:
                cuzdan, short_kar_zarar = short_kar_zarar_hesapla(i, short_entry_price, close[i], cuzdan, kaldirac, komisyon_orani)
                print(timestamp[i], "Tarihinde Short işlem Zararı Durdurma Seviyesine Ulaşıldı - İşlem Kapatılıyor Fiyat :",close[i],"zarar :",short_kar_zarar)
                unsuccessful_trades += 1
                short_position = False
        if short_position and close[i] <= lower_band[i]:
                cuzdan, short_kar_zarar = short_kar_zarar_hesapla(i, short_entry_price, close[i], cuzdan, kaldirac, komisyon_orani)
                print(timestamp[i], "Tarihinde Short işlem Bollinger Alt Bandının Seviyesine Ulaşıldı - İşlem Kapatılıyor Fiyat :",close[i],"kar :",short_kar_zarar)
                short_position = False 
                if short_entry_price > close[i]:
                    successful_trades += 1
                else:
                    unsuccessful_trades +=1
                short_position = False
        if short_position and close[i] > upper_band[i]:
                cuzdan, short_kar_zarar = short_kar_zarar_hesapla(i, short_entry_price, close[i], cuzdan, kaldirac, komisyon_orani)
                print(timestamp[i], "Tarihinde Short işlem Bollinger Üst Bandının Seviyesine Ulaşıldı - İşlem Kapatılıyor Fiyat :",close[i],"kar :",short_kar_zarar)
                short_position = False 
                if short_entry_price > close[i]:
                    successful_trades += 1
                else:
                    unsuccessful_trades +=1
                short_position = False        

print("Başarılı işlem sayısı :",successful_trades)
print("Başarısız işlem sayısı :",unsuccessful_trades)
print("Son cüzdan bakiyesi :",cuzdan)