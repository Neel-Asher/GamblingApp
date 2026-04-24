class InteractiveMenu:

    @staticmethod
    def display_main_menu():
        print("\n" + "=" * 50)
        print("        GAMBLING ENGINE MENU")
        print("=" * 50)
        print("1. Place Bet")
        print("2. View Session Status")
        print("3. View Last Game Result")
        print("4. Exit Session")
        print("=" * 50)

    @staticmethod
    def get_user_choice():
        try:
            return int(input("Enter choice (1-4): "))
        except:
            return -1

    @staticmethod
    def prompt_for_bet_amount():
        try:
            return float(input("\nEnter bet amount: "))
        except:
            print("Invalid input. Defaulting to 0")
            return 0

    @staticmethod
    def prompt_for_probability():
        try:
            return float(input("Enter win probability (0-1): "))
        except:
            print("Invalid input. Defaulting to 0.5")
            return 0.5