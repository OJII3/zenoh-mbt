# zenoh-mbt

MoonBit から zenoh-c を使うための binding を作る。

## 開発環境

```sh
nix develop
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
