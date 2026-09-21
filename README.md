# zenoh-mbt

MoonBit から zenoh-c をリンクするための開発環境。

## 入り方

```sh
nix develop
```

direnv を使うなら、このディレクトリで `direnv allow`。`.envrc` は `use flake`。

`devShells.default` は `aarch64-darwin` と `x86_64-linux` に出る。darwin のシェルに Linux 用バイナリは入らない。

入ったあと、次が通る想定。

```sh
moon version
pkg-config --modversion zenoh-c
zenohd --version
```

MoonBit は [moonbit-community/moonbit-overlay](https://github.com/moonbit-community/moonbit-overlay) の `moonbit-bin.moonbit.latest` を使う。overlay は flake.lock で固定されるため、更新するまでは同じツールチェーンを使う。`zenohd` は nixpkgs の `zenoh`、ライブラリは `zenoh-c`。cmake、pkg-config、clang、gnumake、git も入る。MoonBit CLI は git を要求する。

## moon build / moon test

このリポジトリにはまだ MoonBit モジュールが無い。`moon.mod.json` があるディレクトリで次を実行する。

```sh
moon build
moon test
```

native バックエンドは `moon build --target native`。zenoh-c をリンクするパッケージは `preferred-target` を `native` にしておく。

## zenoh-c のリンク

nixpkgs がインストールする pkg-config ファイルは `zenohc.pc` で、名前は `zenohc`。devShell では同じ内容を `zenoh-c` でも引ける。

```sh
pkg-config --cflags --libs zenoh-c
```

`cc` を指定しないデバッグビルドは tcc を使う。システムライブラリをリンクするときは `cc` を clang にする。store path はシェルが変わると変わるので、展開したフラグはコミットしない。シェルの中で pkg-config の出力を `moon.pkg` に書く。

```
options(
  "native-stub": [ "stub.c" ],
  link: {
    native: {
      "cc": "clang",
      "cc-flags": "<pkg-config --cflags zenoh-c の出力>",
      "cc-link-flags": "<pkg-config --libs zenoh-c の出力>",
    },
  },
)
```

古い `moon.pkg.json` なら同じ項目を `"link"."native"` に置く。ヘッダは `zenoh.h`。リンクするライブラリは `libzenohc` (`-lzenohc`)。
