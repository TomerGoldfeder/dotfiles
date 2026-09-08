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
	default_prog = { "/bin/zsh", "-l" },

	-- 60% opaque. Neovim must use a transparent Normal highlight or this
	-- is covered by the colorscheme background.
	window_background_opacity = 0.6,
	window_decorations = "RESIZE",

	-- Left Option as Alt so nvim/zsh can see Option chords. Right Option
	-- still composes characters (e.g. Option-n → ñ).
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
		-- xterm CSI with modifiers, so tmux (xterm-keys) and nvim/zsh see
		-- Alt+Arrow / Alt+Shift+Arrow instead of composed glyphs or \eOD.
		-- 3 = Alt, 4 = Alt+Shift. See wezterm#253.
		{
			key = "LeftArrow",
			mods = "OPT",
			action = wezterm.action.SendString("\x1b[1;3D"),
		},
		{
			key = "RightArrow",
			mods = "OPT",
			action = wezterm.action.SendString("\x1b[1;3C"),
		},
		{
			key = "LeftArrow",
			mods = "OPT|SHIFT",
			action = wezterm.action.SendString("\x1b[1;4D"),
		},
		{
			key = "RightArrow",
			mods = "OPT|SHIFT",
			action = wezterm.action.SendString("\x1b[1;4C"),
		},
		{
			key = "UpArrow",
			mods = "OPT|SHIFT",
			action = wezterm.action.SendString("\x1b[1;4A"),
		},
		{
			key = "DownArrow",
			mods = "OPT|SHIFT",
			action = wezterm.action.SendString("\x1b[1;4B"),
		},
		-- Option+Backspace → Meta-DEL. Shells/nvim bind this as delete-word.
		{
			key = "Backspace",
			mods = "OPT",
			action = wezterm.action.SendString("\x1b\x7f"),
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
