from validators.input_validator import InputValidator
from validators.exceptions import ValidationException


class SafeInputHandler:

    @staticmethod
    def get_valid_number(prompt, field_name):
        while True:
            try:
                value = input(prompt)
                return InputValidator.parse_and_validate_numeric(value, field_name)

            except Exception as e:
                print(f"Invalid input: {e}")

    @staticmethod
    def get_valid_stake(prompt="Enter initial stake: "):
        while True:
            try:
                value = input(prompt)
                return InputValidator.validate_initial_stake(value)

            except ValidationException as e:
                print(f"{e}")

    @staticmethod
    def get_valid_bet(current_stake):
        while True:
            try:
                value = input(f"Enter bet (Available: {current_stake}): ")
                return InputValidator.validate_bet_amount(value, current_stake)

            except ValidationException as e:
                print(f"{e}")

    @staticmethod
    def get_valid_probability():
        while True:
            try:
                value = input("Enter win probability (0-1): ")
                return InputValidator.validate_probability(value)

            except ValidationException as e:
                print(f"{e}")