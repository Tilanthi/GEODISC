"""
Physics Simulation Engine

Simulates physical phenomena for grounded understanding.
Includes classical mechanics, electromagnetism, and orbital mechanics.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class Particle:
    """A particle in physical space."""
    position: np.ndarray
    velocity: np.ndarray
    mass: float
    charge: float = 0.0
    radius: float = 1.0


class PhysicsSimulator:
    """
    Simulate physical systems.

    Supports:
    - Classical mechanics (Newtonian)
    - N-body gravitational systems
    - Electromagnetic interactions
    """

    def __init__(self,
                 time_step: float = 0.01,
                 dimensions: int = 3):
        self.time_step = time_step
        self.dimensions = dimensions
        self.particles: List[Particle] = []

    def add_particle(self,
                    position: np.ndarray,
                    velocity: np.ndarray,
                    mass: float = 1.0,
                    charge: float = 0.0) -> int:
        """Add particle to simulation."""
        particle = Particle(
            position=np.array(position, dtype=float),
            velocity=np.array(velocity, dtype=float),
            mass=mass,
            charge=charge
        )
        self.particles.append(particle)
        return len(self.particles) - 1

    def simulate_gravity(self,
                         G: float = 1.0,
                         softening: float = 0.1,
                         steps: int = 100) -> List[np.ndarray]:
        """
        Simulate N-body gravitational system.

        Args:
            G: Gravitational constant
            softening: Softening parameter to prevent singularities
            steps: Number of simulation steps

        Returns:
            List of particle positions over time
        """
        trajectories = []

        for _ in range(steps):
            # Record positions
            positions = np.array([p.position for p in self.particles])
            trajectories.append(positions.copy())

            # Compute accelerations
            accelerations = self._compute_gravitational_acceleration(G, softening)

            # Update velocities (leapfrog)
            for i, p in enumerate(self.particles):
                p.velocity += accelerations[i] * self.time_step

            # Update positions
            for p in self.particles:
                p.position += p.velocity * self.time_step

        return trajectories

    def _compute_gravitational_acceleration(self,
                                            G: float,
                                            softening: float) -> np.ndarray:
        """Compute gravitational acceleration for all particles."""
        n = len(self.particles)
        accelerations = np.zeros((n, self.dimensions))

        for i, p1 in enumerate(self.particles):
            for j, p2 in enumerate(self.particles):
                if i == j:
                    continue

                # Vector from p1 to p2
                r_vec = p2.position - p1.position
                r_mag = np.linalg.norm(r_vec)

                # Gravitational force: F = G * m1 * m2 / r^2
                # Acceleration: a = F / m1 = G * m2 / r^2
                # Direction: toward p2
                force_mag = G * p2.mass / (r_mag**2 + softening**2)
                accel_vec = force_mag * r_vec / (r_mag + softening)

                accelerations[i] += accel_vec

        return accelerations

    def simulate_electromagnetic(self,
                                 k_e: float = 1.0,
                                 steps: int = 100) -> List[np.ndarray]:
        """
        Simulate electromagnetic interactions.

        Args:
            k_e: Coulomb constant
            steps: Number of simulation steps

        Returns:
            List of particle positions over time
        """
        trajectories = []

        for _ in range(steps):
            positions = np.array([p.position for p in self.particles])
            trajectories.append(positions.copy())

            # Compute electromagnetic accelerations
            accelerations = self._compute_em_acceleration(k_e)

            # Update velocities and positions
            for i, p in enumerate(self.particles):
                p.velocity += accelerations[i] * self.time_step
                p.position += p.velocity * self.time_step

        return trajectories

    def _compute_em_acceleration(self, k_e: float) -> np.ndarray:
        """Compute electromagnetic acceleration."""
        n = len(self.particles)
        accelerations = np.zeros((n, self.dimensions))

        for i, p1 in enumerate(self.particles):
            for j, p2 in enumerate(self.particles):
                if i == j:
                    continue

                if p1.charge == 0 or p2.charge == 0:
                    continue

                # Coulomb force: F = k_e * q1 * q2 / r^2
                r_vec = p1.position - p2.position
                r_mag = np.linalg.norm(r_vec)

                force_mag = k_e * p1.charge * p2.charge / (r_mag**2 + 0.01)
                accel_vec = force_mag * r_vec / (r_mag + 0.01)

                accelerations[i] += accel_vec / p1.mass

        return accelerations

    def get_system_energy(self) -> Dict[str, float]:
        """Get total kinetic and potential energy."""
        kinetic = 0.0
        potential = 0.0

        for p in self.particles:
            # Kinetic energy: 0.5 * m * v^2
            kinetic += 0.5 * p.mass * np.linalg.norm(p.velocity)**2

        # Potential energy (gravitational)
        G = 1.0
        for i, p1 in enumerate(self.particles):
            for j in range(i+1, len(self.particles)):
                p2 = self.particles[j]
                r = np.linalg.norm(p1.position - p2.position)
                potential -= G * p1.mass * p2.mass / r

        return {'kinetic': kinetic, 'potential': potential, 'total': kinetic + potential}
