from services.gambler_profile_service import gambler_service

prefs = gambler_service.set_betting_preferences(
    username="neel123",
    min_bet=10,
    max_bet=500,
    preferred_game_type="dice",
    auto_play_enabled=True,
    auto_play_max_games=20,
    session_loss_limit=300,
    session_win_target=1000
)

print("Preferences:", prefs)

fetched = gambler_service.get_betting_preferences("neel123")
print("Fetched Prefs:", fetched)