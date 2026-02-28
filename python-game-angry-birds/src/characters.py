"""
Angry Birds Clone - Characters Module
======================================
Defines the physics-based game characters: Bird and Pig.

Both characters are represented as pymunk Circle shapes attached to
dynamic bodies. Their collision types are used by the collision
handlers in main.py to determine interaction behavior:
    - collision_type 0 = Bird
    - collision_type 1 = Pig

Updated for Python 3.12+ and Pymunk 7.x compatibility.
"""

import pymunk as pm
from pymunk import Vec2d


class Bird:
    """A launchable bird projectile with physics properties.

    The bird is created at a fixed spawn point near the slingshot and
    immediately receives an impulse based on the sling's pull distance
    and angle. Once launched, it follows the pymunk physics simulation
    (gravity, collisions, friction).

    Attributes:
        life (int): Hit points of the bird (default 20).
        body (pm.Body): The pymunk rigid body for physics simulation.
        shape (pm.Circle): The pymunk circle collision shape.
    """

    def __init__(
        self, distance: float, angle: float, x: float, y: float, space: pm.Space
    ) -> None:
        """Create a new Bird and launch it with an impulse.

        Args:
            distance: Pull distance of the slingshot (determines launch power).
                      Positive = leftward pull, negative = rightward pull.
            angle: Launch angle in radians (calculated from sling direction).
            x: Spawn X position in pymunk world coordinates.
            y: Spawn Y position in pymunk world coordinates.
            space: The pymunk Space to add this bird's body and shape to.
        """
        self.life: int = 20

        # Physics body configuration
        mass: float = 5  # Bird mass in arbitrary units
        radius: float = 12  # Collision circle radius in pixels
        inertia: float = pm.moment_for_circle(mass, 0, radius, (0, 0))
        body: pm.Body = pm.Body(mass, inertia)
        body.position = x, y

        # Calculate and apply launch impulse
        # Power scales linearly with sling pull distance
        power: float = distance * 53
        impulse: Vec2d = power * Vec2d(1, 0)  # Base impulse along X-axis
        angle = -angle  # Negate angle (screen Y is inverted vs. pymunk Y)
        body.apply_impulse_at_local_point(impulse.rotated(angle))

        # Collision shape configuration
        shape: pm.Circle = pm.Circle(body, radius, (0, 0))
        shape.elasticity = 0.95  # High bounciness
        shape.friction = 1  # Full friction
        shape.collision_type = 0  # Type 0 = Bird (used by collision handlers)

        # Add the body and shape to the physics space
        space.add(body, shape)

        # Store references for external access (rendering, collision checks)
        self.body: pm.Body = body
        self.shape: pm.Circle = shape


class Pig:
    """A destructible pig target that the player must eliminate.

    Pigs are static targets placed in each level. They can be destroyed
    by direct bird impacts or by being crushed by falling wooden structures.
    Each pig has hit points; when reduced to zero, the pig is removed.

    Attributes:
        life (int): Hit points of the pig (default 20, can be customized).
        body (pm.Body): The pymunk rigid body for physics simulation.
        shape (pm.Circle): The pymunk circle collision shape.
    """

    def __init__(self, x: float, y: float, space: pm.Space) -> None:
        """Create a new Pig at the specified position.

        Args:
            x: X position in pymunk world coordinates.
            y: Y position in pymunk world coordinates.
            space: The pymunk Space to add this pig's body and shape to.
        """
        self.life: int = 20

        # Physics body configuration
        mass: float = 5  # Pig mass in arbitrary units
        radius: float = 14  # Collision circle radius (slightly larger than bird)
        inertia: float = pm.moment_for_circle(mass, 0, radius, (0, 0))
        body: pm.Body = pm.Body(mass, inertia)
        body.position = x, y

        # Collision shape configuration
        shape: pm.Circle = pm.Circle(body, radius, (0, 0))
        shape.elasticity = 0.95  # High bounciness
        shape.friction = 1  # Full friction
        shape.collision_type = 1  # Type 1 = Pig (used by collision handlers)

        # Add the body and shape to the physics space
        space.add(body, shape)

        # Store references for external access (rendering, collision checks)
        self.body: pm.Body = body
        self.shape: pm.Circle = shape
