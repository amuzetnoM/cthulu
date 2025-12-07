//+------------------------------------------------------------------+
//|                                Project 21 API and WebRequest.mq5 |
//|                                             Abioye Israel Pelumi |
//|                             https://linktr.ee/abioyeisraelpelumi |
//+------------------------------------------------------------------+
#property copyright "Abioye Israel Pelumi"
#property link      "https://linktr.ee/abioyeisraelpelumi"
#property version   "1.00"

string method = "GET";
string url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=5";
string headers = "";
int time_out = 5000;
char   data[];
char   result[];
string result_headers;


//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
 


   WebRequest(method, url, headers, time_out, data, result, result_headers);
   string server_result = CharArrayToString(result);
// Print(server_result);

   string candle_data[];
   int array_count = StringSplit(server_result,']', candle_data);
   
   //DAY 1
   string day1_data = candle_data[0];
   StringReplace(day1_data,"[[","");
   StringReplace(day1_data,"\"","");
   
   string day1_data_array[];
   StringSplit(day1_data,',',day1_data_array);
 //  ArrayPrint(day1_data_array);
   
  
  //DAY 2
   string day2_data = candle_data[1];
   StringReplace(day2_data,",[","");
   StringReplace(day2_data,"\"","");
   
   string day2_data_array[];
   StringSplit(day2_data,',',day2_data_array);
   
   //DAY 3
   
   string day3_data = candle_data[2];
   StringReplace(day3_data,",[","");
   StringReplace(day3_data,"\"","");
   
   string day3_data_array[];
   StringSplit(day3_data,',',day3_data_array);
   
   
   //DAY 4
   
   string day4_data = candle_data[3];
   StringReplace(day4_data,",[","");
   StringReplace(day4_data,"\"","");
   
   string day4_data_array[];
   StringSplit(day4_data,',',day4_data_array);
   
    //DAY 5
   
   string day5_data = candle_data[4];
   StringReplace(day5_data,",[","");
   StringReplace(day5_data,"\"","");
   
   string day5_data_array[];
   StringSplit(day5_data,',',day5_data_array);
   
   
   
   // Opening Time Array
   
  long day1_time_s =  (long)StringToInteger(day1_data_array[0])/1000;
  datetime day1_time = (datetime)day1_time_s;
  
  long day2_time_s =  (long)StringToInteger(day2_data_array[0])/1000;
  datetime day2_time = (datetime)day2_time_s;
  
  long day3_time_s =  (long)StringToInteger(day3_data_array[0])/1000;
  datetime day3_time = (datetime)day3_time_s;
  
  long day4_time_s =  (long)StringToInteger(day4_data_array[0])/1000;
  datetime day4_time = (datetime)day4_time_s;
  
   long day5_time_s =  (long)StringToInteger(day5_data_array[0])/1000;
  datetime day5_time = (datetime)day5_time_s;
  
  // Print("DAY 1 TIME: ", day1_time,"\nDAY 2 TIME: ",day2_time,"\nDAY 3 TIME: ",day3_time,"\nDAY 4 TIME: ",day4_time,"\nDAY 5 TIME: ",day5_time);
  
  datetime OpenTime[5] = {day1_time, day2_time, day3_time, day4_time, day5_time};
  
 // Print("DAY 1 TIME: ", OpenTime[0],"\nDAY 2 TIME: ",OpenTime[1],"\nDAY 3 TIME: ",OpenTime[2],"\nDAY 4 TIME: ",OpenTime[3],"\nDAY 5 TIME: ",OpenTime[4]);
 
  
 // Opening Price Array
 double day1_open = StringToDouble(day1_data_array[1]);
 double day2_open = StringToDouble(day2_data_array[1]);
 double day3_open = StringToDouble(day3_data_array[1]);
 double day4_open = StringToDouble(day4_data_array[1]);
 double day5_open = StringToDouble(day4_data_array[1]);
 
 double OpenPrice[5] = {day1_open, day2_open, day3_open, day4_open, day5_open};
 
//Print("DAY 1 OPEN PRICE: ", OpenPrice[0],"\nDAY 2 OPEN PRICE: ",OpenPrice[1],"\nDAY 3 OPEN PRICE: ",OpenPrice[2],"\nDAY 4 OPEN PRICE: ",OpenPrice[3],"\nDAY 5 OPEN PRICE: ",OpenPrice[4]);
   
   
 // Closing Price Array
 double day1_close = StringToDouble(day1_data_array[4]);
 double day2_close = StringToDouble(day2_data_array[4]);
 double day3_close = StringToDouble(day3_data_array[4]);
 double day4_close = StringToDouble(day4_data_array[4]);
 double day5_close = StringToDouble(day4_data_array[4]);
 
 double ClosePrice[5] = {day1_close, day2_close, day3_close, day4_close, day5_close};
// Print("DAY 1 CLOSE PRICE: ", ClosePrice[0],"\nDAY 2 CLOSE PRICE: ",ClosePrice[1],"\nDAY 3 CLOSE PRICE: ",ClosePrice[2],"\nDAY 4 CLOSE PRICE: ",ClosePrice[3],"\nDAY 5 CLOSE PRICE: ",ClosePrice[4]);
 
 
 // High Price Array
 double day1_high = StringToDouble(day1_data_array[2]);
 double day2_high = StringToDouble(day2_data_array[2]);
 double day3_high = StringToDouble(day3_data_array[2]);
 double day4_high = StringToDouble(day4_data_array[2]);
 double day5_high = StringToDouble(day4_data_array[2]);
 
 double HighPrice[5] = {day1_high, day2_high, day3_high, day4_high, day5_high};
 //Print("DAY 1 HIGH PRICE: ", HighPrice[0],"\nDAY 2 HIGH PRICE: ", HighPrice[1],"\nDAY 3 HIGH PRICE: ", HighPrice[2],"\nDAY 4 HIGH PRICE: ", HighPrice[3],"\nDAY 5 HIGH PRICE: ", HighPrice[4]);
   
// Low Price Array
 double day1_low = StringToDouble(day1_data_array[3]);
 double day2_low = StringToDouble(day2_data_array[3]);
 double day3_low = StringToDouble(day3_data_array[3]);
 double day4_low = StringToDouble(day4_data_array[3]);
 double day5_low = StringToDouble(day4_data_array[3]);
 
  double LowPrice[5] = {day1_low, day2_low, day3_low, day4_low, day5_low};
  Print("DAY 1 LOW PRICE: ", LowPrice[0],"\nDAY 2 LOW PRICE: ", LowPrice[1],"\nDAY 3 LOW PRICE: ", LowPrice[2],"\nDAY 4 LOW PRICE: ", LowPrice[3],"\nDAY 5 LOW PRICE: ", LowPrice[4]);
 
  
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---

  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---

  }
//+------------------------------------------------------------------+
