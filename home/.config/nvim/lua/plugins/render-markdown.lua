return {
  {
    "MeanderingProgrammer/render-markdown.nvim",
    dependencies = { "nvim-treesitter/nvim-treesitter", "nvim-tree/nvim-web-devicons" },
    ft = { "markdown", "norg", "rmd", "org", "codecompanion" },
    ---@module 'render-markdown'
    ---@type render.md.UserConfig
    opts = {
      heading = {
        -- LazyVim lang.markdown sets icons = {}, which conceals '#' with
        -- nothing. Restore the default circled heading levels (NORMAL mode).
        icons = { "󰲡 ", "󰲣 ", "󰲥 ", "󰲧 ", "󰲩 ", "󰲫 " },
      },
    },
  },
}
