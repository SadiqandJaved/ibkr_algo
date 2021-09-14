import datetime

import pandas as pd
from finta import TA
from ibapi.client import EClient
# types
from ibapi.common import *  # @UnusedWildImport
from ibapi.contract import *  # @UnusedWildImport
from ibapi.order import Order
from ibapi.wrapper import EWrapper

# Using WMA for Slow & HMA for Fast indicator for both TF1 & TF2 time frames

TICKS_PER_CANDLE_TF1 = 5  #10 #34 #55 #89 #144 #233 #377
MOVING_AVG_PERIOD_LENGTH_TF1_S = 3 #9 #14 # slow timeframe (WMA)
MOVING_AVG_PERIOD_LENGTH_TF1_F = 3 #5 #9 # fast timeframe (WMA)
TICKS_PER_CANDLE_TF2 = 5 #5 #10 #34 #55 #89 #144 #233 #377
MOVING_AVG_PERIOD_LENGTH_TF2_S = 5 #9 #14 (WMA)
MOVING_AVG_PERIOD_LENGTH_TF2_F = 5 #5 #9 (WMA)

class TestApp(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.nextValidOrderId = None
        self.permId2ord = {}
        self.contract = Contract()
        self.data_tf1_s = []
        self.data_tf1_f = []
        self.data_tf2_s = []
        self.data_tf2_f = []
        self.data_counter_tf1_s = 0
        self.data_counter_tf1_f = 0
        self.data_counter_tf2_s = 0
        self.data_counter_tf2_f = 0
        self.roc_counter_tf1_s = 0
        self.roc_counter_tf1_f = 0
        self.roc_counter_tf2_s = 0
        self.roc_counter_tf2_f = 0
        self.cci_counter_tf1_s = 0
        self.cci_counter_tf1_f = 0
        self.cci_counter_tf2_s = 0
        self.cci_counter_tf2_f = 0
        self.mov_avg_length_tf1_s = MOVING_AVG_PERIOD_LENGTH_TF1_S
        self.mov_avg_length_tf1_f = MOVING_AVG_PERIOD_LENGTH_TF1_F
        self.mov_avg_length_tf2_s = MOVING_AVG_PERIOD_LENGTH_TF2_S
        self.mov_avg_length_tf2_f = MOVING_AVG_PERIOD_LENGTH_TF2_F
        self.ticks_per_candle_tf1 = TICKS_PER_CANDLE_TF1
        self.ticks_per_candle_tf2 = TICKS_PER_CANDLE_TF2
        self.tick_count = 0
        self.indicator_tf1_s = 0
        self.prev_indicator_tf1_s = 0
        self.indicator_tf1_f = 0
        self.prev_indicator_tf1_f = 0
        self.indicator_tf2_s = 0
        self.prev_indicator_tf2_s = 0
        self.indicator_tf2_f = 0
        self.prev_indicator_tf2_f = 0
        self.n = 0
        self.p = 0
        self.q = 0
        self.r = 0
        self.signal = 'NONE'
        self.prev_signal = 'NONE'
        self.roc_tf1_s = 0
        self.roc_tf1_f = 0
        self.roc_tf2_s = 0
        self.roc_tf2_f = 0
        self.cci_tf1_s = 0
        self.cci_tf1_f = 0
        self.cci_tf2_s = 0
        self.cci_tf2_f = 0
        self.df_indicator_tf1_s = pd.DataFrame()

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

        # we can start now
        self.start()

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    # This is the START of the MAIN program
    def start(self):
        self.tickDataOperations_req() # This is the HEART of the PROGRAM
        # self.accountOperations_req()
        print("\nExecuting requests ... finished\n")

    pd.set_option('display.max_rows', 10, 'display.max_columns', 100, 'display.width', 100000)

    # Commodity Channel Index
    # IF PREVIOUS CCI > OVERSOLD LEVEL AND CCI < OVERSOLD LEVEL = BUY
    # IF PREVIOUS CCI < OVERBOUGHT LEVEL AND CCI > OVERBOUGHT LEVEL = SELL
    def calc_cci_tf1_s(self):
        #self.cci_counter_tf1_s += 1
        #if self.cci_counter_tf1_s < self.mov_avg_length_tf1_s:
        #    return
        self.df_indicator_tf1_s = pd.DataFrame(self.data_tf1_s, columns=['cci_close'])
        self.df_indicator_tf1_s['cci_open'] = self.df_indicator_tf1_s['cci_close']
        self.df_indicator_tf1_s['cci_high'] = self.df_indicator_tf1_s['cci_close']
        self.df_indicator_tf1_s['cci_low'] = self.df_indicator_tf1_s['cci_close']
        # mad function computes the mean deviation based on the price provided
        # TP (typical price) we are using the same value close for all open/close/high/low since we are getting tick by tick data, and forming a candle
        self.df_indicator_tf1_s['TP'] = (self.df_indicator_tf1_s['cci_high'] + self.df_indicator_tf1_s['cci_low'] + self.df_indicator_tf1_s['cci_close']) / 3
        self.df_indicator_tf1_s['sma'] = self.df_indicator_tf1_s['TP'].rolling(MOVING_AVG_PERIOD_LENGTH_TF1_S).mean()
        self.df_indicator_tf1_s['mad'] = self.df_indicator_tf1_s['TP'].rolling(MOVING_AVG_PERIOD_LENGTH_TF1_S).apply(lambda x: pd.Series(x).mad())
        self.df_indicator_tf1_s['CCI'] =(self.df_indicator_tf1_s['TP'] - self.df_indicator_tf1_s['sma']) / (0.015 * self.df_indicator_tf1_s['mad'])
        print("df_indicator_tf1_s: \n", self.df_indicator_tf1_s, "\n")
        # print("CCI Calculation: TP=", self.df_indicator_tf1_s['TP'], "SMA=", self.df_indicator_tf1_s['sma'], "CCI=", self.df_indicator_tf1_s['CCI'], "\n")
        #return self.df_indicator_tf1_s['CCI']
        return self.df_indicator_tf1_s


    # Define ROC using Tick lis
    def calc_roc_tf1_s(self):
        self.roc_counter_tf1_s += 1
        if self.roc_counter_tf1_s < self.mov_avg_length_tf1_s:
            return
        print("\nData_TF1_S =", self.data_tf1_s, "ROC_Counter_TF1_S =", self.roc_counter_tf1_s, "Data_TF1_S_LEN =", len(self.data_tf1_s))
        if len(self.data_tf1_s) >= self.mov_avg_length_tf1_s:
            N = self.data_tf1_s[-MOVING_AVG_PERIOD_LENGTH_TF1_S] #value MOVING_AVG_PERIOD__LENGTH_TF1_S previous
            M = self.data_tf1_s[MOVING_AVG_PERIOD_LENGTH_TF1_S-1] #latest VALUE
            self.roc_tf1_s = ((M-N) / N) * 100
            print("ROC Calculation: M=", M, "N=", N, "ROC_TF1_S=", self.roc_tf1_s, "\n")

    def calc_roc_tf1_f(self):
        self.roc_counter_tf1_f += 1
        if self.roc_counter_tf1_f < self.mov_avg_length_tf1_f:
            return
        print("\nData_TF1_F =", self.data_tf1_f, "ROC_Counter_TF1_F =", self.roc_counter_tf1_f, "Data_TF1_F_LEN =", len(self.data_tf1_f))
        if len(self.data_tf1_f) >= self.mov_avg_length_tf1_f:
            N = self.data_tf1_f[-MOVING_AVG_PERIOD_LENGTH_TF1_F] #value MOVING_AVG_PERIOD__LENGTH_TF1_S previous
            M = self.data_tf1_f[MOVING_AVG_PERIOD_LENGTH_TF1_F-1] #latest VALUE
            self.roc_tf1_f = ((M-N) / N) * 100
            print("ROC Calculation: M=", M, "N=", N, "ROC_TF1_F=", self.roc_tf1_f, "\n")

    def calc_roc_tf2_s(self):
        self.roc_counter_tf2_s += 1
        if self.roc_counter_tf2_s < self.mov_avg_length_tf2_s:
            return
        print("\nData_TF2_S =", self.data_tf2_s, "ROC_Counter_TF2_S =", self.roc_counter_tf2_s, "Data_TF2_S_LEN =", len(self.data_tf2_s))
        if len(self.data_tf2_s) >= self.mov_avg_length_tf2_s:
            N = self.data_tf2_s[-MOVING_AVG_PERIOD_LENGTH_TF2_S] #value MOVING_AVG_PERIOD__LENGTH_TF2_S previous
            M = self.data_tf2_s[MOVING_AVG_PERIOD_LENGTH_TF2_S-1] #latest VALUE
            self.roc_tf2_s = ((M-N) / N) * 100
            print("ROC Calculation: M=", M, "N=", N, "ROC_TF2_S=", self.roc_tf2_s, "\n")

    def calc_roc_tf2_f(self):
        self.roc_counter_tf2_f += 1
        if self.roc_counter_tf2_f < self.mov_avg_length_tf2_f:
            return
        print("\nData_TF2_F =", self.data_tf2_f, "Data_Counter_TF2_F =", self.roc_counter_tf2_f, "Data_TF2_F_LEN =", len(self.data_tf2_f))
        if len(self.data_tf2_f) >= self.mov_avg_length_tf2_f:
            N = self.data_tf2_f[-MOVING_AVG_PERIOD_LENGTH_TF2_F] #value MOVING_AVG_PERIOD__LENGTH_TF2_F previous
            M = self.data_tf2_f[MOVING_AVG_PERIOD_LENGTH_TF2_F-1] #latest VALUE
            self.roc_tf2_f = ((M-N) / N) * 100
            print("ROC Calculation: M=", M, "N=", N, "ROC_TF2_F=", self.roc_tf2_f, "\n")

    #Not popping out the data as the HMA was nnt giving results, due to the fact that the df["deltawma"] didn't have enough columns to compute the hma((sq_root(n))
    #Mking the pop happen after "n" times mov_avg_length_tf* - enough not to fill the memory of DF, and have enough rows to calculate the HMA
    def running_list_tf1_s(self, price: float):
        self.data_tf1_s.append(price)
        self.data_counter_tf1_s += 1
        if self.data_counter_tf1_s < self.mov_avg_length_tf1_s:
            return
        while len(self.data_tf1_s) > (5 * self.mov_avg_length_tf1_s):
            self.data_tf1_s.pop(0)

    def running_list_tf1_f(self, price: float):
        self.data_tf1_f.append(price)
        self.data_counter_tf1_f += 1
        if self.data_counter_tf1_f < self.mov_avg_length_tf1_f:
            return
        while len(self.data_tf1_f) > (5 * self.mov_avg_length_tf1_f):
            self.data_tf1_f.pop(0)

    def running_list_tf2_s(self, price: float):
        self.data_tf2_s.append(price)
        self.data_counter_tf2_s += 1
        if self.data_counter_tf2_s < self.mov_avg_length_tf2_s:
            return
        while len(self.data_tf2_s) > (5 * self.mov_avg_length_tf2_s):
            self.data_tf2_s.pop(0)

    def running_list_tf2_f(self, price: float):
        self.data_tf2_f.append(price)
        self.data_counter_tf2_f += 1
        if self.data_counter_tf2_f < self.mov_avg_length_tf2_f:
            return
        while len(self.data_tf2_f) > (5 * self.mov_avg_length_tf2_f):
            self.data_tf2_f.pop(0)

    #iloc[-1] selects the last column of the dataframe
    #Converting the data_tf1_s list into a dataframe, since finta functions only uses DF
    #print("\nData_TF1_S =", self.data_tf1_s, "\n", "df_indicator_tf1_s =", df_indicator_tf1_s, "\n","indicator_tf1_s =", self.indicator_tf1_s, "\n")
    #Data_TF1_S = [4498.5, 4498.5, 4498.5, 4498.5, 4498.5] 
    #df_indicator_tf1_s =     close    open    high     low   indicator_tf1_s
    #0                        4498.5  4498.5  4498.5  4498.5              NaN
    #1                        4498.5  4498.5  4498.5  4498.5              NaN
    #2                        4498.5  4498.5  4498.5  4498.5              NaN
    #3                        4498.5  4498.5  4498.5  4498.5              NaN
    #4                        4498.5  4498.5  4498.5  4498.5           4498.5
    #indicator_tf1_s = 4498.5

    def calc_indicator_tf1_s(self):
        self.df_indicator_tf1_s = pd.DataFrame(self.data_tf1_s, columns=['close'])
        self.df_indicator_tf1_s['open'] = self.df_indicator_tf1_s['close']
        self.df_indicator_tf1_s['high'] = self.df_indicator_tf1_s['close']
        self.df_indicator_tf1_s['low'] = self.df_indicator_tf1_s['close']
        self.df_indicator_tf1_s['indicator_tf1_s'] = TA.WMA(self.df_indicator_tf1_s, self.mov_avg_length_tf1_s) # choose indicator here
        self.indicator_tf1_s = self.df_indicator_tf1_s['indicator_tf1_s'].iloc[-1]
        print("\nData_TF1_S =", self.data_tf1_s, "\n", "df_indicator_tf1_s =\n", self.df_indicator_tf1_s, "\n", "indicator_tf1_s =", self.indicator_tf1_s, "\n")
        return self.df_indicator_tf1_s

    def calc_prev_indicator_tf1_s(self):
        self.n += 1
        if self.n < self.mov_avg_length_tf1_s:
            return
        self.prev_indicator_tf1_s = self.indicator_tf1_s

    def calc_indicator_tf1_f(self):
        df_indicator_tf1_f = pd.DataFrame(self.data_tf1_f, columns=['close'])
        df_indicator_tf1_f['open'] = df_indicator_tf1_f['close']
        df_indicator_tf1_f['high'] = df_indicator_tf1_f['close']
        df_indicator_tf1_f['low'] = df_indicator_tf1_f['close']
        df_indicator_tf1_f['indicator_tf1_f'] = TA.HMA(df_indicator_tf1_f, self.mov_avg_length_tf1_f) # choose indicator here
        self.indicator_tf1_f = df_indicator_tf1_f['indicator_tf1_f'].iloc[-1]
        print("\nData_TF1_F =", self.data_tf1_f, "\n", "df_indicator_tf1_f =\n", df_indicator_tf1_f, "\n", "indicator_tf1_f =", self.indicator_tf1_f, "\n")

    def calc_prev_indicator_tf1_f(self):
        self.p += 1
        if self.p < self.mov_avg_length_tf1_f:
            return
        self.prev_indicator_tf1_f = self.indicator_tf1_f

    def calc_indicator_tf2_s(self):
        df_indicator_tf2_s = pd.DataFrame(self.data_tf2_s, columns=['close'])
        df_indicator_tf2_s['open'] = df_indicator_tf2_s['close']
        df_indicator_tf2_s['high'] = df_indicator_tf2_s['close']
        df_indicator_tf2_s['low'] = df_indicator_tf2_s['close']
        df_indicator_tf2_s['indicator_tf2_s'] = TA.WMA(df_indicator_tf2_s, self.mov_avg_length_tf2_s) # choose indicator here
        self.indicator_tf2_s = df_indicator_tf2_s['indicator_tf2_s'].iloc[-1]
        print("\nData_TF2_S =", self.data_tf2_s, "\n", "df_indicator_tf2_s =\n", df_indicator_tf2_s, "\n", "indicator_tf2_s =", self.indicator_tf2_s, "\n")

    def calc_prev_indicator_tf2_s(self):
        self.q += 1
        if self.q < self.mov_avg_length_tf2_s:
            return
        self.prev_indicator_tf2_s = self.indicator_tf2_s

    def calc_indicator_tf2_f(self):
        df_indicator_tf2_f = pd.DataFrame(self.data_tf2_f, columns=['close'])
        df_indicator_tf2_f['open'] = df_indicator_tf2_f['close']
        df_indicator_tf2_f['high'] = df_indicator_tf2_f['close']
        df_indicator_tf2_f['low'] = df_indicator_tf2_f['close']
        df_indicator_tf2_f['indicator_tf2_f'] = TA.HMA(df_indicator_tf2_f, self.mov_avg_length_tf2_f) # choose indicator here
        self.indicator_tf2_f = df_indicator_tf2_f['indicator_tf2_f'].iloc[-1]
        print("\nData_TF2_F =", self.data_tf2_f, "\n", "df_indicator_tf2_f =\n", df_indicator_tf2_f,"\n", "indicator_tf2_f =", self.indicator_tf2_f, "\n")

    def calc_prev_indicator_tf2_f(self):
        self.r += 1
        if self.r < self.mov_avg_length_tf2_f:
            return
        self.prev_indicator_tf2_f = self.indicator_tf2_f

    def decision_engine(self):
        if self.prev_indicator_tf1_s != 0:
            self.prev_signal = self.signal
            if self.prev_indicator_tf1_s < self.indicator_tf1_s:
                self.signal = 'LONG'
            elif self.prev_indicator_tf1_s > self.indicator_tf1_s:
                self.signal = 'SHORT'
            else:
                self.signal = self.prev_signal

    def decision_engine_tf1_tf2_enter(self):
        if self.prev_indicator_tf1_s != 0 and self.prev_indicator_tf2_f != 0:
            self.prev_signal = self.signal
            if self.prev_indicator_tf1_s < self.indicator_tf1_s:
                self.signal = 'LONG'
            elif self.prev_indicator_tf2_f > self.indicator_tf2_f:
                self.signal = 'SHORT'
            else:
                self.signal = self.prev_signal

    def decision_engine_tf1_tf2_exit(self):
        if self.prev_indicator_tf1_s != 0 and self.prev_indicator_tf2_f != 0:
            self.prev_signal = self.signal
            if self.prev_indicator_tf1_s < self.indicator_tf1_s:
                self.signal = 'LONG'
            elif self.prev_indicator_tf2_f > self.indicator_tf2_f:
                self.signal = 'SHORT'
            else:
                self.signal = self.prev_signal

    # (tf1_f) Fast is HMA & (tf1_s) Slow is WMA
    # (tf2_f) Fast is HMA & (tf2_s) Slow is WMA
    def decision_engine_crossover(self):
        if self.prev_indicator_tf1_s != 0 and self.prev_indicator_tf1_f != 0: # need to have atleast 2 signals (previous & current) to make a decision
            self.prev_signal = self.signal
            #If we are already SHORT, go LONG as soon as ROC > 00 to COVER (don't have to wait for crossover signal)
            if (self.prev_signal == "SHORT"):
                if (self.roc_tf1_s > 0) or (self.roc_tf1_f > 0) or (self.prev_indicator_tf1_s > self.prev_indicator_tf1_f) and (self.indicator_tf1_s < self.indicator_tf1_f):
                    self.signal = 'LONG'
                    print(f'\nGoing LONG because the following conditions were MET in decision engine\n'
                          f'    {self.roc_tf1_s} (roc_tf1_s) > 0 or {self.roc_tf1_f} (roc_tf1_f) > 0 or both conditions below\n'
                          f'    {self.prev_indicator_tf1_s} (prev_tf1_s) > {self.prev_indicator_tf1_f} (prev_tf1_f) and\n'
                          f'    {self.indicator_tf1_s} (tf1_s) < {self.indicator_tf1_f} (tf1_f) \n')
            #If we are already LONG, go SHORT as soon as ROC < 0 to CLOSE (don't have to wait for crossover signal)
            elif (self.prev_signal == "LONG"):
                if (self.roc_tf1_s < 0) or (self.roc_tf1_f < 0) or ((self.prev_indicator_tf1_s < self.prev_indicator_tf1_f) and (self.indicator_tf1_s > self.indicator_tf1_f)):
                    self.signal = "SHORT"
                    print(f'\nGoing SHORT because the following conditions were MET in decision engine\n'
                          f'    {self.roc_tf1_s} (roc_tf1_s) or {self.roc_tf1_f} (roc_tf1_f) or both conditions below\n'
                          f'    {self.prev_indicator_tf1_s} (prev_tf1_s) < {self.prev_indicator_tf1_f} (prev_tf_f) and\n'
                          f'    {self.indicator_tf1_s} (tf1_s) > {self.indicator_tf1_f} (tf1_f)\n)')
            # Only using ROC for long for now, need to figure out the short condition (if we can use ROC only)
            elif (self.roc_tf1_s > 0) and (self.roc_tf1_f > 0) and (self.prev_indicator_tf1_s > self.prev_indicator_tf1_f) and (self.indicator_tf1_s < self.indicator_tf1_f):
                self.signal = 'LONG'
                print(f'\nGoing LONG because the following conditions were MET in decision engine\n'
                      f'    {self.roc_tf1_s} (roc_tf1_s) > 0 and {self.roc_tf1_f} (roc_tf1_f) > 0 and both conditions below\n'
                      f'    {self.prev_indicator_tf1_s} (prev_tf1_s) > {self.prev_indicator_tf1_f} (prev_tf1_f) and\n'
                      f'    {self.indicator_tf1_s} (tf1_s) < {self.indicator_tf1_f} (tf1_f) \n')
            #Use crossover signal to start a SHORT position (only if we are not already LONG) Not using ROC to start a SHORT position (yet)
            elif ((self.prev_indicator_tf1_s < self.prev_indicator_tf1_f) and (self.indicator_tf1_s > self.indicator_tf1_f)):
                self.signal = 'SHORT'
                print(f'\nGoing SHORT because the following conditions were MET in decision engine\n' 
                      f'    {self.prev_indicator_tf1_s} (prev_tf1_s) < {self.prev_indicator_tf1_f} (prev_tf_f) and both conditions below\n'
                      f'    {self.indicator_tf1_s} (tf1_s) > {self.indicator_tf1_f} (tf1_f) \n'
                      f'    FYI: (not used in decision) {self.roc_tf1_s} (roc_tf1_s) or {self.roc_tf1_f} (roc_tf1_f)\n')
            else:
                self.signal = self.prev_signal

    # we are separating the entry and exit into 2 separate engines because we have to make a decision after each TF1 & TF2 candle is complete (which is not the same time)
    def decision_engine_crossover_tf1_tf2_enter(self):
        if self.prev_indicator_tf1_s != 0 and self.prev_indicator_tf1_f != 0 and self.prev_indicator_tf2_s != 0 and self.prev_indicator_tf2_f != 0: # need to have atleast 2 signals (previous & current) to make a decision
            self.prev_signal = self.signal
            if self.prev_indicator_tf1_s > self.prev_indicator_tf1_f and self.indicator_tf1_s < self.indicator_tf1_f:
                self.signal = 'LONG'
            elif self.prev_indicator_tf2_s < self.prev_indicator_tf2_f and self.indicator_tf2_s > self.indicator_tf2_f:
                self.signal = 'SHORT'
            else:
                self.signal = self.prev_signal

    def decision_engine_crossover_tf1_tf2_exit(self):
        if self.prev_indicator_tf1_s != 0 and self.prev_indicator_tf1_f != 0 and self.prev_indicator_tf2_s != 0 and self.prev_indicator_tf2_f != 0: # need to have atleast 2 signals (previous & current) to make a decision
            self.prev_signal = self.signal
            if self.prev_indicator_tf1_s > self.prev_indicator_tf1_f and self.indicator_tf1_s < self.indicator_tf1_f:
                self.signal = 'LONG'
            elif self.prev_indicator_tf2_s < self.prev_indicator_tf2_f and self.indicator_tf2_s > self.indicator_tf2_f:
                self.signal = 'SHORT'
            else:
                self.signal = self.prev_signal

    def create_order(self):
        if self.signal == self.prev_signal:
            print(f'\nStay in current \"{self.signal}\" position\n')
            return
        elif self.signal == 'LONG':
            self.send_order('BUY')
        elif self.signal == 'SHORT':
            self.send_order('SELL')
        else:
            print('\nWaiting for next order...\n')

    def send_order(self, action):
        order = Order()
        order.action = action
        order.totalQuantity = 1
        order.orderType = 'MKT'
        self.pending_order = True
        self.placeOrder(self.nextOrderId(), self.contract, order)
        print(f'\nSent a {order.action} order\n')
        #print(f'{self.prev_indicator_tf1_s} (prev_tf1_s) - {self.prev_indicator_tf1_f} (prev_tf1_f) - {self.indicator_tf1_s} (tf1_s) - {self.indicator_tf1_f} (tf1_f) ')
        #print(f'\n{self.prev_indicator_tf2_s} (prev_tf2_s) - {self.prev_indicator_tf1_f} (prev_tf2_f) - {self.indicator_tf1_s} (tf2_s) - {self.indicator_tf1_f} (tf2_f) \n')

    # run tick data (Heart of the Program)
    def tickDataOperations_req(self):
        # Create contract object

        # futures contract
        self.contract.symbol = 'ES'   #ES #TQQQ
        self.contract.secType = 'FUT'   #FUT #STK
        self.contract.exchange = 'GLOBEX'  #GLOBEX #SMART
        self.contract.currency = 'USD'
        self.contract.lastTradeDateOrContractMonth = "202109"

        # Request tick data
        self.reqTickByTickData(19002, self.contract, "AllLast", 0, False)

    # Receive tick data
    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                          size: int, tickAttribLast: TickAttribLast, exchange: str,
                          specialConditions: str):

        #now = datetime.now()
        #current_time = now.strftime("%H:%M:%S")
        #"Time: ", datetime.datetime.fromtimestamp(time).strftime(" % Y % m % d % H: % M: % S"),

        print("Time: ", datetime.datetime.fromtimestamp(time),
              "Current Signal:", self.signal,
              "Previous Signal:", self.prev_signal,
              "Current Price:", "{:.2f}\n".format(price),
              "TF1:", self.ticks_per_candle_tf1, "ticks per candle "
              "TF1_S (WMA):", self.mov_avg_length_tf1_s, "candles "
              "TF1_F (HMA):", self.mov_avg_length_tf1_f, "candles "
              "TF2:", self.ticks_per_candle_tf2, "ticks per candle "
              "TF2_S (WMA):", self.mov_avg_length_tf2_s, "candles "
              "TF2_F (HMA):", self.mov_avg_length_tf2_f,"candles \n",
              'Candle_TF1:', str(self.tick_count // self.ticks_per_candle_tf1+1).zfill(3),
              'Tick_TF1:', str(self.tick_count % self.ticks_per_candle_tf1 + 1).zfill(3), "of", str(self.ticks_per_candle_tf1).zfill(3),
              'ROC_TF1_S:', "{:.2f}".format(self.roc_tf1_s),
              'Ind_TF1_S:', "{:.2f}".format(self.indicator_tf1_s),
              'Prev_Ind_TF1_S:', "{:.2f}".format(self.prev_indicator_tf1_s),
              'ROC_TF1_F:', "{:.2f}".format(self.roc_tf1_f),
              'Ind_TF1_F:', "{:.2f}".format(self.indicator_tf1_f),
              'Prev_Ind_TF1_F:', "{:.2f}\n".format(self.prev_indicator_tf1_f),
              'Candle_TF2:', str(self.tick_count // self.ticks_per_candle_tf2 + 1).zfill(3),
              'Tick_TF2:', str(self.tick_count % self.ticks_per_candle_tf2 + 1).zfill(3), "of", str(self.ticks_per_candle_tf2).zfill(3),
              'ROC_TF2_S:', "{:.2f}".format(self.roc_tf2_s),
              'Ind_TF2_S:', "{:.2f}".format(self.indicator_tf2_s),
              'Prev_Ind_TF2_S:', "{:.2f}".format(self.prev_indicator_tf2_s),
              'ROC_TF2_F:', "{:.2f}".format(self.roc_tf2_f),
              'Ind_TF2_F:', "{:.2f}".format(self.indicator_tf2_f),
              'Prev_Ind_TF2_F:', "{:.2f}".format(self.prev_indicator_tf2_f)
        )

        # Checking to see if the TF1 candle is complete (remainder of tick_count & ticks_per_candle_tf1)
        if self.tick_count % self.ticks_per_candle_tf1 == self.ticks_per_candle_tf1 - 1:
            self.running_list_tf1_s(price)
            self.running_list_tf1_f(price)
            self.calc_prev_indicator_tf1_s()
            self.calc_cci_tf1_s()
            self.calc_indicator_tf1_s()
            self.calc_roc_tf1_s()
            self.calc_prev_indicator_tf1_f()
            self.calc_indicator_tf1_f()
            self.calc_roc_tf1_f()
            #self.decision_engine()
            self.decision_engine_crossover()
            #decision_engine_crossover_tf1_tf2_enter
            self.create_order()

        # Checking to see if the TF2 candle is complete (remainder of tick_count & ticks_per_candle_tf2)
        # When using both TF1 & TF2 for crossover, separate entry & exit into two separate decision_engines, and run them in parallel concurrently
        if self.tick_count % self.ticks_per_candle_tf2 == self.ticks_per_candle_tf2 - 1:
            self.running_list_tf2_s(price)
            self.running_list_tf2_f(price)
            self.calc_prev_indicator_tf2_s()
            self.calc_indicator_tf2_s()
            self.calc_roc_tf2_s()
            self.calc_prev_indicator_tf2_f()
            self.calc_indicator_tf2_f()
            self.calc_roc_tf2_f()
            #decision_engine_crossover_tf1_tf2_exit

        self.tick_count += 1

def main():
    app = TestApp()
    app.connect("127.0.0.1", port=7497, clientId=1011)  # make sure you have a different client id for each ticker
    print("serverVersion:%s connectionTime:%s" % (app.serverVersion(),app.twsConnectionTime()))
    app.run()

if __name__ == "__main__":
    main()