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
