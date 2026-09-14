const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
).matches;

const THEME_STORAGE_KEY = "doctor-appointment-theme";

function applyTheme(theme) {
    const isDark = theme === "dark";
    document.documentElement.dataset.theme = isDark ? "dark" : "light";

    const toggle = document.querySelector("[data-theme-toggle]");
    if (toggle) {
        toggle.setAttribute("aria-pressed", String(isDark));
        toggle.setAttribute(
            "aria-label",
            isDark ? "فعال‌کردن حالت روشن" : "فعال‌کردن حالت تیره"
        );

        const label = toggle.querySelector("[data-theme-label]");
        if (label) {
            label.textContent = isDark ? "حالت روشن" : "حالت تیره";
        }

        const icon = toggle.querySelector("[data-theme-icon]");
        if (icon) {
            icon.className = isDark ? "bi bi-sun" : "bi bi-moon-stars";
        }
    }

    const themeColor = document.querySelector('meta[name="theme-color"]');
    if (themeColor) {
        themeColor.setAttribute("content", isDark ? "#0b151e" : "#0f6b6d");
    }
}

function initThemeToggle() {
    const toggle = document.querySelector("[data-theme-toggle]");
    const systemPreference = window.matchMedia("(prefers-color-scheme: dark)");

    applyTheme(document.documentElement.dataset.theme);
    document.documentElement.classList.add("theme-ready");

    if (!toggle) {
        return;
    }

    toggle.addEventListener("click", () => {
        const nextTheme =
            document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        applyTheme(nextTheme);
        try {
            localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
        } catch (error) {
            // Theme still applies for this page when browser storage is unavailable.
        }
    });

    const syncSystemTheme = (event) => {
        try {
            if (localStorage.getItem(THEME_STORAGE_KEY)) {
                return;
            }
        } catch (error) {
            // Follow the live system preference when storage is unavailable.
        }
        applyTheme(event.matches ? "dark" : "light");
    };

    if (typeof systemPreference.addEventListener === "function") {
        systemPreference.addEventListener("change", syncSystemTheme);
    } else {
        systemPreference.addListener(syncSystemTheme);
    }
}

function initRevealMotion() {
    const items = document.querySelectorAll("[data-reveal]");

    if (!items.length || prefersReducedMotion || !("IntersectionObserver" in window)) {
        items.forEach((item) => item.classList.add("is-visible"));
        return;
    }

    const observer = new IntersectionObserver(
        (entries, instance) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                entry.target.classList.add("is-visible");
                instance.unobserve(entry.target);
            });
        },
        {
            threshold: 0.12,
            rootMargin: "0px 0px -24px 0px",
        }
    );

    items.forEach((item) => observer.observe(item));
}

function initHeaderState() {
    const header = document.querySelector(".site-header");

    if (!header) {
        return;
    }

    const updateHeader = () => {
        header.classList.toggle("site-header--scrolled", window.scrollY > 10);
    };

    updateHeader();
    window.addEventListener("scroll", updateHeader, { passive: true });
}

function initPasswordToggles() {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        const targetId = button.getAttribute("data-password-toggle");
        const input = document.getElementById(targetId);

        if (!input) {
            return;
        }

        button.addEventListener("click", () => {
            const isVisible = input.type === "text";
            input.type = isVisible ? "password" : "text";
            button.setAttribute("aria-pressed", String(!isVisible));

            const icon = button.querySelector("i");
            if (icon) {
                icon.className = isVisible ? "bi bi-eye" : "bi bi-eye-slash";
            }
        });
    });
}

function initSlotSelection() {
    const slotRadios = Array.from(document.querySelectorAll("[data-slot-radio]"));

    if (!slotRadios.length) {
        return;
    }

    const syncGroup = (activeRadio) => {
        slotRadios
            .filter(
                (candidate) =>
                    candidate.name === activeRadio.name &&
                    candidate.form === activeRadio.form
            )
            .forEach((candidate) => {
                const chip = candidate.closest(".slot-chip");
                if (chip) {
                    chip.classList.toggle("slot-chip--selected", candidate.checked);
                }
            });
    };

    slotRadios.forEach((radio) => {
        syncGroup(radio);
        radio.addEventListener("change", () => syncGroup(radio));
    });
}

function initBootstrapMobileNav() {
    const navbar = document.getElementById("mainNavbar");

    if (!navbar || typeof bootstrap === "undefined") {
        return;
    }

    navbar.querySelectorAll("a.nav-link").forEach((link) => {
        link.addEventListener("click", () => {
            if (window.innerWidth >= 992 || !navbar.classList.contains("show")) {
                return;
            }

            bootstrap.Collapse.getOrCreateInstance(navbar).hide();
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initThemeToggle();
    initRevealMotion();
    initHeaderState();
    initPasswordToggles();
    initSlotSelection();
    initBootstrapMobileNav();
});
