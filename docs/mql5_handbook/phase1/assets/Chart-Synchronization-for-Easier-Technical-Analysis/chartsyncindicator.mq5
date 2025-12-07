//+------------------------------------------------------------------+
//|                                        ChartSyncIndicator.mq5    |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "GIT under MetaQuotes Ltd."
#property version   "1.01"
#property indicator_chart_window
#property indicator_plots 0

input ENUM_TIMEFRAMES BaseTimeframe = PERIOD_H1;  // Base timeframe for objects
input bool SyncAllTimeframes = false;
input color DefaultObjColor = clrDodgerBlue;
input ENUM_LINE_STYLE DefaultObjStyle = STYLE_SOLID;
input int DefaultObjWidth = 2;
input bool DefaultObjBack = true;
input bool SyncUnlockedObjects = false;
input int   ResetButtonX = 10;
input int   ResetButtonY = 20;

#define OBJ_ORIGIN_TF   "OBJ_ORIGIN_TF_"
#define RESET_BUTTON    "resetBtn"

long baseChartID;
string baseSymbol;
string timeframesAssigned[];
ENUM_TIMEFRAMES availableTFs[4] = {PERIOD_H1, PERIOD_M30, PERIOD_M15, PERIOD_M5};


//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit() {
   baseChartID = ChartID();
   baseSymbol = Symbol();
   
   // Set this chart to user-selected base timeframe
   if(Period() != BaseTimeframe) {
      ChartSetSymbolPeriod(baseChartID, baseSymbol, BaseTimeframe);
   }
   
   AssignTimeframesToCharts();
   CreateResetButtons();
   return INIT_SUCCEEDED;
}

void AssignTimeframesToCharts() {
   // Create a list of timeframes excluding the base TF
   ENUM_TIMEFRAMES timeframes[3];
   int index = 0;
   
   for(int i = 0; i < 4; i++) {
      if(availableTFs[i] != BaseTimeframe) {
         timeframes[index] = availableTFs[i];
         index++;
      }
   }
   
   int tfIndex = 0;
   long currChart = ChartFirst();
   ArrayResize(timeframesAssigned, 0);
   
   while(currChart != -1 && tfIndex < ArraySize(timeframes)) {
      if(currChart != baseChartID) {
         ChartSetSymbolPeriod(currChart, baseSymbol, timeframes[tfIndex]);
         int size = ArraySize(timeframesAssigned);
         ArrayResize(timeframesAssigned, size + 1);
         timeframesAssigned[size] = (string)currChart;
         tfIndex++;
      }
      currChart = ChartNext(currChart);
   }
}

void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam) {
   switch(id) {
      case CHARTEVENT_OBJECT_CREATE:
      case CHARTEVENT_OBJECT_DRAG:
         PropagateObject(sparam, (ENUM_TIMEFRAMES)Period());
         break;
      case CHARTEVENT_OBJECT_DELETE:
         DeleteSyncedInstances(sparam);
         break;
      case CHARTEVENT_OBJECT_CLICK:
         if(sparam == RESET_BUTTON) {
            DeleteAllSyncedObjects();
         }
         break;
   }
}

void PropagateObject(string objName, ENUM_TIMEFRAMES srcTF) {
   if(StringFind(objName, "_clone_") != -1) return;
   bool isLocked = ObjectGetInteger(ChartID(), objName, OBJPROP_SELECTABLE);
   if(!SyncUnlockedObjects && !isLocked) return;

   for(int i = 0; i < ArraySize(timeframesAssigned); i++) {
      long targetChart = (long)StringToInteger(timeframesAssigned[i]);
      ENUM_TIMEFRAMES targetTF = (ENUM_TIMEFRAMES)ChartPeriod(targetChart);
      bool shouldPropagate = false;
      
      if(SyncAllTimeframes) {
         shouldPropagate = true;
      }
      else {
         // Propagate from base timeframe to all others
         if(srcTF == BaseTimeframe) {
            shouldPropagate = true;
         }
         // Propagate from other timeframes only to lower timeframes
         else if(srcTF > targetTF) {
            shouldPropagate = true;
         }
      }
      
      if(shouldPropagate) {
         CloneObject(objName, ChartID(), targetChart);
      }
   }
}

void CloneObject(string objName, long srcChart, long targetChart) {
   int type = (int)ObjectGetInteger(srcChart, objName, OBJPROP_TYPE);
   string newName = objName + "_clone_" + (string)targetChart;
   if(!ObjectCreate(targetChart, newName, (ENUM_OBJECT)type, 0, 0, 0)) return;

   datetime time1 = (datetime)ObjectGetInteger(srcChart, objName, OBJPROP_TIME, 0);
   double price1 = ObjectGetDouble(srcChart, objName, OBJPROP_PRICE, 0);
   ObjectSetInteger(targetChart, newName, OBJPROP_TIME, 0, time1);
   ObjectSetDouble(targetChart, newName, OBJPROP_PRICE, 0, price1);

   datetime time2 = (datetime)ObjectGetInteger(srcChart, objName, OBJPROP_TIME, 1);
   double price2 = ObjectGetDouble(srcChart, objName, OBJPROP_PRICE, 1);
   if(time2 > 0 || price2 > 0) {
      ObjectSetInteger(targetChart, newName, OBJPROP_TIME, 1, time2);
      ObjectSetDouble(targetChart, newName, OBJPROP_PRICE, 1, price2);
   }

   color objColor = ObjectGetInteger(srcChart, objName, OBJPROP_COLOR, 0);
   ENUM_LINE_STYLE objStyle = (ENUM_LINE_STYLE)ObjectGetInteger(srcChart, objName, OBJPROP_STYLE, 0);
   int objWidth = ObjectGetInteger(srcChart, objName, OBJPROP_WIDTH, 0);
   bool objBack = ObjectGetInteger(srcChart, objName, OBJPROP_BACK, 0);

   ObjectSetInteger(targetChart, newName, OBJPROP_COLOR, objColor != clrNONE ? objColor : DefaultObjColor);
   ObjectSetInteger(targetChart, newName, OBJPROP_STYLE, objStyle);
   ObjectSetInteger(targetChart, newName, OBJPROP_WIDTH, objWidth);
   ObjectSetInteger(targetChart, newName, OBJPROP_BACK, objBack);
   ObjectSetInteger(targetChart, newName, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(targetChart, newName, OBJPROP_HIDDEN, true);

   string originTag = OBJ_ORIGIN_TF + EnumToString((ENUM_TIMEFRAMES)Period());
   ObjectSetString(targetChart, newName, OBJPROP_TOOLTIP, originTag);

   if(type == OBJ_TEXT || type == OBJ_LABEL) {
      string txt = ObjectGetString(srcChart, objName, OBJPROP_TEXT);
      ObjectSetString(targetChart, newName, OBJPROP_TEXT, txt);
   }

   if(type == OBJ_FIBO) {
      int levels = (int)ObjectGetInteger(srcChart, objName, OBJPROP_LEVELS);
      ObjectSetInteger(targetChart, newName, OBJPROP_LEVELS, levels);
      for(int i = 0; i < levels; i++) {
         double level = ObjectGetDouble(srcChart, objName, OBJPROP_LEVELVALUE, i);
         ObjectSetDouble(targetChart, newName, OBJPROP_LEVELVALUE, i, level);
      }
   }
}

int OnCalculate(const int rates_total,const int prev_calculated,const datetime &time[],const double &open[],const double &high[],const double &low[],const double &close[],const long &tick_volume[],const long &volume[],const int &spread[]) {
   return(rates_total);
}

void DeleteSyncedInstances(string objName) {
   long thisChart = ChartID();
   bool isClone = StringFind(objName, "_clone_") != -1;
   string baseName = isClone ? StringSubstr(objName, 0, StringFind(objName, "_clone_")) : objName;

   // Delete from all charts
   ObjectDelete(thisChart, objName);
   for(int i = 0; i < ArraySize(timeframesAssigned); i++) {
      long chartID = (long)StringToInteger(timeframesAssigned[i]);
      ObjectDelete(chartID, baseName);
      ObjectDelete(chartID, baseName + "_clone_" + (string)thisChart);
   }
}

void DeleteAllSyncedObjects() {
   long chartIDs[];
   ArrayResize(chartIDs, ArraySize(timeframesAssigned) + 1);
   chartIDs[0] = baseChartID;
   for(int i = 0; i < ArraySize(timeframesAssigned); i++)
      chartIDs[i + 1] = (long)StringToInteger(timeframesAssigned[i]);

   for(int j = 0; j < ArraySize(chartIDs); j++) {
      int total = ObjectsTotal(chartIDs[j]);
      for(int i = total - 1; i >= 0; i--) {
         string name = ObjectName(chartIDs[j], i);
         if(StringFind(name, RESET_BUTTON) == -1)
            ObjectDelete(chartIDs[j], name);
      }
   }
}

void CreateResetButtons() {
   CreateResetButtonOnChart(baseChartID);
   for(int i=0; i<ArraySize(timeframesAssigned); i++)
      CreateResetButtonOnChart((long)StringToInteger(timeframesAssigned[i]));
}

void CreateResetButtonOnChart(long cid) {
   if(ObjectFind(cid, RESET_BUTTON) >= 0) ObjectDelete(cid, RESET_BUTTON);
   if(!ObjectCreate(cid, RESET_BUTTON, OBJ_BUTTON, 0, 0, 0)) return;
   ObjectSetInteger(cid, RESET_BUTTON, OBJPROP_XDISTANCE, ResetButtonX);
   ObjectSetInteger(cid, RESET_BUTTON, OBJPROP_YDISTANCE, ResetButtonY);
   ObjectSetInteger(cid, RESET_BUTTON, OBJPROP_XSIZE, 80);
   ObjectSetInteger(cid, RESET_BUTTON, OBJPROP_YSIZE, 20);
   ObjectSetInteger(cid, RESET_BUTTON, OBJPROP_BGCOLOR, clrGray);
   ObjectSetInteger(cid, RESET_BUTTON, OBJPROP_COLOR, clrWhite);
   ObjectSetString(cid, RESET_BUTTON, OBJPROP_TEXT, "Reset All");
   ObjectSetInteger(cid, RESET_BUTTON, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(cid, RESET_BUTTON, OBJPROP_HIDDEN, false);
   ChartRedraw(cid);
}

void OnDeinit(const int reason) {
   DeleteAllSyncedObjects();
}