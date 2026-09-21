{
  description = "MoonBit + zenoh-c development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    moonbit-overlay = {
      url = "github:moonbit-community/moonbit-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "aarch64-darwin"
        "x86_64-linux"
      ];

      perSystem =
        { system, ... }:
        let
          pkgs = import inputs.nixpkgs {
            inherit system;
            overlays = [ inputs.moonbit-overlay.overlays.default ];
          };
          moonbit = pkgs.moonbit-bin.moonbit.latest;

          # nixpkgs installs zenohc.pc (Name: zenohc), not zenoh-c.pc.
          # Requires reuses that file, so include/lib paths stay absolute.
          zenoh-c-pkgconfig = pkgs.writeTextDir "lib/pkgconfig/zenoh-c.pc" ''
            Name: zenoh-c
            Description: Alias for nixpkgs zenohc.pc
            Version: ${pkgs.zenoh-c.version}
            Requires: zenohc
          '';
        in
        {
          packages.moonbit = moonbit;
          packages.default = moonbit;

          devShells.default = pkgs.mkShell {
            packages = [
              moonbit
              pkgs.zenoh-c
              zenoh-c-pkgconfig
              pkgs.zenoh # provides zenohd
              pkgs.cmake
              pkgs.pkg-config
              pkgs.clang
              pkgs.gnumake
              pkgs.git
            ];
          };
        };
    };
}
