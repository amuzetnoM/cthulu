import sys
import time
import threading
import re
import json
import os
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    import requests
except Exception:
    print("Tkinter not available; GUI cannot start.")
    sys.exit(2)

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cthulu.persistence.database import Database, TradeRecord

LOG_PATH = Path(__file__).parents[1] / 'Cthulu.log'
SUMMARY_PATH = Path(__file__).parents[1] / 'logs' / 'latest_summary.txt'
STRATEGY_INFO_PATH = Path(__file__).parents[1] / 'logs' / 'strategy_info.txt'

REFRESH_INTERVAL = 2000  # ms
TAIL_LINES = 200

RPC_ENDPOINTS = [
    'http://127.0.0.1:8181/trade',
    'http://127.0.0.1:8181/order',
    'http://127.0.0.1:8181/rpc/order',
    'http://127.0.0.1:8181/place_order',
]

THEME_BG = '#0f1720'
THEME_FG = '#e6eef6'
ACCENT = '#8b5cf6'  # Cthulu thematic purple


def tail_file(path: Path, lines: int = TAIL_LINES):
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2)
            filesize = f.tell()
            blocksize = 1024
            data = b''
            while filesize > 0 and lines >= 0:
                read_size = min(blocksize, filesize)
                f.seek(filesize - read_size)
                chunk = f.read(read_size)
                data = chunk + data
                filesize -= read_size
                if data.count(b'\n') > lines:
                    break
            text = data.decode('utf-8', errors='replace')
            return '\n'.join(text.splitlines()[-lines:])
    except FileNotFoundError:
        return ''
    except Exception as e:
        return f'Error reading log: {e}'


def read_summary(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return 'No summary available yet.'
    except Exception as e:
        return f'Error reading summary: {e}'


class CthuluGUI:
    def __init__(self, root):
        self.root = root
        root.title('Cthulu — Monitor')
        root.geometry('1000x760')
        root.configure(bg=THEME_BG)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        # Fonts
        UI_FONT = ('Segoe UI', 11)
        HEADER_FONT = ('Segoe UI Semibold', 13)
        METRIC_FONT = ('Consolas', 11, 'bold')
        TREE_FONT = ('Segoe UI', 10)
        
        # Configure all ttk widgets for dark mode
        # Frame styling (critical for dark mode)
        style.configure('TFrame', background=THEME_BG)
        
        # Label styles
        style.configure('TLabel', background=THEME_BG, foreground=THEME_FG, font=UI_FONT)
        style.configure('Header.TLabel', font=HEADER_FONT, foreground=ACCENT, background=THEME_BG)
        style.configure('Metric.TLabel', font=METRIC_FONT, foreground=THEME_FG, background=THEME_BG)
        
        # Entry styling
        style.configure('TEntry', fieldbackground='#0b1220', foreground=THEME_FG, insertcolor=THEME_FG)
        style.map('TEntry', 
                  fieldbackground=[('readonly', '#07121a'), ('disabled', '#07121a')],
                  foreground=[('readonly', '#808080'), ('disabled', '#606060')])
        
        # Combobox styling
        style.configure('TCombobox', fieldbackground='#0b1220', foreground=THEME_FG, 
                       background='#0b1220', selectbackground='#1f2937', selectforeground=THEME_FG)
        style.map('TCombobox',
                  fieldbackground=[('readonly', '#0b1220'), ('disabled', '#07121a')],
                  selectbackground=[('readonly', '#1f2937')],
                  selectforeground=[('readonly', THEME_FG)])
        
        # Button styling
        style.configure('TButton', background='#1f2937', foreground=THEME_FG, borderwidth=1, 
                       focuscolor='none', relief='flat')
        style.configure('Accent.TButton', background=ACCENT, foreground='#ffffff', borderwidth=1,
                       focuscolor='none', relief='flat')
        style.map('TButton',
                  background=[('active', '#374151'), ('pressed', '#111827')],
                  foreground=[('active', THEME_FG), ('pressed', THEME_FG)])
        style.map('Accent.TButton',
                  background=[('active', '#7c3aed'), ('pressed', '#6d28d9')],
                  foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
        
        # Treeview styling
        style.configure('Treeview', background='#07121a', fieldbackground='#07121a', 
                   foreground=THEME_FG, rowheight=28, borderwidth=0, font=TREE_FONT)
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'), 
                   foreground=THEME_FG, background='#0b1220', borderwidth=1, relief='flat')
        style.map('Treeview', 
                  background=[('selected', '#1f2937')], 
                  foreground=[('selected', THEME_FG)])
        style.map('Treeview.Heading',
                  background=[('active', '#1f2937')],
                  foreground=[('active', ACCENT)])

        # Top: Metrics grid (no scroll)
        metrics_frame = ttk.Frame(root)
        metrics_frame.pack(fill='x', padx=15, pady=(12, 8))

        ttk.Label(metrics_frame, text='Performance Summary', style='Header.TLabel').grid(
            row=0, column=0, columnspan=8, sticky='w', pady=(0, 10)
        )
        self.metrics_labels = {}
        metric_keys = ['Total Trades', 'Win Rate', 'Net Profit', 'Profit Factor', 'Max Drawdown', 'Active Positions', 'Sharpe Ratio', 'Expectancy']
        for i, key in enumerate(metric_keys):
            r = 1 + (i // 4)
            c = (i % 4) * 2
            k_lbl = ttk.Label(metrics_frame, text=f"{key}:", style='Metric.TLabel')
            v_lbl = ttk.Label(metrics_frame, text='—', style='Metric.TLabel')
            k_lbl.grid(row=r*2-1, column=c, sticky='e', padx=(8, 4), pady=3)
            v_lbl.grid(row=r*2-1, column=c+1, sticky='w', padx=(0, 16), pady=3)
            self.metrics_labels[key] = v_lbl

        # Strategy Info Section
        strategy_frame = ttk.Frame(root)
        strategy_frame.pack(fill='x', padx=15, pady=(8, 8))
        
        ttk.Label(strategy_frame, text='Active Strategy', style='Header.TLabel').grid(
            row=0, column=0, sticky='w', pady=(0, 6)
        )
        self.strategy_label = ttk.Label(strategy_frame, text='—', style='Metric.TLabel')
        self.strategy_label.grid(row=1, column=0, sticky='w', padx=8)
        
        ttk.Label(strategy_frame, text='Market Regime', style='Header.TLabel').grid(
            row=0, column=1, sticky='w', pady=(0, 6), padx=(30, 0)
        )
        self.regime_label = ttk.Label(strategy_frame, text='—', style='Metric.TLabel')
        self.regime_label.grid(row=1, column=1, sticky='w', padx=8)

        # Middle: Trades and history
        middle_frame = ttk.Frame(root)
        middle_frame.pack(fill='both', expand=True, padx=15, pady=(8, 8))

        # Live trades panel
        left = ttk.Frame(middle_frame)
        left.pack(side='left', fill='both', expand=True, padx=(0, 8))
        ttk.Label(left, text='Live Trades', style='Header.TLabel').pack(anchor='w', pady=(0, 6))
        self.trades_tree = ttk.Treeview(left, columns=('ticket','symbol','side','volume','price','pnl'), show='headings', height=10)
        # Define clearer column widths for alignment
        trades_cols = [('ticket', 120), ('symbol', 90), ('side', 70), ('volume', 80), ('price', 110), ('pnl', 110)]
        for col, width in trades_cols:
            self.trades_tree.heading(col, text=col.capitalize())
            self.trades_tree.column(col, width=width, anchor='center')
        # alternating row tags for better readability
        try:
            self.trades_tree.tag_configure('odd', background='#0f1720')
            self.trades_tree.tag_configure('even', background='#1a2332')
        except Exception:
            pass
        self.trades_tree.pack(fill='both', expand=True, pady=(0, 4))

        # Trade history panel
        right = ttk.Frame(middle_frame)
        right.pack(side='left', fill='both', expand=True, padx=(8, 0))
        ttk.Label(right, text='Trade History', style='Header.TLabel').pack(anchor='w', pady=(0, 6))
        self.history_tree = ttk.Treeview(right, columns=('time','symbol','side','volume','entry','exit','pnl','status'), show='headings', height=10)
        history_cols = [('time', 140), ('symbol', 90), ('side', 60), ('volume', 75), ('entry', 105), ('exit', 105), ('pnl', 90), ('status', 100)]
        for col, width in history_cols:
            self.history_tree.heading(col, text=col.capitalize())
            self.history_tree.column(col, width=width, anchor='center')
        try:
            self.history_tree.tag_configure('odd', background='#0f1720')
            self.history_tree.tag_configure('even', background='#1a2332')
        except Exception:
            pass
        self.history_tree.pack(fill='both', expand=True, pady=(0, 4))

        # Bottom: Manual trade panel
        bottom = ttk.Frame(root)
        bottom.pack(fill='x', padx=15, pady=(8, 12))
        ttk.Label(bottom, text='Manual Trade', style='Header.TLabel').grid(
            row=0, column=0, columnspan=6, sticky='w', pady=(0, 8)
        )

        ttk.Label(bottom, text='Symbol:', style='TLabel').grid(row=1, column=0, sticky='e', padx=(8, 4), pady=4)
        self.symbol_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.symbol_var, width=12).grid(row=1, column=1, sticky='w', padx=(0, 12), pady=4)

        ttk.Label(bottom, text='Side:', style='TLabel').grid(row=1, column=2, sticky='e', padx=(8, 4), pady=4)
        self.side_var = tk.StringVar(value='BUY')
        ttk.Combobox(bottom, textvariable=self.side_var, values=['BUY','SELL'], width=7).grid(row=1, column=3, sticky='w', padx=(0, 12), pady=4)

        ttk.Label(bottom, text='Volume:', style='TLabel').grid(row=1, column=4, sticky='e', padx=(8, 4), pady=4)
        self.volume_var = tk.StringVar(value='0.01')
        ttk.Entry(bottom, textvariable=self.volume_var, width=8).grid(row=1, column=5, sticky='w', padx=(0, 12), pady=4)

        ttk.Label(bottom, text='SL:', style='TLabel').grid(row=2, column=0, sticky='e', padx=(8, 4), pady=4)
        self.sl_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.sl_var, width=12).grid(row=2, column=1, sticky='w', padx=(0, 12), pady=4)

        ttk.Label(bottom, text='TP:', style='TLabel').grid(row=2, column=2, sticky='e', padx=(8, 4), pady=4)
        self.tp_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.tp_var, width=12).grid(row=2, column=3, sticky='w', padx=(0, 12), pady=4)

        self.place_btn = ttk.Button(bottom, text='Place Trade', style='Accent.TButton', command=self.place_manual_trade)
        self.place_btn.grid(row=2, column=5, sticky='e', padx=(8, 4), pady=4)

        # Live log viewer (shows last N lines of Cthulu.log)
        log_frame = ttk.Frame(root)
        # Allow log area to expand and be resizable
        log_frame.pack(fill='both', expand=True, padx=15, pady=(8, 12))
        ttk.Label(log_frame, text='Live Log', style='Header.TLabel').pack(anchor='w', pady=(0, 6))
        # Use ScrolledText but also add horizontal scrollbar for long log lines
        self.log_text = ScrolledText(log_frame, height=12, bg='#07121a', fg=THEME_FG, insertbackground=THEME_FG, wrap='none')
        try:
            # Use monospace for logs
            self.log_text.configure(font=('Consolas', 10))
        except Exception:
            pass
        # Horizontal scrollbar
        xscroll = tk.Scrollbar(log_frame, orient='horizontal', command=self.log_text.xview)
        self.log_text.configure(xscrollcommand=xscroll.set)
        self.log_text.pack(fill='both', expand=True, pady=(0, 4))
        xscroll.pack(fill='x')

        # Close behavior
        root.protocol('WM_DELETE_WINDOW', self.on_close)

        # Internal live state
        self._trades = {}

        # Database connection for trade history
        try:
            self.db = Database("Cthulu.db")
        except Exception as e:
            print(f"Warning: Could not connect to database: {e}")
            self.db = None

        # Start periodic update
        self.update()

    def update(self):
        # Update metrics from summary file (parse key lines)
        summary = read_summary(SUMMARY_PATH)
        lines = [l.strip() for l in summary.splitlines() if l.strip()]
        metrics_map = {}
        for l in lines:
            if ':' in l:
                k, v = l.split(':', 1)
                metrics_map[k.strip()] = v.strip()

        # Map keys to labels
        def set_metric(key, fallback='—'):
            val = metrics_map.get(key, fallback)
            if key in self.metrics_labels:
                self.metrics_labels[key].configure(text=val)

        set_metric('Total Trades')
        set_metric('Win Rate')
        set_metric('Net Profit')
        set_metric('Profit Factor')
        set_metric('Max Drawdown')
        set_metric('Active Positions')
        set_metric('Sharpe Ratio')
        set_metric('Expectancy')

        # Update strategy info
        try:
            strategy_info = read_summary(STRATEGY_INFO_PATH)
            lines = [l.strip() for l in strategy_info.splitlines() if l.strip()]
            for l in lines:
                if l.startswith('Current Strategy:'):
                    self.strategy_label.configure(text=l.split(':', 1)[1].strip())
                elif l.startswith('Current Regime:'):
                    regime = l.split(':', 1)[1].strip()
                    # Color code regime
                    if 'trending_up' in regime.lower():
                        color = '#4ade80'  # Green
                    elif 'trending_down' in regime.lower():
                        color = '#f87171'  # Red
                    elif 'volatile' in regime.lower():
                        color = '#fbbf24'  # Yellow
                    elif 'ranging' in regime.lower():
                        color = '#60a5fa'  # Blue
                    else:
                        color = THEME_FG
                    self.regime_label.configure(text=regime, foreground=color)
        except Exception:
            pass

        # Update trades by scanning recent log for order fills and position events
        log_text = tail_file(LOG_PATH, TAIL_LINES)
        self._update_trades_from_log(log_text)

        # Update history by scanning for finalised trades
        # Reopen DB briefly to pick up external writes (some processes write to DB)
        if self.db:
            try:
                try:
                    self.db.close()
                except Exception:
                    pass
                self.db = Database("Cthulu.db")
            except Exception:
                # fall back to existing self.db
                pass
        self._update_history_from_log(log_text)

        # Update live log view in the GUI
        try:
            self.log_text.configure(state='normal')
            self.log_text.delete('1.0', tk.END)
            self.log_text.insert(tk.END, log_text)
            self.log_text.see(tk.END)
            self.log_text.configure(state='disabled')
        except Exception:
            pass

        # Schedule next update
        self.root.after(REFRESH_INTERVAL, self.update)

    def _update_trades_from_log(self, log_text: str):
        # Look for 'Order filled' and 'Reconciled' lines to track open trades
        lines = log_text.splitlines()
        seen = {}
        for l in lines:
            if 'Order filled:' in l or 'Order executed' in l:
                # Try to extract ticket and price
                m = re.search(r'Ticket #?(\d+).*Price: ([0-9\.]+)', l) or re.search(r'ticket=(\d+), price=([0-9\.]+)', l)
                if m:
                    ticket = m.group(1)
                    price = m.group(2)
                    seen[ticket] = {'ticket': ticket, 'symbol': '', 'side': '', 'volume': '', 'price': price, 'pnl': ''}
            if 'Position #' in l and 'closed' not in l.lower():
                # e.g., Position #499011910 added to registry
                m = re.search(r'Position #?(\d+)', l)
                if m:
                    tid = m.group(1)
                    seen.setdefault(tid, {'ticket': tid, 'symbol': '', 'side': '', 'volume': '', 'price': '', 'pnl': ''})

        # Refresh tree with alternating rows
        for i in self.trades_tree.get_children():
            self.trades_tree.delete(i)
        for idx, (t, data) in enumerate(sorted(seen.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)):
            tag = 'even' if idx % 2 == 0 else 'odd'
            pnl = data.get('pnl') if data.get('pnl') not in (None, '') else '—'
            self.trades_tree.insert('', 'end', values=(data['ticket'], data['symbol'], data['side'], data['volume'], data['price'], pnl), tags=(tag,))

    def _update_history_from_log(self, log_text: str):
        # Get trade history from database
        if self.db:
            try:
                trades = self.db.get_all_trades(limit=50)
                for i in self.history_tree.get_children():
                    self.history_tree.delete(i)
                for idx, trade in enumerate(trades):
                    tag = 'even' if idx % 2 == 0 else 'odd'
                    # Format trade data - handle both datetime and string
                    if trade.entry_time:
                        entry_time = trade.entry_time.strftime('%Y-%m-%d %H:%M') if hasattr(trade.entry_time, 'strftime') else str(trade.entry_time)[:16]
                    else:
                        entry_time = '—'
                    if trade.exit_time:
                        exit_time = trade.exit_time.strftime('%Y-%m-%d %H:%M') if hasattr(trade.exit_time, 'strftime') else str(trade.exit_time)[:16]
                    else:
                        exit_time = '—'
                    pnl = f"{trade.profit:.2f}" if trade.profit is not None else '—'
                    status = trade.status
                    result = f"{trade.side} {trade.volume}@{trade.entry_price:.5f} → {pnl} ({status})"
                    if trade.exit_price:
                        result += f" exit@{trade.exit_price:.5f}"
                    
                    self.history_tree.insert('', 'end', values=(
                        entry_time, 
                        trade.symbol, 
                        trade.side, 
                        f"{trade.volume:.2f}", 
                        f"{trade.entry_price:.5f}", 
                        f"{trade.exit_price:.5f}" if trade.exit_price else '—', 
                        f"{trade.profit:.2f}" if trade.profit is not None else '—',
                        trade.status
                    ), tags=(tag,))
                return
            except Exception as e:
                print(f"Database error: {e}")
        
        # Fallback to log parsing if database unavailable
        lines = log_text.splitlines()
        history = []
        for l in lines:
            if 'Final performance metrics' in l or 'Order filled:' in l:
                history.append(l.strip())

        # Keep last 50 history items
        history = history[-50:]
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)
        for idx, h in enumerate(history):
            tag = 'even' if idx % 2 == 0 else 'odd'
            # Provide values for all history columns to avoid ValueError
            time_str = (h[:19] if len(h) >= 19 else h)
            symbol = ''
            side = ''
            volume = ''
            entry = (h if len(h) <= 110 else h[:107] + '...')
            exit_price = '—'
            pnl = '—'
            status = 'log'
            self.history_tree.insert('', 'end', values=(time_str, symbol, side, volume, entry, exit_price, pnl, status), tags=(tag,))

    def on_close(self):
        try:
            if self.db:
                self.db.close()
            self.root.destroy()
        finally:
            # Exit cleanly with 0 so Cthulu treats this as user-closed GUI
            sys.exit(0)

    def place_manual_trade(self):
        # Build order payload
        symbol = self.symbol_var.get().strip()
        side = self.side_var.get().strip().upper()
        volume = self.volume_var.get().strip()
        sl = self.sl_var.get().strip() or None
        tp = self.tp_var.get().strip() or None

        if not symbol or not volume:
            self._show_status('Symbol and volume required')
            return

        payload = {
            'symbol': symbol,
            'side': side,
            'volume': float(volume),
            'sl': float(sl) if sl else None,
            'tp': float(tp) if tp else None,
            'order_type': 'market'
        }

        success = False
        last_err = None
        for ep in RPC_ENDPOINTS:
            try:
                r = requests.post(ep, json=payload, timeout=3)
                if r.status_code in (200,201):
                    self._show_status('Order placed (via RPC)')
                    success = True
                    break
                else:
                    last_err = f'Endpoint {ep} returned {r.status_code}: {r.text}'
            except Exception as e:
                last_err = str(e)

        if not success:
            self._show_status(f'Failed to place order: {last_err}')

    def _show_status(self, msg: str):
        # temporary status (could be improved)
        status = tk.Toplevel(self.root)
        status.title('Status')
        ttk.Label(status, text=msg).pack(padx=10, pady=10)
        self.root.after(3000, status.destroy)


def main():
    # Prevent multiple instances using a lock file
    lock_file = Path(__file__).parent.parent / 'logs' / '.gui_lock'
    debug_file = Path(__file__).parent.parent / 'logs' / 'gui_debug.log'
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Helper to write debug events
    def dbg(msg: str):
        try:
            with open(debug_file, 'a', encoding='utf-8') as fh:
                fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
        except Exception:
            pass

    dbg(f"GUI main() start (pid={os.getpid()})")

    # Check if another instance is running
    if lock_file.exists():
        try:
            # Check if the PID in lock file is still running
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Try to check if process exists
            if sys.platform == 'win32':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_INFORMATION = 0x0400
                handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, 0, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    print(f"Cthulu GUI is already running (PID: {pid})")
                    sys.exit(0)
            else:
                # Unix-like systems
                try:
                    os.kill(pid, 0)
                    print(f"Cthulu GUI is already running (PID: {pid})")
                    sys.exit(0)
                except OSError:
                    # Process doesn't exist, remove stale lock
                    lock_file.unlink()
        except Exception:
            # If we can't read/check the lock, remove it and continue
            try:
                lock_file.unlink()
            except Exception:
                pass
    
    # Write our PID to lock file
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass
    
    # Ensure lock is removed on exit
    def cleanup_lock(exit_msg: str = None):
        try:
            if exit_msg:
                dbg(f"cleanup_lock: {exit_msg}")
            lock_file.unlink()
        except Exception as e:
            dbg(f"cleanup_lock exception: {e}")
    
    import atexit
    atexit.register(cleanup_lock)
    
    # Install a global exception hook to log unexpected errors
    def gui_excepthook(exc_type, exc, tb):
        try:
            import traceback
            dbg("Unhandled exception in GUI: " + ''.join(traceback.format_exception(exc_type, exc, tb)))
        except Exception:
            pass
        # Fall back to default handler
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = gui_excepthook

    root = tk.Tk()
    app = CthuluGUI(root)
    try:
        dbg("Entering mainloop")
        root.mainloop()
    except KeyboardInterrupt:
        try:
            root.destroy()
        except Exception:
            pass
    finally:
        dbg("Exiting main()")
        cleanup_lock('normal exit')


if __name__ == '__main__':
    main()




