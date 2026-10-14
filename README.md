# Just for Today RSS Feed

This feed shows the daily Narcotics Anonymous "Just for Today" reading on the Mango Signs TV.

- GitHub Actions runs `jftna_rss_generator.py` every morning, at about 1 AM and 7 AM Edmonton time.
- The script reads today's reading from https://jft.na.org/. If that site is down, it uses the Uncoast NA page instead.
- It writes `jftna.xml`, and GitHub Pages publishes it.
- Feed URL: `https://chad756.github.io/JFT-rss-feed/jftna.xml`

## What the feed shows

- Title: the reading's title, for example "The end of loneliness"
- Description, the short version for the TV: the opening quote plus the "Just for Today" line
- Full reading: in `content:encoded`, for apps that can show long text

## Setup (one time)

1. Create a public repository named `JFT-rss-feed` on GitHub.
2. Upload every file from this folder, including `.nojekyll` and `.github/workflows/update-rss.yml`.
3. Go to Settings > Pages. Under "Deploy from a branch," choose `main` and `/ (root)`, then click Save.
4. Go to Settings > Actions > General > Workflow permissions. Choose "Read and write permissions," then click Save.
5. Go to Actions > Update JFT RSS > Run workflow, so the first update runs now.
6. After 1 to 2 minutes, open the feed URL in a browser. You should see XML.
7. Paste the feed URL into the Mango Signs RSS app.

## Troubleshooting

- If the feed URL shows a 404 error, check that Pages is turned on and the repository is public.
- If the workflow fails, both sources were unreachable that day. Yesterday's feed stays up, and GitHub emails you. Run the workflow again later.
- GitHub turns off scheduled workflows after 60 days with no repository activity. The daily commit keeps it active. If it ever stops, go to the Actions tab and turn it back on.

## Copyright

Just for Today is copyrighted by NA World Services, Inc. Use this feed only for internal display, unless you have NA World Services' permission.
