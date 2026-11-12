# Hüseyin Ateş — Academic Research Website

This repository contains the source for the English-language academic website of Hüseyin Ateş, PhD, Associate Professor of Science Education.

**Website:** https://huseyinates38.github.io/

**Sections:** Home, Research, Publications, Projects, About & CV, and Contact.

## Publishing

GitHub Pages is deployed by the workflow at `.github/workflows/pages.yml`. The static source is stored as four checked, Base64-encoded segments in `site-bundle/` because the connected publishing interface only writes text files.

The GitHub Actions workflow:

1. Reassembles the archived static files and verifies their SHA-256 checksum.
2. Unpacks the six HTML pages and their CSS/JavaScript assets.
3. Generates the public two-page CV from the research data.
4. Publishes the `docs/` directory using the official GitHub Pages actions.

**Repository owner:** In Settings → Pages, choose **GitHub Actions** as the source under Build and deployment. After enabling Pages, use Actions → Publish Academic Website → Run workflow if a deployment has not started.

## Updating the site

For editable source files and local preview, use the original downloadable website package supplied in the ChatGPT conversation. Do not edit the Base64 segments manually.

Publication data and academic profile are sourced from the owner's CV supplied in November 2026. Verify all published facts and links before treating the site as the permanent public academic record.
