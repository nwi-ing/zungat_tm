from django.urls import path

from apps.core.views.logs import log_list
from apps.core.views.settings import settings_panel, toggle_setting

app_name = "core"

urlpatterns = [
    path("logs/", log_list, name="log_list"),
    path("settings/", settings_panel, name="settings_panel"),
    path("settings/<str:module_key>/toggle/", toggle_setting, name="toggle_setting"),
]
