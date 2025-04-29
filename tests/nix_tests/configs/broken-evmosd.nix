{ pkgs ? import ../../../nix { } }:
let ominid = (pkgs.callPackage ../../../. { });
in
ominid.overrideAttrs (oldAttrs: {
  patches = oldAttrs.patches or [ ] ++ [
    ./broken-ominid.patch
  ];
})
