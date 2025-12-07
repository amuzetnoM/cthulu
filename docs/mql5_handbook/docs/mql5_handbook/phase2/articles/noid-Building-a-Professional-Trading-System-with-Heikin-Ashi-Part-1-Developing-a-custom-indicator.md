---
title: "Building a Professional Trading System with Heikin Ashi (Part 1): Developing a custom indicator"
original_url: "https://www.mql5.com/en/articles/19260"
phase: "phase2"
date: "8 September 2025, 08:19"
---

# Building a Professional Trading System with Heikin Ashi (Part 1): Developing a custom indicator



[](javascript:void(false);)

[日本語](/ja/articles/19260)

[](#pocket)

[](/en/articles/19260?print=)

![preview](assets/Building-a-Professional-Trading-System-with-Heikin-Ashi-Part-1-Developing-a-custom-indicator/e6de49aa2eba41b3a2d76e5a6c72d658.jpeg)

![Building a Professional Trading System with Heikin Ashi (Part 1): Developing a custom indicator](https://c.mql5.com/2/167/19260-building-a-professional-trading-system-with-heikin-ashi-part-I_600x314.jpg)

# Building a Professional Trading System with Heikin Ashi (Part 1): Developing a custom indicator

[MetaTrader 5](/en/articles/mt5)

          —
          
[Trading systems](/en/articles/mt5/trading_systems)

        | 
8 September 2025, 08:19

![](https://c.mql5.com/i/icons.svg#views-white-usage)

          9 959
        

[![](https://c.mql5.com/i/icons.svg#comments-white-usage)0](/en/forum/494952)

![Chacha Ian Maroa](https://c.mql5.com/avatar/2025/5/68331b36-7e52.png)

[Chacha Ian Maroa](/en/users/chachaian)
 

### Introduction

 
Technical indicators are at the heart of algorithmic trading, and mastering how to build them is a key step in any MQL5 developer's journey. In this article, we take a hands-on approach to custom indicator development by creating one of the most popular trend-smoothing tools: the Heikin Ashi Chart.
 
This article is the first part of a two-part series. In part one, we will explore the theory behind Heikin Ashi candles, explain how they are calculated, and walk through the step-by-step process of coding a Heikin Ashi indicator from scratch using MQL5. The goal is not just to copy-paste source code but to truly understand the why behind each line of the source code so that you can apply these best practices when building your custom indicators.
 
In Part Two, we will develop an expert advisor that uses the Heikin Ashi indicator as the foundation for its entries and exits. Let us begin by understanding what makes Heikin Ashi charts different from traditional candlestick charts.
 
Before we get started, there are a few things you should be comfortable with. This article assumes that you:
 
 
Have a solid understanding of the MQL5 programming language. 
 
Know how to use MetaTrader 5 and MetaEditor 5.
 
Can attach indicators and expert advisors to a chart.
 
 After reading this article, you will be well equipped with the knowledge on how to implement custom indicators using modern MQL5 best practices. While the example here focuses on Heikin Ashi, the same techniques can be applied to any indicator that requires custom candlesticks or color-based visualization of trading opportunities.
 

### How is Heikin Ashi different from a traditional candlestick?

 
To begin, let us look at two charts side by side.
 
A traditional candlestick chart:
 
 
![Traditional Candlestick chart](https://c.mql5.com/2/165/CandleStickChart.png)
 
A Heikin Ashi chart generated from the same price data:
 
 
![Heikin Ashi Chart](https://c.mql5.com/2/165/HeikinAShiChart.png)
 
Both charts are based on recent gold price action. As you compare them, pay attention to how the candles behave during trending periods. While traditional candlestick charts update with each new price bar, they can often appear choppy, frequently changing color even when the overall trend remains intact. This can create visual noise and make it harder to gauge momentum at a glance. In contrast, Heikin Ashi candles are calculated using smoothed values, which results in a much cleaner appearance. During trending periods, Heikin Ashi typically prints long sequences of same-colored candles, making it easier to visually identify uptrends and downtrends.
 
In simple terms, Heikin Ashi candles tend to stay green during uptrends and red during downtrends, filtering out minor pullbacks that might otherwise look like reversals on a traditional chart. This makes them a powerful tool for traders looking to follow the trend while ignoring temporary fluctuations.
 
In the next section, we'll break down exactly how these candles are calculated.
 

### 

 

### How Heikin Ashi candles are calculated

 
Before we look at how Heikin Ashi candles are calculated, let us first understand what makes them different from regular candlesticks. In a traditional candlestick chart, each candle is formed using four key values from the market.
 
 
![Candle Stick Anatomy](https://c.mql5.com/2/167/CSA.png)
 
 
Open is the price at the start of candlestick formation.
 
High is the highest price reached during candlestick formation.
 
Low is the lowest price reached.
 
Close is the final price at the end of candlestick formation.
 
 
These values directly reflect what happened during a specific time period, such as one hour or one day. However, Heikin Ashi candlesticks don't use these raw values directly. Instead, they use a modified set of values to smooth out the chart and highlight the overall trend more clearly.
 
The Heikin Ashi candle is made up of
 
 
The Heikin Ashi Open, which is a smoothed version of the candlestick open.
 
The Heikin Ashi High, which is the highest value from a set that includes both real and smoothed data.
 
The Heikin Ashi Low, which is the lowest value from the same kind of set.
 
The Heikin Ashi Close, which is the average price of the current real candle.
 
 
Let us now study exactly how each of these Heikin Ashi candlestick values is calculated.
 

### 

 

### The Heikin Ashi Formulas

 
Heikin Ashi close = (Open + High + Low + Close) / 4.
 
This is the average price of the current candle. It gives a single balanced number that reflects the overall movement of price during this period. 
 
Heikin Ashi open = (previous Heikin Ashi candle open + previous Heikin Ashi candle close) / 2.
 
This means that the open of the current Heikin Ashi candle is not the current market open but the midpoint of the previous Heikin Ashi candle's body, which helps smooth transitions between candles and produces that "flowing" appearance.
 
Heikin Ashi High = The highest value among Heikin Ashi High, Heikin Ashi Open, and Heikin Ashi Close.
 
Heikin Ashi Low = The lowest value among Low, Heikin Ashi Open, and Heikin Ashi Close.
 
The previous two values combine the actual highs/lows of the market with the smoothed open and close, giving the candle realistic wicks while still benefiting from smoothing.
 
In short:
 
The Heikin Ashi close reflects the average of the current candle's prices. The Heikin Ashi open depends on the previous candle's smoothed values. Heikin Ashi High/Heikin Ashi Low use both raw and smoothed values to represent price extremes.
 
This method of calculation is what gives the Heikin Ashi candles their clean, trend-focused appearance. They tend to stay green in uptrends and red in downtrends, filtering out short-term fluctuations that can confuse the eye.
 
In the next sections we will put this knowledge into action by building a custom Heikin Ashi indicator step-by-step using MQL5.
 

### 

 

### Planning the Indicator Logic

 
Before jumping into the code, it is important to briefly plan the logic of our Heikin Ashi indicator. First, let us establish that we are going to build a custom indicator that displays Heikin Ashi candles directly on the chart, just like normal candlesticks, but based on smoothed price calculations.
 
In addition to the standard visualization, we will enhance the Heikin Ashi chart by coloring the candles using three distinct colors: one for bullish candles, another for bearish candles, and a third one for neutral candles.
 
To support this visual logic, our indicator will use five buffers:
 
 
Heikin Ashi Open. This is an array that stores the Heikin Ashi open price.
 
Heikin Ashi High. This is an array that stores the Heikin Ashi high price.
 
Heikin Ashi Low. This is an array that stores the Heikin Ashi low price.
 
Heikin Ashi Close. This is an array that stores the Heikin Ashi close price.
 
Color Buffer. This is an array that stores the color index for each Heikin Ashi candle depending on whether it is bullish, bearish, or neutral.
 
 
Each buffer plays an essential role in both plotting the Heikin Ashi candle and applying the appropriate color dynamically.
 
To render these candles, we will use a single graphic plot with DRAW_COLOR_CANDLES, which allows us to use one plot ID and a separate buffer to handle the coloring. One thing we must handle carefully is the very first bar on the chart, since it doesn't have a previous Heikin Ashi value. We will manually initialize the values for the first bar so that the rest of the candles can be built accurately based on the proper formula.
 
Lastly, to keep the code clean and beginner-friendly, we will write it using a modular programming style, separating key parts of the logic into small, manageable functions. This will make the code easier to understand, debug, and expand upon in future tutorials.
 

### 

 

### Step-by-step guide to coding the Heikin Ashi Indicator

 
To create our custom Heikin Ashi Indicator, we'll be using the MQL5 programming language. This is the native language for developing automated trading tools on MetaTrader 5.
 
Since we assume readers already know how to work with MetaTrader 5, MetaEditor, and the basics of attaching indicators to a chart, we'll skip the setup details and move directly into the development of our custom Heikin Ashi indicator.
 
Below is the initial boilerplate code that we'll be working with as the foundation for building our custom indicator. From this starting point, we'll begin implementing the core logic step by step.
 

```
//+------------------------------------------------------------------+
//|                                          heikinAshiIndicator.mq5 |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                          https://www.mql5.com/en/users/chachaian |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, MetaQuotes Ltd."
#property link      "https://www.mql5.com/en/users/chachaian"
#property version   "1.00"

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
  
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int32_t  rates_total,
                const int32_t  prev_calculated,
                const datetime &time       [],
                const double   &open       [],
                const double   &high       [],
                const double   &low        [],
                const double   &close      [],
                const long     &tick_volume[],
                const long     &volume     [],
                const int32_t  &spread     []) 
{
     
   return(rates_total);
}
//+------------------------------------------------------------------+
```

 
Let us break this code down into simple, logical parts so it's easier to follow.
 
Property Directives:
 

```
...
#property copyright "Copyright 2025, MetaQuotes Ltd. Developer is Chacha Ian"
#property link      "https://www.mql5.com/en/users/chachaian"
#property version   "1.00"

...
```

 
These lines set meta-information about the indicator, which will appear in the MetaTrader 5 navigator and description window.
 
 
#property copyright. This declares the copyright holder and developer. Good for branding and code ownership
 
#property link. This provides a clickable link to your project file or project page.
 
#property version. This is helpful for version control during future updates.
 
 Initialization Function: 
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   return(INIT_SUCCEEDED);
}

...
```

 
The initialization function (OnInit()) is called only once when the indicator is first attached to a chart. It is used to handle setup and configuration tasks. Returning the INIT_SUCCEEDED signal to MetaTrader 5 that the indicator has loaded successfully. In the following steps, we will use OnInit() to register indicator buffers and define the visual properties of our plots.
 
Calculate Function:
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int32_t  rates_total,
                const int32_t  prev_calculated,
                const datetime &time[],
                const double   &open[],
                const double   &high[],
                const double   &low[],
                const double   &close[],
                const long     &tick_volume[],
                const long     &volume[],
                const int32_t  &spread[]) 
{

   return(rates_total);
}

...
```

 
This is the heart of your indicator. It's called repeatedly as new candles form. Its parameters provide access to:
 
 
Rates_total. This refers to the total bars available.
 
Prev_calculated. This is how many bars were processed during the last call of the 'OnCalculate' function (for optimization).
 
Time, open, high, low, and close variables, which are basically our historical price time series.
 
Volume, tick_volume, and spread, which are additional trading data.
 
 
One key thing to note is that the 'OnCalculate' function is automatically called whenever new tick data comes in or when historical data is updated. For example, when there's a gap in historical data and it gets filled. This is where most of our indicator's logic will go.
 
In MetaTrader 5, indicators can be displayed in two main ways: either directly on the main chart window (overlaying price candles) or in a separate subwindow below the main chart.
 
To define how an indicator should be displayed, we use either #property indicator_chart_window for chart overlays or #property indicator_sub_window for subwindow-based indicators. Since we are building an indicator that overlays price, we want it to appear right on the main chart.
 
With that in mind, let us go ahead and add the following line just below our existing #property directives:
 

```
#property copyright "Copyright 2025, MetaQuotes Ltd. Developer is Chacha Ian"
#property link      "https://www.mql5.com/en/users/chachaian"
#property version   "1.00"
#property indicator_chart_window

...
```

 
In MQL5, custom indicators usually store their calculated values in special dynamic arrays called indicator buffers. These buffers are registered using a built-in MQL5 function called SetIndexBuffer() and are essential for visualizing data on the chart, like, drawing lines, histograms, arrows, and more.
 
Before you can use them in your source code, you need to specify how many buffers your indicator will use. This is done using the directive #property indicator_buffers N. Here N represents the total number of buffers that your indicator needs. In our case, we are going to use 5 buffers, so we'll declare it like this: #property indicator_buffers 5.
 
Let us go ahead and add the following line just below the other existing directives in our source code.
 

```
...

#property indicator_chart_window
#property indicator_buffers 5
...
```

 
Indicators usually implement graphic constructions to visually display their calculations on the chart. These visual elements, such as lines, histograms, or arrows, are also known as graphic plots. They help traders interpret what the indicator is doing at a glance.
 
The number of graphic plots an indicator will display is set using the directive #property indicator_plots P, where P is the number of graphic plots to be displayed by the indicator. In our case, we are only working with a single graphic plot.
 
Let us go ahead and add the following line of code just below the other existing #property directives.
 

```
...
#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1
...
```

 
Next, we move on to declaring the arrays that will act as indicator buffers. Usually, this is done in the global scope. The data type of these arrays is almost always set as double, since indicator values are typically floating-point numbers. Let's go ahead and declare them now, just above the OnInit() function, so they are available throughout the indicator code.
 

```
...
#property indicator_plots   1

//Global variables
double haOpen [];
double haHigh [];
double haLow  [];
double haClose[];
double colorBuffer [];
...
```

 
Now that we've declared our arrays, the next step is to register each one of them as indicator buffers using the built-in MQL5 function SetIndexBuffer(). This function links our declared arrays to the indicator system so MetaTrader can use them for drawing and calculations. We'll do this inside the OnInit() function, registering each array one by one.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   
   // Registration of indicator buffers
   if(!SetIndexBuffer(0, haOpen, INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!SetIndexBuffer(1, haHigh, INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!SetIndexBuffer(2, haLow,   INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!SetIndexBuffer(3, haClose, INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!SetIndexBuffer(4, colorBuffer, INDICATOR_COLOR_INDEX)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
}

...
```

 
Next, let us set up the core logic of our indicator inside the OnCalculate() function. This function is called every time the indicator is updated. Whether it is when it is first attached to a chart, a new candle forms, or a new price tick arrives.
 
We typically structure this function into three main conditional blocks to handle each of those scenarios efficiently:
 
 
When the indicator is first attached to the chart, this is when prev_calculated == 0. We use this block to perform any initialization logic, like filling in historical values or setting up starting conditions.
 
When a new candle opens, this is when prev_calculated != rates_total and prev_calculated != 0. Here, you can perform logic that only needs to run once per new bar. It is useful for reducing repetitive calculations.
 
When a new price tick arrives on the current bar, this is when prev_calculated == rates_total. In this block, we update real-time values for the current candle using the latest price data.
 
 
Below is the basic structure we'll include in our OnCalculate() function:
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int32_t  rates_total,
                const int32_t  prev_calculated,
                const datetime &time[],
                const double   &open[],
                const double   &high[],
                const double   &low[],
                const double   &close[],
                const long     &tick_volume[],
                const long     &volume[],
                const int32_t  &spread[]) 
{
   // This block is executed when the indicator is initially attached on a chart
   if(prev_calculated == 0){
   }
   
   // This block is executed on every new bar open
   if(prev_calculated != rates_total && prev_calculated != 0){
   }
   
   // This block is executed on arrival of new price (tick) data
   if(prev_calculated == rates_total){
   }
   
   return(rates_total);
}

...
```

 
Next, we are going to define a color palette for our Heikin Ashi candles using the #property indicator_color1 directive. This directive allows us to specify the default colors for our graphical plot we defined earlier. For our indicators, we'll be using three colors:
 
 
clrDarkGreen for bullish Heikin Ashi candles.
 
clrDarkRed for bearish Heikin Ashi candles.
 
clrYellow for neutral candles.
 
 
We'll add this color setting just below our other #property directives so that it's applied during the indicator's initialization. Below is the line of code to add:
 

```
...
#property indicator_plots   1
#property indicator_color1 clrDarkGreen, clrDarkRed, clrYellow
...
```

 
We are now going to add a directive that gives descriptive names to each of our indicator buffers. This helps users understand what each line represents when viewing data from the Data Window in MetaTrader. Add the following line of code just below the existing #property directives:
 

```
...
#property indicator_color1 clrDarkGreen, clrDarkRed, clrYellow
#property indicator_label1 "HeikinAshiOpen;HeikinAshiHigh;HeikinAshiLow;HeikinAshiClose"
...
```

 
Before we implement the full logic inside the OnCalculate event handler, let's first define a few helper functions that will handle Heikin Ashi calculations and visual interpretation. These utility functions will:
 
 
Compute the Heikin Ashi (OHLC) values from regular price data.
 
Determine the visual direction (color) of each Heikin Ashi candle.
 
Separate full historical processing from real-time updates for efficiency.
 
 
Let us now add the following functions just below our OnCalculate() function. Once in place, we'll call them from within OnCalculate as needed, one step at a time.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int32_t  rates_total,
                const int32_t  prev_calculated,
                const datetime &time       [],
                const double   &open       [],
                const double   &high       [],
                const double   &low        [],
                const double   &close      [],
                const long     &tick_volume[],
                const long     &volume     [],
                const int32_t  &spread     []) 
{
   ...
    
   return(rates_total);
}

// Utility functions

//+----------------------------------------------------------------------------------+
//| Calculates Heikin Ashi values for all historical candles using price data arrays.|
//+----------------------------------------------------------------------------------+
void GetHeikinAshiValues(const double &open[], const double &high[], const double &low[], const double &close[], const int32_t rates_total)
{ 

   if(ArraySize(open) < rates_total){
      return;
   }
    
   // Run a loop through all historical bars
   for(int i=0; i<rates_total; i++){      
      if(i == 0){
         haOpen [i] = (open[i] + close[i]) / 2.0;
         haClose[i] = (open[i] + high[i] + low[i] + close[i]) / 4.0;
         haHigh [i] = MathMax(high[i], MathMax(open[i], close[i]));
         haLow  [i] = MathMin(low [i], MathMin(open[i], close[i]));
      }else{
         haOpen [i] = (haOpen[i-1] + haClose[i-1]) / 2.0;
         haClose[i] = (open[i] + high[i] + low[i] + close[i]) / 4.0;
         haHigh [i] = MathMax(high[i], MathMax(haOpen[i], haClose[i]));
         haLow  [i] = MathMin(low [i], MathMin(haOpen[i], haClose[i]));  
      }
   }
   
}


//+---------------------------------------------------------------------------------------+
//| Calculates Heikin Ashi values for the most recent candle only (for real-time updates).|
//+---------------------------------------------------------------------------------------+
void GetCurrentHeikinAshiValue(const double &open[], const double &high[], const double &low[], const double &close[], const int32_t rates_total)
{
   haOpen [rates_total - 1] = (haOpen[rates_total-2] + haClose[rates_total-2]) / 2.0;
   haClose[rates_total - 1] = (open[rates_total - 1] + high[rates_total - 1] + low[rates_total - 1] + close[rates_total - 1]) / 4.0;
   haHigh [rates_total - 1] = MathMax(high[rates_total - 1], MathMax(haOpen[rates_total - 1], haClose[rates_total - 1]));
   haLow  [rates_total - 1] = MathMin(low [rates_total - 1], MathMin(haOpen[rates_total - 1], haClose[rates_total - 1])); 
}


//+------------------------------------------------------------------------------------------------------------------+
//| Assigns a color code to each historical Heikin Ashi candle based on its direction (bullish, bearish, or neutral).|
//+------------------------------------------------------------------------------------------------------------------+
void GetHeikinAshiColors(const int32_t rates_total){
   
   for(int i=0; i<rates_total; i++){
      if(haOpen[i] < haClose[i]){
         colorBuffer[i] = 0;
      }
      
      else if(haOpen[i] > haClose[i]){
         colorBuffer[i] = 1;
      }
      
      else {
         colorBuffer[i] = 2;
      }
   }
   
}

//+-----------------------------------------------------------------------------------------------+
//| Assigns a color code to the latest Heikin Ashi candle only (used for real-time color updates).|
//+-----------------------------------------------------------------------------------------------+
void GetCurrentHeikinAshiColor(const int32_t rates_total){
      if(haOpen[rates_total - 1] < haClose[rates_total - 1]){
         colorBuffer[rates_total - 1] = 0;
      }
      
      else if(haOpen[rates_total - 1] > haClose[rates_total - 1]){
         colorBuffer[rates_total - 1] = 1;
      }
      
      else {
         colorBuffer[rates_total - 1] = 2;
      }
}

...

```

 
We'll now invoke the GetHeikinAshiValues() function inside the OnCalculate() event handler, specifically under the following conditions:
 
 
When prev_calculated == 0, meaning the indicator is loading for the first time and we need to process all historical candles.
 
When prev_calculated != rates_total and prev_calculated != 0, meaning new bars have been added or the chart has been refreshed, so we must recalculate from where we left off.
 
 
This function is responsible for calculating the entire series of Heikin Ashi candles, generating their open, high, low, and close values based on the standard price data arrays. It ensures that our buffers are accurately filled from the beginning or updated properly when new data comes in.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int32_t  rates_total,
                const int32_t  prev_calculated,
                const datetime &time       [],
                const double   &open       [],
                const double   &high       [],
                const double   &low        [],
                const double   &close      [],
                const long     &tick_volume[],
                const long     &volume     [],
                const int32_t  &spread     []) 
{
   // This block is executed when the indicator is initially attached on a chart
   if(prev_calculated == 0){
      GetHeikinAshiValues(open, high, low, close, rates_total);
   }
   
   // This block is executed on every new bar open
   if(prev_calculated != rates_total && prev_calculated != 0){
      GetHeikinAshiValues(open, high, low, close, rates_total);
   }
   
   // This block is executed on arrival of new price (tick) data
   if(prev_calculated == rates_total){
   }
   
   return(rates_total);
}

...
```

 
Next, we'll call the GetHeikinAshiColors() function inside the same conditional blocks within OnCalculate(). That is:
 
 
When prev_calculated == 0, color all historical candles during the initial load.
 
When prev_calculated != rates_total and prev_calculated != 0, refresh the colors for the updated data set.
 
 
This function assigns a numerical color code to each Heikin Ashi candle based on its relationship between open and close:
 
 
0 for bullish candles.
 
1 for bearish candles.
 
2 for neutral candles.
 
 
These color codes will later be mapped to actual visual colors on the chart, allowing us to visually differentiate between bullish, bearish, and neutral price action in the final indicator display.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int32_t  rates_total,
                const int32_t  prev_calculated,
                const datetime &time       [],
                const double   &open       [],
                const double   &high       [],
                const double   &low        [],
                const double   &close      [],
                const long     &tick_volume[],
                const long     &volume     [],
                const int32_t  &spread     []) 
{
   // This block is executed when the indicator is initially attached on a chart
   if(prev_calculated == 0){
      ...
      GetHeikinAshiColors(rates_total);
   }
   
   // This block is executed on every new bar open
   if(prev_calculated != rates_total && prev_calculated != 0){
      ...
      GetHeikinAshiColors(rates_total);
   }
   
   // This block is executed on arrival of new price (tick) data
   if(prev_calculated == rates_total){
   }
   
   return(rates_total);
}

...
```

 
Finally, we'll call the functions GetCurrentHeikinAshiValue() and GetCurrentHeikinAshiColor() inside the block if(prev_calculated == rates_total){}. This block executes when the indicator is updating in real time. That is, when a new tick arrives but no new candle has formed yet.
 
By calling:
 
 
GetCurrentHeikinAshiValue(), we ensure that the most recent Heikin Ashi values are recalculated for the current candle using the latest tick data.
 
GetCurrentHeikinAshiColor(), we immediately assign the corresponding color code for the most recent Heikin Ashi candle.
 
 
This setup keeps the indicator responsive and ensures the most recent candle is always visually accurate on the chart, even mid-formation.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int32_t  rates_total,
                const int32_t  prev_calculated,
                const datetime &time       [],
                const double   &open       [],
                const double   &high       [],
                const double   &low        [],
                const double   &close      [],
                const long     &tick_volume[],
                const long     &volume     [],
                const int32_t  &spread     []) 
{
   ...  
   
   // This block is executed on arrival of new price (tick) data
   if(prev_calculated == rates_total){
      GetCurrentHeikinAshiValue(open, high, low, close, rates_total);
      GetCurrentHeikinAshiColor(rates_total);
   }
   
   
   return(rates_total);
}

...
```

 
Now we are going to configure our graphic plot using the PlotIndexSetInteger() function one after the other so that our Heikin Ashi indicator displays when launched. We'll do this one setting at a time to define how our buffers will be rendered on the chart, including their drawing type.
 
These settings are essential for MetaTrader 5 terminal to understand how to plot the values we've calculated. Once we complete this step, our Heikin Ashi indicator will finally become visually active and display over the chart when applied. Let us walk through these configurations now. We'll begin by configuring our graphic plot by calling the PlotIndexSetInteger() function to set the drawing type. This particular line tells MetaTrader to render our plot using colored candlesticks. We'll place this just below our SetIndexBuffer() calls inside the OnInit() event handler. If this configuration fails, an error message will be printed in the expert's log for debugging purposes.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   ...
  
   if(!SetIndexBuffer(4, colorBuffer, INDICATOR_COLOR_INDEX)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   // Configuration of Graphic Plots
   if(!PlotIndexSetInteger(0, PLOT_DRAW_TYPE, DRAW_COLOR_CANDLES)){
      Print("Error while configuring graphic plots: ", GetLastError());
      return INIT_FAILED;
   }
   
}

...
```

 
Now, let us make sure that the Heikin Ashi data shows up in the data window when you hover over the chart with your mouse. We do this using PlotIndexSetInteger() with PLOT_SHOW_DATA set to true. This line should also go right after the last one inside the OnInit() function. If it doesn't work, it will print an error message.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   ...
   
   // Configuration of Graphic Plots
   if(!PlotIndexSetInteger(0, PLOT_DRAW_TYPE, DRAW_COLOR_CANDLES)){
      Print("Error while configuring graphic plots: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!PlotIndexSetInteger(0, PLOT_SHOW_DATA, true)){
      Print("Error while configuring graphic plots: ", GetLastError());
      return INIT_FAILED;
   }
   
}

...
```

 
Next, we are going to set up some general settings for the indicator. The first setting will define how many decimal places (digits) the indicator values should have, using IndicatorSetInteger() with INDICATOR_DIGITS. This helps ensure that the indicator's values match the symbol's precision. If something goes wrong, we print an error message to help with debugging.
 
Let us add the following lines of code below the PlotIndexSetInteger() functions in the OnInit() section.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   ...
   
   if(!PlotIndexSetInteger(0, PLOT_SHOW_DATA, true)){
      Print("Error while configuring graphic plots: ", GetLastError());
      return INIT_FAILED;
   }
   
   // Configure Indicator
   if(!IndicatorSetInteger(INDICATOR_DIGITS, Digits())){
      Print("Error while setting indicator values accuracy: ", GetLastError());
      return INIT_FAILED;
   }
   
}

...
```

 
Next, we'll give our indicator a short name using IndicatorSetString(). This name, "HeikinAshi," will appear in the data window and on the chart to help users easily identify the indicator. If the name fails to set, we'll print an error message to know what went wrong.
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   ...
   
   // Configure Indicator
   if(!IndicatorSetInteger(INDICATOR_DIGITS, Digits())){
      Print("Error while setting indicator values accuracy: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!IndicatorSetString(INDICATOR_SHORTNAME, "HeikinAshi")){
      Print("Error while setting indicator shortname: ", GetLastError());
      return INIT_FAILED;
   }
   
   return INIT_SUCCEEDED;
   
}

...
```

 
At this point, we've successfully written all the core components of our custom Heikin Ashi indicator. Now, go ahead and click the Compile button in MetaEditor. If everything was done correctly, the indicator should compile without errors and be ready for use on your chart. If you followed all the steps correctly, your full source should now look like this. In case something went wrong or you are getting compile errors, you can compare your code with the version below to find and correct any mistakes.
 

```
//+------------------------------------------------------------------+
//|                                          heikinAshiIndicator.mq5 |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                          https://www.mql5.com/en/users/chachaian |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, MetaQuotes Ltd."
#property link      "https://www.mql5.com/en/users/chachaian"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1
#property indicator_color1 C'38,166,154', C'239,83,80', clrYellow
#property indicator_label1 "HeikinAshiOpen;HeikinAshiHigh;HeikinAshiLow;HeikinAshiClose"

//Global variables
double haOpen      [];
double haHigh      [];
double haLow       [];
double haClose     [];
double colorBuffer [];

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{  
   //--- Registration of indicator buffers
   if(!SetIndexBuffer(0, haOpen, INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!SetIndexBuffer(1, haHigh, INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!SetIndexBuffer(2, haLow,   INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!SetIndexBuffer(3, haClose, INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!SetIndexBuffer(4, colorBuffer, INDICATOR_COLOR_INDEX)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
   
   //--- Configuration of graphic plots
   if(!PlotIndexSetInteger(0, PLOT_DRAW_TYPE, DRAW_COLOR_CANDLES)){
      Print("Error while configuring graphic plots: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!PlotIndexSetInteger(0, PLOT_SHOW_DATA, true)){
      Print("Error while configuring graphic plots: ", GetLastError());
      return INIT_FAILED;
   }
   
   //--- General indicator configurations
   if(!IndicatorSetInteger(INDICATOR_DIGITS, Digits())){
      Print("Error while setting indicator values accuracy: ", GetLastError());
      return INIT_FAILED;
   }
   
   if(!IndicatorSetString(INDICATOR_SHORTNAME, "HeikinAshi")){
      Print("Error while setting indicator shortname: ", GetLastError());
      return INIT_FAILED;
   }
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int32_t  rates_total,
                const int32_t  prev_calculated,
                const datetime &time       [],
                const double   &open       [],
                const double   &high       [],
                const double   &low        [],
                const double   &close      [],
                const long     &tick_volume[],
                const long     &volume     [],
                const int32_t  &spread     []) 
{
   //--- This block is executed when the indicator is initially attached on a chart
   if(prev_calculated == 0){
      GetHeikinAshiValues(open, high, low, close, rates_total);
      GetHeikinAshiColors(rates_total);
   }
   
   //--- This block is executed on every new bar open
   if(prev_calculated != rates_total && prev_calculated != 0){
      GetHeikinAshiValues(open, high, low, close, rates_total);
      GetHeikinAshiColors(rates_total);
   }
   
   //--- This block is executed on arrival of new price (tick) data
   if(prev_calculated == rates_total){
      GetCurrentHeikinAshiValue(open, high, low, close, rates_total);
      GetCurrentHeikinAshiColor(rates_total);
   }
   
   return(rates_total);
}

//--- Utility functions
//+----------------------------------------------------------------------------------+
//| Calculates Heikin Ashi values for all historical candles using price data arrays.|
//+----------------------------------------------------------------------------------+
void GetHeikinAshiValues(const double &open[], const double &high[], const double &low[], const double &close[], const int32_t rates_total)
{ 

   if(ArraySize(open) < rates_total){
      return;
   }
    
   //--- Run a loop through all historical bars
   for(int i=0; i<rates_total; i++){      
      if(i == 0){
         haOpen [i] = (open[i] + close[i]) / 2.0;
         haClose[i] = (open[i] + high[i] + low[i] + close[i]) / 4.0;
         haHigh [i] = MathMax(high[i], MathMax(open[i], close[i]));
         haLow  [i] = MathMin(low [i], MathMin(open[i], close[i]));
      }else{
         haOpen [i] = (haOpen[i-1] + haClose[i-1]) / 2.0;
         haClose[i] = (open[i] + high[i] + low[i] + close[i]) / 4.0;
         haHigh [i] = MathMax(high[i], MathMax(haOpen[i], haClose[i]));
         haLow  [i] = MathMin(low [i], MathMin(haOpen[i], haClose[i]));  
      }
   }
   
}

//+---------------------------------------------------------------------------------------+
//| Calculates Heikin Ashi values for the most recent candle only (for real-time updates).|
//+---------------------------------------------------------------------------------------+
void GetCurrentHeikinAshiValue(const double &open[], const double &high[], const double &low[], const double &close[], const int32_t rates_total)
{
   haOpen [rates_total - 1] = (haOpen[rates_total-2] + haClose[rates_total-2]) / 2.0;
   haClose[rates_total - 1] = (open[rates_total - 1] + high[rates_total - 1] + low[rates_total - 1] + close[rates_total - 1]) / 4.0;
   haHigh [rates_total - 1] = MathMax(high[rates_total - 1], MathMax(haOpen[rates_total - 1], haClose[rates_total - 1]));
   haLow  [rates_total - 1] = MathMin(low [rates_total - 1], MathMin(haOpen[rates_total - 1], haClose[rates_total - 1])); 
}


//+------------------------------------------------------------------------------------------------------------------+
//| Assigns a color code to each historical Heikin Ashi candle based on its direction (bullish, bearish, or neutral).|
//+------------------------------------------------------------------------------------------------------------------+
void GetHeikinAshiColors(const int32_t rates_total)
{
   
   for(int i=0; i<rates_total; i++){
      if(haOpen[i] < haClose[i]){
         colorBuffer[i] = 0;
      }
      
      if(haOpen[i] > haClose[i]){
         colorBuffer[i] = 1;
      }
      
      if(haOpen[i] == haClose[i]){
         colorBuffer[i] = 2;
      }
   }
   
}

//+-----------------------------------------------------------------------------------------------+
//| Assigns a color code to the latest Heikin Ashi candle only (used for real-time color updates).|
//+-----------------------------------------------------------------------------------------------+
void GetCurrentHeikinAshiColor(const int32_t rates_total)
{
      if(haOpen[rates_total - 1] < haClose[rates_total - 1]){
         colorBuffer[rates_total - 1] = 0;
      }
      
      else if(haOpen[rates_total - 1] > haClose[rates_total - 1]){
         colorBuffer[rates_total - 1] = 1;
      }
      
      else {
         colorBuffer[rates_total - 1] = 2;
      }
}
//+------------------------------------------------------------------+

```

 

### 

 

### Testing and visual tuning

 
Before we start visually testing the Heikin Ashi indicator, it is a good idea to clean up the chart so everything becomes easy to see. We'll define a small function that does just that. It adjusts the background, grid, and color settings to make the chart neat and candles clearly visible. Here is the code:
 

```
...

//+-----------------------------------------------------------------------------------------------+
//| Assigns a color code to the latest Heikin Ashi candle only (used for real-time color updates).|
//+-----------------------------------------------------------------------------------------------+ 
void GetCurrentHeikinAshiColor(const int32_t rates_total){
      if(haOpen[rates_total - 1] < haClose[rates_total - 1]){
         colorBuffer[rates_total - 1] = 0;
      }
      
      else if(haOpen[rates_total - 1] > haClose[rates_total - 1]){
         colorBuffer[rates_total - 1] = 1;
      }
      
      else {
         colorBuffer[rates_total - 1] = 2;
      }
}

//+-------------------------------------------------+
//| This function configures the chart's appearance.|
//+-------------------------------------------------+
bool ConfigureChartAppearance()
{
   if(!ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrWhite)){
      Print("Error while setting chart background, ", GetLastError());
      return false;
   }
   
   if(!ChartSetInteger(0, CHART_SHOW_GRID, false)){
      Print("Error while setting chart grid, ", GetLastError());
      return false;
   }
   
   if(!ChartSetInteger(0, CHART_MODE, CHART_LINE)){
      Print("Error while setting chart mode, ", GetLastError());
      return false;
   }

   if(!ChartSetInteger(0, CHART_COLOR_FOREGROUND, clrBlack)){
      Print("Error while setting chart foreground, ", GetLastError());
      return false;
   }
   
   return true;
}
```

 
Think of this function as your chart's personal stylist. It does the following:
 
 
Sets a white background for clarity.
 
Removes the grid so things look cleaner.
 
Changes the chart type to a line chart so it doesn't interfere with your custom candles.
 
Ensures that the foreground is black for good contrast.
 
 
If any of these actions fail, an error message is printed in the terminal for easy debugging. Let us now call the ConfigureChartAppearance() function inside the OnInit() event handler so it automatically adjusts the chart when the indicator is loaded. Here is how to do it:
 

```
...

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{

   if(!ConfigureChartAppearance()){
      Print("Error while configuring chart appearance: ", GetLastError());
      return INIT_FAILED;
   }
   
   // Registration of indicator buffers
   if(!SetIndexBuffer(0, haOpen, INDICATOR_DATA)){
      Print("Error while registering an indicator buffer: ", GetLastError());
      return INIT_FAILED;
   }
      
   ...
   
}

...
```

 
We have successfully completed building our custom Heikin Ashi Indicator. Everything is in place, from calculating the Heikin Ashi candles to drawing them cleanly on the chart with a well-configured appearance. Now it is time to attach the indicator to a chart and see it in action.
 
 
![gold 1hr chart](https://c.mql5.com/2/165/XAUUSDH1.png)
 
We have now attached our custom Heikin Ashi indicator to the gold H1 timeframe, and it works perfectly. Everything is displayed as expected, which means that our code is functioning correctly and the chart is ready for visual tuning and further testing.
 

### 

 

### Conclusion

 
In this part, we have successfully built a fully functional Heikin Ashi custom indicator in MQL5. We walked through each step, from setting up the buffers, calculating values, customizing chart appearance, and finally attached the indicator to the gold H1 timeframe chart. We have confirmed that everything works as expected. To help you follow along or troubleshoot, we have included both the full source code and the compiled version with this tutorial.
 
In the next part of this series, we'll go one step further and build an expert advisor that uses our Heikin Ashi indicator to make trading decisions. Stay tuned. 

Attached files
 |
  

[Download ZIP](/en/articles/download/19260.zip)

[heikinAshiIndicator.mq5](/en/articles/download/19260/heikinAshiIndicator.mq5)

(8.66 KB)

Warning:
 All rights to these materials are reserved by MetaQuotes Ltd. Copying or reprinting of these materials in whole or in part is prohibited.

This article was written by a user of the site and reflects their personal views. MetaQuotes Ltd is not responsible for the accuracy of the information presented, nor for any consequences resulting from the use of the solutions, strategies or recommendations described.

#### Other articles by this author

[Mastering Kagi Charts in MQL5 (Part I): Creating the Indicator](/en/articles/20239)

[Risk-Based Trade Placement EA with On-Chart UI (Part 2): Adding Interactivity and Logic](/en/articles/20159)

[Risk-Based Trade Placement EA with On-Chart UI (Part 1): Designing the User Interface](/en/articles/19932)

[Building a Smart Trade Manager in MQL5: Automate Break-Even, Trailing Stop, and Partial Close](/en/articles/19911)

[Building a Professional Trading System with Heikin Ashi (Part 2): Developing an EA](/en/articles/18810)

[Go to discussion](/en/forum/494952)

![Overcoming The Limitation of Machine Learning (Part 3): A Fresh Perspective on Irreducible Error](https://c.mql5.com/2/167/19371-overcoming-the-limitation-of-logo.png)

[Overcoming The Limitation of Machine Learning (Part 3): A Fresh Perspective on Irreducible Error](/en/articles/19371)

This article takes a fresh perspective on a hidden, geometric source of error that quietly shapes every prediction your models make. By rethinking how we measure and apply machine learning forecasts in trading, we reveal how this overlooked perspective can unlock sharper decisions, stronger returns, and a more intelligent way to work with models we thought we already understood.

![Trend strength and direction indicator on 3D bars](https://c.mql5.com/2/108/16719_logo.png)

[Trend strength and direction indicator on 3D bars](/en/articles/16719)

We will consider a new approach to market trend analysis based on three-dimensional visualization and tensor analysis of the market microstructure.

![Neural Networks in Trading: An Ensemble of Agents with Attention Mechanisms (MASAAT)](https://c.mql5.com/2/105/logo-neural-networks-made-easy-masaat.png)

[Neural Networks in Trading: An Ensemble of Agents with Attention Mechanisms (MASAAT)](/en/articles/16599)

We introduce the Multi-Agent Self-Adaptive Portfolio Optimization Framework (MASAAT), which combines attention mechanisms and time series analysis. MASAAT generates a set of agents that analyze price series and directional changes, enabling the identification of significant fluctuations in asset prices at different levels of detail.

![Price Action Analysis Toolkit Development (Part 38): Tick Buffer VWAP and Short-Window Imbalance Engine](https://c.mql5.com/2/166/19290-price-action-analysis-toolkit-logo.png)

[Price Action Analysis Toolkit Development (Part 38): Tick Buffer VWAP and Short-Window Imbalance Engine](/en/articles/19290)

In Part 38, we build a production-grade MT5 monitoring panel that converts raw ticks into actionable signals. The EA buffers tick data to compute tick-level VWAP, a short-window imbalance (flow) metric, and ATR-based position sizing. It then visualizes spread, ATR, and flow with low-flicker bars. The system calculates a suggested lot size and a 1R stop, and issues configurable alerts for tight spreads, strong flow, and edge conditions. Auto-trading is intentionally disabled; the focus remains on robust signal generation and a clean user experience.

![MQL5 - Language of trade strategies built-in the MetaTrader 5 client terminal](https://c.mql5.com/i/registerlandings/logo-2.png)

You are missing trading opportunities:

Free trading apps

Over 8,000 signals for copying

Economic news for exploring financial markets

Registration

Log in

latin characters without spaces

a password will be sent to this email


      An error occurred
    

[Log in With Google](https://www.mql5.com/en/auth_oauth2?provider=Google&amp;return=popup&amp;reg=1)


    You agree to 
[website policy](/en/about/privacy)
 and 
[terms of use](/en/about/terms)


    If you do not have an account, please 
[register](https://www.mql5.com/en/auth_register)

Allow the use of cookies to log in to the MQL5.com website.

Please enable the necessary setting in your browser, otherwise you will not be able to log in.

 

[Forgot your login/password?](https://www.mql5.com/en/auth_forgotten?return=popup)

[Log in With Google](https://www.mql5.com/en/auth_oauth2?provider=Google&amp;return=popup)

