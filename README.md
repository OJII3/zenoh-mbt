# zenoh-mbt

MoonBit から zenoh-c を使うための binding。

## 開発環境

```sh
nix develop
```

## パッケージ

native target 用の MoonBit パッケージ。`zenoh-c` のヘッダとライブラリは利用側の開発環境から解決する。

```sh
moon check --target native
```
