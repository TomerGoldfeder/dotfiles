-- Add the sketchybar module to the package cpath
package.cpath = package.cpath
  .. ';/Users/'
  .. os.getenv('USER')
  .. '/.local/share/sketchybar_lua/?.so'

local helper_dir = os.getenv('HOME') .. '/.config/sketchybar/helpers'
os.execute('(cd "' .. helper_dir .. '" && make)')
