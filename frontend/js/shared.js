import { trackProgressEvent } from './progress-tracker.js';

export { gsap } from 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/+esm';

export const API_BASE = '';

export async function fetchJson(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`Failed to load ${path}`);
    return res.json();
}

export function setupBrand(site, elementId = 'brandLogo') {
    const brandEl = document.getElementById(elementId);
    if (!brandEl) return;
    if (site.logo) {
        brandEl.innerHTML = `<img src="${site.logo}" alt="Logo" />${site.brand}`;
    } else {
        brandEl.innerHTML = `<span class="brand-avatar">${site.brand.charAt(0)}</span>${site.brand}`;
    }
}

export function renderContact(contact) {
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

export function renderContactModal(contact) {
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

export function initContactModal(contact, gsap) {
    const modal = document.getElementById('contactModal');
    const backdrop = document.getElementById('contactModalBackdrop');
    const closeBtn = document.getElementById('contactModalClose');
    const body = document.getElementById('contactModalBody');
    if (!modal || !body) return;

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
    document.getElementById('casesCtaBtn')?.addEventListener('click', openModal);

    closeBtn?.addEventListener('click', closeModal);
    backdrop?.addEventListener('click', closeModal);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('open')) {
            closeModal();
        }
    });
}

export function initHeaderAnimations(gsap) {
    gsap.from('header', {
        y: -60,
        autoAlpha: 0,
        duration: 0.8,
        ease: 'power3.out',
    });
}
