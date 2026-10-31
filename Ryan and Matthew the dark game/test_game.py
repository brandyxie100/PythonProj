from __future__ import annotations

import unittest

from main import SCREEN_W, STAGES, build_level


class LevelTests(unittest.TestCase):
    def test_every_stage_has_playable_geometry_and_collectibles(self) -> None:
        for stage in STAGES:
            with self.subTest(stage=stage.name):
                level = build_level(stage)
                self.assertGreater(len(level.solids), 0)
                self.assertGreater(len(level.spikes), 0)
                self.assertGreater(len(level.shards), 0)
                self.assertGreater(level.world_width, SCREEN_W)
                self.assertGreater(level.exit_rect.x, 0)
                self.assertLess(level.exit_rect.right, level.world_width)

    def test_stage_names_are_distinct(self) -> None:
        self.assertEqual(len({stage.name for stage in STAGES}), len(STAGES))


if __name__ == "__main__":
    unittest.main()
