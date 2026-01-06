import { Injectable } from '@angular/core';

// --- Framework Enums ---
export enum SpeedMode {
  FAST = 'FAST',
  NORMAL = 'NORMAL',
  SLOW = 'SLOW',
  REALTIME = 'REALTIME',
  HFT_TEST = 'HFT_TEST'
}

export enum WeightingMethod {
  EQUAL = 'EQUAL',
  PERFORMANCE = 'PERFORMANCE',
  SHARPE = 'SHARPE',
  ADAPTIVE = 'ADAPTIVE'
}

export enum SelectionMethod {
  SOFTMAX = 'SOFTMAX',
  ARGMAX = 'ARGMAX'
}

export enum DataSource {
  MT5 = 'MT5',
  CSV = 'CSV'
}

// --- Interfaces ---

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Trade {
  entryTime: number;
  exitTime: number;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  type: 'long' | 'short';
}

export interface BacktestResult {
  metrics: {
    initialCapital: number;
    finalCapital: number;
    totalTrades: number;
    winRate: number;
    sharpeRatio: number;
    maxDrawdown: number;
    profitFactor: number;
    // Ensemble Stats (Mocked for frontend)
    ensembleStats?: Record<string, any>;
  };
  equityCurve: { time: number; value: number }[];
  trades: Trade[];
  candles: Candle[];
}

export interface OptimizationResult {
  bestFastMa: number;
  bestSlowMa: number;
  bestProfitFactor: number;
  bestResult: BacktestResult;
  iterations: number;
}

@Injectable({
  providedIn: 'root',
})
export class SimulationService {
  
  // Parse CSV Data (Date,Open,High,Low,Close,Volume)
  parseCsvData(csvText: string): Candle[] {
    // robust split for various line endings
    const lines = csvText.trim().split(/\r?\n/);
    const candles: Candle[] = [];
    
    // Detect header (check if first char of first line is a number)
    // If it starts with a letter (e.g., 'D' for Date), assume header
    const firstLine = lines[0];
    const hasHeader = /^[a-zA-Z]/.test(firstLine);
    const startIdx = hasHeader ? 1 : 0;

    for (let i = startIdx; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      const parts = line.split(',');
      if (parts.length < 5) continue;

      const timeStr = parts[0];
      const time = new Date(timeStr).getTime();
      const open = parseFloat(parts[1]);
      const high = parseFloat(parts[2]);
      const low = parseFloat(parts[3]);
      const close = parseFloat(parts[4]);
      const volume = parseFloat(parts[5] || '0');

      if (!isNaN(time) && !isNaN(close)) {
        candles.push({ time, open, high, low, close, volume });
      }
    }
    return candles.sort((a, b) => a.time - b.time);
  }

  // Generates random walk market data (Fallback)
  generateData(days: number = 365): Candle[] {
    const candles: Candle[] = [];
    let price = 100;
    const now = new Date();
    
    for (let i = 0; i < days; i++) {
      const time = new Date(now.getTime() - (days - i) * 24 * 60 * 60 * 1000).getTime();
      const volatility = 0.02; // 2% daily volatility
      const change = 1 + (Math.random() * volatility * 2 - volatility);
      
      const open = price;
      const close = price * change;
      const high = Math.max(open, close) * (1 + Math.random() * 0.01);
      const low = Math.min(open, close) * (1 - Math.random() * 0.01);
      const volume = Math.floor(Math.random() * 1000000) + 500000;
      
      candles.push({ time, open, high, low, close, volume });
      price = close;
    }
    return candles;
  }

  // Runs strategy on provided candles (Local Simulation Implementation)
  runBacktest(candles: Candle[], initialCapital: number, commission: number, slippage: number, fastMa: number, slowMa: number): BacktestResult {
    // FALLBACK: If no candles, use mock data
    const dataToUse = (candles && candles.length > 0) ? candles : this.generateData(365);

    let cash = initialCapital;
    let position = 0; // 0 = flat, 1 = long
    let entryPrice = 0;
    let entryTime = 0;
    const trades: Trade[] = [];
    const equityCurve: { time: number; value: number }[] = [];
    let maxEquity = initialCapital;
    let maxDrawdown = 0;

    // Simple MA calculation helper
    const getMa = (idx: number, period: number) => {
      if (idx < period) return 0;
      let sum = 0;
      for (let k = 0; k < period; k++) {
        sum += dataToUse[idx - k].close;
      }
      return sum / period;
    };

    for (let i = 0; i < dataToUse.length; i++) {
      const candle = dataToUse[i];
      // Mark to Market Equity
      const currentEquity = cash + (position > 0 ? (candle.close - entryPrice) * (initialCapital / entryPrice) : 0);
      
      equityCurve.push({ time: candle.time, value: currentEquity });
      
      // Drawdown calc
      if (currentEquity > maxEquity) maxEquity = currentEquity;
      const dd = maxEquity > 0 ? (maxEquity - currentEquity) / maxEquity : 0;
      if (dd > maxDrawdown) maxDrawdown = dd;

      if (i < slowMa) continue;

      const fastVal = getMa(i, fastMa);
      const slowVal = getMa(i, slowMa);
      const prevFast = getMa(i - 1, fastMa);
      const prevSlow = getMa(i - 1, slowMa);

      // Crossover Logic
      if (prevFast <= prevSlow && fastVal > slowVal && position === 0) {
        // Buy Signal
        position = 1;
        // Apply slippage to entry
        entryPrice = candle.close * (1 + slippage);
        entryTime = candle.time;
        // Pay commission
        cash -= initialCapital * commission; 
      } else if (prevFast >= prevSlow && fastVal < slowVal && position === 1) {
        // Sell Signal
        const exitPrice = candle.close * (1 - slippage);
        const pnlPct = (exitPrice - entryPrice) / entryPrice;
        const pnl = (initialCapital * pnlPct) - (initialCapital * commission); // Simple fixed sizing model
        
        cash += pnl;
        
        trades.push({
          entryTime,
          exitTime: candle.time,
          entryPrice,
          exitPrice,
          pnl,
          type: 'long'
        });
        
        position = 0;
      }
    }

    // Calculate Metrics
    const winningTrades = trades.filter(t => t.pnl > 0);
    const totalTrades = trades.length;
    const winRate = totalTrades > 0 ? winningTrades.length / totalTrades : 0;
    
    // Sharpe Ratio (Simplified annual)
    const returns = equityCurve.map((e, i) => i === 0 ? 0 : (e.value - equityCurve[i-1].value) / equityCurve[i-1].value);
    const avgReturn = returns.length > 0 ? returns.reduce((a, b) => a + b, 0) / returns.length : 0;
    const stdDev = returns.length > 0 ? Math.sqrt(returns.map(x => Math.pow(x - avgReturn, 2)).reduce((a, b) => a + b, 0) / returns.length) : 0;
    const sharpeRatio = stdDev === 0 ? 0 : (avgReturn / stdDev) * Math.sqrt(252);

    const grossProfit = trades.filter(t => t.pnl > 0).reduce((acc, t) => acc + t.pnl, 0);
    const grossLoss = Math.abs(trades.filter(t => t.pnl < 0).reduce((acc, t) => acc + t.pnl, 0));
    const profitFactor = grossLoss === 0 ? grossProfit : grossProfit / grossLoss;

    return {
      metrics: {
        initialCapital,
        finalCapital: equityCurve.length > 0 ? equityCurve[equityCurve.length - 1].value : initialCapital,
        totalTrades,
        winRate,
        sharpeRatio,
        maxDrawdown,
        profitFactor
      },
      equityCurve,
      trades,
      candles: dataToUse
    };
  }

  // Optimization Loop with Safety Limit
  optimizeStrategy(
    candles: Candle[],
    initialCapital: number,
    commission: number,
    slippage: number,
    fastStart: number, fastEnd: number, fastStep: number,
    slowStart: number, slowEnd: number, slowStep: number
  ): OptimizationResult {
    const dataToUse = (candles && candles.length > 0) ? candles : this.generateData(365);

    let bestProfitFactor = -Infinity;
    let bestFastMa = fastStart;
    let bestSlowMa = slowStart;
    let bestResult: BacktestResult | null = null;
    let iterations = 0;
    const MAX_ITERATIONS = 5000; // Prevent browser freeze

    for (let f = fastStart; f <= fastEnd; f += fastStep) {
      for (let s = slowStart; s <= slowEnd; s += slowStep) {
        if (f >= s) continue; // Fast MA must be smaller than Slow MA
        
        iterations++;
        // Safety break
        if (iterations > MAX_ITERATIONS) {
            console.warn(`Optimization capped at ${MAX_ITERATIONS} iterations.`);
            if (!bestResult) bestResult = this.runBacktest(dataToUse, initialCapital, commission, slippage, fastStart, slowStart);
            return {
                bestFastMa, bestSlowMa, bestProfitFactor, bestResult, iterations
            };
        }

        const result = this.runBacktest(dataToUse, initialCapital, commission, slippage, f, s);
        
        // Optimize for Profit Factor
        if (result.metrics.profitFactor > bestProfitFactor) {
          bestProfitFactor = result.metrics.profitFactor;
          bestFastMa = f;
          bestSlowMa = s;
          bestResult = result;
        }
      }
    }

    if (!bestResult) {
      // Fallback if no valid combo found
      bestResult = this.runBacktest(dataToUse, initialCapital, commission, slippage, fastStart, slowStart);
    }

    return {
      bestFastMa,
      bestSlowMa,
      bestProfitFactor,
      bestResult,
      iterations
    };
  }
}