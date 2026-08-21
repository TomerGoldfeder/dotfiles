-- AeroSpace window picker: popup list of all windows, highlight + focus.
if WINDOW_MANAGER ~= 'aerospace' then
  return
end

local app_icons = require('helpers.spaces_util.icon_map')

local AEROSPACE = '/opt/homebrew/bin/aerospace'
local POPUP_WIDTH = 420
local TITLE_MAX = 42

local LIST_CMD = table.concat({
  AEROSPACE,
  "list-windows --all --format '%{window-id}%{app-name}%{window-title}%{workspace}' --json",
}, ' ')
local FOCUSED_CMD = AEROSPACE .. " list-windows --focused --format '%{window-id}' --json"

SBAR.add('event', 'window_picker_open')
SBAR.add('event', 'window_picker_close')
SBAR.add('event', 'window_picker_nav')
SBAR.add('event', 'window_picker_select')

local picker = SBAR.add('item', 'windows', {
  position = 'left',
  icon = {
    string = ICONS.windows,
    color = COLORS.lavender,
    padding_left = 8,
    padding_right = 6,
  },
  label = {
    string = '—',
    color = COLORS.subtext1,
    font = { size = STYLE.FONT_SIZE_LABEL },
    padding_right = 8,
  },
  background = {
    color = COLORS.base,
    border_width = STYLE.BORDER_WIDTH,
    height = STYLE.ITEM_HEIGHT,
    border_color = STYLE.UNFOCUSED_BORDER_COLOR,
    corner_radius = STYLE.CORNER_RADIUS,
    drawing = true,
  },
  popup = {
    align = 'left',
    drawing = false,
    y_offset = 4,
  },
})

local header = SBAR.add('item', 'windows.header', {
  position = 'popup.windows',
  icon = {
    string = ICONS.windows,
    color = COLORS.lavender,
    padding_left = 8,
  },
  label = {
    string = 'j/k move  ·  ↵ focus',
    color = COLORS.overlay0,
    align = 'right',
    padding_right = 10,
  },
  width = POPUP_WIDTH,
  background = { drawing = false },
})

local windows = {}
local row_items = {}
local selected = 1
local is_open = false

local function truncate(text, max)
  if not text or text == '' then
    return ''
  end
  text = text:gsub('%s+', ' '):gsub('^%s+', ''):gsub('%s+$', '')
  if #text <= max then
    return text
  end
  return text:sub(1, max - 1) .. '…'
end

local function parse_windows(data)
  local list = {}
  if type(data) ~= 'table' then
    return list
  end

  for _, entry in ipairs(data) do
    local id = entry['window-id']
    if id then
      table.insert(list, {
        id = tonumber(id) or id,
        app = entry['app-name'] or 'App',
        title = entry['window-title'] or '',
        workspace = tostring(entry.workspace or '?'),
      })
    end
  end

  table.sort(list, function(a, b)
    local wa, wb = tonumber(a.workspace) or 0, tonumber(b.workspace) or 0
    if wa ~= wb then
      return wa < wb
    end
    if a.app ~= b.app then
      return a.app < b.app
    end
    return a.title < b.title
  end)

  return list
end

local function focused_id_from(data)
  if type(data) ~= 'table' or not data[1] then
    return nil
  end
  return tonumber(data[1]['window-id'])
end

local function index_of_id(id)
  if not id then
    return 1
  end
  for i, win in ipairs(windows) do
    if win.id == id then
      return i
    end
  end
  return 1
end

local function apply_highlight()
  for i, item in ipairs(row_items) do
    local active = i == selected
    item:set({
      background = {
        drawing = true,
        color = active and COLORS.with_alpha(COLORS.lavender, 0.22) or COLORS.transparent,
        corner_radius = 6,
      },
      icon = { color = active and COLORS.lavender or COLORS.text },
      label = { color = active and COLORS.text or COLORS.subtext1 },
    })
  end
end

local function clear_rows()
  SBAR.remove('/windows\\.row\\..*/')
  SBAR.remove('/windows\\.group\\..*/')
  SBAR.remove('/windows\\.empty/')
  row_items = {}
end

local function exit_picker_mode()
  SBAR.exec(AEROSPACE .. ' mode main')
end

local function close_picker()
  is_open = false
  picker:set({
    popup = { drawing = false },
    background = { border_color = STYLE.UNFOCUSED_BORDER_COLOR },
  })
  exit_picker_mode()
end

local function focus_window(win)
  if not win then
    return
  end
  close_picker()
  -- focus --window-id also switches to that window's workspace
  SBAR.exec(string.format('%s focus --window-id %s', AEROSPACE, win.id))
end

local function add_group_header(workspace)
  SBAR.add('item', 'windows.group.' .. workspace, {
    position = 'popup.windows',
    icon = {
      string = workspace,
      color = COLORS.lavender,
      font = {
        family = FONT.icon,
        style = FONT.style_map['Bold'],
        size = 12.0,
      },
      padding_left = 10,
      padding_right = 6,
      width = 28,
    },
    label = {
      string = 'workspace',
      color = COLORS.overlay0,
      font = { size = 11.0 },
    },
    width = POPUP_WIDTH,
    background = { drawing = false },
  })
end

local function add_window_row(index, win)
  local icon = app_icons[win.app] or app_icons['Default'] or ':default:'
  local title = truncate(win.title, TITLE_MAX)
  local label = title ~= '' and (win.app .. '  ·  ' .. title) or win.app

  local item = SBAR.add('item', 'windows.row.' .. index, {
    position = 'popup.windows',
    icon = {
      string = icon,
      font = 'sketchybar-app-font:Regular:14.0',
      color = COLORS.text,
      padding_left = 12,
      padding_right = 8,
    },
    label = {
      string = label,
      color = COLORS.subtext1,
      align = 'left',
      padding_right = 12,
    },
    width = POPUP_WIDTH,
    background = {
      drawing = true,
      color = COLORS.transparent,
      corner_radius = 6,
      height = 28,
    },
  })

  item:subscribe('mouse.entered', function()
    selected = index
    apply_highlight()
  end)

  item:subscribe('mouse.clicked', function()
    focus_window(win)
  end)

  row_items[index] = item
end

local function render_popup()
  clear_rows()

  if #windows == 0 then
    SBAR.add('item', 'windows.empty', {
      position = 'popup.windows',
      icon = { drawing = false },
      label = {
        string = 'No windows',
        color = COLORS.overlay0,
        padding_left = 12,
      },
      width = POPUP_WIDTH,
    })
    return
  end

  local last_ws = nil
  for i, win in ipairs(windows) do
    if win.workspace ~= last_ws then
      add_group_header(win.workspace)
      last_ws = win.workspace
    end
    add_window_row(i, win)
  end
end

local function set_count(n)
  picker:set({
    label = {
      string = tostring(n),
      drawing = true,
    },
  })
end

local function open_picker()
  SBAR.exec(LIST_CMD, function(data)
    windows = parse_windows(data)
    set_count(#windows)

    SBAR.exec(FOCUSED_CMD, function(focused)
      selected = index_of_id(focused_id_from(focused))
      render_popup()
      apply_highlight()
      is_open = true
      picker:set({
        popup = { drawing = true },
        background = { border_color = STYLE.FOCUSED_BORDER_COLOR },
      })
      SBAR.exec(AEROSPACE .. ' mode window-picker')
    end)
  end)
end

local function navigate(dir)
  if not is_open or #windows == 0 then
    return
  end
  if dir == 'prev' then
    selected = selected - 1
    if selected < 1 then
      selected = #windows
    end
  else
    selected = selected + 1
    if selected > #windows then
      selected = 1
    end
  end
  apply_highlight()
end

local function select_current()
  if not is_open then
    return
  end
  focus_window(windows[selected])
end

local function refresh_count()
  SBAR.exec(LIST_CMD, function(data)
    set_count(#parse_windows(data))
  end)
end

header:subscribe('mouse.clicked', function()
  close_picker()
end)

picker:subscribe('mouse.clicked', function()
  if is_open then
    close_picker()
  else
    open_picker()
  end
end)

picker:subscribe('window_picker_open', function()
  open_picker()
end)

picker:subscribe('window_picker_close', function()
  close_picker()
end)

picker:subscribe('window_picker_nav', function(env)
  navigate(env and env.DIR)
end)

picker:subscribe('window_picker_select', function()
  select_current()
end)

picker:subscribe('aerospace_workspace_change', refresh_count)
picker:subscribe('aerospace_focus_change', refresh_count)

refresh_count()
