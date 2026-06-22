/**
 * 演示视频：优先 HLS（hls.js / Safari 原生），回退 faststart MP4。
 */

let hlsLibPromise = null;

async function loadHlsLib() {
    if (!hlsLibPromise) {
        hlsLibPromise = import('https://cdn.jsdelivr.net/npm/hls.js@1.5.15/+esm').then((m) => m.default);
    }
    return hlsLibPromise;
}

function markReady(wrap) {
    if (wrap) wrap.classList.add('is-ready');
}

/**
 * @param {HTMLElement} [root]
 * @param {{ onVideoProgress?: (videoId: string, currentTime: number, duration: number) => void }} [options]
 * @returns {Promise<() => void>}
 */
export async function initDemoVideoPlayers(root = document, options = {}) {
    const { onVideoProgress } = options;
    const players = root.querySelectorAll('.demo-video-player');
    const destroyers = [];

    for (const video of players) {
        const wrap = video.closest('.demo-video-wrap');
        const card = video.closest('.demo-video-card');
        const videoId = card?.id?.replace(/^cases-/, '') || '';
        const hlsSrc = (video.dataset.hls || '').trim();
        const mp4Src = (video.dataset.mp4 || '').trim();

        video.removeAttribute('src');
        video.preload = 'none';
        video.playsInline = true;

        const onReady = () => markReady(wrap);
        video.addEventListener('canplay', onReady, { once: true });

        if (onVideoProgress && videoId) {
            let lastTick = 0;
            video.addEventListener('timeupdate', () => {
                const now = Date.now();
                if (now - lastTick < 1000) return;
                lastTick = now;
                if (video.duration && Number.isFinite(video.duration)) {
                    onVideoProgress(videoId, video.currentTime, video.duration);
                }
            });
        }

        if (hlsSrc) {
            if (video.canPlayType('application/vnd.apple.mpegurl')) {
                video.src = hlsSrc;
                destroyers.push(() => {
                    video.removeAttribute('src');
                    video.load();
                });
                continue;
            }

            try {
                const Hls = await loadHlsLib();
                if (Hls.isSupported()) {
                    const hls = new Hls({
                        maxBufferLength: 30,
                        maxMaxBufferLength: 60,
                        startLevel: -1,
                        capLevelToPlayerSize: true,
                        enableWorker: true,
                    });
                    hls.loadSource(hlsSrc);
                    hls.attachMedia(video);
                    hls.on(Hls.Events.ERROR, (_e, data) => {
                        if (data.fatal && mp4Src) {
                            hls.destroy();
                            video.src = mp4Src;
                            video.load();
                        }
                    });
                    destroyers.push(() => hls.destroy());
                    continue;
                }
            } catch (err) {
                console.warn('hls.js 加载失败，回退 MP4', err);
            }
        }

        if (mp4Src) {
            video.preload = 'metadata';
            video.src = mp4Src;
            destroyers.push(() => {
                video.removeAttribute('src');
                video.load();
            });
        }
    }

    return () => destroyers.forEach((fn) => fn());
}
