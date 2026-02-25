"""
Angry Birds Clone - Level Module
==================================
Defines the Level class responsible for building and managing the game's
21 levels (build_0 through build_20).

Each level method creates a specific arrangement of Pigs and wooden
Polygon structures (columns and beams) in the pymunk physics space.
Helper methods provide reusable structural patterns:
    - open_flat: An open frame structure (two columns + one beam on top).
    - closed_flat: A closed frame with top and bottom beams.
    - horizontal_pile: A stack of horizontal beams.
    - vertical_pile: A stack of vertical columns.

Level progression:
    - Levels 0-3: Simple structures with 1-3 pigs.
    - Levels 4-5: Mix of free-standing pigs and fortified structures.
    - Levels 6-8: Taller structures with higher-health pigs.
    - Levels 9-11: Complex multi-structure levels requiring strategy.
    - Levels 12-14: Advanced multi-structure castles, more pigs and reinforcement.
    - Levels 15-17: Strategic puzzle layouts requiring chain-reaction planning.
    - Levels 18-20: Expert levels with maximum complexity and boss pigs.

Updated for Python 3.12+ and Pymunk 7.x compatibility.
"""

import pymunk as pm

from characters import Pig
from polygon import Polygon


class Level():
    """Manages level construction, scoring thresholds, and bird counts.

    The Level class holds references to the shared game object lists
    (pigs, columns, beams) and the pymunk Space. Each build_N() method
    populates these lists with the specific layout for level N.

    Attributes:
        pigs (list): Shared list of active Pig objects.
        columns (list): Shared list of active vertical Polygon columns.
        beams (list): Shared list of active horizontal Polygon beams.
        space (pm.Space): The pymunk physics simulation space.
        number (int): Current level index (0-20, wraps around).
        number_of_birds (int): Birds available for the current level.
        one_star (int): Minimum score for a 1-star rating.
        two_star (int): Minimum score for a 2-star rating.
        three_star (int): Minimum score for a 3-star rating.
        bool_space (bool): Whether zero-gravity mode is active
                           (doubles bird count when True).
    """

    def __init__(self, pigs: list, columns: list, beams: list,
                 space: pm.Space) -> None:
        """Initialize the Level manager.

        Args:
            pigs: Shared list reference for storing Pig objects.
            columns: Shared list reference for storing column Polygons.
            beams: Shared list reference for storing beam Polygons.
            space: The pymunk Space where physics bodies are added.
        """
        self.pigs: list = pigs
        self.columns: list = columns
        self.beams: list = beams
        self.space: pm.Space = space
        self.number: int = 0
        self.number_of_birds: int = 4

        # Score thresholds for star ratings (lower limits)
        self.one_star: int = 30000
        self.two_star: int = 40000
        self.three_star: int = 60000

        # Zero-gravity mode flag (doubles available birds)
        self.bool_space: bool = False

    # ===================================================================
    # Reusable Structure Builders
    # ===================================================================

    def open_flat(self, x: int, y: int, n: int) -> None:
        """Create an open flat structure (doorway-like frames stacked vertically).

        Each frame consists of two vertical columns with a horizontal
        beam resting on top, forming an open archway shape:

            ┌─────────┐   <- beam
            │         │
            │         │   <- two columns
            │         │

        Multiple frames are stacked vertically with 100px spacing.

        Args:
            x: X position of the structure's left column (pymunk coords).
            y: Base Y position (pymunk coords).
            n: Number of frames to stack vertically.
        """
        y0 = y
        for i in range(n):
            y = y0 + 100 + i * 100  # Stack frames with 100px vertical gap

            # Left column
            p = (x, y)
            self.columns.append(Polygon(p, 20, 85, self.space))

            # Right column (60px to the right)
            p = (x + 60, y)
            self.columns.append(Polygon(p, 20, 85, self.space))

            # Top beam (centered between columns, 50px above column base)
            p = (x + 30, y + 50)
            self.beams.append(Polygon(p, 85, 20, self.space))

    def closed_flat(self, x: int, y: int, n: int) -> None:
        """Create a closed flat structure (box-like frames stacked vertically).

        Similar to open_flat but with both top and bottom beams,
        creating fully enclosed rectangular frames:

            ┌─────────┐   <- top beam
            │         │
            │         │   <- two columns
            │         │
            └─────────┘   <- bottom beam

        Multiple frames are stacked with 125px spacing.

        Args:
            x: X position of the structure's left column (pymunk coords).
            y: Base Y position (pymunk coords).
            n: Number of frames to stack vertically.
        """
        y0 = y
        for i in range(n):
            y = y0 + 100 + i * 125  # Stack frames with 125px vertical gap

            # Left column (slightly offset right for centering)
            p = (x + 1, y + 22)
            self.columns.append(Polygon(p, 20, 85, self.space))

            # Right column
            p = (x + 60, y + 22)
            self.columns.append(Polygon(p, 20, 85, self.space))

            # Top beam
            p = (x + 30, y + 70)
            self.beams.append(Polygon(p, 85, 20, self.space))

            # Bottom beam
            p = (x + 30, y - 30)
            self.beams.append(Polygon(p, 85, 20, self.space))

    def horizontal_pile(self, x: int, y: int, n: int) -> None:
        """Create a horizontal pile of stacked beams.

        Beams are stacked vertically with 20px spacing,
        forming a wall-like barrier:

            ═══════════   <- beam n
              ...
            ═══════════   <- beam 2
            ═══════════   <- beam 1

        Args:
            x: X position of the beam center (pymunk coords).
            y: Base Y position (pymunk coords).
            n: Number of beams to stack.
        """
        y += 70  # Offset from base position
        for i in range(n):
            p = (x, y + i * 20)  # Stack beams with 20px spacing
            self.beams.append(Polygon(p, 85, 20, self.space))

    def vertical_pile(self, x: int, y: int, n: int) -> None:
        """Create a vertical pile of stacked columns.

        Columns are stacked vertically with 85px spacing,
        forming a tall tower:

            │ │   <- column n
            │ │
            │ │   <- column 2
            │ │
            │ │   <- column 1

        Args:
            x: X position of the column center (pymunk coords).
            y: Base Y position (pymunk coords).
            n: Number of columns to stack.
        """
        y += 10  # Offset from base position
        for i in range(n):
            p = (x, y + 85 + i * 85)  # Stack columns with 85px spacing
            self.columns.append(Polygon(p, 20, 85, self.space))

    # ===================================================================
    # Level Definitions (build_0 through build_11)
    # ===================================================================

    def build_0(self) -> None:
        """Level 0 - Tutorial: Simple two-story house with 2 pigs.

        Layout: A basic two-story structure with one pig on the
        ground floor and one on the second floor.
        Difficulty: Easy (4 birds, standard health pigs).
        """
        # Place pigs inside the structure
        pig1 = Pig(980, 100, self.space)    # Ground floor pig
        pig2 = Pig(985, 182, self.space)    # Second floor pig
        self.pigs.append(pig1)
        self.pigs.append(pig2)

        # Ground floor: two columns + one beam
        p = (950, 80)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1010, 80)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (980, 150)
        self.beams.append(Polygon(p, 85, 20, self.space))

        # Second floor: two columns + one beam
        p = (950, 200)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1010, 200)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (980, 240)
        self.beams.append(Polygon(p, 85, 20, self.space))

        # Level settings
        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8  # Double birds in zero-gravity mode

        # Star rating thresholds
        self.one_star = 30000
        self.two_star = 40000
        self.three_star = 60000

    def build_1(self) -> None:
        """Level 1 - Scattered columns with 1 pig.

        Layout: Several standalone columns and one beam with a single pig.
        The open layout encourages precise shots.
        Difficulty: Easy (4 birds).
        """
        pig = Pig(1000, 100, self.space)
        self.pigs.append(pig)

        # Scattered structural elements
        p = (900, 80)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (850, 80)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (850, 150)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1050, 150)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1105, 210)
        self.beams.append(Polygon(p, 85, 20, self.space))

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_2(self) -> None:
        """Level 2 - Two-tower layout with 2 pigs.

        Layout: Two separate small towers, each sheltering a pig.
        The right tower is taller than the left.
        Difficulty: Easy-Medium (4 birds).
        """
        pig1 = Pig(880, 180, self.space)   # Left tower pig
        self.pigs.append(pig1)
        pig2 = Pig(1000, 230, self.space)  # Right tower pig (higher)
        self.pigs.append(pig2)

        # Left tower: one column + one beam
        p = (880, 80)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (880, 150)
        self.beams.append(Polygon(p, 85, 20, self.space))

        # Right tower: two columns + one beam (taller)
        p = (1000, 80)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1000, 180)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1000, 210)
        self.beams.append(Polygon(p, 85, 20, self.space))

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_3(self) -> None:
        """Level 3 - Pyramid fortress with 3 reinforced pigs.

        Layout: A complex pyramid-like structure with multiple layers.
        Three pigs with increased health (25 HP each) are scattered
        throughout the structure.
        Difficulty: Medium (4 birds, reinforced pigs).
        """
        # Three pigs with boosted health (25 HP instead of default 20)
        pig = Pig(950, 320, self.space)
        pig.life = 25  # Top pig - hardest to reach
        self.pigs.append(pig)
        pig = Pig(885, 225, self.space)
        pig.life = 25  # Mid-left pig
        self.pigs.append(pig)
        pig = Pig(1005, 225, self.space)
        pig.life = 25  # Mid-right pig
        self.pigs.append(pig)

        # Bottom layer: three pairs of columns with beams
        p = (1100, 100)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1070, 152)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (1040, 100)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (980, 100)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (920, 100)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (950, 152)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (1010, 180)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (860, 100)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (800, 100)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (830, 152)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (890, 180)
        self.beams.append(Polygon(p, 85, 20, self.space))

        # Middle layer: four columns with beams
        p = (860, 223)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (920, 223)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (980, 223)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1040, 223)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (890, 280)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (1010, 280)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (950, 300)
        self.beams.append(Polygon(p, 85, 20, self.space))

        # Top layer: two columns + one beam (peak of pyramid)
        p = (920, 350)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (980, 350)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (950, 400)
        self.beams.append(Polygon(p, 85, 20, self.space))

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_4(self) -> None:
        """Level 4 - Free-roaming pigs (no structures).

        Layout: Three pigs placed at various heights with no
        protective structures. Tests precision aiming.
        Difficulty: Medium (requires accurate shots at moving targets).
        """
        pig = Pig(900, 300, self.space)   # High pig
        self.pigs.append(pig)
        pig = Pig(1000, 500, self.space)  # Very high pig
        self.pigs.append(pig)
        pig = Pig(1100, 400, self.space)  # Mid-height pig
        self.pigs.append(pig)

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_5(self) -> None:
        """Level 5 - Beam walls with 2 pigs.

        Layout: Two pigs protected by vertical stacks of horizontal
        beams (beam walls). The left wall is taller (9 beams) while
        the right has a shorter wall (4 beams) with a frame on top.
        Difficulty: Medium (need to break through beam walls).
        """
        pig = Pig(900, 70, self.space)     # Behind left beam wall
        self.pigs.append(pig)
        pig = Pig(1000, 152, self.space)   # Inside right structure
        self.pigs.append(pig)

        # Left beam wall: 9 stacked horizontal beams
        for i in range(9):
            p = (800, 70 + i * 21)
            self.beams.append(Polygon(p, 85, 20, self.space))

        # Right beam wall: 4 stacked horizontal beams
        for i in range(4):
            p = (1000, 70 + i * 21)
            self.beams.append(Polygon(p, 85, 20, self.space))

        # Frame on top of right wall
        p = (970, 176)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1026, 176)
        self.columns.append(Polygon(p, 20, 85, self.space))
        p = (1000, 230)
        self.beams.append(Polygon(p, 85, 20, self.space))

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_6(self) -> None:
        """Level 6 - Tower fortress with 3 pigs (1 reinforced).

        Layout: A closed flat structure on top of a tall triple-column
        tower. One pig with high health (40 HP) is on top, two others
        are at various positions.
        Difficulty: Hard (tall tower, reinforced top pig).
        """
        pig = Pig(920, 533, self.space)
        pig.life = 40  # Boss pig with double health
        self.pigs.append(pig)
        pig = Pig(820, 533, self.space)
        self.pigs.append(pig)
        pig = Pig(720, 633, self.space)
        self.pigs.append(pig)

        # Closed frame structure near the top
        self.closed_flat(895, 423, 1)

        # Three parallel vertical column towers (foundation)
        self.vertical_pile(900, 0, 5)
        self.vertical_pile(926, 0, 5)
        self.vertical_pile(950, 0, 5)

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_7(self) -> None:
        """Level 7 - Three-story open structure with reinforced pigs.

        Layout: A three-story open flat structure flanked by two
        vertical column piles. Three pigs (30 HP each) occupy each
        floor of the structure.
        Difficulty: Hard (reinforced pigs, multi-story building).
        """
        # Three reinforced pigs on different floors
        pig = Pig(978, 180, self.space)
        pig.life = 30  # Second floor
        self.pigs.append(pig)
        pig = Pig(978, 280, self.space)
        pig.life = 30  # Third floor
        self.pigs.append(pig)
        pig = Pig(978, 80, self.space)
        pig.life = 30  # Ground floor
        self.pigs.append(pig)

        # Main three-story open frame structure
        self.open_flat(950, 0, 3)

        # Flanking vertical column piles (defensive barriers)
        self.vertical_pile(850, 0, 3)
        self.vertical_pile(830, 0, 3)

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_8(self) -> None:
        """Level 8 - Staircase structure with 3 reinforced pigs.

        Layout: Three open flat structures of decreasing height
        (3, 2, 1 stories) forming a staircase pattern. One pig
        at each level.
        Difficulty: Hard (multi-structure layout, reinforced pigs).
        """
        pig = Pig(1000, 180, self.space)
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(1078, 280, self.space)
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(900, 80, self.space)
        pig.life = 30
        self.pigs.append(pig)

        # Staircase: tallest on the right, shortest on the left
        self.open_flat(1050, 0, 3)  # 3-story (right)
        self.open_flat(963, 0, 2)   # 2-story (center)
        self.open_flat(880, 0, 1)   # 1-story (left)

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_9(self) -> None:
        """Level 9 - Four towers with 2 pigs.

        Layout: Four open flat structures of varying heights (3, 2, 2, 3)
        spread across the play area. Two standard-health pigs.
        Difficulty: Hard (many structures to navigate, fewer pigs to find).
        """
        pig = Pig(1000, 180, self.space)
        pig.life = 20
        self.pigs.append(pig)
        pig = Pig(900, 180, self.space)
        pig.life = 20
        self.pigs.append(pig)

        # Four towers spanning the right side of the screen
        self.open_flat(1050, 0, 3)  # Right-most (3 stories)
        self.open_flat(963, 0, 2)   # Center-right (2 stories)
        self.open_flat(880, 0, 2)   # Center-left (2 stories)
        self.open_flat(790, 0, 3)   # Left-most (3 stories)

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_10(self) -> None:
        """Level 10 - Fortress with beam barriers and 3 pigs.

        Layout: A central structure made of vertical column piles
        topped with horizontal beam piles. Two additional beam piles
        on the sides protect two more pigs.
        Difficulty: Very Hard (complex structure, multiple barriers).
        """
        pig = Pig(960, 250, self.space)  # Center (protected by beams)
        pig.life = 20
        self.pigs.append(pig)
        pig = Pig(820, 160, self.space)  # Left barrier pig
        self.pigs.append(pig)
        pig = Pig(1100, 160, self.space) # Right barrier pig
        self.pigs.append(pig)

        # Central structure: four vertical column piles
        self.vertical_pile(900, 0, 3)
        self.vertical_pile(930, 0, 3)
        self.vertical_pile(1000, 0, 3)
        self.vertical_pile(1030, 0, 3)

        # Horizontal beam pile on top of center structure
        self.horizontal_pile(970, 250, 2)

        # Side beam barriers protecting outer pigs
        self.horizontal_pile(820, 0, 4)   # Left barrier
        self.horizontal_pile(1100, 0, 4)  # Right barrier

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    def build_11(self) -> None:
        """Level 11 - Final level: Mixed structures with 4 pigs.

        Layout: The most complex level combining horizontal piles,
        vertical piles, and custom beam placements. Four pigs
        (including one reinforced at 30 HP) are spread across the
        structures.
        Difficulty: Very Hard (most pigs, complex layout, reinforced pig).
        """
        # Four pigs at various positions
        pig = Pig(820, 177, self.space)
        self.pigs.append(pig)
        pig = Pig(960, 150, self.space)
        self.pigs.append(pig)
        pig = Pig(1100, 130, self.space)
        self.pigs.append(pig)
        pig = Pig(890, 270, self.space)
        pig.life = 30  # Reinforced pig
        self.pigs.append(pig)

        # Horizontal beam piles of decreasing height
        self.horizontal_pile(800, 0, 5)   # Left (tallest)
        self.horizontal_pile(950, 0, 3)   # Center
        self.horizontal_pile(1100, 0, 2)  # Right (shortest)

        # Vertical column piles for structural support
        self.vertical_pile(745, 0, 2)
        self.vertical_pile(855, 0, 2)
        self.vertical_pile(900, 0, 2)
        self.vertical_pile(1000, 0, 2)

        # Additional standalone beam bridging two column piles
        p = (875, 230)
        self.beams.append(Polygon(p, 85, 20, self.space))

        self.number_of_birds = 4
        if self.bool_space:
            self.number_of_birds = 8

    # ===================================================================
    # Advanced Levels (12-14): Multi-structure castles
    # ===================================================================

    def build_12(self) -> None:
        """Level 12 - Five-tower castle with 3 pigs.

        Layout: Five open flat towers of varying heights (4, 3, 2, 3, 4)
        forming a castle silhouette. Pigs hidden in center and flank towers.
        Strategy: Weaken the middle tower to trigger cascade, or pick off
        flank pigs first.
        Difficulty: Advanced (5 birds, 1 reinforced pig).
        """
        pig = Pig(960, 180, self.space)   # Center tower (middle height)
        pig.life = 30  # Reinforced - hardest to reach
        self.pigs.append(pig)
        pig = Pig(850, 280, self.space)    # Left flank tower
        self.pigs.append(pig)
        pig = Pig(1070, 280, self.space)   # Right flank tower
        self.pigs.append(pig)

        # Five-tower castle: tallest on edges, dip in middle
        self.open_flat(790, 0, 4)   # Far left (4 stories)
        self.open_flat(880, 0, 3)   # Left-center (3 stories)
        self.open_flat(950, 0, 2)   # Center - lowest (2 stories)
        self.open_flat(1020, 0, 3)  # Right-center (3 stories)
        self.open_flat(1090, 0, 4)  # Far right (4 stories)

        self.number_of_birds = 5
        if self.bool_space:
            self.number_of_birds = 10
        self.one_star = 40000
        self.two_star = 55000
        self.three_star = 75000

    def build_13(self) -> None:
        """Level 13 - Twin fortress with 4 pigs.

        Layout: Two mirrored closed structures with beam barriers in front.
        Each fortress has a reinforced pig. Must breach both barriers or
        find angles to hit pigs through gaps.
        Difficulty: Advanced (5 birds, 2 reinforced pigs).
        """
        pig = Pig(860, 320, self.space)   # Left fortress (inside closed frame)
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(940, 320, self.space)   # Left fortress second pig
        self.pigs.append(pig)
        pig = Pig(1040, 320, self.space)  # Right fortress (inside closed frame)
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(1120, 320, self.space)  # Right fortress second pig
        self.pigs.append(pig)

        # Left closed fortress (2 stories) on top of beam barrier
        self.horizontal_pile(860, 0, 5)   # Left beam wall
        self.closed_flat(835, 230, 2)      # Left closed structure

        # Right closed fortress
        self.horizontal_pile(1040, 0, 5)   # Right beam wall
        self.closed_flat(1015, 230, 2)     # Right closed structure

        self.number_of_birds = 5
        if self.bool_space:
            self.number_of_birds = 10
        self.one_star = 45000
        self.two_star = 60000
        self.three_star = 80000

    def build_14(self) -> None:
        """Level 14 - Zigzag fortress with 4 pigs.

        Layout: Four staggered open flats creating a zigzag pattern.
        Pigs at different heights. Strategy: Use falling debris from
        upper structures to damage lower pigs - chain reaction required.
        Difficulty: Advanced (5 birds, mixed reinforcement).
        """
        pig = Pig(820, 80, self.space)    # Ground level left
        self.pigs.append(pig)
        pig = Pig(960, 180, self.space)   # Mid-height center
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(1100, 80, self.space)   # Ground level right
        self.pigs.append(pig)
        pig = Pig(960, 380, self.space)   # High center (above zigzag)
        self.pigs.append(pig)

        # Zigzag: left low, center high, right low (staggered)
        self.open_flat(800, 0, 1)    # Left (1 story - low)
        self.open_flat(930, 0, 3)    # Center (3 stories - high)
        self.open_flat(1060, 0, 1)   # Right (1 story - low)
        self.open_flat(930, 250, 2)   # Top center (2 stories above)

        # Vertical column supports between structures
        self.vertical_pile(870, 0, 2)
        self.vertical_pile(1040, 0, 2)

        self.number_of_birds = 5
        if self.bool_space:
            self.number_of_birds = 10
        self.one_star = 45000
        self.two_star = 62000
        self.three_star = 85000

    # ===================================================================
    # Strategic Levels (15-17): Chain-reaction puzzle layouts
    # ===================================================================

    def build_15(self) -> None:
        """Level 15 - Triple fortress with 5 pigs.

        Layout: Three separate fortified positions (closed flat + beams).
        Left, center, and right. Must choose attack order - collapsing
        one structure can help reach others. 5 pigs with 2 reinforced.
        Difficulty: Strategic (5 birds, plan your approach).
        """
        pig = Pig(780, 200, self.space)    # Left fortress
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(960, 250, self.space)   # Center fortress (reinforced)
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(1140, 200, self.space)   # Right fortress
        self.pigs.append(pig)
        pig = Pig(870, 350, self.space)   # Left upper
        self.pigs.append(pig)
        pig = Pig(1050, 350, self.space)   # Right upper
        self.pigs.append(pig)

        # Left fortress: beam pile + closed flat
        self.horizontal_pile(780, 0, 4)
        self.closed_flat(755, 150, 2)

        # Center fortress: taller
        self.horizontal_pile(960, 0, 6)
        self.closed_flat(935, 120, 2)

        # Right fortress
        self.horizontal_pile(1140, 0, 4)
        self.closed_flat(1115, 150, 2)

        self.number_of_birds = 5
        if self.bool_space:
            self.number_of_birds = 10
        self.one_star = 50000
        self.two_star = 70000
        self.three_star = 90000

    def build_16(self) -> None:
        """Level 16 - Domino palace with 5 pigs.

        Layout: Interconnected beam walls and columns. One good shot can
        trigger a chain reaction. Pigs scattered - some behind beams,
        some vulnerable to falling debris. Requires domino planning.
        Difficulty: Strategic (5 birds, chain-reaction focus).
        """
        pig = Pig(750, 90, self.space)     # Far left
        self.pigs.append(pig)
        pig = Pig(900, 180, self.space)   # Left-center
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(960, 270, self.space)   # Center (high)
        self.pigs.append(pig)
        pig = Pig(1020, 180, self.space)   # Right-center
        self.pigs.append(pig)
        pig = Pig(1150, 90, self.space)    # Far right
        self.pigs.append(pig)

        # Domino layout: beams that can topple into each other
        self.horizontal_pile(750, 0, 6)    # Left wall
        self.horizontal_pile(900, 0, 5)    # Left-center
        self.vertical_pile(955, 0, 3)      # Center support
        self.horizontal_pile(1020, 0, 5)   # Right-center
        self.horizontal_pile(1150, 0, 6)    # Right wall

        # Bridging beams that connect structures
        p = (875, 140)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (1045, 140)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (960, 340)
        self.beams.append(Polygon(p, 85, 20, self.space))

        self.number_of_birds = 5
        if self.bool_space:
            self.number_of_birds = 10
        self.one_star = 55000
        self.two_star = 75000
        self.three_star = 95000

    def build_17(self) -> None:
        """Level 17 - High-rise challenge with 5 pigs.

        Layout: Very tall vertical column towers (6 high) with open flats
        on top. Pigs at multiple heights - some at top, some mid-tower.
        Strategy: Topple the towers to bring down upper pigs, or snipe
        the mid-level pigs through structure gaps.
        Difficulty: Strategic (5 birds, 3 reinforced pigs).
        """
        pig = Pig(880, 550, self.space)    # Left tower top
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(960, 400, self.space)    # Center mid-level
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(1040, 550, self.space)   # Right tower top
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(920, 250, self.space)    # Left lower
        self.pigs.append(pig)
        pig = Pig(1000, 250, self.space)   # Right lower
        self.pigs.append(pig)

        # Three tall towers (6 columns each) with open frames on top
        self.vertical_pile(860, 0, 6)
        self.open_flat(845, 400, 2)       # Left tower cap

        self.vertical_pile(940, 0, 6)
        self.vertical_pile(960, 0, 4)     # Center double-stack
        self.open_flat(945, 350, 1)      # Center cap

        self.vertical_pile(1020, 0, 6)
        self.open_flat(1005, 400, 2)      # Right tower cap

        self.number_of_birds = 5
        if self.bool_space:
            self.number_of_birds = 10
        self.one_star = 55000
        self.two_star = 78000
        self.three_star = 100000

    # ===================================================================
    # Expert Levels (18-20): Maximum complexity
    # ===================================================================

    def build_18(self) -> None:
        """Level 18 - The gauntlet with 6 pigs.

        Layout: Long horizontal spread - beam walls at left and right,
        vertical piles in between, closed frames in center. Six pigs
        across the entire width. Must clear a path through multiple
        barriers. No single shot wins; sustained assault required.
        Difficulty: Expert (6 birds, 2 reinforced).
        """
        pig = Pig(760, 90, self.space)     # Far left
        self.pigs.append(pig)
        pig = Pig(860, 200, self.space)   # Left-center
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(960, 280, self.space)   # Center
        self.pigs.append(pig)
        pig = Pig(1060, 200, self.space)   # Right-center
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(1160, 90, self.space)   # Far right
        self.pigs.append(pig)
        pig = Pig(960, 150, self.space)   # Center high
        self.pigs.append(pig)

        # Full gauntlet layout
        self.horizontal_pile(760, 0, 6)    # Left barrier
        self.vertical_pile(820, 0, 3)
        self.closed_flat(870, 100, 2)      # Left closed block
        self.vertical_pile(955, 0, 4)      # Center support
        self.closed_flat(1005, 100, 2)      # Right closed block
        self.vertical_pile(1090, 0, 3)
        self.horizontal_pile(1140, 0, 6)   # Right barrier

        # Cross beams
        p = (920, 330)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (1000, 330)
        self.beams.append(Polygon(p, 85, 20, self.space))

        self.number_of_birds = 6
        if self.bool_space:
            self.number_of_birds = 12
        self.one_star = 60000
        self.two_star = 85000
        self.three_star = 110000

    def build_19(self) -> None:
        """Level 19 - Boss fortress with 5 pigs.

        Layout: Massive multi-layer fortress. Boss pig (40 HP) at the
        peak, protected by four supporting pigs in lower layers.
        Multiple closed frames and beam barriers. One wrong shot wastes
        a bird; must weaken the base before targeting the boss.
        Difficulty: Expert (6 birds, boss pig 40 HP).
        """
        pig = Pig(960, 500, self.space)    # Boss at peak
        pig.life = 40
        self.pigs.append(pig)
        pig = Pig(880, 350, self.space)   # Left support
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(1040, 350, self.space)  # Right support
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(920, 200, self.space)   # Left base
        self.pigs.append(pig)
        pig = Pig(1000, 200, self.space)  # Right base
        self.pigs.append(pig)

        # Pyramid-style boss fortress
        self.closed_flat(935, 0, 2)       # Base layer
        self.closed_flat(945, 180, 2)     # Second layer
        self.open_flat(955, 350, 2)       # Top layer (boss chamber)
        self.vertical_pile(900, 0, 4)    # Left reinforcement
        self.vertical_pile(1020, 0, 4)   # Right reinforcement
        self.horizontal_pile(960, 420, 2) # Boss platform beams

        self.number_of_birds = 6
        if self.bool_space:
            self.number_of_birds = 12
        self.one_star = 70000
        self.two_star = 95000
        self.three_star = 120000

    def build_20(self) -> None:
        """Level 20 - Final challenge with 6 pigs.

        Layout: Everything combined - dual boss pigs (40 HP each), complex
        chain-reaction layout, beam walls, vertical towers, closed frames.
        Four supporting pigs (2 reinforced). The ultimate test. Master
        chain reactions and precise aim to clear with minimal birds.
        Difficulty: Expert (6 birds, 2 boss pigs, maximum strategy).
        """
        pig = Pig(880, 450, self.space)    # Left boss
        pig.life = 40
        self.pigs.append(pig)
        pig = Pig(1040, 450, self.space)  # Right boss
        pig.life = 40
        self.pigs.append(pig)
        pig = Pig(920, 280, self.space)   # Left support
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(1000, 280, self.space)  # Right support
        pig.life = 30
        self.pigs.append(pig)
        pig = Pig(960, 150, self.space)   # Center base
        self.pigs.append(pig)
        pig = Pig(960, 350, self.space)   # Center mid (between bosses)
        self.pigs.append(pig)

        # Ultimate fortress: dual towers with shared base
        self.horizontal_pile(800, 0, 5)    # Left barrier
        self.horizontal_pile(1120, 0, 5)   # Right barrier
        self.closed_flat(890, 0, 2)       # Left base structure
        self.closed_flat(1010, 0, 2)      # Right base structure
        self.vertical_pile(930, 180, 4)   # Left tower
        self.vertical_pile(990, 180, 4)   # Right tower
        self.open_flat(935, 350, 2)       # Left boss platform
        self.open_flat(985, 350, 2)       # Right boss platform
        # Bridging beams that connect the two boss platforms
        p = (960, 420)
        self.beams.append(Polygon(p, 85, 20, self.space))
        p = (960, 300)
        self.beams.append(Polygon(p, 85, 20, self.space))

        self.number_of_birds = 6
        if self.bool_space:
            self.number_of_birds = 12
        self.one_star = 80000
        self.two_star = 110000
        self.three_star = 140000

    # ===================================================================
    # Level Loader
    # ===================================================================

    def load_level(self) -> None:
        """Dynamically load the current level by calling the corresponding build method.

        Uses Python's getattr() to dynamically resolve the build method
        name from self.number (e.g., number=3 -> calls self.build_3()).
        If the level number exceeds available levels, it wraps back to 0.
        """
        try:
            build_name = "build_" + str(self.number)
            getattr(self, build_name)()
        except AttributeError:
            # Level doesn't exist: wrap back to level 0
            self.number = 0
            build_name = "build_" + str(self.number)
            getattr(self, build_name)()
