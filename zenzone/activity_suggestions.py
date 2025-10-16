# zenzone/activity_suggestions.py

def get_activity_suggestion(stress_score):
    """
    Get activity suggestion based on stress score.
    Returns a dictionary with activity details formatted for the frontend.
    """
    if stress_score < 25:
        return {
            "title": "Calm",
            "activity": "Play soft lo-fi music 🎧",
            "action": "play_lofi",
            "description": "Your stress levels are low. Maintain this calm state with soothing lo-fi music."
        }
    elif stress_score < 50:
        return {
            "title": "Slightly Tense",
            "activity": "Try a 2-min breathing session 🌬️",
            "action": "breathing",
            "description": "Take a short breathing break to maintain your balance."
        }
    elif stress_score < 75:
        return {
            "title": "Stressed",
            "activity": "Do a short body scan meditation 🧘‍♀️",
            "action": "body_scan",
            "description": "A guided body scan can help reduce your building stress."
        }
    else:
        return {
            "title": "Overwhelmed",
            "activity": "Take a walk or listen to nature sounds 🌲🌊",
            "action": "nature_sounds",
            "description": "Your stress levels are high. Take a break with calming nature sounds."
        }
