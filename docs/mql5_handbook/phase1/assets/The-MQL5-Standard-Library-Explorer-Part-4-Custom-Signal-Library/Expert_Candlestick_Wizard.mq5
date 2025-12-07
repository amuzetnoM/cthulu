//+------------------------------------------------------------------+
//|                                           Expert Candlestick Wizard.mq5 |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
//+------------------------------------------------------------------+
//| Include                                                          |
//+------------------------------------------------------------------+
#include <Expert\Expert.mqh>
//--- available signals
#include <Expert\Signal\SignalCandlePattern.mqh>
//--- available trailing
#include <Expert\Trailing\TrailingParabolicSAR.mqh>
//--- available money management
#include <Expert\Money\MoneySizeOptimized.mqh>
//+------------------------------------------------------------------+
//| Inputs                                                           |
//+------------------------------------------------------------------+
//--- inputs for expert
input string Expert_Title                      ="Candlestick Wizard"; // Document name
ulong        Expert_MagicNumber                =964602383;            //
bool         Expert_EveryTick                  =false;                //
//--- inputs for main signal
input int    Signal_ThresholdOpen              =10;                   // Signal threshold value to open [0...100]
input int    Signal_ThresholdClose             =10;                   // Signal threshold value to close [0...100]
input double Signal_PriceLevel                 =0.0;                  // Price level to execute a deal
input double Signal_StopLevel                  =50.0;                 // Stop Loss level (in points)
input double Signal_TakeLevel                  =50.0;                 // Take Profit level (in points)
input int    Signal_Expiration                 =4;                    // Expiration of pending orders (in bars)
input int    Signal_Candle_PatternDoji         =60;                   // Candlestick Patterns(60,80,...) Weight for Doji pattern
input int    Signal_Candle_PatternEngulfing    =80;                   // Candlestick Patterns(60,80,...) Weight for Engulfing pattern
input int    Signal_Candle_PatternHammer       =70;                   // Candlestick Patterns(60,80,...) Weight for Hammer pattern
input int    Signal_Candle_PatternMorningStar  =90;                   // Candlestick Patterns(60,80,...) Weight for Morning Star pattern
input double Signal_Candle_DojiThreshold       =0.1;                  // Candlestick Patterns(60,80,...) Doji body threshold (relative to range)
input double Signal_Candle_EngulfingRatio      =1.5;                  // Candlestick Patterns(60,80,...) Engulfing ratio (current body must be at least this times previ
input double Signal_Candle_Weight              =1.0;                  // Candlestick Patterns(60,80,...) Weight [0...1.0]
//--- inputs for trailing
input double Trailing_ParabolicSAR_Step        =0.02;                 // Speed increment
input double Trailing_ParabolicSAR_Maximum     =0.2;                  // Maximum rate
//--- inputs for money
input double Money_SizeOptimized_DecreaseFactor=3.0;                  // Decrease factor
input double Money_SizeOptimized_Percent       =10.0;                 // Percent
//+------------------------------------------------------------------+
//| Global expert object                                             |
//+------------------------------------------------------------------+
CExpert ExtExpert;
//+------------------------------------------------------------------+
//| Initialization function of the expert                            |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- Initializing expert
   if(!ExtExpert.Init(Symbol(),Period(),Expert_EveryTick,Expert_MagicNumber))
     {
      //--- failed
      printf(__FUNCTION__+": error initializing expert");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Creating signal
   CExpertSignal *signal=new CExpertSignal;
   if(signal==NULL)
     {
      //--- failed
      printf(__FUNCTION__+": error creating signal");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//---
   ExtExpert.InitSignal(signal);
   signal.ThresholdOpen(Signal_ThresholdOpen);
   signal.ThresholdClose(Signal_ThresholdClose);
   signal.PriceLevel(Signal_PriceLevel);
   signal.StopLevel(Signal_StopLevel);
   signal.TakeLevel(Signal_TakeLevel);
   signal.Expiration(Signal_Expiration);
//--- Creating filter CMyCandlePatternSignal
   CMyCandlePatternSignal *filter0=new CMyCandlePatternSignal;
   if(filter0==NULL)
     {
      //--- failed
      printf(__FUNCTION__+": error creating filter0");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
   signal.AddFilter(filter0);
//--- Set filter parameters
   filter0.PatternDoji(Signal_Candle_PatternDoji);
   filter0.PatternEngulfing(Signal_Candle_PatternEngulfing);
   filter0.PatternHammer(Signal_Candle_PatternHammer);
   filter0.PatternMorningStar(Signal_Candle_PatternMorningStar);
   filter0.DojiThreshold(Signal_Candle_DojiThreshold);
   filter0.EngulfingRatio(Signal_Candle_EngulfingRatio);
   filter0.Weight(Signal_Candle_Weight);
//--- Creation of trailing object
   CTrailingPSAR *trailing=new CTrailingPSAR;
   if(trailing==NULL)
     {
      //--- failed
      printf(__FUNCTION__+": error creating trailing");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Add trailing to expert (will be deleted automatically))
   if(!ExtExpert.InitTrailing(trailing))
     {
      //--- failed
      printf(__FUNCTION__+": error initializing trailing");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Set trailing parameters
   trailing.Step(Trailing_ParabolicSAR_Step);
   trailing.Maximum(Trailing_ParabolicSAR_Maximum);
//--- Creation of money object
   CMoneySizeOptimized *money=new CMoneySizeOptimized;
   if(money==NULL)
     {
      //--- failed
      printf(__FUNCTION__+": error creating money");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Add money to expert (will be deleted automatically))
   if(!ExtExpert.InitMoney(money))
     {
      //--- failed
      printf(__FUNCTION__+": error initializing money");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Set money parameters
   money.DecreaseFactor(Money_SizeOptimized_DecreaseFactor);
   money.Percent(Money_SizeOptimized_Percent);
//--- Check all trading objects parameters
   if(!ExtExpert.ValidationSettings())
     {
      //--- failed
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Tuning of all necessary indicators
   if(!ExtExpert.InitIndicators())
     {
      //--- failed
      printf(__FUNCTION__+": error initializing indicators");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- ok
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Deinitialization function of the expert                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   ExtExpert.Deinit();
  }
//+------------------------------------------------------------------+
//| "Tick" event handler function                                    |
//+------------------------------------------------------------------+
void OnTick()
  {
   ExtExpert.OnTick();
  }
//+------------------------------------------------------------------+
//| "Trade" event handler function                                   |
//+------------------------------------------------------------------+
void OnTrade()
  {
   ExtExpert.OnTrade();
  }
//+------------------------------------------------------------------+
//| "Timer" event handler function                                   |
//+------------------------------------------------------------------+
void OnTimer()
  {
   ExtExpert.OnTimer();
  }
//+------------------------------------------------------------------+