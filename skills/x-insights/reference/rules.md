# Rules learned the hard way

Each rule comes from a real post that went wrong or nearly did. The incident is kept in one line so you know when
the rule applies. Add your own at the bottom.

## Finding the conversation

| Rule | What happened |
|---|---|
| Follow quote chains, not only single posts. | A narrative spread through four layers of quotes. The scan caught the two smallest (1K and 4K views); the root (25K views) was a bare link that never named the topic, and the second layer used a nickname the queries did not search. |
| Put the community's nicknames in the filter and the queries. | Posts said "xx chain" while the queries searched the full name; the filter matched but the posts never reached the search results. |
| Surface emerging @handles automatically. | A new project had 19 posts in a morning; none passed the filter because its name was not in it yet. `trends.py` now lets a handle mentioned by 3+ authors through. |
| Rank by lift, not raw views. | Big generalist accounts always top raw views. Lift (views / the author's own median) shows which post broke out. |
| Keep recap bots out of the ranking. | Daily recap accounts filled the top of the outside tier with no view of their own. |

## Choosing the angle

| Rule | What happened |
|---|---|
| Drop angles that add nothing; never fill a quota. | Defending a project's self-reported volume nobody disputed, and grading founders' calls, both read flat. |
| Follow the numbers when they contradict the planned stance. | A "supportive" angle turned out to be a criticism of an insider; it became a friendly reply instead of a post. |
| Track which angles were chosen and published. | Without a list, the same question came back as a "new" angle days later. |

## Numbers

| Rule | What happened |
|---|---|
| Numbers must be what the reader sees in the app. | A post said borrowing against a stock token costs 24% (peak 90%). That came from an unlisted market where one contract held 99.9% of the debt; the app showed 1.39%. The user caught it from a screenshot; two image reviews missed it because they only compared the image to the data file. |
| One snapshot per post. | Mixing a morning TVL with an evening price made a ratio no one could reproduce. |
| Same period, same method, or no comparison. | "A is 12x B" was a single day; over 30 days it was 6.6x. One venue reported APR after fees, the other before. |
| Check the counter-example in your own table. | "Still near its peak at day 112 is a good sign", until a dead peer chain in the same table had also been at its peak on day 112. |
| Keep series, not totals. | The first pull stored a 30-day total only; the chart could not show the daily story and the data had to be pulled again. |
| Probe the data before writing the image brief. | A brief asked for a daily APR series that the API only had for 7 days; the brief was rewritten halfway. |
| Re-run time-sensitive numbers right before handing over. | A scheduled post aborted because a ratio had moved outside its guard band overnight. That was the right outcome. |
| Measure post length with `len()`. | An estimated 216 characters was really 296, over the limit for a normal post. |

## Writing

| Rule | What happened |
|---|---|
| Agents return number cards; the main session writes, one post at a time. | Agents writing at the end of a long data pull produced 6-line posts with 4 caveat lines, every one of them. |
| At most 4 lines, at most 2 caveats; fix or drop a claim instead of adding a warning. | A post got 4 review findings and gained 4 warning lines; the idea drowned. |
| Line 1 is the surprising number. | Opening with the 5.5% background rate and reaching the 56% headline on line 3 lost readers. |
| Slang at most once per post, never repeated in a batch. | Example posts used "tbh/imo/tho" so often that every new post copied them. |
| Do not narrate the work. | "I pulled both APIs myself" adds nothing for the reader. |

## Charts

| Rule | What happened |
|---|---|
| Draw the chart after the post is final. | Editing changed line 1 and the image no longer matched. |
| Daily stacked columns instead of area charts. | Areas hid the day-to-day story and read as decoration. |
| An independent agent reviews every image. | Overlapping labels and a wrong colour role passed the author every time. |

## Your rules

- ...
