from services.betting_service import betting_service
from rich.console import Console
from rich.table import Table

console = Console()


def run_uc3_demo():
    username = "neel123"
    session_id = 3

    base_bet = 100
    win_probability = 0.5
    strategy = "MARTINGALE" 

    console.rule("[bold yellow]UC3: Betting Engine Demo")

    for i in range(1, 11):
        try:
            console.print(f"\n[cyan]Game {i}[/cyan]")

            bet = betting_service.place_bet(
                username=username,
                session_id=session_id,
                base_bet=base_bet,
                win_probability=win_probability,
                strategy_code=strategy
            )

            result = betting_service.resolve_bet(bet["bet_id"])

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Field")
            table.add_column("Value")

            table.add_row("Bet ID", str(bet["bet_id"]))
            table.add_row("Strategy", bet["strategy"])
            table.add_row("Bet Amount", str(bet["bet_amount"]))
            table.add_row("Outcome", result["outcome"])
            table.add_row("Payout", str(result["payout"]))
            table.add_row("Stake After", str(result["stake_after"]))

            console.print(table)

        except Exception as e:
            console.print(f"\n[red]{str(e)}[/red]")
            console.print("[bold yellow]Session stopped.[/bold yellow]")
            break

    console.rule("[bold green]UC3 Demo Finished")


if __name__ == "__main__":
    run_uc3_demo()