//+------------------------------------------------------------------+
//|                                  Wamek_BuySellOrders.mq5         |
//|                        Copyright 2023, MetaQuotes Software Corp. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Wamek Script-2025"
#property link      "eawamek@gmail.com"
#property version   "2.00"
#property script_show_inputs

#include <Trade/Trade.mqh>

//--- order direction enum
enum TradeType
  {
   BUY=0,
   SELL=1
  };

//--- input parameters
input TradeType Trade_Direction = BUY;
input double    Lots            = 0.01;
input int       StopLoss        = 200;   // StopLoss
input double    RRR             = 2.0;   // reward risk ratio
input double    Rstep           = 0.2;   // incremental step
input int       Num_Of_Orders   = 1;

int              MagicNum        = 874;

CTrade trade;

//+------------------------------------------------------------------+
//| Script start                                                     |
//+------------------------------------------------------------------+
void OnStart()
  {
   if(TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
     {
      string dir = (Trade_Direction==BUY) ? "buy" : "sell";
      int pick = MessageBox("You are about to open " +
                            IntegerToString(Num_Of_Orders,0) + 
                            " " + dir + " order(s)\n",
                            "Confirm Orders", MB_OKCANCEL);

      if(pick==IDOK)
        {
         // Configure trade settings
         trade.SetExpertMagicNumber(MagicNum);
         trade.SetDeviationInPoints(3);
         
         for(int i=0; i<Num_Of_Orders; i++)
            place_order(i);
        }
     }
   else
      MessageBox("Enable AutoTrading Please ");
  }

//+------------------------------------------------------------------+
//| Place order using CTrade                                         |
//+------------------------------------------------------------------+
void place_order(int i)
  {
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double sl_points = StopLoss * point;
   double tp_points = StopLoss * (RRR + i * Rstep) * point;
   
   if(Trade_Direction==BUY)
     {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double stoplosslevel = (StopLoss > 0) ? ask - sl_points : 0;
      double takeprofitlevel = (RRR > 0) ? ask + tp_points : 0;

      trade.PositionOpen(_Symbol, ORDER_TYPE_BUY, Lots, ask, 
                         stoplosslevel, takeprofitlevel, "Wamek");
     }
   else if(Trade_Direction==SELL)
     {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double stoplosslevel = (StopLoss > 0) ? bid + sl_points : 0;
      double takeprofitlevel = (RRR > 0) ? bid - tp_points : 0;

      trade.PositionOpen(_Symbol, ORDER_TYPE_SELL, Lots, bid, 
                         stoplosslevel, takeprofitlevel, "Wamek");
     }

   if(trade.ResultRetcode() != TRADE_RETCODE_DONE)
      Alert("OrderSend failed with retcode: ", trade.ResultRetcode(), 
            ", error: ", trade.ResultRetcodeDescription());
  }
//+------------------------------------------------------------------+