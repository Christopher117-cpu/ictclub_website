(function () {
    const toggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('.site-nav');

    if (toggle && nav) {
        toggle.addEventListener('click', function () {
            const isOpen = nav.classList.toggle('open');
            toggle.setAttribute('aria-expanded', String(isOpen));
            toggle.setAttribute('aria-label', isOpen ? 'Close navigation menu' : 'Open navigation menu');
        });

        nav.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                nav.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.setAttribute('aria-label', 'Open navigation menu');
            });
        });
    }

    document.querySelectorAll('[data-audit-created]').forEach(function (entry) {
        const createdAt = Date.parse(entry.getAttribute('data-audit-created'));
        const expiresIn = createdAt + 5 * 60 * 60 * 1000 - Date.now();
        if (!Number.isFinite(createdAt) || expiresIn <= 0) {
            entry.remove();
            return;
        }
        window.setTimeout(function () {
            entry.remove();
        }, expiresIn);
    });
})();
