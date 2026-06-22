/**
 * 浏览进度采集：滚动深度、区块曝光、自定义事件；离开页时 sendBeacon 上报。
 */

const API = '/api/progress';
const SCROLL_THROTTLE_MS = 200;

/** @type {ReturnType<typeof createTrackerState> | null} */
let activeTracker = null;

function createTrackerState(options) {
    const sectionOrder = options.sections || [];
    return {
        sessionId: getSessionId(),
        page: options.page,
        path: options.path || window.location.pathname,
        startedAt: new Date().toISOString(),
        sectionOrder,
        maxScrollPct: 0,
        /** @type {Set<string>} */
        sectionsViewed: new Set(),
        /** @type {Array<Record<string, unknown>>} */
        events: [],
        /** @type {Map<string, Set<number>>} */
        videoMilestones: new Map(),
        scrollTimer: /** @type {ReturnType<typeof setTimeout> | null} */ (null),
        observer: /** @type {IntersectionObserver | null} */ (null),
        destroyed: false,
    };
}

function createSessionId() {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        try {
            return crypto.randomUUID();
        } catch (err) {
            // 非 HTTPS / 非 localhost 时 randomUUID 可能不可用
        }
    }
    return `sess-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

function getSessionId() {
    const key = 'progress_session_id';
    let id = sessionStorage.getItem(key);
    if (!id) {
        id = createSessionId();
        sessionStorage.setItem(key, id);
    }
    return id;
}

function nowIso() {
    return new Date().toISOString();
}

function getDeepestSection(state) {
    const viewed = [...state.sectionsViewed];
    if (!viewed.length) return '';
    const orderMap = Object.fromEntries(state.sectionOrder.map((id, i) => [id, i]));
    return viewed.reduce((best, sid) => {
        const score = orderMap[sid] ?? -1;
        const bestScore = orderMap[best] ?? -1;
        return score > bestScore ? sid : best;
    }, viewed[0]);
}

function buildPayload(state) {
    const started = new Date(state.startedAt).getTime();
    const durationSec = Math.max(0, Math.round((Date.now() - started) / 1000));
    return {
        session_id: state.sessionId,
        page: state.page,
        path: state.path,
        started_at: state.startedAt,
        ended_at: nowIso(),
        max_scroll_pct: state.maxScrollPct,
        sections_viewed: [...state.sectionsViewed],
        deepest_section: getDeepestSection(state),
        section_order: state.sectionOrder,
        events: state.events,
        duration_sec: durationSec,
    };
}

function sendPayload(payload, useBeacon) {
    const body = JSON.stringify(payload);
    if (useBeacon && navigator.sendBeacon) {
        const blob = new Blob([body], { type: 'application/json' });
        navigator.sendBeacon(API, blob);
        return;
    }
    fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        keepalive: true,
    }).catch(() => {});
}

function updateScrollDepth(state) {
    const doc = document.documentElement;
    const scrollTop = window.scrollY || doc.scrollTop;
    const scrollHeight = doc.scrollHeight - window.innerHeight;
    const pct = scrollHeight <= 0 ? 100 : Math.min(100, Math.round((scrollTop / scrollHeight) * 100));
    if (pct > state.maxScrollPct) {
        state.maxScrollPct = pct;
    }
}

function initScrollTracking(state) {
    const onScroll = () => {
        if (state.scrollTimer) return;
        state.scrollTimer = setTimeout(() => {
            state.scrollTimer = null;
            updateScrollDepth(state);
        }, SCROLL_THROTTLE_MS);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    updateScrollDepth(state);
    return () => window.removeEventListener('scroll', onScroll);
}

function initSectionObserver(state, sectionIds) {
    if (!sectionIds.length || typeof IntersectionObserver === 'undefined') {
        return () => {};
    }

    const elements = sectionIds
        .map((id) => document.getElementById(id))
        .filter(Boolean);

    if (!elements.length) return () => {};

    const observer = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                if (!entry.isIntersecting || entry.intersectionRatio < 0.5) continue;
                const sectionId = entry.target.id;
                if (!sectionId || state.sectionsViewed.has(sectionId)) continue;
                state.sectionsViewed.add(sectionId);
                state.events.push({
                    type: 'section_enter',
                    section: sectionId,
                    at: nowIso(),
                });
            }
        },
        { threshold: [0.5] },
    );

    elements.forEach((el) => observer.observe(el));
    state.observer = observer;
    return () => observer.disconnect();
}

function initUnloadFlush(state) {
    const flush = () => {
        if (state.destroyed) return;
        updateScrollDepth(state);
        sendPayload(buildPayload(state), true);
    };

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') flush();
    });
    window.addEventListener('pagehide', flush);

    return flush;
}

/**
 * @param {{ page: string, path?: string, sections?: string[] }} options
 */
export function initProgressTracker(options) {
    if (activeTracker) {
        activeTracker.destroyed = true;
        activeTracker.observer?.disconnect();
    }

    const state = createTrackerState(options);
    activeTracker = state;

    const cleanups = [
        initScrollTracking(state),
        initSectionObserver(state, options.sections || []),
    ];
    const flushOnLeave = initUnloadFlush(state);

    const api = {
        trackSectionView(sectionId) {
            if (!sectionId || state.sectionsViewed.has(sectionId)) return;
            state.sectionsViewed.add(sectionId);
            state.events.push({
                type: 'section_enter',
                section: sectionId,
                at: nowIso(),
            });
        },

        trackEvent(type, payload = {}) {
            state.events.push({ type, ...payload, at: nowIso() });
        },

        trackVideoProgress(videoId, currentTime, duration) {
            if (!videoId || !duration || !Number.isFinite(duration)) return;
            const pct = Math.min(100, Math.round((currentTime / duration) * 100));
            const milestones = [25, 50, 75, 100];
            if (!state.videoMilestones.has(videoId)) {
                state.videoMilestones.set(videoId, new Set());
            }
            const reached = state.videoMilestones.get(videoId);
            for (const milestone of milestones) {
                if (pct >= milestone && !reached.has(milestone)) {
                    reached.add(milestone);
                    state.events.push({
                        type: 'video_progress',
                        video_id: videoId,
                        pct: milestone,
                        at: nowIso(),
                    });
                }
            }
        },

        flush(useBeacon = false) {
            updateScrollDepth(state);
            sendPayload(buildPayload(state), useBeacon);
        },

        destroy() {
            state.destroyed = true;
            cleanups.forEach((fn) => fn());
            state.observer?.disconnect();
            if (activeTracker === state) activeTracker = null;
        },
    };

    return api;
}

/** 供 shared.js 等模块在 tracker 初始化后上报事件 */
export function trackProgressEvent(type, payload = {}) {
    activeTracker?.events.push({ type, ...payload, at: nowIso() });
}

export function getActiveProgressTracker() {
    return activeTracker;
}
