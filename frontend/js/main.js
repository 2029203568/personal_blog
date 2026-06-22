import { gsap } from 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/+esm';
import { ScrollTrigger } from 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/ScrollTrigger/+esm';
import { TextPlugin } from 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/TextPlugin/+esm';
import { ScrollToPlugin } from 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/ScrollToPlugin/+esm';

gsap.registerPlugin(ScrollTrigger, TextPlugin, ScrollToPlugin);

import { initProgressTracker, trackProgressEvent } from './progress-tracker.js';

const INDEX_SECTIONS = ['hero', 'stats', 'skills', 'domain-1', 'projects', 'process'];

const DOMAIN_GRADIENTS = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
];

async function fetchLanding() {
    const res = await fetch('/api/landing');
    if (!res.ok) {
        throw new Error(`接口 /api/landing 返回 ${res.status}，请确认 Nginx 已将 /api/ 反代到后端 8000 端口`);
    }
    return res.json();
}

function renderStats(items) {
    return items.map((item) => `
        <div class="stat-card">
            <div class="stat-value">${item.value}</div>
            <div class="stat-label">${item.label}</div>
            <div class="stat-desc">${item.desc}</div>
        </div>
    `).join('');
}

function renderSkills(items) {
    return items.map((item) => `
        <div class="skill-card">
            <div class="skill-card-header">
                <span class="skill-icon">${item.icon}</span>
                <h3>${item.category}</h3>
            </div>
            <ul class="skill-list">
                ${item.items.map((s) => `<li>${s}</li>`).join('')}
            </ul>
        </div>
    `).join('');
}

function renderDomains(items) {
    return items.map((item, i) => `
        <div class="pain-item ${item.reverse ? 'reverse' : ''}" id="${item.id}">
            <div class="pain-item-img">
                <div class="domain-placeholder" style="background:${DOMAIN_GRADIENTS[i % DOMAIN_GRADIENTS.length]}">
                    <span class="domain-placeholder-text">${item.badge}</span>
                </div>
            </div>
            <div class="pain-item-text">
                <div class="pain-item-badge">${item.badge}</div>
                <h3>${item.title}</h3>
                <p>${item.description}</p>
                <div class="pain-item-tags">
                    ${item.tags.map((tag) => `<span>${tag}</span>`).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

function renderProjects(items) {
    return items.map((item) => `
        <div class="project-card">
            <div class="project-highlight">${item.highlight}</div>
            <h3 class="project-title">${item.title}</h3>
            <span class="project-period">${item.period}</span>
            <p class="project-result">${item.result || ''}</p>
            <p class="project-client">服务：${item.client || '企业客户'}</p>
            <p class="project-desc">${item.description}</p>
            ${item.demo_video || item.demo_anchor ? `
                <a class="project-demo-link" href="/cases#cases-${item.demo_anchor || 'demo-videos'}">查看演示视频 →</a>
            ` : ''}
            <div class="project-tags">
                ${item.tags.map((tag) => `<span>${tag}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

function renderProcess(process) {
    return process.steps.map((step) => `
        <div class="process-step-card">
            <div class="process-step-num">${step.step}</div>
            <h3>${step.title}</h3>
            <p>${step.description}</p>
        </div>
    `).join('');
}

function renderSideNav(items) {
    return items.map((item) => `
        <a href="#${item.id}" data-section="${item.id}">
            <span class="tooltip">${item.label}</span>
        </a>
    `).join('');
}

function renderContact(contact) {
    return `
        <div class="contact-item">
            <span class="contact-label">邮箱</span>
            <a href="mailto:${contact.email}">${contact.email}</a>
        </div>
        <div class="contact-item">
            <span class="contact-label">城市</span>
            <span>${contact.location}</span>
        </div>
    `;
}

function renderContactModal(contact) {
    const wechatQr = contact.wechat_qr || '/assets/wechat-qr.jpg';
    return `
        <div class="contact-modal-info">
            <div class="contact-modal-row">
                <span class="contact-modal-label">邮箱</span>
                <a href="mailto:${contact.email}" class="contact-modal-value">${contact.email}</a>
            </div>
            <div class="contact-modal-row">
                <span class="contact-modal-label">城市</span>
                <span class="contact-modal-value">${contact.location}</span>
            </div>
        </div>
        <div class="contact-modal-wechat">
            <p class="contact-modal-wechat-label">微信扫码添加</p>
            <img src="${wechatQr}" alt="微信二维码" class="contact-modal-qr" loading="eager" />
            <p class="contact-modal-wechat-hint">扫二维码，添加我为朋友</p>
        </div>
    `;
}

function initContactModal(contact) {
    const modal = document.getElementById('contactModal');
    const backdrop = document.getElementById('contactModalBackdrop');
    const closeBtn = document.getElementById('contactModalClose');
    const body = document.getElementById('contactModalBody');

    body.innerHTML = renderContactModal(contact);

    const openModal = () => {
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        trackProgressEvent('contact_modal_open');
        gsap.fromTo('.contact-modal-panel', { y: 30, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.35, ease: 'power3.out' });
        gsap.fromTo('.contact-modal-backdrop', { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.25 });
    };

    const closeModal = () => {
        gsap.to('.contact-modal-panel', {
            y: 20,
            autoAlpha: 0,
            duration: 0.25,
            ease: 'power2.in',
            onComplete: () => {
                modal.classList.remove('open');
                modal.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            },
        });
        gsap.to('.contact-modal-backdrop', { autoAlpha: 0, duration: 0.25 });
    };

    document.getElementById('contactBtn')?.addEventListener('click', openModal);
    closeBtn?.addEventListener('click', closeModal);
    backdrop?.addEventListener('click', closeModal);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('open')) {
            closeModal();
        }
    });

    return { openModal, closeModal };
}

function initHeroAnimations(hero) {
    const titlePrefix = document.getElementById('titlePrefix');
    const gradientWord = document.getElementById('gradientWord');
    const heroPositioning = document.getElementById('heroPositioning');
    const heroSubtitle = document.getElementById('heroSubtitle');
    const heroDesc = document.getElementById('heroDesc');
    const heroCta = document.getElementById('heroCta');
    const titleCursor = document.getElementById('titleCursor');
    const subtitleCursor = document.getElementById('subtitleCursor');

    if (heroPositioning && hero.positioning) {
        heroPositioning.textContent = hero.positioning;
    }

    gsap.set([heroPositioning, heroSubtitle, heroDesc, heroCta], { autoAlpha: 0 });
    gsap.set(heroCta, { y: 15 });
    if (heroPositioning) gsap.set(heroPositioning, { y: 10 });

    const tl = gsap.timeline({ delay: 0.3 });

    tl.to(titlePrefix, {
        duration: hero.title_prefix.length * 0.06,
        text: hero.title_prefix,
        ease: 'none',
    })
        .to(gradientWord, {
            duration: hero.title_highlight.length * 0.06,
            text: hero.title_highlight,
            ease: 'none',
        })
        .to(titleCursor, {
            opacity: 0,
            duration: 0.2,
        })
        .to(heroPositioning, {
            autoAlpha: 1,
            y: 0,
            duration: 0.6,
            ease: 'power2.out',
        })
        .set(heroSubtitle, { autoAlpha: 1 })
        .to('#subtitleText', {
            duration: hero.subtitle.length * 0.08,
            text: hero.subtitle,
            ease: 'none',
        })
        .to(subtitleCursor, {
            opacity: 0,
            duration: 0.2,
        })
        .to(heroDesc, {
            autoAlpha: 1,
            duration: 0.6,
            ease: 'power2.out',
            onStart: () => {
                heroDesc.textContent = hero.description;
            },
        })
        .to(heroCta, {
            autoAlpha: 1,
            y: 0,
            duration: 0.6,
            ease: 'power2.out',
        }, '-=0.2');

    gsap.to(gradientWord, {
        backgroundPosition: '100% 50%',
        duration: 3,
        ease: 'sine.inOut',
        repeat: -1,
        yoyo: true,
    });

    gsap.to(titleCursor, {
        opacity: 0,
        duration: 0.3,
        repeat: -1,
        yoyo: true,
        ease: 'steps(1)',
    });

    gsap.to(subtitleCursor, {
        opacity: 0,
        duration: 0.3,
        repeat: -1,
        yoyo: true,
        ease: 'steps(1)',
        delay: 0.15,
    });
}

function initScrollAnimations() {
    gsap.from('.stat-card', {
        scrollTrigger: {
            trigger: '.stats-section',
            start: 'top 85%',
        },
        y: 30,
        autoAlpha: 0,
        duration: 0.7,
        stagger: 0.12,
        ease: 'power3.out',
    });

    gsap.from('.skills-section .section-header > *', {
        scrollTrigger: {
            trigger: '.skills-section',
            start: 'top 80%',
        },
        y: 40,
        autoAlpha: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
    });

    ScrollTrigger.batch('.skill-card', {
        start: 'top 90%',
        onEnter: (batch) => {
            gsap.from(batch, {
                y: 30,
                autoAlpha: 0,
                duration: 0.7,
                stagger: 0.1,
                ease: 'power3.out',
                overwrite: true,
            });
        },
    });

    gsap.from('.pain-header > *', {
        scrollTrigger: {
            trigger: '.pain-section',
            start: 'top 80%',
        },
        y: 40,
        autoAlpha: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
    });

    gsap.utils.toArray('.pain-item').forEach((item) => {
        gsap.from(item, {
            scrollTrigger: {
                trigger: item,
                start: 'top 85%',
                toggleActions: 'play none none reverse',
            },
            y: 50,
            autoAlpha: 0,
            duration: 0.8,
            ease: 'power3.out',
        });
    });

    gsap.from('.projects-section .section-header > *', {
        scrollTrigger: {
            trigger: '.projects-section',
            start: 'top 80%',
        },
        y: 40,
        autoAlpha: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
    });

    ScrollTrigger.batch('.project-card', {
        start: 'top 90%',
        onEnter: (batch) => {
            gsap.from(batch, {
                y: 30,
                autoAlpha: 0,
                duration: 0.7,
                stagger: 0.1,
                ease: 'power3.out',
                overwrite: true,
            });
        },
    });

    gsap.from('.process-section .section-header > *', {
        scrollTrigger: {
            trigger: '.process-section',
            start: 'top 80%',
        },
        y: 40,
        autoAlpha: 0,
        duration: 0.8,
        stagger: 0.12,
        ease: 'power3.out',
    });

    ScrollTrigger.batch('.process-step-card', {
        start: 'top 90%',
        onEnter: (batch) => {
            gsap.from(batch, {
                y: 30,
                autoAlpha: 0,
                duration: 0.7,
                stagger: 0.12,
                ease: 'power3.out',
                overwrite: true,
            });
        },
    });
}

function initScrollIndicator() {
    const scrollIndicator = document.getElementById('scrollIndicator');
    const mouseWheel = scrollIndicator?.querySelector('.mouse-wheel');

    gsap.from(scrollIndicator, {
        autoAlpha: 0,
        y: 10,
        duration: 1,
        delay: 1,
        ease: 'power2.out',
    });

    if (mouseWheel) {
        gsap.to(mouseWheel, {
            y: 10,
            autoAlpha: 0.3,
            duration: 1,
            repeat: -1,
            yoyo: true,
            ease: 'sine.inOut',
        });
    }

    scrollIndicator?.addEventListener('click', () => {
        gsap.to(window, {
            duration: 1.2,
            scrollTo: { y: '#stats', autoKill: false },
            ease: 'power3.inOut',
        });
    });

    ScrollTrigger.create({
        start: 0,
        end: 100,
        onUpdate: (self) => {
            gsap.to(scrollIndicator, {
                autoAlpha: self.scroll() > 100 ? 0 : 1,
                duration: 0.3,
                overwrite: true,
            });
        },
    });
}

function initSideNav(progress) {
    const sideNav = document.getElementById('sideNav');
    const navLinks = sideNav?.querySelectorAll('a') ?? [];

    ScrollTrigger.create({
        trigger: '#hero',
        start: 'bottom center',
        onEnter: () => sideNav?.classList.add('visible'),
        onLeaveBack: () => sideNav?.classList.remove('visible'),
    });

    navLinks.forEach((link) => {
        const sectionId = link.getAttribute('data-section');
        const target = document.getElementById(sectionId);
        if (!target) return;

        ScrollTrigger.create({
            trigger: target,
            start: 'top center',
            end: 'bottom center',
            onToggle: (self) => {
                if (self.isActive) {
                    navLinks.forEach((l) => l.classList.remove('active'));
                    link.classList.add('active');
                    progress?.trackSectionView(sectionId);
                }
            },
        });

        link.addEventListener('click', (e) => {
            e.preventDefault();
            progress?.trackEvent('nav_click', { section: sectionId });
            gsap.to(window, {
                duration: 1,
                scrollTo: { y: target, autoKill: false },
                ease: 'power3.inOut',
            });
        });
    });
}

function initHeaderAnimations() {
    gsap.from('header', {
        y: -60,
        autoAlpha: 0,
        duration: 0.8,
        ease: 'power3.out',
    });
}

function bindButtons(progress) {
    const scrollToProjects = () => {
        progress?.trackEvent('cta_click', { target: 'projects' });
        gsap.to(window, {
            duration: 1,
            scrollTo: { y: '#projects', autoKill: false },
            ease: 'power3.inOut',
        });
    };

    document.getElementById('ctaBtn')?.addEventListener('click', scrollToProjects);

    document.querySelectorAll('.nav-link').forEach((link) => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href?.startsWith('#')) {
                e.preventDefault();
                progress?.trackEvent('nav_click', { target: href.slice(1) });
                gsap.to(window, {
                    duration: 1,
                    scrollTo: { y: href, autoKill: false },
                    ease: 'power3.inOut',
                });
            }
        });
    });
}

async function init() {
    const progress = initProgressTracker({ page: 'index', path: '/', sections: INDEX_SECTIONS });

    const data = await fetchLanding();

    const brandEl = document.getElementById('brandLogo');
    if (data.site.logo) {
        brandEl.innerHTML = `<img src="${data.site.logo}" alt="Logo" />${data.site.brand}`;
    } else {
        brandEl.innerHTML = `<span class="brand-avatar">${data.site.brand.charAt(0)}</span>${data.site.brand}`;
    }

    document.getElementById('statsGrid').innerHTML = renderStats(data.stats);
    document.getElementById('skillsGrid').innerHTML = renderSkills(data.skills);
    document.getElementById('domainItems').innerHTML = renderDomains(data.domains);
    document.getElementById('projectsGrid').innerHTML = renderProjects(data.projects);
    if (data.projects_section?.intro) {
        document.getElementById('projectsIntro').textContent = data.projects_section.intro;
    }
    if (data.process) {
        document.getElementById('processLabel').textContent = data.process.label;
        document.getElementById('processTitle').innerHTML =
            `${data.process.title_before}<span>${data.process.title_highlight}</span>`;
        document.getElementById('processNote').textContent = data.process.note;
        document.getElementById('processSteps').innerHTML = renderProcess(data.process);
    }
    document.getElementById('sideNav').innerHTML = renderSideNav(data.side_nav);
    document.getElementById('footerContact').innerHTML = renderContact(data.contact);
    document.getElementById('footerCopy').textContent = data.site.copyright;
    document.getElementById('ctaBtn').textContent = data.hero.cta_text;

    initHeaderAnimations();
    initHeroAnimations(data.hero);
    initScrollAnimations();
    initScrollIndicator();
    initSideNav(progress);
    bindButtons(progress);
    initContactModal(data.contact);

    ScrollTrigger.refresh();
}

init().catch((err) => {
    console.error(err);
    const detail = err && err.message ? `<br><small style="color:#666;">${err.message}</small>` : '';
    document.body.innerHTML =
        `<p style="padding:40px;color:red;">页面加载失败，请确认后端服务已启动。${detail}</p>`;
});
