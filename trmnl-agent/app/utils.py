import random

# Static value sets
DAYS = {0: "Sun",
        1: "Mon",
        2: "Tue",
        3: "Wed",
        4: "Thr",
        5: "Fri",
        6: "Sat"}

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"]


def day_of_week(datetime_obj):
    return DAYS[datetime_obj.weekday()]


def get_headers():
    """
    Randomly select a User-Agent header from the predefined list. 
    """
    return {'User-Agent': random.choice(USER_AGENTS)}


def hex_to_grayscale(hex_color):
    """
    Convert a hex color string to its grayscale equivalent.
    Supports formats: '#RRGGBB' or 'RRGGBB'.
    """
    try:
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')

        # Validate length
        if len(hex_color) != 6:
            raise ValueError("Hex color must be 6 characters long.")

        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Apply luminance formula
        gray = int(round(0.299 * r + 0.587 * g + 0.114 * b))

        # Ensure within 0-255
        gray = max(0, min(255, gray))

        # Convert back to hex (same value for R, G, B)
        gray_hex = "#{0:02X}{0:02X}{0:02X}".format(gray)
        return gray_hex

    except ValueError as e:
        return f"Error: {e}"
