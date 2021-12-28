import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import * # @UnusedWildImport
from ibapi.common import *  # @UnusedWildImport
from ibapi.ticktype import * # @UnusedWildImport

# available tick types
# https://interactivebrokers.github.io/tws-api/tick_types.html
# https://cmdlinetips.com/2018/01/how-to-create-pandas-dataframe-from-multiple-lists/

class TestApp(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.contract = Contract()
        self.contract1 = Contract()
        self.underlying = Contract()
        self.data = []
        self.data1 = []
        self.data_counter = 0
        self.data1_counter = 0
        self.dict = {}
        self.df = pd.DataFrame()
        self.tick1 = 3004   # strike 1 bid
        self.tick2 = 3005   # strike 1 ask
        self.tick3 = 3006   # strike 2 bid
        self.tick4 = 3007   # strike 2 ask
        self.tick5 = 3008   # underlying trade
        self.strike1_bid = 0
        self.strike1_ask = 0
        self.strike2_bid = 0
        self.strike2_ask = 0
        self.strike1_mid = 0
        self.strike2_mid = 0
        self.underlying_px = 0
        self.roll_diff = 0
        self.strike1_intrinsic = 0
        self.strike2_intrinsic = 0
        self.strike1_extrinsic = 0
        self.strike2_extrinsic = 0

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

    def start(self):
        self.tickDataOperations_req()
        print("Executing requests ... finished")

    def assign_variables(self, reqId, close: float):
        if reqId == self.tick1:
            self.strike1_bid = close
        elif reqId == self.tick2:
            self.strike1_ask = close
        elif reqId == self.tick3:
            self.strike2_bid = close
        elif reqId == self.tick4:
            self.strike2_ask = close
        elif reqId == self.tick5:
            self.underlying_px = close
        else:
            print("Error")

    def calculate_mid_px(self):
        self.strike1_mid = (self.strike1_bid + self.strike1_ask) / 2
        self.strike2_mid = (self.strike2_bid + self.strike2_ask) / 2

    def calculate_intrinsic(self):
        self.strike1_intrinsic = max((self.underlying_px - self.contract.strike), 0)
        self.strike2_intrinsic = max((self.underlying_px - self.contract1.strike), 0)

    def calculate_extrinsic(self):
        self.strike1_extrinsic = self.strike1_mid - self.strike1_intrinsic
        self.strike2_extrinsic = self.strike2_mid - self.strike2_intrinsic

    def calculate_roll_diff(self):
        self.roll_diff = self.strike2_extrinsic - self.strike1_extrinsic

    def tickDataOperations_req(self):
        # self.contract.symbol = 'NQ'
        # self.contract.secType = 'FUT'
        # self.contract.exchange = 'GLOBEX'
        # self.contract.currency = 'USD'
        # self.contract.lastTradeDateOrContractMonth = "202112"

        self.underlying.symbol = 'TQQQ'
        self.underlying.secType = 'STK'
        self.underlying.exchange = 'SMART'
        self.underlying.currency = 'USD'

        self.contract.symbol = 'TQQQ'
        self.contract.secType = 'OPT'
        self.contract.exchange = 'SMART'
        self.contract.currency = 'USD'
        self.contract.lastTradeDateOrContractMonth = '20211217'
        self.contract.strike = 154
        self.contract.right = "C"
        self.contract.multiplier = "100"

        self.contract1.symbol = 'TQQQ'
        self.contract1.secType = 'OPT'
        self.contract1.exchange = 'SMART'
        self.contract1.currency = 'USD'
        self.contract1.lastTradeDateOrContractMonth = '20211223'
        self.contract1.strike = 154
        self.contract1.right = "C"
        self.contract1.multiplier = "100"

        self.reqRealTimeBars(self.tick1, self.contract, 5, "BID", False, []) # False for after-hours and True for market hours
        self.reqRealTimeBars(self.tick2, self.contract, 5, "ASK", False,[])  # False for after-hours and True for market hours
        self.reqRealTimeBars(self.tick3, self.contract1, 5, "BID", False, []) # False for after-hours and True for market hours
        self.reqRealTimeBars(self.tick4, self.contract1, 5, "ASK", False, [])  # False for after-hours and True for market hours
        self.reqRealTimeBars(self.tick5, self.underlying, 5, "TRADES", False, [])  # False for after-hours and True for market hours

    def realtimeBar(self, reqId: TickerId, time: int, open_: float, high: float, low: float, close: float,
                    volume: int, wap: float, count: int):
        super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        # print("RealTimeBar. TickerId:", reqId, RealTimeBar(time, -1, open_, high, low, close, volume, wap, count), self.data1, self.data, self.dict)
        # print("RealTimeBar. TickerId:", reqId, RealTimeBar(time, -1, open_, high, low, close, volume, wap, count),
        #       f'NQ_bid: {self.NQ_bid} NQ_ask: {self.NQ_ask} ES_bid: {self.ES_bid} ES_ask: {self.ES_ask}' )
        print("TickerId:", reqId,
              f'TQQQ: {self.underlying_px} roll: {self.roll_diff:.2f} strk1_ext: {self.strike1_extrinsic:.2f} strk2_ext: {self.strike2_extrinsic:.2f} strk1_int: {self.strike1_intrinsic:.2f} strk2_int: {self.strike2_intrinsic:.2f} strike1_mid: {self.strike1_mid:.2f} strike2_mid: {self.strike2_mid:.2f} strike1_bid: {self.strike1_bid:.2f} strike1_ask: {self.strike1_ask:.2f} strike2_bid: {self.strike2_bid:.2f} strike2_ask: {self.strike2_ask:.2f}')

        self.assign_variables(reqId, close)
        self.calculate_mid_px()
        self.calculate_intrinsic()
        self.calculate_extrinsic()
        self.calculate_roll_diff()

    # ! [realtimebar]

def main():
    app = TestApp()
    app.connect("127.0.0.1", port=7497, clientId=103)
    print("serverVersion:%s connectionTime:%s" % (app.serverVersion(),app.twsConnectionTime()))
    app.run()

if __name__ == "__main__":
    main()