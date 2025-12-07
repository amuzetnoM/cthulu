import numpy as np
import matplotlib.pyplot as plt

# Simulation parameters
win_rate = 0.43 # 43%
initial_rrr = 1.3  # reward-risk-ratio
rrr_step = 0.2   # rrr increment
risk_percent = 0.01  # 1% risk per trade
num_executions = 100   # Number of confirmation for entry
trades_per_execution = 3   # number of trade per execution
simulations = 500    # number of simulation runs
initial_balance = 1000   # starting balance

# Calculate risk amount per trade
risk_amount = risk_percent * initial_balance

np.random.seed(42)
# Monte Carlo simulation
equity_curves = []
drawdowns = []

for _ in range(simulations):
    equity = initial_balance
    curve = [equity]
    peak = equity
    dd_list = []

    for _ in range(num_executions):
        # Determine win/loss for 5 trades
        trade_outcomes = np.random.rand(trades_per_execution) < win_rate
        num_wins = np.sum(trade_outcomes)
        pnl = 0

        for i in range(trades_per_execution):
            rrr = initial_rrr + i * rrr_step
            if i < num_wins:
                pnl += rrr * risk_amount  # profit
            else:
                pnl -= risk_amount  # loss

        equity += pnl
        curve.append(equity)

        # Track peak and drawdown
        peak = max(peak, equity)
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        dd_list.append(dd)

    equity_curves.append(curve)
    drawdowns.append(max(dd_list))  # store maximum drawdown % for this simulation

# Convert to NumPy array
equity_curves = np.array(equity_curves)
mean_curve = np.mean(equity_curves, axis=0)
median_curve = np.median(equity_curves, axis=0)
median_drawdown = np.median(drawdowns)
profitable_percent = np.mean(equity_curves[:, -1] > initial_balance) * 100

# Plot equity curves
plt.figure(figsize=(10, 5))
for curve in equity_curves:
    plt.plot(curve, color='gray', alpha=0.2)

plt.plot(mean_curve, label='Mean Equity Curve', color='blue', linewidth=2)
plt.plot(median_curve, label='Median Equity Curve', color='green', linewidth=2)
plt.title(f"Equity Curve for Win-rate={win_rate*100}% \n ({trades_per_execution} trade(s) per execution, initRRR={initial_rrr}, Rstep={rrr_step})")
plt.xlabel("Executions")
plt.ylabel("Account Equity")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# Print results
print(f"Mean Equity Curve: ${mean_curve[-1]:,.2f}")
print(f"Median Equity Curve: ${median_curve[-1]:,.2f}")
print(f"Median Drawdown%: {median_drawdown:.2f}%")
print(f"Profitable%: {profitable_percent:.2f}%")
