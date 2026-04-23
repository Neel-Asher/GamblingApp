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
        print(f"\n🎮 GAME {game_no}")
        print("-" * 40)

    @staticmethod
    def display_loading(message="Processing game..."):
        print(f"\n⏳ {message}")