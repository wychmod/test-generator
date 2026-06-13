import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
KB_SCRIPTS = ROOT / "knowledge" / "scripts"
sys.path.insert(0, str(KB_SCRIPTS))

import build_index  # noqa: E402
import search  # noqa: E402


class KnowledgeSearchTests(unittest.TestCase):
    def test_chinese_partial_query_matches_longer_heading(self):
        index = build_index.build_index(rebuild=True)

        results = search.search("密码强度", index, top_k=5)

        self.assertTrue(results)
        self.assertTrue(any("密码强度规则" == item["heading"] for item in results))

    def test_trigger_word_does_not_prevent_keyword_match(self):
        index = build_index.build_index(rebuild=True)

        results = search.search("参考知识库 密码强度", index, top_k=5)

        self.assertTrue(results)
        self.assertTrue(any("project-conventions.md" == item["filename"] for item in results))

    def test_trigger_words_are_not_used_as_search_terms(self):
        index = build_index.build_index(rebuild=True)

        results = search.search("参考知识库 密码强度", index, top_k=3)

        self.assertTrue(results)
        self.assertEqual("密码强度规则", results[0]["heading"])
        self.assertTrue(all(item["heading"] != "(intro)" for item in results))


if __name__ == "__main__":
    unittest.main()
