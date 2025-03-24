from strategies.momentum import run_strategy as strat_momentum
from strategies.moving_average import run_strategy as strat_ma

STRATEGIES = {
    "Momentum": strat_momentum,
    "Moving Average": strat_ma
}
