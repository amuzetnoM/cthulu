//+------------------------------------------------------------------+
//|                                              CthulhuDrawings.mq5 |
//|                                    Cthulu v5.2.0 - Chart Manager |
//|                           Reads JSON zones and draws on MT5 chart|
//+------------------------------------------------------------------+
#property copyright "Cthulu Trading System"
#property link      "https://github.com/cthulu"
#property version   "1.00"
#property indicator_chart_window
#property indicator_plots 0  // No plots - this indicator only draws objects

//--- Input parameters
input string   DrawingsPath = "C:\\workspace\\cthulu\\data\\drawings\\";  // Path to drawings JSON
input int      RefreshSeconds = 5;                                        // Refresh interval in seconds
input bool     DrawZones = true;                                          // Draw zone rectangles
input bool     DrawLevels = true;                                         // Draw horizontal levels
input bool     DrawTrendLines = true;                                     // Draw trend lines
input bool     ShowLabels = true;                                         // Show zone labels
input int      ZoneExtendBars = 50;                                       // Extend zones N bars forward

//--- Object prefix for cleanup
#define OBJ_PREFIX "CTH_"

//--- Global variables
datetime lastFileTime = 0;
string currentSymbol;
string currentTimeframe;

//+------------------------------------------------------------------+
//| Custom indicator initialization function                          |
//+------------------------------------------------------------------+
int OnInit()
{
    currentSymbol = Symbol();
    currentTimeframe = GetTimeframeString(Period());
    
    Print("=== CthulhuDrawings v1.1 ===");
    Print("Symbol: ", currentSymbol, " Timeframe: ", currentTimeframe);
    Print("Looking for JSON in MT5 Common/Files folder");
    
    // Initial load
    LoadAndDrawAll();
    
    // Set timer for periodic refresh
    EventSetTimer(RefreshSeconds);
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                        |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    EventKillTimer();
    CleanupAllObjects();
}

//+------------------------------------------------------------------+
//| Timer function - check for file updates                           |
//+------------------------------------------------------------------+
void OnTimer()
{
    LoadAndDrawAll();
}

//+------------------------------------------------------------------+
//| Main calculation function (called on each tick)                   |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
    return(rates_total);
}

//+------------------------------------------------------------------+
//| Load JSON and draw all objects                                    |
//+------------------------------------------------------------------+
void LoadAndDrawAll()
{
    string safeSymbol = currentSymbol;
    StringReplace(safeSymbol, "#", "");
    StringReplace(safeSymbol, "/", "_");
    
    string filename = safeSymbol + "_" + currentTimeframe + "_drawings.json";
    string jsonContent = "";
    
    Print("Looking for: ", filename);
    
    // Try MT5 common folder first (where Python exports to)
    int handle = FileOpen(filename, FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON);
    if(handle != INVALID_HANDLE)
    {
        Print("Found file in Common/Files folder");
        while(!FileIsEnding(handle))
        {
            jsonContent += FileReadString(handle) + "\n";
        }
        FileClose(handle);
    }
    else
    {
        Print("File not found in Common folder, trying MQL5/Files...");
        // Try MQL5/Files folder
        handle = FileOpen(filename, FILE_READ|FILE_TXT|FILE_ANSI);
        if(handle != INVALID_HANDLE)
        {
            Print("Found file in MQL5/Files folder");
            while(!FileIsEnding(handle))
            {
                jsonContent += FileReadString(handle) + "\n";
            }
            FileClose(handle);
        }
        else
        {
            Print("WARNING: JSON file not found: ", filename);
            Print("Make sure Cthulu is running and exporting drawings");
            return;
        }
    }
    
    if(StringLen(jsonContent) > 10)
    {
        Print("Loaded JSON: ", StringLen(jsonContent), " bytes");
        ParseAndDraw(jsonContent);
    }
    else
    {
        Print("WARNING: JSON content too short or empty");
    }
}

//+------------------------------------------------------------------+
//| Parse JSON content and draw objects                               |
//+------------------------------------------------------------------+
void ParseAndDraw(string &jsonContent)
{
    // Clean up old objects first
    CleanupAllObjects();
    
    // Parse zones
    if(DrawZones)
    {
        ParseAndDrawZones(jsonContent);
    }
    
    // Parse levels
    if(DrawLevels)
    {
        ParseAndDrawLevels(jsonContent);
    }
    
    // Parse trend lines
    if(DrawTrendLines)
    {
        ParseAndDrawTrendLines(jsonContent);
    }
    
    ChartRedraw();
}

//+------------------------------------------------------------------+
//| Parse and draw zones from JSON                                    |
//+------------------------------------------------------------------+
void ParseAndDrawZones(string &json)
{
    // Find zones array
    int zonesStart = StringFind(json, "\"zones\":");
    if(zonesStart < 0) return;
    
    int arrayStart = StringFind(json, "[", zonesStart);
    if(arrayStart < 0) return;
    
    // Find matching closing bracket
    int bracketCount = 1;
    int pos = arrayStart + 1;
    int len = StringLen(json);
    
    while(pos < len && bracketCount > 0)
    {
        string ch = StringSubstr(json, pos, 1);
        if(ch == "[") bracketCount++;
        else if(ch == "]") bracketCount--;
        pos++;
    }
    
    string zonesArray = StringSubstr(json, arrayStart, pos - arrayStart);
    
    // Parse individual zones
    int zoneIndex = 0;
    int searchPos = 0;
    
    while(true)
    {
        int objStart = StringFind(zonesArray, "{", searchPos);
        if(objStart < 0) break;
        
        int objEnd = StringFind(zonesArray, "}", objStart);
        if(objEnd < 0) break;
        
        string zoneObj = StringSubstr(zonesArray, objStart, objEnd - objStart + 1);
        
        // Extract zone properties
        string id = ExtractJsonString(zoneObj, "id");
        string type = ExtractJsonString(zoneObj, "type");
        double upper = ExtractJsonDouble(zoneObj, "upper");
        double lower = ExtractJsonDouble(zoneObj, "lower");
        string colorHex = ExtractJsonString(zoneObj, "color");
        string state = ExtractJsonString(zoneObj, "state");
        double strength = ExtractJsonDouble(zoneObj, "strength");
        
        // Draw the zone
        if(upper > 0 && lower > 0)
        {
            DrawZone(id, type, upper, lower, colorHex, state, strength);
        }
        
        searchPos = objEnd + 1;
        zoneIndex++;
    }
    
    Print("Drew ", zoneIndex, " zones");
}

//+------------------------------------------------------------------+
//| Draw a single zone as a rectangle                                 |
//+------------------------------------------------------------------+
void DrawZone(string id, string type, double upper, double lower, 
              string colorHex, string state, double strength)
{
    string objName = OBJ_PREFIX + "ZONE_" + id;
    
    // Get time range for rectangle
    datetime time1 = iTime(currentSymbol, Period(), ZoneExtendBars);
    datetime time2 = iTime(currentSymbol, Period(), 0) + PeriodSeconds(Period()) * 10;
    
    // Convert hex color to MT5 color
    color zoneColor = HexToColor(colorHex);
    
    // Create rectangle
    if(ObjectCreate(0, objName, OBJ_RECTANGLE, 0, time1, upper, time2, lower))
    {
        ObjectSetInteger(0, objName, OBJPROP_COLOR, zoneColor);
        ObjectSetInteger(0, objName, OBJPROP_FILL, true);
        ObjectSetInteger(0, objName, OBJPROP_BACK, true);
        
        // Opacity based on strength (use style)
        if(state == "TESTED" || state == "WEAKENED")
        {
            ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_DASH);
        }
        else
        {
            ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_SOLID);
        }
        
        ObjectSetInteger(0, objName, OBJPROP_WIDTH, (int)(strength * 2) + 1);
        ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
        ObjectSetInteger(0, objName, OBJPROP_HIDDEN, true);
        
        // Add label if enabled
        if(ShowLabels)
        {
            string labelName = OBJ_PREFIX + "LBL_" + id;
            double midPrice = (upper + lower) / 2;
            
            if(ObjectCreate(0, labelName, OBJ_TEXT, 0, time1, midPrice))
            {
                string labelText = GetZoneLabel(type, state, strength);
                ObjectSetString(0, labelName, OBJPROP_TEXT, labelText);
                ObjectSetInteger(0, labelName, OBJPROP_COLOR, zoneColor);
                ObjectSetInteger(0, labelName, OBJPROP_FONTSIZE, 8);
                ObjectSetString(0, labelName, OBJPROP_FONT, "Arial");
                ObjectSetInteger(0, labelName, OBJPROP_ANCHOR, ANCHOR_LEFT);
                ObjectSetInteger(0, labelName, OBJPROP_SELECTABLE, false);
                ObjectSetInteger(0, labelName, OBJPROP_HIDDEN, true);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Parse and draw levels from JSON                                   |
//+------------------------------------------------------------------+
void ParseAndDrawLevels(string &json)
{
    int levelsStart = StringFind(json, "\"levels\":");
    if(levelsStart < 0) return;
    
    int arrayStart = StringFind(json, "[", levelsStart);
    if(arrayStart < 0) return;
    
    int bracketCount = 1;
    int pos = arrayStart + 1;
    int len = StringLen(json);
    
    while(pos < len && bracketCount > 0)
    {
        string ch = StringSubstr(json, pos, 1);
        if(ch == "[") bracketCount++;
        else if(ch == "]") bracketCount--;
        pos++;
    }
    
    string levelsArray = StringSubstr(json, arrayStart, pos - arrayStart);
    
    int levelIndex = 0;
    int searchPos = 0;
    
    while(true)
    {
        int objStart = StringFind(levelsArray, "{", searchPos);
        if(objStart < 0) break;
        
        int objEnd = StringFind(levelsArray, "}", objStart);
        if(objEnd < 0) break;
        
        string levelObj = StringSubstr(levelsArray, objStart, objEnd - objStart + 1);
        
        double price = ExtractJsonDouble(levelObj, "price");
        string type = ExtractJsonString(levelObj, "type");
        string colorHex = ExtractJsonString(levelObj, "color");
        string label = ExtractJsonString(levelObj, "label");
        string style = ExtractJsonString(levelObj, "style");
        
        if(price > 0)
        {
            DrawLevel(levelIndex, price, type, colorHex, label, style);
        }
        
        searchPos = objEnd + 1;
        levelIndex++;
    }
    
    Print("Drew ", levelIndex, " levels");
}

//+------------------------------------------------------------------+
//| Draw a horizontal level                                           |
//+------------------------------------------------------------------+
void DrawLevel(int index, double price, string type, string colorHex, 
               string label, string style)
{
    string objName = OBJ_PREFIX + "LVL_" + IntegerToString(index);
    
    color levelColor = HexToColor(colorHex);
    ENUM_LINE_STYLE lineStyle = STYLE_DOT;
    
    if(style == "solid") lineStyle = STYLE_SOLID;
    else if(style == "dashed") lineStyle = STYLE_DASH;
    else if(style == "dotted") lineStyle = STYLE_DOT;
    
    if(ObjectCreate(0, objName, OBJ_HLINE, 0, 0, price))
    {
        ObjectSetInteger(0, objName, OBJPROP_COLOR, levelColor);
        ObjectSetInteger(0, objName, OBJPROP_STYLE, lineStyle);
        ObjectSetInteger(0, objName, OBJPROP_WIDTH, 1);
        ObjectSetInteger(0, objName, OBJPROP_BACK, true);
        ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
        ObjectSetInteger(0, objName, OBJPROP_HIDDEN, true);
        
        // Price label
        if(ShowLabels && label != "")
        {
            ObjectSetString(0, objName, OBJPROP_TEXT, label);
        }
    }
}

//+------------------------------------------------------------------+
//| Parse and draw trend lines from JSON                              |
//+------------------------------------------------------------------+
void ParseAndDrawTrendLines(string &json)
{
    int tlStart = StringFind(json, "\"trend_lines\":");
    if(tlStart < 0) return;
    
    int arrayStart = StringFind(json, "[", tlStart);
    if(arrayStart < 0) return;
    
    int bracketCount = 1;
    int pos = arrayStart + 1;
    int len = StringLen(json);
    
    while(pos < len && bracketCount > 0)
    {
        string ch = StringSubstr(json, pos, 1);
        if(ch == "[") bracketCount++;
        else if(ch == "]") bracketCount--;
        pos++;
    }
    
    string tlArray = StringSubstr(json, arrayStart, pos - arrayStart);
    
    int tlIndex = 0;
    int searchPos = 0;
    
    while(true)
    {
        int objStart = StringFind(tlArray, "{", searchPos);
        if(objStart < 0) break;
        
        int objEnd = StringFind(tlArray, "}", objStart);
        if(objEnd < 0) break;
        
        string tlObj = StringSubstr(tlArray, objStart, objEnd - objStart + 1);
        
        string id = ExtractJsonString(tlObj, "id");
        double startPrice = ExtractJsonDouble(tlObj, "start_price");
        double endPrice = ExtractJsonDouble(tlObj, "end_price");
        string colorHex = ExtractJsonString(tlObj, "color");
        string style = ExtractJsonString(tlObj, "style");
        
        // For now, draw as horizontal trend line between recent bars
        // TODO: Parse actual timestamps when available
        if(startPrice > 0 && endPrice > 0)
        {
            DrawTrendLine(tlIndex, startPrice, endPrice, colorHex, style);
        }
        
        searchPos = objEnd + 1;
        tlIndex++;
    }
    
    Print("Drew ", tlIndex, " trend lines");
}

//+------------------------------------------------------------------+
//| Draw a trend line                                                 |
//+------------------------------------------------------------------+
void DrawTrendLine(int index, double startPrice, double endPrice, 
                   string colorHex, string style)
{
    string objName = OBJ_PREFIX + "TL_" + IntegerToString(index);
    
    datetime time1 = iTime(currentSymbol, Period(), ZoneExtendBars);
    datetime time2 = iTime(currentSymbol, Period(), 0);
    
    color lineColor = HexToColor(colorHex);
    ENUM_LINE_STYLE lineStyle = STYLE_SOLID;
    
    if(style == "dashed") lineStyle = STYLE_DASH;
    else if(style == "dotted") lineStyle = STYLE_DOT;
    
    if(ObjectCreate(0, objName, OBJ_TREND, 0, time1, startPrice, time2, endPrice))
    {
        ObjectSetInteger(0, objName, OBJPROP_COLOR, lineColor);
        ObjectSetInteger(0, objName, OBJPROP_STYLE, lineStyle);
        ObjectSetInteger(0, objName, OBJPROP_WIDTH, 2);
        ObjectSetInteger(0, objName, OBJPROP_RAY_RIGHT, true);
        ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
        ObjectSetInteger(0, objName, OBJPROP_HIDDEN, true);
    }
}

//+------------------------------------------------------------------+
//| Cleanup all Cthulu objects from chart                             |
//+------------------------------------------------------------------+
void CleanupAllObjects()
{
    int total = ObjectsTotal(0);
    for(int i = total - 1; i >= 0; i--)
    {
        string name = ObjectName(0, i);
        if(StringFind(name, OBJ_PREFIX) == 0)
        {
            ObjectDelete(0, name);
        }
    }
}

//+------------------------------------------------------------------+
//| Helper: Extract string value from JSON                            |
//+------------------------------------------------------------------+
string ExtractJsonString(string &json, string key)
{
    string searchKey = "\"" + key + "\":";
    int keyPos = StringFind(json, searchKey);
    if(keyPos < 0) return "";
    
    int valueStart = keyPos + StringLen(searchKey);
    
    // Skip whitespace
    while(StringSubstr(json, valueStart, 1) == " " || 
          StringSubstr(json, valueStart, 1) == "\t")
        valueStart++;
    
    // Check if string value (starts with ")
    if(StringSubstr(json, valueStart, 1) == "\"")
    {
        valueStart++;
        int valueEnd = StringFind(json, "\"", valueStart);
        if(valueEnd > valueStart)
        {
            return StringSubstr(json, valueStart, valueEnd - valueStart);
        }
    }
    
    return "";
}

//+------------------------------------------------------------------+
//| Helper: Extract double value from JSON                            |
//+------------------------------------------------------------------+
double ExtractJsonDouble(string &json, string key)
{
    string searchKey = "\"" + key + "\":";
    int keyPos = StringFind(json, searchKey);
    if(keyPos < 0) return 0;
    
    int valueStart = keyPos + StringLen(searchKey);
    
    // Skip whitespace
    while(StringSubstr(json, valueStart, 1) == " " || 
          StringSubstr(json, valueStart, 1) == "\t")
        valueStart++;
    
    // Find end of number
    int valueEnd = valueStart;
    int len = StringLen(json);
    while(valueEnd < len)
    {
        string ch = StringSubstr(json, valueEnd, 1);
        if(ch == "," || ch == "}" || ch == "]" || ch == " " || ch == "\n")
            break;
        valueEnd++;
    }
    
    string valueStr = StringSubstr(json, valueStart, valueEnd - valueStart);
    return StringToDouble(valueStr);
}

//+------------------------------------------------------------------+
//| Helper: Convert hex color to MT5 color                            |
//+------------------------------------------------------------------+
color HexToColor(string hex)
{
    // Remove # prefix if present
    if(StringSubstr(hex, 0, 1) == "#")
        hex = StringSubstr(hex, 1);
    
    if(StringLen(hex) != 6)
        return clrGray;
    
    // Parse RGB components (MT5 uses BGR format internally)
    int r = HexCharToInt(StringSubstr(hex, 0, 2));
    int g = HexCharToInt(StringSubstr(hex, 2, 2));
    int b = HexCharToInt(StringSubstr(hex, 4, 2));
    
    // MT5 color format is 0x00BBGGRR
    return (color)((b << 16) | (g << 8) | r);
}

//+------------------------------------------------------------------+
//| Helper: Convert hex string to int                                 |
//+------------------------------------------------------------------+
int HexCharToInt(string hexStr)
{
    int result = 0;
    StringToUpper(hexStr);
    
    for(int i = 0; i < StringLen(hexStr); i++)
    {
        result *= 16;
        ushort ch = StringGetCharacter(hexStr, i);
        
        if(ch >= '0' && ch <= '9')
            result += ch - '0';
        else if(ch >= 'A' && ch <= 'F')
            result += ch - 'A' + 10;
    }
    
    return result;
}

//+------------------------------------------------------------------+
//| Helper: Get timeframe string                                      |
//+------------------------------------------------------------------+
string GetTimeframeString(ENUM_TIMEFRAMES tf)
{
    switch(tf)
    {
        case PERIOD_M1:  return "M1";
        case PERIOD_M5:  return "M5";
        case PERIOD_M15: return "M15";
        case PERIOD_M30: return "M30";
        case PERIOD_H1:  return "H1";
        case PERIOD_H4:  return "H4";
        case PERIOD_D1:  return "D1";
        case PERIOD_W1:  return "W1";
        case PERIOD_MN1: return "MN1";
        default:         return "M30";
    }
}

//+------------------------------------------------------------------+
//| Helper: Get zone label text                                       |
//+------------------------------------------------------------------+
string GetZoneLabel(string type, string state, double strength)
{
    string label = "";
    
    // Zone type abbreviation
    if(type == "ob_bullish") label = "OB+";
    else if(type == "ob_bearish") label = "OB-";
    else if(type == "orb_high") label = "ORB-H";
    else if(type == "orb_low") label = "ORB-L";
    else if(type == "support") label = "SUP";
    else if(type == "resistance") label = "RES";
    else if(type == "fvg_bullish") label = "FVG+";
    else if(type == "fvg_bearish") label = "FVG-";
    else label = type;
    
    // Add strength indicator
    if(strength >= 0.8) label += " ***";
    else if(strength >= 0.5) label += " **";
    else if(strength >= 0.3) label += " *";
    
    return label;
}
//+------------------------------------------------------------------+
