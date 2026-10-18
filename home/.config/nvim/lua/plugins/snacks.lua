-- Show hidden dotfiles and directories in the Snacks explorer and pickers.
return {
  {
    "folke/snacks.nvim",
    opts = {
      scroll = { enabled = false },
      words = { enabled = false },
      picker = {
        sources = {
          explorer = {
            hidden = true,
          },
          files = {
            hidden = true,
          },
          grep = {
            hidden = true,
          },
        },
      },
    },
  },
}
