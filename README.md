# SKY Lab website

A small static website for the group's people and publications, maintained directly in this repository. The build uses Python 3.12 and its standard library, with no additional packages.

## Update content

Edit the JSON files in `data/`, following the structure of an existing entry:

- `site.json`: group name, introduction, logo, home photo, and photo credit.
- `people.json`: members and their profile links.
- `publications.json`: papers, authors, publication dates, venues, and resource links.

Store images in `site/assets/`: `branding/` for the logo, `photos/` for group photos, and `people/` for member portraits. Set each image path in the corresponding JSON file relative to `site/`, for example `assets/people/yu-zhang.jpg`.

Keep JSON valid: use double quotes and do not add trailing commas. From the repository root, build and check the site after each update:

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

In [Settings → Pages](https://github.com/yuzhimanhua/sky-lab.github.io/settings/pages), under **Build and deployment**, set **Source** to **GitHub Actions**. This setting is required: **Deploy from a branch** publishes the repository's source files, which can display this README as the homepage. Its separate deployment can also overwrite the website deployed by our workflow.

Push changes to `main`. The **Build and deploy website** GitHub Actions workflow builds, checks, and deploys `site/` to [the public website](https://yuzhimanhua.github.io/sky-lab.github.io/). Pull requests run the same build and checks without deploying. After changing the Pages source, run this workflow from the [Actions tab](https://github.com/yuzhimanhua/sky-lab.github.io/actions/workflows/publish.yaml) or push a new change to `main` to publish the site.

Commit the edited JSON, scripts, or assets. Generated HTML is ignored by Git and recreated automatically during deployment.

## Files

- `data/`: editable site content.
- `scripts/build.py`: generates the static HTML.
- `scripts/check_site.py`: checks the generated site.
- `site/`: website served by GitHub Pages; rebuild its generated HTML from the data.
- `site/assets/`: CSS, JavaScript, logo, group photos, and member portraits used by the site.
- `tests/`: regression checks for content updates and generated-page cleanup.
- `.github/workflows/publish.yaml`: the single build and deployment workflow.
