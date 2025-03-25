from strategies.momentum import run_strategy as strat_momentum
from strategies.moving_average import run_strategy as strat_ma
from strategies.bollinger_bands import run_strategy as strat_bollinger
from strategies.breakout_strategie import run_strategy as strat_breakout
from strategies.fibonacci import run_strategy as strat_fibonacci
from strategies.relative_strength import run_strategy as strat_rs
from strategies.september_december import run_strategy as strat_septdec

STRATEGIES = {
    "Momentum": strat_momentum,
    "Moving Average": strat_ma,
    "Bollinger Bands": strat_bollinger,
    "Breakout Strategie": strat_breakout,
    "Fibonacci": strat_fibonacci,
    "Relative Strength": strat_rs,
    "September/December": strat_septdec,
}
