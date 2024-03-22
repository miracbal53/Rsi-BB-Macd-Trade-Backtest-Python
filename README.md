# Rsi-BB-Macd-Trade-Backtest-Python

![Ekran görüntüsü 2023-11-05 191102](https://github.com/miracbal53/Rsi-BB-Macd-Trade-Backtest-Python/assets/108282437/a216f3f2-dd78-4602-9579-d3195d1a42d0)

Backtest sonuçları ekran görüntüsünde gözüktüğü gibi 

Strategy Logic:

For Long Trades: Closing below the Lower Bollinger Band with a reversal signal from MACD or RSI or similar indicators.

For Short Trades: Closing above the Upper Bollinger Band with a reversal signal from MACD or RSI or similar indicators.

TP (Take Profit) and SL (Stop Loss) Conditions:

There are two different methods for TP and SL:

1. ATR (Average True Range): If the variables tp_level and sl_level are greater than 1, it considers them as ATR values. For example, entering a value like 0.002 would be interpreted as 0.2%.
2. Percentage: If the tp_level and sl_level variables are between 0 and 1, they are interpreted as percentages. For instance, entering a value like 0.002 would be interpreted as 0.2%.
