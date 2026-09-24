{ lib, stdenv, swift }:

stdenv.mkDerivation {
  pname = "aerospace-cheatsheet";
  version = "0.1.0";

  src = ./.;

  nativeBuildInputs = [ swift ];

  dontConfigure = true;

  buildPhase = ''
    swiftc -O \
      -framework AppKit \
      -framework SwiftUI \
      -o aerospace-cheatsheet \
      Sources/AeroSpaceCheatsheet/BindingRow.swift \
      Sources/AeroSpaceCheatsheet/SupportPaths.swift \
      Sources/AeroSpaceCheatsheet/ExecutablePath.swift \
      Sources/AeroSpaceCheatsheet/IPC.swift \
      Sources/AeroSpaceCheatsheet/PanelController.swift \
      Sources/AeroSpaceCheatsheet/AppDelegate.swift \
      Sources/AeroSpaceCheatsheet/main.swift
  '';

  installPhase = ''
    install -Dm755 aerospace-cheatsheet $out/bin/aerospace-cheatsheet
  '';

  meta = with lib; {
    description = "Searchable AeroSpace key binding cheat sheet panel";
    platforms = platforms.darwin;
  };
}
