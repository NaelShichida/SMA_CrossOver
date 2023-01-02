from __future__ import (absolute_import, division, print_function,unicode_literals)
import backtrader as bt
from backtrader import Strategy
import pandas
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])


# Create a subclass of bt.Strategy to define the logic of the strategy
class MovingAverageCrossover(bt.Strategy):
    params = (('fast_sma', 10), ('slow_sma', 30))
    
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].close
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        self.fast_sma = bt.indicators.SimpleMovingAverage(self.data, period=self.p.fast_sma)
        self.slow_sma = bt.indicators.SimpleMovingAverage(self.data, period=self.p.slow_sma)
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

        # Write down: no pending order
        self.order = None
    def printTradeAnalysis(analyzer):
        '''
        Function to print the Technical Analysis results in a nice format.
        '''
        #Get the results we are interested in
        total_open = analyzer.total.open
        total_closed = analyzer.total.closed
        total_won = analyzer.won.total
        total_lost = analyzer.lost.total
        win_streak = analyzer.streak.won.longest
        lose_streak = analyzer.streak.lost.longest
        pnl_net = round(analyzer.pnl.net.total,2)
        strike_rate = (total_won / total_closed) * 100
        #Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Strike Rate','Win Streak', 'Losing Streak', 'PnL Net']
        r1 = [total_open, total_closed,total_won,total_lost]
        r2 = [strike_rate, win_streak, lose_streak, pnl_net]
        #Check which set of headers is the longest.
        if len(h1) > len(h2):
            header_length = len(h1)
        else:
            header_length = len(h2)
        #Print the rows
        print_list = [h1,r1,h2,r2]
        row_format ="{:<15}" * (header_length + 1)
        print("Trade Analysis Results:")
        for row in print_list:
            print(row_format.format('',*row))
            
    def printSQN(analyzer):
        sqn = round(analyzer.sqn,2)
        print('SQN: {}'.format(sqn))

    def next(self):
        
        self.log('Close, %.2f' % self.dataclose[0])
        if self.order:
            return
        
        if not self.position:
            # If there is no current position, check if a long entry signal has been generated
            if self.crossover > 0:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
                self.notify_order(self.order)

        else:
            # If there is a current position, check if a sell or cover signal has been generated
            if self.crossover < 0:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
                self.notify_order(self.order)


if __name__ == '__main__':
    # Create an instance of cerebro to run the strategy
    cerebro = bt.Cerebro()

    # Add the strategy to cerebro
    cerebro.addstrategy(MovingAverageCrossover)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")

    # Load the data
    data = bt.feeds.GenericCSVData(
        dataname='Assets/BTCUSD_Bitstamp_12h_2016.csv',
        fromdate=datetime.datetime(2017, 8, 1),
        todate=datetime.datetime(2018, 10, 30),
        dtformat='%Y-%m-%d %H:%M:%S',
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1
    )

    cerebro.adddata(data)
    print(type(data))

    # Set the starting cash
    cerebro.broker.setcash(100000.0)
    # Set the commission
    cerebro.broker.setcommission(commission=0.0)

    # Run the strategy
    # Run over everything
    strategies = cerebro.run()
    firstStrat = strategies[0]
    
    # print the analyzers
    printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
    printSQN(firstStrat.analyzers.sqn.get_analysis())

    #Get final portfolio Value
    portvalue = cerebro.broker.getvalue()

    # Plot the results
    cerebro.plot()
