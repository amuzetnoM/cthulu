//+------------------------------------------------------------------+
//|                                                      ProjectName |
//|                                      Copyright 2020, CompanyName |
//|                                       http://www.companyname.net |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property script_show_inputs

//--- Define our moving average indicator
#define MA_PERIOD_FAST     30                   //--- Moving Average Fast Period
#define MA_PERIOD_SLOW     60                   //--- Moving Average Slow Period
#define MA_TYPE            MODE_SMA             //--- Type of moving average we have
#define HORIZON            5                    //--- Forecast horizon

//--- Our handlers for our indicators
int ma_fast_handle,ma_slow_handle;

//--- Data structures to store the readings from our indicators
double ma_fast_reading[],ma_slow_reading[];

//--- File name
string file_name = Symbol() + " Cross Over Data.csv";

//--- Amount of data requested
input int size = 3000;

//+------------------------------------------------------------------+
//| Our script execution                                             |
//+------------------------------------------------------------------+
void OnStart()
  {
   int fetch = size + (HORIZON * 2);
//---Setup our technical indicators
   ma_fast_handle        = iMA(_Symbol,PERIOD_CURRENT,MA_PERIOD_FAST,0,MA_TYPE,PRICE_CLOSE);
   ma_slow_handle        = iMA(_Symbol,PERIOD_CURRENT,MA_PERIOD_SLOW,0,MA_TYPE,PRICE_OPEN);

   
//---Set the values as series
   CopyBuffer(ma_fast_handle,0,0,fetch,ma_fast_reading);
   ArraySetAsSeries(ma_fast_reading,true);
   CopyBuffer(ma_slow_handle,0,0,fetch,ma_slow_reading);
   ArraySetAsSeries(ma_slow_reading,true);
   
//---Write to file
   int file_handle=FileOpen(file_name,FILE_WRITE|FILE_ANSI|FILE_CSV,",");

   for(int i=size;i>=1;i--)
     {
      if(i == size)
        {
         FileWrite(file_handle,
                  //--- Time
                  "Time",
                   //--- OHLC
                   "Open",
                   "High",
                   "Low",
                   "Close",
                   "MA F",
                   "MA S"
                  );
        }

      else
        {
         FileWrite(file_handle,
                   iTime(_Symbol,PERIOD_CURRENT,i),
                   //--- OHLC
                   iOpen(_Symbol,PERIOD_CURRENT,i),
                   iHigh(_Symbol,PERIOD_CURRENT,i),
                   iLow(_Symbol,PERIOD_CURRENT,i),
                   iClose(_Symbol,PERIOD_CURRENT,i),
                   ma_fast_reading[i],
                   ma_slow_reading[i]
                   );
        }
     }
//--- Close the file
   FileClose(file_handle);
  }
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Undefine system constants                                        |
//+------------------------------------------------------------------+
#undef HORIZON
#undef MA_PERIOD_FAST
#undef MA_PERIOD_SLOW
#undef MA_TYPE
//+------------------------------------------------------------------+