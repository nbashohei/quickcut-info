# quickcut-info

QuickCut の公開情報サイト。本番は **https://quickcut.app**（Cloudflare Pages）。旧 GitHub Pages（https://nbashohei.github.io/quickcut-info/）は対応する本番URLへの転送専用HTMLを配信する。

- [LP（トップ）](https://quickcut.app/) — 10 言語。`index.html` と `<言語>/index.html`・`sitemap.xml`・`robots.txt` は MPCut リポジトリの `scripts/make-landing-page.py` が生成（手で編集しない）
- [ヘルプ / Help](https://quickcut.app/help) — アプリの Help メニュー「QuickCut Help」の遷移先（10 言語。ブラウザ言語で自動選択、`#de` 等で指定可）。MPCut リポジトリの `scripts/make-help-page.py` が生成（手で編集しない）
- [プライバシーポリシー / Privacy Policy](https://quickcut.app/privacy) — アプリの About から開く（10 言語。`#de` 等で指定可）。App Store Connect のプライバシーポリシー URL / サポート URL は当面 github.io 側を登録したまま
- [オープンソースライセンス / OSS Licenses](https://quickcut.app/licenses)

Cloudflare Pages では拡張子なしが正規 URL（`/help.html` は `/help` へ転送）。アプリ 1.0 (3) までと App Store Connect が github.io の URL を参照しているので、GitHub Pages 側は消さない。

## 配信の分離

- Cloudflare Pages: `main` の通常HTML・アセットを従来どおり配信する。転送用の生成物はコミットしない
- GitHub Pages: publishing sourceを **GitHub Actions** に設定し、`.github/workflows/legacy-pages.yml` が専用artifactを配信する
- `.github/scripts/build_legacy_redirects.py` は元HTMLのcanonicalを読み、0秒meta refresh・canonical・手動リンクを持つ移転ページを別ディレクトリに生成する（HTTP 301ではない）。JavaScriptでクエリとハッシュを保持し、旧トップの `#ja` なども対応言語へ移す
- `/help.html`・`/privacy.html`・`/licenses.html` に加え、拡張子なしの入口も用意する。既存アセットURLとGoogle所有権確認ファイルは互換性のため維持する。未知のURLは404のままで一律トップへ転送しない
- 旧ページをnoindexやrobots遮断にはしない。検索結果の切り替えにはGoogleの再クロールが必要。転送は少なくとも1年、可能なら継続して維持する
- 検証: `python3 .github/scripts/test_legacy_redirects.py`。ローカル生成は `python3 .github/scripts/build_legacy_redirects.py --output /tmp/<新しい空ディレクトリ>`（リポジトリ内への出力・既存ファイルの上書きは拒否）
- ロールバック: GitHub Pagesのsourceを `main` / rootのbranch配信へ戻すと従来のLPに戻る。Cloudflareの設定・ファイルは変更不要
