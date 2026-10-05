from pathlib import Path
import re
import xml.etree.ElementTree as ET
from django.test import SimpleTestCase


class AboutBackgroundTests(SimpleTestCase):
    def test_inline_definitions_are_unique_and_resolve_across_all_layers(self):
        folder = Path(__file__).parent / 'templates/core/includes'
        ids = []
        refs = []
        for path in folder.glob('about-art-*.svg'):
            root = ET.parse(path).getroot()
            self.assertEqual(root.get('aria-hidden'), 'true')
            self.assertFalse(any(e.tag.endswith(('script', 'image')) for e in root.iter()))
            ids.extend(e.get('id') for e in root.iter() if e.get('id'))
            refs.extend(re.findall(r'url\(#([^\)]+)\)', path.read_text(encoding='utf-8')))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(refs)
        self.assertTrue(set(refs).issubset(ids))
