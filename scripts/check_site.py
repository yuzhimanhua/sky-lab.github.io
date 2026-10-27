"""Check static pages, local links, and migrated content without extra packages."""

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = []
        self.references = []
        self.text = []
        self.counts = Counter()
        self.classes = Counter()
        self.articles = []
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.counts[tag] += 1
        classes = attrs.get('class', '').split()
        self.classes.update(classes)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.references.append(attrs[key])
        if tag == 'img':
            assert attrs.get('alt'), f'Image needs alt text: {self.path}'
            assert attrs.get('width') and attrs.get('height'), f'Image needs dimensions: {self.path}'
        if tag == 'a' and attrs.get('target') == '_blank':
            assert 'noopener' in attrs.get('rel', ''), f'Unsafe external link: {self.path}'
        if 'publication-item' in classes:
            self.articles.append(attrs)

    def handle_data(self, text):
        self.text.append(text)

    @property
    def plain_text(self):
        return ' '.join(''.join(self.text).split())


def main():
    paths = sorted(SITE.rglob('*.html'))
    assert paths, 'Run python scripts/build.py first.'
    manifest = json.loads((SITE / '.generated-pages.json').read_text(encoding='utf-8'))
    assert {path.relative_to(SITE).as_posix() for path in paths} == set(manifest), 'Generated page manifest is out of date.'
    documents = {path.resolve(): Document(path) for path in paths}
    references = 0
    for path, document in documents.items():
        assert document.counts['h1'] == 1, f'Expected one H1: {path}'
        assert document.counts['main'] == 1, f'Expected one main region: {path}'
        assert len(document.ids) == len(set(document.ids)), f'Duplicate HTML ID: {path}'
        for reference in document.references:
            url = urlsplit(reference)
            if url.scheme or url.netloc:
                assert url.scheme in ('https', 'http', 'mailto'), f'Unsupported URL: {reference}'
                continue
            assert not url.path.startswith('/'), f'Root-relative link breaks subdirectory hosting: {path}: {reference}'
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if target.is_dir():
                target /= 'index.html'
            assert target.is_relative_to(SITE.resolve()), f'Link escapes site: {path}: {reference}'
            assert target.is_file(), f'Broken local link: {path}: {reference}'
            if url.fragment and target.suffix == '.html':
                assert unquote(url.fragment) in documents[target].ids, f'Broken fragment: {path}: {reference}'
            references += 1

    people = json.loads((ROOT / 'data/people.json').read_text(encoding='utf-8'))
    papers = sorted(json.loads((ROOT / 'data/publications.json').read_text(encoding='utf-8')),
                    key=lambda item: item['date'], reverse=True)
    people_page = documents[(SITE / 'people/index.html').resolve()]
    publication_page = documents[(SITE / 'publication/index.html').resolve()]
    assert people_page.classes['person-card'] == len(people), 'People missing or duplicated.'
    assert len(publication_page.articles) == len(papers), 'Publications missing or duplicated.'
    assert [item['data-year'] for item in publication_page.articles] == [p['date'][:4] for p in papers]
    positions = [publication_page.plain_text.index(paper['title']) for paper in papers]
    assert positions == sorted(positions), 'Publications are out of date order.'
    for person in people:
        assert person['name'] in people_page.plain_text
        assert person['role'] in people_page.plain_text
        assert person['id'] in people_page.ids
        assert '../' + person['image'] in people_page.references
        for link in person['links']:
            assert link['url'] in people_page.references, f'Missing person link: {person["name"]}'
    for paper in papers:
        detail = documents[(SITE / 'publication' / paper['id'] / 'index.html').resolve()]
        assert paper['title'] in detail.plain_text
        assert paper['venue'] in detail.plain_text
        assert ', '.join(paper['authors']) in detail.plain_text
        for link in paper['links']:
            assert link['url'] in detail.references, f'Missing detail link: {paper["id"]}'
            assert link['url'] in publication_page.references, f'Missing listing link: {paper["id"]}'
    assert (SITE / '.nojekyll').exists(), 'GitHub Pages must serve static output directly.'
    print(f'Passed: {len(paths)} pages, {references} local links, {len(people)} people, '
          f'{len(papers)} papers and all resource links. Works at root or a repository subpath.')


if __name__ == '__main__':
    main()
