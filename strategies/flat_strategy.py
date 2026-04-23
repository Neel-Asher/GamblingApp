from strategies.base_strategy import BaseStrategy


class FlatStrategy(BaseStrategy):

    def get_next_bet(self, context):
        return context["base_bet"]