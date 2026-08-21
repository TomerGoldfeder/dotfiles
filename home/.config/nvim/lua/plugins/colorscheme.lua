-- Catppuccin Mocha to match WezTerm. transparent_background lets the
-- terminal's window_background_opacity (60%) show through Neovim.
return {
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = false,
    priority = 1000,
    opts = {
      flavour = "mocha",
      transparent_background = true,
      integrations = {
        native_lsp = { enabled = true },
        treesitter = true,
      },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "catppuccin",
    },
  },
}
