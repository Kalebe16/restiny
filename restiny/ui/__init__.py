"""
This module contains the specific sections of the DataFox user interface (UI).
"""

from restiny.ui.collections_area import CollectionsArea
from restiny.ui.request_area import RequestArea
from restiny.ui.response_area import ResponseArea
from restiny.ui.top_bar_area import TopBarArea
from restiny.ui.url_area import URLArea

__all__ = [
    'RequestArea',
    'ResponseArea',
    'URLArea',
    'CollectionsArea',
    'TopBarArea',
]
