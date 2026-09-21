# zenoh-mbt

MoonBit から zenoh-c を使うための binding。

## 開発環境

```sh
nix develop
```

## パッケージ

native target 用の MoonBit パッケージ。リリースには次の `zenoh-c` static library artifact を添付する。

- `macos-aarch64`
- `macos-x86_64`
- `linux-x86_64`
- `windows-x86_64`

利用側の native build では `prebuild.py` がホストに対応する artifact を選択する。ソースツリーから開発するときは、`zenoh-c` が `pkg-config` で見つかればそれを使う。Moon の prebuild config script を使うため、native build には Python 3 が必要になる。

```sh
moon check --target native
```
