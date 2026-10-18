import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from build_legacy_redirects import SOURCE, HeadLinks, build, render_redirect


def tree_hash(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and not any(x.startswith('.') for x in p.relative_to(root).parts)}


class LegacyRedirectTests(unittest.TestCase):
    def test_real_site_mapping_and_source_preservation(self):
        before = tree_hash(SOURCE)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "output"
            manifest = build(SOURCE, out)
            self.assertEqual(manifest['index.html'], 'https://quickcut.app/en/')
            for locale in ['ja','en','de','es','fr','it','ko','pt-br','zh-hans','zh-hant']:
                self.assertEqual(manifest[f'{locale}/index.html'], f'https://quickcut.app/{locale}/')
            for page in ['help','privacy','licenses']:
                self.assertEqual(manifest[f'{page}.html'], f'https://quickcut.app/{page}')
                self.assertEqual(manifest[f'{page}/index.html'], f'https://quickcut.app/{page}')
            for relative, target in manifest.items():
                text = (out / relative).read_text()
                self.assertIn(f'content="0; url={target}"', text)
                self.assertEqual(HeadLinks(text).canonicals, [target])
                self.assertNotIn('noindex', text)
                self.assertNotIn('<video', text)
                self.assertIn('id="destination"', text)
            self.assertNotIn('Disallow:', (out / 'robots.txt').read_text())
            self.assertNotIn('http-equiv="refresh"', (out / '404.html').read_text())
            for file in (SOURCE / 'assets').iterdir():
                if file.is_file():
                    self.assertEqual(file.read_bytes(), (out / 'assets' / file.name).read_bytes())
            self.assertFalse((out / '.github').exists())
            self.assertFalse((out / 'CNAME').exists())
        self.assertEqual(tree_hash(SOURCE), before)

    def test_output_cannot_overwrite_checkout_or_existing_files(self):
        for output in [SOURCE, SOURCE / '_site', SOURCE.parent]:
            with self.assertRaises(ValueError):
                build(SOURCE, output)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'keep.txt').write_text('keep')
            with self.assertRaises(ValueError):
                build(SOURCE, path)
            self.assertEqual((path / 'keep.txt').read_text(), 'keep')

    def test_only_https_quickcut_targets(self):
        for target in ['https://evil.invalid/ja/', 'javascript:alert(1)', 'http://quickcut.app/', 'https://quickcut.app.evil.invalid/', 'https://quickcut.app/"bad']:
            with self.assertRaises(ValueError):
                render_redirect(target)

    def test_search_console_verification_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'source', root / 'output'
            source.mkdir()
            (source / 'index.html').write_text('<link rel="canonical" href="https://quickcut.app/en/">')
            token = 'google-site-verification: google123abc.html'
            (source / 'google123abc.html').write_text(token)
            build(source, output)
            self.assertEqual((output / 'google123abc.html').read_text(), token)

    def test_runtime_preserves_query_and_hash_and_has_no_open_redirect(self):
        root_links = HeadLinks((SOURCE / 'index.html').read_text()).languages
        cases = []
        for target, languages, query, fragment, expected in [
            ('https://quickcut.app/help', {}, '?from=old', '#ja-save', 'https://quickcut.app/help?from=old#ja-save'),
            ('https://quickcut.app/privacy', {}, '', '#de', 'https://quickcut.app/privacy#de'),
            ('https://quickcut.app/ja/', {}, '?utm_source=old', '#pricing', 'https://quickcut.app/ja/?utm_source=old#pricing'),
            ('https://quickcut.app/en/', root_links, '?from=legacy', '#ja', 'https://quickcut.app/ja/?from=legacy'),
            ('https://quickcut.app/en/', root_links, '', '#zh-Hant', 'https://quickcut.app/zh-hant/'),
            ('https://quickcut.app/en/', root_links, '?url=https://evil.invalid', '#pricing', 'https://quickcut.app/en/?url=https://evil.invalid#pricing'),
        ]:
            script = render_redirect(target, languages).split('<script>')[1].split('</script>')[0]
            cases.append(dict(script=script, search=query, hash=fragment, expected=expected))
        program = '''const vm=require('node:vm'),assert=require('node:assert/strict');
const cases=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
for(const c of cases){let actual;const refresh={},link={};const listeners={};
vm.runInNewContext(c.script,{URL,location:{search:c.search,hash:c.hash,replace:v=>actual=v},document:{getElementById:id=>id==='redirect'?refresh:link,addEventListener:(k,f)=>listeners[k]=f}});
assert.equal(actual,c.expected);assert.equal(refresh.content,'0; url='+c.expected);listeners.DOMContentLoaded();assert.equal(link.href,c.expected);}
console.log(cases.length+' JS redirect cases passed');'''
        subprocess.run(['node', '-e', program], input=json.dumps(cases), text=True, check=True)


if __name__ == '__main__':
    unittest.main()
