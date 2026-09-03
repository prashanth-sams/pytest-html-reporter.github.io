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

  /* ------------------------------------------------------------ 10. Search
     Client-side, over assets/search-index.json — one record per page section,
     written by tools/build.py. The index is ~370 KB, so it is fetched on the
     first open rather than on every page load, and never at all for a reader
     who does not search. */

  var searchTriggers = $$('.searchbtn');

  if (searchTriggers.length) (function () {
    var root  = searchTriggers[0].getAttribute('data-search-root') || '';
    var index = null;       /* the records, once loaded */
    var state = 'idle';     /* idle | loading | ready | failed */
    var dlg, input, list, empty, active = -1, hits = [], lastFocus = null;

    var MAC = /Mac|iPhone|iPad/.test(navigator.platform || '');
    $$('.searchbtn__mod').forEach(function (el) { if (MAC) el.textContent = '⌘'; });

    var ICON_PAGE    = '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>';
    var ICON_SECTION = '<path d="M4 6h16M4 12h10M4 18h13"/>';

    function svg(paths, cls) {
      return '<svg class="' + cls + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
             'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
             paths + '</svg>';
    }

    function esc(t) {
      return String(t).replace(/[&<>"]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
      });
    }

    /* Escape the term, then wrap the matches — never the other way round, or a
       query of "amp" starts lighting up the entities. */
    function mark(text, terms) {
      if (!terms.length) return esc(text);
      var re = new RegExp('(' + terms.map(function (t) {
        return t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }).join('|') + ')', 'ig');
      var out = '', last = 0, m;
      while ((m = re.exec(text)) !== null) {
        out += esc(text.slice(last, m.index)) + '<mark>' + esc(m[0]) + '</mark>';
        last = m.index + m[0].length;
        if (m[0].length === 0) re.lastIndex++;
      }
      return out + esc(text.slice(last));
    }

    /* --- scoring ---------------------------------------------------------
       Every term has to appear somewhere in the record, so "xdist junit"
       finds the one section about both rather than every section about
       either. Where it appears is what orders the results. */

    /* How often a section says a thing is a fair proxy for whether it is the
       section about that thing — thirty pages mention --html-report, one
       documents it. */
    function count(hay, needle) {
      var n = 0, at = 0;
      while ((at = hay.indexOf(needle, at)) !== -1) { n++; at += needle.length; }
      return n;
    }

    function score(rec, terms) {
      var heading = (rec.h || rec.t).toLowerCase();
      var title   = rec.t.toLowerCase();
      var text    = rec.x.toLowerCase();
      var keys    = ' ' + (rec.k || '') + ' ';
      var total   = 0;

      for (var i = 0; i < terms.length; i++) {
        var q = terms[i], at = heading.indexOf(q), s = 0;
        if (at === 0) s = 100;
        else if (at > 0) s = heading.charAt(at - 1) === ' ' ? 64 : 40;
        else if (title.indexOf(q) !== -1) s = 26;
        /* How much of the heading the term covers. "screenshot" against
           "Screenshots" is nearly all of it; against "Screenshots across
           shards" it is a third, and the shorter heading is the better hit. */
        if (at >= 0) s += Math.round(18 * q.length / heading.length);
        /* A section that names --html-report in its own markup is where the
           flag is documented; a section that mentions it is not. */
        if (keys.indexOf(' ' + q + ' ') !== -1) s += 72;
        else if (q.length > 2 && keys.indexOf(q) !== -1) s += 34;
        var n = count(text, q);
        if (n) s += (s ? 4 : 12) + Math.min(9, (n - 1) * 3);
        if (!s) return 0;
        total += s;
      }
      /* A whole-page record is a fallback for its own sections, not a rival. */
      if (!rec.h) total -= 6;
      return total;
    }

    function snippet(rec, terms) {
      var text = rec.x || '';
      if (!text) return '';
      var low = text.toLowerCase(), at = -1;
      for (var i = 0; i < terms.length && at < 0; i++) at = low.indexOf(terms[i]);
      if (at < 60) return text.slice(0, 190);
      var from = text.lastIndexOf(' ', at - 55) + 1;
      return '…' + text.slice(from, from + 190);
    }

    function collect(terms) {
      var out = [];
      for (var i = 0; i < index.length; i++) {
        var sc = score(index[i], terms);
        if (sc > 0) out.push({ rec: index[i], score: sc, i: i });
      }
      /* Ties keep document order, so a page reads top to bottom in results. */
      out.sort(function (a, b) { return b.score - a.score || a.i - b.i; });
      return out;
    }

    function search(query) {
      var terms = query.toLowerCase().split(/\s+/).filter(Boolean);
      if (!terms.length || !index) return [];

      var out = collect(terms);
      if (!out.length) {
        /* Nothing matched the words as typed. Try their stems, so that
           "installation" still finds the page that says "install". */
        var stems = terms.map(function (t) { return t.length > 5 ? t.slice(0, 5) : t; });
        if (stems.join(' ') !== terms.join(' ')) {
          out = collect(stems);
          terms = stems;
        }
      }
      return out.slice(0, 24).map(function (h) {
        return { rec: h.rec, snippet: snippet(h.rec, terms), terms: terms };
      });
    }

    /* --- rendering ------------------------------------------------------- */

    function render(query) {
      hits = search(query);
      active = hits.length ? 0 : -1;

      if (state === 'loading') return say('Loading the index…');
      if (state === 'failed')  return say('Search could not load. The sidebar has every page.');
      if (!query.trim())       return say('Type to search every page in the documentation.');
      if (!hits.length)        return say('No match for <b>' + esc(query) + '</b>.');

      empty.hidden = true;
      var html = '', page = null;
      hits.forEach(function (h, n) {
        if (h.rec.t !== page) {
          page = h.rec.t;
          html += '<div class="searchdlg__group">' + esc(page) + '</div>';
        }
        var href = root + h.rec.p + (h.rec.a ? '#' + h.rec.a : '');
        html += '<a class="searchhit' + (n === active ? ' is-active' : '') + '" href="' + esc(href) +
                '" data-n="' + n + '">' +
                svg(h.rec.h ? ICON_SECTION : ICON_PAGE, 'searchhit__icon') +
                '<span class="searchhit__body">' +
                  '<span class="searchhit__title">' + mark(h.rec.h || h.rec.t, h.terms) + '</span>' +
                  (h.snippet ? '<span class="searchhit__text">' + mark(h.snippet, h.terms) + '</span>' : '') +
                '</span></a>';
      });
      list.innerHTML = html;
      list.hidden = false;
    }

    function say(html) {
      list.hidden = true;
      list.innerHTML = '';
      empty.hidden = false;
      empty.innerHTML = html;
    }

    function move(step) {
      if (!hits.length) return;
      active = (active + step + hits.length) % hits.length;
      var rows = $$('.searchhit', list);
      rows.forEach(function (r, n) { r.classList.toggle('is-active', n === active); });
      if (rows[active]) rows[active].scrollIntoView({ block: 'nearest' });
    }

    /* --- the dialog ------------------------------------------------------ */

    function build() {
      dlg = document.createElement('div');
      dlg.className = 'searchdlg';
      dlg.hidden = true;
      dlg.setAttribute('role', 'dialog');
      dlg.setAttribute('aria-modal', 'true');
      dlg.setAttribute('aria-label', 'Search the documentation');
      dlg.innerHTML =
        '<div class="searchdlg__scrim"></div>' +
        '<div class="searchdlg__panel">' +
          '<div class="searchdlg__field">' +
            svg('<circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/>', '') +
            '<input class="searchdlg__input" type="search" placeholder="Search the docs…" ' +
              'autocomplete="off" autocorrect="off" spellcheck="false" aria-label="Search query">' +
            '<kbd class="searchdlg__esc">Esc</kbd>' +
          '</div>' +
          '<div class="searchdlg__results" hidden></div>' +
          '<div class="searchdlg__empty"></div>' +
          '<div class="searchdlg__foot">' +
            '<span><kbd>↑</kbd><kbd>↓</kbd> to navigate</span>' +
            '<span><kbd>↵</kbd> to open</span>' +
            '<span><kbd>Esc</kbd> to close</span>' +
          '</div>' +
        '</div>';
      document.body.appendChild(dlg);

      input = $('.searchdlg__input', dlg);
      list  = $('.searchdlg__results', dlg);
      empty = $('.searchdlg__empty', dlg);

      $('.searchdlg__scrim', dlg).addEventListener('click', close);
      input.addEventListener('input', function () { render(input.value); });

      input.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown')      { e.preventDefault(); move(1); }
        else if (e.key === 'ArrowUp')   { e.preventDefault(); move(-1); }
        else if (e.key === 'Enter') {
          var row = $$('.searchhit', list)[active];
          if (row) { e.preventDefault(); go(row.href); }
        } else if (e.key === 'Escape')  { e.preventDefault(); close(); }
      });

      /* A hit on the page you are already reading is just a hash change: no
         reload happens, so nothing would dismiss the dialog on its own. */
      list.addEventListener('click', function (e) {
        if (e.target.closest && e.target.closest('.searchhit')) close();
      });

      /* Pointer over a row makes it the one Enter opens — otherwise the
         keyboard highlight and the mouse disagree about what is selected. */
      list.addEventListener('mousemove', function (e) {
        var row = e.target.closest && e.target.closest('.searchhit');
        if (!row) return;
        var n = +row.getAttribute('data-n');
        if (n === active) return;
        active = n;
        $$('.searchhit', list).forEach(function (r, i) { r.classList.toggle('is-active', i === n); });
      });
    }

    function load() {
      if (state !== 'idle') return;
      state = 'loading';
      fetch(root + 'assets/search-index.json')
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) {
          index = data.d || [];
          state = 'ready';
          if (dlg && !dlg.hidden) render(input.value);
        })
        .catch(function () {
          state = 'failed';
          if (dlg && !dlg.hidden) render(input.value);
        });
    }

    function open(seed) {
      if (!dlg) build();
      load();
      lastFocus = document.activeElement;
      dlg.hidden = false;
      document.body.style.overflow = 'hidden';
      input.value = seed || '';
      render(input.value);
      input.focus();
      input.select();
    }

    function go(href) {
      close();
      location.href = href;
    }

    function close() {
      if (!dlg || dlg.hidden) return;
      dlg.hidden = true;
      document.body.style.overflow = '';
      var back = lastFocus && lastFocus.isConnected && lastFocus !== document.body
        ? lastFocus : searchTriggers[0];
      if (back && back.focus) back.focus();
      /* focus() on something unfocusable is a silent no-op, which would leave
         the caret inside the dialog we have just hidden. */
      if (dlg.contains(document.activeElement)) {
        document.activeElement.blur();
        if (searchTriggers[0]) searchTriggers[0].focus();
      }
    }

    searchTriggers.forEach(function (b) {
      b.addEventListener('click', function () { open(); });
      /* Warm the index on intent, so the first keystroke has it already. */
      b.addEventListener('mouseenter', load, { once: true });
    });

    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        dlg && !dlg.hidden ? close() : open();
        return;
      }
      if (dlg && !dlg.hidden) {
        if (e.key === 'Escape') { e.preventDefault(); close(); }
        return;
      }
      var tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === '/') { e.preventDefault(); open(); }
    });
  })();

  /* --------------------------------------------------------- 11. Keyboard */

  document.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || e.metaKey || e.ctrlKey || e.altKey) return;
    /* Shift+D toggles the theme — a docs-site convention worth keeping. */
    if (e.key === 'D' && e.shiftKey) {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    }
  });
})();
