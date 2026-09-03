/* pytest-html-reporter docs — site behaviour
   Theme, navigation, copy buttons, syntax highlighting, scrollspy, search.
   No dependencies. */
(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------------------------------------------------------- 1. Theme
     The no-flash bootstrap runs inline in <head>; this only wires the button. */

  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }

  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('phr-theme', t); } catch (e) {}
    $$('.theme-toggle').forEach(function (b) {
      b.setAttribute('aria-label', t === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
      b.setAttribute('title', t === 'dark' ? 'Light theme' : 'Dark theme');
    });
  }

  $$('.theme-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  });
  applyTheme(currentTheme());

  /* Follow the OS until the reader picks a side. */
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  var onOS = function (e) {
    var stored = null;
    try { stored = localStorage.getItem('phr-theme'); } catch (err) {}
    if (!stored) applyTheme(e.matches ? 'dark' : 'light');
  };
  if (mq.addEventListener) mq.addEventListener('change', onOS);
  else if (mq.addListener) mq.addListener(onOS);

  /* ------------------------------------------------------ 2. Sticky nav */

  var topbar = $('.topbar');
  if (topbar) {
    var onScroll = function () { topbar.classList.toggle('is-stuck', window.scrollY > 6); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* --------------------------------------------------- 3. Mobile sidebar */

  var sidebar = $('.sidebar');
  var burger  = $('.navburger');
  var scrim   = $('.navscrim');

  function closeNav() {
    if (sidebar) sidebar.classList.remove('is-open');
    if (scrim) scrim.classList.remove('is-open');
    if (burger) burger.setAttribute('aria-expanded', 'false');
  }

  if (burger && sidebar) {
    burger.addEventListener('click', function () {
      var open = sidebar.classList.toggle('is-open');
      if (scrim) scrim.classList.toggle('is-open', open);
      burger.setAttribute('aria-expanded', String(open));
    });
  }
  if (scrim) scrim.addEventListener('click', closeNav);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeNav(); });
  if (sidebar) $$('a', sidebar).forEach(function (a) { a.addEventListener('click', closeNav); });

  /* --------------------------------------------- 4. Syntax highlighting
     Small, deliberate highlighter — enough for shell, python, yaml, ini,
     json and toml, which is everything this site shows. */

  var RULES = {
    shell: [
      [/^(\s*)([#].*)$/gm, '$1<span class="tok-com">$2</span>'],
      [/(^|\n)(\$ )/g, '$1<span class="tok-pmt">$2</span>'],
      [/(&#039;[^&]*?&#039;|&quot;[^&]*?&quot;)/g, '<span class="tok-str">$1</span>'],
      [/(\s)(--?[a-zA-Z][\w-]*)/g, '$1<span class="tok-flg">$2</span>'],
      [/\b(pytest|pip3?|python3?|npm|npx|git|code|export|cd|echo|uv|uvx)\b/g, '<span class="tok-key">$1</span>']
    ],
    python: [
      [/(#.*?)(?=\n|$)/g, '<span class="tok-com">$1</span>'],
      [/(&quot;&quot;&quot;[\s\S]*?&quot;&quot;&quot;|&#039;[^&\n]*?&#039;|&quot;[^&\n]*?&quot;|f&quot;[^&\n]*?&quot;)/g, '<span class="tok-str">$1</span>'],
      [/(@[\w.]+)/g, '<span class="tok-dec">$1</span>'],
      [/\b(def|class|import|from|as|return|with|for|in|if|elif|else|try|except|finally|raise|yield|assert|lambda|pass|None|True|False|not|and|or|async|await|global|while|break|continue)\b/g, '<span class="tok-key">$1</span>'],
      [/\b(\d+\.?\d*)\b/g, '<span class="tok-num">$1</span>']
    ],
    yaml: [
      [/(#.*?)(?=\n|$)/g, '<span class="tok-com">$1</span>'],
      [/^(\s*-?\s*)([\w.$-]+)(:)/gm, '$1<span class="tok-key">$2</span>$3'],
      [/(&#039;[^&\n]*?&#039;|&quot;[^&\n]*?&quot;)/g, '<span class="tok-str">$1</span>'],
      [/(\$\{\{[^}]*\}\})/g, '<span class="tok-dec">$1</span>'],
      [/\b(true|false|null|on|off)\b/g, '<span class="tok-num">$1</span>']
    ],
    ini: [
      [/(^\s*[#;].*?)(?=\n|$)/gm, '<span class="tok-com">$1</span>'],
      [/^(\[.*?\])$/gm, '<span class="tok-dec">$1</span>'],
      [/^(\s*)([\w.-]+)(\s*=)/gm, '$1<span class="tok-key">$2</span>$3']
    ],
    json: [
      [/(&quot;[^&]*?&quot;)(\s*:)/g, '<span class="tok-key">$1</span>$2'],
      [/(:\s*)(&quot;[^&]*?&quot;)/g, '$1<span class="tok-str">$2</span>'],
      [/\b(true|false|null)\b/g, '<span class="tok-num">$1</span>'],
      [/\b(-?\d+\.?\d*)\b/g, '<span class="tok-num">$1</span>']
    ]
  };
  RULES.gherkin = RULES.feature = [
    [/(#.*?)(?=\n|$)/g, '<span class="tok-com">$1</span>'],
    [/^(\s*)(Feature|Background|Scenario Outline|Scenario|Examples|Rule)(:)/gm,
      '$1<span class="tok-dec">$2</span>$3'],
    [/^(\s*)(Given|When|Then|And|But|\*)\b/gm, '$1<span class="tok-key">$2</span>'],
    [/(&quot;[^&\n]*?&quot;|&#039;[^&\n]*?&#039;)/g, '<span class="tok-str">$1</span>'],
    [/(@[\w-]+)/g, '<span class="tok-flg">$1</span>'],
    [/\b(\d+)\b/g, '<span class="tok-num">$1</span>']
  ];
  /* data-lang="output" is deliberate: it says "this is program output, do not
     colour it" rather than leaving the attribute off, which reads as an oversight. */
  RULES.output = null;
  RULES.bash = RULES.sh = RULES.console = RULES.text = RULES.shell;
  RULES.py = RULES.python;
  RULES.yml = RULES.yaml;
  RULES.toml = RULES.cfg = RULES.ini;
  RULES.ts = RULES.js = RULES.json;

  function highlight(el) {
    var lang = (el.getAttribute('data-lang') || '').toLowerCase();
    var rules = RULES[lang];
    if (!rules) return;
    var html = el.innerHTML;
    /* Never re-enter markup we already inserted. */
    if (html.indexOf('<span') !== -1) return;
    rules.forEach(function (r) { html = html.replace(r[0], r[1]); });
    el.innerHTML = html;
  }
  $$('.codeblock pre code').forEach(highlight);

  /* -------------------------------------------------- 5. Copy to clipboard */

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.cssText = 'position:absolute;left:-9999px;top:0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy') ? resolve() : reject(); }
      catch (e) { reject(e); }
      finally { document.body.removeChild(ta); }
    });
  }

  $$('.copybtn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var block = btn.closest('.codeblock');
      var code = block && block.querySelector('pre');
      if (!code) return;
      /* Strip the shell prompt — nobody wants "$ " pasted into their terminal. */
      var text = code.innerText.replace(/^\$ /gm, '').replace(/\s+$/, '');
      copyText(text).then(function () {
        btn.classList.add('is-done');
        var label = btn.querySelector('.copybtn__label');
        var was = label ? label.textContent : null;
        if (label) label.textContent = 'Copied';
        setTimeout(function () {
          btn.classList.remove('is-done');
          if (label && was !== null) label.textContent = was;
        }, 1800);
      }).catch(function () {
        var label = btn.querySelector('.copybtn__label');
        if (label) label.textContent = 'Press ⌘C';
      });
    });
  });

  /* ---------------------------------------------------------- 6. Code tabs */

  $$('.codetabs').forEach(function (group) {
    var tabs   = $$('.codetabs__tab', group);
    var panels = $$('.codetabs__panel', group);
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t, j) {
          t.classList.toggle('is-active', i === j);
          t.setAttribute('aria-selected', String(i === j));
        });
        panels.forEach(function (p, j) { p.hidden = i !== j; });
      });
      tab.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (!d) return;
        e.preventDefault();
        var next = tabs[(i + d + tabs.length) % tabs.length];
        next.focus(); next.click();
      });
    });
  });

  /* ------------------------------------- 7. Heading anchors + TOC scrollspy */

  var main = $('.docmain');
  var toc  = $('.toc');

  if (main) {
    $$('h2[id], h3[id]', main).forEach(function (h) {
      if ($('.anchor', h)) return;
      var a = document.createElement('a');
      a.className = 'anchor';
      a.href = '#' + h.id;
      a.textContent = '#';
      a.setAttribute('aria-label', 'Link to this section');
      h.appendChild(a);
    });
  }

  if (toc && main) {
    var links = $$('a[href^="#"]', toc);
    var targets = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); })
                       .filter(Boolean);

    if (targets.length && 'IntersectionObserver' in window) {
      var visible = new Set();
      var mark = function () {
        var best = null;
        targets.forEach(function (t) { if (visible.has(t.id) && !best) best = t.id; });
        if (!best) {
          /* Nothing in the observer band — fall back to the last heading above the fold. */
          for (var i = targets.length - 1; i >= 0; i--) {
            if (targets[i].getBoundingClientRect().top < 140) { best = targets[i].id; break; }
          }
        }
        links.forEach(function (a) {
          a.classList.toggle('is-active', a.getAttribute('href') === '#' + best);
        });
      };
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) visible.add(e.target.id); else visible.delete(e.target.id);
        });
        mark();
      }, { rootMargin: '-72px 0px -68% 0px', threshold: 0 });
      targets.forEach(function (t) { io.observe(t); });
      window.addEventListener('scroll', mark, { passive: true });
      mark();
    }
  }

  /* ------------------------------------------------------- 8. Reveal on scroll */

  var reveals = $$('.reveal');
  if (reveals.length) {
    if (!('IntersectionObserver' in window) ||
        window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      reveals.forEach(function (el) { el.classList.add('is-in'); });
    } else {
      var ro = new IntersectionObserver(function (entries) {
        entries.forEach(function (e, i) {
          if (!e.isIntersecting) return;
          var el = e.target;
          var delay = parseInt(el.getAttribute('data-delay') || '0', 10);
          setTimeout(function () { el.classList.add('is-in'); }, delay);
          ro.unobserve(el);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: .06 });
      reveals.forEach(function (el) { ro.observe(el); });
      /* Anything still hidden after two seconds is shown regardless: a print
         dialog, a screenshot tool or a headless render may never scroll. */
      setTimeout(function () {
        reveals.forEach(function (el) { el.classList.add('is-in'); });
      }, 2000);
    }
  }

  /* ------------------------------------------- 9. Mark the current sidebar page */

  var here = location.pathname.replace(/index\.html$/, '').replace(/\/$/, '');
  $$('.sidebar__link, .navlinks a').forEach(function (a) {
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) === '#' || /^https?:/.test(href)) return;
    var path = new URL(href, location.href).pathname.replace(/index\.html$/, '').replace(/\/$/, '');
    if (path === here) a.classList.add('is-active');
  });

  /* --------------------------------------------------------- 10. Keyboard */

  document.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || e.metaKey || e.ctrlKey || e.altKey) return;
    /* Shift+D toggles the theme — a docs-site convention worth keeping. */
    if (e.key === 'D' && e.shiftKey) {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    }
  });
})();
