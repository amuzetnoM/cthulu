import sys
import time
import threading
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
except Exception:
    print("Tkinter not available; GUI cannot start.")
    sys.exit(2)

LOG_PATH = Path(__file__).parents[1] / 'herald.log'
SUMMARY_PATH = Path(__file__).parents[1] / 'logs' / 'latest_summary.txt'

REFRESH_INTERVAL = 2000  # ms
TAIL_LINES = 200

RPC_ENDPOINTS = [
    'http://127.0.0.1:8181/order',
    'http://127.0.0.1:8181/rpc/order',
    'http://127.0.0.1:8181/place_order',
]

THEME_BG = '#0f1720'
THEME_FG = '#e6eef6'
ACCENT = '#8b5cf6'  # Herald thematic purple


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


class HeraldGUI:
    def __init__(self, root):
        self.root = root
        root.title('Herald — Monitor')
        root.geometry('1000x760')
        root.configure(bg=THEME_BG)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TLabel', background=THEME_BG, foreground=THEME_FG)
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'), foreground=ACCENT)
        style.configure('Metric.TLabel', font=('Consolas', 11), foreground=THEME_FG, background=THEME_BG)
        style.configure('Treeview', background='#0b1220', fieldbackground='#0b1220', foreground=THEME_FG)

        # Top: Metrics grid (no scroll)
        metrics_frame = ttk.Frame(root)
        metrics_frame.pack(fill='x', padx=10, pady=(10, 6))

        ttk.Label(metrics_frame, text='Performance Summary', style='Header.TLabel').grid(row=0, column=0, sticky='w', pady=(0,6))
        self.metrics_labels = {}
        metric_keys = ['Total Trades', 'Win Rate', 'Net Profit', 'Profit Factor', 'Max Drawdown', 'Active Positions', 'Sharpe Ratio', 'Expectancy']
        for i, key in enumerate(metric_keys):
            r = 1 + (i // 4)
            c = i % 4
            k_lbl = ttk.Label(metrics_frame, text=f"{key}:", style='Metric.TLabel')
            v_lbl = ttk.Label(metrics_frame, text='—', style='Metric.TLabel')
            k_lbl.grid(row=r*2-1, column=c*2, sticky='w', padx=6, pady=2)
            v_lbl.grid(row=r*2, column=c*2, sticky='w', padx=6, pady=2)
            self.metrics_labels[key] = v_lbl

        # Middle: Trades and history
        middle_frame = ttk.Frame(root)
        middle_frame.pack(fill='both', expand=True, padx=10, pady=6)

        # Live trades panel
        left = ttk.Frame(middle_frame)
        left.pack(side='left', fill='both', expand=True, padx=(0,6))
        ttk.Label(left, text='Live Trades', style='Header.TLabel').pack(anchor='w')
        self.trades_tree = ttk.Treeview(left, columns=('ticket','symbol','side','volume','price','pnl'), show='headings', height=10)
        for col in ('ticket','symbol','side','volume','price','pnl'):
            self.trades_tree.heading(col, text=col.capitalize())
            self.trades_tree.column(col, width=100, anchor='center')
        self.trades_tree.pack(fill='both', expand=True, pady=4)

        # Trade history panel
        right = ttk.Frame(middle_frame)
        right.pack(side='left', fill='both', expand=True, padx=(6,0))
        ttk.Label(right, text='Trade History', style='Header.TLabel').pack(anchor='w')
        self.history_tree = ttk.Treeview(right, columns=('time','symbol','side','price','result'), show='headings', height=10)
        for col in ('time','symbol','side','price','result'):
            self.history_tree.heading(col, text=col.capitalize())
            self.history_tree.column(col, width=120, anchor='center')
        self.history_tree.pack(fill='both', expand=True, pady=4)

        # Bottom: Manual trade panel
        bottom = ttk.Frame(root)
        bottom.pack(fill='x', padx=10, pady=(6,10))
        ttk.Label(bottom, text='Manual Trade', style='Header.TLabel').grid(row=0, column=0, columnspan=6, sticky='w')

        ttk.Label(bottom, text='Symbol:', style='TLabel').grid(row=1, column=0, sticky='e')
        self.symbol_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.symbol_var, width=12).grid(row=1, column=1, sticky='w')

        ttk.Label(bottom, text='Side:', style='TLabel').grid(row=1, column=2, sticky='e')
        self.side_var = tk.StringVar(value='BUY')
        ttk.Combobox(bottom, textvariable=self.side_var, values=['BUY','SELL'], width=6).grid(row=1, column=3, sticky='w')

        ttk.Label(bottom, text='Volume:', style='TLabel').grid(row=1, column=4, sticky='e')
        self.volume_var = tk.StringVar(value='0.01')
        ttk.Entry(bottom, textvariable=self.volume_var, width=8).grid(row=1, column=5, sticky='w')

        ttk.Label(bottom, text='SL:', style='TLabel').grid(row=2, column=0, sticky='e')
        self.sl_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.sl_var, width=12).grid(row=2, column=1, sticky='w')

        ttk.Label(bottom, text='TP:', style='TLabel').grid(row=2, column=2, sticky='e')
        self.tp_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.tp_var, width=12).grid(row=2, column=3, sticky='w')

        self.place_btn = ttk.Button(bottom, text='Place Trade', command=self.place_manual_trade)
        self.place_btn.grid(row=2, column=5, sticky='e')

        # Close behavior
        root.protocol('WM_DELETE_WINDOW', self.on_close)

        # Internal live state
        self._trades = {}

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

        # Update trades by scanning recent log for order fills and position events
        log_text = tail_file(LOG_PATH, TAIL_LINES)
        self._update_trades_from_log(log_text)

        # Update history by scanning for finalised trades
        self._update_history_from_log(log_text)

        # Schedule next update
        self.root.after(REFRESH_INTERVAL, self.update)

    def _update_trades_from_log(self, log_text: str):
        # Look for 'Order filled' and 'Reconciled' lines to track open trades
        lines = log_text.splitlines()
        seen = {}
        for l in lines:
            if 'Order filled:' in l or 'Order executed' in l:
                # Try to extract ticket and price
                import re
                m = re.search(r'Ticket #?(\d+).*Price: ([0-9\.]+)', l) or re.search(r'ticket=(\d+), price=([0-9\.]+)', l)
                if m:
                    ticket = m.group(1)
                    price = m.group(2)
                    seen[ticket] = {'ticket': ticket, 'symbol': '', 'side': '', 'volume': '', 'price': price, 'pnl': ''}
            if 'Position #' in l and 'closed' not in l.lower():
                # e.g., Position #499011910 added to registry
                import re
                m = re.search(r'Position #?(\d+)', l)
                if m:
                    tid = m.group(1)
                    seen.setdefault(tid, {'ticket': tid, 'symbol': '', 'side': '', 'volume': '', 'price': '', 'pnl': ''})

        # Refresh tree
        for i in self.trades_tree.get_children():
            self.trades_tree.delete(i)
        for t, data in seen.items():
            self.trades_tree.insert('', 'end', values=(data['ticket'], data['symbol'], data['side'], data['volume'], data['price'], data['pnl']))

    def _update_history_from_log(self, log_text: str):
        lines = log_text.splitlines()
        history = []
        for l in lines:
            if 'Final performance metrics' in l or 'Order filled:' in l:
                history.append(l.strip())

        # Keep last 50 history items
        history = history[-50:]
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)
        for h in history:
            self.history_tree.insert('', 'end', values=(h[:19], '', '', '', h))

    def on_close(self):
        try:
            self.root.destroy()
        finally:
            # Exit cleanly with 0 so herald treats this as user-closed GUI
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

        import json, requests
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
        import tkinter as tk
        status = tk.Toplevel(self.root)
        status.title('Status')
        ttk.Label(status, text=msg).pack(padx=10, pady=10)
        self.root.after(3000, status.destroy)


def main():
    root = tk.Tk()
    app = HeraldGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        try:
            root.destroy()
        except Exception:
            pass


if __name__ == '__main__':
    main()
