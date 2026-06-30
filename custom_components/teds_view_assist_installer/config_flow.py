"""Config and options flow for Ted's View Assist Installer."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_BRANCH, CONF_REPO, DEFAULT_BRANCH, DEFAULT_REPO, DOMAIN


def _schema(repo: str, branch: str) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_REPO, default=repo): str,
            vol.Required(CONF_BRANCH, default=branch): str,
        }
    )


class TedsVAInstallerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Single-instance config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(
                title="Ted's View Assist",
                data={},
                options={
                    CONF_REPO: user_input[CONF_REPO].strip(),
                    CONF_BRANCH: user_input[CONF_BRANCH].strip(),
                },
            )
        return self.async_show_form(
            step_id="user", data_schema=_schema(DEFAULT_REPO, DEFAULT_BRANCH)
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return TedsVAInstallerOptionsFlow()


class TedsVAInstallerOptionsFlow(config_entries.OptionsFlow):
    """Let the user change the source repo/branch."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_REPO: user_input[CONF_REPO].strip(),
                    CONF_BRANCH: user_input[CONF_BRANCH].strip(),
                }
            )
        opts = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(
                opts.get(CONF_REPO, DEFAULT_REPO), opts.get(CONF_BRANCH, DEFAULT_BRANCH)
            ),
        )
