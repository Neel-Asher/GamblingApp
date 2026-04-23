from decimal import Decimal, InvalidOperation
import math

from validators.validation_result import ValidationResult
from validators.validation_config import ValidationConfig
from validators.exceptions import (
    StakeValidationException,
    BetValidationException,
    LimitValidationException,
    ProbabilityValidationException,
)


class InputValidator:

    @staticmethod
    def parse_and_validate_numeric(value, field_name):
        try:
            if value is None:
                raise ValueError("Null value")

            num = Decimal(str(value))

            if math.isinf(float(num)) or math.isnan(float(num)):
                raise ValueError("NaN or Infinity")

            return num

        except (InvalidOperation, ValueError):
            raise ValueError(f"Invalid numeric input for {field_name}: {value}")

    @staticmethod
    def validate_initial_stake(stake):
        stake = InputValidator.parse_and_validate_numeric(stake, "initial_stake")

        if stake <= 0:
            raise StakeValidationException("Stake must be positive", "initial_stake", stake)

        if stake < ValidationConfig.MIN_STAKE or stake > ValidationConfig.MAX_STAKE:
            raise StakeValidationException("Stake out of allowed range", "initial_stake", stake)

        return stake

    @staticmethod
    def validate_bet_amount(bet, current_stake):
        bet = InputValidator.parse_and_validate_numeric(bet, "bet_amount")

        if bet <= 0:
            raise BetValidationException("Bet must be positive", "bet_amount", bet)

        if bet > current_stake:
            raise BetValidationException("Bet exceeds current stake", "bet_amount", bet)

        return bet

    @staticmethod
    def validate_limits(min_limit, max_limit):
        min_limit = InputValidator.parse_and_validate_numeric(min_limit, "min_limit")
        max_limit = InputValidator.parse_and_validate_numeric(max_limit, "max_limit")

        if min_limit < 0 or max_limit < 0:
            raise LimitValidationException("Limits cannot be negative")

        if max_limit <= min_limit:
            raise LimitValidationException("Max limit must be greater than min limit")

        return min_limit, max_limit

    @staticmethod
    def validate_probability(prob):
        prob = InputValidator.parse_and_validate_numeric(prob, "probability")

        if prob < ValidationConfig.MIN_PROBABILITY or prob > ValidationConfig.MAX_PROBABILITY:
            raise ProbabilityValidationException("Probability must be between 0 and 1")

        return prob

    @staticmethod
    def validate_non_negative_stake(stake):
        stake = InputValidator.parse_and_validate_numeric(stake, "stake")

        if stake < 0:
            raise StakeValidationException("Stake cannot be negative")

        if stake == 0 and not ValidationConfig.ALLOW_ZERO_STAKE:
            raise StakeValidationException("Zero stake not allowed")

        return stake