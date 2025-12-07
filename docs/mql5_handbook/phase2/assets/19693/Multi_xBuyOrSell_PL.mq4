//+------------------------------------------------------------------+
//|                                  Wamek_BuySellOrders.mq4         |
//|                        Copyright 2023, MetaQuotes Software Corp. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Wamek Script-2025"
#property link      "eawamek@gmail.com"
#property version   "2.00"
#property strict
#property script_show_inputs

//--- order direction enum
enum TradeType
  {
   BUY=0,
   SELL=1
  };

//--- input parameters
extern TradeType Trade_Direction = BUY;
extern double    Lots            = 0.01;
extern int       StopLoss        = 200;   // StopLoss
extern double    RRR             = 2.0;   //  reward risk ratio
extern double    Rstep           = 0.2;   // incremental step
extern int       Num_Of_Orders   = 1;

int              MagicNum        = 874;

//+------------------------------------------------------------------+
//| Script start                                                     |
//+------------------------------------------------------------------+
void OnStart()
  {
   if(IsTradeAllowed())
     {
      string dir = (Trade_Direction==BUY) ? "buy" : "sell";
      int pick = MessageBox("You are about to open " +
                            DoubleToString(Num_Of_Orders,0) + 
                            " " + dir + " order(s)\n",
                            "Confirm Orders", 0x00000001);

      if(pick==1)
        {
         for(int i=0; i<Num_Of_Orders; i++)
            place_order(i);
        }
     }
   else
      MessageBox("Enable AutoTrading Please ");
  }

//+------------------------------------------------------------------+
//| Place order                                                      |
//+------------------------------------------------------------------+
void place_order(int i)
  {
   int ticket;
   double stoplosslevel=0, takeprofitlevel=0;
   double sl_points = StopLoss * Point;
   double tp_points = StopLoss * (RRR + i * Rstep) * Point;

   if(Trade_Direction==BUY)
     {
      if(StopLoss > 0) stoplosslevel = Ask - sl_points;
      if(RRR > 0)      takeprofitlevel = Ask + tp_points;

      ticket = OrderSend(Symbol(), OP_BUY, Lots, Ask, 3,
                         stoplosslevel, takeprofitlevel,
                         NULL, MagicNum, 0, Green);
     }
   else if(Trade_Direction==SELL)
     {
      if(StopLoss > 0) stoplosslevel = Bid + sl_points;
      if(RRR > 0)      takeprofitlevel = Bid - tp_points;

      ticket = OrderSend(Symbol(), OP_SELL, Lots, Bid, 3,
                         stoplosslevel, takeprofitlevel,
                         NULL, MagicNum, 0, Red);
     }

   if(ticket <= 0)
      Alert("OrderSend failed with error #", GetLastError());
  }

//+------------------------------------------------------------------+
