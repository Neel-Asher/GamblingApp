from strategies.base_strategy import BaseStrategy


class MartingaleStrategy(BaseStrategy):

    def get_next_bet(self, context):
        last_outcome = context.get("last_outcome")
        last_bet = context.get("last_bet", context["base_bet"])

        if last_outcome == "LOSS":
            return last_bet * 2
        else:
            return context["base_bet"]