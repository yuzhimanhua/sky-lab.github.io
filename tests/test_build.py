"""Regression tests for editable content and safe generated-page cleanup."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_builder', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def test_member_profile_keeps_stable_id_after_name_change(self):
        member = dict(builder.PEOPLE[0], name='Renamed Member', id='stable-profile')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(builder, 'OUTPUT', output), patch.object(builder, 'MEMBERS', {member['name']: member}), \
                    patch.object(builder, 'PUBLICATIONS', []), patch.object(builder, 'GENERATED', set()):
                # page() uses publication dates for the footer; keep one unrelated paper.
                builder.PUBLICATIONS = [dict(title='Example', authors=[], date='2026-09-01')]
                builder.build_authors()
                self.assertTrue((output / 'author/stable-profile/index.html').is_file())
                self.assertFalse((output / 'author/renamed-member/index.html').exists())
                self.assertIn('author/stable-profile/', builder.person_card(member, '../'))

    def test_cleanup_removes_only_obsolete_registered_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in ['old.html', 'current.html', 'handwritten.html', 'portrait.jpg']:
                (output / name).write_text('keep', encoding='utf-8')
            (output / '.generated-pages.json').write_text(json.dumps(['old.html', 'current.html']), encoding='utf-8')
            with patch.object(builder, 'OUTPUT', output), patch.object(builder, 'GENERATED', {'current.html'}):
                builder.update_manifest()
            self.assertFalse((output / 'old.html').exists())
            for name in ['current.html', 'handwritten.html', 'portrait.jpg']:
                self.assertTrue((output / name).is_file())

    def test_cleanup_rejects_paths_outside_output(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            output = parent / 'site'
            output.mkdir()
            protected = parent / 'source.html'
            protected.write_text('source', encoding='utf-8')
            (output / '.generated-pages.json').write_text(json.dumps(['../source.html']), encoding='utf-8')
            with patch.object(builder, 'OUTPUT', output), patch.object(builder, 'GENERATED', set()):
                with self.assertRaises(ValueError):
                    builder.update_manifest()
            self.assertTrue(protected.is_file())


if __name__ == '__main__':
    unittest.main()
