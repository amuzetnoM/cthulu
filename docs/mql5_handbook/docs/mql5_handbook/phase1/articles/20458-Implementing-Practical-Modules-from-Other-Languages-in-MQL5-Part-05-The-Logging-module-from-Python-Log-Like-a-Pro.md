---
title: "Implementing Practical Modules from Other Languages in MQL5 (Part 05): The Logging module from Python, Log Like a Pro"
original_url: "https://www.mql5.com/en/articles/20458"
phase: "phase1"
article_id: "20458"
date: "4 December 2025, 10:29"
---

# Implementing Practical Modules from Other Languages in MQL5 (Part 05): The Logging module from Python, Log Like a Pro



[](#pocket)

[](/en/articles/20458?print=)

![preview](assets/20458/76b9aa82dd6ca3ddcd3d77e53e1a934e.jpeg)

![Implementing Practical Modules from Other Languages in MQL5 (Part 05): The Logging module from Python, Log Like a Pro](https://c.mql5.com/2/184/20458-implementing-practical-modules-from-other-languages-in-mql5_600x314.jpg)

# Implementing Practical Modules from Other Languages in MQL5 (Part 05): The Logging module from Python, Log Like a Pro

[MetaTrader 5](/en/articles/mt5)

          —
          
[Trading](/en/articles/mt5/trading)

        | 
4 December 2025, 10:29

![](https://c.mql5.com/i/icons.svg#views-usage)

          465
        

[![](https://c.mql5.com/i/icons.svg#comments-usage)0](/en/forum/501166)

![Omega J Msigwa](https://c.mql5.com/avatar/2022/6/62B4B2F2-C377.png)

[Omega J Msigwa](/en/users/omegajoctan)
 

Contents
 
 
[Introduction](/en/articles/20458#intro)
 
[Problems with the MetaTrader 5 Logging Mechanism](/en/articles/20458#problems-w-mt5-logging)
 
[The Logging Facility for Python in MQL5](/en/articles/20458#python-logging-facility)
 
[Basic Configurations for a Logger](/en/articles/20458#basic-configs-logger)
 
[Logging Some Information](/en/articles/20458#logging-information)
 
[Specific Function for each Log Message](/en/articles/20458#specific-func-4-message)
 
[Optimizing the Logging Process](/en/articles/20458#optimize-logging)
 
[Making Logging Much Easier — The Python Way](/en/articles/20458#make-logging-easier)
 
[Conclusion](/en/articles/20458#conclusion)
 
 
 
 

### Introduction

 
Logging is very crucial in any modern device, program, or software. It is simply the process of keeping records of everything that has happened in the lifetime of a particular operation.
 
 
Computers keep records of software usage, connections, and system events.
 
Our browsers keep the history of the sites we visit and how we interact with them.
 
 
 
Keeping these records is essential for many important reasons, including troubleshooting, debugging, auditing, monitoring performance, and understanding the behavior of our systems over time.
 
 
![image source: pexels.com](https://c.mql5.com/2/183/article_image.png)
 
In the algorithmic trading space, logging is very important as well as it helps us:
 
 
Monitor trading decisions, we can see what happened and when Expert Advisors opened, modified, or closed a position — and why, etc.
 
Validate and ensure our logic is firing exactly as intended during all market conditions.
 
Track down complex logic to see where a calculation went wrong or why a trade was rejected, and more.
 
 
 
MetaTrader 5 has a built-in logging mechanism, which is quite decent and works just fine, but it has several limitations.
 
 

### Problems with the MetaTrader 5 Logging Mechanism

 
All logs are mixed together with system-generated logs
 
The experts tab doesn't display information about a specific program; all logs and printed in the same console and stored within the same log file for a particular day.
 
This makes it difficult to monitor logs for a specific program or functionality.
 
They are hard to format
 
Since there is no specified or particular way to print the information in MQL5, all logs can be different. This inconsistency makes it challenging to spot errors and identify flaws.
 
You have little to no-control over verbosity
 
Unless you explicitly put a couple of if statements before every 
"Print function call"
, there is no way to control the information that comes out of the experts tab.
 
 
These are just a few of the limitations of the built-in MetaTrader 5 logging. In Python, there is a built-in module named logging, which addresses some of the limitations outlined above. In this article, we will see what this module is about and implement a very similar library in the MQL5 programming language.
 
 
 

### The Logging Facility for Python in MQL5

 
According to the 
[Python documentation](/go?link=https://docs.python.org/3/library/logging.html)
:
 
 
The module named logging defines functions and classes that implement a flexible event logging system for applications and libraries.
 
 
This module focuses on flexibility while maintaining the same core principles of logging, enabling users to have a simple and universal way to keep records of the events in their Python applications.
 
Example.
 

```
import logging
logger = logging.getLogger(__name__)

def do_something():
    logger.info('Doing something important')

def main():
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    
    logger.info('Started')
    do_something()
    logger.info('Finished')

if __name__ == '__main__':
    main()
```

 
Outputs (myapp.log).
 

```
INFO:__main__:Finished
INFO:__main__:Started
INFO:__main__:Doing something important
INFO:__main__:Finished
```

 
In just a few lines of code, we were able to specify the file we'll use to store the logs and log some information into that file.
 
But, the similar MQL5 class, we don't need the function named
 getLogger
 because all it does is retrieve (or create) a logger with a specific name.
 
This can be handled in our class constructor, with an option to assign a name. A class constructor can return the CLogger object.
 

```
class CLogger
  {
private:

   string            m_name;
   LogLevels         m_loglevel;
   string            m_filename;
   int               m_filehandle; // Handle of log file
   bool              m_iscommon;
   string            m_logs_format;
   bool              m_console_on;

   int               m_fileflags;
   bool              is_configured;

public:

   void              CLogger(const string name);
   void              CLogger(void); // Constructor
   void             ~CLogger(void); // Destructor
  };
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
CLogger::CLogger(void):
   m_filename("logs.log"),
   is_configured(false),
   m_filehandle(-1),
   m_console_on(true),
   m_iscommon(false),
   m_logs_format(DEFAULT_MSG_FORMAT),
   m_loglevel(LOG_LEVEL_INFO)
  {

  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
CLogger::CLogger(const string name):
   m_name(name)
  {
   CLogger();
  }
```

 
One of the most important functions in this class is a function named 
basicConfig
.
 
 

### Basic Configurations for a Logger

 
The ability to specify what to expect from your logs is crucial, and it can only be done inside this function. Below are several things (variables) we have to configure.
 
The file name (filename)
 
This is the name of the file you want to write all the logs inside.
 
 
The file name extension must either be 
.txt
 or 
.log
.
 
 

```
bool CLogger::basicConfig(LogLevels log_level = LOG_LEVEL_INFO,
                          string filename = "logs.log",
                          bool console_on = true,
                          string format = DEFAULT_MSG_FORMAT,
                          bool file_common = false)
  {
   m_filename = filename;
   m_logs_format = format;
   m_console_on = console_on;
   m_iscommon = file_common;
   m_loglevel = log_level;


//--- Before reading the file check if the extension is ok

   if(!checkFileExtenstion(filename))
     {
      is_configured = false;
      return false;
     }

```

 
File name extension checking.
 

```
bool CLogger::checkFileExtenstion(string filename)
  {
   if(StringFind(filename, ".txt") > 0 || StringFind(filename, ".log") > 0)
      return true;

   printf("Unsupported file extension, the logger expects a file [.txt, .log] file extensions (types)");

   return false;
  }
```

 
Again, logging is a process of storing information in a specified file. Let us open a specified text file.
 

```
bool CLogger::basicConfig(LogLevels log_level = LOG_LEVEL_INFO,
                          string filename = "logs.log",
                          bool console_on = true,
                          string format = DEFAULT_MSG_FORMAT,
                          bool file_common = false)
  {
   m_filename = filename;
   m_logs_format = format;
   m_console_on = console_on;
   m_iscommon = file_common;
   m_loglevel = log_level;


//--- Before reading the file check if the extension is ok

   if(!checkFileExtenstion(filename))
     {
      is_configured = false;
      return false;
     }

//--- Open the file for writting

   m_fileflags = FILE_READ | FILE_WRITE | FILE_SHARE_WRITE | FILE_TXT | FILE_ANSI;

   if(m_iscommon)
      m_fileflags |= FILE_COMMON;

   m_filehandle = FileOpen(filename, m_fileflags); // Open or create file

   if(m_filehandle == INVALID_HANDLE)
     {
      printf("func=%s line=%d, failed to open a '%s'. Error = %d", __FUNCTION__, __LINE__, filename, GetLastError());
      is_configured = false;
      return false;
     }

   FileSeek(m_filehandle, 0, SEEK_END); //Move to the end of the file

//--- Handle large files than accepted

   fileRotate(m_filehandle, m_filename, m_fileflags, m_iscommon);

   is_configured = true;
   return true;
  }
```

 
For efficiency and faster logging, we have to optimize the process of reading and writing to a log file. We must be strict on how big a log file can be 
(big text files are harder to read and write as they consume too much of the memory)
.
 

```
// Max file size in megabytes
#define MAX_FILE_SIZEMB 10
// The maximum number of files of FILE_SIZEMB to create before the system stop writting for good
#define MAX_LOG_FILES 1000
```

 
The default value is 10 Megabytes. As you might know, a text file larger than 10 MB is huge. Too big for a plain text file with a few bytes of information per line.
 
 
Every time a file exceeds this limit, a new log file will be created automatically with the same base name + _[existing log files with the same name++]. For example, if there is an existing log file called 
mylogs.log
 a new file with the name 
mylogs_1.log
 will be created.
 
Also, there is a limit on how many files for a particular basename can be created, the limit is 1000 files
 
(by default)
.
 
 
The function named 
fileRotate
 is up for this task.
 

```
void CLogger::fileRotate(int &handle, string &filename, int flags, bool is_common)
  {
   if (!isFileSizeLimitReached(handle))
      return;   // No rotation

//--- Close the current larger file

   FileClose(handle);
   
//---

   if(!checkFileExtenstion(filename))
      return;

//--- Get the base name of the file

   string extension = StringFind(filename, ".log") < 0 ? ".txt" : ".log";
   int ext_start = MathMax(StringFind(filename, ".log"), StringFind(filename, ".txt"));
   string base_name = StringSubstr(filename, 0, ext_start);

//--- Get the incremented file names

   string new_name = "";
   for(int i = 1; i <= MAX_LOG_FILES; i++)
     {
      new_name = base_name + "_" + string(i) + extension;

      if (!FileIsExist(new_name, is_common))
        {
         handle = FileOpen(new_name, flags);
         if(handle == INVALID_HANDLE)
           {
            printf("Failed to rotate into a new file");
            return;
           }
           
          break;
        }
      else //Check whether an existing file is full or not, if it's not log into that file until it's full
        {
         int temp_handle = FileOpen(new_name, flags);
         if(temp_handle == INVALID_HANDLE)
            continue;
            
         if (!isFileSizeLimitReached(temp_handle))
            {
               handle = temp_handle;
               break;
            }
         else
             FileClose(temp_handle); //Close a temporarily opened file
        }
     }

//---
   
   FileSeek(handle, 0, SEEK_END); //Move to the end of the file
  }
```

 

```
   bool              isFileSizeLimitReached(int handle)
     {
      int size = (int)FileSize(handle);
      if(size <= MAX_FILE_SIZEMB * 1000000)
         return false;   // No rotation
      
      //---
      
      return true;
     }
```

 
 
Exa
mple outputs.
 
 
![](https://c.mql5.com/2/183/log_files_rotation__1.gif)
 
File size estimation might not be the most accurate, but it is very close. When a file is close to the 10 MegaBytes mark, a new one is created, and new logs are written inside it.
 
console_on
 
When set to true, all the logs will be printed in the console (Experts Tab) after they have been saved in a specified log file.
 
This helps us avoid writing an additional line of code just for printing the information.
 
file_common
 
This boolean variable tells whether a specified "log file" is located under the 
[Common directory](/en/docs/standardlibrary/tradeclasses/cterminalinfo/cterminalinfocommondatapath)
 (when set to true) or the regular 
[MQL5 data path](/en/docs/standardlibrary/tradeclasses/cterminalinfo/cterminalinfodatapath)
 (when set to false).
 

```
//--- Open the file for writting

   m_fileflags = FILE_READ | FILE_WRITE | FILE_SHARE_WRITE | FILE_TXT | FILE_ANSI;

   if(m_iscommon)
      m_fileflags |= FILE_COMMON;
```

 
log_level
 
This variable tells the logger about how far/deep we want to print the information. 
 

```
enum LogLevels
  {
   LOG_LEVEL_DEBUG    = 10,
   LOG_LEVEL_INFO     = 20,
   LOG_LEVEL_WARNING  = 30,
   LOG_LEVEL_ERROR    = 40,
   LOG_LEVEL_CRITICAL = 50
  };

```

 
What LOG_LEVEL Does to a Class?
 
This variable is important, as many people might think, as it dictates the minimum severity that the logger will actually write to the file or print, 
It acts as a filter.
 
Suppose the user has selected LOG_LEVEL_INFO, this means that all levels below this log level will be ignored.
 
 
 
 
Function
 
Level
 
Will it Log/Print?
 
 
 
 
 
 

```
CLogger.debug()
```

 
10
 
NO
 
 
 
 

```
CLogger.info()
```

 
20
 
YES
 
 
 
 

```
CLogger.warning()
```

 
30
 
YES
 
 
 
 

```
CLogger.error()
```

 
40
 
YES
 
 
 
 

```
CLogger.critical()
```

 
50
 
YES 
 
 
 
 
So, despite the function named debug() running it, it does nothing because the level is lower than the minimum allowed.
 
 
This is very useful as it allows you to control the verbosity by configuration. For example, when you are in development mode, you might select LOG_LEVEL_DEBUG, which will make the class log everything, helping you debug your programs effectively on the contrast you might select LOG_LEVEL_WARNING in live trading mode just to log warnings, errors, and the most critical/fatal errors that must be logged.
 
 
format
 
The format variable is one of the most important variables in the class, it is the only place where you can control how the logs would appear in the experts tab and when stored within the files.
 
The table below has a description of format placeholders and their outputs.
 
 
 
 
Placeholder
 
Description
 
Notes & Example 
 
 
 
 
 
 

```
%(asctime)s
```

 
A local timestamp of the log entry TimeLocal, formatted as YYY.MM.DD HH:MM:SS.
 
A datetime value of: 2025.01.01 00:00:05.
 
 
 
 

```
%(levelname)s
```

 
Log level name as text
 
It can be INFO, DEBUG, ERROR, WARNING, CRITICAL 
 
 
 
 

```
%(programname)s
```

 
The name of the program or component. It can be set via an optional class constructor with the argument 
name.
 
Example, My Indicator.
 
 
 
 

```
%(functionname)s
```

 
Name of the function where a log is generated.
 
Can be provided manually through the logging functions, for example, OnTick, OnInit
 
 
 
 

```
%(linenumber)d
```

 
Code line number where the log is generated.
 
For example, line 118. Only if the line number is parsed, otherwise it returns empty.
 
 
 
 

```
%(programtype)s
```

 
The type of a program running, this can be set using a custom constructor. It depends on ENUM_PROGRAM_TYPE.
 

```
CLogger::CLogger(const string name,ENUM_PROGRAM_TYPE program_type):
   m_name(name),
   m_program_type(ProgramTypeToSTring(program_type))
 {
 
 }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string CLogger::ProgramTypeToSTring(ENUM_PROGRAM_TYPE prog_type)
{
   switch(prog_type)
   {
      case PROGRAM_SCRIPT:
         return "Script";

      case PROGRAM_EXPERT:
         return "EA";

      case PROGRAM_INDICATOR:
         return "Indicator";

      case PROGRAM_SERVICE:
         return "Service";

      default:
         return "Unknown";
   }
}
```

 
It can be Script, EA, Indicator, Service, or Unknown.
 
 
 
 

```
%(message)s
```

 
The log message itself.
 
For example, 
Failed to create a pending order.
 
 
 
 
We'll see in detail how the formats interact with the logs in the later sections of this post.
 
Example format.
 

```
string format = "%(asctime)s: %(levelname)s:%(programname)s:%(programtype)s:%(functionname)s:%(linenumber)d:%(message)s";
logger.basicConfig(LOG_LEVEL_DEBUG, "logs.log", false, format);
```

 
Outputs.
 
 

```
2025.12.02 09:13:54:INFO:Logging Test:Script:OnStart:36:The script has started
2025.12.02 09:13:54:ERROR:Logging Test:Script:OnStart:40:Some operation has failed Error = 0
```

 
Example format.
 

```
string format = "%(asctime)s | [%(levelname)s] [%(programname)s] [%(programtype)s] func:%(functionname)s line:%(linenumber)d --> [%(message)s]";
logger.basicConfig(LOG_LEVEL_DEBUG, "logs.log", false, format);
```

 
Outputs.
 

```
2025.12.02 09:15:41 | [INFO] [Logging Test] [Script] func:OnStart line:37 --> [The script has started]
2025.12.02 09:15:41 | [ERROR] [Logging Test] [Script] func:OnStart line:41 --> [Some operation has failed Error = 0]
```

 
 
 

### Logging Some Information

 
A private function in the class called 
Log
 is the one responsible for formatting, crafting, writing a message (log) to a file, not to mention displaying the information under the Experts tab (printing).
 

```
void              Log(LogLevels level, string msg, string func_name = "", int line_no = -1);
```

 
Since all class constructors are optional, it allows users to start logging without much configuration unless needed.
 
The function 
basicConfig
, which does the configurations, is an optional method as well. We have to reinforce default configurations (if a user hasn't offered theirs) before attempting to write (log) some information or values.
 

```
void CLogger::Log(LogLevels level,
                  string msg,
                  string func_name = "",
                  int line_no = -1)
  {
//---

   if(!is_configured)  //Auto-configure if the function basicConfig wasn't called
      basicConfig();

```

 
As described previously about Log levels, we have to check if the current level of a log is not below the required level set by the user.
 

```
//--- Level filtering

   if(level < m_loglevel)
      return;

```

 
Formatting the logs
 
We have to remove all placeholders and replace them with a desired value.
 

```
// Standard placeholders

   StringReplace(entry, "%(asctime)s", t);
   StringReplace(entry, "%(levelname)s", LevelToString(level));
   StringReplace(entry, "%(message)s", msg);

// Custom placeholders

// ---- Custom placeholders ----

// Program name

   if(m_name != "")
       StringReplace(entry, "%(programname)s", m_name);
   else
      StringReplace(entry, "%(programname)s", "");

// Function name
   if(func_name != "")
      StringReplace(entry, "%(functionname)s", func_name);
   else
      StringReplace(entry, "%(functionname)s", "");

// Program type

   if(m_program_type != "")
      StringReplace(entry, "%(programtype)s", m_program_type);
   else
      StringReplace(entry, "%(programtype)s", "");

// Line number
   if(line_no >= 0)
      StringReplace(entry, "%(linenumber)d", IntegerToString(line_no));
   else
      StringReplace(entry, "%(linenumber)d", "");

   entry += "\n";
```

 
Handling file rotations
 
Since any file can reach the 10MB maximum size (by default), we have to check for this condition every time before attempting to add new information into the file.
 

```
//--- Handle file rotations before writing

   fileRotate(m_filehandle, m_filename, m_fileflags, m_iscommon);
```

 
Writing and Printing the logs
 

```
//--- Write to log file (plain text)

   FileWriteString(m_filehandle, entry);
   FileFlush(m_filehandle);

   if(m_console_on)
      Print(entry);
```

 
The function named Log isn't accessible outside of the class, as it is meant to populate other functions for very specific log messages. A section below represents those functions.
 
 

### Specific Function for each Log Message

 
Logs for debugging purposes
 

```
   void              debug(string msg, string func_name = "", int line_no = -1)
     {
      this.Log(LOG_LEVEL_DEBUG, msg, func_name, line_no);
     }
```

 
This function is aimed at printing the message at the lowest level, usually intended for developers who want to understand the entire behaviour of some lines of code and functions.
 
Example usage.
 

```
string format = "%(asctime)s | [%(levelname)s] [%(programname)s] [%(programtype)s] func:%(functionname)s line:%(linenumber)d --> [%(message)s]";
logger.basicConfig(LOG_LEVEL_DEBUG, "logs.log", false, format);

bool num_a = 10;
bool num_b = -10;
  
logger.debug("num_a>num_b "+(string)bool(num_a>num_b), __FUNCTION__, __LINE__);  
```

 
 
Outputs.
 

```
2025.12.02 09:26:06 | [DEBUG] [Logging Test] [Script] func:OnStart line:43 --> [num_a>num_b false]
```

 
Informative logs
 
These are often the type of message used for indicating some ongoing process or activity.
 

```
void OnStart()
  {
//---
      
   logger.info("The script has started");
   
   // some activity   

   logger.info("End of the script!");
  }
```

 
Outputs.
 
 

```
2025.12.02 09:26:06 | [INFO] [Logging Test] [Script] func:OnStart line:38 --> [The script has started]
2025.12.02 09:26:06 | [INFO] [Logging Test] [Script] func: line: --> [End of the script!]
```

 
Displaying errors to users
 
These are logs intended to display a malfunction in the program.
 

```
   void              error(string msg, string func_name = "", int line_no = -1)
     {
      this.Log(LOG_LEVEL_ERROR, msg, func_name, line_no);
     }
```

 
Output.
 

```
void OnStart()
  {
//---

   if (!doSomething())
      {
        logger.error(StringFormat("Some operation has failed Error = %d",GetLastError()), __FUNCTION__, __LINE__);
      }
     
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool doSomething()
 {
   return false;
 }
```

 
Outputs.
 

```
2025.12.02 09:29:26 | [ERROR] [Logging Test] [Script] func:OnStart line:47 --> [Some operation has failed Error = 0]
```

 
Logging some warnings
 
These logs are used to warn users about something that might not be fatal to the program, but has to be acknowledged.
 
Example usage.
 

```
input int risk_per_trade = 50; //Risk Per Trade
//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
  {
//---
   
   string format = "%(asctime)s | [%(levelname)s] [%(programname)s] [%(programtype)s] func:%(functionname)s line:%(linenumber)d --> [%(message)s]";
   logger.basicConfig(LOG_LEVEL_DEBUG, "logs.log", false, format);
 
   logger.info("The script has started",__FUNCTION__,__LINE__);
   
   if (risk_per_trade>10) //if a user has set the risk higher than 10% of the account balance
      logger.warning(StringFormat("You have risked too much for a single trade. Risk percentage = %d", risk_per_trade));
  }
```

 
 
Outputs.
 

```
2025.12.02 09:15:41 | [WARNING] [Logging Test] [Script] func: line: --> [You have risked too much for a single trade. Risk percentage = 50]
```

 
Fatal or critical logs
 
These are the most important logs due to their severity. They are often used to display a huge flaw in the system that usually signifies the program can't proceed in execution until a specific issue is addressed.
 

```
   void              critical(string msg, string func_name = "", int line_no = -1)
     {
      this.Log(LOG_LEVEL_CRITICAL, msg, func_name, line_no);
     }
```

 
Suppose you have an indicator so useful to your strategy, once the program fails to load it, the whole program should break 
 

```
#include <PyMQL5\logging.mqh>
CLogger logger(PROG_NAME, PROG_TYPE);

int important_indicator_handle;
//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
  {
//---
   
   string format = "%(asctime)s | [%(levelname)s] [%(programname)s] [%(programtype)s] func:%(functionname)s line:%(linenumber)d --> [%(message)s]";
   logger.basicConfig(LOG_LEVEL_DEBUG, "logs.log", false, format);
 
   important_indicator_handle = iMA(Symbol(), Period(), -1, 0, MODE_SMA, PRICE_CLOSE); //An indicator with a negative period
   
   if (important_indicator_handle == INVALID_HANDLE)
     {
       logger.critical("Failed to load the Moving Average indicator, Error = "+(string)GetLastError(), __FUNCTION__, __LINE__);
       return;
     }
 }
```

 
 
Outputs.
 

```
2025.12.02 09:34:54 | [CRITICAL] [Logging Test] [Script] func:OnStart line:56 --> [Failed to load the Moving Average indicator, Error = 4002]
```

 
 

### Optimizing the Logging Process

 
The process of reading and writing to text files 
[(I/O operations)](/en/docs/files/fileopen)
 is one of the most expensive processes in the MQL5 language, not to mention a built-in function named Print we use for displaying the information on the Experts tab.
 
Instead of writing to a text file very often (in a matter of seconds), we can give users an option to store the logs temporarily in memory (cache) before they decide whether to save that information to some specified file.
 
 
The process is simple: have a global array we are going to write the logs to, and have a function that writes the whole array to a specified file.
 
 

```
class CLogger
  {
private:
   
   //--- Caching
   
   bool              m_cache_mode;
   string            m_logs_cache[];
   uint              m_logs_count;
   
public:

   void              CLogger(const string name);
   void              CLogger(const string name, ENUM_PROGRAM_TYPE program_type);
   void              CLogger(void); // Constructor
   void             ~CLogger(void); // Destructor

   bool              basicConfig(LogLevels log_level = LOG_LEVEL_INFO, 
                                 string filename = "logs.log",
                                 bool console_on = true,
                                 string format = DEFAULT_MSG_FORMAT,
                                 bool file_common = false,
                                 bool cache_mode = false);

   //---
   
   void              WriteCache()
     {
       for (uint i=0; i<m_logs_count; i++)
         { 
           if (m_filehandle==INVALID_HANDLE)
             DebugBreak();
           
           fileRotate(m_filehandle, m_filename, m_fileflags, m_iscommon);
             
           FileWriteString(m_filehandle, m_logs_cache[i]);
           FileFlush(m_filehandle);
         }
     }
  };
//+------------------------------------------------------------------+
//|         Basic configurations                                     |
//+------------------------------------------------------------------+
bool CLogger::basicConfig(LogLevels log_level = LOG_LEVEL_INFO,
                          string filename = "logs.log",
                          bool console_on = true,
                          string format = DEFAULT_MSG_FORMAT,
                          bool file_common = false,
                          bool cache_mode = false)
  {
   m_filename = filename;
   m_logs_format = format;
   m_console_on = console_on;
   m_iscommon = file_common;
   m_loglevel = log_level;
   m_cache_mode = cache_mode;

//--- some lines of code

   return true;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void CLogger::Log(LogLevels level,
                  string msg,
                  string func_name = "",
                  int line_no = -1)
  {
//---

// some lines of code....

//--- Write to log file (plain text)
   
   if (m_cache_mode) //Write to an array 
     {
       this.m_logs_count++;
       if (m_logs_count>m_logs_cache.Size()) 
         ArrayResize(m_logs_cache, m_logs_count+MAX_CACHE_SIZE); 
       
       //---
       
       m_logs_cache[m_logs_count-1] = entry;
     }
   else // write to a file
     {
       FileWriteString(m_filehandle, entry);
       FileFlush(m_filehandle);
     }

   if(m_console_on)
      Print(entry);
  }
```

 
The function named 
WriteCache 
writes all the information stored in the array 
m_logs_cache
 to a desired file, similarly to how the information is written automatically to the files when variable 
cache_mode
 is set to false inside the function 
basicConfig
.
 
Since users are capable of calling this function as they would like, let's make things much simpler by introducing a boolean variable named 
write_cache_automatically
to the 
basicConfig
 function, when this variable is set to 
true
 all the information stored in a temporary cached array will be written to a specified file in the destructor of the class.
 
 
Assuming that we want to save the logs after all operations are complete. i.e., An expert advisor is removed from the chart, or the strategy tester operation has ended.
 
 

```
bool CLogger::basicConfig(LogLevels log_level = LOG_LEVEL_INFO,
                          string filename = "logs.log",
                          bool console_on = true,
                          string format = DEFAULT_MSG_FORMAT,
                          bool file_common = false,
                          bool cache_mode = false,
                          bool write_cache_automatically = false)
  {
   m_filename = filename;
   m_logs_format = format;
   m_console_on = console_on;
   m_iscommon = file_common;
   m_loglevel = log_level;
   m_cache_mode = cache_mode;
   m_write_cache_automatically = write_cache_automatically;
```

 

```
CLogger::~CLogger(void)
  {
   if (m_cache_mode && m_write_cache_automatically)
      WriteCache();
   
//---

   if(m_filehandle != INVALID_HANDLE)
      FileClose(m_filehandle); //Close the file, finally
  }
```

 
Finally, I was able to see some improvements in the strategy tester (about a 50% decrease in testing time) compared to the non-caching version. 
 
This was also after several changes were made in the function responsible for rotating the files.
 

```
void CLogger::fileRotate(int &handle, string &filename, int flags, bool is_common)
{
   //---If first time -> open main file
   if(handle == -1)
   {
      handle = OpenFile(filename, flags);
      if(handle == -1) 
         return;
   }

   //--- Check rotation trigger
   if(!isFileSizeLimitReached(handle))
      return;

   //--- Close current big file 
   FileClose(handle);
   
   //--- Rotate through numbered files
   for(int i = 1; i <= MAX_LOG_FILES; i++)
   {
      string new_name = m_base_name + "_" + (string)i + m_file_extension;

      // File exists → check if it still has space
      if(is_common?FileIsExist(new_name, FILE_COMMON):FileIsExist(new_name))
      {
         int temp = OpenFile(filename, flags);
         
         //---
         
         if (MQLInfoInteger(MQL_DEBUG))  
           printf("Filename %s size MB = %f",new_name, FileSize(temp)/1e6);
          
         if (temp != -1)
          {
            bool too_big = isFileSizeLimitReached(temp);
            FileClose(temp);

            if(too_big)
               continue;   //--- The fill is full try the next one
          }
      }

      // File does not exist or is small, use it
      if (filename == new_name)
        return;
        
      filename = new_name;
      handle = OpenFile(filename, flags);

      if(handle == -1)
         DebugBreak();

      FileSeek(handle, 0, SEEK_END);
      return;   // IMPORTANT: stop rotation here
   }
}
```

 
Optimal strategy testing with logging
 
After ensuring the caching mode is set to true, you need to prevent printing by setting 
console_on
 variable to false in the strategy tester unless you have a solid reason to do so, this might help to lower the overall tester runtime.
 

```
#define PROG_NAME MQLInfoString(MQL_PROGRAM_NAME)
#define PROG_TYPE (ENUM_PROGRAM_TYPE)MQLInfoInteger(MQL_PROGRAM_TYPE)
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
#include <PyMQL5\logging.mqh>
CLogger logger(PROG_NAME, PROG_TYPE);
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
   
   string format = "%(asctime)s:%(programname)s:%(programtype)s:%(functionname)s:%(linenumber)d:%(message)s";
   
   bool is_tester = (bool)MQLInfoInteger(MQL_TESTER);
   logger.basicConfig(LOG_LEVEL_DEBUG, "logs.log", !is_tester, format, is_tester, true, true);
 
   logger.info("Program started!");
   
//---
   return(INIT_SUCCEEDED);
  }
```

 
 
Since the Strategy Tester stores all the information stored in files in a different data path, we have to set the variable 
file_common
 
to true so that we can get all logs stored under the 
common folder
.
 
The rest of an EA.
 

```
void OnDeinit(const int reason)
  {
//---
   logger.info("Program stopped. Reason = "+UninitializeReasonDescription(reason), __FUNCTION__, __LINE__);
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---
   
   logger.info("Program running");
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string UninitializeReasonDescription(const int reason) 
  { 
   switch(reason) 
     { 
      //--- the EA has stopped working calling the ExpertRemove() function 
      case REASON_PROGRAM : 
        return("Expert Advisor terminated its operation by calling the ExpertRemove() function"); 
      //--- program removed from a chart 
      case REASON_REMOVE : 
        return("Program has been deleted from the chart"); 
      //--- program recompiled 
      case REASON_RECOMPILE : 
        return("Program has been recompiled"); 
      //--- symbol or chart period changed 
      case REASON_CHARTCHANGE : 
        return("Symbol or chart period has been changed"); 
      //--- chart closed 
      case REASON_CHARTCLOSE : 
        return("Chart has been closed"); 
      //--- inputs changed by user 
      case REASON_PARAMETERS : 
        return("Input parameters have been changed by a user"); 
      //--- another account has been activated or reconnection to the trade server has occurred due to changes in the account settings 
      case REASON_ACCOUNT : 
        return("Another account has been activated or reconnection to the trade server has occurred due to changes in the account settings"); 
      //--- another chart template applied 
      case REASON_TEMPLATE : 
        return("A new template has been applied"); 
      //--- OnInit() handler returned a non-zero value 
      case REASON_INITFAILED : 
        return("This value means that OnInit() handler has returned a nonzero value"); 
      //--- terminal closed 
      case REASON_CLOSE : 
        return("Terminal has been closed"); 
     } 
  
//--- deinitialization reason unknown 
   return("Unknown reason"); 
  }
```

 
Output.
 
Several files were created under the common directory as expected, each file with a size close to 10 MB.
 
 
![](https://c.mql5.com/2/184/tester_logs.gif)
 
 

### Making Logging Much Easier — The Python Way

 
If you are familiar with the logging module in Python, you might notice that it doesn't require you to parse the name of the function and a specific line of code that produces an error.
 

```
import logging
logger = logging.getLogger(__name__)

logging.basicConfig(filename='myapp.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s - file:%(filename)s - line:%(lineno)d - func:%(funcName)s')

def some_function():
    logger.info('Doing something')    
    
some_function()
```

 
Output.
 

```
2025-12-01 20:01:42,542 - INFO - Doing something - file:log.py - line:9 - func:some_function

```

 
In MQL5, we have to hardcode most of the values (a line and function name for every log message, program name(filename) in the class constructor). To avoid this tiresome/repetitive process, we can use the 
[#define](/en/docs/basis/preprosessor/constant)
 macros.
 

```
#define logger_info(msg) logger.info(msg, __FUNCTION__, __LINE__)
#define logger_debug(msg) logger.debug(msg, __FUNCTION__, __LINE__)
#define logger_warning(msg) logger.warning(msg, __FUNCTION__, __LINE__)
#define logger_error(msg) logger.error(msg, __FUNCTION__, __LINE__)
#define logger_critical(msg) logger.critical(msg, __FUNCTION__, __LINE__)
```

 
Usage.
 

```
void OnStart()
  {
//---
   
   string format = "%(asctime)s | [%(levelname)s] [%(programname)s] [%(programtype)s] func:%(functionname)s line:%(linenumber)d --> [%(message)s]";
   logger.basicConfig(LOG_LEVEL_DEBUG, "logs.log", false, format);
 
   logger_info("The script has started");
   
   bool num_a = 10;
   bool num_b = -10;
     
   logger_info("num_a>num_b "+(string)bool(num_a>num_b));  

   if (!doSomething())
      {
        logger_error(StringFormat("Some operation has failed Error = %d",GetLastError()));
      }
      
   if (risk_per_trade>10) //if a user has set the risk higher than 10% of the account balance
      logger_warning(StringFormat("You have risked too much for a single trade. Risk percentage = %d", risk_per_trade));
      
   important_indicator_handle = iMA(Symbol(), Period(), -1, 0, MODE_SMA, PRICE_CLOSE); //An indicator with a negative period
   
   if (important_indicator_handle == INVALID_HANDLE)
     {
       logger_critical("Failed to load the Moving Average indicator, Error = "+(string)GetLastError());
       //return;
     }
     
//---

   logger_info("End of the script!");
  }
```

 
 
Outputs.
 

```
2025.12.02 09:47:49 | [INFO] [Logging Test] [Script] func:OnStart line:43 --> [The script has started]
2025.12.02 09:47:49 | [INFO] [Logging Test] [Script] func:OnStart line:48 --> [num_a>num_b false]
2025.12.02 09:47:49 | [ERROR] [Logging Test] [Script] func:OnStart line:52 --> [Some operation has failed Error = 0]
2025.12.02 09:47:49 | [WARNING] [Logging Test] [Script] func:OnStart line:56 --> [You have risked too much for a single trade. Risk percentage = 50]
2025.12.02 09:47:49 | [CRITICAL] [Logging Test] [Script] func:OnStart line:62 --> [Failed to load the Moving Average indicator, Error = 4002]
2025.12.02 09:47:49 | [INFO] [Logging Test] [Script] func:OnStart line:68 --> [End of the script!]
```

 
 

### Final Thoughts

 
Logging is more than just printing plain text into the Experts tab
. It is a fundamental part of software development, helping us understand how our program behaves, diagnose problems, and trace events over time.
 
By implementing a structured and reusable logging module in MQL5, similar to Python’s logging library. We bring modern development practices into our trading systems. This makes our code easier to maintain, easier to debug, and more consistent with how professional developers worldwide store and interpret logs in Python-based systems, web servers, etc. 
 
 
A reliable logging module is not just a convenience; it is a tool that helps to keep us organized, efficient, and aligned with industry-standard programming practices.
 
A repository containing all the code discussed in this article series can be found here: 
[https://github.com/MegaJoctan/PyMQL5](/go?link=https://github.com/MegaJoctan/PyMQL5)
 for contributions and bug fixes.
 
 
Attachments Table
 
 
 
 
Filename
 
Description & Usage
 
 
 
 
 
Include\PyMQL5\logging.mqh
 
Python-like logging class for displaying and storing the logs. It has the class named CLogger.
 
 
 
Scripts\Logging Test.mq5
 
A simple script for testing methods presented in the CLogger class.
 
 
 
Experts\Logging Test.mq5
 
An Expert Advisor (EA) designed to test the methods presented in the CLogger class in the real trading environment.
 
 
 

Attached files
 |
  

[Download ZIP](/en/articles/download/20458.zip)

[Attachments.zip](/en/articles/download/20458/Attachments.zip)

(7.35 KB)

Warning:
 All rights to these materials are reserved by MetaQuotes Ltd. Copying or reprinting of these materials in whole or in part is prohibited.

This article was written by a user of the site and reflects their personal views. MetaQuotes Ltd is not responsible for the accuracy of the information presented, nor for any consequences resulting from the use of the solutions, strategies or recommendations described.

#### Other articles by this author

[Implementing Practical Modules from Other Languages in MQL5 (Part 04): time, date, and datetime modules from Python](/en/articles/19035)

[Python-MetaTrader 5 Strategy Tester (Part 01): Trade Simulator](/en/articles/18971)

[Implementing Practical Modules from Other Languages in MQL5 (Part 03): Schedule Module from Python, the OnTimer Event on Steroids](/en/articles/18913)

[Data Science and ML (Part 46): Stock Markets Forecasting Using N-BEATS in Python](/en/articles/18242)

[Implementing Practical Modules from Other Languages in MQL5 (Part 02): Building the REQUESTS Library, Inspired by Python](/en/articles/18728)

[Implementing Practical Modules from Other Languages in MQL5 (Part 01): Building the SQLite3 Library, Inspired by Python](/en/articles/18640)

[Go to discussion](/en/forum/501166)

![Currency pair strength indicator in pure MQL5](https://c.mql5.com/2/123/Indicator_for_assessing_the_strength_and_weakness_of_currency_pairs_in_pure_MQL5__LOGO.png)

[Currency pair strength indicator in pure MQL5](/en/articles/17303)

We are going to develop a professional indicator for currency strength analysis in MQL5. This step-by-step guide will show you how to develop a powerful trading tool with a visual dashboard for MetaTrader 5. You will learn how to calculate the strength of currency pairs across multiple timeframes (H1, H4, D1), implement dynamic data updates, and create a user-friendly interface.

![The View and Controller components for tables in the MQL5 MVC paradigm: Simple controls](https://c.mql5.com/2/146/18221-komponenti-view-i-controller-logo.png)

[The View and Controller components for tables in the MQL5 MVC paradigm: Simple controls](/en/articles/18221)

The article covers simple controls as components of more complex graphical elements of the View component within the framework of table implementation in the MVC (Model-View-Controller) paradigm. The basic functionality of the Controller is implemented for interaction of elements with the user and with each other. This is the second article on the View component and the fourth one in a series of articles on creating tables for the MetaTrader 5 client terminal.

![Statistical Arbitrage Through Cointegrated Stocks (Part 8): Rolling Windows Eigenvector Comparison for Portfolio Rebalancing](https://c.mql5.com/2/184/20485-statistical-arbitrage-through-logo.png)

[Statistical Arbitrage Through Cointegrated Stocks (Part 8): Rolling Windows Eigenvector Comparison for Portfolio Rebalancing](/en/articles/20485)

This article proposes using Rolling Windows Eigenvector Comparison for early imbalance diagnostics and portfolio rebalancing in a mean-reversion statistical arbitrage strategy based on cointegrated stocks. It contrasts this technique with traditional In-Sample/Out-of-Sample ADF validation, showing that eigenvector shifts can signal the need for rebalancing even when IS/OOS ADF still indicates a stationary spread. While the method is intended mainly for live trading monitoring, the article concludes that eigenvector comparison could also be integrated into the scoring system—though its actual contribution to performance remains to be tested.

![From Basic to Intermediate: Structs (II)](https://c.mql5.com/2/120/Do_bzsico_ao_intermedi1rio_Struct_I___LOGO.png)

[From Basic to Intermediate: Structs (II)](/en/articles/15731)

In this article, we will try to understand why programming languages like MQL5 have structures, and why in some cases structures are the ideal way to pass values between functions and procedures, while in other cases they may not be the best way to do it.

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

