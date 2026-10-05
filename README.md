# quickcut-info

QuickCut の公開情報サイト。本番は **https://quickcut.app**（Cloudflare Pages）。同じ内容が旧 GitHub Pages（https://nbashohei.github.io/quickcut-info/）にも配信されるが、各ページの canonical・hreflang・sitemap は quickcut.app を指す。

- [LP（トップ）](https://quickcut.app/) — 10 言語。`index.html` と `<言語>/index.html`・`sitemap.xml`・`robots.txt` は MPCut リポジトリの `scripts/make-landing-page.py` が生成（手で編集しない）
- [ヘルプ / Help](https://quickcut.app/help) — アプリの Help メニュー「QuickCut Help」の遷移先（10 言語。ブラウザ言語で自動選択、`#de` 等で指定可）。MPCut リポジトリの `scripts/make-help-page.py` が生成（手で編集しない）
- [プライバシーポリシー / Privacy Policy](https://quickcut.app/privacy) — アプリの About から開く（10 言語。`#de` 等で指定可）。App Store Connect のプライバシーポリシー URL / サポート URL は当面 github.io 側を登録したまま
- [オープンソースライセンス / OSS Licenses](https://quickcut.app/licenses)

Cloudflare Pages では拡張子なしが正規 URL（`/help.html` は `/help` へ転送）。アプリ 1.0 (3) までと App Store Connect が github.io の URL を参照しているので、GitHub Pages 側は消さない。
