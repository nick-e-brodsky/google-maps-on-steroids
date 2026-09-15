# 0004: Make the repo public, host the map via GitHub Pages

Status: Accepted
Date: 2026-09-15

## Context

The Leaflet map prototype (0002/0003) needs a durable, always-reachable
surface - manually running a local web server each time to check it on
mobile isn't sustainable, and mobile Safari's automatic HTTPS-upgrade
behavior makes plain local HTTP awkward to use anyway.

GitHub Pages was the natural fit (already using GitHub, zero new
accounts), but on GitHub's free plan Pages requires the **source repo**
to be public - not just the built output. Paid plans (Pro/Team) let the
source stay private, but the *published site* is still public regardless
of plan, short of GitHub Enterprise Cloud's access control. So there is no
free option that keeps this genuinely private.

## Decision

Make the repo public. Nick explicitly chose this over three alternatives
that were laid out with their tradeoffs (a dedicated public repo
containing only the derived map output; paying for GitHub Pro, which
protects source but not the published site; a third-party host with real
access control like Cloudflare Pages + Access).

## Alternatives considered

- Dedicated second repo containing only the generated map HTML (title/
  category/neighborhood/cuisine/coordinates - no raw Notes/Tags/original
  Google Maps URLs), keeping this repo private forever. Smaller exposure
  surface, but a second repo to maintain and sync.
- GitHub Pro (~$4/mo) to keep the source repo private. Doesn't actually
  solve privacy, since the published site is public either way - only
  protects the raw source data from being browsable.
- Third-party host with real access control (e.g. Cloudflare Pages +
  Cloudflare Access, free tier). Genuinely private, but a new external
  account/service to set up and maintain.

## Consequences

- Everything in the repo is now publicly browsable: raw Notes/Tags,
  original Google Maps Saved-list URLs, full `state.json`, this decisions
  history, all of it - not just what the rendered map shows.
- No ongoing cost, no new accounts, no server to keep running.
- Revisit if the exposure becomes uncomfortable as more cities/places are
  added (a larger, more detailed personal travel footprint) - the
  dedicated-public-repo alternative above is the fallback if so.
