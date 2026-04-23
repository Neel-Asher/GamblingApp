from services.game_session_manager import session_manager
from rich.console import Console
from rich.table import Table
import time


def run_uc4_demo():
    console = Console()
    username = "neel123"

    console.rule("[bold cyan]UC4: Game Session Management Demo")

    console.print("\n[green]Starting new session...[/green]")
    
    existing = session_manager.get_active_session(username)
    if existing:
        session_manager.end_session(existing, "RESET_BEFORE_DEMO")

    session_id = session_manager.start_session(username)
    console.print(f"[bold]Session Started:[/bold] {session_id}")

    console.print("\n[blue]Simulating gameplay...[/blue]")
    time.sleep(1)

    console.print("\n[yellow]Pausing session...[/yellow]")
    session_manager.pause_session(session_id, "USER_BREAK")
    time.sleep(1)

    console.print("\n[green]Resuming session...[/green]")
    session_manager.resume_session(session_id)
    time.sleep(1)

    console.print("\n[yellow]Pausing again...[/yellow]")
    session_manager.pause_session(session_id, "PHONE_CALL")
    time.sleep(1)

    console.print("\n[green]Resuming again...[/green]")
    session_manager.resume_session(session_id)
    time.sleep(1)

    console.print("\n[red]Ending session...[/red]")
    session_manager.end_session(session_id, "USER_EXIT")

    session = session_manager.get_session_details(session_id)

    table = Table(title="Session Summary")

    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in session.items():
        table.add_row(str(key), str(value))

    console.print(table)

    console.rule("[bold green]UC4 Demo Finished")

if __name__ == "__main__":
    run_uc4_demo()