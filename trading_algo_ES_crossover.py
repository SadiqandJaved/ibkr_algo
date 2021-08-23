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

TICKS_PER_CANDLE_TF1 = 144 #10 #144
MOVING_AVG_PERIOD_LENGTH_TF1_S = 14 #9 #14 # slow timeframe (WMA)
MOVING_AVG_PERIOD_LENGTH_TF1_F = 9 #5 #9 # fast timeframe (EMA)
TICKS_PER_CANDLE_TF2 = 89 #5 #89
MOVING_AVG_PERIOD_LENGTH_TF2_S = 9 #9 #14 (WMA)
MOVING_AVG_PERIOD_LENGTH_TF2_F = 5 #5 #9 (EMA) (TA.HMA was not updating, showing nan)

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

    def running_list_tf1_s(self, price: float):
        self.data_tf1_s.append(price)
        self.data_counter_tf1_s += 1
        if self.data_counter_tf1_s < self.mov_avg_length_tf1_s:
            return
        while len(self.data_tf1_s) > self.mov_avg_length_tf1_s:
            self.data_tf1_s.pop(0)

    def running_list_tf1_f(self, price: float):
        self.data_tf1_f.append(price)
        self.data_counter_tf1_f += 1
        if self.data_counter_tf1_f < self.mov_avg_length_tf1_f:
            return
        while len(self.data_tf1_f) > self.mov_avg_length_tf1_f:
            self.data_tf1_f.pop(0)

    def running_list_tf2_s(self, price: float):
        self.data_tf2_s.append(price)
        self.data_counter_tf2_s += 1
        if self.data_counter_tf2_s < self.mov_avg_length_tf2_s:
            return
        while len(self.data_tf2_s) > self.mov_avg_length_tf2_s:
            self.data_tf2_s.pop(0)

    def running_list_tf2_f(self, price: float):
        self.data_tf2_f.append(price)
        self.data_counter_tf2_f += 1
        if self.data_counter_tf2_f < self.mov_avg_length_tf2_f:
            return
        while len(self.data_tf2_f) > self.mov_avg_length_tf2_f:
            self.data_tf2_f.pop(0)

    def calc_indicator_tf1_s(self):
        df_indicator_tf1_s = pd.DataFrame(self.data_tf1_s, columns=['close'])
        df_indicator_tf1_s['open'] = df_indicator_tf1_s['close']
        df_indicator_tf1_s['high'] = df_indicator_tf1_s['close']
        df_indicator_tf1_s['low'] = df_indicator_tf1_s['close']
        df_indicator_tf1_s['indicator'] = TA.WMA(df_indicator_tf1_s, self.mov_avg_length_tf1_s) # choose indicator here
        self.indicator_tf1_s = df_indicator_tf1_s['indicator'].iloc[-1]

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
        df_indicator_tf1_f['indicator1'] = TA.EMA(df_indicator_tf1_f, self.mov_avg_length_tf1_f) # choose indicator here
        self.indicator_tf1_f = df_indicator_tf1_f['indicator1'].iloc[-1]

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
        df_indicator_tf2_s['indicator_a'] = TA.WMA(df_indicator_tf2_s, self.mov_avg_length_tf2_s) # choose indicator here
        self.indicator_tf2_s = df_indicator_tf2_s['indicator_a'].iloc[-1]

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
        df_indicator_tf2_f['indicator_a1'] = TA.EMA(df_indicator_tf2_f, self.mov_avg_length_tf2_f) # choose indicator here
        self.indicator_tf2_f = df_indicator_tf2_f['indicator_a1'].iloc[-1]

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

    # TA.HMA was not working, so using TA.EMA instead
    # (tf1_f) Fast is HMA & (tf1_s) Slow is WMA
    # (tf2_f) Fast is HMA & (tf2_s) Slow is WMA
    def decision_engine_crossover(self):
        if self.prev_indicator_tf1_s != 0 and self.prev_indicator_tf1_f != 0: # need to have atleast 2 signals (previous & current) to make a decision
            self.prev_signal = self.signal
            if self.prev_indicator_tf1_s > self.prev_indicator_tf1_f and self.indicator_tf1_s < self.indicator_tf1_f:
                self.signal = 'LONG'
                print(f'\nGoing LONG because {self.prev_indicator_tf1_s} (prev_tf1_s) > {self.prev_indicator_tf1_f} (prev_tf1_f) and {self.indicator_tf1_s} (tf1_s) < {self.indicator_tf1_f} (tf1_f) \n')
            elif self.prev_indicator_tf1_s < self.prev_indicator_tf1_f and self.indicator_tf1_s > self.indicator_tf1_f:
                self.signal = 'SHORT'
                print(f'\nGoing SHORT because {self.prev_indicator_tf1_s} (prev_tf1_s) < {self.prev_indicator_tf1_f} (prev_tf_f) and {self.indicator_tf1_s} (tf1_s) > {self.indicator_tf1_f} (tf1_f) \n')
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
            print('\nStay in current position\n')
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
        self.contract.symbol = 'ES'
        self.contract.secType = 'FUT'
        self.contract.exchange = 'GLOBEX'
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
              'Candle_TF1:', str(self.tick_count // self.ticks_per_candle_tf1+1).zfill(3),
              'Tick_TF1:', str(self.tick_count % self.ticks_per_candle_tf1 + 1).zfill(3),
              'Ind_TF1_S:', "{:.2f}".format(self.indicator_tf1_s),
              'Prev_Ind_TF1_S:', "{:.2f}".format(self.prev_indicator_tf1_s),
              'Ind_TF1_F:', "{:.2f}".format(self.indicator_tf1_f),
              'Prev_Ind_TF1_F:', "{:.2f}\n".format(self.prev_indicator_tf1_f),
              'Candle_TF2:', str(self.tick_count // self.ticks_per_candle_tf2 + 1).zfill(3),
              'Tick_TF2:', str(self.tick_count % self.ticks_per_candle_tf2 + 1).zfill(3),
              'Ind_TF2_S:', "{:.2f}".format(self.indicator_tf2_s),
              'Prev_Ind_TF2_S:', "{:.2f}".format(self.prev_indicator_tf2_s),
              'Ind_TF2_F:', "{:.2f}".format(self.indicator_tf2_f),
              'Prev_Ind_TF2_F:', "{:.2f}".format(self.prev_indicator_tf2_f)
        )

        # Checking to see if the TF1 candle is complete (remainder of tick_count & ticks_per_candle_tf1)
        if self.tick_count % self.ticks_per_candle_tf1 == self.ticks_per_candle_tf1 - 1:
            self.running_list_tf1_s(price)
            self.running_list_tf1_f(price)
            self.calc_prev_indicator_tf1_s()
            self.calc_indicator_tf1_s()
            self.calc_prev_indicator_tf1_f()
            self.calc_indicator_tf1_f()
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
            self.calc_prev_indicator_tf2_f()
            self.calc_indicator_tf2_f()
            #decision_engine_crossover_tf1_tf2_exit

        self.tick_count += 1

def main():
    app = TestApp()
    app.connect("127.0.0.1", port=7497, clientId=101)  # make sure you have a different client id for each ticker
    print("serverVersion:%s connectionTime:%s" % (app.serverVersion(),app.twsConnectionTime()))
    app.run()

if __name__ == "__main__":
    main()