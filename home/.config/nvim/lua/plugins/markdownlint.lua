-- Point markdownlint-cli2 at the global config so disabled rules apply in
-- every buffer, not only inside the dotfiles repo.
local config = vim.fn.expand("~/.markdownlint.jsonc")

return {
  {
    "mfussenegger/nvim-lint",
    optional = true,
    opts = {
      linters = {
        -- LazyVim prepends these to nvim-lint's default { "-" }, so stdin stays last.
        ["markdownlint-cli2"] = {
          prepend_args = { "--config", config },
        },
      },
    },
  },
  {
    -- The markdown extra also adds none-ls markdownlint_cli2, which does not get
    -- --config and reports every rule outside this repo. Drop it so nvim-lint
    -- is the only markdown linter.
    "nvimtools/none-ls.nvim",
    optional = true,
    opts = function(_, opts)
      opts.sources = vim.tbl_filter(function(source)
        return source.name ~= "markdownlint-cli2"
      end, opts.sources or {})
    end,
  },
  {
    "stevearc/conform.nvim",
    optional = true,
    opts = {
      formatters = {
        ["markdownlint-cli2"] = {
          prepend_args = { "--config", config },
        },
      },
    },
  },
}
