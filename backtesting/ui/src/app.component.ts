import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { provideHttpClient } from '@angular/common/http';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ConfigurationComponent, ConfigData } from './components/configuration.component';
import { ChartComponent } from './components/chart.component';
import { MetricsComponent } from './components/metrics.component';
import { SimulationService, BacktestResult, Candle, OptimizationResult } from './services/simulation.service';
import { AiService } from './services/ai.service';
import { BackendService } from './services/backend.service';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [CommonModule, HttpClientModule, ConfigurationComponent, ChartComponent, MetricsComponent],
    template: `
    <div class="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-emerald-500/30">
      <div class="w-full px-4 md:px-6 lg:px-8 py-6">
        <header class="mb-8 flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
              <i class="fa-solid fa-layer-group mr-2 text-emerald-500"></i>
              CTHULU BACKTESTER <span class="text-slate-600 text-lg font-mono">v5.1</span>
            </h1>
            <p class="text-slate-500 text-sm mt-1">High-Frequency Backtesting & Optimization Engine</p>
          </div>
          <div class="flex items-center space-x-4">
            <!-- Backend Connection Status -->
            <div class="flex items-center space-x-2 px-3 py-1.5 rounded-lg" 
                 [class]="backendService.connectionStatus() === 'connected' ? 'bg-emerald-900/30 border border-emerald-500/30' : 'bg-red-900/30 border border-red-500/30'">
              <i class="fa-solid fa-circle text-xs" 
                 [class]="backendService.connectionStatus() === 'connected' ? 'text-emerald-400 animate-pulse' : 'text-red-400'"></i>
              <span class="text-xs font-mono">
                {{backendService.connectionStatus() === 'connected' ? 'Backend Connected' : 'Local Mode'}}
              </span>
            </div>
            <!-- Mode Toggle -->
            <button (click)="toggleMode()" 
                    class="px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
                    [class]="useBackend() ? 'bg-cyan-900/30 border border-cyan-500/30 text-cyan-400' : 'bg-slate-800 border border-slate-700 text-slate-400'">
              <i class="fa-solid fa-server mr-1"></i>
              {{useBackend() ? 'Backend Mode' : 'Client Mode'}}
            </button>
          </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <!-- Sidebar / Config -->
          <div class="lg:col-span-3 space-y-6">
            <app-configuration 
               (run)="handleRun($event)" 
               (fileLoaded)="onFileLoaded($event)">
            </app-configuration>
            
            <!-- Optimization Results Panel -->
            @if (optResult(); as opt) {
              <div class="bg-slate-900 border border-purple-500/30 rounded-lg p-4 shadow-lg animate-fade-in">
                 <h3 class="text-purple-400 font-bold mb-3 flex items-center">
                   <i class="fa-solid fa-trophy mr-2"></i> Optimization Winner
                 </h3>
                 <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                      <span class="text-slate-400">Iterations</span>
                      <span class="font-mono text-white">{{opt.iterations}}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-slate-400">Best Fast MA</span>
                      <span class="font-mono text-emerald-400">{{opt.bestFastMa}}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-slate-400">Best Slow MA</span>
                      <span class="font-mono text-emerald-400">{{opt.bestSlowMa}}</span>
                    </div>
                    <div class="flex justify-between pt-2 border-t border-slate-700">
                      <span class="text-slate-400">Profit Factor</span>
                      <span class="font-mono text-purple-400 font-bold">{{opt.bestProfitFactor.toFixed(2)}}</span>
                    </div>
                 </div>
              </div>
            }
            
            <!-- Backend Job Status -->
            @if (isRunning()) {
              <div class="bg-slate-900 border border-cyan-500/30 rounded-lg p-4 shadow-lg animate-pulse">
                <h3 class="text-cyan-400 font-bold mb-3 flex items-center">
                  <i class="fa-solid fa-spinner fa-spin mr-2"></i> Running...
                </h3>
                <p class="text-sm text-slate-400">Job ID: {{currentJobId()}}</p>
              </div>
            }
          </div>

          <!-- Main Content -->
          <div class="lg:col-span-9 space-y-6">
            @if (results(); as res) {
               <app-metrics [data]="res.metrics"></app-metrics>
               
               <app-chart [data]="res"></app-chart>
               
               <!-- AI Analysis Section -->
               <div class="bg-slate-900 border border-slate-700 rounded-lg p-6 shadow-xl relative overflow-hidden">
                 <div class="absolute top-0 right-0 p-4 opacity-10">
                   <i class="fa-solid fa-brain text-9xl"></i>
                 </div>
                 
                 <div class="flex justify-between items-start mb-4 relative z-10">
                   <h3 class="text-xl font-bold text-slate-100 flex items-center">
                     <i class="fa-solid fa-robot mr-2 text-cyan-400"></i> AI Analysis
                   </h3>
                   @if (!aiAnalysis() && !isAnalyzing()) {
                     <button (click)="analyze()" class="bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold py-2 px-4 rounded transition-colors shadow-lg shadow-cyan-900/20">
                       Generate Report
                     </button>
                   }
                 </div>

                 @if (isAnalyzing()) {
                   <div class="flex items-center space-x-3 text-cyan-400 animate-pulse py-8">
                     <i class="fa-solid fa-circle-notch fa-spin text-2xl"></i>
                     <span class="font-mono">Processing market telemetry...</span>
                   </div>
                 }

                 @if (aiAnalysis()) {
                   <div class="prose prose-invert max-w-none text-sm animate-fade-in" [innerHTML]="aiAnalysis()"></div>
                 }
               </div>

               <!-- Recent Trades List -->
               <div class="bg-slate-900 border border-slate-700 rounded-lg p-4 shadow-xl">
                  <h3 class="text-slate-400 text-xs font-bold uppercase mb-4">Recent Trades</h3>
                  <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                      <thead class="text-slate-500 border-b border-slate-700">
                        <tr>
                          <th class="pb-2">Type</th>
                          <th class="pb-2">Entry Date</th>
                          <th class="pb-2">Price</th>
                          <th class="pb-2">Exit Date</th>
                          <th class="pb-2">Price</th>
                          <th class="pb-2 text-right">PnL</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-slate-800">
                        @for (trade of lastTrades(); track $index) {
                          <tr class="hover:bg-slate-800/50 transition-colors">
                            <td class="py-2">
                               <span class="px-2 py-0.5 rounded-full bg-emerald-900/50 text-emerald-400 border border-emerald-900">LONG</span>
                            </td>
                            <td class="py-2 font-mono text-slate-400">{{formatDate(trade.entryTime)}}</td>
                            <td class="py-2 font-mono text-slate-300">{{trade.entryPrice.toFixed(2)}}</td>
                            <td class="py-2 font-mono text-slate-400">{{formatDate(trade.exitTime)}}</td>
                            <td class="py-2 font-mono text-slate-300">{{trade.exitPrice.toFixed(2)}}</td>
                            <td class="py-2 font-mono text-right font-bold" [class]="trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'">
                              {{trade.pnl.toFixed(2)}}
                            </td>
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>
               </div>

            } @else {
               <div class="h-96 flex flex-col items-center justify-center text-slate-600 border-2 border-dashed border-slate-800 rounded-lg">
                  <i class="fa-solid fa-chart-line text-4xl mb-4 opacity-50"></i>
                  <p>Load data and run simulation to view results</p>
               </div>
            }
          </div>
        </div>
      </div>
    </div>
  `
})
export class AppComponent {
    private simulationService = inject(SimulationService);
    private aiService = inject(AiService);
    private sanitizer: DomSanitizer = inject(DomSanitizer);
    public backendService = inject(BackendService);

    candles = signal<Candle[]>([]);
    results = signal<BacktestResult | null>(null);
    optResult = signal<OptimizationResult | null>(null);

    aiAnalysis = signal<SafeHtml | null>(null);
    isAnalyzing = signal<boolean>(false);

    // Backend integration
    useBackend = signal<boolean>(false);
    currentJobId = signal<string | null>(null);
    isRunning = signal<boolean>(false);

    constructor() {
        // Initialize with mock data so it works out of the box
        this.candles.set(this.simulationService.generateData(365));

        // Check backend connection on startup
        this.backendService.checkConnection().then(connected => {
            if (connected) {
                console.log('✅ Backend connected');
                // Auto-enable backend mode if available
                this.useBackend.set(true);
            } else {
                console.log('⚠️ Backend not available, using client-side simulation');
            }
        });

        // Subscribe to backend progress updates
        this.backendService.progress$.subscribe(progress => {
            console.log(`Job ${progress.job_id}: ${progress.message}`);
        });
    }

    lastTrades = computed(() => {
        const res = this.results();
        if (!res) return [];
        // Return last 10 trades reversed
        return [...res.trades].reverse().slice(0, 10);
    });

    onFileLoaded(csvContent: string) {
        const parsedCandles = this.simulationService.parseCsvData(csvContent);
        if (parsedCandles.length > 0) {
            this.candles.set(parsedCandles);
            // Reset results on new data load
            this.results.set(null);
            this.optResult.set(null);
            this.aiAnalysis.set(null);
        } else {
            alert('Failed to parse CSV. Ensure format: Date,Open,High,Low,Close,Volume');
        }
    }

    toggleMode() {
        if (this.backendService.connectionStatus() === 'connected') {
            this.useBackend.update(v => !v);
            console.log(`Switched to ${this.useBackend() ? 'Backend' : 'Client'} mode`);
        } else {
            alert('Backend is not available. Please start the backend server.');
        }
    }

    handleRun(config: ConfigData) {
        // Reset AI analysis when new simulation runs
        this.aiAnalysis.set(null);
        this.optResult.set(null); // Clear previous optimization if running manual

        // Ensure we have data
        if (this.candles().length === 0) {
            this.candles.set(this.simulationService.generateData(365));
        }

        if (this.useBackend() && this.backendService.connectionStatus() === 'connected') {
            // Run on backend
            this.runOnBackend(config);
        } else {
            // Run locally
            this.runLocally(config);
        }
    }

    private runLocally(config: ConfigData) {
        if (config.mode === 'single') {
            const res = this.simulationService.runBacktest(
                this.candles(),
                config.initialCapital,
                config.commission,
                config.slippage,
                config.fastMa,
                config.slowMa
            );
            this.results.set(res);
        }
        else if (config.mode === 'optimize' && config.optimization) {
            const opt = this.simulationService.optimizeStrategy(
                this.candles(),
                config.initialCapital,
                config.commission,
                config.slippage,
                config.optimization.fastStart,
                config.optimization.fastEnd,
                config.optimization.fastStep,
                config.optimization.slowStart,
                config.optimization.slowEnd,
                config.optimization.slowStep
            );

            this.optResult.set(opt);
            this.results.set(opt.bestResult);
        }
    }

    private runOnBackend(config: ConfigData) {
        this.isRunning.set(true);

        // Convert CSV data to string if available
        const csvData = this.candles().length > 0 ? this.convertCandlesToCsv() : undefined;

        // Create backend config
        const backendConfig = this.backendService.convertToBackendConfig(
            config.initialCapital,
            config.commission,
            config.slippage,
            config.fastMa,
            config.slowMa,
            csvData
        );

        if (config.mode === 'single') {
            // Run single backtest
            this.backendService.runBacktest(backendConfig).subscribe({
                next: (job) => {
                    this.currentJobId.set(job.job_id);
                    console.log('Backtest submitted:', job.job_id);

                    // Poll for results
                    this.backendService.pollJobUntilComplete(job.job_id).subscribe({
                        next: (updatedJob) => {
                            if (updatedJob.status === 'COMPLETED' && updatedJob.result) {
                                const results = this.backendService.convertFromBackendResults(updatedJob.result);
                                this.results.set(results);
                                this.isRunning.set(false);
                                console.log('✅ Backtest completed');
                            } else if (updatedJob.status === 'FAILED') {
                                alert(`Backtest failed: ${updatedJob.error}`);
                                this.isRunning.set(false);
                            }
                        },
                        error: (error) => {
                            console.error('Error polling job:', error);
                            this.isRunning.set(false);
                            alert('Error running backtest. Check console for details.');
                        }
                    });
                },
                error: (error) => {
                    console.error('Error submitting backtest:', error);
                    this.isRunning.set(false);
                    alert('Failed to submit backtest. Is the backend running?');
                }
            });
        } else if (config.mode === 'optimize' && config.optimization) {
            // Run optimization
            const optConfig = {
                method: 'grid_search' as const,
                param_grid: {
                    'strategy.fast_period': this.range(
                        config.optimization.fastStart,
                        config.optimization.fastEnd,
                        config.optimization.fastStep
                    ),
                    'strategy.slow_period': this.range(
                        config.optimization.slowStart,
                        config.optimization.slowEnd,
                        config.optimization.slowStep
                    )
                },
                objective: 'sharpe_ratio'
            };

            this.backendService.runOptimization(backendConfig, optConfig).subscribe({
                next: (job) => {
                    this.currentJobId.set(job.job_id);
                    console.log('Optimization submitted:', job.job_id);

                    // Poll for results
                    this.backendService.pollJobUntilComplete(job.job_id).subscribe({
                        next: (updatedJob) => {
                            if (updatedJob.status === 'COMPLETED' && updatedJob.result) {
                                // Convert optimization results
                                const bestResult = updatedJob.result.results[0];
                                this.optResult.set({
                                    iterations: updatedJob.result.total_iterations,
                                    bestFastMa: bestResult.config['strategy.fast_period'],
                                    bestSlowMa: bestResult.config['strategy.slow_period'],
                                    bestProfitFactor: bestResult.metrics.profit_factor,
                                    bestResult: this.backendService.convertFromBackendResults(bestResult.metrics)
                                });
                                this.results.set(this.optResult()!.bestResult);
                                this.isRunning.set(false);
                                console.log('✅ Optimization completed');
                            } else if (updatedJob.status === 'FAILED') {
                                alert(`Optimization failed: ${updatedJob.error}`);
                                this.isRunning.set(false);
                            }
                        },
                        error: (error) => {
                            console.error('Error polling optimization:', error);
                            this.isRunning.set(false);
                        }
                    });
                },
                error: (error) => {
                    console.error('Error submitting optimization:', error);
                    this.isRunning.set(false);
                    alert('Failed to submit optimization. Is the backend running?');
                }
            });
        }
    }

    private convertCandlesToCsv(): string {
        const header = 'Date,Open,High,Low,Close,Volume\n';
        const rows = this.candles().map(c =>
            `${new Date(c.time).toISOString()},${c.open},${c.high},${c.low},${c.close},${c.volume}`
        ).join('\n');
        return header + rows;
    }

    private range(start: number, end: number, step: number): number[] {
        const result = [];
        for (let i = start; i <= end; i += step) {
            result.push(i);
        }
        return result;
    }

    async analyze() {
        const metrics = this.results()?.metrics;
        if (!metrics) return;

        this.isAnalyzing.set(true);
        const rawHtml = await this.aiService.analyzeBacktest(metrics);
        // Sanitize the HTML to prevent XSS while allowing styling
        this.aiAnalysis.set(this.sanitizer.bypassSecurityTrustHtml(rawHtml));
        this.isAnalyzing.set(false);
    }

    formatDate(ts: number): string {
        return new Date(ts).toLocaleDateString();
    }
}
