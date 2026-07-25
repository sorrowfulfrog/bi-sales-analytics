# SportStore Analytics portfolio site

This directory is a static, public-safe presentation layer. It contains no
database credentials, Jira tokens, or Bitrix24 webhook URLs.

Run locally from the project root:

```bash
python3 -m http.server 8080 --directory site
```

Then open `http://localhost:8080`.

Deployment target: Cloudflare Pages. Configure `site` as the build output
directory and attach the custom domain only after the Pages project exists.
