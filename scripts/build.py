"""Render the SKY Lab website using only the Python standard library."""

from collections import defaultdict
from datetime import datetime
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'site'
GENERATED = set()
GROUPS = ['Principal Investigator', 'PhD Students', "Master's Students",
          'Undergraduate Students', 'Visiting Students']
MONTHS = ['', 'January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']


def load(name):
    return json.loads((ROOT / 'data' / f'{name}.json').read_text(encoding='utf-8'))


def esc(value):
    return escape(str(value), quote=True)


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')


def author_id(name):
    return MEMBERS[name]['id'] if name in MEMBERS else slug(name)


def safe_url(value):
    if urlsplit(value).scheme not in ('https', 'http', 'mailto'):
        raise ValueError(f'Unsupported URL: {value}')
    return esc(value)


def resource_links(links, css='publication-links'):
    return f'<div class="{css}">' + ''.join(
        f'<a href="{safe_url(link["url"])}" target="_blank" rel="noopener noreferrer">'
        f'{esc(link["label"])} <span aria-hidden="true">↗</span></a>' for link in links
    ) + '</div>'


def date_label(publication):
    date = datetime.fromisoformat(publication['date'].replace('Z', '+00:00'))
    return f'{MONTHS[date.month]} {date.year}'


def page(path, title, description, body, active=''):
    depth = len(Path(path).parts) - 1
    base = '../' * depth if depth else './'
    nav = ''.join(
        f'<a href="{base}{url}"' + (' aria-current="page"' if active == label else '')
        + f'>{label}</a>' for label, url in [('About', ''), ('People', 'people/'), ('Publications', 'publication/')]
    )
    document = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | SKY Lab · Texas A&amp;M University</title>
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#500000">
  <meta property="og:title" content="{esc(title)} | SKY Lab">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <link rel="icon" href="{base}{esc(SITE['logo']['image'])}" type="image/png">
  <link rel="stylesheet" href="{base}assets/site.css">
  <script defer src="{base}assets/site.js"></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header"><div class="header-inner container">
    <a class="brand" href="{base}" aria-label="SKY Lab home"><span class="brand-mark"><img src="{base}{esc(SITE['logo']['image'])}" alt="SKY Lab" width="{SITE['logo']['width']}" height="{SITE['logo']['height']}"></span>
      <span class="brand-affiliation">Texas A&amp;M University</span></a>
    <nav class="site-nav" aria-label="Main navigation">{nav}</nav>
  </div></header>
  <main id="main" class="container">{body}</main>
  <footer class="site-footer"><div class="footer-inner container">
    <div><a class="footer-brand" href="{base}">SKY Lab</a><p>Scientific Knowledge discoverY<br>Texas A&amp;M University</p></div>
    <div class="footer-links"><a href="mailto:{esc(SITE['email'])}">{esc(SITE['email'])}</a><span>College Station, Texas</span>
    <small>© {max(p['date'][:4] for p in PUBLICATIONS)} SKY Lab</small></div>
  </div></footer>
</body>
</html>
'''
    destination = OUTPUT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding='utf-8', newline='\n')
    GENERATED.add(path)


def author_list(authors, base):
    return ', '.join(
        f'<a class="lab-author" href="{base}people/#{MEMBERS[name]["id"]}">{esc(name)}</a>'
        if name in MEMBERS else esc(name) for name in authors
    )


def publication_item(publication, base):
    search = ' '.join([publication['title'], *publication['authors'], publication['venue'], publication['date'][:4]])
    return f'''<li class="publication-item" data-search="{esc(search)}" data-year="{publication['date'][:4]}">
      <div class="publication-meta"><span class="venue">{esc(publication['venue'])}</span>
        <time datetime="{publication['date'][:7]}">{date_label(publication)}</time></div>
      <h3 class="publication-title"><a href="{base}publication/{publication['id']}/">{esc(publication['title'])}</a></h3>
      <p class="publication-authors">{author_list(publication['authors'], base)}</p>
      {resource_links(publication['links'])}
    </li>'''


def grouped_publications(publications, base):
    years = defaultdict(list)
    for publication in publications:
        years[publication['date'][:4]].append(publication)
    return ''.join(f'''<section class="publication-year" data-year="{year}" aria-labelledby="year-{year}">
        <div class="year-heading"><h2 id="year-{year}">{year}</h2><span class="group-count">{len(items)} papers</span></div>
        <ul class="publication-list">{''.join(publication_item(p, base) for p in items)}</ul>
      </section>''' for year, items in sorted(years.items(), reverse=True))


def portrait(person, base, eager=False):
    return f'<div class="person-photo"><img src="{base}{esc(person["image"])}" alt="{esc(person["name"])}" width="400" height="400" loading="{"eager" if eager else "lazy"}"></div>'


def person_card(person, base, principal=False):
    return f'''<article class="person-card{' pi-card' if principal else ''}" id="{person['id']}">
      <a class="portrait-link" href="{base}author/{person['id']}/" tabindex="-1" aria-hidden="true">{portrait(person, base, principal)}</a>
      <div class="person-info"><h3 class="person-name"><a href="{base}author/{person['id']}/">{esc(person['name'])}</a></h3>
        <p class="person-role">{esc(person['role'])}</p>
        {'<p class="pi-description">Leading the Scientific Knowledge discoverY Lab at Texas A&amp;M University.</p>' if principal else ''}
        {resource_links(person['links'], 'person-links')}
      </div>
    </article>'''


def build_home():
    body = f'''<section class="hero" aria-labelledby="hero-title">
      <div class="hero-copy"><p class="eyebrow">Scientific Knowledge discoverY Lab</p>
        <h1 class="hero-title" id="hero-title">Knowledge that<br>moves <em>science</em><br>forward.</h1>
        <p class="hero-description">We study data mining and natural language processing to help make sense of scientific knowledge and accelerate discovery.</p>
        <div class="hero-actions"><a class="button" href="./publication/">Explore our research <span aria-hidden="true">↗</span></a>
          <a class="button secondary" href="./people/">Meet the people <span aria-hidden="true">→</span></a></div>
      </div>
      <div class="hero-aside"><svg class="sky-graphic" viewBox="0 0 460 430" fill="none" role="img" aria-labelledby="network-title">
        <title id="network-title">A constellation connecting language, knowledge, and discovery</title>
        <circle cx="230" cy="210" r="172" stroke="#ded8d0" stroke-dasharray="3 7"/><circle cx="230" cy="210" r="110" stroke="#e6e0d8"/>
        <g stroke="#b6a99f" stroke-width="1"><path d="M82 250 159 89 325 125 367 288 213 345 82 250 231 210 159 89M231 210 325 125M231 210 367 288M231 210 213 345M159 89 213 345M82 250 325 125M159 89 367 288"/></g>
        <path d="m82 250 149-40 94-85" stroke="#500000" stroke-width="2"/>
        <g fill="#f8f7f4" stroke="#9b887c"><circle cx="159" cy="89" r="6"/><circle cx="367" cy="288" r="6"/><circle cx="213" cy="345" r="6"/></g>
        <g fill="#500000"><circle cx="82" cy="250" r="7"/><circle cx="325" cy="125" r="7"/><circle cx="231" cy="210" r="11"/></g>
        <circle cx="231" cy="210" r="20" stroke="#500000" stroke-opacity=".2"/>
        <g fill="#75685f" font-family="system-ui,sans-serif" font-size="10" letter-spacing="2"><text x="116" y="65">LANGUAGE</text><text x="278" y="99">KNOWLEDGE</text><text x="172" y="377">DISCOVERY</text></g>
      </svg><div class="research-tags"><span>Data mining</span><span>Natural language processing</span><span>AI for science</span></div></div>
    </section>
    <figure class="home-photo">
      <a href="./{esc(SITE['home_photo']['image'])}" target="_blank" rel="noopener noreferrer" aria-label="View the full-size group photo">
        <img src="./{esc(SITE['home_photo']['image'])}" alt="{esc(SITE['home_photo']['alt'])}" width="{SITE['home_photo']['width']}" height="{SITE['home_photo']['height']}" loading="lazy" decoding="async">
      </a>
      <figcaption>{esc(SITE['home_photo']['caption'])}</figcaption>
    </figure>
    <section class="home-research" aria-labelledby="about-heading">
      <div class="section-heading"><p class="eyebrow">About the lab</p><h2 id="about-heading">Connecting ideas.<br>Discovering what’s next.</h2></div>
      <div class="lab-note"><p>{esc(SITE['description'])}</p><a class="text-link" href="{safe_url(SITE['pi_url'])}" target="_blank" rel="noopener noreferrer">About Prof. Yu Zhang <span aria-hidden="true">↗</span></a></div>
    </section>
    <section class="recent-publications" aria-labelledby="recent-heading">
      <div class="section-heading"><div><p class="eyebrow">From our group</p><h2 id="recent-heading">Recent publications</h2></div>
        <a class="text-link" href="./publication/">All publications <span aria-hidden="true">→</span></a></div>
      <ul class="publication-list">{''.join(publication_item(p, './') for p in PUBLICATIONS[:3])}</ul>
    </section>'''
    page('index.html', 'Scientific Knowledge discoverY Lab', SITE['description'], body, 'About')


def build_people():
    body = '''<header class="page-intro"><p class="eyebrow">Our group</p><h1>People</h1><p class="page-description">The people behind the research.</p></header>'''
    for group in GROUPS:
        people = [p for p in PEOPLE if p['group'] == group]
        if not people:
            continue
        principal = group == 'Principal Investigator'
        body += f'''<section class="people-section{' pi-section' if principal else ''}" aria-labelledby="{slug(group)}">
          <div class="group-heading"><h2 id="{slug(group)}">{esc(group)}</h2><span class="group-count">{len(people):02}</span></div>
          <div class="{'pi-grid' if principal else 'people-grid'}">{''.join(person_card(p, '../', principal) for p in people)}</div>
        </section>'''
    page('people/index.html', 'People', 'Meet the faculty and students of the SKY Lab at Texas A&M University.', body, 'People')


def build_publications():
    years = sorted({p['date'][:4] for p in PUBLICATIONS}, reverse=True)
    options = ''.join(f'<option value="{year}">{year}</option>' for year in years)
    body = f'''<header class="page-intro"><p class="eyebrow">Our research</p><h1>Publications</h1>
      <p class="page-description">Papers, code, and resources from SKY Lab.</p></header>
      <form class="publication-toolbar" role="search" hidden>
        <div class="search-field"><label for="publication-search">Search publications</label><input type="search" id="publication-search" placeholder="Search by title, author, or venue…" autocomplete="off"></div>
        <div class="filter-field"><label for="publication-year">Year</label><select id="publication-year"><option value="all">All years</option>{options}</select></div>
        <p class="result-count" role="status" aria-live="polite" aria-atomic="true">{len(PUBLICATIONS)} publications</p>
      </form>
      <div id="publication-results">{grouped_publications(PUBLICATIONS, '../')}</div>
      <div class="empty-state" hidden><h2>No publications found</h2><p>Try a different title, author, venue, or year.</p><button class="button secondary" type="button" id="reset-filters">Clear filters</button></div>'''
    page('publication/index.html', 'Publications', 'Research publications, papers, code, datasets, and models from SKY Lab.', body, 'Publications')
    for publication in PUBLICATIONS:
        body = f'''<article class="publication-detail"><a class="back-link" href="../../publication/">← All publications</a>
          <div class="detail-meta publication-meta"><span class="venue">{esc(publication['venue'])}</span><time datetime="{publication['date'][:7]}">{date_label(publication)}</time><span>{'Journal article' if publication['type'] == 'journal' else 'Conference paper'}</span></div>
          <h1>{esc(publication['title'])}</h1><p class="detail-authors">{author_list(publication['authors'], '../../')}</p>
          {resource_links(publication['links'], 'detail-links publication-links')}
        </article>'''
        page(f'publication/{publication["id"]}/index.html', publication['title'], f'{publication["title"]}. {publication["venue"]}.', body, 'Publications')


def build_authors():
    # Preserve the former author URLs, including collaborators with publications.
    names = {name for p in PUBLICATIONS for name in p['authors']} | set(MEMBERS)
    for name in sorted(names):
        person = MEMBERS.get(name)
        papers = [p for p in PUBLICATIONS if name in p['authors']]
        body = '<div class="page-intro"><a class="back-link" href="../../people/">← People</a>'
        body += f'<p class="eyebrow">{esc(person["group"]) if person else "Publications by author"}</p><h1>{esc(name)}</h1></div>'
        if person:
            body += f'<div class="author-profile">{portrait(person, "../../", True)}<div><p class="person-role">{esc(person["role"])}</p>{resource_links(person["links"], "person-links")}</div></div>'
        if papers:
            body += f'<div class="section-heading"><h2>Publications</h2></div>{grouped_publications(papers, "../../")}'
        page(f'author/{author_id(name)}/index.html', name, f'{name} — SKY Lab, Texas A&M University.', body, 'People')


def validate_data():
    for asset in (SITE['logo'], SITE['home_photo']):
        image = (OUTPUT / asset['image']).resolve()
        if not image.is_relative_to(OUTPUT.resolve()) or not image.is_file():
            raise ValueError(f'Missing or invalid site image: {asset["image"]}')
    for entries in (PEOPLE, PUBLICATIONS):
        ids = [entry['id'] for entry in entries]
        if len(ids) != len(set(ids)) or any(not re.fullmatch(r'[a-z0-9-]+', value) for value in ids):
            raise ValueError('IDs must be unique lowercase URL slugs.')
        for entry in entries:
            for link in entry['links']:
                safe_url(link['url'])
    for person in PEOPLE:
        if person['group'] not in GROUPS:
            raise ValueError(f'Unknown group: {person["group"]}')
        image = (OUTPUT / person['image']).resolve()
        if not image.is_relative_to(OUTPUT.resolve()) or not image.is_file():
            raise ValueError(f'Missing or invalid portrait: {person["image"]}')
    for publication in PUBLICATIONS:
        date_label(publication)
        if publication['type'] not in ('journal', 'conference'):
            raise ValueError(f'Unknown publication type: {publication["type"]}')
    names = {name for p in PUBLICATIONS for name in p['authors']} | set(MEMBERS)
    routes = [author_id(name) for name in names]
    if len(routes) != len(set(routes)) or any(not route for route in routes):
        raise ValueError('Author names or member IDs produce conflicting page URLs.')


def update_manifest():
    # Remove only pages from an earlier build, never hand-authored source or assets.
    manifest = OUTPUT / '.generated-pages.json'
    previous = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    for path in set(previous) - GENERATED:
        destination = (OUTPUT / path).resolve()
        if not destination.is_relative_to(OUTPUT.resolve()) or destination.suffix != '.html':
            raise ValueError(f'Invalid generated-page path: {path}')
        destination.unlink(missing_ok=True)
    manifest.write_text(json.dumps(sorted(GENERATED), indent=2) + '\n', encoding='utf-8')


SITE = load('site')
PEOPLE = sorted(load('people'), key=lambda person: person['order'])
PUBLICATIONS = sorted(load('publications'), key=lambda publication: publication['date'], reverse=True)
MEMBERS = {person['name']: person for person in PEOPLE}


if __name__ == '__main__':
    validate_data()
    build_home()
    build_people()
    build_publications()
    build_authors()
    update_manifest()
    (OUTPUT / '.nojekyll').touch()
    print(f'Built SKY Lab: {len(PEOPLE)} people, {len(PUBLICATIONS)} publications. No external dependencies.')
