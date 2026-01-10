import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { GoogleGenAI } from "@google/genai";
import { firstValueFrom } from 'rxjs';

export interface Trade {
  id: string;
  type: 'BUY' | 'SELL';
  price: number;
  size: number;
  timestamp: number;
  status: 'OPEN' | 'CLOSED';
  pnl?: number;
  origin: 'AUTO' | 'USER';
  reason?: string;
}

export interface LogEntry {
  timestamp: number;
  level: 'INFO' | 'WARN' | 'ERROR' | 'TRADE';
  message: string;
  source: 'SYSTEM' | 'CTHULU_AI';
  real_time_str?: string;
}

export interface SignalEntry {
  signal_id: string;
  symbol: string;
  action: string;
  confidence: number;
  timestamp: string; // ISO DB string
  price: number;
  reason: string;
}

export interface OrderBookEntry {
  price: number;
  size: number;
  total: number;
}

export interface OrderBook {
  asks: OrderBookEntry[];
  bids: OrderBookEntry[];
  spread: number;
  spreadPct: number;
}

@Injectable({
  providedIn: 'root'
})
export class HeraldService {
  private http = inject(HttpClient);
  private API_URL = 'http://localhost:5000/api';

  // State Signals
  readonly price = signal<number>(0); // 0 indicates unknown
  readonly priceHistory = signal<{ time: number, value: number }[]>([]);
  readonly trades = signal<Trade[]>([]);
  readonly logs = signal<LogEntry[]>([]);
  readonly signals = signal<SignalEntry[]>([]);
  readonly orderBook = signal<OrderBook>({ asks: [], bids: [], spread: 0, spreadPct: 0 });

  // System Status
  readonly isRunning = signal<boolean>(true);
  readonly isConnected = signal<boolean>(false);
  readonly lastHeartbeat = signal<number>(0);

  // Indicators
  readonly currentRSI = signal<number>(0);

  // Metrics
  readonly pnl = computed(() => this.trades().reduce((acc, t) => acc + (t.pnl || 0), 0));
  readonly openPositions = computed(() => this.trades().filter(t => t.status === 'OPEN').length);

  // Gemini Client
  private ai: GoogleGenAI;
  private timer: any;

  constructor() {
    this.ai = new GoogleGenAI({ apiKey: '' });
    this.initPolling();
  }

  private initPolling() {
    // Poll faster for status, slower for heavy data
    setInterval(() => this.checkStatus(), 2000);
    this.timer = setInterval(() => {
      if (!this.isConnected()) return;
      this.tick();
    }, 2000); // 2s data refresh

    // Initial Load
    this.fetchHistory();
  }

  private async checkStatus() {
    try {
      await firstValueFrom(this.http.get(`${this.API_URL}/status`));
      this.isConnected.set(true);
      this.lastHeartbeat.set(Date.now());
    } catch (e) {
      this.isConnected.set(false);
      const lastLog = this.logs()[0];
      if (!lastLog || lastLog.message !== 'Backend Offline - Waiting for Cthulu...') {
        this.localLog('ERROR', 'Backend Offline - Waiting for Cthulu...', 'SYSTEM');
      }
    }
  }

  private tick() {
    this.fetchTrades();
    this.fetchLogs();
    this.fetchSignals();
    this.fetchTicker(); // Live Price
  }

  private fetchTicker() {
    this.http.get<any>(`${this.API_URL}/ticker?symbol=BTC-USD`).subscribe({
      next: (data) => {
        if (data && data.price) {
          this.updatePrice(data.price);
        }
      }
    });
  }

  private fetchHistory() {
    // Get 1 day of minute data for initial chart
    this.http.get<any[]>(`${this.API_URL}/history?symbol=BTC-USD&period=1d&interval=1m`).subscribe({
      next: (data) => {
        if (data && data.length > 0) {
          // Transform for chart
          const history = data.map(d => ({ time: d.time, value: d.close }));
          this.priceHistory.set(history);
          // Calc initial indicators
          const closes = history.map(h => h.value);
          this.currentRSI.set(this.calculateRSI(closes));
        }
      }
    });
  }

  private fetchTrades() {
    this.http.get<Trade[]>(`${this.API_URL}/trades`).subscribe({
      next: (data) => { if (data) this.trades.set(data); },
      error: () => { }
    });
  }

  private fetchLogs() {
    this.http.get<LogEntry[]>(`${this.API_URL}/logs`).subscribe({
      next: (data) => { if (data && data.length > 0) this.logs.set(data); }
    });
  }

  private fetchSignals() {
    this.http.get<any[]>(`${this.API_URL}/signals`).subscribe({
      next: (data) => { if (data) this.signals.set(data); }
    });
  }

  private fetchMetrics() { }

  private updatePrice(newPrice: number) {
    if (newPrice === this.price()) return;

    this.price.set(newPrice);
    this.priceHistory.update(h => {
      const newHistory = [...h, { time: Date.now(), value: newPrice }];
      if (newHistory.length > 500) newHistory.shift(); // Keep more history
      return newHistory;
    });

    // Update RSI on every tick (simplified)
    const history = this.priceHistory().map(h => h.value);
    this.currentRSI.set(this.calculateRSI(history));
  }

  // --- Indicators ---

  private calculateRSI(prices: number[], period: number = 14): number {
    if (prices.length < period + 1) return 50;

    let gains = 0;
    let losses = 0;

    // Calculate initial RS
    for (let i = prices.length - period; i < prices.length; i++) {
      const diff = prices[i] - prices[i - 1];
      if (diff >= 0) gains += diff;
      else losses -= diff;
    }

    if (losses === 0) return 100;

    const avgGain = gains / period;
    const avgLoss = losses / period;
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
  }

  // --- Actions ---

  public placeManualTrade(type: 'BUY' | 'SELL', size: number) {
    if (!this.isConnected()) {
      this.localLog('ERROR', 'Cannot trade: System Offline', 'SYSTEM');
      return;
    }

    const payload = {
      symbol: "BTCUSD#", // Match config.json
      side: type,
      volume: size
    };

    this.localLog('INFO', `Sending ${type} order to Cthulu RPC...`, 'SYSTEM');
    this.http.post(`${this.API_URL}/trade`, payload).subscribe({
      next: (res: any) => {
        if (res.error) {
          this.localLog('ERROR', `Trade Failed: ${res.error}`, 'SYSTEM');
        } else {
          this.localLog('INFO', `Trade Accepted: #${res.order_id}`, 'SYSTEM');
        }
      },
      error: (err) => {
        this.localLog('ERROR', `RPC Error: ${err.message}`, 'SYSTEM');
      }
    });
  }

  public toggleSystem() {
    this.isRunning.update(v => !v);
  }

  public closeTrade(id: string) {
    this.localLog('WARN', 'Remote close not yet implemented.', 'SYSTEM');
  }

  private localLog(level: 'INFO' | 'WARN' | 'ERROR' | 'TRADE', message: string, source: 'SYSTEM' | 'CTHULU_AI') {
    this.logs.update(l => [{
      timestamp: Date.now(),
      level,
      message,
      source
    }, ...l].slice(0, 100));
  }
}