from validators.safe_input_handler import SafeInputHandler
from services.betting_service import betting_service
from services.game_session_manager import session_manager

from rich.console import Console

console = Console()


def run_uc6_demo():
    console.rule("[bold red]UC6: Input Validation Demo")

    username = "neel123"

    session_id = session_manager.start_session(username)

    base_bet = SafeInputHandler.get_valid_stake("Enter base bet: ")
    probability = SafeInputHandler.get_valid_probability()

    for i in range(5):
        print(f"\nGame {i+1}")

        try:
            bet = betting_service.place_bet(
                username=username,
                session_id=session_id,
                base_bet=base_bet,
                win_probability=probability,
                strategy_code="FLAT"
            )

            result = betting_service.resolve_bet(bet["bet_id"])

            print("Outcome:", result["outcome"])
            print("Stake:", result["stake_after"])

        except Exception as e:
            print(f"⚠️ Error handled safely: {e}")
            continue

    console.rule("[bold green]UC6 Complete")


if __name__ == "__main__":
    run_uc6_demo()