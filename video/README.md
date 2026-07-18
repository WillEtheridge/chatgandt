# ChatG&T LinkedIn videos

## Fast teaser — recommended LinkedIn cut

`ChatGntTeaser` is a 20-second, 4:5 teaser built for retention rather than a complete explanation. It keeps the “An AI walked into a bar” opening, gives the product’s “MIXING…” state room to build anticipation, shows one real answer fragment, sets up the prompted-versus-fine-tuned experiment, and moves directly into the Tasting Room challenge.

The sound-on cut uses an original 150 BPM electro/hip-hop score in D minor, with every impact, whoosh, click, shaker fill, glitch and final sting locked to the visual timeline. Both stems are generated locally, with no stock-music dependency.

- `renders/ChatGnt-Teaser-LinkedIn.mp4` — final 1080×1350 H.264/AAC sound-on teaser
- `renders/ChatGnt-Teaser-Silent.mp4` — matching video-only version
- `renders/ChatGnt-Teaser-master.mp4` — high-quality pre-normalization master
- `renders/ChatGnt-Teaser-cover.png` — matching curiosity-led cover frame
- 600 frames / 20 seconds / 30 fps
- Default CTA: `github.com/WillEtheridge/chatgandt`

```bash
npm run audio:teaser
npm run render:teaser
npm run normalize:teaser
npm run render:teaser-cover
```

The final mix targets approximately −15 LUFS with a −1.5 dB mastering ceiling. The beat and sound-design levels remain independently adjustable in `src/Teaser.tsx`.

## Original promo

A 42-second, 4:5 promotional film for ChatG&T, built in Remotion.

The edit follows the product’s typographic-brutalist mixology system: Neue Montreal Mono Book, warm concrete, deep steel, oxide signal red, hard rules, exposed grids, and the ASCII martini loader. It is designed to remain understandable on mute, with an original minimal electronic soundtrack for sound-on playback.

## Deliverables

- `renders/ChatGnt-Promo-LinkedIn.mp4` — final 1080×1350 H.264/AAC social upload
- `renders/ChatGnt-Promo-cover.png` — matching cover frame
- `renders/ChatGnt-Promo-master.mp4` — high-quality pre-normalization master
- `renders/ChatGnt-Promo-preview-normalized.mp4` — lightweight review copy

## Composition

- ID: `ChatGntPromo`
- 1080×1350 (4:5)
- 30 fps
- 1,260 frames / 42 seconds
- Default CTA: `github.com/WillEtheridge/chatgandt`

The CTA is exposed as the `url` composition prop and can be changed in Remotion Studio without editing scene markup.

## Commands

```bash
npm install
npm run dev
npm run lint
npm run render:master
npm run normalize:linkedin
```

The final normalization targets social-friendly playback at approximately −18 LUFS with a −1.5 dB true-peak ceiling while copying the rendered video stream unchanged.
