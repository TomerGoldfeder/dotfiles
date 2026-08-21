local wezterm = require("wezterm")
return {
	adjust_window_size_when_changing_font_size = false,
	color_scheme = "Catppuccin Mocha",
	enable_tab_bar = false,
	font_size = 16.0,
	font = wezterm.font_with_fallback({
		"JetBrainsMono Nerd Font",
		"JetBrains Mono",
		"Symbols Nerd Font Mono",
	}),
	macos_window_background_blur = 30,
	default_prog = { "/run/current-system/sw/bin/nu" },

	-- 60% opaque. Neovim must use a transparent Normal highlight or this
	-- is covered by the colorscheme background.
	window_background_opacity = 0.6,
	window_decorations = "RESIZE",

	-- Left Option as Alt so nvim can see Option/Shift+Option chords.
	send_composed_key_when_left_alt_is_pressed = false,
	send_composed_key_when_right_alt_is_pressed = true,

	keys = {
		{
			key = "q",
			mods = "CTRL",
			action = wezterm.action.ToggleFullScreen,
		},
		{
			key = "'",
			mods = "CTRL",
			action = wezterm.action.ClearScrollback("ScrollbackAndViewport"),
		},
		{
			key = "LeftArrow",
			mods = "OPT|SHIFT",
			action = wezterm.action.SendKey({ key = "LeftArrow", mods = "ALT|SHIFT" }),
		},
		{
			key = "RightArrow",
			mods = "OPT|SHIFT",
			action = wezterm.action.SendKey({ key = "RightArrow", mods = "ALT|SHIFT" }),
		},
		{
			key = "UpArrow",
			mods = "OPT|SHIFT",
			action = wezterm.action.SendKey({ key = "UpArrow", mods = "ALT|SHIFT" }),
		},
		{
			key = "DownArrow",
			mods = "OPT|SHIFT",
			action = wezterm.action.SendKey({ key = "DownArrow", mods = "ALT|SHIFT" }),
		},
	},
	mouse_bindings = {
		-- Ctrl-click will open the link under the mouse cursor
		{
			event = { Up = { streak = 1, button = "Left" } },
			mods = "CTRL",
			action = wezterm.action.OpenLinkAtMouseCursor,
		},
	},
}
