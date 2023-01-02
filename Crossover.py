import backtrader as bt
from datetime import datetime
from collections import OrderedDict
import matplotlib
matplotlib.use('Agg')

# Create a subclass of bt.Strategy to define the logic of the strategy
class firstStrategy(bt.Strategy):
    params = (('fast_sma', 10), ('slow_sma', 30))

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # Initialise first_trade to True
        self.first_trade = True
        
        self.fast_sma = bt.indicators.SimpleMovingAverage(self.data, period=self.p.fast_sma)
        self.slow_sma = bt.indicators.SimpleMovingAverage(self.data, period=self.p.slow_sma)
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

    def next(self):
        # self.log('Crossover, %.2f' % self.crossover)        
        # if self.order:
        #     return

        # if self.first_trade and not self.position:
        #     # If there is no current position, check if a long entry signal has been generated
        if self.crossover > 0:
                self.close()
                self.log('BUY CREATE, %.2f' % self.data.close[0]) #This is currently the right price to be buying at, however self.buy below is not
                print(self.position)

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(price=self.data.close[0])
                print("test")

        # else:
        #     # If there is a current position, check if a sell or cover signal has been generated
        elif self.crossover < 0:
                self.close()
                self.log('SELL CREATE, %.2f' % self.data.close[0])
                print(self.position)
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(price=self.data.close[0])
                print("test")
                print(self.order.status)



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

#Variable for our starting cash
startcash = 100000

#Create an instance of cerebro
cerebro = bt.Cerebro(cheat_on_open=True)

#Add our strategy
cerebro.addstrategy(firstStrategy)

# Load the data
data = bt.feeds.GenericCSVData(
    dataname='Assets/BTCUSD_Bitstamp_12h_2016.csv',
    fromdate=datetime(2017, 1, 1),
    todate=datetime(2018, 1, 1),
    dtformat='%Y-%m-%d %H:%M:%S',
    datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=5,
    openinterest=-1
)

#Add the data to Cerebro
cerebro.adddata(data)

# Set our desired cash start
cerebro.broker.setcash(startcash)

# Add the analyzers we are interested in
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

# Run over everything
strategies = cerebro.run()
firstStrat = strategies[0]

# print the analyzers
printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
printSQN(firstStrat.analyzers.sqn.get_analysis())

#Get final portfolio Value
portvalue = cerebro.broker.getvalue()

#Print out the final result
print('Final Portfolio Value: ${}'.format(portvalue))

#Finally plot the end results
cerebro.plot(style='candlestick')