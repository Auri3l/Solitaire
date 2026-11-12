/**
 * Solitaire Pro 2.0 - Internationalization (i18n) Module
 * Complete dictionary and translation utilities for English (en) and Turkish (tr).
 */

export const SUPPORTED_LANGUAGES = ['en', 'tr'];
export const DEFAULT_LANGUAGE = 'en';

export const TRANSLATIONS = {
  en: {
    // Brand & Header HUD
    brandTitle: 'Solitaire',
    brandSubtitle: 'Pro',
    draw1: 'Draw 1',
    draw3: 'Draw 3',
    score: 'Score',
    moves: 'Moves',
    time: 'Time',
    bankroll: 'Bankroll',
    handNet: 'Hand Net',
    toProfit: 'to Profit',
    pass: 'Pass',
    bet: 'Bet:',
    doubleDown: '⚡ Double Down',
    doubleDownTitle: 'Double Down: 2x Stake Bet & 2x Foundation Payouts (D)',
    buyPass: '🎲 Buy Pass ($20)',
    buyPassTitle: 'Buy 1 Extra Deck Pass',
    cashier: '🏦 Cashier',
    cashierTitle: 'Vegas Cashier: Reload Chips or Reset Bankroll',
    leaderboardTitle: 'High Scores & Leaderboards',

    // Action Buttons
    newGame: 'New Game',
    newGameTitle: 'Start a New Game (N)',
    restart: 'Restart',
    restartTitle: 'Replay this exact deal',
    undo: 'Undo',
    undoTitle: 'Undo last move (Ctrl+Z or U)',
    redo: 'Redo',
    redoTitle: 'Redo move (Ctrl+Y or R)',
    hint: '💡 Hint',
    hintTitle: 'Show best move hint (H)',
    autoComplete: '✨ Auto Complete',
    autoCompleteTitle: 'Auto-complete game (A)',
    soundTitle: 'Toggle Sound (M)',
    soundMutedTitle: 'Muted (M)',
    soundEnabledTitle: 'Sound Effects Enabled (M)',
    settingsTitle: 'Settings',
    statsTitle: 'Statistics',
    rulesTitle: 'How To Play',

    // Board Slots
    stockTitle: 'Stock pile - click to draw or recycle',
    wasteTitle: 'Waste pile',
    foundationsTitle: 'Foundation piles (Hearts, Diamonds, Clubs, Spades)',
    tableauTitle: 'Tableau columns',

    // New Game Modal
    modalNewGameHeader: 'Start New Game',
    newGamePrompt: 'Select the type of deal you want to play:',
    btnSolvable: '🌟 Solvable Deal (Guaranteed Winnable)',
    btnRandom: '🎲 Classic Random Deal',

    // Settings Modal
    modalSettingsHeader: 'Game Settings',
    setLanguageTitle: 'Language',
    setLanguageDesc: 'Choose user interface language',
    setThemeTitle: 'Table Theme',
    setThemeDesc: 'Choose tabletop felt color and atmosphere',
    setCardBackTitle: 'Card Back Design',
    setCardBackDesc: 'Style of card backs',
    setCardSizeTitle: 'Card Size',
    setCardSizeDesc: 'Scale cards for your computer screen',
    setDrawModeTitle: 'Draw Mode',
    setDrawModeDesc: 'Number of cards drawn from stock',
    setScoringTitle: 'Scoring System',
    setScoringDesc: 'Scoring rules applied',
    setVegasBankrollTitle: 'Vegas Bankroll Mode',
    setVegasBankrollDesc: 'Persistent bankroll across games vs standalone deals',
    setVegasStakeTitle: 'Vegas Default Stake',
    setVegasStakeDesc: 'Initial wager and foundation payout scaling',
    setDealTypeTitle: 'Default Deal Type',
    setDealTypeDesc: 'Winnable seeds or pure random',
    setSoundTitle: 'Sound Effects',
    setSoundDesc: 'Procedural card audio synthesis',
    setVolumeTitle: 'Audio Volume',
    setVolumeDesc: 'Adjust sound effects level',
    setHapticsTitle: 'Haptic Feedback',
    setHapticsDesc: 'Vibration on card moves and interactions',
    enabled: 'Enabled',
    btnCancel: 'Cancel',
    btnSaveSettings: 'Save Changes',
    confirmSettingsChange: 'Settings changed. Start a new game with these settings?',

    // Settings Options
    optEmerald: 'Emerald Felt',
    optMidnight: 'Midnight Velvet',
    optCrimson: 'Royal Crimson',
    optObsidian: 'Obsidian Dark',
    optWood: 'Warm Mahogany',
    optTeal: 'Ocean Teal',

    optClassicBack: 'Classic Geometric',
    optFiligreeBack: 'Royal Filigree',
    optCelticBack: 'Emerald Celtic',
    optNeonBack: 'Cyber Neon',
    optGradientBack: 'Modern Gradient',

    optCardAuto: 'Auto (Responsive)',
    optCardNormal: 'Medium (Comfortable)',
    optCardLarge: 'Large (High Visibility)',
    optCardXLarge: 'Extra Large (Maximum Size)',
    optCardCompact: 'Compact (Classic Small)',

    optDraw1: 'Draw 1 (Turn 1)',
    optDraw3: 'Draw 3 (Turn 3)',

    optScoreStandard: 'Standard Klondike',
    optScoreVegas: 'Vegas Rules',
    optScoreNone: 'Casual (No Score)',

    optVegasCumulative: 'Cumulative (Persistent Bankroll)',
    optVegasStandalone: 'Standalone ($52 Buy-in Each Game)',

    optStake1: 'Standard (1x: $52 Bet / $5 Card)',
    optStake2: 'High Roller (2x: $104 Bet / $10 Card)',
    optStake5: 'VIP Whale (5x: $260 Bet / $25 Card)',
    optStake10: 'High Stakes (10x: $520 Bet / $50 Card)',

    optDealSolvable: 'Solvable Deals',
    optDealRandom: 'Random Deals',

    // Statistics Modal
    modalStatsHeader: 'Game Statistics',
    tabStandard1: 'Standard (Draw 1)',
    tabStandard3: 'Standard (Draw 3)',
    tabVegas1: 'Vegas (Draw 1)',
    tabVegas3: 'Vegas (Draw 3)',
    statGamesPlayed: 'Games Played',
    statGamesWon: 'Games Won',
    statWinRate: 'Win Rate',
    statCurrentStreak: 'Current Streak',
    statBestStreak: 'Best Streak',
    statBestTime: 'Best Time',
    statBestScore: 'Highest Score',
    statFewestMoves: 'Fewest Moves',
    btnResetStats: 'Reset Statistics',
    btnClose: 'Close',
    confirmResetStats: 'Are you sure you want to reset all game statistics?',

    // Rules Modal
    modalRulesHeader: 'How To Play Solitaire',
    rulesObjectiveHeading: 'Objective',
    rulesObjectiveText: 'The goal is to move all 52 cards into the four Foundation piles at the top right, sorted by suit from Ace up to King (A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K).',
    rulesTableauHeading: 'Tableau Building',
    rulesTableau1: 'Cards in the 7 tableau columns must be stacked in descending numerical rank with alternating colors (e.g., Red 6 on Black 7).',
    rulesTableau2: 'You can move single cards or whole descending alternating sequences together.',
    rulesTableau3: 'Empty tableau columns can only be filled with a King (or a stack headed by a King).',
    rulesTableau4: 'When you uncover a face-down card, click it or move the card above it to flip it face up.',
    rulesStockHeading: 'Stock and Waste',
    rulesStock1: 'Click the Stock pile on the top left to draw cards into the Waste pile.',
    rulesStock2: 'When the Stock is empty, click the empty slot to recycle the Waste pile back into Stock.',
    rulesControlsHeading: 'Controls',
    rulesControls1: 'Drag & Drop: Drag any face-up card or stack to valid destination.',
    rulesControls2: 'Click / Tap: Single click any face-up card to auto-move it to the best legal slot (Foundation first, then Tableau).',
    rulesControls3: 'Auto-Complete: When all face-down cards are uncovered and stock/waste are clear, click the glowing "Auto Complete" button to finish the game automatically!',
    rulesVegasHeading: '🎰 Vegas Solitaire Rules & Risk-Reward',
    rulesVegas1: 'The Buy-in & Goal: You wager $52 to buy the deck (-$52). Each card moved to the Foundation pays out +$5.',
    rulesVegas2: 'Break-Even at 11 Cards: Getting 11 cards into the Foundations yields $55, breaking even and putting you into net profit! Every additional card is pure reward.',
    rulesVegas3: 'Pass Limits: Draw 1 allows 1 pass through the deck (0 recycles). Draw 3 allows 3 passes (2 recycles).',
    rulesVegas4: '⚡ Double Down: Before scoring cards to foundation, click Double Down (or press D) to double your wager and double all payouts ($10 per card). High risk, high reward!',
    rulesVegas5: '🎲 Buy Extra Pass: Ran out of passes? Pay the extra pass fee ($20) to buy one more pass through the deck to hunt down that missing card.',
    rulesVegas6: '🏆 Clearance Jackpot: Clear all 52 cards to earn the +$100 Clearance Jackpot!',
    btnGotIt: 'Got it!',

    // Keyboard Shortcuts Modal
    modalShortcutsHeader: 'Keyboard Shortcuts',
    shortcutUndo: 'Undo Move',
    shortcutRedo: 'Redo Move',
    shortcutHint: 'Show Hint',
    shortcutStock: 'Draw from Stock',
    shortcutNewGame: 'New Game',
    shortcutAutoComplete: 'Auto-Complete',
    shortcutDoubleDown: 'Double Down (Vegas)',
    shortcutToggleSound: 'Toggle Sound',
    shortcutCloseModal: 'Close Modal',

    // Cashier Modal
    modalCashierHeader: '🎰 Vegas Cashier',
    cashierPrompt: 'Manage your Solitaire Vegas bankroll and chips:',
    cashierBalanceLabel: 'Current Bankroll',
    btnReloadChips: '💵 Reload +$500 Chips',
    btnResetChips: '🔄 Reset Bankroll to $500',
    btnDone: 'Done',
    cashierNotEnough: 'Not enough chips for a $${cost} bet. Top up your bankroll to keep playing:',
    btnWatchVideoChips: '🎬 Watch a Video: +$500 Chips',
    btnVideoLoading: '🎬 Video loading, try again shortly',
    btnDailyChips: '🎁 Free Daily Chips: Refill to $500',
    btnDailyChipsUsed: '🎁 Daily Chips: back tomorrow',
    toastVideoNotReady: 'The video is not ready yet. Try again in a moment.',
    toastDailyChips: '🎁 Daily chips claimed! Bankroll refilled to $500.',
    toastDailyChipsUsed: 'Daily chips are only for bankrolls under $500, once a day.',
    toastStakeLowered: 'Bet lowered to $${cost} to match your bankroll.',
    toastStakeLockedDoubleDown: 'The bet can\'t change after Doubling Down.',
    setPrivacyTitle: 'Privacy & Ad Choices',
    setPrivacyDesc: 'Review how ads use your data',
    btnPrivacyOptions: 'Manage',
    setRemoveAdsTitle: 'Remove Ads',
    setRemoveAdsDesc: 'One-time purchase: no banner and no ads between games',
    setAdsRemovedDesc: 'Thanks for your support! Ads are off for good.',
    btnRemoveAdsPrice: 'Remove Ads (${price})',
    btnRemoveAds: 'Remove Ads',
    btnAdsRemoved: '✓ Ads Removed',
    btnRestorePurchase: 'Restore',
    toastAdsRemoved: '🎉 Thank you! Ads are removed.',
    toastPurchaseUnavailable: 'The store isn\'t available right now. Try again later.',
    rulesVegas7: '🏦 Bankroll: Bets come out of your persistent bankroll. Out of chips? Visit the Cashier for free daily chips or more chips.',

    // Victory Modal
    victoryHeading: 'Congratulations! You Won!',
    victoryTime: 'Time',
    victoryMoves: 'Moves',
    victoryScore: 'Final Score',
    victoryVegasReceipt: '🏆 VEGAS PAYOUT SETTLEMENT',
    victoryCasinoReceipt: '🏆 VEGAS PAYOUT SETTLEMENT',
    victoryBuyIn: 'Buy-in Stake:',
    victoryReturns: 'Foundation Returns (52 × payout):',
    victoryJackpot: 'Clearance Jackpot Bonus:',
    victoryExtraPasses: 'Extra Passes Purchased:',
    victoryNetProfit: 'Net Hand Profit:',
    victoryUpdatedBankroll: 'Updated Bankroll:',
    victoryPrompt: 'Click the screen to enjoy the classic card bounce celebration, or play another hand!',
    btnPlayAgain: '🎮 Play Another Game',

    // Bottom Ad Banner
    adBadge: 'AD',
    adTitle: 'Solitaire Pro Mobile',
    adSubtitle: 'Play offline & ad-free with Pro Edition • Free on Google Play',
    adCta: 'Install',
    adClosedMsg: 'Advertisement closed',

    // In-game Toasts & Alerts
    toastNoMoves: 'No more legal moves found!',
    toastBreakEven: '🎉 IN THE MONEY! Break-even reached!',
    toastReloadChips: '💵 Bankroll reloaded with +$500 chips!',
    toastResetChips: '🔄 Bankroll reset to $500.',
    toastDoubleDown: '⚡ DOUBLE DOWN! Bet is now $${buyIn}, Foundation payouts are $${payout}/card!',
    toastExtraPass: '🎲 Extra pass purchased for $${cost}! Waste reshuffled to stock.',
    toastCannotDraw: 'Cannot draw cards',

    // Vegas HUD & Settlement additions
    inTheMoney: '🎉 IN THE MONEY (${net})',
    breakEvenTitle: '${breakEven} cards needed to break even and reach net profit',
    doubleDownActive: '⚡ 2X DOUBLED DOWN',
    buyPassWithCost: '🎲 Buy Pass ($${cost})',
    extraPassesBought: '-$${cost} (${count} bought)',
    bankrollTitle: 'Total accumulated Vegas bankroll across games',
    handNetTitle: 'Net profit/loss on this current deal',
    betStakeTitle: 'Vegas Bet Stake',

    // Leaderboard & Google Play Games
    modalLeaderboardHeader: 'High Scores & Leaderboards',
    tabWeekly: '📅 Weekly Top',
    tabMonthly: '🗓️ Monthly Top',
    tabAllTime: '👑 All-Time Top',
    filterAll: 'All Modes',
    filterStandard: 'Standard',
    filterVegas: 'Vegas',
    filterStandard1: 'Standard (1)',
    filterStandard3: 'Standard (3)',
    filterVegas1: 'Vegas (1)',
    filterVegas3: 'Vegas (3)',
    gpgOffline: 'Offline',
    gpgLevelBadge: 'Google Play Games • Lv. ${level}',
    rankHeader: '#',
    playerHeader: 'Player',
    scoreHeader: 'Score',
    timeHeader: 'Time',
    movesHeader: 'Moves',
    modeHeader: 'Mode',
    dateHeader: 'Date',
    yourBestRank: 'Your Best Standing: #${rank} (${score} pts)',
    noRankYet: 'No scores recorded yet. Win a deal to take your spot!',
    btnChangeName: '✏️ Change Name',
    promptChangeName: 'Enter your player display name:',
    btnViewLeaderboard: '🏆 Leaderboards',
    newHighScoreToast: '🌟 NEW HIGH SCORE! You reached #${rank} on the weekly leaderboard!',
    gpgConnect: '🎮 Connect with Google Play Games',
    gpgConnected: '🟢 Synced with Google Play',
    gpgConnecting: 'Connecting to Google Play...',
    gpgSyncNow: '☁️ Sync Now',
    gpgDisconnect: 'Sign Out',
    gpgOpenLeaderboard: 'Open in Play Games',
    gpgPrompt: 'Connect with Google Play Games to sync your scores across devices and compete on global weekly & monthly leaderboards.',
    gpgSyncedToast: '🎮 Google Play Games: Score synced successfully!',
    statViewLeaderboard: '🏆 View Leaderboards',
    victoryHighScoreBanner: '🌟 NEW HIGH SCORE RECORD!',

    // In-game Confirm Prompts
    confirmRestart: 'Restart this deal from the beginning?',
    gameNumberTitle: 'Game number: tap to copy it or play another number',
    promptGameNumber: 'Game number (copy it, or enter another number to play that game):',
    toastInvalidGameNumber: 'Enter a game number from 1 to 1000000.',

    // Home screen
    homeButtonTitle: 'Home screen',
    homeContinue: '▶ Continue',
    homeKlondike1: 'Klondike · Draw 1',
    homeKlondike1Desc: 'Classic, one card at a time',
    homeKlondike3: 'Klondike · Draw 3',
    homeKlondike3Desc: 'Harder, three cards at a time',
    homeVegas: '💰 Vegas',
    homeVegasDesc: 'Bet chips, $${payout} per card · Bankroll: $${balance}',
    homeModeDraw1: 'Draw 1',
    homeModeDraw3: 'Draw 3',
    homeGameNumber: 'Game no.',
    homeStats: 'Stats',
    homeSettings: 'Settings',
    homeLeaderboard: 'Scores',
    homeRules: 'How to play',
    homeRemoveAds: 'No ads',
    confirmBuyPass: 'No deck passes remaining in Vegas rules! Would you like to buy an extra pass for $${cost}?',
    confirmChangeStake: 'Change default stake to ${stake}x ($${cost})? Start a new game with this stake?',

    // Hint translations
    hintUncoversHidden: ' (uncovers a hidden card!)',
    hintFreesCard: ' (frees a card for Foundation)',
    hintDrawCards: 'Draw cards from Stock',
    hintRecycleStock: 'Recycle waste cards into stock'
  },

  tr: {
    // Brand & Header HUD
    brandTitle: 'Solitaire',
    brandSubtitle: 'Pro',
    draw1: '1 Kart Çek',
    draw3: '3 Kart Çek',
    score: 'Skor',
    moves: 'Hamle',
    time: 'Süre',
    bankroll: 'Kasa',
    handNet: 'El Net',
    toProfit: 'Kâra',
    pass: 'Tur',
    bet: 'Bahis:',
    doubleDown: '⚡ İkiye Katla',
    doubleDownTitle: 'İkiye Katla: 2x Bahis ve 2x Temel Kazancı (D)',
    buyPass: '🎲 Tur Al ($20)',
    buyPassTitle: '1 Ekstra Deste Turu Satın Al',
    cashier: '🏦 Vezne',
    cashierTitle: 'Vegas Veznesi: Fiş Yükle veya Kasayı Sıfırla',
    leaderboardTitle: 'Yüksek Skorlar & Liderlik Tablosu',

    // Action Buttons
    newGame: 'Yeni Oyun',
    newGameTitle: 'Yeni Oyun Başlat (N)',
    restart: 'Yeniden Başlat',
    restartTitle: 'Bu dağıtımı baştan oyna',
    undo: 'Geri Al',
    undoTitle: 'Son hamleyi geri al (Ctrl+Z veya U)',
    redo: 'Yinele',
    redoTitle: 'Hamleyi yinele (Ctrl+Y veya R)',
    hint: '💡 İpucu',
    hintTitle: 'En iyi hamle ipucunu göster (H)',
    autoComplete: '✨ Otomatik Bitir',
    autoCompleteTitle: 'Oyunu otomatik tamamla (A)',
    soundTitle: 'Sesi Aç/Kapat (M)',
    soundMutedTitle: 'Sessiz (M)',
    soundEnabledTitle: 'Ses Efektleri Açık (M)',
    settingsTitle: 'Ayarlar',
    statsTitle: 'İstatistikler',
    rulesTitle: 'Nasıl Oynanır',

    // Board Slots
    stockTitle: 'Deste - kart çekmek veya desteyi yenilemek için tıklayın',
    wasteTitle: 'Atık destesi',
    foundationsTitle: 'Temel seriler (Kupa, Karo, Sinek, Maça)',
    tableauTitle: 'Tablo sütunları',

    // New Game Modal
    modalNewGameHeader: 'Yeni Oyun Başlat',
    newGamePrompt: 'Oynamak istediğiniz dağıtım türünü seçin:',
    btnSolvable: '🌟 Çözülebilir Dağıtım (Garantili Kazanılabilir)',
    btnRandom: '🎲 Klasik Rastgele Dağıtım',

    // Settings Modal
    modalSettingsHeader: 'Oyun Ayarları',
    setLanguageTitle: 'Dil (Language)',
    setLanguageDesc: 'Kullanıcı arayüzü dilini seçin',
    setThemeTitle: 'Masa Teması',
    setThemeDesc: 'Masa çuha rengini ve atmosferini seçin',
    setCardBackTitle: 'Kart Arkası Deseni',
    setCardBackDesc: 'Kart arkalarının görsel stili',
    setCardSizeTitle: 'Kart Boyutu',
    setCardSizeDesc: 'Ekranınıza göre kart ölçeğini ayarlayın',
    setDrawModeTitle: 'Kart Çekme Modu',
    setDrawModeDesc: 'Desteden tek seferde çekilecek kart sayısı',
    setScoringTitle: 'Puanlama Sistemi',
    setScoringDesc: 'Uygulanacak puanlama kuralları',
    setVegasBankrollTitle: 'Vegas Kasa Modu',
    setVegasBankrollDesc: 'Oyunlar arası kalıcı kasa mı yoksa tek el mi?',
    setVegasStakeTitle: 'Vegas Varsayılan Bahis',
    setVegasStakeDesc: 'Başlangıç bahsi ve temel ödeme çarpanı',
    setDealTypeTitle: 'Varsayılan Dağıtım Türü',
    setDealTypeDesc: 'Kazanılabilir eller mi yoksa saf rastgele mi?',
    setSoundTitle: 'Ses Efektleri',
    setSoundDesc: 'İşlemsel kart ses efektleri',
    setVolumeTitle: 'Ses Düzeyi',
    setVolumeDesc: 'Ses efektleri seviyesini ayarlayın',
    setHapticsTitle: 'Dokunsal Geri Bildirim',
    setHapticsDesc: 'Kart hareketlerinde ve dokunuşlarda titreşim',
    enabled: 'Etkin',
    btnCancel: 'İptal',
    btnSaveSettings: 'Değişiklikleri Kaydet',
    confirmSettingsChange: 'Ayarlar değişti. Bu ayarlarla yeni bir oyun başlatılsın mı?',

    // Settings Options
    optEmerald: 'Zümrüt Çuha',
    optMidnight: 'Gece Kadifesi',
    optCrimson: 'Kraliyet Kırmızısı',
    optObsidian: 'Obsidyen Karanlığı',
    optWood: 'Sıcak Maun',
    optTeal: 'Okyanus Camgöbeği',

    optClassicBack: 'Klasik Geometrik',
    optFiligreeBack: 'Kraliyet Telkari',
    optCelticBack: 'Zümrüt Kelt',
    optNeonBack: 'Siber Neon',
    optGradientBack: 'Modern Gradyan',

    optCardAuto: 'Otomatik (Duyarlı)',
    optCardNormal: 'Orta (Rahat)',
    optCardLarge: 'Büyük (Yüksek Görünürlük)',
    optCardXLarge: 'Çok Büyük (Maksimum Boyut)',
    optCardCompact: 'Kompakt (Klasik Küçük)',

    optDraw1: '1 Kart Çek (Tur 1)',
    optDraw3: '3 Kart Çek (Tur 3)',

    optScoreStandard: 'Standart Klondike',
    optScoreVegas: 'Vegas Kuralları',
    optScoreNone: 'Serbest (Puansız)',

    optVegasCumulative: 'Kümülatif (Kalıcı Kasa)',
    optVegasStandalone: 'Bağımsız (Her Oyunda $52 Giriş)',

    optStake1: 'Standart (1x: $52 Bahis / $5 Kart)',
    optStake2: 'Yüksek Bahis (2x: $104 Bahis / $10 Kart)',
    optStake5: 'VIP Balina (5x: $260 Bahis / $25 Kart)',
    optStake10: 'Maksimum (10x: $520 Bahis / $50 Kart)',

    optDealSolvable: 'Çözülebilir Dağıtımlar',
    optDealRandom: 'Rastgele Dağıtımlar',

    // Statistics Modal
    modalStatsHeader: 'Oyun İstatistikleri',
    tabStandard1: 'Standart (1 Kart)',
    tabStandard3: 'Standart (3 Kart)',
    tabVegas1: 'Vegas (1 Kart)',
    tabVegas3: 'Vegas (3 Kart)',
    statGamesPlayed: 'Oynanan Oyunlar',
    statGamesWon: 'Kazanılan Oyunlar',
    statWinRate: 'Kazanma Oranı',
    statCurrentStreak: 'Mevcut Seri',
    statBestStreak: 'En İyi Seri',
    statBestTime: 'En İyi Süre',
    statBestScore: 'En Yüksek Puan',
    statFewestMoves: 'En Az Hamle',
    btnResetStats: 'İstatistikleri Sıfırla',
    btnClose: 'Kapat',
    confirmResetStats: 'Tüm oyun istatistiklerini sıfırlamak istediğinizden emin misiniz?',

    // Rules Modal
    modalRulesHeader: 'Solitaire Nasıl Oynanır',
    rulesObjectiveHeading: 'Amaç',
    rulesObjectiveText: 'Amaç, 52 kartın tamamını sağ üstteki dört Temel desteye, her seriyi As\'tan Papaz\'a (A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K) doğru sıralayarak yerleştirmektir.',
    rulesTableauHeading: 'Tablo Dizilimi',
    rulesTableau1: '7 tablo sütunundaki kartlar, azalan sayısal değerde ve ardışık zıt renklerle (örneğin Siyah 7 üzerine Kırmızı 6) dizilmelidir.',
    rulesTableau2: 'Tek kartları veya kurallara uygun dizilmiş kart gruplarını birlikte taşıyabilirsiniz.',
    rulesTableau3: 'Boşalan tablo sütunlarına yalnızca bir Papaz (veya Papaz ile başlayan bir grup) yerleştirilebilir.',
    rulesTableau4: 'Kapalı bir kartın üzerini açtığınızda, kartı açmak için üzerine tıklayın veya üstündeki kartı taşıyın.',
    rulesStockHeading: 'Deste ve Atık',
    rulesStock1: 'Atık destesine kart açmak için sol üstteki Desteye tıklayın.',
    rulesStock2: 'Deste bittiğinde, atık kartları desteye geri almak için boş yuvaya tıklayın.',
    rulesControlsHeading: 'Kontroller',
    rulesControls1: 'Sürükle & Bırak: Açık herhangi bir kartı veya grubu geçerli bir konuma sürükleyin.',
    rulesControls2: 'Tıkla / Dokun: Açık bir karta tek tıklandığında, otomatik olarak en uygun yuvaya taşınır (önce Temel, sonra Tablo).',
    rulesControls3: 'Otomatik Tamamla: Tüm kapalı kartlar açıldığında ve deste boşaldığında, oyunu tek tıkla bitirmek için parlayan "Otomatik Bitir" düğmesine tıklayın!',
    rulesVegasHeading: '🎰 Vegas Solitaire Kuralları ve Risk-Kazanç',
    rulesVegas1: 'Giriş ve Amaç: Desteyi satın almak için $52 yatırırsınız (-$52). Temele taşınan her kart +$5 kazandırır.',
    rulesVegas2: '11 Kartta Başabaş: Temellere 11 kart yerleştirdiğinizde $55 kazanır, başabaş noktasına ulaşır ve net kâra geçersiniz! Sonraki her kart saf kârdır.',
    rulesVegas3: 'Tur Sınırları: 1 Kart çekmede desteden yalnızca 1 tur hakkınız vardır (0 yenileme). 3 Kart çekmede 3 tur (2 yenileme) verilir.',
    rulesVegas4: '⚡ İkiye Katla: Temellere kart taşımadan önce İkiye Katla\'ya (veya D tuşuna) basarak bahsinizi ve kart kazancınızı ikiye ($10/kart) katlayın. Yüksek risk, yüksek kazanç!',
    rulesVegas5: '🎲 Ekstra Tur Al: Turunuz bitti mi? Eksik kartı bulmak için masa ücretini ($20) ödeyerek desteden bir tur daha satın alın.',
    rulesVegas6: '🏆 Büyük İkramiye (Jackpot): 52 kartın tamamını temizleyerek +$100 Temizleme İkramiyesini kazanın!',
    btnGotIt: 'Anladım!',

    // Keyboard Shortcuts Modal
    modalShortcutsHeader: 'Klavye Kısayolları',
    shortcutUndo: 'Hamleyi Geri Al',
    shortcutRedo: 'Hamleyi Yinele',
    shortcutHint: 'İpucu Göster',
    shortcutStock: 'Desteden Kart Çek',
    shortcutNewGame: 'Yeni Oyun',
    shortcutAutoComplete: 'Otomatik Bitir',
    shortcutDoubleDown: 'İkiye Katla (Vegas)',
    shortcutToggleSound: 'Sesi Aç/Kapat',
    shortcutCloseModal: 'Pencereyi Kapat',

    // Cashier Modal
    modalCashierHeader: '🎰 Vegas Veznesi',
    cashierPrompt: 'Solitaire Vegas kasanızı ve fişlerinizi yönetin:',
    cashierBalanceLabel: 'Mevcut Kasa',
    btnReloadChips: '💵 +$500 Fiş Yükle',
    btnResetChips: '🔄 Kasayı $500 Olarak Sıfırla',
    btnDone: 'Tamam',
    cashierNotEnough: '$${cost} bahis için yeterli fişiniz yok. Oynamaya devam etmek için kasanızı doldurun:',
    btnWatchVideoChips: '🎬 Video İzle: +$500 Fiş',
    btnVideoLoading: '🎬 Video yükleniyor, birazdan tekrar deneyin',
    btnDailyChips: '🎁 Günlük Bedava Fiş: Kasayı $500 Yap',
    btnDailyChipsUsed: '🎁 Günlük Fiş: yarın tekrar',
    toastVideoNotReady: 'Video henüz hazır değil. Birazdan tekrar deneyin.',
    toastDailyChips: '🎁 Günlük fişler alındı! Kasa $500 oldu.',
    toastDailyChipsUsed: 'Günlük fişler günde bir kez, kasa $500 altındayken alınabilir.',
    toastStakeLowered: 'Bahis kasanıza göre $${cost} olarak düşürüldü.',
    toastStakeLockedDoubleDown: 'Katlamadan sonra bahis değiştirilemez.',
    setPrivacyTitle: 'Gizlilik ve Reklam Tercihleri',
    setPrivacyDesc: 'Reklamların verilerinizi nasıl kullandığını yönetin',
    btnPrivacyOptions: 'Yönet',
    setRemoveAdsTitle: 'Reklamları Kaldır',
    setRemoveAdsDesc: 'Tek seferlik satın alma: banner yok, oyunlar arasında reklam yok',
    setAdsRemovedDesc: 'Desteğiniz için teşekkürler! Reklamlar tamamen kapalı.',
    btnRemoveAdsPrice: 'Reklamları Kaldır (${price})',
    btnRemoveAds: 'Reklamları Kaldır',
    btnAdsRemoved: '✓ Reklamlar Kaldırıldı',
    btnRestorePurchase: 'Geri Yükle',
    toastAdsRemoved: '🎉 Teşekkürler! Reklamlar kaldırıldı.',
    toastPurchaseUnavailable: 'Mağaza şu anda kullanılamıyor. Daha sonra tekrar deneyin.',
    rulesVegas7: '🏦 Kasa: Bahisler kalıcı kasanızdan ödenir. Fişiniz mi bitti? Günlük bedava fiş veya daha fazla fiş için Vezneye uğrayın.',

    // Victory Modal
    victoryHeading: 'Tebrikler! Kazandınız!',
    victoryTime: 'Süre',
    victoryMoves: 'Hamle',
    victoryScore: 'Son Skor',
    victoryVegasReceipt: '🏆 VEGAS KAZANÇ MAKBUZU',
    victoryCasinoReceipt: '🏆 VEGAS KAZANÇ MAKBUZU',
    victoryBuyIn: 'Giriş Bahsi:',
    victoryReturns: 'Temel Kazancı (52 × ödeme):',
    victoryJackpot: 'Temizleme İkramiyesi:',
    victoryExtraPasses: 'Satın Alınan Ekstra Turlar:',
    victoryNetProfit: 'Net El Kârı:',
    victoryUpdatedBankroll: 'Güncel Kasa:',
    victoryPrompt: 'Klasik zıplayan kart kutlamasının tadını çıkarmak için ekrana tıklayın veya yeni bir el oynayın!',
    btnPlayAgain: '🎮 Yeni Bir Oyun Oyna',

    // Bottom Ad Banner
    adBadge: 'REKLAM',
    adTitle: 'Solitaire Pro Mobil',
    adSubtitle: 'Google Play\'de ücretsiz • İstediğin zaman internetsiz oyna',
    adCta: 'Yükle',
    adClosedMsg: 'Reklam kapatıldı',

    // In-game Toasts & Alerts
    toastNoMoves: 'Başka yasal hamle bulunamadı!',
    toastBreakEven: '🎉 KÂRDASINIZ! Başabaş noktasına ulaşıldı!',
    toastReloadChips: '💵 Kasa +$500 fiş ile dolduruldu!',
    toastResetChips: '🔄 Kasa $500 olarak sıfırlandı.',
    toastDoubleDown: '⚡ İKİYE KATLANDI! Yeni bahis: $${buyIn}, Temel kazancı: $${payout}/kart!',
    toastExtraPass: '🎲 $${cost} karşılığında ekstra tur satın alındı! Atık desteye karıştırıldı.',
    toastCannotDraw: 'Kart çekilemiyor',

    // Vegas HUD & Settlement additions
    inTheMoney: '🎉 KÂRDASINIZ (${net})',
    breakEvenTitle: 'Kâra geçmek ve başabaş noktasına ulaşmak için ${breakEven} kart gerekli',
    doubleDownActive: '⚡ 2X İKİYE KATLANDI',
    buyPassWithCost: '🎲 Tur Al ($${cost})',
    extraPassesBought: '-$${cost} (${count} adet alındı)',
    bankrollTitle: 'Oyunlar boyunca biriken toplam Vegas kasası',
    handNetTitle: 'Bu dağıtımdaki net kâr/zarar',
    betStakeTitle: 'Vegas Bahis Tutarı',

    // Leaderboard & Google Play Games
    modalLeaderboardHeader: 'Yüksek Skorlar & Liderlik Tablosu',
    tabWeekly: '📅 Haftalık Liderler',
    tabMonthly: '🗓️ Aylık Liderler',
    tabAllTime: '👑 Tüm Zamanlar',
    filterAll: 'Tüm Modlar',
    filterStandard: 'Standart',
    filterVegas: 'Vegas',
    filterStandard1: 'Standart (1)',
    filterStandard3: 'Standart (3)',
    filterVegas1: 'Vegas (1)',
    filterVegas3: 'Vegas (3)',
    gpgOffline: 'Çevrimdışı',
    gpgLevelBadge: 'Google Play Games • Sv. ${level}',
    rankHeader: 'Sıra',
    playerHeader: 'Oyuncu',
    scoreHeader: 'Skor',
    timeHeader: 'Süre',
    movesHeader: 'Hamle',
    modeHeader: 'Mod',
    dateHeader: 'Tarih',
    yourBestRank: 'Sizin En İyi Dereceniz: #${rank} (${score} puan)',
    noRankYet: 'Henüz kayıtlı skorunuz yok. Bir el kazanarak liderlikte yerinizi alın!',
    btnChangeName: '✏️ İsim Değiştir',
    promptChangeName: 'Oyuncu adınızı girin:',
    btnViewLeaderboard: '🏆 Liderlik Tablosu',
    newHighScoreToast: '🌟 YENİ YÜKSEK SKOR! Haftalık liderlik tablosunda #${rank} sıraya yerleştiniz!',
    gpgConnect: '🎮 Google Play Games ile Bağlan',
    gpgConnected: '🟢 Google Play ile Eşitlendi',
    gpgConnecting: 'Google Play\'e bağlanılıyor...',
    gpgSyncNow: '☁️ Şimdi Eşitle',
    gpgDisconnect: 'Çıkış Yap',
    gpgOpenLeaderboard: 'Google Play\'de Aç',
    gpgPrompt: 'Google Play Games ile bağlanarak skorlarınızı cihazlar arasında senkronize edin, haftalık ve aylık liderlik tablolarında yarışın.',
    gpgSyncedToast: '🎮 Google Play Games: Skor başarıyla buluta eşitlendi!',
    statViewLeaderboard: '🏆 Liderlik Tablosuna Git',
    victoryHighScoreBanner: '🌟 YENİ YÜKSEK SKOR BAŞARISI!',

    // In-game Confirm Prompts
    confirmRestart: 'Bu dağıtımı baştan başlatmak istiyor musunuz?',
    gameNumberTitle: 'Oyun numarası: kopyalamak ya da başka bir numarayı oynamak için dokunun',
    promptGameNumber: 'Oyun numarası (kopyalayın ya da o oyunu oynamak için başka bir numara girin):',
    toastInvalidGameNumber: '1 ile 1000000 arasında bir oyun numarası girin.',

    // Home screen
    homeButtonTitle: 'Ana ekran',
    homeContinue: '▶ Devam Et',
    homeKlondike1: 'Klondike · 1 Kart',
    homeKlondike1Desc: 'Klasik, her seferinde bir kart',
    homeKlondike3: 'Klondike · 3 Kart',
    homeKlondike3Desc: 'Daha zor, her seferinde üç kart',
    homeVegas: '💰 Vegas',
    homeVegasDesc: 'Fişle oyna, kart başına $${payout} · Kasa: $${balance}',
    homeModeDraw1: '1 Kart',
    homeModeDraw3: '3 Kart',
    homeGameNumber: 'Oyun no.',
    homeStats: 'İstatistik',
    homeSettings: 'Ayarlar',
    homeLeaderboard: 'Skorlar',
    homeRules: 'Nasıl oynanır',
    homeRemoveAds: 'Reklamsız',
    confirmBuyPass: 'Vegas kurallarında deste turu hakkınız kalmadı! $${cost} karşılığında ekstra tur almak ister misiniz?',
    confirmChangeStake: 'Varsayılan bahsi ${stake}x ($${cost}) olarak değiştirip yeni bir oyun başlatmak istiyor musunuz?',

    // Hint translations
    hintUncoversHidden: ' (gizli bir kartı açığa çıkarır!)',
    hintFreesCard: ' (Temel için bir kartı açığa çıkarır)',
    hintDrawCards: 'Desteden kart çek',
    hintRecycleStock: 'Atık destesini desteye geri dönüştür'
  }
};

/**
 * Translate an English hint description to Turkish when applicable.
 * @param {string} text - Hint text produced by HintEngine
 * @param {string} lang - 'en' | 'tr'
 * @returns {string}
 */
export function translateHint(text, lang = 'en') {
  if (!text || lang === 'en') return text;

  const tr = text.trim();

  // 1. Waste to Foundation: "Move A♥ from Waste to Foundation"
  const mWasteFound = tr.match(/^Move\s+(.+?)\s+from\s+Waste\s+to\s+Foundation(.*)$/i);
  if (mWasteFound) {
    const card = mWasteFound[1];
    const rest = translateHintSuffix(mWasteFound[2]);
    return `${card} kartını Atık destesinden Temele taşı${rest}`;
  }

  // 2. Waste to Tableau: "Move Q♥ from Waste to Tableau"
  const mWasteTab = tr.match(/^Move\s+(.+?)\s+from\s+Waste\s+to\s+Tableau(.*)$/i);
  if (mWasteTab) {
    const card = mWasteTab[1];
    const rest = translateHintSuffix(mWasteTab[2]);
    return `${card} kartını Atık destesinden Tabloya taşı${rest}`;
  }

  // 3. Tableau to Foundation: "Move A♥ to Foundation..."
  const mTabFound = tr.match(/^Move\s+(.+?)\s+to\s+Foundation(.*)$/i);
  if (mTabFound) {
    const card = mTabFound[1];
    const rest = translateHintSuffix(mTabFound[2]);
    return `${card} kartını Temele taşı${rest}`;
  }

  // 4. Move to empty column or empty space:
  // "Move K♠ to empty column..." or "Move K♠ onto empty space..."
  const mEmptyCol = tr.match(/^Move\s+(.+?)\s+(?:onto\s+empty\s+space|to\s+empty\s+column)(.*)$/i);
  if (mEmptyCol) {
    const card = mEmptyCol[1];
    const rest = translateHintSuffix(mEmptyCol[2]);
    return `${card} kartını boş sütuna taşı${rest}`;
  }

  // 5. Tableau to Tableau onto a target: "Move 6♥ onto 7♠..."
  const mOnto = tr.match(/^Move\s+(.+?)\s+onto\s+(.+?)(?:\s+(\(.*\)))?$/i);
  if (mOnto) {
    const card = mOnto[1];
    const target = mOnto[2].trim();
    const rest = mOnto[3] ? translateHintSuffix(mOnto[3]) : '';
    if (target.toLowerCase() === 'empty space' || target.toLowerCase() === 'empty column') {
      return `${card} kartını boş sütuna taşı${rest}`;
    }
    return `${card} kartını ${target} üzerine taşı${rest}`;
  }

  // 6. Stock draw: "Draw cards from Stock (15 remaining)" or "Draw cards from Stock"
  const mDraw = tr.match(/^Draw\s+cards\s+from\s+Stock(?:\s+\((\d+)\s+remaining\))?/i);
  if (mDraw) {
    if (mDraw[1]) {
      return `Desteden kart çek (kalan: ${mDraw[1]})`;
    }
    return TRANSLATIONS.tr.hintDrawCards;
  }

  // 7. Recycle: "Recycle Waste back to Stock" or "Recycle waste cards into stock"
  if (/^Recycle\s+[Ww]aste/i.test(tr)) {
    return TRANSLATIONS.tr.hintRecycleStock;
  }

  return tr;
}

function translateHintSuffix(suffix) {
  if (!suffix) return '';
  const s = suffix.trim();

  // (uncovers a hidden card!)
  if (s.toLowerCase().includes('uncovers a hidden card')) {
    return ' (gizli bir kartı açığa çıkarır!)';
  }

  // (frees 8♦ for Foundation) or (frees a card for Foundation)
  const mFreesCard = s.match(/frees\s+(.+?)\s+for\s+Foundation/i);
  if (mFreesCard) {
    const c = mFreesCard[1].trim();
    if (c.toLowerCase() === 'a card') {
      return ' (Temel için bir kartı açığa çıkarır)';
    }
    return ` (Temel için ${c} kartını açığa çıkarır)`;
  }

  // (frees an empty column for a King)
  if (s.toLowerCase().includes('frees an empty column for a king')) {
    return ' (Papaz için boş bir sütun açar)';
  }

  return s ? ` ${s}` : '';
}

/**
 * Get a translation string by key with optional variable replacements.
 * @param {string} key
 * @param {string} lang
 * @param {Object} [params]
 * @returns {string}
 */
export function t(key, lang = 'en', params = {}) {
  const dict = TRANSLATIONS[lang] || TRANSLATIONS.en;
  let text = dict[key] || TRANSLATIONS.en[key] || key;
  for (const [pKey, pVal] of Object.entries(params)) {
    text = text.replace(new RegExp(`\\$\\{${pKey}\\}`, 'g'), String(pVal));
  }
  return text;
}
