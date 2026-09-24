{ lib, buildGoModule }:

buildGoModule {
  pname = "h";
  version = "0.1.0";
  src = ./.;

  vendorHash = "sha256-uwBJAqN4sIepiiJf9lCDumLqfKJEowQO2tOiSWD3Fig=";

  ldflags = [ "-s" "-w" ];

  postInstall = ''
    mv $out/bin/hs $out/bin/h
  '';

  meta = with lib; {
    description = "Herdr session picker (glyph command-palette + spinner)";
    mainProgram = "h";
    platforms = platforms.unix;
  };
}
