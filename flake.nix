{
  description = "dotfiles";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-26.05-darwin";
    nix-darwin.url = "github:nix-darwin/nix-darwin/nix-darwin-26.05";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";

    home-manager.url = "github:nix-community/home-manager/release-26.05";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

    # bump with `nix flake update herdr`
    herdr.url = "github:herdrdev/herdr/v0.9.1";
  };

  outputs = { self, nix-darwin, home-manager, nixpkgs, herdr }:
    let
      user = "tomergo";
    in
    {
      darwinConfigurations."mac" = nix-darwin.lib.darwinSystem {
        specialArgs = { inherit user herdr; };
        modules = [
          ./configuration.nix
          home-manager.darwinModules.home-manager
          {
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.extraSpecialArgs = { inherit user herdr; };
            # Distinct from leftover ~/.zshrc.backup so HM can move colliding files.
            home-manager.backupFileExtension = "hm-backup";
            home-manager.users.${user} = import ./home.nix;
          }
        ];
      };
    };
}
