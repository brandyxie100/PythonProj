"""
Angry Birds Clone - Polygon Module
====================================
Defines the Polygon class representing wooden structural elements
(beams and columns) used to build destructible structures in each level.

Each Polygon is a pymunk box-shaped rigid body with a wood texture
rendered via Pygame. They interact with birds and pigs through
collision type 2 (Wood).

Updated for Python 3.12+ and Pymunk 7.x compatibility.
"""

import math
import os

import pymunk as pm
from pymunk import Vec2d
import pygame

# Resolve resource paths relative to this script's directory so loading
# works regardless of the current working directory.
_SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
_RESOURCE_DIR: str = os.path.join(_SCRIPT_DIR, "..", "resources")


def _res(relative_path: str) -> str:
    """Build an absolute path to a resource file.

    Args:
        relative_path: Path relative to the resources/ directory.

    Returns:
        The absolute file-system path to the resource.
    """
    return os.path.join(_RESOURCE_DIR, relative_path)


class Polygon:
    """A wooden structural element (beam or column) with physics and rendering.

    Polygons are rectangular pymunk bodies that form the destructible
    structures in each level. They can be either horizontal beams or
    vertical columns, distinguished by their width/height ratio and
    the texture applied during rendering.

    Note:
        Wood textures are loaded from disk each time a Polygon is created.
        For a production game, consider caching these textures to improve
        loading performance.

    Attributes:
        body (pm.Body): The pymunk rigid body for physics simulation.
        shape (pm.Poly): The pymunk box collision shape.
        beam_image (pygame.Surface): Texture sprite for horizontal beams.
        column_image (pygame.Surface): Texture sprite for vertical columns.
    """

    def __init__(
        self,
        pos: tuple[float, float],
        length: int,
        height: int,
        space: pm.Space,
        mass: float = 5.0,
    ) -> None:
        """Create a new wooden Polygon (beam or column).

        Args:
            pos: Position (x, y) in pymunk world coordinates.
            length: Width of the box shape in pixels.
            height: Height of the box shape in pixels.
            space: The pymunk Space to add this polygon's body and shape to.
            mass: Mass of the body (default 5.0).
        """
        # Physics body configuration
        moment: float = 1000  # Moment of inertia (rotational resistance)
        body: pm.Body = pm.Body(mass, moment)
        body.position = Vec2d(*pos)

        # Create a box-shaped collision polygon
        shape: pm.Poly = pm.Poly.create_box(body, (length, height))
        shape.friction = 0.5  # Moderate friction for wood surfaces
        shape.collision_type = 2  # Type 2 = Wood (used by collision handlers)

        # Add the body and shape to the physics space
        space.add(body, shape)

        # Store references for external access
        self.body: pm.Body = body
        self.shape: pm.Poly = shape

        # Load wood texture sprite sheets
        wood: pygame.Surface = pygame.image.load(
            _res("images/wood.png")
        ).convert_alpha()
        wood2: pygame.Surface = pygame.image.load(
            _res("images/wood2.png")
        ).convert_alpha()

        # Crop the beam texture (horizontal plank) from the sprite sheet
        rect = pygame.Rect(251, 357, 86, 22)
        self.beam_image: pygame.Surface = wood.subsurface(rect).copy()

        # Crop the column texture (vertical post) from the sprite sheet
        rect = pygame.Rect(16, 252, 22, 84)
        self.column_image: pygame.Surface = wood2.subsurface(rect).copy()

    def to_pygame(self, p: Vec2d) -> tuple[int, int]:
        """Convert pymunk physics coordinates to pygame screen coordinates.

        Pymunk Y-axis points upward; Pygame Y-axis points downward.
        This flips the Y coordinate and offsets by 600.

        Args:
            p: A pymunk Vec2d position vector.

        Returns:
            A (x, y) tuple in pygame screen coordinates.
        """
        return int(p.x), int(-p.y + 600)

    def draw_poly(self, element: str, screen: pygame.Surface) -> None:
        """Draw this polygon's wireframe outline and wood texture.

        The polygon's vertices are converted from pymunk to pygame
        coordinates, a red wireframe outline is drawn, and then the
        appropriate wood texture (beam or column) is rendered with
        rotation matching the physics body's angle.

        Args:
            element: Either 'beams' or 'columns', determining which
                     wood texture to render.
            screen: The pygame Surface to draw on.
        """
        poly = self.shape

        # Get the polygon vertices in world coordinates and close the loop
        ps = poly.get_vertices()
        ps.append(ps[0])

        # Convert all vertices to pygame screen coordinates
        ps = map(self.to_pygame, ps)
        ps = list(ps)

        # Draw a red wireframe outline of the polygon shape
        color = (255, 0, 0)
        pygame.draw.lines(screen, color, False, ps)

        if element == "beams":
            # Render the horizontal beam wood texture
            p = poly.body.position
            p = Vec2d(*self.to_pygame(p))

            # Rotate the texture to match the physics body rotation
            # Add 180 degrees to correct texture orientation
            angle_degrees = math.degrees(poly.body.angle) + 180
            rotated_logo_img = pygame.transform.rotate(self.beam_image, angle_degrees)

            # Center the rotated image on the body's position
            offset = Vec2d(*rotated_logo_img.get_size()) / 2.0
            p = p - offset
            np = p
            screen.blit(rotated_logo_img, (np.x, np.y))

        if element == "columns":
            # Render the vertical column wood texture
            p = poly.body.position
            p = Vec2d(*self.to_pygame(p))

            # Rotate the texture to match the physics body rotation
            angle_degrees = math.degrees(poly.body.angle) + 180
            rotated_logo_img = pygame.transform.rotate(self.column_image, angle_degrees)

            # Center the rotated image on the body's position
            offset = Vec2d(*rotated_logo_img.get_size()) / 2.0
            p = p - offset
            np = p
            screen.blit(rotated_logo_img, (np.x, np.y))
