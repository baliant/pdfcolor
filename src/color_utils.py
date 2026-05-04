def rgb_float_to_hex(rgb):
    if not rgb:
        return None

    r, g, b = rgb[:3]

    return "#{:02x}{:02x}{:02x}".format(
        int(round(r * 255)),
        int(round(g * 255)),
        int(round(b * 255)),
    )


def hex_to_rgb(hex_color):
    hex_color = hex_color.replace("#", "")

    return tuple(
        int(hex_color[i:i + 2], 16)
        for i in (0, 2, 4)
    )


def color_distance(hex1, hex2):
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)

    return max(
        abs(r1 - r2),
        abs(g1 - g2),
        abs(b1 - b2),
    )


def match_color(actual_hex, configured_colors, tolerance):
    if actual_hex is None:
        return "No color"

    best_name = "Other"
    best_distance = 999

    for name, target_hex in configured_colors.items():
        dist = color_distance(actual_hex, target_hex.lower())

        if dist < best_distance:
            best_distance = dist
            best_name = name

    if best_distance <= tolerance:
        return best_name

    return "Other"
