//+------------------------------------------------------------------+
//|                                      Project 19 Telegram API.mq5 |
//|                                             Abioye Israel Pelumi |
//|                             https://linktr.ee/abioyeisraelpelumi |
//+------------------------------------------------------------------+
#property copyright "Abioye Israel Pelumi"
#property link      "https://linktr.ee/abioyeisraelpelumi"
#property version   "1.00"

const string method = "POST";
const string telegram_api_url = "https://api.telegram.org";
const string bot_chatID = "6972412345";
const string group_chatID = "-1003277012345";
const string headers = "";
const int time_out = 5000;

const string bot_token  = "8345012345:AAHdAPtMQR6VHEQeHk1y_H9IuL3zc5abcde";
const string MessageID = "35";
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---

  char data[];
   char res[];
   string resHeaders = "";

 string body = "chat_id=" + group_chatID + "&text=Hello from MT5!";
   StringToCharArray(body, data, 0);

   string url = telegram_api_url + "/bot" + bot_token + "/sendMessage";

   WebRequest(method,url,headers,time_out,data,res,resHeaders);
    Print(CharArrayToString(res));
   
   //DELETE
   /*
   
    const string url = telegram_api_url + "/bot" + bot_token + "/deleteMessage";

   string body = "chat_id=" + group_chatID +"&message_id=" + MessageID;
   StringToCharArray(body, data, 0);

   WebRequest(method,url,headers,time_out,data,res,resHeaders);
   
   */
   
   
   //EDIT
    /*
   
   string new_message = "Updated message text from MT5!";
   string url = telegram_api_url + "/bot" + bot_token +
                "/editMessageText";

   string body = "chat_id=" + group_chatID +"&message_id=" + MessageID + "&text=" + new_message;
   StringToCharArray(body, data, 0);

   WebRequest(method,url,headers,time_out,data,res,resHeaders);
   
   */
   
   
   
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
