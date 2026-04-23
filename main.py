from services.gambler_profile_service import gambler_service
from services.stake_management_service import stake_service
from config.database import db


def setup_demo_user():
    try:
        gambler = gambler_service.create_gambler(
            username="neel123",
            full_name="Neel Asher",
            email="neel@test.com",
            initial_stake=1000
        )
        print("Gambler created:", gambler)
    except Exception:
        print("Gambler already exists")

    return gambler_service.get_gambler_by_username("neel123")


def create_session(gambler_id):
    db.execute("""
        INSERT INTO sessions (gambler_id, status, starting_stake)
        VALUES (%s, 'ACTIVE', %s)
    """, (gambler_id, 1000))

    session = db.execute("""
        SELECT session_id FROM sessions 
        WHERE gambler_id = %s 
        ORDER BY session_id DESC LIMIT 1
    """, (gambler_id,), fetch=True)

    return session[0]["session_id"]


def run_uc2_demo():
    print("\n===== UC2: STAKE MANAGEMENT DEMO =====\n")

    gambler = setup_demo_user()
    session_id = create_session(gambler["gambler_id"])

    print(f"Session created: {session_id}")

    # Initial stake
    print("\nCurrent Stake:")
    print(stake_service.get_current_stake("neel123"))

    # Deposit
    print("\nDepositing 500...")
    stake_service.deposit("neel123", 500, session_id)

    # Withdraw
    print("\nWithdrawing 200...")
    stake_service.withdraw("neel123", 200, session_id)

    # Adjust
    print("\nAdjusting -100...")
    stake_service.adjust_stake("neel123", -100, session_id)

    # Final stake
    print("\nFinal Stake:")
    print(stake_service.get_current_stake("neel123"))

    # Transaction history
    print("\nTransaction History:")
    history = stake_service.get_transaction_history("neel123")
    for txn in history:
        print(txn)

    # Stake summary
    print("\nStake Summary:")
    summary = stake_service.get_stake_summary("neel123")
    print(summary)

    # Session stats
    print("\nSession Stats:")
    stats = db.execute("""
        SELECT peak_stake, lowest_stake 
        FROM sessions WHERE session_id = %s
    """, (session_id,), fetch=True)

    print(stats[0])


if __name__ == "__main__":
    run_uc2_demo()