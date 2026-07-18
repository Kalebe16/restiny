import qdarktheme


def dark(accent_color: str) -> None:
    custom_colors = None
    if accent_color:
        custom_colors = {
            'primary': accent_color,
        }
    qdarktheme.setup_theme('dark', custom_colors=custom_colors)


def light(accent_color: str) -> None:
    custom_colors = None
    if accent_color:
        custom_colors = {
            'primary': accent_color,
        }
    qdarktheme.setup_theme('light', custom_colors=custom_colors)
