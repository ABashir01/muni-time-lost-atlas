# Product Experience

## Product Promise
The site should make one promise and fulfill it immediately:

**Where Muni riders lose the most time**

The experience should be answer-first, not chart-first. Users should first see which routes are losing the most time, then why, where, and when.

## Core User Questions
The product should answer these questions in order:
1. `Which routes are losing the most time?`
2. `What kind of time loss is it?`
3. `Where on the route does it happen?`
4. `When does it happen?`
5. `How does this route compare to others?`

## Primary User-Facing Metric
Use:
- `Typical trip: +X.X min`
- long form: `Typical extra time on a full one-way trip`

This is the MVP headline because it is honest without requiring passenger weighting.

Supporting metrics:
- `waiting loss`
- `in-vehicle loss`
- `bunching rate`
- `worst time window`
- `worst segment`

Avoid as primary language:
- `on-time percentage`
- `headway variance`
- `schedule deviation index`
- `observed/scheduled ratio`

## Overview Page
The homepage should include:
- a strong title and civic subhead
- time window controls like `Now`, `Today`, `This week`, `This month`
- route ranking cards
- a route map colored by time lost
- an explanatory strip for `Waiting`, `Slow travel`, and `Bunching`
- a compare teaser

Each route card should show:
- route name
- total typical loss
- waiting vs travel split
- worst time window
- worst segment label

## Route Detail
The route detail page should answer:
- how much extra time a typical full trip loses
- whether the loss is mainly waiting or onboard delay
- where on the route the loss is worst
- when the route breaks down most

The route detail page should contain:
- summary metric row
- segment or corridor emphasis
- time-of-day pattern
- problem-type interpretation
- comparison against system or route peers

## Map View
The map should show:
- route corridors colored by time loss
- optional live vehicle overlay
- optional stop overlay
- optional transit-only lane overlay

The map is evidence, not the only story. The user should never need to decode raw dots before understanding the headline.

## Compare View
The compare view should let the user compare 2-4 routes and quickly answer:
- which route loses more time
- whether the loss is mostly waiting or travel time
- which time window is worst
- which segment is worst

## Methodology Page
The methodology page should:
- define the main metric in plain English
- explain waiting loss and in-vehicle loss separately
- explain baseline choices
- list data sources
- note caveats without overwhelming the reader

## Visual Direction
The interface should feel:
- civic
- punchy
- flat-color
- transit-signage inspired

Use:
- black / white structure
- strong route-color accents
- crisp geometry and strong typography

Reference planning mockups:
- [dark mode mockup](./mockups/homepage-dark-mode.png)
- [light mode mockup](./mockups/homepage-light-mode.png)

