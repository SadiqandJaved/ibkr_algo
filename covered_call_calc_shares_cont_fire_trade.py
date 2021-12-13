import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
# types
from ibapi.contract import * # @UnusedWildImport
from ibapi.order import Order
from ibapi.common import *  # @UnusedWildImport
from ibapi.ticktype import * # @UnusedWildImport
# other packages
from datetime import datetime
import math
import pause

class TestApp(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)

        # this is for trading
        self.nextValidOrderId = None
        self.permId2ord = {}

        # this is for calcs of share and contracts
        self.contract = Contract()
        self.CallContract = Contract()
        self.data_px = []
        self.data = []
        self.df_px = pd.DataFrame()
        self.df = pd.DataFrame()
        self.cash_value = 0
        self.recent_px = 0
        self.shares_to_buy = 0
        self.num_contracts = 0

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

    def tickDataOperations_req(self):
        self.contract.symbol = 'QQQ'
        self.contract.secType = 'STK'
        self.contract.exchange = 'SMART'
        self.contract.currency = 'USD'
        # self.contract.lastTradeDateOrContractMonth = "202112"

        self.reqMktData(1002, self.contract, "", True, False, [])

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float,
                  attrib: TickAttrib):
        super().tickPrice(reqId, tickType, price, attrib)
        # print("TickPrice. TickerId:", reqId, "tickType:", tickType,
        #       "Price:", price, "CanAutoExecute:", attrib.canAutoExecute,
        #       "PastLimit:", attrib.pastLimit, end=' ')
        self.data_px.append([tickType, price])
        self.df_px = pd.DataFrame(self.data_px, columns=['TickType', 'Price'])

    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        super().tickSize(reqId, tickType, size)
        # print("TickSize. TickerId:", reqId, "TickType:", tickType, "Size:", size)

    def tickSnapshotEnd(self, reqId: int):
        super().tickSnapshotEnd(reqId)
        print("TickSnapshotEnd. TickerId:", reqId)
        self.get_px()

    def get_px(self):
        print(self.df_px)
        self.recent_px = self.df_px.loc[self.df_px['TickType'] == 4, 'Price'].iloc[0]
        print(f'recent price: {self.recent_px}')
        self.accountOperations_req()

    def accountOperations_req(self):
        # Requesting accounts' summary
        # ! [reqaaccountsummary]
        self.reqAccountSummary(9002, "All", "$LEDGER")
        # ! [reqaaccountsummary]

        # ! [accountsummary]

    def accountSummary(self, reqId: int, account: str, tag: str, value: str,
                       currency: str):
        super().accountSummary(reqId, account, tag, value, currency)
        # print("AccountSummary. ReqId:", reqId, "Account:", account,
        #       "Tag: ", tag, "Value:", value, "Currency:", currency)
        self.data.append([tag, value])
        self.df = pd.DataFrame(self.data, columns=['Account', 'Value'])

    def accountSummaryEnd(self, reqId: int):
        super().accountSummaryEnd(reqId)
        print("AccountSummaryEnd. ReqId:", reqId)
        self.get_cash()

    def get_cash(self):
        print(self.df)
        self.df.to_csv('acct_value.csv')
        self.cash_value = self.df.loc[self.df['Account'] == 'CashBalance', 'Value'].iloc[0]
        print(f'cash value: {self.cash_value}')
        self.calc_contracts()

    def calc_contracts(self):
        num_shares = float(self.cash_value) / (self.recent_px) # get rid of  / 100
        safety_num_shares = 0.10 * num_shares # this is percentage of cash
        self.shares_to_buy = math.floor(safety_num_shares / 100) * 100
        print(f'shares to buy: {self.shares_to_buy}')
        self.num_contracts = self.shares_to_buy / 100
        print(f'number of contracts: {self.num_contracts}')
        self.check_and_send_order()

    def sendOrder(self, action):
        order = Order()
        order.action = action
        order.totalQuantity = self.shares_to_buy
        order.orderType = "MKT"
        self.placeOrder(self.nextOrderId(), self.contract, order)

    def sendCallOrder(self, action):
        self.CallContract.symbol = 'QQQ'
        self.CallContract.secType = 'OPT'
        self.CallContract.exchange = 'SMART'
        self.CallContract.currency = 'USD'
        self.CallContract.lastTradeDateOrContractMonth = "20211217"
        self.CallContract.strike = 395
        self.CallContract.right = "C"
        self.CallContract.multiplier = "100"

        order = Order()
        order.action = action
        order.totalQuantity = self.num_contracts
        order.orderType = "MKT"
        self.placeOrder(self.nextOrderId(), self.CallContract, order)

    def check_and_send_order(self):
        pause.until(datetime(2021, 12, 13, 11, 20, 0))  # this is the time at which you can buy shares
        self.sendOrder('BUY')
        pause.until(datetime(2021, 12, 13, 11, 20, 15))
        self.sendCallOrder('SELL')

        self.disconnect()

def main():
    app = TestApp()
    app.connect("127.0.0.1", port=7497, clientId=102)
    print("serverVersion:%s connectionTime:%s" % (app.serverVersion(),app.twsConnectionTime()))
    app.run()

if __name__ == "__main__":
    main()