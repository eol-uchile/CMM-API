from django.apps import AppConfig
from openedx.core.djangoapps.plugins.constants import (
    PluginSettings,
    PluginURLs,
    ProjectType,
    SettingsType,
)


class CMMAPIConfig(AppConfig):
    name = 'cmmapi'
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: "cmmapi",
                PluginURLs.REGEX: r"^cmm_api/",
                PluginURLs.RELATIVE_PATH: "urls_lms",
            },
        },
        PluginSettings.CONFIG: {
            ProjectType.CMS: {
                SettingsType.COMMON: {
                    PluginSettings.RELATIVE_PATH: "settings.common"}},
            ProjectType.LMS: {
                SettingsType.COMMON: {
                    PluginSettings.RELATIVE_PATH: "settings.common"}},
        },
    }
