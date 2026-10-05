{
  description = "Vericoding tutorial: small verified Lean 4 programs as a stepped slideshow";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs systems
          (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [ pkgs.lean4 pkgs.python3 ];
        };
      });

      packages = forAllSystems (pkgs: {
        slides = pkgs.runCommand "vericoding-tutorial-slides"
          {
            nativeBuildInputs = [ pkgs.lean4 pkgs.python3 ];
          } ''
          mkdir -p $out
          cp -r ${self} tutorial
          chmod -R u+w tutorial
          cd tutorial
          python3 scripts/build_deck.py \
            --example Examples/Head.lean \
            --example Examples/Find.lean \
            --output $out/index.html
        '';

        default = self.packages.${pkgs.stdenv.hostPlatform.system}.slides;
      });
    };
}
