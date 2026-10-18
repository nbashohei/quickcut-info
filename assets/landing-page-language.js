/* Static language URLs remain authoritative. Only the neutral entry may route. */
(() => {
  const script = document.currentScript;
  if (!script) return;
  const base = new URL('../', script.src);
  const paths = {
    en: 'en/', ja: 'ja/', de: 'de/', es: 'es/', fr: 'fr/', it: 'it/',
    ko: 'ko/', 'pt-BR': 'pt-br/', 'zh-Hans': 'zh-hans/', 'zh-Hant': 'zh-hant/',
  };
  const storageKey = 'quickcut.preferredLanguage.v1';
  function language(tag) {
    if (typeof tag !== 'string') return null;
    const parts = tag.trim().toLowerCase().replace(/_/g, '-').split('-');
    if (parts[0] === 'zh') {
      if (parts.includes('hant')) return 'zh-Hant';
      if (parts.includes('hans')) return 'zh-Hans';
      return parts.some(part => ['tw', 'hk', 'mo'].includes(part)) ? 'zh-Hant' : 'zh-Hans';
    }
    if (parts[0] === 'pt') return 'pt-BR';
    return Object.hasOwn(paths, parts[0]) ? parts[0] : null;
  }
  function remember(code) {
    try { localStorage.setItem(storageKey, code); } catch { /* Storage is optional. */ }
  }
  // No interception: normal links still work with JS/storage disabled and in new tabs.
  document.addEventListener('click', event => {
    const link = event.target.closest?.('a[data-language]');
    const code = link?.dataset.language;
    if (Object.hasOwn(paths, code)) remember(code);
  });

  const isEntry = script.dataset.autoLanguage === 'true' &&
    [base.pathname, base.pathname + 'index.html'].includes(location.pathname);
  if (!isEntry) return;

  function route(legacyOnly = false) {
    // Preserve old /#ja and /#zh-Hant links, including same-document navigation.
    let hash = '';
    try { hash = decodeURIComponent(location.hash.slice(1)); } catch { /* Ordinary anchor. */ }
    const explicit = Object.keys(paths).find(code => code.toLowerCase() === hash.toLowerCase());
    if (legacyOnly && !explicit) return;
    let saved = null;
    try {
      const value = localStorage.getItem(storageKey);
      if (Object.hasOwn(paths, value)) saved = value;
    } catch { /* Private/blocked storage: use browser preferences instead. */ }
    const preferences = navigator.languages?.length ? navigator.languages : [navigator.language];
    const detected = Array.from(preferences).map(language).find(Boolean);
    const selected = explicit || saved || detected || 'en';
    if (explicit) remember(explicit);
    // English and unsupported preferences see the already-rendered English HTML.
    if (selected === 'en' && !explicit) return;
    const target = new URL(paths[selected], base);
    target.search = location.search;
    target.hash = explicit ? '' : location.hash;
    document.documentElement.dataset.languageRedirecting = 'true';
    location.replace(target.href);
  }
  window.addEventListener('hashchange', () => route(true));
  route();
})();
