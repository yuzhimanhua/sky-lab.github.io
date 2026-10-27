# SKY Lab website

A small static website for the group's people and publications. The build uses Python 3.12 and its standard library; no packages, Hugo, Go, or Node.js are required.

## Update content

Edit the JSON files in `data/`, following the structure of an existing entry:

- `site.json`: group name, introduction, and site settings.
- `people.json`: members and their profile links.
- `publications.json`: papers, authors, publication dates, venues, and resource links.

Keep JSON valid: use double quotes and do not add trailing commas. Build and check the site after each update:

```sh
python scripts/build.py
python scripts/check_site.py
python -m unittest discover -s tests
```

## Preview locally

```sh
python -m http.server 8000 --directory site
```

Open <http://localhost:8000/>. Stop the server with Ctrl+C. After changing the data, rerun the build and refresh the browser.

## Publish

Push changes to `main`. The **Build and deploy website** GitHub Actions workflow builds, checks, and deploys `site/` to GitHub Pages. Pull requests run the same build and checks without deploying. You can also run the workflow manually from the Actions tab.

Commit the edited JSON, scripts, or assets. Generated HTML is ignored by Git and recreated automatically during deployment.

In the repository's **Settings → Pages**, set the source to **GitHub Actions**. The optional Netlify configuration also builds and publishes `site/`.

## Files

- `data/`: editable site content.
- `scripts/build.py`: generates the static HTML.
- `scripts/check_site.py`: checks the generated site.
- `site/`: website served by GitHub Pages; rebuild its generated HTML from the data.
- `site/assets/`: CSS, JavaScript, and portraits used by the site.
- `tests/`: regression checks for content updates and generated-page cleanup.
- `.github/workflows/publish.yaml`: the single build and deployment workflow.

The previous Hugo content and configuration remain in the repository as migration reference. The new build does not use them.
