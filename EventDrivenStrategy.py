import calendar
import pandas as pd
import io
import datetime


class EventDrivenStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2008, 1, 1)  # Set Start Date
        # self.SetEndDate(2009, 2, 25)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        self.AddEquity("SPY", Resolution.Minute)
        self.AddEquity("TLT", Resolution.Minute)
        
        self.buySPY = 0
        self.sellSPY = 0
        self.buyTLT = 0
        self.sellTLT = 0
    
        file = self.Download("https://raw.githubusercontent.com/Quant-Invest/public-data/master/treasury-auction-dates.csv")
        self.auction_df = pd.read_csv(io.StringIO(file))
        self.auction_df['Auction_Date'] = pd.to_datetime(self.auction_df['Auction_Date'])
        

        # self.auction_df = pd.read_csv("https://raw.githubusercontent.com/Quant-Invest/public-data/master/treasury-auction-dates.csv")
        
        # self.Schedule.On(self.DateRules.EveryDay("SPY"), self.TimeRules.BeforeMarketClose("SPY", 5), self.BuySPYLastDay) 
        # self.Schedule.On(self.DateRules.EveryDay("SPY"), self.TimeRules.BeforeMarketClose("SPY", 5), self.SellSPYFirstDay)
        
        # End of month effect
        self.Schedule.On(self.DateRules.EveryDay("TLT"), self.TimeRules.BeforeMarketClose("TLT", 5), self.BuyTLTTwoDaysBeforeLastDay) 
        self.Schedule.On(self.DateRules.EveryDay("TLT"), self.TimeRules.BeforeMarketClose("TLT", 5), self.SellTLTLastDay)
        
        # Auction Day Effect
        self.Schedule.On(self.DateRules.EveryDay("TLT"), self.TimeRules.BeforeMarketClose("TLT", 5), self.BuyTLTTwoDaysBeforeAuctionDay) 
        self.Schedule.On(self.DateRules.EveryDay("TLT"), self.TimeRules.BeforeMarketClose("TLT", 5), self.SellTLTAfterAuctionDay)

    def OnData(self, data):
        '''OnData event is the primary entry point for your algorithm. Each new data point will be pumped in here.
            Arguments:
                data: Slice object keyed by symbol containing the stock data
        '''

        # if not self.Portfolio["SPY"].Invested and self.buySPY > 0:
        #     self.SetHoldings("SPY", 1)
        #     self.buySPY = 0
        # elif self.Portfolio["SPY"].Invested and self.sellSPY > 0:
        #     self.SetHoldings("SPY", 0)
        #     self.sellSPY = 0
        if not self.Portfolio["TLT"].Invested and self.buyTLT > 0:
            self.SetHoldings("TLT", 2)
            self.buyTLT = 0
            self.sellTLT = 0
        elif self.Portfolio["TLT"].Invested and self.sellTLT > 0:
            self.SetHoldings("TLT", 0)
            self.sellTLT = 0
            self.buyTLT = 0
        
    def BuySPYLastDay(self):
        if self.Time.date() == self.GetLastTradingDay():
            self.buySPY = 1
    
    def SellSPYFirstDay(self):
        if self.Time.date() == self.GetFirstTradingDay():
            self.sellSPY = 1
        
    def BuyTLTTwoDaysBeforeLastDay(self):
        if self.Time.date() == self.GetLastButTwoTradingDay():
            self.buyTLT = 1
    
    def SellTLTLastDay(self):
        if self.Time.date() == self.GetLastTradingDay():
            self.sellTLT = 1
            
    def BuyTLTTwoDaysBeforeAuctionDay(self):
        if self.IsNextAuctionDayComingUp():
            self.buyTLT = 1
    
    def SellTLTAfterAuctionDay(self):
        if self.IsAuctionDayPassed():
            self.sellTLT = 1
        
    def GetLastTradingDay(self):
        month_last_day = DateTime(self.Time.year, self.Time.month, DateTime.DaysInMonth(self.Time.year, self.Time.month))
        trading_days = list(self.TradingCalendar.GetDaysByType(TradingDayType.BusinessDay, self.Time, month_last_day))
        if len(trading_days) >= 1:
            return trading_days[len(trading_days)-1].Date.date()     
        else:
            return None    
            
    def GetLastButTwoTradingDay(self):
        month_last_day = DateTime(self.Time.year, self.Time.month, DateTime.DaysInMonth(self.Time.year, self.Time.month))
        trading_days = list(self.TradingCalendar.GetDaysByType(TradingDayType.BusinessDay, self.Time, month_last_day))
        if len(trading_days) >= 3:
            return trading_days[len(trading_days)-3].Date.date()
        else:
            return None
            
    def GetFirstTradingDay(self):
        trading_days = list(self.TradingCalendar.GetDaysByType(TradingDayType.BusinessDay, 1, self.Time))
        return trading_days[0].Date.date()
        
    def IsNextAuctionDayComingUp(self):
        df = self.auction_df
        start_date = None
        end_date = None
        if self.Time.weekday() == 4:
            start_date = df['Auction_Date'] > self.Time.date()
            end_date = df['Auction_Date'] <= (self.Time.date() + datetime.timedelta(days=3))
        else:
            start_date = df['Auction_Date'] > self.Time.date()
            end_date = df['Auction_Date'] <= (self.Time.date() + datetime.timedelta(days=1))
        
        mask = start_date & end_date
        df = df.loc[mask]
        if len(df) > 0:
            return True
        else:
            return False
    
    def IsAuctionDayPassed(self):
        df = self.auction_df
        start_date = None
        end_date = None
        trading_days = []
        i = -1
        while len(trading_days) < 3:
            i = i + 1
            trading_days = list(self.TradingCalendar.GetDaysByType(TradingDayType.BusinessDay, self.Time - datetime.timedelta(days=3+i), self.Time))    
                
        start_date = df['Auction_Date'] >= trading_days[0].Date.date()
        end_date = df['Auction_Date'] < trading_days[1].Date.date()
        mask = start_date & end_date
        df = df.loc[mask]
        if len(df) > 0:
            return True
        else:
            return False
