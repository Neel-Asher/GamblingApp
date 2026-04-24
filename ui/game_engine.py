from services.betting_service import betting_service
from services.game_session_manager import session_manager
from ui.game_status_display import GameStatusDisplay
from ui.interactive_menu import InteractiveMenu
from ui.session_summary import SessionSummary


class SimpleGameEngine:

    def __init__(self, username):
        self.username = username
        self.session_id = session_manager.start_session(username)
        self.last_bet_result = None

    def run(self):

        game_no = 1

        while True:

            InteractiveMenu.display_main_menu()
            choice = InteractiveMenu.get_user_choice()

            if choice == 1:

                GameStatusDisplay.display_game_header(game_no)

                bet_amount = InteractiveMenu.prompt_for_bet_amount()
                win_prob = InteractiveMenu.prompt_for_probability()

                try:
                    self.last_bet_result = betting_service.place_bet(
                        username=self.username,
                        session_id=self.session_id,
                        base_bet=bet_amount,
                        win_probability=win_prob,
                        strategy_code="FLAT"
                    )

                    result = betting_service.resolve_bet(
                        self.last_bet_result["bet_id"]
                    )

                    GameStatusDisplay.display_current_status(
                        self.username,
                        self.session_id,
                        result["stake_after"],
                        game_no
                    )

                    print(f"Outcome: {result['outcome']}")
                    print(f"Updated Stake: {result['stake_after']}")

                    game_no += 1

                except Exception as e:
                    print(f"Error: {e}")

            elif choice == 2:
                    session_data = session_manager.get_session_status(self.session_id)
                    GameStatusDisplay.display_session_status(session_data)

            elif choice == 3:
                result = betting_service.get_last_game_result(self.session_id)

                if result:
                    print("\nLAST GAME RESULT")
                    print("-" * 30)
                    print(f"Bet ID: {result['bet_id']}")
                    print(f"Outcome: {result['outcome']}")
                    print(f"Bet Amount: {result['bet_amount']}")
                    print(f"Stake After: {result['stake_after']}")
                    print("-" * 30)
                else:
                    print("\nNo games played yet.")

            elif choice == 4:
                session_data = session_manager.get_session_summary(self.session_id)
                SessionSummary.display_summary(session_data)
                break

            else:
                print("Invalid choice. Try again.")