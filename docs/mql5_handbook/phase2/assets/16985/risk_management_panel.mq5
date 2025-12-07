//+------------------------------------------------------------------+
//|                                        Risk Management Panel.mq5 |
//|                                                        Your name |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Your name"
#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict

#include <Controls\Dialog.mqh>
#include <Controls\Edit.mqh>
#include <Controls\Label.mqh>
#include <Controls\Button.mqh>
#include <Risk_Management.mqh>
#include <Controls\ComboBox.mqh>

//+------------------------------------------------------------------+
//| defines                                                          |
//+------------------------------------------------------------------+
//--- for edits
#define EDIT_HEIGHT                         (20)      // edit height

//--- for buttons
#define BUTTON_WIDTH                        (80)     // size by X coordinate 
#define BUTTON_HEIGHT                       (20)      // size by Y coordinate 

//--- for combo box
#define COMBO_BOX_WIDTH                        (200)     // size by X coordinate 
#define COMBO_BOX_HEIGHT                       (20)      // size by Y coordinate 

string elements_order_type[8] =
  {
   "ORDER_TYPE_BUY",
   "ORDER_TYPE_SELL",
   "ORDER_TYPE_BUY_LIMIT",
   "ORDER_TYPE_SELL_LIMIT",
   "ORDER_TYPE_BUY_STOP",
   "ORDER_TYPE_SELL_STOP",
   "ORDER_TYPE_BUY_STOP_LIMIT",
   "ORDER_TYPE_SELL_STOP_LIMIT"
  };

//+-------------------------------------------------------------------+
//| Class CRiskManagementPanel                                        |
//| This class inherits from CAppDialog and will define the panel for |
//| managing risk parameters.                                         |
//+-------------------------------------------------------------------+
class CRiskManagementPanel : public CAppDialog
  {
private:
   //--- Labels for risk parameters
   CLabel            m_label_risk_per_operation;    // Label for risk per operation
   CEdit             m_edit_risk_per_operation;     // Edit control for entering risk per operation

   CLabel            m_label_deviation;             // Label for deviation
   CEdit             m_edit_deviation;              // Edit control for entering deviation

   CLabel            m_label_stop_limit;            // Label for stop limit
   CEdit             m_edit_stop_limit;             // Edit control for entering stop limit

   //--- Labels and controls for order type and lot size
   CLabel            m_label_get_lote;              // Label for get lot size
   CComboBox         m_combobox_order_type_get_lot; // ComboBox for selecting order type to get lot size

   CLabel            m_label_sl;                    // Label for stop loss
   CEdit             m_edit_sl;                     // Edit control for entering stop loss
   CButton           m_button_get_lote;             // Button for calculating lot size
   CLabel            m_label_result_lote;           // Label to display result for lot size
   CLabel            m_label_the_result_lote;       // Label for the result of lot size

   //--- Labels and controls for stop loss order type
   CLabel            m_label_get_sl;                // Label for stop loss
   CComboBox         m_combobox_order_type_get_sl;  // ComboBox for selecting order type for stop loss
   CLabel            m_label_lote;                  // Label for lot
   CButton           m_button_get_sl;               // Button to get stop loss
   CLabel            m_label_result_sl;             // Label for result of stop loss
   CLabel            m_label_the_result_sl;         // Label for the result of stop loss


   //--- Variables to store the data entered by the user
   double            deviation;                    // Stores deviation entered by the user
   double            stop_limit;                   // Stores stop limit entered by the user
   double            risk_per_operation;           // Stores risk per operation entered by the user
   long              sl;                           // Stores stop loss value entered by the user
   ENUM_ORDER_TYPE   order_type_get_sl;            // Stores the selected order type for stop loss
   ENUM_ORDER_TYPE   order_type_get_lot;           // Stores the selected order type for lot size


   //--- create labels and buttons
   bool CreateAreaClientPanel();

   //--- functions to edit labels dynamically
   void EditLabelResultSL(string text);
   void EditLabelResultLote(string text);

   //--- create controls (buttons, labels, edits, combo boxes)
   bool CreateEdit(CEdit &m_edit, const string name, const int x1, const int y1, string initial_Text = "");
   bool CreateLabel(CLabel &label, const string name, const string text, const int x1, const int y1);
   bool CreateButton(CButton &button, const string name, const string text, const int x1, const int y1, int x2_ = BUTTON_WIDTH, int y2_ = BUTTON_HEIGHT);
   bool CreateComboBox(CComboBox &combo_box, const string name, string &elements[], string initial_text, const int x1, const int y1);

   //--- combo box functions for handling user input
   void OnChangeComBoxOrderTypeGetLote();
   void OnChangeComBoxOrderTypeGetSL();


public:
   CRiskManagementPanel(void);
   ~CRiskManagementPanel(void);

   //--- create panel and controls
   virtual bool Create(const long chart, const string name, const int subwin, const int x1, const int y1, const int x2, const int y2);
    
   //--- chart event handler
   virtual bool OnEvent(const int id, const long &lparam, const double &dparam, const string &sparam);

   //--- function to convert string to ENUM_ORDER_TYPE
   static ENUM_ORDER_TYPE StringOrderTypeToEnum(const string OrderType);

  };

//+------------------------------------------------------------------+
//| Function to convert a string into an order type                  |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE CRiskManagementPanel::StringOrderTypeToEnum(const string OrderType)
{
   // Convert the string order type to its corresponding enum value
   if(OrderType == "ORDER_TYPE_BUY")
      return ORDER_TYPE_BUY;
   if(OrderType == "ORDER_TYPE_SELL")
      return ORDER_TYPE_SELL;
   if(OrderType == "ORDER_TYPE_BUY_LIMIT")
      return ORDER_TYPE_BUY_LIMIT;
   if(OrderType == "ORDER_TYPE_SELL_LIMIT")
      return ORDER_TYPE_SELL_LIMIT;
   if(OrderType == "ORDER_TYPE_BUY_STOP")
      return ORDER_TYPE_BUY_STOP;
   if(OrderType == "ORDER_TYPE_SELL_STOP")
      return ORDER_TYPE_SELL_STOP;
   if(OrderType == "ORDER_TYPE_BUY_STOP_LIMIT")
      return ORDER_TYPE_BUY_STOP_LIMIT;
   if(OrderType == "ORDER_TYPE_SELL_STOP_LIMIT")
      return ORDER_TYPE_SELL_STOP_LIMIT;

   // Return WRONG_VALUE if no match is found
   return WRONG_VALUE;
}

//+------------------------------------------------------------------+
//| Function to update the variable that stores                      |
//| the order type to obtain the ideal sl                            |
//+------------------------------------------------------------------+
void CRiskManagementPanel::OnChangeComBoxOrderTypeGetSL(void)
{
   // Iterate through the order types array to find the selected type
   for(int i = 0; i < ArraySize(elements_order_type); i++)
   {
      // If the selected order type matches the one in the array
      if(m_combobox_order_type_get_sl.Select() == elements_order_type[i])
      {
         // Update the order type variable for stop loss
         this.order_type_get_sl = StringOrderTypeToEnum(m_combobox_order_type_get_sl.Select());
         Print("New order type for sl: ", EnumToString(this.order_type_get_sl)); // Log the selected order type
         break;
      }
   }
}
//+------------------------------------------------------------------+
//| Function to update the variable that stores                      |
//| the order type to obtain the ideal lot                           |
//+------------------------------------------------------------------+
void CRiskManagementPanel::OnChangeComBoxOrderTypeGetLote(void)
{
   // Iterate through the order types array to find the selected type
   for(int i = 0; i < ArraySize(elements_order_type); i++)
   {
      // If the selected order type matches the one in the array
      if(m_combobox_order_type_get_lot.Select() == elements_order_type[i])
      {
         // Update the order type variable for lot size
         this.order_type_get_lot = StringOrderTypeToEnum(m_combobox_order_type_get_lot.Select());
         Print("New order type for lot: ", EnumToString(this.order_type_get_lot)); // Log the selected order type
         break;
      }
   }
}

//+------------------------------------------------------------------+
//| Function to edit the text of the stop loss label                 |
//+------------------------------------------------------------------+
void CRiskManagementPanel::EditLabelResultSL(string text)
{
   // This function updates the text of the label that shows the ideal stop loss value.
   this.m_label_the_result_sl.Text(text); // Set the new text to the stop loss label
}

//+------------------------------------------------------------------+
//| Function to edit the text of the lot size label                   |
//+------------------------------------------------------------------+
void CRiskManagementPanel::EditLabelResultLote(string text)
{
   // This function updates the text of the label that shows the ideal lot size.
   this.m_label_the_result_lote.Text(text); // Set the new text to the label
}
  
//+-------------------------------------------------------------------+
//| Function to create the complex object: combo box                  |
//| This function creates a combo box with multiple selectable items. |
//+-------------------------------------------------------------------+
bool CRiskManagementPanel::CreateComboBox(CComboBox &combo_box, const string name, string &elements[], string initial_text, const int x1, const int y1)
{
   //--- calculate coordinates for the combo box
   int x2 = x1 + COMBO_BOX_WIDTH;
   int y2 = y1 + COMBO_BOX_HEIGHT;

   //--- create the combo box control
   if (!combo_box.Create(m_chart_id, name, m_subwin, x1, y1, x2, y2))
      return (false);

   //--- add items to the combo box
   for (int i = 0; i < ArraySize(elements); i++)
   {
      if (!combo_box.AddItem(elements[i], i))
         return (false);
   }

   //--- select the initial text
   combo_box.SelectByText(initial_text);

   //--- add the combo box to the panel
   if (!Add(combo_box))
      return (false);

   //--- successfully created the combo box
   return (true);
}

//+------------------------------------------------------------------+
//| Main function to create the components of the panel area         |
//+------------------------------------------------------------------+
bool CRiskManagementPanel::CreateAreaClientPanel(void)
{
   int x1 = 11; // Initial X coordinate
   int y1 = 15; // Initial Y coordinate

   // --- General Section: Risk Per Operation Configuration ---
   if (!CreateLabel(m_label_risk_per_operation, "L-Risk-Per-operation", "Risk per operation %: ", x1, y1))
      return false; // Create the label for risk per operation
   if (!CreateEdit(m_edit_risk_per_operation, "Risk-Per-operation", x1 + 150, y1))
      return false; // Create the editable field for risk per operation
   
   y1 += 30; // Move the Y coordinate down for the next section

   if (!CreateLabel(m_label_deviation, "L-Deviation", "Deviation (Points):", x1, y1))
      return false; // Create the label for deviation
   if (!CreateEdit(m_edit_deviation, "Deviation", x1 + 150, y1, "100"))
      return false; // Create the editable field for deviation
   
   this.deviation = 100; // Default value for deviation

   y1 += 30;

   if (!CreateLabel(m_label_stop_limit, "L-StopLimit", "Stop Limit (Points):", x1, y1))
      return false; // Create the label for stop limit
   if (!CreateEdit(m_edit_stop_limit, "Stop Limit", x1 + 150, y1, "50"))
      return false; // Create the editable field for stop limit
   
   this.stop_limit = 50; // Default value for stop limit

   y1 += 50;

   // --- Lot Calculation Section ---
   if (!CreateLabel(m_label_get_lote, "L-Get-Lote-Title", "Get Lote", x1, y1))
      return false; // Create the label for lot calculation section
   if (!CreateComboBox(m_combobox_order_type_get_lot, "ORDER_TYPE_LOT", elements_order_type, "ORDER_TYPE_BUY", x1 + 60, y1))
      return false; // Create the combo box to select order type for lot calculation

   this.order_type_get_lot = ORDER_TYPE_BUY; // Default order type

   y1 += 30;

   if (!CreateLabel(m_label_sl, "L-SL", "SL Point: ", x1, y1))
      return false; // Create the label for SL point
   if (!CreateEdit(m_edit_sl, "WRITE-SL", x1 + 60, y1))
      return false; // Create the editable field for SL
   if (!CreateButton(m_button_get_lote, "GET-LOTE", "Save", x1 + 160 + 5, y1))
      return false; // Create the button to save the lot calculation

   y1 += 25;

   if (!CreateLabel(m_label_result_lote, "L-Result-Lote", "Ideal Lot: ", x1, y1))
      return false; // Create the label for displaying the ideal lot
   if (!CreateLabel(m_label_the_result_lote, "L-The-Result-lot", "  ", x1 + 65, y1))
      return false; // Create a label to display the calculated ideal lot

   y1 += 50;

   // --- Stop Loss Calculation Section ---
   if (!CreateLabel(m_label_get_sl, "L-Get-SL-Title", "Get SL", x1, y1))
      return false; // Create the label for stop loss calculation section
   if (!CreateComboBox(m_combobox_order_type_get_sl, "ORDER_TYPE_SL", elements_order_type, "ORDER_TYPE_BUY", x1 + 50, y1))
      return false; // Create the combo box to select order type for stop loss calculation

   this.order_type_get_sl = ORDER_TYPE_BUY; // Default order type

   y1 += 30;

   if (!CreateLabel(m_label_lote, "L-LOTE", "Get ideal sl:", x1, y1))
      return false; // Create the label for getting the ideal stop loss
   if (!CreateButton(m_button_get_sl, "GET-SL", "Get", x1 + 90, y1))
      return false; // Create the button to get the stop loss value

   y1 += 25;

   if (!CreateLabel(m_label_result_sl, "L-Result-sl", "Ideal SL:", x1, y1))
      return false; // Create the label for displaying the ideal stop loss
   if (!CreateLabel(m_label_the_result_sl, "L-The-result-sl", "  ", x1 + 65, y1))
      return false; // Create a label to display the calculated ideal stop loss

   return true; // If all components are successfully created
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CRiskManagementPanel::CRiskManagementPanel(void)
  {
  }
//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CRiskManagementPanel::~CRiskManagementPanel(void)
  {
  }
//+------------------------------------------------------------------+
//| function to create the interface                                 |
//+------------------------------------------------------------------+
bool CRiskManagementPanel::Create(const long chart,const string name,const int subwin,const int x1,const int y1,const int x2,const int y2)
  {
   if(!CAppDialog::Create(chart,name,subwin,x1,y1,x2,y2))
      return(false);
   if(!CreateAreaClientPanel())
      return(false);
//--- succeed
   return(true);
  }
//+------------------------------------------------------------------+
//| Function to create edits                                         |
//+------------------------------------------------------------------+
bool CRiskManagementPanel::CreateEdit(CEdit &m_edit, const string name, const int x1, const int y1, string initial_Text = "")
  {
//--- coordinates
   int y2=y1+EDIT_HEIGHT;
   int x2 =x1 +100;
//--- create
   if(!m_edit.Create(m_chart_id,name+"Edit",m_subwin,x1,y1,x2,y2))
      return(false);
//--- allow editing the content
   if(!m_edit.ReadOnly(false))
      return(false);
   if(!Add(m_edit))
      return(false);

   m_edit.Text(initial_Text);

//--- succeed
   return(true);
  }
//+------------------------------------------------------------------+
//| Function to create labels                                        |
//+------------------------------------------------------------------+
bool CRiskManagementPanel::CreateLabel(CLabel &label,const string name, const string text, const int x1, const int y1)
  {
//--- coordinates
   int x2=x1+50;
   int y2=y1+20;
//--- create
   if(!label.Create(m_chart_id,name+"Label",m_subwin,x1,y1,x2,y2))
      return(false);
   if(!label.Text(text))
      return(false);
   if(!Add(label))
      return(false);

//--- succeed
   return(true);
  }
//+------------------------------------------------------------------+
//| Function to create buttons                                       |
//+------------------------------------------------------------------+
bool CRiskManagementPanel::CreateButton(CButton &buttom,const string name, const string text, const int x1, const int y1,int x2_= BUTTON_WIDTH,int y2_ = BUTTON_HEIGHT)
  {
   int x2=x1+x2_;
   int y2=y1+y2_;
//--- create
   if(!buttom.Create(m_chart_id,name,m_subwin,x1,y1,x2,y2))
      return(false);
   if(!buttom.Text(text))
      return(false);
   if(!Add(buttom))
      return(false);
//--- succeed
   return(true);
  }
//+------------------------------------------------------------------+
//| On Event function to execute chart events                        |
//+------------------------------------------------------------------+
bool CRiskManagementPanel::OnEvent(const int id,const long &lparam,const double &dparam,const string &sparam)
  {
   if(id == ON_CHANGE  + CHARTEVENT_CUSTOM && lparam == m_combobox_order_type_get_lot.Id())
     {
      OnChangeComBoxOrderTypeGetLote();
     }
   if(id == ON_CHANGE + CHARTEVENT_CUSTOM && lparam == m_combobox_order_type_get_sl.Id())
     {
      OnChangeComBoxOrderTypeGetSL();
     }
   if(id == ON_END_EDIT + CHARTEVENT_CUSTOM  && lparam == m_edit_risk_per_operation.Id())
     {
      this.risk_per_operation = StringToDouble(m_edit_risk_per_operation.Text());
      this.risk_per_operation = NormalizeDouble((this.risk_per_operation/100.0)*AccountInfoDouble(ACCOUNT_BALANCE),2);
      Print("Edit Risk Per Operation: ", this.risk_per_operation);
     }
   if(id == ON_END_EDIT + CHARTEVENT_CUSTOM  && lparam == m_edit_sl.Id())
     {
      this.sl = StringToInteger(m_edit_sl.Text());
      Print("Edit SL: ",  this.sl);
     }
   if(id == ON_END_EDIT + CHARTEVENT_CUSTOM  && lparam == m_edit_deviation.Id())
     {
      this.deviation  = StringToDouble(m_edit_deviation.Text());
      Print("Edit Deviation: ", this.deviation);
     }
   if(id == ON_END_EDIT + CHARTEVENT_CUSTOM  && lparam == m_edit_stop_limit.Id())
     {
      this.stop_limit = StringToDouble(m_edit_stop_limit.Text());
      Print("Edit Stop Limit: ",  this.stop_limit);
     }


//+------------------------------------------------------------------+
   if(id == ON_CLICK + CHARTEVENT_CUSTOM && lparam == m_button_get_lote.Id())
     {
      Print("Risk Per operation: ", this.risk_per_operation);
      Print("SL in points: ", this.sl);
      Print("Order type get lot: ", EnumToString(this.order_type_get_lot));

      double new_lot;
      double new_risk_per_operation;

      GetIdealLot(new_lot,GetMaxLote(this.order_type_get_lot),this.risk_per_operation,new_risk_per_operation,this.sl);

      PrintFormat("Loss in case the following operation fail, with the parameters: lot %.2f and stop loss of %i points will be %.2f ",new_lot,this.sl,new_risk_per_operation);

      EditLabelResultLote(DoubleToString(new_lot,2));
      m_button_get_lote.Pressed(false);
     }
//+------------------------------------------------------------------+
   if(id == ON_CLICK + CHARTEVENT_CUSTOM && lparam == m_button_get_sl.Id())
     {
      Print("Risk Per operation: ", this.risk_per_operation);
      Print("Order type get sl: ", EnumToString(this.order_type_get_lot));
      double new_lot;

      long new_sl = CalculateSL(this.order_type_get_sl,this.risk_per_operation,new_lot,this.deviation,this.stop_limit);
      PrintFormat("For the risk per operation %.2f the chosen lot is %.2f and the ideal stop loss in points is %i",this.risk_per_operation,new_lot,new_sl);

      EditLabelResultSL(IntegerToString(new_sl));
      m_button_get_sl.Pressed(false);
     }


   return(CAppDialog::OnEvent(id, lparam, dparam, sparam));
  }
//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CRiskManagementPanel risk_panel;
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- create application dialog
   if(!risk_panel.Create(0,"Test Risk Management",0,40,40,380,380))
      return(INIT_FAILED);
//--- run application
   risk_panel.Run();
//--- succeed
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//--- destroy dialog
   risk_panel.Destroy(reason);
  }
//+------------------------------------------------------------------+
//| Expert chart event function                                      |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,         // event ID
                  const long& lparam,   // event parameter of the long type
                  const double& dparam, // event parameter of the double type
                  const string& sparam) // event parameter of the string type
  {
   risk_panel.ChartEvent(id,lparam,dparam,sparam);
  }

//+------------------------------------------------------------------+
