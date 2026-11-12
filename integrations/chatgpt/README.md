# ChatGPT resource-directory integration (read-only)

This optional integration exposes the repository's **site directory**, not copyrighted video files. It does not scrape sites, download media, authenticate to cloud drives, or verify that a listed site has distribution rights.

## Endpoints

- `GET /health`: API process status.
- `GET /resources?q=美剧&category=magnet_search&status=reachable&limit=20`: search the upstream directory by name, summary, and tags.
- `GET /openapi.json`: OpenAPI schema for a ChatGPT GPT Action.

Source JSON is fetched from `resources/resources.json` and `reports/availability.json` on GitHub and cached for 15 minutes (configurable). The code requires Python 3.10+ and no third-party packages.

## Local run

From the repository root:

```bash
python3 integrations/chatgpt/resource_api.py
curl http://127.0.0.1:8787/health
curl 'http://127.0.0.1:8787/resources?category=subtitles'
```

Alternatively, deploy in Docker:

```bash
docker build -f integrations/chatgpt/Dockerfile -t zhuiju-directory-api .
docker run --rm -p 8787:8787 zhuiju-directory-api
```

For a private NAS deployment, keep port 8787 within your trusted network. The API exposes publicly listed URLs only; it does not need your 115 or Emby credentials.

## Connecting to ChatGPT

A ChatGPT **custom GPT Action**, where supported, requires a reachable **HTTPS** API URL. Local `localhost`, ordinary private LAN addresses, and a Tailscale-only address are not reachable from ChatGPT's servers.

1. Deploy the service on your own HTTPS host. Set `PUBLIC_BASE_URL=https://your-domain.example`.
2. Open `https://your-domain.example/openapi.json` and use that schema in the GPT Actions editor.
3. Select no authentication only if you intentionally expose this public-directory service. Otherwise put suitable HTTPS/API authentication in front and update the schema accordingly.
4. Test `searchResources` with `category=cloud_search` or `category=subtitles`.

This is **not** an installable GitHub or ChatGPT Plugin Directory package. It is a prototype HTTP interface that can be adapted to supported GPT Actions or other clients. Deployment, public HTTPS, and ChatGPT Action configuration are not performed automatically.

## Data caveats

- A reachable homepage is not evidence that downloading works.
- Availability reports reflect the GitHub Actions testing network, not your home network.
- The upstream repository includes copyright and safety risk fields. Never treat inclusion, a star rating, or an HTTP 200 as permission to download any particular work.
- The API has no control over third-party listings or their terms of use.

## Configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `PORT` | `8787` | HTTP server port |
| `SOURCE_REPO` | `allendong117/awesome-zhuiju-free` | Repo serving JSON data |
| `SOURCE_BRANCH` | `main` | Branch serving JSON data |
| `CACHE_SECONDS` | `900` | Cache duration |
| `PUBLIC_BASE_URL` | unset | HTTPS URL placed into the OpenAPI schema |

License/attribution: this project is derived from [laoma528/awesome-zhuiju-free](https://github.com/laoma528/awesome-zhuiju-free), under CC BY 4.0 for its published directory content. Retain credit and comply with upstream license terms.
