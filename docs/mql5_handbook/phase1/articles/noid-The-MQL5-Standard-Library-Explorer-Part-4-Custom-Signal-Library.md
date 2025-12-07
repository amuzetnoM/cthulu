---
title: "The MQL5 Standard Library Explorer (Part 4): Custom Signal Library"
original_url: "https://www.mql5.com/en/articles/20266"
phase: "phase1"
date: "27 November 2025, 10:25"
---

# The MQL5 Standard Library Explorer (Part 4): Custom Signal Library



[](#pocket)

[](/en/articles/20266?print=)

![preview](assets/The-MQL5-Standard-Library-Explorer-Part-4-Custom-Signal-Library/86b06a99d6f81dff20a761f9174437c0.jpeg)

![The MQL5 Standard Library Explorer (Part 4): Custom Signal Library](https://c.mql5.com/2/183/20266-the-mql5-standard-library-explorer-part-4-custom-signal-library_600x314__2.jpg)

# The MQL5 Standard Library Explorer (Part 4): Custom Signal Library

[MetaTrader 5](/en/articles/mt5)

          —
          
[Examples](/en/articles/mt5/examples)

        | 
27 November 2025, 10:25

![](https://c.mql5.com/i/icons.svg#views-white-usage)

          1 287
        

[![](https://c.mql5.com/i/icons.svg#comments-white-usage)0](/en/forum/500823)

![Clemence Benjamin](https://c.mql5.com/avatar/2025/3/67df27c6-2936.png)

[Clemence Benjamin](/en/users/billionaire2024)
 

### Contents

[Introduction](/en/articles/20266#para2)
[Implementation](/en/articles/20266#para3)
[Testing](/en/articles/20266#para4)
[Conclusion](/en/articles/20266#para5)

### Introduction

The development of sophisticated Expert Advisors is achievable through the 
[MQL5 Wizard](/en/book/intro/mql_wizard)
 even with limited programming experience. The default Signal library contains numerous pre-built signals that can be optimized to produce exceptional trading performance. In this comprehensive exploration, we embarked on creating custom signals to transform trading ideas into fully functional Expert Advisors compatible with the MQL5 Wizard framework. This article documents our journey from initial concept to final implementation, highlighting the challenges, solutions, and valuable insights gained throughout the process.
The MQL5 Wizard Advantage
The MQL5 Wizard represents a paradigm shift in algorithmic trading development, offering several key benefits:
1. Rapid Prototyping Capabilities
Accelerated Development: Generate complete Expert Advisors in minutes rather than weeks.
Standardized Architecture: Ensure code consistency and maintainability
Modular Design: Easily swap and combine different trading components
Built-in Risk Management: Integrate professional money management from inception.
2. Pre-Optimized Components
The Wizard provides access to extensively tested modules, including:
multiple signal generation systems
various trailing stop mechanisms,
diverse money management strategies,
comprehensive risk management protocols.
Thinking more deeply about this topic, I decided to compile a table showing how two different types of developers can benefit from the MQL5 Wizard. See the table below.
Benefits of MQL5 Wizard and Signal Library for Different Developer Types
#
Developer with Zero Programming Knowledge
Developer with Good Programming Skills
1
Instant EA Creation
Generate complete Expert Advisors in minutes without writing any code through intuitive point-and-click interface
Rapid Prototyping
Quickly test trading ideas by generating complete EA framework, then customize and extend with advanced programming
2
Pre-Built Signal Library
Access dozens of professionally-coded technical indicators and trading strategies without understanding implementation details
Extensible Architecture
Leverage well-designed base classes and interfaces to create custom signals while maintaining compatibility with Wizard framework
3
Built-in Risk Management
Automatically integrate professional money management, trailing stops, and position sizing without coding expertise
Code Generation & Standards
Generate boilerplate code following MQL5 best practices, reducing development time and ensuring code quality
4
Visual Strategy Builder
Combine multiple signals with drag-and-drop simplicity and immediately see parameter effects on strategy performance
Modular Component System
Create reusable signal modules that can be easily shared, tested, and combined in different strategy configurations
5
Error-Free Implementation
Avoid common programming mistakes with pre-tested, validated trading components and automatic error handling
Advanced Debugging Framework
Utilize built-in debugging capabilities and standardized logging to quickly identify and resolve issues.
6
Learning Platform
Study generated code to understand proper EA structure and gradually learn MQL5 programming concepts
Testing Infrastructure
Access comprehensive back-testing and optimization tools with minimal setup time for strategy validation
7
Parameter Optimization
Easily optimize trading strategies through visual interface without understanding complex optimization algorithms
Performance Benchmarking
Compare custom signals against built-in library using standardized testing protocols and metrics
8
Strategy Validation
Quickly test multiple signal combinations and filter settings to find profitable configurations through systematic exploration
Custom Integration Points
Extend Wizard functionality by hooking into initialization, tick processing, and trade execution events
Conceptualizing Custom Signals
The default signal list is mainly built from the terminal’s standard indicators. In today’s project, we want to go the extra mile. Most traders are already familiar with candlestick names and patterns, so it becomes easier to grasp the concepts we are about to use. Our task is to build a signal class based on candlestick patterns, with the goal of detecting specific price action formations and generating trading signals accordingly. After creating this class, we will integrate it into an Expert Advisor using the MQL5 Wizard, then study the generated code and its behavior in the Strategy Tester. Successful trading systems often combine multiple confirmation factors rather than relying on a single indicator, and this approach takes us closer to that ideal.
![List of available signal](https://c.mql5.com/2/183/MetaEditor64_rD8aZwlaip.png)
List of available signal modules

### Implementation

Creating Custom Signals for MQL5 Wizard
Our implementation journey followed a logical progression, but we encountered a critical hurdle right from the start. When I created my first custom signal class, it compiled successfully but didn't appear in the MQL5 Wizard's list of available signals for selection. This required specific adjustments to make the signal visible and selectable alongside the pre-built options.
The Class Structure
When creating custom trading signals for the MQL5 Wizard, we start by establishing the fundamental class structure that forms the backbone of our candlestick pattern recognition system. This class inherits from the powerful 
[CExpertSignal](/en/docs/standardlibrary/expertclasses/expertbaseclasses/cexpertsignal)
 base class, which provides all the essential functionality needed to integrate with the MQL5 Wizard framework. Think of this as building upon a proven foundation—we get all the sophisticated signal processing capabilities while focusing our efforts on the unique candlestick pattern logic that makes our trading strategy special.

```
//+------------------------------------------------------------------+
//| MyCandlePatternSignal.mqh                                        |
//| Custom Signal based on Candlestick Patterns                      |
//+------------------------------------------------------------------+
#include <Expert\ExpertSignal.mqh>
//+------------------------------------------------------------------+
//| Class CMyCandlePatternSignal                                     |
//+------------------------------------------------------------------+
class CMyCandlePatternSignal : public CExpertSignal
{
```

Notice how we include ExpertSignal.mqh—this is absolutely crucial because it provides the base class functionality that the MQL5 Wizard expects. Without this include, our class wouldn't compile properly, much less work within the Wizard framework.
Designing Your Trading Parameters: Member Variables
Every successful trading system needs configurable parameters, and our candlestick signal class is no exception. We declare two types of member variables: pattern weights that determine how strongly each candlestick formation influences our trading decisions, and detection parameters that fine-tune how we identify these patterns in market data. This separation allows traders to adjust both the sensitivity of pattern detection and the confidence level of each signal independently.

```
protected:
   //--- Pattern weights
   int               m_pattern_doji;        // Doji pattern weight
   int               m_pattern_engulfing;   // Engulfing pattern weight  
   int               m_pattern_hammer;      // Hammer/Hanging man weight
   int               m_pattern_morning_star;// Morning/Evening star weight
   
   //--- Detection parameters
   double            m_doji_threshold;      // Doji body threshold
   double            m_engulfing_ratio;     // Engulfing size ratio
```

The protected access modifier ensures these variables are accessible within our class hierarchy but hidden from external code, maintaining good object-oriented design principles while keeping our trading logic secure.
Creating the Control Panel: Public Interface Methods
To make our signal configurable within the MQL5 Wizard, we need to provide public methods that allow traders to adjust our parameters. These setter methods act as the control panel for our trading signal—each one corresponds to an input parameter that will appear in the Expert Advisor's settings when generated by the Wizard. The beauty of this design is that we're building a user-friendly interface without any extra GUI programming!

```
public:
   //--- Constructor
                     CMyCandlePatternSignal(void);
   
   //--- Methods for setting parameters
   void              PatternDoji(int value)        { m_pattern_doji=value; }
   void              PatternEngulfing(int value)   { m_pattern_engulfing=value; }
   void              PatternHammer(int value)      { m_pattern_hammer=value; }
   void              PatternMorningStar(int value) { m_pattern_morning_star=value; }
   void              DojiThreshold(double value)   { m_doji_threshold=value; }
   void              EngulfingRatio(double value)  { m_engulfing_ratio=value; }
```

These inline setter methods are efficient and straightforward—they directly assign values to our member variables. When the MQL5 Wizard generates an Expert Advisor from our signal, it will automatically create input parameters that call these methods.
Defining the Brain of Our System: Core Functionality
The protected section of our class declaration is where we define the core intelligence of our trading signal. Here we declare the pattern detection methods that identify specific candlestick formations and the crucial signal generation methods that the MQL5 Wizard calls to make trading decisions. This is where our unique trading logic lives—the methods that transform raw price data into actionable trading signals.

```
protected:
   //--- Candlestick pattern detection methods
   bool              IsDoji(int idx);
   bool              IsBullishEngulfing(int idx);
   bool              IsBearishEngulfing(int idx);
   bool              IsHammer(int idx);
   bool              IsShootingStar(int idx);
   bool              IsMorningStar(int idx);
   bool              IsEveningStar(int idx);
   
   //--- Main signal generation methods
   virtual int       LongCondition(void);
   virtual int       ShortCondition(void);
};
```

The virtual keyword before LongCondition() and ShortCondition() indicates that we're overriding methods from the base CExpertSignal class. These are the methods the MQL5 Wizard framework calls to determine when to enter long and short positions.
Setting Up Default Values: The Constructor
Every class needs proper initialization, and our constructor is where we set sensible default values for all our trading parameters. This initialization list ensures our signal starts with reasonable settings that have proven effective for candlestick pattern trading. The m_used_series assignment is particularly important—it tells the framework which price data we need access to for our calculations.

```
//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CMyCandlePatternSignal::CMyCandlePatternSignal(void) : 
   m_pattern_doji(60),
   m_pattern_engulfing(80),
   m_pattern_hammer(70),
   m_pattern_morning_star(90),
   m_doji_threshold(0.1),
   m_engulfing_ratio(1.5)
{
   m_used_series=USE_SERIES_OPEN+USE_SERIES_HIGH+USE_SERIES_LOW+USE_SERIES_CLOSE;
}
```

The m_used_series assignment is absolutely vital—without it, our signal won't have access to the Open, High, Low, and Close price data needed for candlestick analysis. This is a common oversight that can lead to confusing errors when the signal tries to access price data that hasn't been initialized.
Implementing Pattern Recognition: Doji Detection
The doji pattern represents market indecision, occurring when the opening and closing prices are virtually equal. Our detection method calculates the candle's body size relative to its total range, using a configurable threshold to determine what constitutes a "small" body. This mathematical approach ensures consistent pattern recognition across different instruments and market conditions.

```
//+------------------------------------------------------------------+
//| Check if candle is Doji                                          |
//+------------------------------------------------------------------+
bool CMyCandlePatternSignal::IsDoji(int idx)
{
   double open = m_open.GetData(idx);
   double close = m_close.GetData(idx);
   double high = m_high.GetData(idx);
   double low = m_low.GetData(idx);
   
   double body_size = MathAbs(close - open);
   double range = high - low;
   
   // Doji: very small body relative to range
   if(range > 0 && body_size <= range * m_doji_threshold)
      return true;
   
   return false;
}
```

Notice how we use m_doji_threshold to make our detection adaptive. A value of 0.1 means the body must be 10% or less of the total candle range. This parameter allows traders to adjust sensitivity based on market volatility—lower values for more precise doji detection, higher values for more frequent signals.
Capturing Market Reversals: Engulfing Patterns
Engulfing patterns are powerful reversal signals that occur when a candle completely "engulfs" the previous candle's body. Our implementation carefully checks multiple conditions: the direction of both candles, the engulfing relationship, and the size difference using our configurable ratio. This multi-layered verification ensures we only identify high-quality engulfing patterns.

```
//+------------------------------------------------------------------+
//| Check for Bullish Engulfing pattern                              |
//+------------------------------------------------------------------+
bool CMyCandlePatternSignal::IsBullishEngulfing(int idx)
{
   double prev_open = m_open.GetData(idx+1);
   double prev_close = m_close.GetData(idx+1);
   double curr_open = m_open.GetData(idx);
   double curr_close = m_close.GetData(idx);
   
   // Previous candle must be bearish
   if(prev_close >= prev_open) return false;
   
   // Current candle must be bullish
   if(curr_close <= curr_open) return false;
   
   // Current body must engulf previous body
   if(curr_open < prev_close && curr_close > prev_open)
   {
      double prev_body = MathAbs(prev_close - prev_open);
      double curr_body = MathAbs(curr_close - curr_open);
      
      // Current body should be significantly larger
      if(curr_body >= prev_body * m_engulfing_ratio)
         return true;
   }
   
   return false;
}
```

The engulfing pattern represents a dramatic shift in market sentiment. The previous candle shows one side in control, but the engulfing candle demonstrates the opposite side overwhelming them. Our m_engulfing_ratio parameter ensures the new momentum is strong enough to be significant.
Identifying Precision Tools: Hammer and Shooting Star
Hammer and Shooting Star patterns are excellent for pinpointing potential reversal points. These patterns have small bodies with long shadows, indicating rejection of higher or lower prices. Our implementation uses precise ratios to distinguish genuine reversal patterns from ordinary candles with extended wicks.

```
//+------------------------------------------------------------------+
//| Check for Hammer pattern (bullish reversal)                      |
//+------------------------------------------------------------------+
bool CMyCandlePatternSignal::IsHammer(int idx)
{
   double open = m_open.GetData(idx);
   double close = m_close.GetData(idx);
   double high = m_high.GetData(idx);
   double low = m_low.GetData(idx);
   
   double body_size = MathAbs(close - open);
   double lower_shadow = MathMin(open, close) - low;
   double upper_shadow = high - MathMax(open, close);
   double range = high - low;
   
   if(range <= 0) return false;
   
   // Hammer: small body, long lower shadow, little to no upper shadow
   bool is_small_body = body_size <= range * 0.3;
   bool is_long_lower_shadow = lower_shadow >= body_size * 2.0;
   bool is_small_upper_shadow = upper_shadow <= body_size * 0.5;
   
   return (is_small_body && is_long_lower_shadow && is_small_upper_shadow);
}
```

The hammer pattern tells a story of sellers pushing prices lower during the period, but buyers recovering most of the losses by the close. This creates a long lower shadow that indicates potential bullish reversal. Our three-condition check ensures we only identify high-probability hammer formations.
Making Trading Decisions: Signal Generation
The LongCondition() and ShortCondition() methods are where everything comes together—these are the decision-making engines that the MQL5 Wizard calls to generate actual trading signals. Using a weighted voting system, each pattern contributes its confidence level to the final decision, with the total needing to exceed the Wizard's threshold for a trade to execute.

```
//+------------------------------------------------------------------+
//| "Long" condition (BUY signals)                                   |
//+------------------------------------------------------------------+
int CMyCandlePatternSignal::LongCondition(void)
{
   int result=0;
   int idx=StartIndex();
   
   //--- Pattern 0: Bullish Engulfing
   if(IsBullishEngulfing(idx))
   {
      if(IS_PATTERN_USAGE(0))
         result += m_pattern_engulfing;
   }
   
   //--- Pattern 1: Hammer
   if(IsHammer(idx))
   {
      if(IS_PATTERN_USAGE(1))
         result += m_pattern_hammer;
   }
   
   //--- Pattern 2: Doji at support (potential reversal)
   if(IsDoji(idx))
   {
      // You could add additional logic here to check if at support
      if(IS_PATTERN_USAGE(2))
         result += m_pattern_doji;
   }
   
   return(result);
}
```

The IS_PATTERN_USAGE() macro is incredibly powerful—it allows traders to enable or disable individual patterns without changing the code. This means our signal can adapt to different market conditions by focusing on the most relevant patterns for the current environment.
Why Our Signal Remained Hidden
Despite having a perfectly functional and well-structured candlestick pattern recognition class, you might have encountered a frustrating reality: it doesn't appear in the MQL5 Wizard's signal selection list. This happens because the Wizard doesn't automatically scan for any class that inherits from CExpertSignal—it specifically looks for classes with a special identification header.
The MQL5 Wizard uses a metadata system to identify available signals. Without the proper wizard description header, our class is like an unlisted phone number—functionally complete but impossible to find through normal channels. The Wizard needs explicit instructions about how to display our signal, what parameters to expose, and how to integrate it into the Expert Advisor generation process.
In the next section, we'll transform our invisible signal into a fully integrated Wizard component by adding the crucial metadata header that makes it discoverable and configurable within the MQL5 development environment. This small addition will bridge the gap between our sophisticated pattern recognition logic and the user-friendly Wizard interface that makes MQL5 development accessible to traders of all experience levels.
Unlocking Wizard Compatibility: The Secret Sauce for MQL5 Signal Integration
Wizard Description Header
Imagine you've built a sophisticated trading signal, but it's like having a luxury car with no keys—functionally perfect but unusable. The wizard description header is that set of keys that unlocks compatibility with the MQL5 Wizard. This special comment block acts as a handshake between your custom code and the wizard's interface, providing all the metadata needed to display, configure, and integrate your signal seamlessly.

```
// wizard description start
//+--------------------------------------------------------------------------------------------------------------+
//| Description of the class                                                                                     |
//| Title=Signals of candlestick patterns                                                                        |
//| Type=SignalAdvanced                                                                                          |
//| Name=Candlestick Patterns                                                                                    |
//| ShortName=Candle                                                                                             |
//| Class=CMyCandlePatternSignal                                                                                 |
//| Page=signal_candle_pattern                                                                                   |
//| Parameter=PatternDoji,int,60,Weight for Doji pattern                                                         |
//| Parameter=PatternEngulfing,int,80,Weight for Engulfing pattern                                               |
//| Parameter=PatternHammer,int,70,Weight for Hammer pattern                                                     |
//| Parameter=PatternMorningStar,int,90,Weight for Morning Star pattern                                          |
//| Parameter=DojiThreshold,double,0.1,Doji body threshold (relative to range)                                   |
//| Parameter=EngulfingRatio,double,1.5,Engulfing ratio (current body must be at least this times previous body) |
//+--------------------------------------------------------------------------------------------------------------+
// wizard description end
```

This isn't just any comment—it's a structured data format that the MQL5 Wizard actively scans for when populating its signal library. Without this exact format, your signal remains invisible no matter how well-coded it might be.
Understanding the Wizard Directives
Each directive in the wizard description serves a specific purpose, acting like fields on an identification card that the wizard uses to understand and categorize your signal. The title is what users see in the selection list, Type categorizes your signal for proper handling, while name and shortName become part of the generated expert advisor's code structure.

```
//| Title=Signals of candlestick patterns                            |
//| Type=SignalAdvanced                                              |
//| Name=Candlestick Patterns                                        |
//| ShortName=Candle                                                 |
//| Class=CMyCandlePatternSignal                                     |
```

The Type=SignalAdvanced directive is crucial—it tells the Wizard that this is a sophisticated signal using the weighted voting system. Never change this unless you're creating a different type of trading module.
Parameter Magic: Transforming Code into User-Friendly Inputs
The most powerful aspect of wizard compatibility is how it transforms your class's setter methods into user-friendly input parameters. Each parameter directive corresponds to one of your public setter methods, automatically generating the appropriate input controls in the EA's settings panel.

```
//| Parameter=PatternDoji,int,60,Weight for Doji pattern             |
//| Parameter=PatternEngulfing,int,80,Weight for Engulfing pattern   |
//| Parameter=PatternHammer,int,70,Weight for Hammer pattern         |
```

Parameter Syntax Breakdown:
Name: Must exactly match your setter method name (without the "Pattern" prefix)
Type: The data type (int, double, string, etc.)
Default Value: The initial value that appears in the Wizard.
Description: Help text that guides users on parameter usage
File Structure and Naming: The Organizational Key
Proper file organization is the final piece of the compatibility puzzle. The MQL5 Wizard expects signal files to follow specific naming conventions and reside in precisely the right directory location. This structured approach ensures consistency across the entire MQL5 ecosystem.

```
//+------------------------------------------------------------------+
//|                                          SignalCandlePattern.mqh |
//|                               Copyright 2025, Clemence Benjamin  |
//+------------------------------------------------------------------+
#include <Expert\ExpertSignal.mqh>
```

Essential Requirements:
Location: Must be in 
MQL5/Include/Expert/Signal/
File Naming: Should follow the Signal[YourSignalName].mqh pattern.
Class Naming: Should match the class directive in the wizard description.
Include Statement: Must include 
ExpertSignal.mqh 
for base functionality
The Complete Integration: How It All Works Together
When you've correctly implemented wizard compatibility, the transformation is remarkable. Your signal becomes a first-class citizen in the MQL5 Wizard ecosystem, appearing alongside all the built-in signals with the same level of integration and user experience.
What Users Experience:
Discovery: Your signal appears in the alphabetically sorted signal list.
Configuration: All parameters display with helpful descriptions and default values
Integration: The wizard automatically generates proper initialization code.
Combination: Your signal can be mixed and matched with other signals
Critical Success Factors for Wizard Compatibility
1
. Exact Directive Formatting
The wizard description must use precise formatting with no deviations. The 
// 
wizard description start and 
// 
wizard description end markers are non-negotiable, and each directive must be on its own line with proper syntax.
2. Parameter-Method Consistency
Every parameter directive must have a corresponding public setter method in your class. The wizard generates code that calls these methods, so any mismatch will cause compilation errors in the generated EA.
3. File Location Precision
Your signal file must reside in the exact correct directory. The wizard only scans 
MQL5/Include/Expert/Signal/
 for compatible signals, so even a slight deviation in file location will render your signal invisible.
4. MetaEditor Restart Requirement
After creating or modifying a signal file, you must restart MetaEditor for the wizard to detect the changes. The wizard scans for available signals during startup, so new signals won't appear until the next launch.
Testing Your Wizard Compatibility
Once you've implemented the wizard description header, verify your success with these steps:
Restart MetaEditor to refresh the signal cache
Launch MQL5 Wizard and create a new Expert Advisor
Click "Add" in the Signals section
Look for your signal in the alphabetical list
Select your signal and verify all parameters appear correctly
The Transformation Complete
With wizard compatibility properly implemented, your custom candlestick pattern signal transforms from an invisible class file into a fully integrated trading component. Users can now discover your signal, configure its parameters through an intuitive interface, and combine it with other signals to create sophisticated trading systems—all without ever seeing a line of code.
This compatibility layer represents the bridge between sophisticated programming and accessible trading strategy development, embodying the MQL5 philosophy of making advanced trading automation available to everyone, regardless of their programming expertise.
Once compatibility has been handled, it’s time to generate our Expert Advisor. In the next few steps, we’ll walk through the process, examine the code produced by the Wizard.
Launch the MQL5 Wizard (Create new document, Ctrl + N in MetaEditor 5)
Set Expert Advisor properties
Add and configure the candlestick signal
Select the trailing stop module
Configure money management
![Launch the Wizard.](https://c.mql5.com/2/183/MetaEditor64_olOWFI56RP.gif)
Launching the wizard
Understanding the Wizard's Blueprint: The Generated EA Structure
The MQL5 Wizard has just transformed our custom candlestick signal into a complete, functional Expert Advisor. This generated code represents a sophisticated trading framework that handles all the complex aspects of automated trading while leaving the strategic decisions to our signal logic. Let's break down this professional-grade architecture and understand how each component contributes to a robust trading system.

```
//+------------------------------------------------------------------+
//|                                    Expert Candlestick Wizard.mq5 |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
```

These property declarations establish the EA's identity and version control. While they seem simple, they're crucial for professional distribution and tracking different versions of your trading system.
The Expert Framework: Professional-Grade Architecture
The Wizard generates code that leverages MQL5's sophisticated Expert framework, which provides a standardized architecture for all trading operations. This framework handles the complex aspects of order management, event processing, and error handling so we can focus on our trading strategy.

```
//+------------------------------------------------------------------+
//| Include                                                          |
//+------------------------------------------------------------------+
#include <Expert\Expert.mqh>
//--- available signals
#include <Expert\Signal\SignalCandlePattern.mqh>
//--- available trailing
#include <Expert\Trailing\TrailingParabolicSAR.mqh>
//--- available money management
#include <Expert\Money\MoneySizeOptimized.mqh>
```

The Wizard follows a component-based architecture where signals, money management, and trailing stops are separate modules. This allows for incredible flexibility—you can easily swap out any component without affecting the others.
Configuration Interface: User-Friendly Input Parameters
The input parameters section transforms our technical trading concepts into accessible settings that any trader can understand and adjust. This is where the Wizard truly shines—it automatically creates a comprehensive configuration interface based on our signal class's parameters.

```
//+------------------------------------------------------------------+
//| Inputs                                                           |
//+------------------------------------------------------------------+
//--- inputs for expert
input string Expert_Title                      ="Candlestick Wizard"; // Document name
ulong        Expert_MagicNumber                =964602383;            //
bool         Expert_EveryTick                  =false;                //
//--- inputs for main signal
input int    Signal_ThresholdOpen              =10;                   // Signal threshold value to open [0...100]
input int    Signal_ThresholdClose             =10;                   // Signal threshold value to close [0...100]
input double Signal_PriceLevel                 =0.0;                  // Price level to execute a deal
input double Signal_StopLevel                  =50.0;                 // Stop Loss level (in points)
input double Signal_TakeLevel                  =50.0;                 // Take Profit level (in points)
input int    Signal_Expiration                 =4;                    // Expiration of pending orders (in bars)
```

Notice how the wizard sets sensible default values. The threshold of 10 means our candlestick patterns need to generate at least 10 "votes" to trigger a trade. These defaults provide a safe starting point for testing.
Signal-Specific Configuration: Our Custom Parameters
This is where our custom candlestick signal parameters appear, automatically generated from the wizard description header we created earlier. Each parameter corresponds directly to the setter methods in our signal class.

```
input int    Signal_Candle_PatternDoji         =60;                   // Candlestick Patterns(60,80,...) Weight for Doji pattern
input int    Signal_Candle_PatternEngulfing    =80;                   // Candlestick Patterns(60,80,...) Weight for Engulfing pattern
input int    Signal_Candle_PatternHammer       =70;                   // Candlestick Patterns(60,80,...) Weight for Hammer pattern
input int    Signal_Candle_PatternMorningStar  =90;                   // Candlestick Patterns(60,80,...) Weight for Morning Star pattern
input double Signal_Candle_DojiThreshold       =0.1;                  // Candlestick Patterns(60,80,...) Doji body threshold (relative to range)
input double Signal_Candle_EngulfingRatio      =1.5;                  // Candlestick Patterns(60,80,...) Engulfing ratio (current body must be at least this times previ
input double Signal_Candle_Weight              =1.0;                  // Candlestick Patterns(60,80,...) Weight [0...1.0]
```

The weights reflect the relative strength of each pattern—engulfing patterns (80) are considered stronger signals than hammers (70), while Morning Stars (90) are the most significant. This weighting system allows for sophisticated signal prioritization.
Risk Management Integration: Professional Trading Components
The wizard doesn't just stop at signal generation—it integrates comprehensive risk management through trailing stops and money management modules. This transforms our simple signal into a complete trading system.

```
//--- inputs for trailing
input double Trailing_ParabolicSAR_Step        =0.02;                 // Speed increment
input double Trailing_ParabolicSAR_Maximum     =0.2;                  // Maximum rate
//--- inputs for money
input double Money_SizeOptimized_DecreaseFactor=3.0;                  // Decrease factor
input double Money_SizeOptimized_Percent       =10.0;                 // Percent
```

The Parabolic SAR trailing stop will automatically protect profits by moving stop losses as the trade moves in our favor. The money management system ensures we never risk more than a percentage of our account on any single trade.
Core Expert Object
At the heart of every wizard-generated EA is the CExpert object—a sophisticated trading engine that coordinates all components and handles the complex logic of trade execution, monitoring, and management.

```
//+------------------------------------------------------------------+
//| Global expert object                                             |
//+------------------------------------------------------------------+
CExpert ExtExpert;
```

This single object manages the entire trading process, from receiving market data through our signal, to executing trades, to managing open positions with trailing stops and proper money management.
Initialization Mastery: Building the Trading System
The OnInit() function is where our trading system comes to life. This carefully orchestrated sequence ensures all components are properly initialized, configured, and validated before any trading begins.

```
//+------------------------------------------------------------------+
//| Initialization function of the expert                            |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- Initializing expert
   if(!ExtExpert.Init(Symbol(),Period(),Expert_EveryTick,Expert_MagicNumber))
     {
      //--- failed
      printf(__FUNCTION__+": error initializing expert");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
```

Notice the comprehensive error checking at every step. If any component fails to initialize, the EA gracefully shuts down and reports the specific error. This prevents trading with incomplete or misconfigured systems.
Signal Creation and Configuration: Bringing Our Strategy to Life
This section creates and configures our custom candlestick signal, transforming the input parameters into a live trading strategy. The wizard automatically generates the exact code needed to instantiate and configure our signal class.

```
//--- Creating signal
   CExpertSignal *signal=new CExpertSignal;
   if(signal==NULL)
     {
      //--- failed
      printf(__FUNCTION__+": error creating signal");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//---
   ExtExpert.InitSignal(signal);
   signal.ThresholdOpen(Signal_ThresholdOpen);
   signal.ThresholdClose(Signal_ThresholdClose);
   signal.PriceLevel(Signal_PriceLevel);
   signal.StopLevel(Signal_StopLevel);
   signal.TakeLevel(Signal_TakeLevel);
   signal.Expiration(Signal_Expiration);
```

The base CExpertSignal object provides the voting infrastructure that our custom signal will use. The threshold, stop, and take levels configure how signals are converted into actual trading decisions.
Custom Signal Integration: Our Candlestick Patterns Take Center Stage
This is where our custom candlestick signal gets integrated into the trading system. The Wizard creates an instance of our specific signal class and configures it with all the parameters we defined.

```
//--- Creating filter CMyCandlePatternSignal
   CMyCandlePatternSignal *filter0=new CMyCandlePatternSignal;
   if(filter0==NULL)
     {
      //--- failed
      printf(__FUNCTION__+": error creating filter0");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
   signal.AddFilter(filter0);
//--- Set filter parameters
   filter0.PatternDoji(Signal_Candle_PatternDoji);
   filter0.PatternEngulfing(Signal_Candle_PatternEngulfing);
   filter0.PatternHammer(Signal_Candle_PatternHammer);
   filter0.PatternMorningStar(Signal_Candle_PatternMorningStar);
   filter0.DojiThreshold(Signal_Candle_DojiThreshold);
   filter0.EngulfingRatio(Signal_Candle_EngulfingRatio);
   filter0.Weight(Signal_Candle_Weight);
```

The "filter0" naming convention reveals a powerful feature—the Wizard can combine multiple signals. We could add filter1, filter2, etc., each with different trading strategies that work together.
Complete System Integration: Risk Management Components
The initialization continues by adding professional trailing stops and money management, creating a complete, production-ready trading system that manages both entry signals and risk control.

```
//--- Creation of trailing object
   CTrailingPSAR *trailing=new CTrailingPSAR;
   if(trailing==NULL)
     {
      //--- failed
      printf(__FUNCTION__+": error creating trailing");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Add trailing to expert (will be deleted automatically))
   if(!ExtExpert.InitTrailing(trailing))
     {
      //--- failed
      printf(__FUNCTION__+": error initializing trailing");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Set trailing parameters
   trailing.Step(Trailing_ParabolicSAR_Step);
   trailing.Maximum(Trailing_ParabolicSAR_Maximum);
```

The Parabolic SAR trailing stop will dynamically adjust stop losses based on price movement, locking in profits while giving trades room to develop.
Money Management: Professional Position Sizing
No professional trading system is complete without proper money management. The Wizard integrates sophisticated position sizing that adapts to account size and market conditions.

```
//--- Creation of money object
   CMoneySizeOptimized *money=new CMoneySizeOptimized;
   if(money==NULL)
     {
      //--- failed
      printf(__FUNCTION__+": error creating money");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Add money to expert (will be deleted automatically))
   if(!ExtExpert.InitMoney(money))
     {
      //--- failed
      printf(__FUNCTION__+": error initializing money");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Set money parameters
   money.DecreaseFactor(Money_SizeOptimized_DecreaseFactor);
   money.Percent(Money_SizeOptimized_Percent);
```

The optimized money management system calculates position sizes based on account equity, ensuring consistent risk exposure regardless of account size.
System Validation and Indicator Initialization
Before the EA begins trading, it performs comprehensive validation and prepares all necessary technical indicators. This ensures the system is completely ready for live market conditions.

```
//--- Check all trading objects parameters
   if(!ExtExpert.ValidationSettings())
     {
      //--- failed
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- Tuning of all necessary indicators
   if(!ExtExpert.InitIndicators())
     {
      //--- failed
      printf(__FUNCTION__+": error initializing indicators");
      ExtExpert.Deinit();
      return(INIT_FAILED);
     }
//--- ok
   return(INIT_SUCCEEDED);
  }
```

The validation process confirms that all components are properly configured and compatible. The indicator initialization ensures all technical analysis tools are ready for real-time data processing.
Event-Driven Architecture: Efficient Market Processing
The Wizard generates an event-driven architecture that efficiently processes market events without unnecessary CPU usage. This ensures optimal performance even during high-volatility periods.

```
//+------------------------------------------------------------------+
//| Deinitialization function of the expert                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   ExtExpert.Deinit();
  }
//+------------------------------------------------------------------+
//| "Tick" event handler function                                    |
//+------------------------------------------------------------------+
void OnTick()
  {
   ExtExpert.OnTick();
  }
//+------------------------------------------------------------------+
//| "Trade" event handler function                                   |
//+------------------------------------------------------------------+
void OnTrade()
  {
   ExtExpert.OnTrade();
  }
//+------------------------------------------------------------------+
//| "Timer" event handler function                                   |
//+------------------------------------------------------------------+
void OnTimer()
  {
   ExtExpert.OnTimer();
  }
//+------------------------------------------------------------------+
```

By delegating all event processing to the CExpert framework, the EA ensures professional-grade performance and reliability. The framework handles tick processing, trade events, and timer events with optimized efficiency.
The Generated EA Assessment: Strengths and Improvement Opportunities
What's Excellent:
Professional architecture with proper error handling
Comprehensive risk management integration
Modular design allowing easy component swapping
Event-driven efficiency
Production-ready validation and initialization
Areas for Enhancement:
Limited debugging and logging capabilities
Basic error messages without context
No performance tracking or statistics
Missing trade confirmation and validation
No market condition adaptivity

### Testing

After successfully generating our Expert Advisor through the MQL5 Wizard, the crucial next step was to validate its performance and trading behavior in the Strategy Tester. This testing phase served as the ultimate proof-of-concept, demonstrating that our custom candlestick signal could successfully identify trading opportunities and execute orders in simulated market conditions.
Testing Objectives Achieved:
Order Execution: Confirmed the EA can successfully place both BUY and SELL orders
Signal Accuracy: Verified candlestick patterns trigger appropriate trading decisions
Risk Management: Observed trailing stops dynamically adjusting to protect profits
System Stability: Ensured the EA operates without errors across different market conditions
The animated demonstration clearly shows our EA in action—placing trades based on candlestick pattern recognition while the Parabolic SAR trailing stops actively manage risk by progressively locking in profits as trades move in our favor.
![Strategy Tester](https://c.mql5.com/2/183/metatester64_PBOqzB4S45.gif)
Testing the generated EA

### Conclusion

Our development journey from a simple candlestick pattern concept to a fully functional Expert Advisor shows how the MQL5 Wizard has transformed algorithmic trading development. By mastering Wizard compatibility and understanding the generated architecture, we unlock the ability to create sophisticated trading systems with much greater efficiency.
Professional-grade algorithmic trading is now accessible to developers at almost any skill level. The MQL5 Wizard bridges the gap between trading expertise and programming knowledge, allowing traders to focus on strategy logic while the framework takes care of most low-level implementation details.
This exploration has produced a working Expert Advisor and a clear roadmap for continuous improvement and professional growth in algorithmic trading. The foundation we’ve built can be extended endlessly—from basic pattern recognition to adaptive, multi-strategy systems capable of handling complex market conditions. From here, the next step is to optimize the strategy and its settings to achieve better profitability. Additional filters can be integrated to screen signals and select only the highest-quality trades.
We all value profitability, but in most EA development it is healthier to focus first on correctness: making sure the EA executes orders exactly according to the rules. Profitability then becomes an optimization stage once the logic is stable and reliable.
The journey from concept to code is complete, but the path to trading mastery continues—with stronger tools and a profound understanding of how to build increasingly sophisticated and profitable trading systems. The source file table is shown below, and the files are attached at the end of the article so you can download them and have fun experimenting. Until the next publication, stay tuned—and you are welcome to share your thoughts in the comments.

### Attachments

Source File
Description:
[SignalCandlePattern.mqh](/en/articles/download/20266/210691/SignalCandlePattern.mqh)
Custom Signal Class
Contains the complete implementation of our candlestick pattern recognition system. This file defines the CMyCandlePatternSignal class that inherits from CExpertSignal, including pattern detection methods for Doji, Engulfing, Hammer, Shooting Star, and other candlestick formations. Features wizard-compatible description header for seamless MQL5 Wizard integration.
[Expert Candlestick Wizard.mq5](/en/articles/download/20266/210691/Expert_Candlestick_Wizard.mq5)
Generated Expert Advisor
Complete trading robot automatically generated by MQL5 Wizard using our custom signal class. Includes integrated risk management with Parabolic SAR trailing stops, optimized money management, and professional error handling. Ready for compilation and deployment in MetaTrader 5 platform.

Attached files
 |
  

[Download ZIP](/en/articles/download/20266.zip)

[SignalCandlePattern.mqh](/en/articles/download/20266/SignalCandlePattern.mqh)

(10.06 KB)

[Expert_Candlestick_Wizard.mq5](/en/articles/download/20266/Expert_Candlestick_Wizard.mq5)

(8.19 KB)

Warning:
 All rights to these materials are reserved by MetaQuotes Ltd. Copying or reprinting of these materials in whole or in part is prohibited.

This article was written by a user of the site and reflects their personal views. MetaQuotes Ltd is not responsible for the accuracy of the information presented, nor for any consequences resulting from the use of the solutions, strategies or recommendations described.

#### Other articles by this author

[From Novice to Expert: Developing a Geographic Market Awareness with MQL5 Visualization](/en/articles/20417)

[The MQL5 Standard Library Explorer (Part 5): Multiple Signal Expert](/en/articles/20289)

[From Novice to Expert: Predictive Price Pathways](/en/articles/20160)

[From Novice to Expert: Time Filtered Trading](/en/articles/20037)

[From Novice to Expert: Forex Market Periods](/en/articles/20005)

[The MQL5 Standard Library Explorer (Part 3): Expert Standard Deviation Channel](/en/articles/20041)

[Go to discussion](/en/forum/500823)

![Introduction to MQL5 (Part 29): Mastering API and WebRequest Function in MQL5 (III)](https://c.mql5.com/2/183/20375-introduction-to-mql5-part-29-logo__1.png)

[Introduction to MQL5 (Part 29): Mastering API and WebRequest Function in MQL5 (III)](/en/articles/20375)

In this article, we continue mastering API and WebRequest in MQL5 by retrieving candlestick data from an external source. We focus on splitting the server response, cleaning the data, and extracting essential elements such as opening time and OHLC values for multiple daily candles, preparing the data for further analysis.

![From Basic to Intermediate: Struct (I)](https://c.mql5.com/2/117/Do_b8sico_ao_intermediario_Struct_I___LOGO.png)

[From Basic to Intermediate: Struct (I)](/en/articles/15730)

Today we will begin to study structures in a simpler, more practical, and comfortable way. Structures are among the foundations of programming, whether they are structured or not. I know many people think of structures as just collections of data, but I assure you that they are much more than just structures. And here we will begin to explore this new universe in the most didactic way.

![Price Action Analysis Toolkit Development (Part 53): Pattern Density Heatmap for Support and Resistance Zone Discovery](https://c.mql5.com/2/183/20390-price-action-analysis-toolkit-logo.png)

[Price Action Analysis Toolkit Development (Part 53): Pattern Density Heatmap for Support and Resistance Zone Discovery](/en/articles/20390)

This article introduces the Pattern Density Heatmap, a price‑action mapping tool that transforms repeated candlestick pattern detections into statistically significant support and resistance zones. Rather than treating each signal in isolation, the EA aggregates detections into fixed price bins, scores their density with optional recency weighting, and confirms levels against higher‑timeframe data. The resulting heatmap reveals where the market has historically reacted—levels that can be used proactively for trade timing, risk management, and strategy confidence across any trading style.

![Automating Trading Strategies in MQL5 (Part 42): Session-Based Opening Range Breakout (ORB) System](https://c.mql5.com/2/183/20339-automating-trading-strategies-logo.png)

[Automating Trading Strategies in MQL5 (Part 42): Session-Based Opening Range Breakout (ORB) System](/en/articles/20339)

In this article, we create a fully customizable session-based Opening Range Breakout (ORB) system in MQL5 that lets us set any desired session start time and range duration, automatically calculates the high and low of that opening period, and trades only confirmed breakouts in the direction of the move.

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

