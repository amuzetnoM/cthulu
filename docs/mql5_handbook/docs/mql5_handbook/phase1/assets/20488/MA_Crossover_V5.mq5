//+------------------------------------------------------------------+
//|                                              MA Crossover V1.mq5 |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"

//+------------------------------------------------------------------+
//| Resources                                                        |
//+------------------------------------------------------------------+
#resource "\\Files\\EURUSD Detailed RF.onnx" as const uchar onnx_proto[];

//+------------------------------------------------------------------+
//| Technical Indicators                                             |
//+------------------------------------------------------------------+
int      ma_fast_handler,ma_slow_handler,atr_handler;
double   ma_fast_reading[],ma_slow_reading[],atr_reading[];

//+------------------------------------------------------------------+
//| Global variables                                                 |
//+------------------------------------------------------------------+
double  ask,bid;
vectorf model_inputs,model_outputs;
long    model;

//+------------------------------------------------------------------+
//| Libraries                                                        |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>
CTrade Trade;

#define HORIZON 5

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- Setup our indicators
   ma_fast_handler = iMA("EURUSD",PERIOD_D1,30,0,MODE_SMA,PRICE_CLOSE);
   ma_slow_handler = iMA("EURUSD",PERIOD_D1,60,0,MODE_SMA,PRICE_CLOSE);
   atr_handler     = iATR("EURUSD",PERIOD_D1,14);

//--- Setup the ONNX model
   model = OnnxCreateFromBuffer(onnx_proto,ONNX_DATA_TYPE_FLOAT);

//--- Define the model parameter shape
   ulong input_shape[] = {1,20};
   ulong output_shape[] = {1,3};

   OnnxSetInputShape(model,0,input_shape);
   OnnxSetOutputShape(model,0,output_shape);

   model_inputs = vectorf::Zeros(20);
   model_outputs = vectorf::Zeros(3);

   if(model != INVALID_HANDLE)
     {
      return(INIT_SUCCEEDED);
     }

//---
   return(INIT_FAILED);
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
   OnnxRelease(model);
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
      CopyBuffer(ma_fast_handler,0,0,10,ma_fast_reading);
      CopyBuffer(ma_slow_handler,0,0,10,ma_slow_reading);
      CopyBuffer(atr_handler,0,0,10,atr_reading);

      double open = iOpen("EURUSD",PERIOD_D1,0);
      double close = iClose("EURUSD",PERIOD_D1,0);
      double high = iHigh("EURUSD",PERIOD_D1,0);
      double low = iLow("EURUSD",PERIOD_D1,0);

      model_inputs[0] = (float) open;
      model_inputs[1] = (float) high;
      model_inputs[2] = (float) low;
      model_inputs[3] = (float) close;
      model_inputs[4] = (float) ma_fast_reading[0];
      model_inputs[5] = (float) ma_slow_reading[0];
      model_inputs[6] = (float) (iOpen(_Symbol,PERIOD_CURRENT,0) - iOpen(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[7] = (float) (iHigh(_Symbol,PERIOD_CURRENT,0) - iHigh(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[8] = (float) (iLow(_Symbol,PERIOD_CURRENT,0) - iLow(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[9] = (float) (iClose(_Symbol,PERIOD_CURRENT,0) - iClose(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[10] = (float)  (ma_fast_reading[0] - ma_fast_reading[0+HORIZON]);
      model_inputs[11] = (float) (ma_slow_reading[0] - ma_slow_reading[0+HORIZON]);
      model_inputs[12] = (float) (iOpen(_Symbol,PERIOD_CURRENT,0+HORIZON) - iHigh(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[13] = (float)  (iOpen(_Symbol,PERIOD_CURRENT,0+HORIZON) - iLow(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[14] = (float) (iOpen(_Symbol,PERIOD_CURRENT,0+HORIZON) - iClose(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[15] = (float)  (iHigh(_Symbol,PERIOD_CURRENT,0+HORIZON) - iLow(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[16] = (float) (iHigh(_Symbol,PERIOD_CURRENT,0+HORIZON) - iClose(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[17] = (float) (iLow(_Symbol,PERIOD_CURRENT,0+HORIZON) - iClose(_Symbol,PERIOD_CURRENT,0+HORIZON));
      model_inputs[18] = (float) (iClose(_Symbol,PERIOD_CURRENT,0+HORIZON) - ma_fast_reading[0+HORIZON]);
      model_inputs[19] = (float) (iClose(_Symbol,PERIOD_CURRENT,0+HORIZON) - ma_slow_reading[0+HORIZON]);


      ask = SymbolInfoDouble("EURUSD",SYMBOL_ASK);
      bid = SymbolInfoDouble("EURUSD",SYMBOL_BID);

      //--- If we have no open positions
      if(PositionsTotal() == 0)
        {

         if(!(OnnxRun(model,ONNX_DATA_TYPE_FLOAT,model_inputs,model_outputs)))
           {
            Comment("Failed to obtain a forecast from our model: ",GetLastError());
           }


         else
           {
            Comment("Forecast: ",model_outputs);

            //--- Trading rules
            if(((model_outputs[1] > 0)) || ((ma_fast_reading[0] > ma_slow_reading[0]) && (low > ma_fast_reading[0])))
              {
               //--- Buy signal
               Trade.Buy(0.01,"EURUSD",ask,ask-(atr_reading[0] * 2),ask+(atr_reading[0] * 2),"");
              }

            else
               if(((model_outputs[1] < 0)) || ((ma_fast_reading[0] < ma_slow_reading[0]) && (low < ma_slow_reading[0])))
                 {
                  //--- Sell signal
                  Trade.Sell(0.01,"EURUSD",bid,bid+(atr_reading[0] * 2),bid-(atr_reading[0] * 2),"");
                 }
           }
        }
     }
  }
//+------------------------------------------------------------------+