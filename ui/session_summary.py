class SessionSummary:

    @staticmethod
    def display_summary(session_data):
        print("\n" + "=" * 60)
        print("         SESSION SUMMARY")
        print("=" * 60)

        print(f"Session ID      : {session_data['session_id']}")
        print(f"Total Games     : {session_data['games_played']}")
        print(f"Starting Stake  : {session_data['starting_stake']}")
        print(f"Ending Stake    : {session_data['ending_stake']}")
        print(f"Peak Stake      : {session_data['peak_stake']}")
        print(f"Lowest Stake    : {session_data['lowest_stake']}")
        print(f"Net Profit      : {session_data['ending_stake'] - session_data['starting_stake']}")

        print("=" * 60 + "\n")