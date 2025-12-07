//+------------------------------------------------------------------+
//|                             Get Lot By Risk Per Trade and SL.mq5 |
//|                                                        Your name |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Your name"
#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict
#property script_show_inputs

input double percentage_risk_per_operation = 1.0; // Risk per operation in %
input long   sl = 600; // Stop Loss in points
input ENUM_ORDER_TYPE Order_Type = ORDER_TYPE_BUY; // Order Type

#include <Risk Management.mqh>

//+------------------------------------------------------------------+
//| Main script function                                             |
//+------------------------------------------------------------------+
void OnStart()
  {
   // Calculate the maximum allowable risk per operation in account currency
   double risk_per_operation = ((percentage_risk_per_operation / 100.0) * AccountInfoDouble(ACCOUNT_BALANCE));
   
   // Print input and calculated risk details
   Print("Risk Per operation: ", risk_per_operation);
   Print("SL in points: ", sl);
   Print("Order type: ", EnumToString(Order_Type));
   
   double new_lot;
   double new_risk_per_operation;
   
   // Calculate the ideal lot size
   GetIdealLot(new_lot, GetMaxLote(Order_Type), risk_per_operation, new_risk_per_operation, sl);
   
   // Check if the lot size is valid
   if (new_lot <= 0)
     {
      Print("The stop loss is too large or the risk per operation is low. Increase the risk or decrease the stop loss.");
     }
   else
     {
      // Display calculated values
      Print("Ideal Lot: ", new_lot);
      Print("Maximum loss with SL: ", sl, " | Lot: ", new_lot, " is: ", new_risk_per_operation);
      Comment("Ideal Lot: ", new_lot);
     }
   
   Sleep(1000);
   Comment(" ");
  }
//+------------------------------------------------------------------+