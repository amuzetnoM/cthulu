---
title: "MQL5 Trading Tools (Part 9): Developing a First Run User Setup Wizard for Expert Advisors with Scrollable Guide"
original_url: "https://www.mql5.com/en/articles/19714"
phase: "phase1"
date: "30 September 2025, 09:16"
---

# MQL5 Trading Tools (Part 9): Developing a First Run User Setup Wizard for Expert Advisors with Scrollable Guide



[](#pocket)

[](/en/articles/19714?print=)

![preview](assets/MQL5-Trading-Tools-Part-9-Developing-a-First-Run-User-Setup-Wizard-for-Expert-Advisors-with-Scrollable-Guide/80722037d4ceb32de331b890ef518893.jpeg)

![MQL5 Trading Tools (Part 9): Developing a First Run User Setup Wizard for Expert Advisors with Scrollable Guide](https://c.mql5.com/2/172/19714-mql5-trading-tools-part-9-developing-a-first-run-user-setup_600x314.jpg)

# MQL5 Trading Tools (Part 9): Developing a First Run User Setup Wizard for Expert Advisors with Scrollable Guide

[MetaTrader 5](/en/articles/mt5)

          —
          
[Trading](/en/articles/mt5/trading)

        | 
30 September 2025, 09:16

![](https://c.mql5.com/i/icons.svg#views-white-usage)

          1 832
        

[![](https://c.mql5.com/i/icons.svg#comments-white-usage)0](/en/forum/496479)

![Allan Munene Mutiiria](https://c.mql5.com/avatar/2022/11/637df59b-9551.jpg)

[Allan Munene Mutiiria](/en/users/29210372)
 

### Introduction

In our 
[previous article (Part 8)](/en/articles/19059)
, we developed an informational dashboard in 
[MetaQuotes Language 5](https://www.metaquotes.net/en/metatrader5/algorithmic-trading/mql5)
 (MQL5) to monitor multi-symbol positions and account metrics. In Part 9, we create a dynamic first run wizard to orient new users the first time they run a program. First-run setup 
[wizards](https://en.wikipedia.org/wiki/Wizard_(software))
 are essential tools for simplifying the configuration of complex systems, such as Expert Advisors (EAs) in MetaTrader 5, guiding new users through the initial setup and providing an orientation model to ensure optimal performance. In this article, we develop an MQL5 First Run User Setup Wizard for Expert Advisors, featuring a scrollable dashboard with dynamic text, interactive buttons, and a checkbox for streamlined configuration, which will only run once when the program is first launched. We will cover the following topics:
[Understanding the Role and Value of a First Run Setup Guide for Trading Programs](/en/articles/19714#para1)
[Implementation in MQL5](/en/articles/19714#para2)
[Testing the Setup Wizard](/en/articles/19714#para3)
[Conclusion](/en/articles/19714#para4)
By the end, you’ll have an interactive MQL5 wizard to enhance EA initialization, ready to customize for your trading needs—let’s dive in!

### Understanding the Role and Value of a First Run Setup Guide for Trading Programs

A first-run setup guide is a crucial feature for trading programs like Expert Advisors (EAs) in 
[MetaTrader 5](https://www.metatrader5.com/)
, providing step-by-step instructions to configure essential settings such as lot sizes, risk levels, and trading filters, helping traders avoid errors that could lead to losses, such as setting an overly large lot size that risks excessive drawdown. Let's say it is more like an orientation that introduces new users to the program schematics and capabilities. Its value lies in simplifying the onboarding process for traders of all experience levels, ensuring proper program setup from the start, and utilizing a mechanism to remember if the guide has been shown, thereby preventing unnecessary prompts during future initializations to optimize the user experience, especially for traders who repeatedly attach programs to charts.
Our approach is to design an intuitive, scrollable dashboard that displays a clear setup guide with visually distinct text (such as highlighted headings and clickable links for support), interactive buttons for user actions, and a checkbox to let traders choose whether to skip the guide in future runs. We will leverage the MQL5 global variable capability to store the user choice in a variable that saves and recalls the trading terminal build number (the software version) and 
[operating system](https://en.wikipedia.org/wiki/Operating_system)
 (OS) where the program is first run. We will create a centered interface with a header, body, and footer, incorporating dynamic text formatting for readability, scrollable content for comprehensive instructions, and adaptive sizing to fit different screen resolutions. This ensures traders can easily follow steps such as setting risk parameters or enabling AutoTrading, making the setup process seamless and efficient. We will follow the in-built structure for the '
[One Click Trading](https://www.metatrader5.com/en/terminal/help/trading/one_click_trading)
' setup guide as follows.
![APPROACH FRAMEWORK COMPARISON](https://c.mql5.com/2/172/Screenshot_2025-09-25_155135.png)
From the image, you can see the approach we will be taking. We will be adding an optional scaled program image to distinguish it from other programs. In a nutshell, here is a visualization of what we aim to achieve.
![INITIAL RUN WIZARD FRAMEWORK GIF](https://c.mql5.com/2/172/Init_setup_guide_GIF.gif)

### Implementation in MQL5

To create the program in MQL5, open the 
[MetaEditor](https://www.metatrader5.com/en/automated-trading/metaeditor)
, go to the Navigator, locate the Experts folder, click on the "New" tab, and follow the prompts to create the file. Once it is made, in the coding environment, we will need to declare some 
[global variables](/en/docs/basis/variables/global)
 that we will use throughout the program.

```
//+------------------------------------------------------------------+
//|                                      EA Initialization Setup.mq5 |
//|                           Copyright 2025, Allan Munene Mutiiria. |
//|                                   https://t.me/Forex_Algo_Trader |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Allan Munene Mutiiria."
#property link "https://t.me/Forex_Algo_Trader"
#property version "1.00"
#property strict
#property icon "1. Forex Algo-Trader.ico"

//+------------------------------------------------------------------+
//| Global variables for setup                                       |
//+------------------------------------------------------------------+
string GV_SETUP = "";                             //--- Store global variable name with build and OS
string g_scaled_image_resource = "";              //--- Store name of scaled image resource
int g_mainX = 0;                                  //--- Store calculated x-coordinate of main container
int g_mainY = 50;                                 //--- Set starting y-coordinate 50px below chart top
int g_mainWidth = 500;                            //--- Set main container width
int g_headerHeight = 50;                          //--- Set header height
int g_footerHeight = 40;                          //--- Set footer height
int g_padding = 10;                               //--- Set general padding
int g_textPadding = 10;                           //--- Set text padding
int g_spacing = 0;                                //--- Set spacing between header/body/footer
int g_lineSpacing = 3;                            //--- Set spacing between text lines
int g_minBodyHeight = 200;                        //--- Set minimum body height
int g_maxBodyHeight = 400;                        //--- Set maximum body height
int g_bottomMargin = 50;                          //--- Set bottom margin
int g_displayHeight = 0;                          //--- Store calculated display height
int g_mainHeight = 0;                             //--- Store calculated main container height
int g_adjustedLineHeight = 0;                     //--- Store adjusted line height for scrolling
int g_max_scroll = 0;                             //--- Store maximum scroll to prevent overflow
bool scroll_visible = false;                      //--- Track scrollbar visibility
bool mouse_in_body = false;                       //--- Track if mouse is in body
int scroll_pos = 0;                               //--- Store current scroll position
int prev_scroll_pos = -1;                         //--- Store previous scroll position
int slider_height = 20;                           //--- Set default slider height
bool movingStateSlider = false;                   //--- Track slider drag state
int mlbDownX_Slider = 0;                          //--- Store mouse x on slider click
int mlbDownY_Slider = 0;                          //--- Store mouse y on slider click
int mlbDown_YD_Slider = 0;                        //--- Store slider y on click
int g_total_height = 0;                           //--- Store total text height
int g_visible_height = 0;                         //--- Store visible text height
bool checkbox_checked = false;                    //--- Track checkbox state
bool ok_button_hovered = false;                   //--- Track OK button hover
bool cancel_button_hovered = false;               //--- Track Cancel button hover
bool checkbox_hovered = false;                    //--- Track checkbox hover
bool header_cancel_hovered = false;               //--- Track header cancel hover
bool scroll_up_hovered = false;                   //--- Track scroll up button hover
bool scroll_down_hovered = false;                 //--- Track scroll down button hover
bool scroll_slider_hovered = false;               //--- Track scroll slider hover
string ea_name = "Expert Advisor Setup Wizard";   //--- Set EA name
const int MAX_LINES = 100;                        //--- Set maximum text lines

//+------------------------------------------------------------------+
//| Enum for scrollbar mode                                          |
//+------------------------------------------------------------------+
enum ENUM_SCROLLBAR_MODE {                         // Define scrollbar visibility modes
   SCROLL_ALWAYS,                                  // Show scrollbar if needed
   SCROLL_ON_HOVER,                                // Show scrollbar on hover if needed
   SCROLL_NEVER                                    // Never show scrollbar, wheel only
};
ENUM_SCROLLBAR_MODE ScrollbarMode = SCROLL_ALWAYS; // Scrollbar shows when needed and remains

//+------------------------------------------------------------------+
//| Scrollbar object names                                           |
//+------------------------------------------------------------------+
#define SCROLL_LEADER "Setup_Scroll_Leader"        //--- Define scroll leader name
#define SCROLL_UP_REC "Setup_Scroll_Up_Rec"        //--- Define scroll up rectangle name
#define SCROLL_UP_LABEL "Setup_Scroll_Up_Label"    //--- Define scroll up label name
#define SCROLL_DOWN_REC "Setup_Scroll_Down_Rec"    //--- Define scroll down rectangle name
#define SCROLL_DOWN_LABEL "Setup_Scroll_Down_Label" //--- Define scroll down label name
#define SCROLL_SLIDER "Setup_Scroll_Slider"        //--- Define scroll slider name

//+------------------------------------------------------------------+
//| Dashboard object names                                           |
//+------------------------------------------------------------------+
#define SETUP_MAIN "Setup_MainContainer"           //--- Define main container name
#define SETUP_HEADER_BG "Setup_HeaderBg"           //--- Define header background name
#define SETUP_HEADER_IMAGE "Setup_HeaderImage"     //--- Define header image name
#define SETUP_HEADER_TITLE "Setup_HeaderTitle"     //--- Define header title name
#define SETUP_HEADER_SUBTITLE "Setup_HeaderSubtitle" //--- Define header subtitle name
#define SETUP_HEADER_CANCEL "Setup_HeaderCancel"   //--- Define header cancel button name
#define SETUP_BODY_BG "Setup_BodyBg"               //--- Define body background name
#define SETUP_FOOTER_BG "Setup_FooterBg"           //--- Define footer background name
#define SETUP_CHECKBOX_BG "Setup_CheckboxBg"       //--- Define checkbox background name
#define SETUP_CHECKBOX_LABEL "Setup_CheckboxLabel" //--- Define checkbox label name
#define SETUP_CHECKBOX_TEXT "Setup_CheckboxText"   //--- Define checkbox text name
#define SETUP_OK_BUTTON "Setup_OkButton"           //--- Define OK button name
#define SETUP_CANCEL_BUTTON "Setup_CancelButton"   //--- Define Cancel button name

//+------------------------------------------------------------------+
//| Enhanced setup text                                              |
//+------------------------------------------------------------------+
string setup_text =                                //--- Define setup guide text
"\nExpert Advisor Initialization Guide\n\n"
"Welcome to the Expert Advisor Setup Wizard – Your Gateway to Automated Trading in MetaTrader 5!\n\n"
"Unlock the power of algorithmic trading with this comprehensive setup guide. Designed for seamless integration, this wizard ensures your EA is configured optimally for performance, risk management, and reliability across diverse market conditions.\n\n"
"Key Features:\n"
"- Versatile Configuration: Tailor parameters for lot sizing, magic numbers, stop losses, and take profits to suit your trading style and broker requirements.\n"
"- Risk Controls: Implement drawdown limits, position sizing rules, and equity protection mechanisms to safeguard your capital.\n"
"- Filter Integration: Apply time-based, spread, and news filters to avoid unfavorable trading environments and enhance entry precision.\n"
"- Monitoring Tools: Access real-time panels for trade tracking, performance metrics, and alert notifications.\n"
"- Backtesting Support: Optimize settings with historical data, ensuring robust strategies before live deployment.\n"
"- Broker Adaptability: Supports netting and hedging modes, with customizable slippage and execution tolerances.\n\n"
"Initial Setup Instructions:\n"
"1. Attach the EA to a new chart of your selected symbol (e.g., EURUSD) on an appropriate timeframe (e.g., M15 for intraday strategies).\n"
"2. Adjust core inputs: Define risk parameters, enable/disable filters, and set notification preferences to align with your objectives.\n"
"3. Activate AutoTrading: Ensure MT5's AutoTrading is enabled, and verify EA permissions for secure operation.\n"
"4. Customize Interfaces: Toggle visibility of info panels, trade managers, and alerts for an intuitive user experience.\n"
"5. Validate Setup: Run a forward test on demo to confirm functionality and fine-tune based on observed behavior.\n\n"
"Important Notes:\n"
"- Risk Disclaimer: Automated trading carries inherent risks. Always use appropriate leverage and start with conservative settings on a demo account.\n"
"- Compatibility Check: Confirm broker supports required features like hedging; monitor spreads during volatile periods.\n"
"- Optimization Tips: Regularly review performance logs and adjust filters to adapt to evolving market dynamics.\n"
"- Security Measures: Use unique magic numbers and enable two-factor authentication for account protection.\n"
"- Legal Notice: No guarantees of profitability. Trade responsibly and consult professionals as needed.\n\n"
"Contact Methods:\n"
"NB:\n"
"********************************************\n"
" >*** FOR SUPPORT, QUERIES, OR CUSTOMIZATIONS, REACH OUT IMMEDIATELY: ***<\n"
" __________________________________________\n\n"
" 1. Email: mutiiriallan.forex@gmail.com (Primary Support Channel)\n"
" 2. Telegram Channel: @ForexAlgo-Trader (Updates & Community)\n"
" 3. Telegram Group: https://t.me/Forex_Algo_Trader (Direct Assistance & Discussions)\n\n"
"********************************************\n\n"
"Thank you for choosing our Expert Advisor solutions. Configure wisely, trade confidently, and elevate your trading journey! 🚀\n";


```

To set up the Wizard’s foundation, we use 
[global variables](/en/docs/basis/variables/global)
 to manage the dashboard layout. We set up coordinates ("g_mainX", "g_mainY" at 50), dimensions ("g_mainWidth" at 500, "g_headerHeight" at 50, "g_footerHeight" at 40), and padding ("g_padding", "g_textPadding" at 10). We also define spacing ("g_spacing" at 0, "g_lineSpacing" at 3), body height limits ("g_minBodyHeight" at 200, "g_maxBodyHeight" at 400), and margin ("g_bottomMargin" at 50). For scrolling, we set variables like "scroll_visible", "scroll_pos", and "slider_height" to 20. Mouse interaction states include "movingStateSlider" and "mlbDownX_Slider". We add hover flags for buttons and checkboxes. We set "ea_name" as "Expert Advisor Setup Wizard" and "MAX_LINES" at 100.
The "ENUM_SCROLLBAR_MODE" 
[enum](/en/docs/basis/types/integer/enumeration)
 defines scrollbar behavior ("SCROLL_ALWAYS", "SCROLL_ON_HOVER", "SCROLL_NEVER"), defaulting to "SCROLL_ALWAYS". We 
[define](/en/docs/basis/preprosessor/constant)
 constants for object names like "SETUP_MAIN", "SETUP_HEADER_BG", "SCROLL_LEADER", and others for consistent naming of dashboard and scrollbar elements. Finally, we create the "setup_text" string, a comprehensive guide with sections on features, setup instructions, notes, and contact methods formatted with headings and numbered steps, creating a system for organizing the wizard’s interface and content for user interaction. You can modify the positioning or content; we just used arbitrary values. The next thing we will need to configure is the image to be used as the header icon. You can skip this step if you don't want to have it. We will need to convert our image file to a 
[bitmap](https://en.wikipedia.org/wiki/Bitmap)
 (BMP) file. Upon conversion, the image should have properties that depict the following.
![BITMAP FILE IMAGE](https://c.mql5.com/2/172/Screenshot_2025-09-25_164029.png)
From the image, you can see that our image is a 
[Bitmap](https://en.wikipedia.org/wiki/Bitmap)
 file. You don't have to worry about the size or dimensions since we can scale in any direction we want later when needed. Remember to place the file in the same folder as the program file. What we now need to do is add the file as a resource to the program.

```
#resource "1. Forex Algo-Trader SQ.bmp"
#define resourceImg "::1. Forex Algo-Trader SQ.bmp"


```

We use the "
[#resource](/en/docs/runtime/resources)
" directive to include the image file named "1. Forex Algo-Trader SQ.bmp" and define a constant "resourceImg" as "::1. Forex Algo-Trader SQ.bmp" for referencing the image in the program. This will give the wizard’s dashboard a professional and branded user experience. We will now begin the creation of the interface, and we will need some helper functions. Let us define functions to create the necessary rectangle labels, texts, images, and buttons.

```
//+------------------------------------------------------------------+
//| Create rectangle label                                           |
//+------------------------------------------------------------------+
bool createRecLabel(string objName, int xD, int yD, int xS, int yS,
                    color clrBg, int widthBorder, color clrBorder = clrNONE,
                    ENUM_BORDER_TYPE borderType = BORDER_FLAT,
                    ENUM_LINE_STYLE borderStyle = STYLE_SOLID,
                    ENUM_BASE_CORNER corner = CORNER_LEFT_UPPER) {
   ResetLastError();                                              //--- Reset error code
   if (!ObjectCreate(0, objName, OBJ_RECTANGLE_LABEL, 0, 0, 0)) { //--- Create rectangle label
      Print(__FUNCTION__, ": failed to create rec label! Error code = ", GetLastError()); //--- Log failure
      return false;                                               //--- Return failure
   }
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, xD);           //--- Set x distance
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, yD);           //--- Set y distance
   ObjectSetInteger(0, objName, OBJPROP_XSIZE, xS);               //--- Set width
   ObjectSetInteger(0, objName, OBJPROP_YSIZE, yS);               //--- Set height
   ObjectSetInteger(0, objName, OBJPROP_CORNER, corner);          //--- Set corner
   ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, clrBg);          //--- Set background color
   ObjectSetInteger(0, objName, OBJPROP_BORDER_TYPE, borderType); //--- Set border type
   ObjectSetInteger(0, objName, OBJPROP_STYLE, borderStyle);      //--- Set border style
   ObjectSetInteger(0, objName, OBJPROP_WIDTH, widthBorder);      //--- Set border width
   ObjectSetInteger(0, objName, OBJPROP_COLOR, clrBorder);        //--- Set border color
   ObjectSetInteger(0, objName, OBJPROP_BACK, false);             //--- Set to foreground
   ObjectSetInteger(0, objName, OBJPROP_STATE, false);            //--- Disable state
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);       //--- Disable selectability
   ObjectSetInteger(0, objName, OBJPROP_SELECTED, false);         //--- Disable selection
   return true;                                                   //--- Return success
}

//+------------------------------------------------------------------+
//| Create button                                                    |
//+------------------------------------------------------------------+
bool createButton(string objName, int xD, int yD, int xS, int yS,
                  string txt = "", color clrTxt = clrBlack, int fontSize = 12,
                  color clrBg = clrNONE, color clrBorder = clrNONE,
                  string font = "Arial",
                  ENUM_BASE_CORNER corner = CORNER_LEFT_UPPER, bool isBack = false) {
   ResetLastError();                                              //--- Reset error code
   if (!ObjectCreate(0, objName, OBJ_BUTTON, 0, 0, 0)) {          //--- Create button
      Print(__FUNCTION__, ": failed to create the button! Error code = ", GetLastError()); //--- Log failure
      return false;                                               //--- Return failure
   }
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, xD);           //--- Set x distance
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, yD);           //--- Set y distance
   ObjectSetInteger(0, objName, OBJPROP_XSIZE, xS);               //--- Set width
   ObjectSetInteger(0, objName, OBJPROP_YSIZE, yS);               //--- Set height
   ObjectSetInteger(0, objName, OBJPROP_CORNER, corner);          //--- Set corner
   ObjectSetString(0, objName, OBJPROP_TEXT, txt);                //--- Set button text
   ObjectSetInteger(0, objName, OBJPROP_COLOR, clrTxt);           //--- Set text color
   ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, fontSize);      //--- Set font size
   ObjectSetString(0, objName, OBJPROP_FONT, font);               //--- Set font
   ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, clrBg);          //--- Set background color
   ObjectSetInteger(0, objName, OBJPROP_BORDER_COLOR, clrBorder); //--- Set border color
   ObjectSetInteger(0, objName, OBJPROP_BACK, isBack);            //--- Set background/foreground
   ObjectSetInteger(0, objName, OBJPROP_STATE, false);            //--- Disable state
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);       //--- Disable selectability
   ObjectSetInteger(0, objName, OBJPROP_SELECTED, false);         //--- Disable selection
   return true;                                                   //--- Return success
}

//+------------------------------------------------------------------+
//| Create text label                                                |
//+------------------------------------------------------------------+
bool createLabel(string objName, int xD, int yD,
                 string txt, color clrTxt = clrBlack, int fontSize = 12,
                 string font = "Arial",
                 ENUM_BASE_CORNER corner = CORNER_LEFT_UPPER, ENUM_ANCHOR_POINT anchor = ANCHOR_LEFT_UPPER) {
   ResetLastError();                                              //--- Reset error code
   if (!ObjectCreate(0, objName, OBJ_LABEL, 0, 0, 0)) {           //--- Create label
      Print(__FUNCTION__, ": failed to create the label! Error code = ", GetLastError()); //--- Log failure
      return false;                                               //--- Return failure
   }
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, xD);           //--- Set x distance
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, yD);           //--- Set y distance
   ObjectSetInteger(0, objName, OBJPROP_CORNER, corner);          //--- Set corner
   ObjectSetString(0, objName, OBJPROP_TEXT, txt);                //--- Set label text
   ObjectSetInteger(0, objName, OBJPROP_COLOR, clrTxt);           //--- Set text color
   ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, fontSize);      //--- Set font size
   ObjectSetString(0, objName, OBJPROP_FONT, font);               //--- Set font
   ObjectSetInteger(0, objName, OBJPROP_ANCHOR, anchor);          //--- Set anchor
   ObjectSetInteger(0, objName, OBJPROP_BACK, false);             //--- Set to foreground
   ObjectSetInteger(0, objName, OBJPROP_STATE, false);            //--- Disable state
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);       //--- Disable selectability
   ObjectSetInteger(0, objName, OBJPROP_SELECTED, false);         //--- Disable selection
   return true;                                                   //--- Return success
}

//+------------------------------------------------------------------+
//| Create bitmap label                                              |
//+------------------------------------------------------------------+
bool createBitmapLabel(string objName, int xD, int yD, int xS, int yS,
                       string bitmapPath, color clr, ENUM_BASE_CORNER corner = CORNER_LEFT_UPPER) {
   ResetLastError();                                              //--- Reset error code
   if (!ObjectCreate(0, objName, OBJ_BITMAP_LABEL, 0, 0, 0)) {    //--- Create bitmap label
      Print(__FUNCTION__, ": failed to create bitmap label! Error code = ", GetLastError()); //--- Log failure
      return false;                                               //--- Return failure
   }
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, xD);           //--- Set x distance
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, yD);           //--- Set y distance
   ObjectSetInteger(0, objName, OBJPROP_XSIZE, xS);               //--- Set width
   ObjectSetInteger(0, objName, OBJPROP_YSIZE, yS);               //--- Set height
   ObjectSetInteger(0, objName, OBJPROP_CORNER, corner);          //--- Set corner
   ObjectSetString(0, objName, OBJPROP_BMPFILE, bitmapPath);      //--- Set bitmap path
   ObjectSetInteger(0, objName, OBJPROP_COLOR, clr);              //--- Set color
   ObjectSetInteger(0, objName, OBJPROP_BACK, false);             //--- Set to foreground
   ObjectSetInteger(0, objName, OBJPROP_STATE, false);            //--- Disable state
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);       //--- Disable selectability
   ObjectSetInteger(0, objName, OBJPROP_SELECTED, false);         //--- Disable selection
   return true;                                                   //--- Return success
}
```

Here, we implement the core graphical components for the interactive dashboard. First, we develop the "createRecLabel" function, which creates a rectangle label (
[OBJ_RECTANGLE_LABEL](/en/docs/constants/objectconstants/enum_object/obj_rectangle_label)
) with specified coordinates, size, background color, border width, type (
[BORDER_FLAT](/en/docs/constants/objectconstants/enum_object_property#enum_border_type)
), style (
[STYLE_SOLID](/en/docs/constants/indicatorconstants/drawstyles#enum_line_style)
), and corner (
[CORNER_LEFT_UPPER](/en/docs/constants/objectconstants/enum_basecorner)
) using the 
[ObjectCreate](/en/docs/objects/objectcreate)
 and 
[ObjectSetInteger](/en/docs/objects/objectsetinteger)
 functions, logging errors with 
[Print](/en/docs/common/print)
 if creation fails, and setting it to non-selectable foreground. Then, we implement the "createButton" function, which creates a button (
[OBJ_BUTTON](/en/docs/constants/objectconstants/enum_object/obj_button)
) with text, color, font size, font (default "Arial"), background, border, and corner, using the same format.
Next, we create the "createLabel" function, which generates a text label (
[OBJ_LABEL](/en/docs/constants/objectconstants/enum_object/obj_label)
) with text, color, font size, font, corner, and anchor (
[ANCHOR_LEFT_UPPER](/en/docs/constants/objectconstants/enum_anchorpoint)
) using similar object creation and property-setting calls, logging errors if needed. Finally, we build the "createBitmapLabel" function, which creates a bitmap label (
[OBJ_BITMAP_LABEL](/en/docs/constants/objectconstants/enum_object/obj_bitmap_label)
) for images with coordinates, size, bitmap path, color, and corner, using "ObjectCreate" and setting properties to ensure non-selectable foreground display, logging any failures. This will make sure we create a system for rendering the wizard’s visual elements, such as containers, buttons, text, and images. 
We can proceed to create some utility functions to help us calculate the height of the dashboard because we want to dynamically center, get the text fonts dynamically as per the screen resolution, so that some texts don't appear too small or too big on different devices, and truncate the text if it is long to avoid potential overflow.

```
//+------------------------------------------------------------------+
//| Calculate font size based on screen DPI                          |
//+------------------------------------------------------------------+
int getFontSizeByDPI(int baseFontSize, int baseDPI = 96) {
   int currentDPI = (int)TerminalInfoInteger(TERMINAL_SCREEN_DPI); //--- Retrieve current screen DPI
   int scaledFontSize = (int)(baseFontSize * (double)baseDPI / currentDPI); //--- Calculate scaled font size
   return scaledFontSize;                                          //--- Return scaled font size
}

//+------------------------------------------------------------------+
//| Calculate dashboard dimensions                                   |
//+------------------------------------------------------------------+
void CalculateDashboardDimensions() {
   long chart_width = ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);   //--- Get chart width
   long chart_height = ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS); //--- Get chart height
   g_mainX = (int)((chart_width - g_mainWidth) / 2); //--- Center main container horizontally
   int available_height = (int)(chart_height - g_mainY - g_bottomMargin - g_headerHeight - g_footerHeight - 2 * g_spacing); //--- Calculate available height
   g_displayHeight = MathMin(g_maxBodyHeight, MathMax(g_minBodyHeight, available_height)); //--- Set display height
   g_mainHeight = g_headerHeight + g_displayHeight + g_footerHeight + 2 * g_spacing; //--- Calculate main container height
}

//+------------------------------------------------------------------+
//| Truncate string                                                  |
//+------------------------------------------------------------------+
string truncateString(string valueStr, int startPos, int lengthStr = -1, int threshHold = 0, bool isEllipsis = false) {
   string result = valueStr;                                        //--- Initialize result
   if (StringLen(valueStr) > threshHold && threshHold > 0) {        //--- Check if truncation needed
      result = StringSubstr(valueStr, startPos, lengthStr);         //--- Extract substring
      if (isEllipsis) result += "...";                              //--- Add ellipsis if needed
   }
   return result;                                                   //--- Return truncated string
}

```

Here, we implement utility functions to ensure adaptive sizing and text formatting. We develop the "getFontSizeByDPI" function, which retrieves the screen 
[DPI](https://en.wikipedia.org/wiki/Dots_per_inch)
 (Dots Per Inch) using 
[TerminalInfoInteger](/en/docs/check/terminalinfointeger)
 with 
[TERMINAL_SCREEN_DPI](/en/docs/constants/environment_state/terminalstatus#enum_terminal_info_integer)
, calculates a scaled font size by adjusting the base font size relative to a standard DPI (96) using a simple ratio, and returns the result for consistent text display across devices.
Then, we create the "CalculateDashboardDimensions" function, which gets the chart’s width and height via 
[ChartGetInteger](/en/docs/chart_operations/chartgetinteger)
 with 
[CHART_WIDTH_IN_PIXELS](/en/docs/constants/chartconstants/enum_chart_property#enum_chart_property_integer)
 and "CHART_HEIGHT_IN_PIXELS", centers the main container horizontally by setting "g_mainX" to half the difference between chart width and "g_mainWidth", computes available height by subtracting "g_mainY", "g_bottomMargin", "g_headerHeight", "g_footerHeight", and twice "g_spacing" from chart height, sets "g_displayHeight" within "g_minBodyHeight" and "g_maxBodyHeight" bounds using 
[MathMin](/en/docs/math/mathmin)
 and 
[MathMax](/en/docs/math/mathmax)
, and calculates "g_mainHeight" as the sum of header, body, footer heights, and spacing.
Finally, we implement the "truncateString" function, which returns the input string unchanged if its length is below a threshold or zero, otherwise extracts a substring with 
[StringSubstr](/en/docs/strings/stringsubstr)
 from "startPos" for "lengthStr" characters, adding an ellipsis if specified, to manage text overflow. With these functions, we can begin the implementation by creating the main dashboard. We will house its logic in a function for modularization.

```
//+------------------------------------------------------------------+
//| Show the setup dashboard                                         |
//+------------------------------------------------------------------+
void ShowDashboard() {
   checkbox_checked = false;                         //--- Reset checkbox state
   createRecLabel(SETUP_MAIN, g_mainX, g_mainY, g_mainWidth, g_mainHeight, C'20,20,20', 1, C'40,40,40', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create main container
   createRecLabel(SETUP_HEADER_BG, g_mainX, g_mainY, g_mainWidth, g_headerHeight, C'45,45,45', 1, C'60,60,60', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create header background

}
```

We implement the "ShowDashboard" function, and first, we reset the checkbox state to false, ensuring a clean start for user interaction. Then, we call "createRecLabel" to draw the main container ("SETUP_MAIN") at coordinates "g_mainX" and "g_mainY" with dimensions "g_mainWidth" and "g_mainHeight", using a dark gray background (C'20,20,20'), a 1-pixel border (C'40,40,40'), flat border type, solid style, and top-left corner alignment.
Next, we use "createRecLabel" to create the header background ("SETUP_HEADER_BG") at the same x-coordinate and "g_mainY", spanning "g_mainWidth" and "g_headerHeight", with a slightly lighter gray background (C'45,45,45') and border (C'60,60,60'), maintaining consistent styling, rendering the foundational visual structure of the wizard’s dashboard. We now need to call this function in the 
[OnInit](/en/docs/event_handlers/oninit)
 event handler.

```
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
   int build = (int)TerminalInfoInteger(TERMINAL_BUILD); //--- Get terminal build number
   string os = TerminalInfoString(TERMINAL_OS_VERSION);  //--- Get operating system version
   StringReplace(os, " ", "_");                          //--- Replace spaces with underscores
   StringReplace(os, ".", "_");                          //--- Replace dots with underscores
   StringReplace(os, ",", "_");                          //--- Replace commas with underscores
   GV_SETUP = "EA_Setup_" + IntegerToString(build) + "_" + os; //--- Set global variable name
   CalculateDashboardDimensions();                       //--- Calculate dashboard dimensions
   if (!GlobalVariableCheck(GV_SETUP)) {                 //--- Check if global variable exists
      Print("Global variable '" + GV_SETUP + "' not found. Creating new one with value FALSE (0.0)."); //--- Log variable creation
      GlobalVariableSet(GV_SETUP, 0.0);                  //--- Set variable to false
      ShowDashboard();                                   //--- Display dashboard
   } else {                                              //--- Variable exists
      double val = GlobalVariableGet(GV_SETUP);          //--- Get variable value
      if (val == 1.0) {                                  //--- Check if set to never show
         // No dashboard
      } else {                                           //--- Show dashboard
         ShowDashboard();                                //--- Display dashboard
      }
   }
   ChartSetInteger(0, CHART_EVENT_MOUSE_MOVE, true);     //--- Enable mouse move events
   ChartSetInteger(0, CHART_EVENT_MOUSE_WHEEL, true);    //--- Enable mouse wheel events
   ChartSetInteger(0, CHART_MOUSE_SCROLL, true);         //--- Enable chart scrolling
   return(INIT_SUCCEEDED);                               //--- Return initialization success
}
```

We proceed to implement the initialization logic to manage the display behavior in the 
[OnInit](/en/docs/event_handlers/oninit)
 function, where we retrieve the MetaTrader 5 terminal build number using 
[TerminalInfoInteger](/en/docs/check/terminalinfointeger)
 with 
[TERMINAL_BUILD](/en/docs/constants/environment_state/terminalstatus#enum_terminal_info_integer)
 and the operating system version with 
[TerminalInfoString](/en/docs/check/terminalinfostring)
 using 
[TERMINAL_OS_VERSION](/en/docs/constants/environment_state/terminalstatus#enum_terminal_info_string)
, replacing spaces, dots, and commas in the OS string with underscores via 
[StringReplace](/en/docs/strings/StringReplace)
 to create a clean global variable name ("GV_SETUP") formatted as "EA_Setup_<build>_<OS>" You could use any other like magic number or program name and version number, it just felt genius and unique to use this combination. We call "CalculateDashboardDimensions" to set up the dashboard’s layout based on chart dimensions.
Then, we check if the global variable exists with 
[GlobalVariableCheck](/en/docs/globals/globalvariablecheck)
; if not, we log its creation with "Print", set it to 0.0 (false) using 
[GlobalVariableSet](/en/docs/globals/globalvariableset)
, and display the dashboard with "ShowDashboard". If the variable exists, we retrieve its value with 
[GlobalVariableGet](/en/docs/globals/globalvariableget)
, showing the dashboard only if the value is not 1.0 (indicating the user chose not to show it again). Finally, we enable mouse move and wheel events with 
[ChartSetInteger](/en/docs/chart_operations/chartsetinteger)
 using 
[CHART_EVENT_MOUSE_MOVE](/en/docs/constants/chartconstants/enum_chart_property#enum_chart_property_integer)
, "CHART_EVENT_MOUSE_WHEEL", and "CHART_MOUSE_SCROLL" to support interactive features, which will be helpful in the 
[OnChartEvent](/en/docs/event_handlers/onchartevent)
 event handler, and return 
[INIT_SUCCEEDED](/en/docs/basis/function/events#enum_init_retcode)
 for successful initialization. Upon compilation, we get the following outcome.
![BASE DASHBOARD WITH HEADER](https://c.mql5.com/2/172/Screenshot_2025-09-25_174130.png)
Since we now have a header section, let us add the image file to it. We will need to scale the image, so let's define the functions to do the heavy lifting, then we can call them to scale our image file.

```
//+------------------------------------------------------------------+
//| Scale image using bicubic interpolation                          |
//+------------------------------------------------------------------+
void ScaleImage(uint &pixels[], int original_width, int original_height, int new_width, int new_height) {
   uint scaled_pixels[];                                               //--- Declare scaled pixel array
   ArrayResize(scaled_pixels, new_width * new_height);                 //--- Resize scaled pixel array
   for (int y = 0; y < new_height; y++) {                              //--- Iterate through new height
      for (int x = 0; x < new_width; x++) {                            //--- Iterate through new width
         double original_x = (double)x * original_width / new_width;   //--- Calculate original x
         double original_y = (double)y * original_height / new_height; //--- Calculate original y
         uint pixel = BicubicInterpolate(pixels, original_width, original_height, original_x, original_y); //--- Interpolate pixel
         scaled_pixels[y * new_width + x] = pixel;                     //--- Store scaled pixel
      }
   }
   ArrayResize(pixels, new_width * new_height);                        //--- Resize original pixel array
   ArrayCopy(pixels, scaled_pixels);                                   //--- Copy scaled pixels
}

//+------------------------------------------------------------------+
//| Perform bicubic interpolation for a single pixel                 |
//+------------------------------------------------------------------+
uint BicubicInterpolate(uint &pixels[], int width, int height, double x, double y) {
   int x0 = (int)x;                                                    //--- Get integer x coordinate
   int y0 = (int)y;                                                    //--- Get integer y coordinate
   double fractional_x = x - x0;                                       //--- Calculate fractional x
   double fractional_y = y - y0;                                       //--- Calculate fractional y
   int x_indices[4], y_indices[4];                                     //--- Declare index arrays
   for (int i = -1; i <= 2; i++) {                                     //--- Calculate indices
      x_indices[i + 1] = MathMin(MathMax(x0 + i, 0), width - 1);       //--- Clamp x indices
      y_indices[i + 1] = MathMin(MathMax(y0 + i, 0), height - 1);      //--- Clamp y indices
   }
   uint neighborhood_pixels[16];                                       //--- Declare neighborhood pixels
   for (int j = 0; j < 4; j++) {                                       //--- Iterate y indices
      for (int i = 0; i < 4; i++) {                                    //--- Iterate x indices
         neighborhood_pixels[j * 4 + i] = pixels[y_indices[j] * width + x_indices[i]]; //--- Store pixel
      }
   }
   uchar alpha_components[16], red_components[16], green_components[16], blue_components[16]; //--- Declare color components
   for (int i = 0; i < 16; i++) {                                      //--- Extract components
      GetArgb(neighborhood_pixels[i], alpha_components[i], red_components[i], green_components[i], blue_components[i]); //--- Get ARGB components
   }
   uchar alpha_out = (uchar)BicubicInterpolateComponent(alpha_components, fractional_x, fractional_y); //--- Interpolate alpha
   uchar red_out = (uchar)BicubicInterpolateComponent(red_components, fractional_x, fractional_y); //--- Interpolate red
   uchar green_out = (uchar)BicubicInterpolateComponent(green_components, fractional_x, fractional_y); //--- Interpolate green
   uchar blue_out = (uchar)BicubicInterpolateComponent(blue_components, fractional_x, fractional_y); //--- Interpolate blue
   return (alpha_out << 24) | (red_out << 16) | (green_out << 8) | blue_out; //--- Combine components
}

//+------------------------------------------------------------------+
//| Perform bicubic interpolation for a single color component       |
//+------------------------------------------------------------------+
double BicubicInterpolateComponent(uchar &components[], double fractional_x, double fractional_y) {
   double weights_x[4];                                                 //--- Declare x weights
   double t = fractional_x;                                             //--- Set x fraction
   weights_x[0] = (-0.5 * t * t * t + t * t - 0.5 * t);                 //--- Calculate x weight 0
   weights_x[1] = (1.5 * t * t * t - 2.5 * t * t + 1);                  //--- Calculate x weight 1
   weights_x[2] = (-1.5 * t * t * t + 2 * t * t + 0.5 * t);             //--- Calculate x weight 2
   weights_x[3] = (0.5 * t * t * t - 0.5 * t * t);                      //--- Calculate x weight 3
   double y_values[4];                                                  //--- Declare y values
   for (int j = 0; j < 4; j++) {                                        //--- Iterate y indices
      y_values[j] = weights_x[0] * components[j * 4 + 0] + weights_x[1] * components[j * 4 + 1] +
                    weights_x[2] * components[j * 4 + 2] + weights_x[3] * components[j * 4 + 3]; //--- Calculate y value
   }
   double weights_y[4];                                                 //--- Declare y weights
   t = fractional_y;                                                    //--- Set y fraction
   weights_y[0] = (-0.5 * t * t * t + t * t - 0.5 * t);                 //--- Calculate y weight 0
   weights_y[1] = (1.5 * t * t * t - 2.5 * t * t + 1);                  //--- Calculate y weight 1
   weights_y[2] = (-1.5 * t * t * t + 2 * t * t + 0.5 * t);             //--- Calculate y weight 2
   weights_y[3] = (0.5 * t * t * t - 0.5 * t * t);                      //--- Calculate y weight 3
   double result = weights_y[0] * y_values[0] + weights_y[1] * y_values[1] +
                   weights_y[2] * y_values[2] + weights_y[3] * y_values[3]; //--- Calculate final value
   return MathMax(0, MathMin(255, result));        //--- Clamp result to valid range
}

//+------------------------------------------------------------------+
//| Extract ARGB components from a pixel                             |
//+------------------------------------------------------------------+
void GetArgb(uint pixel, uchar &alpha, uchar &red, uchar &green, uchar &blue) {
   alpha = (uchar)((pixel >> 24) & 0xFF);                               //--- Extract alpha component
   red = (uchar)((pixel >> 16) & 0xFF);                                 //--- Extract red component
   green = (uchar)((pixel >> 8) & 0xFF);                                //--- Extract green component
   blue = (uchar)(pixel & 0xFF);                                        //--- Extract blue component
}
```

Here, we implement image processing functions to enhance the visual quality. First, we develop the "ScaleImage" function, which resizes an image by creating a new pixel array with 
[ArrayResize](/en/docs/array/arrayresize)
 for the target dimensions ("new_width" x "new_height"), iterating through each pixel, mapping coordinates to the original image using proportional scaling, and calling "BicubicInterpolate" to compute the interpolated pixel value, storing it in the scaled array before copying back to the original array with the 
[ArrayCopy](/en/docs/array/arraycopy)
 function.
Then, we create the "BicubicInterpolate" function, which calculates a pixel’s color at non-integer coordinates ("x", "y") by selecting a 4x4 neighborhood of pixels, clamping indices with 
[MathMin](/en/docs/math/mathmin)
 and 
[MathMax](/en/docs/math/mathmax)
 to stay within the image bounds, extracting 
[ARGB components](https://en.wikipedia.org/wiki/RGBA_color_model)
 with "GetArgb", interpolating each component using "BicubicInterpolateComponent", and combining them into a final pixel value with 
[bitwise](/en/docs/basis/operations/bit)
 operations. Next, we implement "BicubicInterpolateComponent", which applies bicubic interpolation to a single color component by calculating cubic weights for x and y fractional coordinates, computing intermediate y-values from a 4x4 grid, and combining them with y-weights, clamping the result between 0 and 255. Finally, the "GetArgb" function extracts alpha, red, green, and blue components from a pixel using 
[bitwise shifts](/en/docs/basis/operations/bit)
 and masks. This will adapt a smoothly scaling approach for our images to fit the dashboard or designated area. We can now call this function to scale our resource image and display it.

```
uint img_pixels[];                                       //--- Declare pixel array for image
uint orig_width = 0, orig_height = 0;                    //--- Initialize image dimensions
bool image_loaded = ResourceReadImage(resourceImg, img_pixels, orig_width, orig_height); //--- Load image resource
if (image_loaded && orig_width > 0 && orig_height > 0) { //--- Check image load success
   ScaleImage(img_pixels, (int)orig_width, (int)orig_height, 40, 40); //--- Scale image to 40x40
   g_scaled_image_resource = "::SetupHeaderImageScaled"; //--- Set scaled image resource name
   if (ResourceCreate(g_scaled_image_resource, img_pixels, 40, 40, 0, 0, 40, COLOR_FORMAT_ARGB_NORMALIZE)) { //--- Create scaled resource
      createBitmapLabel(SETUP_HEADER_IMAGE, g_mainX + 5, g_mainY + (g_headerHeight - 40)/2, 40, 40, g_scaled_image_resource, clrWhite, CORNER_LEFT_UPPER); //--- Create scaled image label
   } else {                                              //--- Handle resource creation failure
      Print("Failed to create scaled image resource");   //--- Log failure
      createBitmapLabel(SETUP_HEADER_IMAGE, g_mainX + 5, g_mainY + (g_headerHeight - 40)/2, 40, 40, resourceImg, clrWhite, CORNER_LEFT_UPPER); //--- Use original image
   }
} else {                                                 //--- Handle image load failure
   Print("Failed to load original image resource");      //--- Log failure
   createBitmapLabel(SETUP_HEADER_IMAGE, g_mainX + 5, g_mainY + (g_headerHeight - 40)/2, 40, 40, resourceImg, clrWhite, CORNER_LEFT_UPPER); //--- Use original image
}

```

To implement the image loading and scaling logic, we declare a pixel array "img_pixels" and initialize dimensions "orig_width" and "orig_height" to zero, then load the resource image with "ResourceReadImage" using "resourceImg", checking if successful ("image_loaded" and dimensions > 0); if true, we call "ScaleImage" to resize to 40x40 pixels - which you can modify, set "g_scaled_image_resource" to "::SetupHeaderImageScaled", and create a new resource with 
[ResourceCreate](/en/docs/common/resourcecreate)
 in ARGB format, followed by "createBitmapLabel" to display the scaled image at the header’s position with white color. If resource creation fails, we log the instance and fall back to the original image; if the load fails, we log and use the original "resourceImg" directly with the "createBitmapLabel" function. Upon compilation, we get the following outcome.
![HEADER WITH SCALED IMAGE FILE](https://c.mql5.com/2/172/Screenshot_2025-09-25_175529.png)
Now that we have the image file ready, we move on to implementing the other core elements as follows.

```
string truncated_name = truncateString(ea_name, 0, -1, 20, true); //--- Truncate EA name
int titleFontSize = getFontSizeByDPI(14);           //--- Calculate title font size
createLabel(SETUP_HEADER_TITLE, g_mainX + 5 + 40 + 5, g_mainY + 5, truncated_name, clrWhite, titleFontSize, "Arial Bold", CORNER_LEFT_UPPER, ANCHOR_LEFT_UPPER); //--- Create title label
int subtitleFontSize = getFontSizeByDPI(10);        //--- Calculate subtitle font size
createLabel(SETUP_HEADER_SUBTITLE, g_mainX + 5 + 40 + 5, g_mainY + 25, "Streamlined configuration for optimal performance", C'200,200,200', subtitleFontSize, "Arial", CORNER_LEFT_UPPER, ANCHOR_LEFT_UPPER); //--- Create subtitle label
int headerCancelFontSize = getFontSizeByDPI(16);    //--- Calculate cancel button font size
createLabel(SETUP_HEADER_CANCEL, g_mainX + g_mainWidth - 25, g_mainY + 10, ShortToString(0x274C), C'150,150,150', headerCancelFontSize, "Arial Rounded MT Bold", CORNER_LEFT_UPPER, ANCHOR_LEFT_UPPER); //--- Create header cancel button
int bodyY = g_mainY + g_headerHeight + g_spacing;   //--- Calculate body y position
createRecLabel(SETUP_BODY_BG, g_mainX, bodyY, g_mainWidth, g_displayHeight, C'25,25,25', 1, C'40,40,40', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create body background
int footerY = bodyY + g_displayHeight + g_spacing;  //--- Calculate footer y position
createRecLabel(SETUP_FOOTER_BG, g_mainX, footerY, g_mainWidth, g_footerHeight, C'35,35,35', 1, C'50,50,50', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create footer background
createRecLabel(SETUP_CHECKBOX_BG, g_mainX + 10, footerY + (g_footerHeight - 20)/2, 20, 20, C'60,60,60', 1, C'80,80,80', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create checkbox background
int checkboxLabelFontSize = getFontSizeByDPI(17);   //--- Calculate checkbox label font size
createLabel(SETUP_CHECKBOX_LABEL, g_mainX + 10 + 2, footerY + (g_footerHeight - 20)/2, " ", clrWhite, checkboxLabelFontSize, "Wingdings", CORNER_LEFT_UPPER, ANCHOR_LEFT_UPPER); //--- Create checkbox label
int checkboxTextFontSize = getFontSizeByDPI(10);    //--- Calculate checkbox text font size
createLabel(SETUP_CHECKBOX_TEXT, g_mainX + 40, footerY + (g_footerHeight - 20)/2 + 2, "Do not show this guide again", clrWhite, checkboxTextFontSize, "Calibri Bold", CORNER_LEFT_UPPER, ANCHOR_LEFT_UPPER); //--- Create checkbox text
int buttonFontSize = getFontSizeByDPI(12);          //--- Calculate button font size
color buttonBg = C'60,60,60';                       //--- Set button background color
color buttonBorder = C'80,80,80';                   //--- Set button border color
createButton(SETUP_OK_BUTTON, g_mainX + g_mainWidth - 170 - 10, footerY + 5, 80, 30, "OK", clrWhite, buttonFontSize, buttonBg, buttonBorder, "Arial Rounded MT Bold", CORNER_LEFT_UPPER, false); //--- Create OK button
createButton(SETUP_CANCEL_BUTTON, g_mainX + g_mainWidth - 80 - 10, footerY + 5, 80, 30, "Cancel", clrWhite, buttonFontSize, buttonBg, buttonBorder, "Arial Rounded MT Bold", CORNER_LEFT_UPPER, false); //--- Create Cancel button
int textFontSize = getFontSizeByDPI(10);            //--- Calculate text font size
for (int i = 0; i < MAX_LINES; i++) {               //--- Create text line labels
   string lineName = "Setup_ResponseLine_" + IntegerToString(i); //--- Generate line name
   createLabel(lineName, 0, -100, " ", clrWhite, textFontSize, "Arial", CORNER_LEFT_UPPER, ANCHOR_LEFT_UPPER); //--- Create line label
}

```

Here, we implement the remaining dashboard components for the Wizard to complete its user interface. We truncate the program's name to 20 characters with "truncateString" for readability and create a title label ("SETUP_HEADER_TITLE") with "createLabel" at calculated coordinates, using a DPI-adjusted font size from "getFontSizeByDPI" (base 14) and "Arial Bold". Next, we add a subtitle label ("SETUP_HEADER_SUBTITLE") with fixed text and a smaller DPI-adjusted font size (base 10), followed by a header cancel button ("SETUP_HEADER_CANCEL") using a 
[Unicode](https://en.wikipedia.org/wiki/Unicode)
 cross (0x274C) in "Arial Rounded MT Bold". Here is its description.
![CROSS MARK DETAILS](https://c.mql5.com/2/172/Screenshot_2025-09-25_180228.png)
We calculate the body’s y-position ("bodyY") and create its background ("SETUP_BODY_BG") with "createRecLabel" using a dark gray background (C'25,25,25') and border, spanning "g_mainWidth" and "g_displayHeight". Then, we compute the footer’s y-position ("footerY") and create its background ("SETUP_FOOTER_BG") with a lighter gray, followed by a checkbox background ("SETUP_CHECKBOX_BG") as a 20x20 square, a checkbox label ("SETUP_CHECKBOX_LABEL") with an empty 
[Wingdings](https://en.wikipedia.org/wiki/Wingdings)
 character, and its text ("SETUP_CHECKBOX_TEXT") stating "Do not show this guide again" in "Calibri Bold". We add OK and Cancel buttons ("SETUP_OK_BUTTON", "SETUP_CANCEL_BUTTON") with "createButton" at DPI-adjusted font size (base 12), using consistent gray colors. Finally, we loop to create up to "MAX_LINES" text labels ("Setup_ResponseLine_") with "createLabel", initially hidden off-screen, for dynamic text display. This creates a system for rendering the wizard’s interactive and visually cohesive dashboard. We get the following outcome upon running the program.
![WIZARD ENHANCED ELEMENTS](https://c.mql5.com/2/172/Screenshot_2025-09-25_180512.png)
Since we now have the dashboard with the basic elements, we need to update the display to show the wizard's designated labels. Since having rich multi-line text labels in MQL5 is not as easy as there is no direct way of achieving that, we will need to use a text wrapping approach.

```
//+------------------------------------------------------------------+
//| Get line color based on content                                  |
//+------------------------------------------------------------------+
color GetLineColor(string lineText) {
   if (StringLen(lineText) == 0 || lineText == " ") return C'25,25,25'; //--- Set invisible for empty lines
   if (StringFind(lineText, "mutiiriallan.forex@gmail.com") >= 0) return C'255,100,100'; //--- Set light red for email
   if (StringFind(lineText, "https://t.me/Forex_Algo_Trader") >= 0) return C'150,100,200'; //--- Set light purple for group link
   if (StringFind(lineText, "@ForexAlgo-Trader") >= 0) return C'100,150,255'; //--- Set light blue for channel link
   if (StringFind(lineText, "http") >= 0 || StringFind(lineText, "t.me") >= 0) return C'100,150,255'; //--- Set light blue for general links
   string start3 = StringSubstr(lineText, 0, 3);    //--- Get first three characters
   if ((start3 == "1. " || start3 == "2. " || start3 == "3. " || start3 == "4. " || start3 == "5. ") &&
       StringFind(lineText, "Initial Setup Instructions") < 0) { //--- Check instruction lines
      return C'255,200,100';                        //--- Set light yellow for instructions
   }
   return clrWhite;                                 //--- Default to white
}

//+------------------------------------------------------------------+
//| Wrap text with colors                                            |
//+------------------------------------------------------------------+
void WrapText(const string inputText, const string font, const int fontSize, const int maxWidth, string &wrappedLines[], color &wrappedColors[], int offset = 0) {
   const int maxChars = 60;                         //--- Set maximum characters per line
   ArrayResize(wrappedLines, 0);                    //--- Clear wrapped lines array
   ArrayResize(wrappedColors, 0);                   //--- Clear wrapped colors array
   TextSetFont(font, fontSize);                     //--- Set font
   string paragraphs[];                             //--- Declare paragraphs array
   int numParagraphs = StringSplit(inputText, '\n', paragraphs); //--- Split text into paragraphs
   for (int p = 0; p < numParagraphs; p++) {        //--- Iterate through paragraphs
      string para = paragraphs[p];                  //--- Get current paragraph
      color paraColor = GetLineColor(para);         //--- Get paragraph color
      if (StringLen(para) == 0) {                   //--- Check empty paragraph
         int size = ArraySize(wrappedLines);        //--- Get current size
         ArrayResize(wrappedLines, size + 1);       //--- Resize lines array
         wrappedLines[size] = " ";                  //--- Add empty line
         ArrayResize(wrappedColors, size + 1);      //--- Resize colors array
         wrappedColors[size] = C'25,25,25';         //--- Set invisible color
         continue;                                  //--- Skip to next
      }
      string words[];                               //--- Declare words array
      int numWords = StringSplit(para, ' ', words); //--- Split paragraph into words
      string currentLine = "";                      //--- Initialize current line
      for (int w = 0; w < numWords; w++) {          //--- Iterate through words
         string testLine = currentLine + (StringLen(currentLine) > 0 ? " " : "") + words[w]; //--- Build test line
         uint wid, hei;                             //--- Declare width and height
         TextGetSize(testLine, wid, hei);           //--- Get test line size
         int textWidth = (int)wid;                  //--- Get text width
         if (textWidth + offset <= maxWidth && StringLen(testLine) <= maxChars) { //--- Check line fits
            currentLine = testLine;                 //--- Update current line
         } else {                                   //--- Line exceeds limits
            if (StringLen(currentLine) > 0) {       //--- Check non-empty line
               int size = ArraySize(wrappedLines);  //--- Get current size
               ArrayResize(wrappedLines, size + 1); //--- Resize lines array
               wrappedLines[size] = currentLine;    //--- Add line
               ArrayResize(wrappedColors, size + 1); //--- Resize colors array
               wrappedColors[size] = paraColor;     //--- Add color
            }
            currentLine = words[w];                 //--- Start new line
            TextGetSize(currentLine, wid, hei);     //--- Get new line size
            textWidth = (int)wid;                   //--- Update text width
            if (textWidth + offset > maxWidth || StringLen(currentLine) > maxChars) { //--- Check word too long
               string wrappedWord = "";             //--- Initialize wrapped word
               for (int c = 0; c < StringLen(words[w]); c++) { //--- Iterate through characters
                  string testWord = wrappedWord + StringSubstr(words[w], c, 1); //--- Build test word
                  TextGetSize(testWord, wid, hei);  //--- Get test word size
                  int wordWidth = (int)wid;         //--- Get word width
                  if (wordWidth + offset > maxWidth || StringLen(testWord) > maxChars) { //--- Check word fits
                     if (StringLen(wrappedWord) > 0) { //--- Check non-empty word
                        int size = ArraySize(wrappedLines); //--- Get current size
                        ArrayResize(wrappedLines, size + 1); //--- Resize lines array
                        wrappedLines[size] = wrappedWord; //--- Add wrapped word
                        ArrayResize(wrappedColors, size + 1); //--- Resize colors array
                        wrappedColors[size] = paraColor; //--- Add color
                     }
                     wrappedWord = StringSubstr(words[w], c, 1); //--- Start new word
                  } else {                          //--- Word fits
                     wrappedWord = testWord;        //--- Update wrapped word
                  }
               }
               currentLine = wrappedWord;          //--- Set current line to wrapped word
               if (StringLen(currentLine) > 0) {   //--- Check non-empty line
                  int size = ArraySize(wrappedLines); //--- Get current size
                  ArrayResize(wrappedLines, size + 1); //--- Resize lines array
                  wrappedLines[size] = currentLine; //--- Add line
                  ArrayResize(wrappedColors, size + 1); //--- Resize colors array
                  wrappedColors[size] = paraColor; //--- Add color
               }
               currentLine = "";                   //--- Reset current line
            }
         }
      }
      if (StringLen(currentLine) > 0) {            //--- Check remaining line
         int size = ArraySize(wrappedLines);       //--- Get current size
         ArrayResize(wrappedLines, size + 1);      //--- Resize lines array
         wrappedLines[size] = currentLine;         //--- Add line
         ArrayResize(wrappedColors, size + 1);     //--- Resize colors array
         wrappedColors[size] = paraColor;          //--- Add color
      }
   }
}
```

Here, we implement text formatting and color-coding logic to enhance the readability of the guide. In the "GetLineColor" function, we assign colors based on content: empty lines get an invisible dark gray (C'25,25,25'), email addresses use light red (C'255,100,100'), group links use light purple (C'150,100,200'), author links and other uniform resource locator (
[URLs](https://en.wikipedia.org/wiki/URL)
) use light blue (C'100,150,255'), instruction lines starting with "1. " to "5. " (excluding the heading) use light yellow (C'255,200,100'), and all others default to white. You can define any of your choice; we just included this to provide an insight into how rich text encoding can be achieved.
In the "WrapText" function, we split the input text into paragraphs using 
[StringSplit](/en/docs/strings/StringSplit)
 on newlines, set the font with 
[TextSetFont](/en/docs/objects/textsetfont)
, and for each paragraph, retrieve its color with "GetLineColor", adding empty paragraphs as a space with invisible color. We split paragraphs into words with "StringSplit", building lines by adding words if they fit within "maxWidth" and a 60-character limit, though the maximum limit is 63, using 
[TextGetSize](/en/docs/objects/textgetsize)
, otherwise starting a new line; for oversized words, we split character by character, adding segments to new lines if they exceed limits, ensuring each line is stored in "wrappedLines" with its color in "wrappedColors" using the 
[ArrayResize](/en/docs/array/arrayresize)
 function. With this function, we can update the display. We will ensure that logic is a function.

```
//+------------------------------------------------------------------+
//| Get text height                                                  |
//+------------------------------------------------------------------+
int TextGetHeight(string text, string font, int fontSize) {
   uint wid, hei;                                   //--- Declare width and height
   TextSetFont(font, fontSize);                     //--- Set font
   TextGetSize(text, wid, hei);                     //--- Get text size
   return (int)hei;                                 //--- Return height
}

//+------------------------------------------------------------------+
//| Check if line is a heading                                       |
//+------------------------------------------------------------------+
bool IsHeading(string lineText) {
   if (StringLen(lineText) == 0) return false;      //--- Return false for empty lines
   if (StringGetCharacter(lineText, StringLen(lineText) - 1) == ':') return true; //--- Check for colon
   if (StringFind(lineText, "Expert Advisor Initialization Guide") >= 0) return true; //--- Check main heading
   if (StringFind(lineText, "Key Features") >= 0) return true; //--- Check features heading
   if (StringFind(lineText, "Initial Setup Instructions") >= 0) return true; //--- Check instructions heading
   if (StringFind(lineText, "Important Notes") >= 0) return true; //--- Check notes heading
   if (StringFind(lineText, "Contact Methods") >= 0) return true; //--- Check contact heading
   if (StringFind(lineText, "NB:") >= 0) return true; //--- Check NB heading
   return false;                                    //--- Default to false
}

//+------------------------------------------------------------------+
//| Update body display with scrollable text                         |
//+------------------------------------------------------------------+
void UpdateBodyDisplay() {
   int textX = g_mainX + g_padding + g_textPadding; //--- Set text x position
   int textY = g_mainY + g_headerHeight + g_spacing; //--- Set text y position
   int fullMaxWidth = g_mainWidth - 2 * g_padding - 2 * g_textPadding; //--- Calculate max text width
   string font = "Arial";                           //--- Set font
   int fontSize = getFontSizeByDPI(10);             //--- Calculate font size
   int lineHeight = TextGetHeight("A", font, fontSize); //--- Get line height
   int adjustedLineHeight = lineHeight + g_lineSpacing; //--- Calculate adjusted line height
   g_adjustedLineHeight = adjustedLineHeight;       //--- Store adjusted line height
   int visibleHeight = g_displayHeight;             //--- Set visible height
   g_visible_height = visibleHeight;                //--- Store visible height
   static string wrappedLines[];                    //--- Store wrapped text lines
   static color wrappedColors[];                    //--- Store line colors
   static bool wrapped = false;                     //--- Track if text wrapped
   if (!wrapped) {                                  //--- Check if text needs wrapping
      WrapText(setup_text, font, fontSize, fullMaxWidth, wrappedLines, wrappedColors); //--- Wrap text
      wrapped = true;                               //--- Set wrapped flag
   }
   int numLines = ArraySize(wrappedLines);          //--- Get number of lines
   g_total_height = numLines * adjustedLineHeight;  //--- Calculate total text height
   bool need_scroll = g_total_height > visibleHeight; //--- Check if scrollbar needed
   bool should_show_scrollbar = false;              //--- Initialize scrollbar visibility
   int reserved_width = 0;                          //--- Initialize reserved width
   if (need_scroll && ScrollbarMode != SCROLL_NEVER) { //--- Check scrollbar mode
      should_show_scrollbar = true;                 //--- Enable scrollbar
      reserved_width = 16;                          //--- Reserve scrollbar width
   }
   if (reserved_width > 0 && fullMaxWidth - reserved_width != fullMaxWidth) { //--- Check width change
      WrapText(setup_text, font, fontSize, fullMaxWidth - reserved_width, wrappedLines, wrappedColors); //--- Rewrap text
      numLines = ArraySize(wrappedLines);           //--- Update line count
      g_total_height = numLines * adjustedLineHeight; //--- Update total height
   }

   int startLine = scroll_pos / adjustedLineHeight; //--- Calculate start line
   int currentY = textY;                            //--- Set current y position
   int labelIndex = 0;                              //--- Initialize label index
   for (int line = startLine; line < numLines; line++) { //--- Iterate visible lines
      string lineText = wrappedLines[line];         //--- Get line text
      if (StringLen(lineText) == 0) lineText = " "; //--- Set empty lines to space
      color lineColor = wrappedColors[line];        //--- Get line color
      if (IsHeading(lineText)) lineColor = clrBlue; //--- Set blue for headings
      if (currentY + adjustedLineHeight > textY + visibleHeight) break; //--- Prevent overflow
      string lineName = "Setup_ResponseLine_" + IntegerToString(labelIndex); //--- Generate line name
      if (ObjectFind(0, lineName) >= 0) {          //--- Check if label exists
         ObjectSetString(0, lineName, OBJPROP_TEXT, lineText); //--- Set line text
         ObjectSetInteger(0, lineName, OBJPROP_XDISTANCE, textX); //--- Set x position
         ObjectSetInteger(0, lineName, OBJPROP_YDISTANCE, currentY); //--- Set y position
         ObjectSetInteger(0, lineName, OBJPROP_COLOR, lineColor); //--- Set line color
         string lineFont = IsHeading(lineText) ? "Arial Bold" : "Arial"; //--- Set font
         ObjectSetString(0, lineName, OBJPROP_FONT, lineFont); //--- Set font type
         ObjectSetInteger(0, lineName, OBJPROP_FONTSIZE, fontSize); //--- Set font size
         ObjectSetInteger(0, lineName, OBJPROP_HIDDEN, false); //--- Show label
      }
      currentY += adjustedLineHeight;               //--- Increment y position
      labelIndex++;                                 //--- Increment label index
   }
   for (int i = labelIndex; i < MAX_LINES; i++) {   //--- Hide unused labels
      string lineName = "Setup_ResponseLine_" + IntegerToString(i); //--- Generate line name
      if (ObjectFind(0, lineName) >= 0) {           //--- Check if label exists
         ObjectSetInteger(0, lineName, OBJPROP_HIDDEN, true); //--- Hide label
      }
   }
   ChartRedraw();                                   //--- Redraw chart
}
```

To implement text rendering and scrolling logic to display the guide dynamically, in the "TextGetHeight" function, we set the font and size with 
[TextSetFont](/en/docs/objects/textsetfont)
 and use 
[TextGetSize](/en/docs/objects/textgetsize)
 to calculate the height of a sample character, returning it for consistent line spacing. The "IsHeading" function identifies headings by checking for empty lines, colons at the end, or specific guide section titles (e.g., "Key Features"), returning true if matched. In the "UpdateBodyDisplay" function, we calculate the text area’s position ("textX", "textY") and width ("fullMaxWidth") using padding and container dimensions, set the font to Arial with a DPI-adjusted size from "getFontSizeByDPI", and compute line height with "TextGetHeight" plus "g_lineSpacing", storing it in "g_adjustedLineHeight".
We wrap the guide text with "WrapText" if not already done, calculate total text height ("g_total_height"), and determine scrollbar visibility based on "ScrollbarMode" and text overflow, reserving 16 pixels for the scrollbar if needed and rewrapping text accordingly. We compute the starting line from "scroll_pos", update visible text labels with 
[ObjectSetString](/en/docs/objects/objectsetstring)
 and 
[ObjectSetInteger](/en/docs/objects/ObjectSetInteger)
 for position, color (blue for headings via "IsHeading"), and font, hide unused labels, and redraw the chart. When we call this function in the function to show the dashboard, we get the following outcome.
![INITIALIZED DISPLAY](https://c.mql5.com/2/172/Screenshot_2025-09-25_201506.png)
We can see we have the display ready with the text fitting perfectly in the display area. What we need to do is fetch the logic for displaying the scrollbar when needed.

```
//+------------------------------------------------------------------+
//| Create scrollbar                                                 |
//+------------------------------------------------------------------+
void CreateScrollbar() {
   int bodyY = g_mainY + g_headerHeight + g_spacing; //--- Calculate body y position
   int textAreaY = bodyY;                            //--- Set text area y
   int textAreaHeight = g_displayHeight;             //--- Set text area height
   int scrollbar_x = g_mainX + g_mainWidth - 16 - 1; //--- Calculate scrollbar x
   int scrollbar_width = 16;                         //--- Set scrollbar width
   int button_size = 16;                             //--- Set button size
   int scrollbar_y = textAreaY + 2;                  //--- Calculate scrollbar y
   int scrollbar_height = textAreaHeight - 2 - 2;    //--- Calculate scrollbar height
   createRecLabel(SCROLL_LEADER, scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, C'45,45,45', 1, C'60,60,60', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create scroll leader
   createRecLabel(SCROLL_UP_REC, scrollbar_x, scrollbar_y, scrollbar_width, button_size, C'60,60,60', 1, C'60,60,60', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create scroll up rectangle
   int scrollUpLabelFontSize = getFontSizeByDPI(10); //--- Calculate scroll up font size
   createLabel(SCROLL_UP_LABEL, scrollbar_x + 2, scrollbar_y - 2, CharToString(0x35), C'150,150,150', scrollUpLabelFontSize, "Webdings", CORNER_LEFT_UPPER, ANCHOR_LEFT_UPPER); //--- Create scroll up label
   int down_rec_y = scrollbar_y + scrollbar_height - button_size; //--- Calculate scroll down y
   createRecLabel(SCROLL_DOWN_REC, scrollbar_x, down_rec_y, scrollbar_width, button_size, C'60,60,60', 1, C'60,60,60', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create scroll down rectangle
   createLabel(SCROLL_DOWN_LABEL, scrollbar_x + 2, down_rec_y - 2, CharToString(0x36), C'150,150,150', scrollUpLabelFontSize, "Webdings", CORNER_LEFT_UPPER, ANCHOR_LEFT_UPPER); //--- Create scroll down label
   slider_height = CalculateSliderHeight();          //--- Calculate slider height
   createRecLabel(SCROLL_SLIDER, scrollbar_x, scrollbar_y + button_size, scrollbar_width, slider_height, C'80,80,80', 1, C'100,100,100', BORDER_FLAT, STYLE_SOLID, CORNER_LEFT_UPPER); //--- Create scroll slider
}

//+------------------------------------------------------------------+
//| Delete scrollbar                                                 |
//+------------------------------------------------------------------+
void DeleteScrollbar() {
   string scroll_objects[] = {SCROLL_LEADER, SCROLL_UP_REC, SCROLL_UP_LABEL, SCROLL_DOWN_REC, SCROLL_DOWN_LABEL, SCROLL_SLIDER}; //--- Define scroll objects
   for (int i = 0; i < ArraySize(scroll_objects); i++) { //--- Iterate through objects
      ObjectDelete(0, scroll_objects[i]);            //--- Delete object
   }
   ChartRedraw();                                    //--- Redraw chart
}

//+------------------------------------------------------------------+
//| Calculate slider height                                          |
//+------------------------------------------------------------------+
int CalculateSliderHeight() {
   int textAreaHeight = g_displayHeight;            //--- Get text area height
   int scroll_area_height = textAreaHeight - 32;    //--- Calculate scroll area height
   int slider_min_height = 20;                      //--- Set minimum slider height
   if (g_total_height <= g_visible_height) return scroll_area_height; //--- Return full height if no scroll
   double visible_ratio = (double)g_visible_height / g_total_height; //--- Calculate visible ratio
   int height = (int)MathFloor(scroll_area_height * visible_ratio); //--- Calculate slider height
   return MathMax(slider_min_height, height);       //--- Return minimum or calculated height
}

//+------------------------------------------------------------------+
//| Update slider position                                           |
//+------------------------------------------------------------------+
void UpdateSliderPosition() {
   int bodyY = g_mainY + g_headerHeight + g_spacing; //--- Calculate body y position
   int textAreaY = bodyY;                           //--- Set text area y
   int textAreaHeight = g_displayHeight;            //--- Set text area height
   int scroll_area_height = textAreaHeight - 32;    //--- Calculate scroll area height
   int slider_min_y = textAreaY + 16;               //--- Set minimum slider y
   if (g_max_scroll <= 0) return;                   //--- Exit if no scroll
   double scroll_ratio = (double)scroll_pos / g_max_scroll; //--- Calculate scroll ratio
   int slider_max_y = slider_min_y + scroll_area_height - slider_height; //--- Calculate max slider y
   int new_y = slider_min_y + (int)MathRound(scroll_ratio * (slider_max_y - slider_min_y)); //--- Calculate new y
   ObjectSetInteger(0, SCROLL_SLIDER, OBJPROP_YDISTANCE, new_y); //--- Set slider y position
}

//+------------------------------------------------------------------+
//| Update scrollbar button colors                                   |
//+------------------------------------------------------------------+
void UpdateButtonColors() {
   int max_scroll = g_max_scroll;                   //--- Get max scroll
   color up_color = (scroll_pos == 0) ? C'80,80,80' : (scroll_up_hovered ? C'100,100,100' : C'150,150,150'); //--- Set up button color
   color down_color = (scroll_pos >= max_scroll) ? C'80,80,80' : (scroll_down_hovered ? C'100,100,100' : C'150,150,150'); //--- Set down button color
   ObjectSetInteger(0, SCROLL_UP_LABEL, OBJPROP_COLOR, up_color); //--- Update up label color
   ObjectSetInteger(0, SCROLL_DOWN_LABEL, OBJPROP_COLOR, down_color); //--- Update down label color
   ObjectSetInteger(0, SCROLL_UP_REC, OBJPROP_BGCOLOR, scroll_up_hovered ? C'70,70,70' : C'60,60,60'); //--- Update up rectangle color
   ObjectSetInteger(0, SCROLL_DOWN_REC, OBJPROP_BGCOLOR, scroll_down_hovered ? C'70,70,70' : C'60,60,60'); //--- Update down rectangle color
}

//+------------------------------------------------------------------+
//| Scroll up                                                        |
//+------------------------------------------------------------------+
void ScrollUp() {
   if (g_adjustedLineHeight > 0 && scroll_pos > 0) { //--- Check scroll possible
      scroll_pos = MathMax(0, scroll_pos - g_adjustedLineHeight); //--- Decrease scroll position
      UpdateBodyDisplay();                           //--- Update body display
      if (scroll_visible) {                          //--- Check scrollbar visible
         UpdateSliderPosition();                     //--- Update slider position
         UpdateButtonColors();                       //--- Update button colors
      }
   }
}

//+------------------------------------------------------------------+
//| Scroll down                                                      |
//+------------------------------------------------------------------+
void ScrollDown() {
   int max_scroll = g_max_scroll;                    //--- Get max scroll
   if (g_adjustedLineHeight > 0 && scroll_pos < max_scroll) { //--- Check scroll possible
      scroll_pos = MathMin(max_scroll, scroll_pos + g_adjustedLineHeight); //--- Increase scroll position
      UpdateBodyDisplay();                           //--- Update body display
      if (scroll_visible) {                          //--- Check scrollbar visible
         UpdateSliderPosition();                     //--- Update slider position
         UpdateButtonColors();                       //--- Update button colors
      }
   }
}

```

To implement the scrollbar functionality to enable smooth navigation of the setup guide, we create the "CreateScrollbar" function and in it we calculate the scrollbar’s position and dimensions based on the body’s y-coordinate ("bodyY"), setting "scrollbar_x" to the right edge of the main container and using a 16-pixel width, creating a leader rectangle ("SCROLL_LEADER") with "createRecLabel" for the scrollbar track, and up/down buttons ("SCROLL_UP_REC", "SCROLL_DOWN_REC") with labels ("SCROLL_UP_LABEL", "SCROLL_DOWN_LABEL") using Webdings arrows (0x35, 0x36). We call "CalculateSliderHeight" to determine the slider’s height based on the visible text ratio, creating the slider ("SCROLL_SLIDER") with "createRecLabel". The "DeleteScrollbar" function removes all scrollbar objects ("SCROLL_LEADER", etc.) using 
[ObjectDelete](/en/docs/objects/objectdelete)
 and redraws the chart.
In "CalculateSliderHeight", we compute the slider height as a proportion of the display height to total text height, ensuring a minimum of 20 pixels. The "UpdateSliderPosition" function adjusts the slider’s y-position using a scroll ratio derived from "scroll_pos" and "g_max_scroll", setting it with "ObjectSetInteger". In "UpdateButtonColors", we update the up/down button colors based on scroll position and hover state for dynamic visual feedback. The "ScrollUp" and "ScrollDown" functions adjust "scroll_pos" by "g_adjustedLineHeight", clamping within bounds, and call "UpdateBodyDisplay", "UpdateSliderPosition", and "UpdateButtonColors" if the scrollbar is visible, ensuring seamless scrolling. We can now call these functions inside the display update function to add the scrollbar. Here is the approach we use to achieve that.

```
int num_visible_lines = g_visible_height / g_adjustedLineHeight; //--- Calculate visible lines
g_max_scroll = MathMax(0, (numLines - num_visible_lines) * g_adjustedLineHeight); //--- Calculate max scroll
bool prev_scroll_visible = scroll_visible;       //--- Store previous scrollbar state
scroll_visible = should_show_scrollbar;          //--- Update scrollbar visibility
if (scroll_visible != prev_scroll_visible) {     //--- Check scrollbar state change
   if (scroll_visible) {                         //--- Show scrollbar
      CreateScrollbar();                         //--- Create scrollbar
   } else {                                      //--- Hide scrollbar
      DeleteScrollbar();                         //--- Delete scrollbar
   }
}
scroll_pos = MathMax(0, MathMin(scroll_pos, g_max_scroll)); //--- Clamp scroll position
if (scroll_visible) {                            //--- Update scrollbar
   slider_height = CalculateSliderHeight();      //--- Calculate slider height
   ObjectSetInteger(0, SCROLL_SLIDER, OBJPROP_YSIZE, slider_height); //--- Set slider height
   UpdateSliderPosition();                       //--- Update slider position
   UpdateButtonColors();                         //--- Update button colors
}

```

Inside the "UpdateBodyDisplay" function, we calculate the number of visible lines by dividing "g_visible_height" by "g_adjustedLineHeight" and determine the maximum scroll distance ("g_max_scroll") as the excess text height beyond visible lines, using 
[MathMax](/en/docs/math/mathmax)
 to avoid negative values. We store the previous scrollbar visibility state in "prev_scroll_visible", update "scroll_visible" based on whether a scrollbar is needed, and if the state changes, call "CreateScrollbar" to draw the scrollbar or "DeleteScrollbar" to remove it. We clamp "scroll_pos" between 0 and "g_max_scroll" using "MathMax" and 
[MathMin](/en/docs/math/mathmin)
 to prevent overflow. If the scrollbar is visible, we update "slider_height" with "CalculateSliderHeight", set the slider’s height with 
[ObjectSetInteger](/en/docs/objects/objectsetinteger)
 for "SCROLL_SLIDER", and call "UpdateSliderPosition" and "UpdateButtonColors" to refresh the scrollbar’s appearance and position. When we compile, we get the following outcome.
![SCROLLBAR ENABLED](https://c.mql5.com/2/172/Screenshot_2025-09-25_203431.png)
From the image, we can see that the dashboard elements are fully created. We now need to make sure that we discard the dashboard when we log out or deinitialize the program.

```
//+------------------------------------------------------------------+
//| Delete the dashboard                                             |
//+------------------------------------------------------------------+
void DeleteDashboard() {
   string objects[] = {                             //--- Define dashboard objects
      SETUP_MAIN, SETUP_HEADER_BG, SETUP_HEADER_IMAGE, SETUP_HEADER_TITLE, SETUP_HEADER_SUBTITLE, SETUP_HEADER_CANCEL,
      SETUP_BODY_BG, SETUP_FOOTER_BG, SETUP_CHECKBOX_BG, SETUP_CHECKBOX_LABEL, SETUP_CHECKBOX_TEXT,
      SETUP_OK_BUTTON, SETUP_CANCEL_BUTTON, SCROLL_LEADER, SCROLL_UP_REC, SCROLL_UP_LABEL,
      SCROLL_DOWN_REC, SCROLL_DOWN_LABEL, SCROLL_SLIDER
   };
   for (int i = 0; i < ArraySize(objects); i++) {   //--- Iterate through objects
      ObjectDelete(0, objects[i]);                  //--- Delete object
   }
   int total = ObjectsTotal(0);                     //--- Get total objects
   for (int j = total - 1; j >= 0; j--) {           //--- Iterate through remaining objects
      string name = ObjectName(0, j);               //--- Get object name
      if (StringFind(name, "Setup_ResponseLine_") == 0) { //--- Check for text lines
         ObjectDelete(0, name);                     //--- Delete text line
      }
   }
   ChartRedraw();                                   //--- Redraw chart
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
   DeleteDashboard();                                //--- Remove dashboard objects
   if (StringLen(g_scaled_image_resource) > 0) {     //--- Check if scaled image exists
      ResourceFree(g_scaled_image_resource);         //--- Free scaled image resource
   }
}

```

Here, we implement cleanup functionality for the Wizard to ensure proper resource management. In the "DeleteDashboard" function, we define an array of dashboard object names, including main container, header, body, footer, buttons, checkbox, and scrollbar components, and iterate through them using 
[ObjectDelete](/en/docs/objects/objectdelete)
 to remove each from the chart. We then loop through all remaining chart objects with 
[ObjectsTotal](/en/docs/objects/objectstotal)
 and 
[ObjectName](/en/docs/objects/objectname)
, deleting any text line objects starting with "Setup_ResponseLine_" using "ObjectDelete", and redraw the chart with 
[ChartRedraw](/en/docs/chart_operations/ChartRedraw)
 for a clean display. In the "OnDeinit" function, we call "DeleteDashboard" to remove all dashboard elements and check if a scaled image resource exists ("
[StringLen(g_scaled_image_resource)](/en/docs/strings/stringlen)
 > 0"), freeing it with 
[ResourceFree](/en/docs/common/resourcefree)
 to release memory. We can now move on to breathing life into the dashboard. We want it so that when we click on the buttons, they do their designated calls, and hover effects to show the state of the cursor. We will need a function to do that for simplicity.

```
//+------------------------------------------------------------------+
//| Update hover effects                                             |
//+------------------------------------------------------------------+
void UpdateHoverEffects(int mouseX, int mouseY) {
   int ok_x = (int)ObjectGetInteger(0, SETUP_OK_BUTTON, OBJPROP_XDISTANCE);    //--- Get OK button x
   int ok_y = (int)ObjectGetInteger(0, SETUP_OK_BUTTON, OBJPROP_YDISTANCE);    //--- Get OK button y
   int ok_width = (int)ObjectGetInteger(0, SETUP_OK_BUTTON, OBJPROP_XSIZE);    //--- Get OK button width
   int ok_height = (int)ObjectGetInteger(0, SETUP_OK_BUTTON, OBJPROP_YSIZE);   //--- Get OK button height
   bool is_ok_hovered = (mouseX >= ok_x && mouseX <= ok_x + ok_width && mouseY >= ok_y && mouseY <= ok_y + ok_height); //--- Check OK button hover
   if (is_ok_hovered != ok_button_hovered) {                                   //--- Check hover state change
      ok_button_hovered = is_ok_hovered;                                       //--- Update hover state
      color hoverBg = is_ok_hovered ? C'40,80,40' : C'60,60,60';               //--- Set hover background
      color hoverBorder = is_ok_hovered ? C'60,100,60' : C'80,80,80';          //--- Set hover border
      ObjectSetInteger(0, SETUP_OK_BUTTON, OBJPROP_BGCOLOR, hoverBg);          //--- Update background
      ObjectSetInteger(0, SETUP_OK_BUTTON, OBJPROP_BORDER_COLOR, hoverBorder); //--- Update border
      ChartRedraw();                                                           //--- Redraw chart
   }
   int cancel_x = (int)ObjectGetInteger(0, SETUP_CANCEL_BUTTON, OBJPROP_XDISTANCE);  //--- Get Cancel button x
   int cancel_y = (int)ObjectGetInteger(0, SETUP_CANCEL_BUTTON, OBJPROP_YDISTANCE);  //--- Get Cancel button y
   int cancel_width = (int)ObjectGetInteger(0, SETUP_CANCEL_BUTTON, OBJPROP_XSIZE);  //--- Get Cancel button width
   int cancel_height = (int)ObjectGetInteger(0, SETUP_CANCEL_BUTTON, OBJPROP_YSIZE); //--- Get Cancel button height
   bool is_cancel_hovered = (mouseX >= cancel_x && mouseX <= cancel_x + cancel_width && mouseY >= cancel_y && mouseY <= cancel_y + cancel_height); //--- Check Cancel button hover
   if (is_cancel_hovered != cancel_button_hovered) {                                 //--- Check hover state change
      cancel_button_hovered = is_cancel_hovered;                                     //--- Update hover state
      color hoverBg = is_cancel_hovered ? C'80,40,40' : C'60,60,60';                 //--- Set hover background
      color hoverBorder = is_cancel_hovered ? C'100,60,60' : C'80,80,80';            //--- Set hover border
      ObjectSetInteger(0, SETUP_CANCEL_BUTTON, OBJPROP_BGCOLOR, hoverBg);            //--- Update background
      ObjectSetInteger(0, SETUP_CANCEL_BUTTON, OBJPROP_BORDER_COLOR, hoverBorder);   //--- Update border
      ChartRedraw();                               //--- Redraw chart
   }
   int checkbox_x = (int)ObjectGetInteger(0, SETUP_CHECKBOX_BG, OBJPROP_XDISTANCE);  //--- Get checkbox x
   int checkbox_y = (int)ObjectGetInteger(0, SETUP_CHECKBOX_BG, OBJPROP_YDISTANCE);  //--- Get checkbox y
   int checkbox_width = (int)ObjectGetInteger(0, SETUP_CHECKBOX_BG, OBJPROP_XSIZE);  //--- Get checkbox width
   int checkbox_height = (int)ObjectGetInteger(0, SETUP_CHECKBOX_BG, OBJPROP_YSIZE); //--- Get checkbox height
   bool is_checkbox_hovered = (mouseX >= checkbox_x && mouseX <= checkbox_x + checkbox_width && mouseY >= checkbox_y && mouseY <= checkbox_y + checkbox_height); //--- Check checkbox hover
   if (is_checkbox_hovered != checkbox_hovered) {   //--- Check hover state change
      checkbox_hovered = is_checkbox_hovered;       //--- Update hover state
      if (checkbox_checked) {                       //--- Check checkbox state
         ObjectSetInteger(0, SETUP_CHECKBOX_BG, OBJPROP_BGCOLOR, is_checkbox_hovered ? C'0,150,0' : C'0,128,0'); //--- Update background
      } else {                                      //--- Unchecked state
         ObjectSetInteger(0, SETUP_CHECKBOX_BG, OBJPROP_BGCOLOR, is_checkbox_hovered ? C'70,70,70' : C'60,60,60'); //--- Update background
      }
      ChartRedraw();                                //--- Redraw chart
   }
   int header_cancel_x = (int)ObjectGetInteger(0, SETUP_HEADER_CANCEL, OBJPROP_XDISTANCE); //--- Get header cancel x
   int header_cancel_y = (int)ObjectGetInteger(0, SETUP_HEADER_CANCEL, OBJPROP_YDISTANCE); //--- Get header cancel y
   int header_cancel_width = 20;                    //--- Set header cancel width
   int header_cancel_height = 20;                   //--- Set header cancel height
   bool is_header_cancel_hovered = (mouseX >= header_cancel_x && mouseX <= header_cancel_x + header_cancel_width &&
                                    mouseY >= header_cancel_y && mouseY <= header_cancel_y + header_cancel_height); //--- Check header cancel hover
   if (is_header_cancel_hovered != header_cancel_hovered) { //--- Check hover state change
      header_cancel_hovered = is_header_cancel_hovered; //--- Update hover state
      ObjectSetInteger(0, SETUP_HEADER_CANCEL, OBJPROP_COLOR, is_header_cancel_hovered ? C'255,100,100' : C'150,150,150'); //--- Update color
      ChartRedraw();                                //--- Redraw chart
   }
   if (scroll_visible) {                            //--- Check scrollbar visible
      int scroll_up_x = (int)ObjectGetInteger(0, SCROLL_UP_REC, OBJPROP_XDISTANCE);  //--- Get scroll up x
      int scroll_up_y = (int)ObjectGetInteger(0, SCROLL_UP_REC, OBJPROP_YDISTANCE);  //--- Get scroll up y
      int scroll_up_width = (int)ObjectGetInteger(0, SCROLL_UP_REC, OBJPROP_XSIZE);  //--- Get scroll up width
      int scroll_up_height = (int)ObjectGetInteger(0, SCROLL_UP_REC, OBJPROP_YSIZE); //--- Get scroll up height
      bool is_scroll_up_hovered = (mouseX >= scroll_up_x && mouseX <= scroll_up_x + scroll_up_width &&
                                   mouseY >= scroll_up_y && mouseY <= scroll_up_y + scroll_up_height); //--- Check scroll up hover
      if (is_scroll_up_hovered != scroll_up_hovered) {                               //--- Check hover state change
         scroll_up_hovered = is_scroll_up_hovered;                                   //--- Update hover state
         ObjectSetInteger(0, SCROLL_UP_REC, OBJPROP_BGCOLOR, is_scroll_up_hovered ? C'70,70,70' : C'60,60,60'); //--- Update background
         ObjectSetInteger(0, SCROLL_UP_LABEL, OBJPROP_COLOR, (scroll_pos == 0) ? C'80,80,80' : (is_scroll_up_hovered ? C'100,100,100' : C'150,150,150')); //--- Update label color
         ChartRedraw();                                                              //--- Redraw chart
      }
      int scroll_down_x = (int)ObjectGetInteger(0, SCROLL_DOWN_REC, OBJPROP_XDISTANCE);  //--- Get scroll down x
      int scroll_down_y = (int)ObjectGetInteger(0, SCROLL_DOWN_REC, OBJPROP_YDISTANCE);  //--- Get scroll down y
      int scroll_down_width = (int)ObjectGetInteger(0, SCROLL_DOWN_REC, OBJPROP_XSIZE);  //--- Get scroll down width
      int scroll_down_height = (int)ObjectGetInteger(0, SCROLL_DOWN_REC, OBJPROP_YSIZE); //--- Get scroll down height
      bool is_scroll_down_hovered = (mouseX >= scroll_down_x && mouseX <= scroll_down_x + scroll_down_width &&
                                     mouseY >= scroll_down_y && mouseY <= scroll_down_y + scroll_down_height); //--- Check scroll down hover
      if (is_scroll_down_hovered != scroll_down_hovered) {                               //--- Check hover state change
         scroll_down_hovered = is_scroll_down_hovered;                                   //--- Update hover state
         ObjectSetInteger(0, SCROLL_DOWN_REC, OBJPROP_BGCOLOR, is_scroll_down_hovered ? C'70,70,70' : C'60,60,60'); //--- Update background
         ObjectSetInteger(0, SCROLL_DOWN_LABEL, OBJPROP_COLOR, (scroll_pos >= g_max_scroll) ? C'80,80,80' : (is_scroll_down_hovered ? C'100,100,100' : C'150,150,150')); //--- Update label color
         ChartRedraw();                                                                  //--- Redraw chart
      }
      int scroll_slider_x = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_XDISTANCE);  //--- Get scroll slider x
      int scroll_slider_y = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_YDISTANCE);  //--- Get scroll slider y
      int scroll_slider_width = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_XSIZE);  //--- Get scroll slider width
      int scroll_slider_height = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_YSIZE); //--- Get scroll slider height
      bool is_scroll_slider_hovered = (mouseX >= scroll_slider_x && mouseX <= scroll_slider_x + scroll_slider_width &&
                                       mouseY >= scroll_slider_y && mouseY <= scroll_slider_y + scroll_slider_height); //--- Check scroll slider hover
      if (is_scroll_slider_hovered != scroll_slider_hovered) {                           //--- Check hover state change
         scroll_slider_hovered = is_scroll_slider_hovered;                               //--- Update hover state
         ObjectSetInteger(0, SCROLL_SLIDER, OBJPROP_BGCOLOR, is_scroll_slider_hovered ? C'100,100,100' : C'80,80,80'); //--- Update background
         ChartRedraw();                                                                  //--- Redraw chart
      }
   }
}

```

Here, we implement hover effects for the interactive elements that we have created to enhance user feedback. We create the "UpdateHoverEffects" function and in it we check mouse coordinates ("mouseX", "mouseY") against the positions and sizes of the OK button ("SETUP_OK_BUTTON"), Cancel button ("SETUP_CANCEL_BUTTON"), checkbox ("SETUP_CHECKBOX_BG"), header cancel button ("SETUP_HEADER_CANCEL"), and scrollbar components ("SCROLL_UP_REC", "SCROLL_DOWN_REC", "SCROLL_SLIDER") using 
[ObjectGetInteger](/en/docs/objects/ObjectGetInteger)
 for their dimensions.
For each element, we detect hover by verifying if the mouse is within its bounds, updating respective hover states ("ok_button_hovered", "cancel_button_hovered", etc.) if changed, and adjust colors with 
[ObjectSetInteger](/en/docs/objects/objectsetinteger)
: OK button uses green shades (C'40,80,40'), Cancel button uses red shades (C'80,40,40'), checkbox uses green when checked (C'0,150,0') or gray (C'70,70,70'), header cancel shifts to bright red (C'255,100,100'), and scrollbar buttons/slider use varying grays (C'70,70,70' or C'100,100,100') based on hover and scroll position ("scroll_pos"). All these colors can be modified as per your liking. We just used arbitrary values again to gain an edge over visual feedback. We redraw the chart with 
[ChartRedraw](/en/docs/chart_operations/ChartRedraw)
 after each update. We now need to just implement this in the 
[OnChartEvent](/en/docs/event_handlers/onchartevent)
 event handler, which takes care of all chart events, but in our case, we are interested in the mouse movement and click events.

```
//+------------------------------------------------------------------+
//| Chart event handler                                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam) {
   int mouseX = (int)lparam;                        //--- Get mouse x coordinate
   int mouseY = (int)dparam;                        //--- Get mouse y coordinate
   int body_inner_y = g_mainY + g_headerHeight + g_spacing; //--- Calculate body y position
   int textAreaEventY = body_inner_y;               //--- Set text area y position
   int textAreaEventH = g_displayHeight;            //--- Set text area height
   int bodyX = g_mainX + g_padding + g_textPadding; //--- Calculate body x position
   int bodyW = g_mainWidth - 2 * g_padding - 2 * g_textPadding - (scroll_visible ? 16 : 0); //--- Calculate body width
   if (id == CHARTEVENT_OBJECT_CLICK) {             //--- Handle object click events
      if (sparam == SETUP_HEADER_CANCEL || sparam == SETUP_CANCEL_BUTTON) { //--- Check cancel button click
         GlobalVariableSet(GV_SETUP, 0.0);          //--- Set global variable to false
         DeleteDashboard();                         //--- Remove dashboard from chart
      } else if (sparam == SETUP_OK_BUTTON) {       //--- Check OK button click
         double new_val = checkbox_checked ? 1.0 : 0.0; //--- Set global variable based on checkbox
         GlobalVariableSet(GV_SETUP, new_val);      //--- Update global variable
         DeleteDashboard();                         //--- Remove dashboard from chart
      } else if (sparam == SETUP_CHECKBOX_BG || sparam == SETUP_CHECKBOX_TEXT || sparam == SETUP_CHECKBOX_LABEL) { //--- Check checkbox click
         checkbox_checked = !checkbox_checked;      //--- Toggle checkbox state
         string check_text = checkbox_checked ? CharToString(252) : " ";         //--- Set checkbox symbol
         ObjectSetString(0, SETUP_CHECKBOX_LABEL, OBJPROP_TEXT, check_text);     //--- Update checkbox label text
         color text_color = checkbox_checked ? C'173,216,230' : clrWhite;        //--- Set text color based on state
         ObjectSetInteger(0, SETUP_CHECKBOX_TEXT, OBJPROP_COLOR, text_color);    //--- Update checkbox text color
         if (checkbox_checked) {                    //--- Check if checkbox is selected
            ObjectSetInteger(0, SETUP_CHECKBOX_BG, OBJPROP_BGCOLOR, C'0,128,0'); //--- Set checked background color
            ObjectSetInteger(0, SETUP_CHECKBOX_LABEL, OBJPROP_COLOR, clrWhite);  //--- Set checked label color
         } else {                                   //--- Handle unchecked state
            ObjectSetInteger(0, SETUP_CHECKBOX_BG, OBJPROP_BGCOLOR, C'60,60,60'); //--- Set unchecked background color
            ObjectSetInteger(0, SETUP_CHECKBOX_LABEL, OBJPROP_COLOR, clrWhite);  //--- Set unchecked label color
         }
         ChartRedraw();                            //--- Redraw chart to reflect changes
      } else if (sparam == SCROLL_UP_REC || sparam == SCROLL_UP_LABEL) {         //--- Check scroll up click
         ScrollUp();                               //--- Execute scroll up action
      } else if (sparam == SCROLL_DOWN_REC || sparam == SCROLL_DOWN_LABEL) {     //--- Check scroll down click
         ScrollDown();                             //--- Execute scroll down action
      }
   } else if (id == CHARTEVENT_MOUSE_MOVE) {       //--- Handle mouse move events
      int MouseState = (int)sparam;                //--- Get mouse state
      bool is_in = (mouseX >= bodyX && mouseX <= bodyX + bodyW && mouseY >= textAreaEventY && mouseY <= textAreaEventY + textAreaEventH); //--- Check if mouse is in body
      mouse_in_body = is_in;                       //--- Update mouse in body status
      UpdateHoverEffects(mouseX, mouseY);          //--- Update hover effects for elements
      static int prevMouseState = 0;               //--- Store previous mouse state
      if (prevMouseState == 0 && MouseState == 1 && scroll_visible) {                //--- Check for slider drag start
         int xd_slider = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_XDISTANCE); //--- Get slider x position
         int yd_slider = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_YDISTANCE); //--- Get slider y position
         int xs_slider = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_XSIZE);     //--- Get slider width
         int ys_slider = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_YSIZE);     //--- Get slider height
         if (mouseX >= xd_slider && mouseX <= xd_slider + xs_slider &&
             mouseY >= yd_slider && mouseY <= yd_slider + ys_slider) { //--- Check if mouse is over slider
            movingStateSlider = true;              //--- Set slider drag state
            mlbDownX_Slider = mouseX;              //--- Store mouse x position
            mlbDownY_Slider = mouseY;              //--- Store mouse y position
            mlbDown_YD_Slider = yd_slider;         //--- Store slider y position
            ObjectSetInteger(0, SCROLL_SLIDER, OBJPROP_BGCOLOR, C'100,100,100'); //--- Set drag color
            ChartSetInteger(0, CHART_MOUSE_SCROLL, false); //--- Disable chart scrolling
         }
      }
      if (movingStateSlider) {                     //--- Handle slider dragging
         int delta_y = mouseY - mlbDownY_Slider;   //--- Calculate y displacement
         int new_y = mlbDown_YD_Slider + delta_y;  //--- Calculate new slider y position
         int textAreaY_local = body_inner_y;       //--- Set text area y position
         int textAreaHeight_local = g_displayHeight;   //--- Set text area height
         int scroll_area_y_min = textAreaY_local + 16; //--- Set minimum slider y
         int scroll_area_y_max = textAreaY_local + textAreaHeight_local - 16 - slider_height; //--- Set maximum slider y
         new_y = MathMax(scroll_area_y_min, MathMin(new_y, scroll_area_y_max));               //--- Clamp new y position
         ObjectSetInteger(0, SCROLL_SLIDER, OBJPROP_YDISTANCE, new_y);                        //--- Update slider y position
         int max_scroll = g_max_scroll;            //--- Get maximum scroll
         double scroll_ratio = (double)(new_y - scroll_area_y_min) / (scroll_area_y_max - scroll_area_y_min); //--- Calculate scroll ratio
         int new_scroll_pos = (int)MathRound(scroll_ratio * max_scroll);                      //--- Calculate new scroll position
         if (new_scroll_pos != scroll_pos) {       //--- Check if scroll position changed
            scroll_pos = new_scroll_pos;           //--- Update scroll position
            UpdateBodyDisplay();                   //--- Update body text display
         }
         ChartRedraw();                            //--- Redraw chart
      }
      if (MouseState == 0) {                       //--- Handle mouse release
         if (movingStateSlider) {                  //--- Check if slider was being dragged
            movingStateSlider = false;             //--- Reset drag state
            int max_scroll = g_max_scroll;         //--- Get maximum scroll
            int textAreaY_local = body_inner_y;    //--- Set text area y position
            int textAreaHeight_local = g_displayHeight; //--- Set text area height
            int scroll_area_y_min_local = textAreaY_local + 16; //--- Set minimum slider y
            int scroll_area_y_max_local = textAreaY_local + textAreaHeight_local - 16 - slider_height; //--- Set maximum slider y
            int current_slider_y = (int)ObjectGetInteger(0, SCROLL_SLIDER, OBJPROP_YDISTANCE); //--- Get current slider y
            double scroll_ratio = (double)(current_slider_y - scroll_area_y_min_local) / (scroll_area_y_max_local - scroll_area_y_min_local); //--- Calculate scroll ratio
            int temp_scroll = (int)MathRound(scroll_ratio * max_scroll); //--- Calculate temporary scroll
            if (g_adjustedLineHeight > 0) {        //--- Check if line height valid
               int snapped_line = (int)MathRound((double)temp_scroll / g_adjustedLineHeight); //--- Calculate snapped line
               scroll_pos = MathMax(0, MathMin(snapped_line * g_adjustedLineHeight, max_scroll)); //--- Snap to nearest line
            } else {                               //--- No valid line height
               scroll_pos = temp_scroll;           //--- Use temporary scroll
            }
            UpdateBodyDisplay();                   //--- Update body text display
            UpdateSliderPosition();                //--- Update slider position
            ObjectSetInteger(0, SCROLL_SLIDER, OBJPROP_BGCOLOR, scroll_slider_hovered ? C'100,100,100' : C'80,80,80'); //--- Reset slider color
            ChartSetInteger(0, CHART_MOUSE_SCROLL, true); //--- Re-enable chart scrolling
         }
      }
      prevMouseState = MouseState;                 //--- Update previous mouse state
   } else if (id == CHARTEVENT_MOUSE_WHEEL) {      //--- Handle mouse wheel events
      int wheel_delta = (int)sparam;               //--- Get wheel delta
      bool in_body = (mouseX >= bodyX && mouseX <= bodyX + bodyW && mouseY >= textAreaEventY && mouseY <= textAreaEventY + textAreaEventH); //--- Check if mouse in body
      if (in_body && g_total_height > g_visible_height && g_adjustedLineHeight > 0) { //--- Check scroll conditions
         int direction = (wheel_delta > 0) ? -1 : 1; //--- Determine scroll direction
         int notches = MathAbs(wheel_delta) / 120; //--- Calculate scroll notches
         int scroll_amount = g_adjustedLineHeight * direction * notches; //--- Calculate scroll amount
         scroll_pos += scroll_amount;              //--- Update scroll position
         int max_scroll = g_max_scroll;            //--- Get maximum scroll
         scroll_pos = MathMax(0, MathMin(scroll_pos, max_scroll)); //--- Clamp scroll position
         UpdateBodyDisplay();                      //--- Update body text display
         if (scroll_visible) {                     //--- Check if scrollbar visible
            UpdateSliderPosition();                //--- Update slider position
            UpdateButtonColors();                  //--- Update button colors
         }
         ChartRedraw();                            //--- Redraw chart
      }
   }
}
```

Finally, in the 
[OnChartEvent](/en/docs/event_handlers/onchartevent)
 function, we handle click events (
[CHARTEVENT_OBJECT_CLICK](/en/docs/constants/chartconstants/enum_chartevents)
) by checking the clicked object ("sparam"): if it’s the header cancel ("SETUP_HEADER_CANCEL") or Cancel button ("SETUP_CANCEL_BUTTON"), we set the global variable "GV_SETUP" to 0.0 with 
[GlobalVariableSet](/en/docs/globals/globalvariableset)
 and remove the dashboard with "DeleteDashboard"; if it’s the OK button ("SETUP_OK_BUTTON"), we set "GV_SETUP" to 1.0 if the checkbox is checked ("checkbox_checked") or 0.0 otherwise, then remove the dashboard; if it’s the checkbox components ("SETUP_CHECKBOX_BG", "SETUP_CHECKBOX_TEXT", "SETUP_CHECKBOX_LABEL"), we toggle "checkbox_checked", update the checkbox label to a checkmark (Unicode 252) or space with 
[ObjectSetString](/en/docs/objects/objectsetstring)
, set the text color to light blue (C'173,216,230') or white with 
[ObjectSetInteger](/en/docs/objects/objectsetinteger)
, and adjust the checkbox background to green (C'0,128,0') or gray (C'60,60,60'). MQL5 provides a detailed list of the Wingdings font characters, and that is what we used. You can use any of your choice or a different approach. Here is a visualization of the possible 
[MQL5 Wingdings](/en/docs/constants/objectconstants/wingdings)
 characters you can use.
![MQL5 WINGDINGS](https://c.mql5.com/2/172/C_MQL5_WINGDINGS.png)
For scroll up ("SCROLL_UP_REC", "SCROLL_UP_LABEL") or down ("SCROLL_DOWN_REC", "SCROLL_DOWN_LABEL") clicks, we call "ScrollUp" or "ScrollDown". For mouse move events (
[CHARTEVENT_MOUSE_MOVE](/en/docs/constants/chartconstants/enum_chartevents)
), we calculate the body area, update "mouse_in_body", and call "UpdateHoverEffects" with "mouseX" and "mouseY"; we detect slider drag start ("MouseState" 1) by checking if the mouse is over "SCROLL_SLIDER", setting "movingStateSlider" and storing mouse positions, and during drag, adjust the slider’s y-position with 
[ObjectSetInteger](/en/docs/objects/objectsetinteger)
, update "scroll_pos" based on the scroll ratio, and refresh the display with "UpdateBodyDisplay". On mouse release ("MouseState" 0), we snap "scroll_pos" to the nearest line, reset the slider state, and re-enable chart scrolling with the 
[ChartSetInteger](/en/docs/chart_operations/chartsetinteger)
 function. For mouse wheel events (
[CHARTEVENT_MOUSE_WHEEL](/en/docs/constants/chartconstants/enum_chartevents)
), we adjust "scroll_pos" based on wheel direction and notches, clamp it within "g_max_scroll", and update the display and scrollbar. When we compile, we get the following outcome.
![FINAL WIZARD WITH FULL FUNCTIONALITY](https://c.mql5.com/2/172/Screenshot_2025-09-25_205754.png)
From the image, we can see that the dashboard is now fully functional and interactive. When we click on the okay button, we should get a global variable set. To access the global variable, you need to click on "Tools" then "Global Variables" or simply press F3 on your keyboard. Here is a complete visualization.
![GLOBAL VARIABLE SETUP](https://c.mql5.com/2/172/Screenshot_2025-09-25_210430.png)
From the images, we can see that we have correctly set up the wizard with all the objectives achieved. What now remains is testing the workability of the project, and that is handled in the preceding section.

### Testing the Setup Wizard

We did the testing, and below is the compiled visualization in a single 
[Graphics Interchange Format](https://en.wikipedia.org/wiki/GIF)
 (GIF) bitmap image format.
![WIZARD BACKTEST GIF](https://c.mql5.com/2/172/FIRST_RUN_WIZARD_GIF.gif)

### Conclusion

In conclusion, we’ve developed a first-run user setup Wizard for Expert Advisors in MQL5, creating an interactive dashboard with a scrollable guide, dynamic text formatting, and user controls like buttons and a checkbox to streamline program configuration in 
[MetaTrader 5](https://www.metatrader5.com/)
. The tool enhances trader onboarding by providing clear instructions and a mechanism to skip future displays, ensuring efficient setup and adaptability across screen settings. It equips you to simplify program initialization by providing custom one-time user insights, ready for further customization in your trading toolkit. Happy trading!

Attached files
 |
  

[Download ZIP](/en/articles/download/19714.zip)

[EA_First_Initialization_Setup.mq5](/en/articles/download/19714/EA_First_Initialization_Setup.mq5)

(153.52 KB)

Warning:
 All rights to these materials are reserved by MetaQuotes Ltd. Copying or reprinting of these materials in whole or in part is prohibited.

This article was written by a user of the site and reflects their personal views. MetaQuotes Ltd is not responsible for the accuracy of the information presented, nor for any consequences resulting from the use of the solutions, strategies or recommendations described.

#### Other articles by this author

[Automating Trading Strategies in MQL5 (Part 44): Change of Character (CHoCH) Detection with Swing High/Low Breaks](/en/articles/20355)

[Automating Trading Strategies in MQL5 (Part 43): Adaptive Linear Regression Channel Strategy](/en/articles/20347)

[Automating Trading Strategies in MQL5 (Part 42): Session-Based Opening Range Breakout (ORB) System](/en/articles/20339)

[Automating Trading Strategies in MQL5 (Part 41): Candle Range Theory (CRT) – Accumulation, Manipulation, Distribution (AMD)](/en/articles/20323)

[Building AI-Powered Trading Systems in MQL5 (Part 6): Introducing Chat Deletion and Search Functionality](/en/articles/20254)

[Automating Trading Strategies in MQL5 (Part 40): Fibonacci Retracement Trading with Custom Levels](/en/articles/20221)

[Building AI-Powered Trading Systems in MQL5 (Part 5): Adding a Collapsible Sidebar with Chat Popups](/en/articles/20249)

[Go to discussion](/en/forum/496479)

![From Novice to Expert: Backend Operations Monitor using MQL5](https://c.mql5.com/2/172/19649-from-novice-to-expert-backend-logo.png)

[From Novice to Expert: Backend Operations Monitor using MQL5](/en/articles/19649)

Using a ready-made solution in trading without concerning yourself with the internal workings of the system may sound comforting, but this is not always the case for developers. Eventually, an upgrade, misperformance, or unexpected error will arise, and it becomes essential to trace exactly where the issue originates to diagnose and resolve it quickly. Today’s discussion focuses on uncovering what normally happens behind the scenes of a trading Expert Advisor, and on developing a custom dedicated class for displaying and logging backend processes using MQL5. This gives both developers and traders the ability to quickly locate errors, monitor behavior, and access diagnostic information specific to each EA.

![Price Action Analysis Toolkit Development (Part 42): Interactive Chart Testing with Button Logic and Statistical Levels](https://c.mql5.com/2/172/19697-price-action-analysis-toolkit-logo.png)

[Price Action Analysis Toolkit Development (Part 42): Interactive Chart Testing with Button Logic and Statistical Levels](/en/articles/19697)

In a world where speed and precision matter, analysis tools need to be as smart as the markets we trade. This article presents an EA built on button logic—an interactive system that instantly transforms raw price data into meaningful statistical levels. With a single click, it calculates and displays mean, deviation, percentiles, and more, turning advanced analytics into clear on-chart signals. It highlights the zones where price is most likely to bounce, retrace, or break, making analysis both faster and more practical.

![Automating Trading Strategies in MQL5 (Part 35): Creating a Breaker Block Trading System](https://c.mql5.com/2/173/19638-automating-trading-strategies-logo.png)

[Automating Trading Strategies in MQL5 (Part 35): Creating a Breaker Block Trading System](/en/articles/19638)

In this article, we create a Breaker Block Trading System in MQL5 that identifies consolidation ranges, detects breakouts, and validates breaker blocks with swing points to trade retests with defined risk parameters. The system visualizes order and breaker blocks with dynamic labels and arrows, supporting automated trading and trailing stops.

![Cyclic Parthenogenesis Algorithm (CPA)](https://c.mql5.com/2/113/Cyclic_Parthenogenesis_Algorithm____LOGO.png)

[Cyclic Parthenogenesis Algorithm (CPA)](/en/articles/16877)

The article considers a new population optimization algorithm - Cyclic Parthenogenesis Algorithm (CPA), inspired by the unique reproductive strategy of aphids. The algorithm combines two reproduction mechanisms — parthenogenesis and sexual reproduction — and also utilizes the colonial structure of the population with the possibility of migration between colonies. The key features of the algorithm are adaptive switching between different reproductive strategies and a system of information exchange between colonies through the flight mechanism.

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

