class GameStatusDisplay:

    @staticmethod
    def display_current_status(username, session_id, stake, games_played):
        print("\n" + "=" * 60)
        print(f"PLAYER: {username}")
        print(f"SESSION: {session_id}")
        print(f"CURRENT STAKE: {stake}")
        print(f"GAMES PLAYED: {games_played}")
        print("=" * 60 + "\n")

    @staticmethod
    def display_game_header(game_no):
        print(f"\nGAME {game_no}")
        print("-" * 40)

    @staticmethod
    def display_loading(message="Processing game..."):
        print(f"\n{message}")

    @staticmethod
    def display_session_status(session):
        print("\nSESSION STATUS")
        print("-" * 30)
        print(f"Session ID: {session['session_id']}")
        print(f"Username: {session['username']}")
        print(f"Status: {session['status']}")
        print(f"Current Stake: {session['lowest_stake'] + (session['peak_stake'] - session['starting_stake'])}")
        print(f"Games Played: {session['games_played']}")
        print(f"Peak Stake: {session['peak_stake']}")
        print(f"Lowest Stake: {session['lowest_stake']}")
        print("-" * 30)