#Import the libraries
import numpy as np
import pandas as pd
import time
import datetime
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

#Load the data (from google colab)
#Not using google.colab import file method, using yfinance method below
#https://www.youtube.com/watch?v=NjEc7PB0TxQ
#from google.colab import files
#files.upload()

ticker = "AAPL"
period1 = int(time.mktime(datetime.datetime(2021, 1, 1, 23, 59).timetuple()))
period2 = int(time.mktime(datetime.datetime(2021, 8, 31, 23, 59).timetuple()))
interval = "1d" # 1d, 1wk 1m

query_string = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={period1}&period2={period2}&interval={interval}&events=history&includeAdjustedClose=true"

df = pd.read_csv(query_string)
#print(df) # but the index is number 0, 1, 2, 3 ...
# making the date as index
df = df.set_index(pd.DatetimeIndex(df['Date'].values))
#pd.set_option("display.max_rows", None, "display.max.columns", None)
#print(df)

# visually show the close price
#plt.figure(figsize=(16,8))
#plt.title("Close Price History", fontsize = 18)
#plt.plot(df["Close"])
#plt.xlabel("Date", fontsize=18)
#plt.ylabel("Close Price", fontsize=18)
#plt.show()

def print_full(x):
    pd.set_option('display.max_rows', len(x), 'display.max_columns', len(df.columns), 'display.width', 100000)
    print(x)
    pd.reset_option('display.max_rows', 'display.max_columns')

# Create a function to calculate the SMA
def SMA(data, period = 30, column="Close"):
    return data[column].rolling(window=period).mean()

# Define ROC function
# ROC = ((Most recent closing price - Closing price n periods ago) / Closing price n periods ago) x 100
def ROC(df,n):
    M = df.diff(n-1)
    N = df.shift(n-1)
    ROC = pd.Series(((M/N)*100), name="ROC_" + str(n))
    return ROC

# Commodity Channel Index
def CCI(df, n):
    df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['sma'] = df['TP'].rolling(n).mean()
    df['mad'] = df['TP'].rolling(n).apply(lambda x: pd.Series(x).mad())
    df['CCI'] = (df['TP'] - df['sma']) / (0.015 * df['mad'])
    return df['CCI']

# Compute the Bollinger Bands
def BBANDS(df, n):
    df['MA'] = df['Close'].rolling(n).mean()
    df['SD'] = df['Close'].rolling(n).std()
    df['UpperBB'] = df['MA'] + (2 * df['SD'])
    df['LowerBB'] = df['MA'] - (2 * df['SD'])
    return df

def WMA(df, period: int = 9, column: str = "Close"):

     d = (period * (period + 1)) / 2  # denominator
     weights = np.arange(1, period + 1)

     def linear(w):
         def _compute(x):
             return (w * x).sum() / d

         return _compute

     _close = df[column].rolling(period, min_periods=period)
     wma = _close.apply(linear(weights), raw=True)

     return pd.Series(wma, name="{0} period WMA.".format(period))

def HMA(df, period: int = 9):
    import math

    half_length = int(period / 2)
    sqrt_length = int(math.sqrt(period))

    df["wmaf"] = WMA(df, period=half_length)
    df["wmas"] = WMA(df, period=period)
    df["deltawma"] = 2 * df["wmaf"] - df["wmas"]
    df["hma"] = WMA(df, column="deltawma", period=sqrt_length)
    hma = WMA(df, column="deltawma", period=sqrt_length)

    return pd.Series(hma, name="{0} period HMA.".format(period))

# https://www.roelpeters.be/many-ways-to-calculate-the-rsi-in-python-pandas/
def RSI(df, periods=14, ema=True):
    #Returns a pd.Series with the relative strength index.
    close_delta = df['Close'].diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    if ema == True:
        # Use exponential moving average
        ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
        ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window=periods, adjust=False).mean()
        ma_down = down.rolling(window=periods, adjust=False).mean()

    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))
    return rsi

# Create 4 new columns to store the SMA20, SMA50, ROC & RSI
df["SMA20"] = SMA(df,20)
df["SMA50"] = SMA(df,50)
df["WMA9"] = WMA(df,9)
df["HMA9"] = HMA(df,9)
df["ROC"] = ROC(df["Close"],14)
df["RSI"] = RSI(df,14, True)
df["CCI"] = CCI(df,14)

# Get the buy & sell signals
# We get 4 signals, 1-1, 1-0, 0-1, 0-0 (based on the 1,0 output), so we get both buy/sell signals
df["SMA_Signal"] = np.where(df["SMA20"] > df["SMA50"], 1, 0)
df["WMA_HMA_Signal"] = np.where(df["HMA9"] > df["WMA9"], 1, 0)
df["ROC_Signal"] = np.where(df["ROC"] > 0, 1, 0)
df["ROC_Diff"] = df["ROC"].diff()
df["ROC_Slope"] = np.where(df["ROC_Diff"] > 0, 1, 0)
df["CCI_Signal"] = np.where(df["CCI"] > 100, 1, 0)
#This ROC_Slope was causing too many buy-sell signals
#df["Signal"] = np.where(df["SMA_Signal"] & df["ROC_Signal"] & df["ROC_Slope"] > 0, 1, 0)
df["SMA_Signal"] = np.where(df["SMA_Signal"] & df["ROC_Signal"] & df["CCI_Signal"] > 0, 1, 0)
df["WMA_HMA_Signal"] = np.where(df["WMA_HMA_Signal"] & df["ROC_Signal"] & df["CCI_Signal"] > 0, 1, 0)

# Subtract the previous signal from the current signal
#df["Signal"] = df["SMA_Signal"] and df["ROC_Signal"]
df["SMA_Position"] = df["SMA_Signal"].diff()
# Create a new column called BUY
# Position = 4 Signal Changes: Current - Previous: 0-0 = 0, 1-1 = 0, 1-0 = 1, 0-1 = -1
# Position = 1 (BUY), -1 (SELL), 0 (NAN: No Change)
df["SMA_Buy"] = np.where(df["SMA_Position"] == 1, df["Close"], np.NAN)
df["SMA_Sell"] = np.where(df["SMA_Position"] == -1, df["Close"], np.NAN)

# Subtract the previous signal from the current signal
#df["Signal"] = df["SMA_Signal"] and df["ROC_Signal"]
df["WMA_HMA_Position"] = df["WMA_HMA_Signal"].diff()
# Create a new column called BUY
# Position = 4 Signal Changes: Current - Previous: 0-0 = 0, 1-1 = 0, 1-0 = 1, 0-1 = -1
# Position = 1 (BUY), -1 (SELL), 0 (NAN: No Change)
df["WMA_HMA_Buy"] = np.where(df["WMA_HMA_Position"] == 1, df["Close"], np.NAN)
df["WMA_HMA_Sell"] = np.where(df["WMA_HMA_Position"] == -1, df["Close"], np.NAN)

#print(df.tail())
#print_full(df.tail())
print_full(df)


# visually show the close price
plt.figure(figsize=(23,24))

#In order to split the figure you should give 3-digit integer as a parameter to subplot().
# The integers describe the position of subplots: first digit is the number of rows, the second is the number of columns, and the third is the index of the subplot
plt.subplot(511)
plt.title("Close Price History with MA Crossover Buy/Sell Signals", fontsize = 18)
plt.plot(df["Close"], alpha=0.5, label ="Close")
plt.plot(df["SMA20"], alpha=0.5, label ="SMA20")
plt.plot(df["SMA50"], alpha=0.5, label ="SMA50")
#plt.plot(df["WMA9"], alpha=0.5, label ="WMA9", color="Blue")
#plt.plot(df["HMA9"], alpha=0.5, label ="HMA9", color="Red")
plt.scatter(df.index, df["SMA_Buy"], alpha=1, label="Buy Signal", marker="^", color="Green")
plt.scatter(df.index, df["SMA_Sell"], alpha=1, label="Sell Signal", marker="v", color="Red")
plt.xlabel("Date", fontsize=12)
plt.ylabel("Close Price", fontsize=18)
plt.legend()

plt.subplot(512)
#plt.title("Close Price History with HMA/WMA Crossover Buy/Sell Signals", fontsize = 18)
plt.plot(df["Close"], alpha=0.5, label ="Close")
plt.plot(df["WMA9"], alpha=0.5, label ="WMA9", color="Blue")
plt.plot(df["HMA9"], alpha=0.5, label ="HMA9", color="Red")
plt.scatter(df.index, df["WMA_HMA_Buy"], alpha=1, label="Buy Signal", marker="^", color="Green")
plt.scatter(df.index, df["WMA_HMA_Sell"], alpha=1, label="Sell Signal", marker="v", color="Red")
plt.xlabel("Date", fontsize=12)
plt.ylabel("Close Price", fontsize=18)
plt.legend()

plt.subplot(513)
plt.plot(df["ROC"], alpha=0.5, label ="ROC")
plt.xlabel("Date", fontsize=12)
plt.ylabel("ROC", fontsize=18)
plt.legend()

plt.subplot(514)
plt.plot(df["RSI"], alpha=0.5, label ="RSI")
plt.xlabel("Date", fontsize=12)
plt.ylabel("RSI", fontsize=18)
plt.legend()

plt.subplot(515)
plt.plot(df["CCI"], alpha=0.5, label ="CCI")
plt.xlabel("Date", fontsize=12)
plt.ylabel("CCI", fontsize=18)
plt.legend()


plt.show()

#print(df)