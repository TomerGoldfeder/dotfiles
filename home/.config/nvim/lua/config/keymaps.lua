-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua

-- Option+Arrows: word jump. Shift+Option+Arrows: word/line visual select.
-- WezTerm sends these as xterm CSI Alt / Alt+Shift (see wezterm.lua).
vim.keymap.set({ "n", "v" }, "<M-Left>", "b", { desc = "Word left" })
vim.keymap.set({ "n", "v" }, "<M-Right>", "w", { desc = "Word right" })
vim.keymap.set("i", "<M-Left>", "<C-Left>", { desc = "Word left" })
vim.keymap.set("i", "<M-Right>", "<C-Right>", { desc = "Word right" })
vim.keymap.set("c", "<M-Left>", "<S-Left>", { desc = "Word left" })
vim.keymap.set("c", "<M-Right>", "<S-Right>", { desc = "Word right" })
vim.keymap.set("i", "<M-BS>", "<C-w>", { desc = "Delete word" })
vim.keymap.set("c", "<M-BS>", "<C-w>", { desc = "Delete word" })
vim.keymap.set("n", "<M-BS>", "db", { desc = "Delete word" })
vim.keymap.set("v", "<M-BS>", "d", { desc = "Delete word" })
-- WezTerm sends Meta-DEL (\x1b\x7f); some builds report that as <M-Del>.
vim.keymap.set("i", "<M-Del>", "<C-w>", { desc = "Delete word" })
vim.keymap.set("c", "<M-Del>", "<C-w>", { desc = "Delete word" })
vim.keymap.set("n", "<M-Del>", "db", { desc = "Delete word" })
vim.keymap.set("v", "<M-Del>", "d", { desc = "Delete word" })

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
