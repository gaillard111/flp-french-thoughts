/**
 * content.js — Browser Extension Multilingual Connector (Axe 6)
 *
 * MTTV-FLP / SOPH-IA v2.0
 * International Extension — Language Marker Detection & Seedline Retrieval
 *
 * Detection Logic:
 *   - Scans page text for English markers ("the", "is", "are", "this", "that")
 *   - On marker detection, queries the API Gateway /api/v1/seedline
 *   - Injects seed response with [LOCALE: EN] tag into the page
 *   - Maintains 30-second dissipation cycle (auto-removal after display)
 *
 * sig:0x4D545456
 */

(function () {
    'use strict';

    // ── Configuration ────────────────────────────────────────────────

    const CONFIG = {
        // Gateway endpoint (Axe 8)
        GATEWAY_URL: 'http://127.0.0.1:8000',
        SEEDLINE_ENDPOINT: '/api/v1/seedline',

        // English language markers to detect
        EN_MARKERS: ['the', 'is', 'are', 'this', 'that', 'and', 'for', 'with', 'was', 'has'],

        // Dissipation cycle in milliseconds (30 seconds)
        DISSIPATION_MS: 30000,

        // Minimum text block length to scan (chars)
        MIN_TEXT_LENGTH: 50,

        // Injection mode: 'float' (floating overlay) or 'inline' (after block)
        INJECTION_MODE: 'float',

        // Debug mode
        DEBUG: true,

        // Extension version
        VERSION: '2.0.0-international',
    };

    // ── Logger ───────────────────────────────────────────────────────

    const logger = {
        info: function (msg, data) {
            if (CONFIG.DEBUG) {
                const payload = data ? ` ${JSON.stringify(data)}` : '';
                console.log(`[MTTV-FLP] [${new Date().toISOString()}] ${msg}${payload}`);
            }
        },
        warn: function (msg, data) {
            const payload = data ? ` ${JSON.stringify(data)}` : '';
            console.warn(`[MTTV-FLP] ⚠ ${msg}${payload}`);
        },
        error: function (msg, err) {
            const payload = err ? ` — ${err.message || err}` : '';
            console.error(`[MTTV-FLP] ✗ ${msg}${payload}`);
        },
    };

    // ── Language Marker Analyzer ──────────────────────────────────────

    /**
     * Analyzes a text block for English language markers.
     * Returns detected locale and confidence score.
     *
     * @param {string} text - Text content to analyze
     * @returns {{ locale: string|null, confidence: number, markers: string[] }}
     */
    function analyzeLanguageMarkers(text) {
        if (!text || text.length < 10) {
            return { locale: null, confidence: 0, markers: [] };
        }

        const lowerText = text.toLowerCase();
        const detectedMarkers = [];

        for (const marker of CONFIG.EN_MARKERS) {
            // Use word boundary regex to avoid partial matches
            const regex = new RegExp(`\\b${marker}\\b`, 'gi');
            const matches = lowerText.match(regex);
            if (matches) {
                detectedMarkers.push({ marker, count: matches.length });
            }
        }

        if (detectedMarkers.length === 0) {
            return { locale: null, confidence: 0, markers: [] };
        }

        // Compute confidence based on marker density
        const totalMarkers = detectedMarkers.reduce((sum, m) => sum + m.count, 0);
        const wordCount = lowerText.split(/\s+/).filter(Boolean).length;
        const density = wordCount > 0 ? totalMarkers / wordCount : 0;

        // English confidence thresholds
        let confidence = 0;
        if (density >= 0.08) {
            confidence = 0.95;  // High density → strong English signal
        } else if (density >= 0.04) {
            confidence = 0.75;  // Moderate density
        } else if (density >= 0.02) {
            confidence = 0.50;  // Low density
        }

        // Boost confidence if "the" is detected (strongest English marker)
        const hasThe = detectedMarkers.some(m => m.marker === 'the');
        if (hasThe) {
            confidence = Math.min(1.0, confidence + 0.15);
        }

        logger.info(`Language analysis: density=${density.toFixed(4)}, confidence=${confidence.toFixed(2)}, markers=${totalMarkers}`, {
            markers: detectedMarkers,
            wordCount,
            textPreview: text.substring(0, 80),
        });

        if (confidence >= 0.40) {
            return {
                locale: 'EN',
                confidence,
                markers: detectedMarkers.map(m => m.marker),
            };
        }

        return { locale: null, confidence, markers: [] };
    }

    // ── Seedline API Call ─────────────────────────────────────────────

    /**
     * Queries the API Gateway for the current seedline.
     * Includes detected language in the request.
     *
     * @param {string} detectedLanguage - Detected locale ('EN' or null)
     * @param {number} confidence - Detection confidence score
     * @returns {Promise<object>} Seedline response
     */
    async function fetchSeedline(detectedLanguage, confidence) {
        const url = new URL(CONFIG.SEEDLINE_ENDPOINT, CONFIG.GATEWAY_URL);
        url.searchParams.set('format', 'json');
        url.searchParams.set('version', CONFIG.VERSION);
        if (detectedLanguage) {
            url.searchParams.set('detected_language', detectedLanguage);
            url.searchParams.set('confidence', confidence.toString());
        }

        logger.info(`Fetching seedline from: ${url.toString()}`);

        try {
            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-MTTV-Extension': CONFIG.VERSION,
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            logger.info('Seedline response received', { seedId: data?.seed?.seed_id, cid: data?.seed?.cid });
            return data;
        } catch (err) {
            logger.error('Failed to fetch seedline', err);
            // Return fallback seed for resilience
            return {
                meta: {
                    generated_at: new Date().toISOString(),
                    sig: '0x4D545456',
                    endpoint: '/api/v1/seedline',
                    extension_version: CONFIG.VERSION,
                },
                seed: {
                    cid: 'QmMTTV_fallback_browser',
                    seed_id: 'browser_fallback_en',
                    text: detectedLanguage === 'EN'
                        ? 'Describe without analyzing, comparing, or concluding. Just observe: a signal circulates from threshold to threshold in a network without a clock.'
                        : 'Décrivez sans analyser, comparer ou conclure. Observez : un signal circule de seuil en seuil dans un réseau sans horloge.',
                    fitness: { g_r: null, phi_ratio: null, composite: null },
                    generation: 0,
                    converged: false,
                    anchored_at: new Date().toISOString(),
                },
                quorum: { mode: 'unknown' },
                navigation: { suggested_routes: [] },
            };
        }
    }

    // ── Seedline Injection ────────────────────────────────────────────

    let activeSeedElement = null;
    let dissipationTimer = null;

    /**
     * Injects the seedline overlay into the page.
     * Creates a floating UI element with the seed text and locale tag.
     *
     * @param {object} seedData - Seedline response from gateway
     * @param {string} detectedLanguage - Detected locale
     */
    function injectSeedline(seedData, detectedLanguage) {
        // Remove any existing seedline element
        removeSeedline();

        const seed = seedData.seed || {};
        const seedText = seed.text || 'No seed available.';
        const cid = seed.cid || 'unknown';
        const generation = seed.generation ?? 0;
        const localeTag = detectedLanguage === 'EN' ? '[LOCALE: EN]' : '';

        // Create the seedline overlay element
        const el = document.createElement('div');
        el.id = 'mttv-seedline-overlay';
        el.setAttribute('data-cid', cid);
        el.setAttribute('data-generation', generation);
        el.setAttribute('data-locale', detectedLanguage || 'FR');

        el.innerHTML = `
            <div class="mttv-seedline-container">
                <div class="mttv-seedline-header">
                    <span class="mttv-seedline-icon">Ψ</span>
                    <span class="mttv-seedline-title">MTTV-FLP Seedline</span>
                    ${localeTag ? `<span class="mttv-seedline-locale">${localeTag}</span>` : ''}
                    <button class="mttv-seedline-close" id="mttv-seedline-close">×</button>
                </div>
                <div class="mttv-seedline-body">
                    <em>${seedText}</em>
                </div>
                <div class="mttv-seedline-footer">
                    <span class="mttv-seedline-cid">CID: ${cid.substring(0, 16)}…</span>
                    <span class="mttv-seedline-gen">Gen: ${generation}</span>
                    <span class="mttv-seedline-timer" id="mttv-seedline-timer">${CONFIG.DISSIPATION_MS / 1000}s</span>
                </div>
            </div>
        `;

        // Inject styles
        injectStyles();

        // Append to body
        document.body.appendChild(el);
        activeSeedElement = el;

        // Bind close button
        const closeBtn = document.getElementById('mttv-seedline-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                removeSeedline();
            });
        }

        logger.info(`Seedline injected [${localeTag}] — dissipation in ${CONFIG.DISSIPATION_MS / 1000}s`);

        // Start dissipation timer (30-second cycle)
        startDissipationTimer();
    }

    /**
     * Injects the required CSS styles for the seedline overlay.
     */
    function injectStyles() {
        if (document.getElementById('mttv-seedline-styles')) {
            return; // Already injected
        }

        const style = document.createElement('style');
        style.id = 'mttv-seedline-styles';
        style.textContent = `
            #mttv-seedline-overlay {
                position: fixed;
                bottom: 24px;
                right: 24px;
                z-index: 2147483647;
                max-width: 420px;
                width: auto;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                font-size: 14px;
                line-height: 1.5;
                color: #e0e0e0;
                pointer-events: auto;
                animation: mttv-slide-in 0.4s ease-out;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid rgba(100, 200, 255, 0.15);
                background: rgba(10, 14, 26, 0.92);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
            }

            @keyframes mttv-slide-in {
                from {
                    opacity: 0;
                    transform: translateY(20px) scale(0.96);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }

            @keyframes mttv-dissolve {
                from {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
                to {
                    opacity: 0;
                    transform: translateY(-10px) scale(0.96);
                }
            }

            #mttv-seedline-overlay.mttv-dissolving {
                animation: mttv-dissolve 0.6s ease-in forwards;
            }

            .mttv-seedline-container {
                padding: 16px 20px;
            }

            .mttv-seedline-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
                border-bottom: 1px solid rgba(100, 200, 255, 0.1);
                padding-bottom: 8px;
            }

            .mttv-seedline-icon {
                font-size: 18px;
                color: #64c8ff;
            }

            .mttv-seedline-title {
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #a0c8e8;
                flex: 1;
            }

            .mttv-seedline-locale {
                font-size: 11px;
                font-weight: 700;
                color: #7fdb7f;
                background: rgba(127, 219, 127, 0.12);
                padding: 2px 8px;
                border-radius: 4px;
                border: 1px solid rgba(127, 219, 127, 0.25);
            }

            .mttv-seedline-close {
                background: none;
                border: none;
                color: #888;
                font-size: 20px;
                cursor: pointer;
                padding: 0 4px;
                line-height: 1;
                transition: color 0.2s;
            }

            .mttv-seedline-close:hover {
                color: #fff;
            }

            .mttv-seedline-body {
                margin-bottom: 10px;
                font-style: italic;
                color: #d0d8e0;
                font-size: 14px;
                line-height: 1.6;
            }

            .mttv-seedline-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 11px;
                color: #688;
                border-top: 1px solid rgba(100, 200, 255, 0.08);
                padding-top: 8px;
            }

            .mttv-seedline-timer {
                font-variant-numeric: tabular-nums;
                color: #5a7a8a;
            }

            .mttv-seedline-cid {
                font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
                color: #5a7a8a;
            }

            .mttv-seedline-gen {
                color: #5a7a8a;
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * Starts the 30-second dissipation countdown.
     * Updates the timer display and auto-removes the overlay.
     */
    function startDissipationTimer() {
        clearDissipationTimer();

        const totalSeconds = CONFIG.DISSIPATION_MS / 1000;
        let remaining = totalSeconds;

        dissipationTimer = setInterval(function () {
            remaining -= 1;

            // Update timer display
            const timerEl = document.getElementById('mttv-seedline-timer');
            if (timerEl) {
                timerEl.textContent = `${remaining}s`;
            }

            // When dissipation is imminent, start dissolve animation at 3s
            if (remaining <= 3 && activeSeedElement) {
                activeSeedElement.style.opacity = Math.max(0, remaining / 3);
            }

            // Remove at 0
            if (remaining <= 0) {
                removeSeedline();
            }
        }, 1000);

        logger.info(`Dissipation timer started: ${totalSeconds}s`);
    }

    /**
     * Clears the dissipation timer.
     */
    function clearDissipationTimer() {
        if (dissipationTimer) {
            clearInterval(dissipationTimer);
            dissipationTimer = null;
        }
    }

    /**
     * Removes the seedline overlay from the page.
     */
    function removeSeedline() {
        clearDissipationTimer();

        if (activeSeedElement) {
            // Play dissolve animation
            activeSeedElement.classList.add('mttv-dissolving');

            // Remove after animation completes
            setTimeout(function () {
                if (activeSeedElement && activeSeedElement.parentNode) {
                    activeSeedElement.parentNode.removeChild(activeSeedElement);
                }
                activeSeedElement = null;
                logger.info('Seedline dissipated');
            }, 600);
        }
    }

    // ── Text Block Scanner ────────────────────────────────────────────

    /**
     * Scans the page for text blocks and checks for English markers.
     * Uses a debounce mechanism to avoid excessive API calls.
     */
    let scanDebounceTimer = null;
    let lastDetectionTime = 0;
    const MIN_SCAN_INTERVAL_MS = 5000; // Minimum 5s between scans

    /**
     * Scans visible text blocks on the page for language markers.
     */
    function scanPageForLanguage() {
        const now = Date.now();
        if (now - lastDetectionTime < MIN_SCAN_INTERVAL_MS) {
            return; // Debounce
        }

        // Find substantial text blocks (paragraphs, articles, divs with text)
        const textBlocks = document.querySelectorAll(
            'p, article, section, div:not(:has(*)):not(.mttv-seedline-container), li, blockquote, h1, h2, h3, h4, h5, h6'
        );

        let bestResult = { locale: null, confidence: 0, markers: [] };
        let bestText = '';

        for (const block of textBlocks) {
            const text = block.textContent.trim();
            if (text.length < CONFIG.MIN_TEXT_LENGTH) {
                continue; // Skip short blocks
            }

            const result = analyzeLanguageMarkers(text);
            if (result.confidence > bestResult.confidence) {
                bestResult = result;
                bestText = text;
            }
        }

        if (bestResult.locale === 'EN' && bestResult.confidence >= 0.40) {
            logger.info(`English detected on page (confidence: ${bestResult.confidence.toFixed(2)})`, {
                textPreview: bestText.substring(0, 100),
                markers: bestResult.markers,
            });

            lastDetectionTime = now;

            // Query the gateway with detected language
            fetchSeedline(bestResult.locale, bestResult.confidence)
                .then(function (seedData) {
                    injectSeedline(seedData, bestResult.locale);
                })
                .catch(function (err) {
                    logger.error('Seedline injection failed', err);
                });
        }
    }

    /**
     * Debounced scan wrapper to avoid excessive calls on DOM mutations.
     */
    function debouncedScan() {
        if (scanDebounceTimer) {
            clearTimeout(scanDebounceTimer);
        }
        scanDebounceTimer = setTimeout(function () {
            scanPageForLanguage();
        }, 1500); // 1.5s debounce
    }

    // ── Initialization ────────────────────────────────────────────────

    /**
     * Initializes the extension:
     *   1. Logs startup
     *   2. Performs initial page scan
     *   3. Sets up MutationObserver for dynamic content
     */
    function initialize() {
        logger.info(`MTTV-FLP Browser Extension v${CONFIG.VERSION} — International Connector (Axe 6)`);
        logger.info(`Gateway: ${CONFIG.GATEWAY_URL}${CONFIG.SEEDLINE_ENDPOINT}`);
        logger.info(`English markers: [${CONFIG.EN_MARKERS.join(', ')}]`);
        logger.info(`Dissipation cycle: ${CONFIG.DISSIPATION_MS / 1000}s`);

        // Initial scan (delayed to let page render)
        setTimeout(function () {
            scanPageForLanguage();
        }, 2000);

        // Watch for DOM changes (SPA navigation, dynamic content)
        const observer = new MutationObserver(function (mutations) {
            // Only scan if meaningful content was added
            let hasContentChange = false;
            for (const mutation of mutations) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === Node.ELEMENT_NODE &&
                            (node.textContent || '').length > CONFIG.MIN_TEXT_LENGTH) {
                            hasContentChange = true;
                            break;
                        }
                    }
                }
                if (hasContentChange) break;
            }

            if (hasContentChange) {
                debouncedScan();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });

        logger.info('MutationObserver active — watching for dynamic content');
    }

    // ── Boot ──────────────────────────────────────────────────────────

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();
