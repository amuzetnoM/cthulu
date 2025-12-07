//+------------------------------------------------------------------+
//|                                          SignalCandlePattern.mqh |
//|                               Copyright 2025, Clemence Benjamin  |
//+------------------------------------------------------------------+
#include <Expert\ExpertSignal.mqh>

// wizard description start
//+------------------------------------------------------------------+
//| Description of the class                                         |
//| Title=Signals of candlestick patterns                            |
//| Type=SignalAdvanced                                              |
//| Name=Candlestick Patterns                                        |
//| ShortName=Candle                                                 |
//| Class=CMyCandlePatternSignal                                     |
//| Page=signal_candle_pattern                                       |
//| Parameter=PatternDoji,int,60,Weight for Doji pattern             |
//| Parameter=PatternEngulfing,int,80,Weight for Engulfing pattern   |
//| Parameter=PatternHammer,int,70,Weight for Hammer pattern         |
//| Parameter=PatternMorningStar,int,90,Weight for Morning Star pattern |
//| Parameter=DojiThreshold,double,0.1,Doji body threshold (relative to range) |
//| Parameter=EngulfingRatio,double,1.5,Engulfing ratio (current body must be at least this times previous body) |
//+------------------------------------------------------------------+
// wizard description end

//+------------------------------------------------------------------+
//| Class CMyCandlePatternSignal                                     |
//+------------------------------------------------------------------+
class CMyCandlePatternSignal : public CExpertSignal
{
protected:
   //--- Pattern weights
   int               m_pattern_doji;        // Doji pattern weight
   int               m_pattern_engulfing;   // Engulfing pattern weight  
   int               m_pattern_hammer;      // Hammer/Hanging man weight
   int               m_pattern_morning_star;// Morning/Evening star weight
   
   //--- Detection parameters
   double            m_doji_threshold;      // Doji body threshold
   double            m_engulfing_ratio;     // Engulfing size ratio

public:
   //--- Constructor
                     CMyCandlePatternSignal(void);
   
   //--- Methods for setting parameters
   void              PatternDoji(int value)        { m_pattern_doji=value; }
   void              PatternEngulfing(int value)   { m_pattern_engulfing=value; }
   void              PatternHammer(int value)      { m_pattern_hammer=value; }
   void              PatternMorningStar(int value) { m_pattern_morning_star=value; }
   void              DojiThreshold(double value)   { m_doji_threshold=value; }
   void              EngulfingRatio(double value)  { m_engulfing_ratio=value; }

protected:
   //--- Candlestick pattern detection methods
   bool              IsDoji(int idx);
   bool              IsBullishEngulfing(int idx);
   bool              IsBearishEngulfing(int idx);
   bool              IsHammer(int idx);
   bool              IsShootingStar(int idx);
   
   //--- Main signal generation methods
   virtual int       LongCondition(void);
   virtual int       ShortCondition(void);
};
//+------------------------------------------------------------------+
//| Constructor                                                      |
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
//+------------------------------------------------------------------+
//| Check if candle is Doji                                          |
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
//+------------------------------------------------------------------+
//| Check for Bullish Engulfing pattern                              |
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
//+------------------------------------------------------------------+
//| Check for Bearish Engulfing pattern                              |
//+------------------------------------------------------------------+
bool CMyCandlePatternSignal::IsBearishEngulfing(int idx)
{
   double prev_open = m_open.GetData(idx+1);
   double prev_close = m_close.GetData(idx+1);
   double curr_open = m_open.GetData(idx);
   double curr_close = m_close.GetData(idx);
   
   // Previous candle must be bullish
   if(prev_close <= prev_open) return false;
   
   // Current candle must be bearish
   if(curr_close >= curr_open) return false;
   
   // Current body must engulf previous body
   if(curr_open > prev_close && curr_close < prev_open)
   {
      double prev_body = MathAbs(prev_close - prev_open);
      double curr_body = MathAbs(curr_close - curr_open);
      
      // Current body should be significantly larger
      if(curr_body >= prev_body * m_engulfing_ratio)
         return true;
   }
   
   return false;
}
//+------------------------------------------------------------------+
//| Check for Hammer pattern (bullish reversal)                      |
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
//+------------------------------------------------------------------+
//| Check for Shooting Star pattern (bearish reversal)               |
//+------------------------------------------------------------------+
bool CMyCandlePatternSignal::IsShootingStar(int idx)
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
   
   // Shooting Star: small body, long upper shadow, little to no lower shadow
   bool is_small_body = body_size <= range * 0.3;
   bool is_long_upper_shadow = upper_shadow >= body_size * 2.0;
   bool is_small_lower_shadow = lower_shadow <= body_size * 0.5;
   
   return (is_small_body && is_long_upper_shadow && is_small_lower_shadow);
}
//+------------------------------------------------------------------+
//| "Long" condition (BUY signals)                                   |
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
      if(IS_PATTERN_USAGE(2))
         result += m_pattern_doji;
   }
   
   return(result);
}
//+------------------------------------------------------------------+
//| "Short" condition (SELL signals)                                 |
//+------------------------------------------------------------------+
int CMyCandlePatternSignal::ShortCondition(void)
{
   int result=0;
   int idx=StartIndex();
   
   //--- Pattern 0: Bearish Engulfing
   if(IsBearishEngulfing(idx))
   {
      if(IS_PATTERN_USAGE(0))
         result += m_pattern_engulfing;
   }
   
   //--- Pattern 1: Shooting Star
   if(IsShootingStar(idx))
   {
      if(IS_PATTERN_USAGE(1))
         result += m_pattern_hammer;
   }
   
   //--- Pattern 2: Doji at resistance (potential reversal)
   if(IsDoji(idx))
   {
      if(IS_PATTERN_USAGE(2))
         result += m_pattern_doji;
   }
   
   return(result);
}
//+------------------------------------------------------------------+