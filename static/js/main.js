const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
).matches;

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
    initRevealMotion();
    initHeaderState();
    initPasswordToggles();
    initBootstrapMobileNav();
});
