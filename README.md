# zenoh-mbt

MoonBit から zenoh-c を使うための binding を作る。

## 開発環境

```sh
nix develop
```

direnv を使うなら、このディレクトリで `direnv allow`。`.envrc` は `use flake`。

`devShells.default` は `aarch64-darwin` と `x86_64-linux` に出る。

シェルには MoonBit、zenoh-c、clang、pkg-config、git、zenohd が入る。clang と pkg-config は native binding のビルドに使い、zenohd はローカルの疎通確認に使う。MoonBit は [moonbit-community/moonbit-overlay](https://github.com/moonbit-community/moonbit-overlay) を使い、flake.lock で固定する。

```sh
moon version
pkg-config --modversion zenohc
zenohd --version
```

## ビルドとリンク

`moon.mod.json` があるディレクトリで実行する。

```sh
moon build
moon test
```

zenoh-c を使うパッケージは `preferred-target` を `native` にする。

zenoh-c のリンク設定には `pkg-config` の出力を使う。`cc` を指定しないデバッグビルドは tcc を使うため、システムライブラリをリンクするときは clang を指定する。store path はシェルごとに変わるので、展開したフラグはコミットしない。

```
options(
  "native-stub": [ "stub.c" ],
  link: {
    native: {
      "cc": "clang",
      "cc-flags": "<pkg-config --cflags zenohc の出力>",
      "cc-link-flags": "<pkg-config --libs zenohc の出力>",
    },
  },
)
```

古い `moon.pkg.json` なら同じ項目を `"link"."native"` に置く。ヘッダは `zenoh.h`、ライブラリは `libzenohc`。
