import { gsap } from 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/+esm';
import { ScrollTrigger } from 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/ScrollTrigger/+esm';
import { ScrollToPlugin } from 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/ScrollToPlugin/+esm';

import {
    fetchJson,
    initContactModal,
    initHeaderAnimations,
    renderContact,
    setupBrand,
} from './shared.js';
import { initProgressTracker } from './progress-tracker.js';
import { initDemoVideoPlayers } from './video-player.js';

const CASES_SECTIONS = ['casesConceptHero', 'casesGallery', 'casesCta'];

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

let galleryItems = [];
let currentIndex = 0;

function renderConceptStats(items) {
    return items.map((item) => `
        <div class="cases-stat-card">
            <div class="cases-stat-value">${item.value}</div>
            <div class="cases-stat-label">${item.label}</div>
        </div>
    `).join('');
}

function renderPillars(items) {
    return items.map((item) => `
        <div class="cases-pillar-card">
            <span class="cases-pillar-icon">${item.icon}</span>
            <h3>${item.title}</h3>
            <p>${item.description}</p>
        </div>
    `).join('');
}

function renderCaseCards(items) {
    return items.map((item) => `
        <article class="case-card" data-index="${item.id - 1}">
            <div class="case-card-img-wrap">
                <img src="${item.image}" alt="${item.title}" loading="lazy" decoding="async" />
            </div>
            <div class="case-card-footer">
                <span class="case-card-num">${String(item.id).padStart(2, '0')}</span>
                <span class="case-card-title">${item.title}</span>
            </div>
        </article>
    `).join('');
}

function renderDemoVideos(items) {
    return items.map((item) => `
        <article class="demo-video-card" id="cases-${item.id}">
            <div class="demo-video-wrap">
                <video
                    class="demo-video-player"
                    data-hls="${item.video_hls || ''}"
                    data-mp4="${item.video || ''}"
                    controls
                    playsinline
                    title="${item.title}"
                ></video>
            </div>
            <div class="demo-video-body">
                <h3 class="project-title">${item.title}</h3>
                <p class="project-result">${item.result || ''}</p>
                <p class="project-desc">${item.description || ''}</p>
                <p class="project-client">对应首页项目：${item.project_title}</p>
            </div>
        </article>
    `).join('');
}

function renderCaseSections(sections) {
    return sections.map((section) => {
        if (section.type === 'videos') {
            return `
                <section class="cases-group cases-group-videos" id="cases-${section.id}">
                    <div class="cases-group-header">
                        <h3 class="cases-group-title">${section.name}</h3>
                        <p class="cases-group-desc">${section.description}</p>
                    </div>
                    <div class="demo-videos-grid">${renderDemoVideos(section.items)}</div>
                </section>
            `;
        }
        return `
            <section class="cases-group cases-group-screenshots" id="cases-${section.id}">
                <div class="cases-group-header">
                    <h3 class="cases-group-title">${section.name}</h3>
                    <p class="cases-group-desc">${section.description}</p>
                </div>
                <div class="cases-grid">${renderCaseCards(section.items)}</div>
            </section>
        `;
    }).join('');
}

function populateConceptSection(data) {
    const { hero, stats, pillars, gallery } = data.cases;

    document.getElementById('casesConceptLabel').textContent = hero.label;
    document.getElementById('casesTitlePrefix').textContent = hero.title_prefix;
    document.getElementById('casesTitleHighlight').textContent = hero.title_highlight;
    document.getElementById('casesTitleSuffix').textContent = hero.title_suffix;
    document.getElementById('casesConceptTagline').textContent = hero.tagline;
    document.getElementById('casesConceptDesc').textContent = hero.description;
    document.getElementById('casesConceptStats').innerHTML = renderConceptStats(stats);
    document.getElementById('casesPillars').innerHTML = renderPillars(pillars);

    document.getElementById('galleryLabel').textContent = gallery.label;
    document.getElementById('galleryTitle').innerHTML =
        `${gallery.title_before}<span>${gallery.title_highlight}</span>${gallery.title_after}`;
    document.getElementById('galleryDesc').textContent = gallery.description;

    const cta = data.cases.cta;
    if (cta) {
        document.getElementById('casesCtaTitle').textContent = cta.title;
        document.getElementById('casesCtaDesc').textContent = cta.description;
        document.getElementById('casesCtaBtn').textContent = cta.button;
    }
}

function initConceptHeroAnimations(hero) {
    const label = document.getElementById('casesConceptLabel');
    const titlePrefix = document.getElementById('casesTitlePrefix');
    const titleHighlight = document.getElementById('casesTitleHighlight');
    const titleSuffix = document.getElementById('casesTitleSuffix');
    const tagline = document.getElementById('casesConceptTagline');
    const desc = document.getElementById('casesConceptDesc');
    const stats = document.getElementById('casesConceptStats');
    const pillars = document.querySelectorAll('.cases-pillar-card');
    const scrollIndicator = document.getElementById('casesScrollIndicator');

    gsap.set([tagline, desc, stats, pillars, scrollIndicator], { autoAlpha: 0, y: 24 });

    const tl = gsap.timeline({ delay: 0.2 });

    tl.from(label, { y: 20, autoAlpha: 0, duration: 0.6, ease: 'power3.out' })
        .from([titlePrefix, titleHighlight, titleSuffix], {
            y: 40,
            autoAlpha: 0,
            duration: 0.7,
            stagger: 0.08,
            ease: 'power3.out',
        }, '-=0.2')
        .to(tagline, { autoAlpha: 1, y: 0, duration: 0.6, ease: 'power2.out' })
        .to(desc, { autoAlpha: 1, y: 0, duration: 0.6, ease: 'power2.out' }, '-=0.3')
        .to(stats, { autoAlpha: 1, y: 0, duration: 0.6, ease: 'power2.out' }, '-=0.3')
        .from('.cases-stat-card', {
            y: 20,
            autoAlpha: 0,
            duration: 0.5,
            stagger: 0.1,
            ease: 'power3.out',
        }, '-=0.4')
        .to(pillars, {
            autoAlpha: 1,
            y: 0,
            duration: 0.5,
            stagger: 0.12,
            ease: 'power2.out',
        }, '-=0.2')
        .to(scrollIndicator, { autoAlpha: 1, y: 0, duration: 0.8, ease: 'power2.out' }, '-=0.1');

    gsap.to(titleHighlight, {
        backgroundPosition: '100% 50%',
        duration: 3,
        ease: 'sine.inOut',
        repeat: -1,
        yoyo: true,
    });
}

function initScrollIndicator() {
    const scrollIndicator = document.getElementById('casesScrollIndicator');
    const mouseWheel = scrollIndicator?.querySelector('.mouse-wheel');
    const gallery = document.getElementById('casesGallery');

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
            scrollTo: { y: gallery, autoKill: false },
            ease: 'power3.inOut',
        });
    });

    ScrollTrigger.create({
        trigger: '#casesConceptHero',
        start: 'bottom center',
        onEnter: () => gsap.to(scrollIndicator, { autoAlpha: 0, duration: 0.3 }),
        onLeaveBack: () => gsap.to(scrollIndicator, { autoAlpha: 1, duration: 0.3 }),
    });
}

function initGalleryScrollAnimations() {
    gsap.from('.cases-gallery-header > *', {
        scrollTrigger: {
            trigger: '#casesGallery',
            start: 'top 80%',
        },
        y: 40,
        autoAlpha: 0,
        duration: 0.8,
        stagger: 0.12,
        ease: 'power3.out',
    });

    ScrollTrigger.batch('.case-card', {
        start: 'top 92%',
        onEnter: (batch) => {
            gsap.from(batch, {
                y: 30,
                autoAlpha: 0,
                duration: 0.6,
                stagger: 0.06,
                ease: 'power3.out',
                overwrite: true,
            });
        },
    });

    ScrollTrigger.batch('.demo-video-card', {
        start: 'top 90%',
        onEnter: (batch) => {
            gsap.from(batch, {
                y: 36,
                autoAlpha: 0,
                duration: 0.7,
                stagger: 0.15,
                ease: 'power3.out',
                overwrite: true,
            });
        },
    });

    gsap.from('.cases-cta-inner > *', {
        scrollTrigger: {
            trigger: '#casesCta',
            start: 'top 85%',
        },
        y: 36,
        autoAlpha: 0,
        duration: 0.7,
        stagger: 0.12,
        ease: 'power3.out',
    });
}

function openLightbox(index, progress, { fromNav = false } = {}) {
    const lightbox = document.getElementById('lightbox');
    const img = document.getElementById('lightboxImg');
    const caption = document.getElementById('lightboxCaption');
    if (!lightbox || !img || !galleryItems.length) return;

    currentIndex = index;
    const item = galleryItems[currentIndex];
    img.src = item.image;
    img.alt = item.title;
    caption.textContent = `${item.title} · ${currentIndex + 1} / ${galleryItems.length}`;
    lightbox.classList.add('open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    if (!fromNav) {
        progress?.trackEvent('lightbox_open', { index: currentIndex, title: item.title });
    }

    gsap.fromTo('.lightbox-panel', { scale: 0.96, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.3, ease: 'power2.out' });
}

function closeLightbox() {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox?.classList.contains('open')) return;

    gsap.to('.lightbox-panel', {
        scale: 0.96,
        autoAlpha: 0,
        duration: 0.2,
        onComplete: () => {
            lightbox.classList.remove('open');
            lightbox.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        },
    });
}

function showLightbox(delta, progress) {
    if (!galleryItems.length) return;
    currentIndex = (currentIndex + delta + galleryItems.length) % galleryItems.length;
    progress?.trackEvent('lightbox_nav', { index: currentIndex, direction: delta > 0 ? 'next' : 'prev' });
    openLightbox(currentIndex, progress, { fromNav: true });
}

function initLightbox(progress) {
    document.getElementById('lightboxClose')?.addEventListener('click', closeLightbox);
    document.getElementById('lightboxBackdrop')?.addEventListener('click', closeLightbox);
    document.getElementById('lightboxPrev')?.addEventListener('click', () => showLightbox(-1, progress));
    document.getElementById('lightboxNext')?.addEventListener('click', () => showLightbox(1, progress));

    document.getElementById('casesGroups')?.addEventListener('click', (e) => {
        const card = e.target.closest('.case-card');
        if (!card) return;
        openLightbox(Number(card.dataset.index), progress);
    });

    document.addEventListener('keydown', (e) => {
        const lightbox = document.getElementById('lightbox');
        if (!lightbox?.classList.contains('open')) return;
        if (e.key === 'Escape') closeLightbox();
        if (e.key === 'ArrowLeft') showLightbox(-1, progress);
        if (e.key === 'ArrowRight') showLightbox(1, progress);
    });
}

async function init() {
    const progress = initProgressTracker({ page: 'cases', path: '/cases', sections: CASES_SECTIONS });

    const data = await fetchJson('/api/cases');
    galleryItems = data.items;

    setupBrand(data.site);
    populateConceptSection(data);
    const videoCount = data.video_count || 0;
    const screenshotCount = data.total || 0;
    document.getElementById('casesCount').textContent =
        videoCount
            ? `${videoCount} 段演示视频 · ${screenshotCount} 张项目交付截图`
            : `共 ${screenshotCount} 张项目交付截图`;
    const sections = data.sections?.length
        ? data.sections
        : [{ id: 'delivery-screenshots', type: 'screenshots', name: '项目交付截图', description: '', items: data.items }];
    document.getElementById('casesGroups').innerHTML = renderCaseSections(sections);
    await initDemoVideoPlayers(document.getElementById('casesGroups'), {
        onVideoProgress: (videoId, currentTime, duration) => {
            progress.trackVideoProgress(videoId, currentTime, duration);
        },
    });

    if (window.location.hash) {
        progress.trackEvent('hash_nav', { hash: window.location.hash });
        requestAnimationFrame(() => {
            const target = document.querySelector(window.location.hash);
            target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }
    document.getElementById('footerContact').innerHTML = renderContact(data.contact);
    document.getElementById('footerCopy').textContent = data.site.copyright;

    initHeaderAnimations(gsap);
    initContactModal(data.contact, gsap);
    initConceptHeroAnimations(data.cases.hero);
    initScrollIndicator();
    initLightbox(progress);
    initGalleryScrollAnimations();
    ScrollTrigger.refresh();
}

init().catch((err) => {
    console.error(err);
    const detail = err && err.message ? `<br><small style="color:#666;">${err.message}</small>` : '';
    document.body.innerHTML =
        `<p style="padding:40px;color:red;">案例页加载失败，请确认后端服务已启动。${detail}</p>`;
});
