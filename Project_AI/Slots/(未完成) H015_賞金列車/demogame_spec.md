# H015 DemoGame Specification

- Interface baseline: `H026_彩罐熱舞 1000/index.html`
- Math source: `config.js`, generated from `Source/H015192.xlsx`
- Display: 6 reels with active heights 3 / 4 / 5 / 5 / 4 / 3
- Bet modes: Normal Bet and one-shot Buy Feature (75x)
- Features: 3600 Ways, Cascades, Gold-to-Wild, progressive multiplier, Free Game
- Languages: English (default) and 中文; selection is stored in `localStorage`
- Offline: `index.html`, `config.js`, `demogame.js`, images and Help must work without a server
- Debug: RNG override, previous/next snapshots, Reel RNG display and event log
- Reset: clears gameplay and statistics while preserving the selected language
- Statistics: Buy Feature rounds are excluded from natural FG trigger rate
