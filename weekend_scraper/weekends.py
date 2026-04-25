from datetime import date, timedelta, datetime

def next_n_weekends(today: date, n: int = 26) -> list[tuple[date, date]]:
    """
    Returns a list of (friday, sunday) date tuples for the next n weekends.
    """
    weekends = []
    
    # weekday() returns 0 for Monday, 4 for Friday
    days_until_friday = (4 - today.weekday()) % 7
    
    # If today is Friday, check if it's already evening (past 17:00)
    if days_until_friday == 0:
        if datetime.now().hour >= 17:
            days_until_friday = 7
            
    first_friday = today + timedelta(days=days_until_friday)
    
    for i in range(n):
        friday = first_friday + timedelta(weeks=i)
        sunday = friday + timedelta(days=2)
        weekends.append((friday, sunday))
        
    return weekends
