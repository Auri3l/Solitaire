/**
 * Solitaire SVG Card Renderer
 * Generates crisp vector SVG markup for card faces, pips, court cards, and card backs.
 */

// SVG Suit Pip Paths (normalized viewBox 0 0 100 100)
export const SUIT_PATHS = {
  H: 'M 50,30 C 50,15 20,5 15,35 C 10,60 50,90 50,90 C 50,90 90,60 85,35 C 80,5 50,15 50,30 Z',
  D: 'M 50,10 L 88,50 L 50,90 L 12,50 Z',
  C: 'M 50,12 C 40,12 36,25 43,33 C 33,30 20,38 23,52 C 26,63 38,65 44,58 C 42,65 38,80 34,88 L 66,88 C 62,80 58,65 56,58 C 62,65 74,63 77,52 C 80,38 67,30 57,33 C 64,25 60,12 50,12 Z',
  S: 'M 50,10 C 45,22 15,50 15,68 C 15,80 28,86 42,78 C 40,82 36,88 32,90 L 68,90 C 64,88 60,82 58,78 C 72,86 85,80 85,68 C 85,50 55,22 50,10 Z'
};

const SUIT_COLORS_HEX = {
  H: '#c62828',
  D: '#c62828',
  C: '#181a1f',
  S: '#181a1f'
};

/**
 * Standard pip positions for card center (x: % of card width, y: % of card height, flip: boolean)
 */
const PIP_CONFIGS = {
  1: [{ x: 50, y: 50, scale: 0.45 }],
  2: [{ x: 50, y: 25 }, { x: 50, y: 75, flip: true }],
  3: [{ x: 50, y: 25 }, { x: 50, y: 50 }, { x: 50, y: 75, flip: true }],
  4: [
    { x: 30, y: 25 }, { x: 70, y: 25 },
    { x: 30, y: 75, flip: true }, { x: 70, y: 75, flip: true }
  ],
  5: [
    { x: 30, y: 25 }, { x: 70, y: 25 },
    { x: 50, y: 50 },
    { x: 30, y: 75, flip: true }, { x: 70, y: 75, flip: true }
  ],
  6: [
    { x: 30, y: 25 }, { x: 70, y: 25 },
    { x: 30, y: 50 }, { x: 70, y: 50 },
    { x: 30, y: 75, flip: true }, { x: 70, y: 75, flip: true }
  ],
  7: [
    { x: 30, y: 25 }, { x: 70, y: 25 },
    { x: 50, y: 37.5 },
    { x: 30, y: 50 }, { x: 70, y: 50 },
    { x: 30, y: 75, flip: true }, { x: 70, y: 75, flip: true }
  ],
  8: [
    { x: 30, y: 22 }, { x: 70, y: 22 },
    { x: 50, y: 36 },
    { x: 30, y: 50 }, { x: 70, y: 50 },
    { x: 50, y: 64, flip: true },
    { x: 30, y: 78, flip: true }, { x: 70, y: 78, flip: true }
  ],
  9: [
    { x: 30, y: 22 }, { x: 70, y: 22 },
    { x: 30, y: 40 }, { x: 70, y: 40 },
    { x: 50, y: 50 },
    { x: 30, y: 60, flip: true }, { x: 70, y: 60, flip: true },
    { x: 30, y: 78, flip: true }, { x: 70, y: 78, flip: true }
  ],
  10: [
    { x: 30, y: 20 }, { x: 70, y: 20 },
    { x: 50, y: 32 },
    { x: 30, y: 40 }, { x: 70, y: 40 },
    { x: 30, y: 60, flip: true }, { x: 70, y: 60, flip: true },
    { x: 50, y: 68, flip: true },
    { x: 30, y: 80, flip: true }, { x: 70, y: 80, flip: true }
  ]
};

/**
 * Returns refined art-deco / geometric court card vector illustration for J, Q, K
 */
function getCourtIllustration(rank, suit, color) {
  const isKing = rank === 13;
  const isQueen = rank === 12;
  const suitPath = SUIT_PATHS[suit];
  const isRed = color === '#c62828';
  const robePrimary = isRed ? '#9e1c24' : '#1b2638';
  const robeSecondary = isRed ? '#c62828' : '#2d3e58';
  const accent = '#d4af37';
  const accentDark = '#9a7518';

  return `
    <g class="court-art" transform="translate(18, 19) scale(0.64)">
      <!-- Ornate Double Court Frame -->
      <rect x="0" y="0" width="100" height="152" rx="6" fill="#faf7f0" stroke="${color}" stroke-width="1.6" opacity="0.9"/>
      <rect x="3.5" y="3.5" width="93" height="145" rx="4" fill="#fdfbf6" stroke="${accent}" stroke-width="1.4"/>
      <!-- Corner Diamond Flourishes -->
      <polygon points="8,8 11,11 8,14 5,11" fill="${accent}"/>
      <polygon points="92,8 95,11 92,14 89,11" fill="${accent}"/>
      <polygon points="8,138 11,141 8,144 5,141" fill="${accent}"/>
      <polygon points="92,138 95,141 92,144 89,141" fill="${accent}"/>

      <!-- Subtle Radial Backdrop -->
      <circle cx="50" cy="76" r="36" fill="${accent}" opacity="0.09"/>
      <circle cx="50" cy="76" r="36" fill="none" stroke="${accent}" stroke-width="0.7" stroke-dasharray="2,2" opacity="0.55"/>

      <!-- Royal Halo / Crest -->
      ${isKing ? `
        <!-- King's Imperial Crown -->
        <path d="M 30,36 L 34,20 L 43,28 L 50,15 L 57,28 L 66,20 L 70,36 Z" fill="${accent}" stroke="${accentDark}" stroke-width="1.3" stroke-linejoin="round"/>
        <rect x="30" y="35" width="40" height="4.5" rx="1.5" fill="${accentDark}"/>
        <circle cx="50" cy="14" r="2.2" fill="${color}"/>
        <circle cx="34" cy="19" r="1.7" fill="${color}"/>
        <circle cx="66" cy="19" r="1.7" fill="${color}"/>
      ` : isQueen ? `
        <!-- Queen's Tiara & Veil -->
        <path d="M 28,44 Q 50,24 72,44" stroke="${accent}" stroke-width="1.5" fill="none" opacity="0.7"/>
        <path d="M 33,36 L 39,23 L 45,30 L 50,18 L 55,30 L 61,23 L 67,36 Z" fill="${accent}" stroke="${accentDark}" stroke-width="1.2" stroke-linejoin="round"/>
        <circle cx="50" cy="17" r="2.2" fill="${color}"/>
        <circle cx="42" cy="31" r="1.4" fill="#ffffff"/>
        <circle cx="58" cy="31" r="1.4" fill="#ffffff"/>
      ` : `
        <!-- Jack's Heraldic Cap & Plume -->
        <path d="M 34,37 C 34,25 66,25 66,37 Z" fill="${robePrimary}" stroke="${accent}" stroke-width="1.4"/>
        <path d="M 32,37 L 68,37" stroke="${accent}" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M 60,28 C 72,15 79,22 72,33 C 68,36 63,34 60,28 Z" fill="${color}" opacity="0.88"/>
        <circle cx="50" cy="31" r="2" fill="${accent}"/>
      `}

      <!-- Stylized Geometric Bust & Collar -->
      <path d="M 37,51 C 37,42 63,42 63,51 L 60,62 C 56,66 44,66 40,62 Z" fill="#f3d6b6" stroke="#c89e74" stroke-width="1.2"/>
      <!-- Regal Collar / Ruff -->
      <polygon points="36,63 50,74 64,63 58,60 50,65 42,60" fill="#ffffff" stroke="${accent}" stroke-width="1.2"/>

      <!-- Layered Royal Mantle / Robes -->
      <path d="M 23,66 C 23,66 18,108 21,141 L 79,141 C 82,108 77,66 77,66 L 63,63 L 50,74 L 37,63 Z" fill="${robePrimary}" stroke="${accent}" stroke-width="1.6"/>
      <path d="M 32,68 L 50,141 L 68,68 L 50,78 Z" fill="${robeSecondary}"/>
      <path d="M 43,72 L 50,141 L 57,72 Z" fill="${accent}" opacity="0.88"/>

      <!-- Center Heraldic Suit Medallion -->
      <circle cx="50" cy="102" r="16" fill="#ffffff" stroke="${accent}" stroke-width="2"/>
      <circle cx="50" cy="102" r="13" fill="none" stroke="${color}" stroke-width="0.8" opacity="0.4"/>
      <g transform="translate(39, 91) scale(0.22)">
        <path d="${suitPath}" fill="${color}"/>
      </g>

      <!-- Scepter / Sword / Rose Accent -->
      ${isKing ? `
        <line x1="20" y1="46" x2="20" y2="136" stroke="${accent}" stroke-width="2.8" stroke-linecap="round"/>
        <circle cx="20" cy="44" r="4.8" fill="${accent}" stroke="${accentDark}" stroke-width="1"/>
        <circle cx="20" cy="44" r="2" fill="${color}"/>
      ` : isQueen ? `
        <line x1="80" y1="52" x2="80" y2="134" stroke="${accent}" stroke-width="2.4" stroke-linecap="round"/>
        <polygon points="80,43 85,50 80,57 75,50" fill="${color}" stroke="${accent}" stroke-width="1"/>
      ` : `
        <line x1="20" y1="48" x2="20" y2="134" stroke="#90a4ae" stroke-width="2.6" stroke-linecap="round"/>
        <polygon points="20,38 25,49 15,49" fill="#cfd8dc" stroke="#607d8b" stroke-width="1"/>
      `}
    </g>
  `;
}

const cardFaceCache = new Map();
let cardBackUid = 0;

/**
 * Generates the full inner SVG content of a face-up playing card.
 * Card coordinate space: 0 0 100 145 (standard 2.5 x 3.5 ratio).
 */
export function getCardFaceSVG(card) {
  if (card && card.id && cardFaceCache.has(card.id)) {
    return cardFaceCache.get(card.id);
  }

  const { rank, suit, color, rankName } = card;
  const hexColor = SUIT_COLORS_HEX[suit];
  const suitPath = SUIT_PATHS[suit];

  let centerContent = '';

  if (rank === 1) {
    const pips = PIP_CONFIGS[1] || [];
    const acePip = pips.map(pip => {
      const scale = pip.scale || 0.45;
      const x = (pip.x / 100) * 100;
      const y = (pip.y / 100) * 145;
      const transform = `translate(${x}, ${y}) scale(${scale}) translate(-50, -50)`;
      return `<path d="${suitPath}" fill="${hexColor}" transform="${transform}"/>`;
    }).join('\n');

    // Ornamental filigree medallion framing the Ace
    centerContent = `
      <circle cx="50" cy="72.5" r="28" fill="none" stroke="#d4af37" stroke-width="1" opacity="0.45"/>
      <circle cx="50" cy="72.5" r="24" fill="none" stroke="${hexColor}" stroke-width="0.6" stroke-dasharray="2,2" opacity="0.25"/>
      ${acePip}
    `;
  } else if (rank >= 2 && rank <= 10) {
    const pips = PIP_CONFIGS[rank] || [];
    centerContent = pips.map(pip => {
      const scale = pip.scale || 0.22;
      const x = (pip.x / 100) * 100;
      const y = (pip.y / 100) * 145;
      const transform = `translate(${x}, ${y}) scale(${scale}) translate(-50, -50) ${pip.flip ? 'rotate(180 50 50)' : ''}`;
      return `<path d="${suitPath}" fill="${hexColor}" transform="${transform}"/>`;
    }).join('\n');
  } else {
    centerContent = getCourtIllustration(rank, suit, hexColor);
  }

  const isTen = rank === 10;
  const fontSize = isTen ? '13' : '15';
  const textX = isTen ? '8.5' : '8';
  const pipX = isTen ? '3.5' : '3';
  const paperId = `paper-${suit}-${rank}`;

  // Top-left and bottom-right corner indices
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="145" viewBox="0 0 100 145" class="card-svg">
      <defs>
        <linearGradient id="${paperId}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#ffffff"/>
          <stop offset="100%" stop-color="#f5f2eb"/>
        </linearGradient>
      </defs>
      <!-- Card Background -->
      <rect width="100" height="145" rx="8" ry="8" fill="url(#${paperId})" class="card-base"/>
      <rect x="0.75" y="0.75" width="98.5" height="143.5" rx="7.5" ry="7.5" fill="none" stroke="#d6d1c7" stroke-width="0.8"/>
      <rect x="2.5" y="2.5" width="95" height="140" rx="5.5" ry="5.5" fill="none" stroke="#ebe7de" stroke-width="0.75"/>

      <!-- Top-Left Corner Index -->
      <g class="corner-index top-left">
        <text x="${textX}" y="18" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="${fontSize}" font-weight="bold" fill="${hexColor}" text-anchor="middle">${rankName}</text>
        <g transform="translate(${pipX}, 20) scale(0.1)">
          <path d="${suitPath}" fill="${hexColor}"/>
        </g>
      </g>

      <!-- Center Pips or Court Art -->
      <g class="card-center">
        ${centerContent}
      </g>

      <!-- Bottom-Right Corner Index (Rotated 180) -->
      <g class="corner-index bottom-right" transform="rotate(180 50 72.5)">
        <text x="${textX}" y="18" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="${fontSize}" font-weight="bold" fill="${hexColor}" text-anchor="middle">${rankName}</text>
        <g transform="translate(${pipX}, 20) scale(0.1)">
          <path d="${suitPath}" fill="${hexColor}"/>
        </g>
      </g>
    </svg>
  `;

  if (card && card.id) {
    cardFaceCache.set(card.id, svg);
  }
  return svg;
}

/**
 * Generates SVG for Card Backs based on selected theme.
 * Uses unique per-instance gradient/pattern IDs so multiple face-down cards never share duplicate DOM IDs.
 */
export function getCardBackSVG(theme = 'classic') {
  const uid = ++cardBackUid;
  switch (theme) {
    case 'filigree':
      return `
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="145" viewBox="0 0 100 145" class="card-back-svg">
          <defs>
            <linearGradient id="goldGrad-${uid}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#ffd700"/>
              <stop offset="50%" stop-color="#b8860b"/>
              <stop offset="100%" stop-color="#daa520"/>
            </linearGradient>
            <radialGradient id="navyBg-${uid}" cx="50%" cy="50%" r="60%">
              <stop offset="0%" stop-color="#1a2a44"/>
              <stop offset="100%" stop-color="#0a1220"/>
            </radialGradient>
          </defs>
          <rect width="100" height="145" rx="8" ry="8" fill="url(#navyBg-${uid})"/>
          <rect x="5" y="5" width="90" height="135" rx="5" fill="none" stroke="url(#goldGrad-${uid})" stroke-width="2"/>
          <rect x="8" y="8" width="84" height="129" rx="3" fill="none" stroke="url(#goldGrad-${uid})" stroke-width="0.75" stroke-dasharray="2,2"/>
          <!-- Central Medallion -->
          <circle cx="50" cy="72.5" r="22" fill="none" stroke="url(#goldGrad-${uid})" stroke-width="2"/>
          <circle cx="50" cy="72.5" r="16" fill="none" stroke="url(#goldGrad-${uid})" stroke-width="1"/>
          <polygon points="50,56 54,68 66,72.5 54,77 50,89 46,77 34,72.5 46,68" fill="url(#goldGrad-${uid})"/>
        </svg>
      `;

    case 'celtic':
      return `
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="145" viewBox="0 0 100 145" class="card-back-svg">
          <defs>
            <radialGradient id="emeraldBg-${uid}" cx="50%" cy="50%" r="60%">
              <stop offset="0%" stop-color="#145228"/>
              <stop offset="100%" stop-color="#0a2a14"/>
            </radialGradient>
          </defs>
          <rect width="100" height="145" rx="8" ry="8" fill="url(#emeraldBg-${uid})"/>
          <rect x="6" y="6" width="88" height="133" rx="4" fill="none" stroke="#d4af37" stroke-width="2"/>
          <!-- Celtic Cross / Knots -->
          <g stroke="#d4af37" stroke-width="2" fill="none" transform="translate(50, 72.5)">
            <circle cx="0" cy="0" r="20"/>
            <path d="M -26,0 L 26,0 M 0,-32 L 0,32"/>
            <circle cx="-14" cy="-14" r="7"/>
            <circle cx="14" cy="-14" r="7"/>
            <circle cx="-14" cy="14" r="7"/>
            <circle cx="14" cy="14" r="7"/>
          </g>
        </svg>
      `;

    case 'neon':
      return `
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="145" viewBox="0 0 100 145" class="card-back-svg">
          <defs>
            <linearGradient id="neonGlow-${uid}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#00f2fe"/>
              <stop offset="100%" stop-color="#4facfe"/>
            </linearGradient>
            <pattern id="hexGrid-${uid}" width="14" height="24" patternUnits="userSpaceOnUse">
              <path d="M 7,0 L 14,4 L 14,12 L 7,16 L 0,12 L 0,4 Z M 7,24 L 14,20 L 14,12 M 0,12 L 0,20 L 7,24" fill="none" stroke="#ff007f" stroke-width="0.8" opacity="0.4"/>
            </pattern>
          </defs>
          <rect width="100" height="145" rx="8" ry="8" fill="#0b0c16"/>
          <rect x="4" y="4" width="92" height="137" rx="6" fill="url(#hexGrid-${uid})"/>
          <rect x="5" y="5" width="90" height="135" rx="5" fill="none" stroke="url(#neonGlow-${uid})" stroke-width="1.8"/>
          <polygon points="50,52 68,72.5 50,93 32,72.5" fill="none" stroke="#ff007f" stroke-width="2"/>
          <polygon points="50,58 62,72.5 50,87 38,72.5" fill="none" stroke="#00f2fe" stroke-width="1.5"/>
        </svg>
      `;

    case 'gradient':
      return `
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="145" viewBox="0 0 100 145" class="card-back-svg">
          <defs>
            <linearGradient id="modGrad-${uid}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#667eea"/>
              <stop offset="100%" stop-color="#764ba2"/>
            </linearGradient>
          </defs>
          <rect width="100" height="145" rx="8" ry="8" fill="url(#modGrad-${uid})"/>
          <rect x="6" y="6" width="88" height="133" rx="5" fill="none" stroke="#ffffff" stroke-width="1.5" opacity="0.6"/>
          <circle cx="50" cy="72.5" r="20" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.8"/>
          <circle cx="50" cy="72.5" r="10" fill="#ffffff" opacity="0.25"/>
        </svg>
      `;

    case 'classic':
    default:
      return `
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="145" viewBox="0 0 100 145" class="card-back-svg">
          <defs>
            <linearGradient id="classicBg-${uid}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#19427a"/>
              <stop offset="100%" stop-color="#0c2347"/>
            </linearGradient>
            <pattern id="cardPattern-${uid}" width="10" height="10" patternUnits="userSpaceOnUse">
              <path d="M 0,5 L 5,0 L 10,5 L 5,10 Z" fill="rgba(255,255,255,0.06)" stroke="rgba(147,197,253,0.22)" stroke-width="0.6"/>
              <circle cx="5" cy="5" r="0.8" fill="rgba(212,175,55,0.28)"/>
            </pattern>
          </defs>
          <rect width="100" height="145" rx="8" ry="8" fill="#faf8f3"/>
          <rect x="4" y="4" width="92" height="137" rx="5" fill="url(#classicBg-${uid})"/>
          <rect x="6" y="6" width="88" height="133" rx="4" fill="url(#cardPattern-${uid})"/>
          <rect x="6" y="6" width="88" height="133" rx="4" fill="none" stroke="rgba(255,255,255,0.75)" stroke-width="1"/>
          <rect x="9" y="9" width="82" height="127" rx="2.5" fill="none" stroke="rgba(212,175,55,0.55)" stroke-width="0.75"/>
          <!-- Center Compass Rosette -->
          <circle cx="50" cy="72.5" r="19" fill="#0d2850" stroke="rgba(212,175,55,0.85)" stroke-width="1.3"/>
          <circle cx="50" cy="72.5" r="15" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="0.75"/>
          <polygon points="50,56 54,68.5 66,72.5 54,76.5 50,89 46,76.5 34,72.5 46,68.5" fill="#faf8f3"/>
          <circle cx="50" cy="72.5" r="3" fill="#d4af37"/>
        </svg>
      `;
  }
}

/**
 * Returns placeholder watermark icon for empty foundation slots.
 */
export function getFoundationPlaceholderSVG(suit) {
  const suitPath = SUIT_PATHS[suit];
  return `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="145" viewBox="0 0 100 145" class="slot-placeholder-svg">
      <rect x="1" y="1" width="98" height="143" rx="8" ry="8" fill="rgba(0,0,0,0.16)" stroke="rgba(255,255,255,0.16)" stroke-width="1.5"/>
      <rect x="5" y="5" width="90" height="135" rx="5" ry="5" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="1"/>
      <circle cx="50" cy="72.5" r="24" fill="rgba(0,0,0,0.12)" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
      <g transform="translate(30, 52.5) scale(0.4)" opacity="0.28">
        <path d="${suitPath}" fill="#ffffff"/>
      </g>
    </svg>
  `;
}

/**
 * Returns placeholder SVG for empty stock slot.
 */
export function getStockPlaceholderSVG() {
  return `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="145" viewBox="0 0 100 145" class="slot-placeholder-svg">
      <rect x="1" y="1" width="98" height="143" rx="8" ry="8" fill="rgba(0,0,0,0.16)" stroke="rgba(255,255,255,0.16)" stroke-width="1.5"/>
      <circle cx="50" cy="72.5" r="24" fill="rgba(0,0,0,0.12)" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
      <g transform="translate(35, 57.5) scale(0.3)" opacity="0.35">
        <!-- Circular reload arrow -->
        <path d="M 50,15 A 35,35 0 1,1 15,50" fill="none" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
        <polygon points="15,30 15,58 43,58" fill="#ffffff"/>
      </g>
    </svg>
  `;
}
