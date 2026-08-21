-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua

-- Shift+Option+Arrows: word/line visual select (macOS / VS Code muscle memory).
-- WezTerm must send these as Alt+Shift (see wezterm.lua).
vim.keymap.set("n", "<M-S-Left>", "vb", { desc = "Select word left" })
vim.keymap.set("n", "<M-S-Right>", "ve", { desc = "Select word right" })
vim.keymap.set("n", "<M-S-Up>", "Vk", { desc = "Select line up" })
vim.keymap.set("n", "<M-S-Down>", "Vj", { desc = "Select line down" })

vim.keymap.set("v", "<M-S-Left>", "b", { desc = "Select word left" })
vim.keymap.set("v", "<M-S-Right>", "e", { desc = "Select word right" })
vim.keymap.set("v", "<M-S-Up>", "k", { desc = "Select line up" })
vim.keymap.set("v", "<M-S-Down>", "j", { desc = "Select line down" })

vim.keymap.set("i", "<M-S-Left>", "<Esc>vb", { desc = "Select word left" })
vim.keymap.set("i", "<M-S-Right>", "<Esc>ve", { desc = "Select word right" })
vim.keymap.set("i", "<M-S-Up>", "<Esc>Vk", { desc = "Select line up" })
vim.keymap.set("i", "<M-S-Down>", "<Esc>Vj", { desc = "Select line down" })
