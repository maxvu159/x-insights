# Image review checklist

For the review agent in step 5. The reviewer receives only: the PNG, spec.json, the data file, and this file.
Not the post, not the drawing agent's opinions. Return **PASS** or a list of issues by item number, one issue per
line: item, what is wrong, how to fix it in the spec.

1. **The image says the right thing.** The title is a one-sentence conclusion with a number. In 3 seconds the image
   must show what the title says. The chart form fits the question (see `catalog.md`). Cumulative charts must not be
   used to tell a story about decline.
2. **Numbers match the data.** Every number on the image (title, subtitle, labels, big numbers) traces back to the
   data file, from one snapshot (`asof`). If the title says 4x, the image must show 4x, not 3.6x.
3. **Text inside the safe area, no overlap, no overflow.** Safe area: 6% each side, 8% top and bottom. End labels,
   value labels and annotations do not overlap and are not cut off. Subtitle at most 2 lines, source at most 2 lines.
4. **Colors match roles.** At most 4 data colors. Coral only for negative or risk, and only once. The main series
   uses the accent color, the comparison side is grey. No colors outside the style.
5. **Supporting parts serve the main idea.** Side panels, big numbers and callouts all answer "compared with what"
   or "where is the risk" for the title. If covering a supporting part does not weaken the title, it is redundant.
6. **Source, date, handle.** The source line states sources and assumptions (self-reported numbers, stablecoin = $1,
   definition of "fresh"). The data date is present. The handle is top right (when the style or `INSIGHTS_HANDLE`
   sets one).
7. **No wasted space.** No empty area wider than 8% of the width or taller than 12% of the height with nothing in it.
   The y axis is not squeezed so data peaks get cut. The chart covers at least 45% of the image.

Problems caused by the renderer or the style (title or source position, axis margins, a role's color) are marked as
**render issue**, not spec issue, so the drawer fixes `bin/` or tells the user instead of editing the spec in vain.

Also note if seen: title longer than 2 lines, legend duplicating direct labels, odd number formats (3.08998x), dates
not yet in the form `21 Oct 2026`.
