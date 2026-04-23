from services.betting_service import betting_service
from services.game_session_manager import session_manager
from services.analytics_service import analytics_service
from rich.console import Console
from rich.table import Table

console = Console()


def run_uc5_demo():
    username = "neel123"

    session_id = session_manager.start_session(username)

    console.rule("[bold green]UC5: Analytics Demo")

    # Play 10 games
    for i in range(10):
        bet = betting_service.place_bet(
            username=username,
            session_id=session_id,
            base_bet=100,
            win_probability=0.5,
            strategy_code="MARTINGALE"
        )

        result = betting_service.resolve_bet(bet["bet_id"])

        session_manager.update_after_game(session_id, result["stake_after"])

        reason = session_manager.check_and_end_session(
            session_id,
            result["stake_after"]
        )

        if reason:
            print(f"Session ended due to: {reason}")
            break

    # 📊 SUMMARY
    summary = analytics_service.get_session_summary(session_id)

    if summary:
        table = Table(title="Session Summary")

        table.add_column("Metric")
        table.add_column("Value")

        table.add_row("Total Games", str(summary["total_games"]))
        table.add_row("Wins", str(summary["total_wins"]))
        table.add_row("Losses", str(summary["total_losses"]))
        table.add_row("Net Profit", str(summary["net_profit"]))
        table.add_row("Win Rate", str(round(summary["win_rate"], 2)))
        table.add_row("ROI", str(round(summary["roi"], 2)))
        table.add_row("Longest Win Streak", str(summary["longest_win_streak"]))
        table.add_row("Longest Loss Streak", str(summary["longest_loss_streak"]))

        console.print(table)

    console.rule("[bold blue]UC5 Demo Finished")


if __name__ == "__main__":
    run_uc5_demo()