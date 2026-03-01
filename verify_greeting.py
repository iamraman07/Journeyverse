def get_greeting(hour):
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    elif 17 <= hour < 21:
        return "Good Evening"
    else:
        return "Hello" # Changed from "Good Night"

def verify_greetings():
    test_cases = [
        (8, "Good Morning"),
        (14, "Good Afternoon"),
        (19, "Good Evening"),
        (22, "Hello"),
        (2, "Hello")
    ]
    
    for h, expected in test_cases:
        result = get_greeting(h)
        print(f"Hour {h}: Expected '{expected}', Got '{result}' - {'PASS' if result == expected else 'FAIL'}")

if __name__ == "__main__":
    verify_greetings()
