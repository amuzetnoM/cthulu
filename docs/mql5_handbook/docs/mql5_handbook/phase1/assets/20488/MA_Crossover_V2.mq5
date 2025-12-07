//+------------------------------------------------------------------+
//|                                              MA Crossover V1.mq5 |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"

//+------------------------------------------------------------------+
//| Technical Indicators                                             |
//+------------------------------------------------------------------+
int      ma_fast_handler,ma_slow_handler,atr_handler;
double   ma_fast_reading[],ma_slow_reading[],atr_reading[];

//+------------------------------------------------------------------+
//| Global variables                                                 |
//+------------------------------------------------------------------+
double ask,bid;

//+------------------------------------------------------------------+
//| Libraries                                                        |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>
CTrade Trade;


//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- Setup our indicators
   ma_fast_handler = iMA("EURUSD",PERIOD_D1,30,0,MODE_SMA,PRICE_CLOSE);
   ma_slow_handler = iMA("EURUSD",PERIOD_D1,60,0,MODE_SMA,PRICE_CLOSE);
   atr_handler     = iATR("EURUSD",PERIOD_D1,14);
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//--- Free up memory we are no longer using when the application is off
   IndicatorRelease(ma_fast_handler);
   IndicatorRelease(ma_slow_handler);
   IndicatorRelease(atr_handler);
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//--- When price levels change

   datetime current_time = iTime("EURUSD",PERIOD_D1,0);
   static datetime  time_stamp;

//--- Update the time
   if(current_time != time_stamp)
     {
      time_stamp = current_time;

      //--- Fetch indicator current readings
      CopyBuffer(ma_fast_handler,0,0,1,ma_fast_reading);
      CopyBuffer(ma_slow_handler,0,0,1,ma_slow_reading);
      CopyBuffer(atr_handler,0,0,1,atr_reading);
      double close = iClose("EURUSD",PERIOD_D1,0);
      double high = iHigh("EURUSD",PERIOD_D1,0);
      double low = iLow("EURUSD",PERIOD_D1,0);

      ask = SymbolInfoDouble("EURUSD",SYMBOL_ASK);
      bid = SymbolInfoDouble("EURUSD",SYMBOL_BID);

      //--- If we have no open positions
      if(PositionsTotal() == 0)
        {
         //--- Trading rules
         if((ma_fast_reading[0] > ma_slow_reading[0]) && (low > ma_fast_reading[0]))
           {
            //--- Buy signal
            Trade.Buy(0.01,"EURUSD",ask,ask-(atr_reading[0] * 2),ask+(atr_reading[0] * 2),"");
           }

         else
            if((ma_fast_reading[0] < ma_slow_reading[0]) && (high < ma_slow_reading[0]))
              {
               //--- Sell signal
               Trade.Sell(0.01,"EURUSD",bid,bid+(atr_reading[0] * 2),bid-(atr_reading[0] * 2),"");
              }
        }

     }

  }
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
