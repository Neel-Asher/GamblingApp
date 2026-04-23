from strategies.flat_strategy import FlatStrategy
from strategies.martingale_strategy import MartingaleStrategy


class StrategyFactory:

    @staticmethod
    def get_strategy(strategy_code):
        if strategy_code == "FLAT":
            return FlatStrategy()
        elif strategy_code == "MARTINGALE":
            return MartingaleStrategy()
        else:
            raise ValueError("Invalid strategy")