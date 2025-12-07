---
title: "Introduction to MQL5 (Part 30): Mastering API and WebRequest Function in MQL5 (IV)"
original_url: "https://www.mql5.com/en/articles/20425"
phase: "phase1"
article_id: "20425"
date: "3 December 2025, 12:16"
---

# Introduction to MQL5 (Part 30): Mastering API and WebRequest Function in MQL5 (IV)



[](#pocket)

[](/en/articles/20425?print=)

![preview](assets/20425/5660f357bbf6c98a4b1b74cee5699329.jpeg)

![Introduction to MQL5 (Part 30): Mastering API and WebRequest Function in MQL5 (IV)](https://c.mql5.com/2/184/20425-introduction-to-mql5-part-30-mastering-api-and-webrequest-function_600x314.jpg)

# Introduction to MQL5 (Part 30): Mastering API and WebRequest Function in MQL5 (IV)

[MetaTrader 5](/en/articles/mt5)

          —
          
[Integration](/en/articles/mt5/integration)

        | 
3 December 2025, 12:16

![](https://c.mql5.com/i/icons.svg#views-usage)

          910
        

[![](https://c.mql5.com/i/icons.svg#comments-usage)2](/en/forum/501092)

![Israel Pelumi Abioye](https://c.mql5.com/avatar/2023/11/6554a830-8858.png)

[Israel Pelumi Abioye](/en/users/13467913)
 

### Introduction

Welcome back to Part 30 of the Introduction to MQL5 series! We continue our exploration of working with external APIs in MQL5 in this article, going beyond simple data extraction and basic requests. You've already seen how to submit a request, get a response, clean up the raw data, and divide the results into components that may be used. 
We obtained and processed the data for the past five daily candles in the previous article. We analyzed their composition, removed unnecessary characters, and split each candle into its individual elements. It's time to arrange the raw materials more effectively now that they have been clearly separated. 
You will learn how to organize comparable elements from various candles into their own dedicated arrays, rather than working with each candle individually. For instance, a single array will have all the opening times from each candle. The open prices, high prices, low prices, close prices, volumes, and any other candle components you like to examine will all be subject to the same analysis. Comparing numbers across days, identifying trends, performing computations, and preparing the data for indicators or trading logic are all made simpler by this methodical approach. After reading this article, you will have a clear and effective method for arranging API candle data, which will improve the readability, scalability, and readability of your MQL5 code and prepare it for more complex analysis.
   

### Grouping All Opening Times into a Single Array

We will start by combining all the opening times from the many candles into a single array. Previously, when we retrieved and cleaned the data from the API response, the opening time of each candle was stored separately. To make them easier to access and process, we now combine them into a single structured array rather than keeping them apart. We generate a correct timestamp sequence that corresponds to the candles' order by storing all opening times in a single array. Working with time-based computations, such as seeing patterns, calculating the intervals between candles, comparing dates, or coordinating the times with other candle elements like the open, high, low, or close prices, becomes considerably simpler as a result.
Every part in the array has its own index in arranging the elements of a particular candle. As an example, index 0 contains the first candle's opening time, index 1 contains the second candle's opening time, and so forth. Printing the array once everything has been stored enables you to visually verify that the times are accurately grouped and ordered. The basis for sorting the remaining candle data is laid by this straightforward yet crucial step. The open prices, high prices, low prices, closing prices, and volumes will all follow the same pattern following the opening timings. As you deal with more candles or more sophisticated techniques, your MQL5 scripts get easier to scale, your code becomes easier to understand, and your analysis becomes cleaner by grouping comparable data together.
Recall that we divided the server response into a daily candle string array and eliminated any unnecessary characters in the 
[previous part](/en/articles/20375)
. The comma was used as a delimiter to divide each candle's data into distinct elements. We haven't yet indicated which location within each split array corresponds to the opening time, though. Before we group anything, we must first determine that. 
The opening time consistently shows in the same location because all the candles in the dataset are arranged in the same arrangement. We may extract the opening time from each of the remaining candles in the same manner after verifying this location from the first candle. This enables us to compile all the opening times into a single, well-organized array that will be simple to access and utilize at a later time.
Example:

```
//DAY 1
string day1_data = candle_data[0];
StringReplace(day1_data,"[[","");
StringReplace(day1_data,"\"","");

string day1_data_array[];
StringSplit(day1_data,',',day1_data_array);
ArrayPrint(day1_data_array);
```

day1_data_array[]:

```
 1763424000000,              // opening time (0)
 92215.14000000,             // open price (1)
 93836.01000000,             // high price (2)
 89253.78000000,             // low price (3)
 92960.83000000,             // close price (4)
 39835.14769000,             // volume (5)
 1763510399999,              // closing time (6)
 3641033186.30045840,        // quote asset volume (7)
 8786593,                    // number of trades (8)
 20130.95957000,             // taker buy base asset volume (9)
 1841176605.14182350,        // taker buy quote asset volume (10)
 0                           // placeholder (11)

```

After examining the outcome of our split data, we can observe that the opening time is saved as the first member in the array. Which means, we may use the day one data array to get the first candle's opening time, which is at index 0.
Example:

```
Print(day1_data_array[0]);
```

![Figure 1. Time in Milliseconds](https://c.mql5.com/2/184/figure_1__1.png)
This value is located at index 0 of the array, as can be seen from the first element of the day one candle data. The output, which shows the precise instant the candle opened, is displayed in milliseconds. To put it another way, the number you see is the exact opening time of the candle and is a timestamp stated in milliseconds.  
It is presently not possible to use the opening time as an actual date and time in MQL5 since it is in string format. The string must first be converted into a suitable datetime type to operate with it correctly or store it alongside other candle opening timings. 
We first divide the time value given by the server by 1000 to convert it to seconds because it is measured in milliseconds. This change is crucial since MQL5 datetime's base format is seconds rather than milliseconds. Once it has been converted, we may save the outcome inside a datetime array, which enables us to do computations, compare opening times, or use the values for additional analysis.
Example: 

```
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
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
//  ArrayPrint(day1_data_array);

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
   long day1_time_s = (long)StringToInteger(day1_data_array[0])/1000;
   datetime day1_time = (datetime)day1_time_s;
   Print(day1_time);

//---
   return(INIT_SUCCEEDED);
  }
```

Output: 
![Figure 2. Date](https://c.mql5.com/2/184/figure_2__1.png)
Explanation: 
Since the opening time that was taken from the first element was initially in string format, it cannot be used directly in MQL5 operations. We turn it into a format that MQL5 accepts as a legitimate time after first converting it to a whole number. This conversion guarantees that the value may be processed, saved, and compared with other candle times without any problems. We store this number in a long integer variable after converting the milliseconds to seconds. We can securely handle huge numbers, which are typical when counting milliseconds over many years, thanks to the long integer.
This long integer is then converted to a datetime type. In this stage, the raw numerical value is converted into an appropriate date and time representation that MQL5 can understand. The value can be stored in an array of opening times or used for computations and comparisons once it is in datetime format. The second day will then follow the same process. We take the opening time from the second day's data, transform it from text into a useful time format, and save or show it, just like we did with the first candle. This guarantees that the opening time on the second day can be grouped with the other candles and adheres to the same structure.
Example:

```
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
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
//  ArrayPrint(day1_data_array);

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

   long day1_time_s = (long)StringToInteger(day1_data_array[0])/1000;
   datetime day1_time = (datetime)day1_time_s;

   long day2_time_s = (long)StringToInteger(day2_data_array[0])/1000;
   datetime day2_time = (datetime)day2_time_s;
   Print("DAY 1 TIME: ", day1_time,"\nDAY 2 TIME: ",day2_time);
//---
   return(INIT_SUCCEEDED);
  }
```

Output: 
![Figure 3. Day 1 and 2 Time](https://c.mql5.com/2/184/figure_3__1.png)
Explanation: 
Consider the string array's opening time as an extremely accurate clock that shows the time in milliseconds. It is difficult to read or understand as a standard time even though it measures time precisely, since the value is still merely a string of numbers. 
This string must first be transformed into a number. This is similar to realizing that the written stopwatch reading is a real number that you may use for calculations. Since most systems that handle dates and times operate in seconds rather than milliseconds since the Unix epoch, we divide the resultant value by 1000 to convert it from milliseconds to seconds. To fit within the clock system, it is comparable to turning minuscule fractions of a second into complete seconds. We convert the value to datetime after converting it to seconds. This phase marks the exact opening of the second daily candle and enables the system to understand the value as a definite moment.
The opening times are plainly visible in a human-readable format when we print the times for both the first and second days. This enables us to evaluate, compare, and utilize them in computations or indicators. The value gives us a precise timestamp for our project by representing the point on the chart where the candle officially began to form. 
It's time to apply the same process to the following three days now that we have a good understanding of how to convert and determine the opening time for the first two daily candles. We can precisely record the opening time for each candle by checking each string array for the corresponding daily candle, converting the first value from milliseconds to seconds, and then casting it to a datetime type. This guarantees that each of the five daily candle opening times is reliably recorded in the datetime format, preparing them for grouping into a single array for use in trading methods or additional analysis.
Example: 

```
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
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
//  ArrayPrint(day1_data_array);


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

   long day1_time_s = (long)StringToInteger(day1_data_array[0])/1000;
   datetime day1_time = (datetime)day1_time_s;

   long day2_time_s = (long)StringToInteger(day2_data_array[0])/1000;
   datetime day2_time = (datetime)day2_time_s;

   long day3_time_s = (long)StringToInteger(day3_data_array[0])/1000;
   datetime day3_time = (datetime)day3_time_s;

   long day4_time_s = (long)StringToInteger(day4_data_array[0])/1000;
   datetime day4_time = (datetime)day4_time_s;

   long day5_time_s = (long)StringToInteger(day5_data_array[0])/1000;
   datetime day5_time = (datetime)day5_time_s;

   Print("DAY 1 TIME: ", day1_time,"\nDAY 2 TIME: ",day2_time,"\nDAY 3 TIME: ",day3_time,"\nDAY 4 TIME: ",day4_time,"\nDAY 5 TIME: ",day5_time);

  }
```

Output: 
![Figure 4. Day 1 to 5 Time](https://c.mql5.com/2/184/figure_4.png)
By using the same process for the remaining three candles as we did for the first two, we were able to obtain all five opening times. The first array element of each day was cast into datetime after being transformed from a string to a long integer in seconds. As a result, a full set of opening times is produced, which may be verified by printing all five and then merging or examining them.
Each of the five daily candles' opening times has been successfully extracted. The next step is to create a datetime array so that our program can work with all of these opening times as a single collection.
Example:

```
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
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
 //  ArrayPrint(day1_data_array);
     
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
   
  long day1_time_s =  (long)StringToInteger(day1_data_array[0])/1000;
  datetime day1_time = (datetime)day1_time_s;
  
  long day2_time_s =  (long)StringToInteger(day2_data_array[0])/1000;
  datetime day2_time = (datetime)day2_time_s;
  
  long day3_time_s =  (long)StringToInteger(day3_data_array[0])/1000;
  datetime day3_time = (datetime)day3_time_s;
  
  long day4_time_s =  (long)StringToInteger(day4_data_array[0])/1000;
  datetime day4_time = (datetime)day4_time_s;
  
  long day5_time_s =  (long)StringToInteger(day5_data_array[0])/1000;
  datetime day5_time = (datetime)day5_time_s;
  
  datetime OpenTime[5] = {day1_time, day2_time, day3_time, day4_time, day5_time};
  ArrayPrint(OpenTime);
}

```

Output:
![Figure 5. ArrayPrint](https://c.mql5.com/2/184/Figure_5.png)
Explanation: 
A single array was created by combining the five daily candle opening periods. Instead of juggling several variables every day, this design gives us a single, well-organized container to deal with, enabling us to handle the data effectively. We used ArrayPrint (OpenTime) after defining the array. The complete array was printed by this function in the log window of MetaTrader. We were able to verify that the conversion procedure was effective and that each day's opening time had been correctly positioned inside the array by seeing all the saved datetime values.
An array can be displayed without depending on a single function. We may print each item independently by iterating through the array, and we can even alter the output for clarification. For a more straightforward summary, it is also possible to put all the values on one line. This flexibility gives us complete control over the array's presentation.
Example:

```
Print("DAY 1 TIME: ", OpenTime[0],"\nDAY 2 TIME: ",OpenTime[1],"\nDAY 3 TIME: ",OpenTime[2],"\nDAY 4 TIME: ",OpenTime[3],"\nDAY 5 TIME: ",OpenTime[4]);
```

From the first to the fifth day, each number in the array corresponds to the opening time of a certain candle. You can easily determine which opening time corresponds to which candle when they are shown separately. When you wish to examine or troubleshoot specific entries rather than viewing the entire set at once, this is helpful. 
   

### Grouping All Open Prices into a Single Array

We can observe from the daily data arrangement that the opening price is the element that appears immediately after the opening time in each string array. Therefore, we concentrated on determining each candle's opening price in this part. 
After locating the opening price by using the appropriate index in the string array, we transformed the string value into a double data type so that it could be utilized in MQL5 computations. After converting it, we obtained the opening pricing for each of the five candles by following the same procedure. This made it possible for us to consistently and cleanly extract the opening price for every day, prepping the data so that, as with the opening timings, we could compile all the information into a single array.

```
  1763424000000,       // opening time (0)
  92215.14000000,      // open price (1)
  93836.01000000,      // high price (2)
  89253.78000000,      // low price (3)
  92960.83000000,      // close price (4)
  39835.14769000,      // volume (5)
  1763510399999,       // closing time (6)
  3641033186.30045840, // quote asset volume (7)
  8786593,             // number of trades (8)
  20130.95957000,      // taker buy base asset volume (9)
  1841176605.14182350, // taker buy quote asset volume (10)
  0                    // placeholder (11)

```

Example: 

```
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
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
//  ArrayPrint(day1_data_array);

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

   long day1_time_s = (long)StringToInteger(day1_data_array[0])/1000;
   datetime day1_time = (datetime)day1_time_s;

   long day2_time_s = (long)StringToInteger(day2_data_array[0])/1000;
   datetime day2_time = (datetime)day2_time_s;

   long day3_time_s = (long)StringToInteger(day3_data_array[0])/1000;
   datetime day3_time = (datetime)day3_time_s;

   long day4_time_s = (long)StringToInteger(day4_data_array[0])/1000;
   datetime day4_time = (datetime)day4_time_s;

   long day5_time_s = (long)StringToInteger(day5_data_array[0])/1000;
   datetime day5_time = (datetime)day5_time_s;

   datetime OpenTime[5] = {day1_time, day2_time, day3_time, day4_time, day5_time};

// Opening Price Array
   double day1_open = StringToDouble(day1_data_array[1]);

//---
   return(INIT_SUCCEEDED);
  }
```

Explanation: 
We started by locating the opening price inside the day one data array. We verified that the opening price was kept in index 1 after looking at the daily candle data's structure. That made sense because the opening time was represented by index 0, and the opening price was logically represented by index 1. After determining the index, we transformed the string into a double data type. Since pricing values typically contain decimals and storing them as integers or strings would prevent correct calculations, we used double. The value was converted to double so that it could be used for mathematical operations like averages, comparisons, and additional analysis.
To better grasp this, picture the raw data we got from the API as written information. Like a number scribbled with a pen, the opening price was written in text. The computer interpreted it as text even though it appeared to be a number. We basically converted the number into a calculator using a conversion function so it could be utilized for actual computations. The value was changed from a straightforward text remark to a useful numerical number in that phase. We were able to record the correct double value in day1_open after this conversion, and we could then carry out the same procedure for the remaining candles. 
We chose to follow the identical process for the other four candles since we now knew how to determine and convert the opening price for the first candle. The strategy remained the same. All we did was stick to the same pattern as before. To ensure we were selecting the correct opening price for each of the other days, we first verified that each string array had the correct index. Similar to day one, day two, day three, day four, and day five opening prices also showed up in index 1 of their corresponding arrays. The value has to be changed from string format to double data type after the position was verified. Because price values typically include decimals, this conversion was crucial. For instance, if we wish to utilize a price like 1.08512 or 154.72 in calculations or to compare it with other prices, it must be recorded as double. MetaTrader would not handle it as a numerical value if we left it as a string.
The process can be compared to entering printed numbers into a calculator. The calculator can only operate with actual numerical values, even when the numbers on the paper appear to be valid. We were essentially prepping the values so that MQL5 could use them for calculations in the future by transforming each opening price from string to double.
Example:

```
// Opening Price Array
 double day1_open = StringToDouble(day1_data_array[1]);
 double day2_open = StringToDouble(day2_data_array[1]);
 double day3_open = StringToDouble(day3_data_array[1]);
 double day4_open = StringToDouble(day4_data_array[1]);
 double day5_open = StringToDouble(day4_data_array[1]);
 
 double OpenPrice[5] = {day1_open, day2_open, day3_open, day4_open, day5_open};
 
 Print("DAY 1 OPEN PRICE: ", OpenPrice[0],"\nDAY 2 OPEN PRICE: ",OpenPrice[1],"\nDAY 3 OPEN PRICE: "
  ,OpenPrice[2],"\nDAY 4 OPEN PRICE: ",OpenPrice[3],"\nDAY 5 OPEN PRICE: ",OpenPrice[4]);

```

Output: 
![Figure 6. Open Prices](https://c.mql5.com/2/183/figure_6.png)
Explanation: 
The open-price string from a particular day's data array is taken by each of the first four lines, which then transforms it into a decimal-precision numeric value and puts it in a double variable for that day. Prices must be converted from string to double because they contain decimal places and need to be handled as floating-point values to do calculations for arithmetic, comparisons, and indicators. Since the second element of each day's split data (index 1) was previously determined to represent the location of the open price in the candle structure, the conversion step reads it. 
The fifth conversion differs significantly from the other four in that it reads from day4_data_array once more, whereas the first four use each day's own data array to obtain the open price. In the absence of a correction, the fifth day's open price would be the same as the fourth day's. To ensure that each day's pricing originates from the appropriate element, you should check the source array for the fifth conversion and modify it to use the data array for the fifth day. 
All five prices are combined into a single array once the starting price of each day is transformed into a numerical number. It is simple to do computations, examine trends, or use them in indicators when they are all in one array. Compared to managing the prices as distinct text strings, it is more dependable and efficient. All five prices are gathered into a single array after the opening price for each day is transformed into a numerical value. Calculations, trend analysis, and indicator use are all made simple by having them in one array. It is more dependable and effective than treating the prices as distinct text strings.
Lastly, the open price for each day is displayed in a comprehensible fashion by printing each array element by index. You may quickly verify that every conversion and grouping was successful and that the data sequence matches your expectations by looking at that printout. Before using the source indices and array names in computations, make sure they are accurate.
   

### Grouping All Close Prices into a Single Array

We employ the same methodical process that we previously employed when dealing with the opening prices to extract the close prices from each daily candle. We already know the precise location of the close price within each array because the data for each candle is organized consistently. Because we don't have to guess or search through the elements, this predictable structure simplifies the extraction process. Rather, we just make reference to the proper place, knowing that every candle will follow the same pattern. As long as the data structure doesn't change, this consistency enables us to create dependable code that functions for any number of candles. 
The next step is to retrieve the value after determining which position within each day's data contains the close price. The data is still kept in the string array at this point as text. The number must be transformed into a numeric type before it can be utilized in computations, even though it appears to be a price. For MQL5 to handle the value as a real number, we must extract the value from the array and convert it to a double.
Calculations, comparisons, and other processing can be carried out without error when the close price is a double data type. Because MQL5 handles strings and numbers quite differently and the platform requires the correct data type before any mathematical operations can be applied, this conversion step is crucial. The next goal is to arrange them after each close price has been transformed into a useful figure. We combine the values into a single array that holds the close prices for each of the five days rather than dispersing them over several variables. We can access the data more easily and write cleaner code thanks to this design.
Not only that, but we can loop through the values, apply calculations, feed them into indicators, compare one day's close to another, and carry out any analysis that calls for structured data by storing them in an array. Because they enable us to manage several linked values as a single, well-organized entity rather than handling each item independently, arrays aid in streamlining our workflow. To ensure that everything was recorded accurately, we can print or display the near prices once the array has been built and filled. The effective extraction and conversion are confirmed by this crucial verification phase. It is also simpler to visually review the data and make sure there are no errors when all the close prices are displayed together.

```
 1763424000000,     // opening time (0)
 92215.14000000,    // open price (1)
 93836.01000000,    // high price (2)
 89253.78000000,    // low price (3)
 92960.83000000,    // close price (4)
 39835.14769000,    // volume (5)

```

This layout makes it evident that the close price is located in index 4, or the fifth element in the data array. We just find the index containing the close price, change the string value to a double, and store each result in a new array using the same methodical procedure. Because pricing values must be represented with a numeric data type that supports fractional amounts and contains decimals, converting to double is crucial. 
We combine the five days' close prices into a single array after determining each one. As with the opening prices, this enables us to work with all the close prices at once. This grouped data makes it simple to obtain the close price of any given day depending on the array index and utilize it for computations, comparisons, graphing, and other processing within our indicator or script.
Example:

```
// Opening Time Array
  long day1_time_s =  (long)StringToInteger(day1_data_array[0])/1000;
  datetime day1_time = (datetime)day1_time_s;
  
  long day2_time_s =  (long)StringToInteger(day2_data_array[0])/1000;
  datetime day2_time = (datetime)day2_time_s;
  
  long day3_time_s =  (long)StringToInteger(day3_data_array[0])/1000;
  datetime day3_time = (datetime)day3_time_s;
  
  long day4_time_s =  (long)StringToInteger(day4_data_array[0])/1000;
  datetime day4_time = (datetime)day4_time_s;
  
   long day5_time_s =  (long)StringToInteger(day5_data_array[0])/1000;
  datetime day5_time = (datetime)day5_time_s;
      
  datetime OpenTime[5] = {day1_time, day2_time, day3_time, day4_time, day5_time};
   
 // Opening Price Array
 double day1_open = StringToDouble(day1_data_array[1]);
 double day2_open = StringToDouble(day2_data_array[1]);
 double day3_open = StringToDouble(day3_data_array[1]);
 double day4_open = StringToDouble(day4_data_array[1]);
 double day5_open = StringToDouble(day4_data_array[1]);
 
 double OpenPrice[5] = {day1_open, day2_open, day3_open, day4_open, day5_open}; 

 // Closing Price Array
 double day1_close = StringToDouble(day1_data_array[4]);
 double day2_close = StringToDouble(day2_data_array[4]);
 double day3_close = StringToDouble(day3_data_array[4]);
 double day4_close = StringToDouble(day4_data_array[4]);
 double day5_close = StringToDouble(day4_data_array[4]);
 
 double ClosePrice[5] = {day1_close, day2_close, day3_close, day4_close, day5_close};
 Print("DAY 1 CLOSE PRICE: ", ClosePrice[0],"\nDAY 2 CLOSE PRICE: ",ClosePrice[1],"\nDAY 3 CLOSE PRICE: "
,ClosePrice[2],"\nDAY 4 CLOSE PRICE: ",ClosePrice[3],"\nDAY 5 CLOSE PRICE: ",ClosePrice[4]);

```

Output:
![Figure 7. Close Prices](https://c.mql5.com/2/183/Figure_7.png)
Explanation: 
Finding which index represents the closing price was the first step. It is evident by looking at the values' arrangement that the closing price is always in the same spot for each candle, enabling us to confidently extract it for every day. After confirming the closing price's position, each number had to be changed from a string to a numerical type that could be used in computations. Since activities like comparisons and computations require numeric values and the data received from the server is originally in string format, this translation is crucial. The same process was used for each of the five daily candles, converting each closing price into a numerical format.
A single array called ClosePrice was made to combine all the daily closing prices after each individual closing price was doubled. With the first element denoting the most current candle and the last element denoting the fifth candle in our series, this array keeps each day's closure in sequential order. This method of data organization makes it simple to get the closing price of any particular candle or conduct analysis over several candles. After each daily candle's closing price was found, it had to be converted from a string to a number that could be utilized in computations. To prevent problems brought on by string data, this phase ensures that all five closing prices are in a format that can be utilized for analysis, comparison, and additional processing.
   

### Grouping All High Prices into a Single Array

The goal of this section is to compile all the high prices from each daily candle into a single array. The first step is to determine which element in each candle array corresponds to the high price, much as we did with the opening and closing prices. We can identify the appropriate index that has the high price for each day by looking at the pattern of the candle data.

```
 1763424000000,     // opening time (0)
 92215.14000000,    // open price (1)
 93836.01000000,    // high price (2)
 89253.78000000,    // low price (3)
 92960.83000000,    // close price (4)
 39835.14769000,    // volume (5)

```

After identifying the index, we will translate each high price from a string to a number. Because prices frequently contain decimals and numerical data is required for calculations or comparisons, this conversion is required. Once all the high prices have been converted, we will combine these values into a single array, each of which will represent the top price of a particular daily candle. It will be simpler to assess trends, compare values across many candles, and use the data for indicators or trading methods if the high prices are arranged into a single array. To ensure a uniform approach to processing candle data, this procedure will be similar to what we did with the opening and closing prices.
Example: 

```
// High Price Array
 double day1_high = StringToDouble(day1_data_array[2]);
 double day2_high = StringToDouble(day2_data_array[2]);
 double day3_high = StringToDouble(day3_data_array[2]);
 double day4_high = StringToDouble(day4_data_array[2]);
 double day5_high = StringToDouble(day4_data_array[2]);
 
 double HighPrice[5] = {day1_high, day2_high, day3_high, day4_high, day5_high};

```

Explanation: 
Here, we are creating a single array that contains all the top prices from each daily candle. Finding the element in each day's string array that best symbolizes the high price is the first stage. The third element in each daily candle array, index 2, is where the high price is located, according to our analysis of the data. 
We transform the string value at this point into a double data type for every day. Price values frequently contain decimals; thus, saving them as numerical values enables us to do computations, comparisons, or analyzes at a later time. For instance, the first day's candle array's third member is converted to a double to generate day1_high. This process is repeated for the following four days. 
We combined the values from all five days into a single array after converting the high prices for each day. It is simple to access, evaluate, or change the high prices across several candles in an organized manner because each point in the array represents the peak price of a particular day. 
   

### Grouping All Low Prices into a Single Array

Putting all the low prices into a single array is the next stage in arranging our candle data. We start by locating the low price in each daily candle array, just as we did with the high and open prices. The low price is at index 3, which is the fourth element in each candle's array, according to the data. 
We will change the low price from a string to a double data type for each day. This guarantees the values' suitability for computations, comparisons, and additional analysis. After conversion, we combine all five daily candles' low prices into a single array. This array makes it simple to retrieve and interact with individual low prices because each index represents a certain day. We now have a structured system where each candle component is arranged into a separate array by grouping the low prices in this manner. In addition to making data management easier, this method gets the candle data ready for any analysis, indicators, or trading methods we may wish to use.
Example:

```
// Low Price Array

 double day1_low = StringToDouble(day1_data_array[3]);
 double day2_low = StringToDouble(day2_data_array[3]);
 double day3_low = StringToDouble(day3_data_array[3]);
 double day4_low = StringToDouble(day4_data_array[3]);
 double day5_low = StringToDouble(day4_data_array[3]);


  double LowPrice[5] = {day1_low, day2_low, day3_low, day4_low, day5_low};
```

Explanation: 
We recorded the low prices for each of the five days in a single array after converting the values from strings to doubles and taking the low price from the candle data for each day. Printing the array confirms that the values are prepared and ordered correctly for use in indicators, strategies, or an expert advisor. A certain day is associated with each slot.                                                                                                         

### Conclusion

In this article, we successfully took the next step in organizing API candle data by grouping similar elements from multiple daily candles into dedicated arrays. . Each candle's opening times, open prices, high prices, low prices, and closure prices were retrieved, transformed, and stored in structured arrays. Accessing particular data points, carrying out computations, and utilizing the data in indications or Expert Advisors are all made simpler with this method. By the time you finish reading this post, you will have a clear and effective method for managing several candles in MQL5, setting the stage for more sophisticated analysis and trading strategy automation.

Attached files
 |
  

[Download ZIP](/en/articles/download/20425.zip)

[Project_21_API_and_WebRequest_B.mq5](/en/articles/download/20425/Project_21_API_and_WebRequest_B.mq5)

(6.26 KB)

Warning:
 All rights to these materials are reserved by MetaQuotes Ltd. Copying or reprinting of these materials in whole or in part is prohibited.

This article was written by a user of the site and reflects their personal views. MetaQuotes Ltd is not responsible for the accuracy of the information presented, nor for any consequences resulting from the use of the solutions, strategies or recommendations described.

#### Other articles by this author

[Introduction to MQL5 (Part 29): Mastering API and WebRequest Function in MQL5 (III)](/en/articles/20375)

[Introduction to MQL5 (Part 28): Mastering API and WebRequest Function in MQL5 (II)](/en/articles/20280)

[Introduction to MQL5 (Part 27): Mastering API and WebRequest Function in MQL5](/en/articles/17774)

[Introduction to MQL5 (Part 26): Building an EA Using Support and Resistance Zones](/en/articles/20021)

[Introduction to MQL5 (Part 25): Building an EA that Trades with Chart Objects (II)](/en/articles/19968)

[Introduction to MQL5 (Part 24): Building an EA that Trades with Chart Objects](/en/articles/19912)


         Last comments |
 
[Go to discussion](/en/forum/501092)


        (2)
    

![Jiang Huang](https://c.mql5.com/avatar/avatar_na2.png)

[Jiang Huang](/en/users/wild-child)

              |
              
4 Dec 2025 at 11:49

[]()

I like your WebRequest series. May I ask how to use it for backtesting and live trading? Using 
[custom symbols](https://www.mql5.com/en/articles/3540)
?

![Israel Pelumi Abioye](https://c.mql5.com/avatar/2023/11/6554a830-8858.png)

[Israel Pelumi Abioye](/en/users/13467913)

              |
              
4 Dec 2025 at 14:27

[]()

Jiang Huang 
[#](/en/forum/501092#comment_58655043)
:
 
I like your WebRequest series. May I ask how to use it for backtesting and live trading? Using 
[custom symbols](https://www.mql5.com/en/articles/3540)
?
 
Thank you. Watch out for the next article 
            

![Developing a Trading Strategy: Using a Volume-Bound Approach](https://c.mql5.com/2/184/20469-developing-a-trading-strategy-logo__1.png)

[Developing a Trading Strategy: Using a Volume-Bound Approach](/en/articles/20469)

In the world of technical analysis, price often takes center stage. Traders meticulously map out support, resistance, and patterns, yet frequently ignore the critical force that drives these movements: volume. This article delves into a novel approach to volume analysis: the Volume Boundary indicator. This transformation, utilizing sophisticated smoothing functions like the butterfly and triple sine curves, allows for clearer interpretation and the development of systematic trading strategies.

![Automating Trading Strategies in MQL5 (Part 44): Change of Character (CHoCH) Detection with Swing High/Low Breaks](https://c.mql5.com/2/184/20355-automating-trading-strategies-logo.png)

[Automating Trading Strategies in MQL5 (Part 44): Change of Character (CHoCH) Detection with Swing High/Low Breaks](/en/articles/20355)

In this article, we develop a Change of Character (CHoCH) detection system in MQL5 that identifies swing highs and lows over a user-defined bar length, labels them as HH/LH for highs or LL/HL for lows to determine trend direction, and triggers trades on breaks of these swing points, indicating a potential reversal, and trades the breaks when the structure changes.

![Capital management in trading and the trader's home accounting program with a database](https://c.mql5.com/2/123/Capital_Management_in_Trading_and_Home_Accounting_Program_for_Traders_with_Database_LOGO-3.png)

[Capital management in trading and the trader's home accounting program with a database](/en/articles/17282)

How can a trader manage capital? How can a trader and investor keep track of expenses, income, assets, and liabilities? I am not just going to introduce you to accounting software; I am going to show you a tool that might become your reliable financial navigator in the stormy sea of trading.

![Neural Networks in Trading: Multi-Task Learning Based on the ResNeXt Model](https://c.mql5.com/2/117/Neural_Networks_in_Trading_Multi-Task_Learning_Based_on_the_ResNeXt_Model__LOGO.png)

[Neural Networks in Trading: Multi-Task Learning Based on the ResNeXt Model](/en/articles/17142)

A multi-task learning framework based on ResNeXt optimizes the analysis of financial data, taking into account its high dimensionality, nonlinearity, and time dependencies. The use of group convolution and specialized heads allows the model to effectively extract key features from the input data.

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

