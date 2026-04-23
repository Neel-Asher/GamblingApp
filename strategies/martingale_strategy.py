from decimal import Decimal
from strategies.base_strategy import BaseStrategy

class MartingaleStrategy(BaseStrategy):

    def get_next_bet(self, context):
        base_bet = Decimal(context["base_bet"])
        last_outcome = context.get("last_outcome")
        last_bet = context.get("last_bet")

        if last_outcome is None or not last_bet or last_bet <= 0:
            return base_bet

        last_bet = Decimal(last_bet)

        if last_outcome == "LOSS":
            return last_bet * 2

        if last_outcome == "WIN":
            return base_bet

        return base_bet