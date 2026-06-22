/**
 * 管理后台登录页：眼动跟随 + 粒子背景 + 表单提交
 */

function initEyeTracking() {
    const art = document.getElementById('erAuthArt');
    if (!art) return;

    art.dataset.eyeTrackingReady = '1';

    document.addEventListener('mousemove', (e) => {
        const eyes = art.querySelectorAll('.er-auth-eye');
        eyes.forEach((eye) => {
            const rect = eye.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;
            const dx = e.clientX - cx;
            const dy = e.clientY - cy;
            const dist = Math.hypot(dx, dy) || 1;
            const max = 3.5;
            const x = (dx / dist) * Math.min(max, dist / 18);
            const y = (dy / dist) * Math.min(max, dist / 18);
            eye.style.setProperty('--er-eye-x', `${x.toFixed(2)}px`);
            eye.style.setProperty('--er-eye-y', `${y.toFixed(2)}px`);
        });
    });
}

function initParticles() {
    const canvas = document.getElementById('ripple-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let particles = [];
    let animationId = null;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function createParticle(x, y) {
        const colors = ['#FF6B6B', '#D34947', '#4ECDC4', '#45B7D1', '#FFEEAD'];
        return {
            x,
            y,
            vx: (Math.random() - 0.5) * 2,
            vy: (Math.random() - 0.5) * 2,
            life: 1,
            size: Math.random() * 3 + 1,
            color: colors[Math.floor(Math.random() * colors.length)],
        };
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (let i = particles.length - 1; i >= 0; i -= 1) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life -= 0.02;
            p.size *= 0.95;
            if (p.life <= 0 || p.size < 0.1) {
                particles.splice(i, 1);
                continue;
            }
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life;
            ctx.fill();
            ctx.globalAlpha = 1;
        }

        animationId = requestAnimationFrame(animate);
    }

    resize();
    window.addEventListener('resize', resize);

    document.addEventListener('mousemove', (e) => {
        for (let i = 0; i < 2; i += 1) {
            particles.push(createParticle(e.clientX, e.clientY));
        }
        if (!animationId) animate();
    });
}

function getNextUrl() {
    const params = new URLSearchParams(window.location.search);
    const next = params.get('next') || '/progress-dashboard';
    if (!next.startsWith('/') || next.startsWith('//')) {
        return '/progress-dashboard';
    }
    return next;
}

async function handleLogin(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const errorEl = document.getElementById('loginError');
    const submitBtn = document.getElementById('loginBtn');
    const username = form.username.value.trim();
    const password = form.password.value;

    errorEl.classList.remove('visible');
    errorEl.textContent = '';
    submitBtn.disabled = true;

    try {
        const next = getNextUrl();
        const res = await fetch(`/api/admin/login?next=${encodeURIComponent(next)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const detail = data.detail;
            const message = typeof detail === 'string'
                ? detail
                : (Array.isArray(detail) ? detail[0]?.msg : '登录失败');
            throw new Error(message || '登录失败');
        }
        window.location.assign(data.redirect || next);
    } catch (err) {
        errorEl.textContent = err.message || '登录失败，请重试';
        errorEl.classList.add('visible');
        submitBtn.disabled = false;
    }
}

async function redirectIfAuthed() {
    try {
        const res = await fetch('/api/admin/me', { credentials: 'include' });
        if (res.ok) {
            window.location.replace(getNextUrl());
        }
    } catch {
        /* stay on login */
    }
}

initEyeTracking();
initParticles();
document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
redirectIfAuthed();
