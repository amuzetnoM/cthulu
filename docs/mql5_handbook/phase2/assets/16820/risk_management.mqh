//+------------------------------------------------------------------+
//|                                              Risk Management.mqh |
//|                                                       Your name  |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Your name "
#property link      "https://www.mql5.com"
#property strict

//--------------------------------  
double GetMaxLote(ENUM_ORDER_TYPE type, double DEVIATION = 100, double STOP_LIMIT = 50) 
  { 
   //--- Set variables
   double VOLUME = 1.0; // Initial volume size
   ENUM_ORDER_TYPE new_type = MarketOrderByOrderType(type); 
   double price = PriceByOrderType(_Symbol, type, DEVIATION, STOP_LIMIT); // Price for the given order type
   double volume_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP); // Volume step for the symbol
   double margin = EMPTY_VALUE; // Required margin, initialized as empty
  
   //--- Get margin for one lot
   ResetLastError(); 
   if (!OrderCalcMargin(new_type, _Symbol, VOLUME, price, margin)) 
     { 
      Print("OrderCalcMargin() failed. Error ", GetLastError()); 
      return 0; // Exit the function if margin calculation fails
     }
   //--- Calculate the maximum lot size
   double result = MathFloor((AccountInfoDouble(ACCOUNT_MARGIN_FREE) / margin) / volume_step) * volume_step; 
   return result; // Return the maximum lot size
  }
ENUM_ORDER_TYPE MarketOrderByOrderType(ENUM_ORDER_TYPE type) 
  { 
   switch(type) 
     { 
      case ORDER_TYPE_BUY  : case ORDER_TYPE_BUY_LIMIT  : case ORDER_TYPE_BUY_STOP  : case ORDER_TYPE_BUY_STOP_LIMIT  : 
        return(ORDER_TYPE_BUY); 
      case ORDER_TYPE_SELL : case ORDER_TYPE_SELL_LIMIT : case ORDER_TYPE_SELL_STOP : case ORDER_TYPE_SELL_STOP_LIMIT : 
        return(ORDER_TYPE_SELL); 
     } 
   return(WRONG_VALUE); 
  }   
double PriceByOrderType(const string symbol, const ENUM_ORDER_TYPE order_type ,double  DEVIATION = 100  ,double STOP_LIMIT = 50) 
  {
   int     digits=0; 
   double  point=0; 
   MqlTick tick={}; 
  
//--- we get the Point value of the symbol
   ResetLastError(); 
   if(!SymbolInfoDouble(symbol, SYMBOL_POINT, point)) 
     { 
      Print("SymbolInfoDouble() failed. Error ", GetLastError()); 
      return 0; 
     } 
      
//--- we get the Digits value of the symbol
   long value=0; 
   if(!SymbolInfoInteger(symbol, SYMBOL_DIGITS, value)) 
     { 
      Print("SymbolInfoInteger() failed. Error ", GetLastError()); 
      return 0; 
     } 
    digits=(int)value; 
    
//--- we get the latest prices of the symbol
   if(!SymbolInfoTick(symbol, tick)) 
     { 
      Print("SymbolInfoTick() failed. Error ", GetLastError()); 
      return 0; 
     } 
//--- Depending on the type of order, we return the price
   switch(order_type) 
     { 
      case ORDER_TYPE_BUY              :  return(tick.ask); 
      case ORDER_TYPE_SELL             :  return(tick.bid); 
      case ORDER_TYPE_BUY_LIMIT        :  return(NormalizeDouble(tick.ask - DEVIATION * point, digits)); 
      case ORDER_TYPE_SELL_LIMIT       :  return(NormalizeDouble(tick.bid + DEVIATION * point, digits)); 
      case ORDER_TYPE_BUY_STOP         :  return(NormalizeDouble(tick.ask + DEVIATION * point, digits)); 
      case ORDER_TYPE_SELL_STOP        :  return(NormalizeDouble(tick.bid - DEVIATION * point, digits)); 
      case ORDER_TYPE_BUY_STOP_LIMIT   :  return(NormalizeDouble(tick.ask + DEVIATION * point - STOP_LIMIT * point, digits)); 
      case ORDER_TYPE_SELL_STOP_LIMIT  :  return(NormalizeDouble(tick.bid - DEVIATION * point + STOP_LIMIT * point, digits)); 
      default                          :  return(0); 
     } 
  } 

//-------------------------------- 
  
ulong GetMagic(const ulong ticket)
{
HistoryOrderSelect(ticket);
return HistoryOrderGetInteger(ticket,ORDER_MAGIC); 
}  

double GetNetProfitSince(bool include_all_magic, ulong specific_magic, datetime start_date)
{
   double total_net_profit = 0.0; // Initialize the total net profit
   ResetLastError(); // Reset any previous errors

   // Check if the start date is valid
   if((start_date > 0 || start_date != D'1971.01.01 00:00'))
   {   
      // Select the order history from the given start date to the current time
      if(!HistorySelect(start_date, TimeCurrent())) 
      {
         Print("Error when selecting orders: ", _LastError); 
         return 0.0; // Exit if unable to select the history
      }

      int total_deals = HistoryDealsTotal(); // Get the total number of deals in history
  
      // Iterate through all deals
      for(int i = 0; i < total_deals; i++)
      {
         ulong deal_ticket = HistoryDealGetTicket(i); // Retrieve the deal ticket

         // Skip balance-type deals
         if(HistoryDealGetInteger(deal_ticket, DEAL_TYPE) == DEAL_TYPE_BALANCE) continue;            

         ENUM_DEAL_ENTRY deal_entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY); // Get deal entry type
         long deal_close_time_long = HistoryDealGetInteger(deal_ticket, DEAL_TIME); // Get deal close time (as long)
         datetime deal_close_time = (datetime)deal_close_time_long; // Explicit conversion to datetime
         ulong position_id = HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID); // Get the position ID

         // Check if the deal is within the specified date range and is a valid entry/exit deal
         if(deal_close_time >= start_date && (deal_entry == DEAL_ENTRY_OUT || deal_entry == DEAL_ENTRY_IN))
         {             
            // Check if the deal matches the specified magic number or if all deals are to be included
            if((HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) == specific_magic || specific_magic == GetMagic(position_id)) 
               || include_all_magic == true)
            {
               double deal_profit = HistoryDealGetDouble(deal_ticket, DEAL_PROFIT); // Retrieve profit from the deal
               double deal_commission = HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION); // Retrieve commission
               double deal_swap = HistoryDealGetDouble(deal_ticket, DEAL_SWAP); // Retrieve swap fees
               
               double deal_net_profit = deal_profit + deal_commission + deal_swap; // Calculate net profit for the deal
               total_net_profit += deal_net_profit; // Add to the total net profit
            }
         }
      }
   }
     
   return NormalizeDouble(total_net_profit, 2); // Return the total net profit rounded to 2 decimals
}

//-------------------------------- 

void GetIdealLot(double& nlot , double glot , double max_risk_per_operation , double& new_risk_per_operation, long StopLoss)
{
 if(StopLoss <= 0)
  {
   Print("[ERROR SL] Stop Loss distance is less than or equal to zero, now correct the stoploss distance: ", StopLoss);
   nlot = 0.0;
   return;
  }
  Print("Max Lot: " , glot, "  |  RiskPerOperation: " , max_risk_per_operation); 

 new_risk_per_operation= 0;
 long spread = (long)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
 double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
 double step = SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
 
 double rpo = (glot * (spread + 1 + (StopLoss*tick_value))); 
   
 if(rpo >  max_risk_per_operation )
   {
    if(max_risk_per_operation <= 0) return;
    
    double new_lot = (max_risk_per_operation  / rpo) * glot;
    new_lot  = MathFloor(new_lot /step)*step; 
    new_risk_per_operation =  new_lot  * (spread + 1 + (StopLoss*tick_value ));      
    nlot=  new_lot ; 
   }
 else
   {
    new_risk_per_operation = rpo;
    nlot = glot ;
   }   

} 

//-------------------------------- 

long GetSL(const ENUM_ORDER_TYPE type , double risk_per_operation , double lot) 
{
 long spread = (long)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
 double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
 double result = ((risk_per_operation/lot)-spread-1)/tick_value;
 
return long(MathRound(result));
}  

//-------------------------------- 

int DistanceToPoint(double dist)
{
  double pointSize = SymbolInfoDouble(_Symbol, SYMBOL_POINT); // Get the point size for the current symbol
  return (int)(dist / pointSize); // Calculate and return the distance in points
}  