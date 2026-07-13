"""
Theory Refutation Engine

Systematically tests theoretical proposals against ALL known constraints
simultaneously to rapidly identify unviable theories and guide refinement.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ConstraintType(Enum):
    """Types of constraints to test against"""
    MATHEMATICAL = "mathematical"  # Well-posedness, regularity
    PHYSICAL = "physical"  # Conservation laws, thermodynamics
    QUANTUM = "quantum"  # Unitarity, uncertainty principle
    RELATIVISTIC = "relativistic"  # Causality, Lorentz invariance
    OBSERVATIONAL = "observational"  # Agreement with data
    THEORETICAL = "theoretical"  # Consistency with established theory


class Severity(Enum):
    """Severity of constraint violations"""
    FATAL = "fatal"  # Theory is completely unviable
    SEVERE = "severe"  # Major revision needed
    MODERATE = "moderate"  # Significant concerns
    MILD = "mild"  # Minor issues or limitations
    INFO = "info"  # Informational note


@dataclass
class ConstraintViolation:
    """A constraint violation found during testing"""
    constraint_name: str
    constraint_type: ConstraintType
    severity: Severity
    description: str
    location: Optional[str] = None  # Where in the theory
    suggested_fix: Optional[str] = None
    confidence: float = 1.0  # How certain we are about this violation


@dataclass
class TheoryTestResult:
    """Result of testing a theory against constraints"""
    theory_name: str
    total_constraints_tested: int
    violations: List[ConstraintViolation]
    is_viable: bool
    viability_score: float  # 0-1
    fatal_violations: List[ConstraintViolation] = field(default_factory=list)
    warnings: List[ConstraintViolation] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class MathematicalConsistencyChecker:
    """Checks mathematical consistency of theoretical frameworks"""

    @staticmethod
    def check_well_posedness(equation: str, variables: List[str]) -> List[ConstraintViolation]:
        """Check if PDE/problem is well-posed"""
        violations = []

        # Basic checks (simplified - production would use proper PDE analysis)
        if '=' not in equation:
            violations.append(ConstraintViolation(
                constraint_name="well_posedness",
                constraint_type=ConstraintType.MATHEMATICAL,
                severity=Severity.FATAL,
                description="Not an equation (no equals sign)"
            ))

        # Check for common issues
        if '∞' in equation and 'limit' not in equation.lower():
            violations.append(ConstraintViolation(
                constraint_name="regularity",
                constraint_type=ConstraintType.MATHEMATICAL,
                severity=Severity.SEVERE,
                description="Potential singularity - needs limiting procedure",
                suggested_fix="Add regularization or specify limiting behavior"
            ))

        return violations

    @staticmethod
    def check_dimensional_consistency(equation: str) -> List[ConstraintViolation]:
        """Check dimensional consistency of equation"""
        violations = []

        # Simplified check - production would parse units
        # For now, just check for common dimensional mismatches
        lhs, rhs = equation.split('=') if '=' in equation else ('', '')

        # Very basic heuristic
        if 'energy' in lhs.lower() and 'velocity' in rhs.lower():
            # Energy can't equal velocity (dimensional mismatch)
            violations.append(ConstraintViolation(
                constraint_name="dimensional_consistency",
                constraint_type=ConstraintType.MATHEMATICAL,
                severity=Severity.FATAL,
                description="Dimensional mismatch detected",
                suggested_fix="Check units on both sides of equation"
            ))

        return violations

    @staticmethod
    def check_stability(analysis: str) -> List[ConstraintViolation]:
        """Check for stability issues"""
        violations = []

        # Look for potential instability indicators
        instability_keywords = {
            'exponential_growth': Severity.SEVERE,
            'runaway_solution': Severity.SEVERE,
            'negative_energy': Severity.FATAL,
            'imaginary_frequency': Severity.MODERATE,
        }

        for keyword, severity in instability_keywords.items():
            if keyword in analysis.lower():
                violations.append(ConstraintViolation(
                    constraint_name="stability",
                    constraint_type=ConstraintType.MATHEMATICAL,
                    severity=severity,
                    description=f"Potential instability: {keyword}",
                    suggested_fix="Add damping or check boundary conditions"
                ))

        return violations


class PhysicalConstraintsChecker:
    """Checks against fundamental physical constraints"""

    # Physical limits and constraints
    SPEED_LIMIT = 2.998e10  # c in cm/s
    GRAVITATIONAL_CONSTANT = 6.674e-8  # cgs
    BOLTZMANN_CONSTANT = 1.381e-16  # cgs
    PLANCK_CONSTANT = 6.626e-27  # cgs

    @classmethod
    def check_conservation_laws(
        cls,
        theory: Dict[str, Any]
    ) -> List[ConstraintViolation]:
        """Check conservation laws"""
        violations = []

        # Energy conservation
        if 'energy' in theory:
            if theory.get('energy_creation', False):
                violations.append(ConstraintViolation(
                    constraint_name="energy_conservation",
                    constraint_type=ConstraintType.PHYSICAL,
                    severity=Severity.FATAL,
                    description="Theory creates energy (violates conservation)",
                    suggested_fix="Add energy sink or modify theory to conserve energy"
                ))

        # Momentum conservation
        if 'momentum' in theory:
            if theory.get('external_force_without_reaction', False):
                violations.append(ConstraintViolation(
                    constraint_name="momentum_conservation",
                    constraint_type=ConstraintType.PHYSICAL,
                    severity=Severity.FATAL,
                    description="Action without reaction (violates Newton's 3rd law)",
                    suggested_fix="Include reaction forces or use non-inertial frame with fictitious forces"
                ))

        # Charge conservation
        if 'charge' in theory:
            if theory.get('charge_non_conservation', False):
                violations.append(ConstraintViolation(
                    constraint_name="charge_conservation",
                    constraint_type=ConstraintType.PHYSICAL,
                    severity=Severity.FATAL,
                    description="Electric charge not conserved",
                    suggested_fix="Include current sources/sinks or conserve charge"
                ))

        return violations

    @classmethod
    def check_thermodynamics(cls, theory: Dict[str, Any]) -> List[ConstraintViolation]:
        """Check thermodynamic constraints"""
        violations = []

        # Temperature positivity
        if 'temperature' in theory:
            temp = theory.get('temperature', 0)
            if temp < 0:
                violations.append(ConstraintViolation(
                    constraint_name="temperature_positivity",
                    constraint_type=ConstraintType.PHYSICAL,
                    severity=Severity.FATAL,
                    description=f"Negative temperature: {temp} K",
                    suggested_fix="Temperature must be positive in standard thermodynamics"
                ))

        # Entropy non-decrease (isolated system)
        if 'entropy_change' in theory:
            delta_S = theory.get('entropy_change', 0)
            if delta_S < 0 and theory.get('isolated', False):
                violations.append(ConstraintViolation(
                    constraint_name="entropy_law",
                    constraint_type=ConstraintType.PHYSICAL,
                    severity=Severity.FATAL,
                    description="Entropy decreases in isolated system",
                    suggested_fix="System may not be isolated or entropy not properly calculated"
                ))

        # Heat flows hot to cold
        if 'heat_flow' in theory:
            # Simplified check
            violations.append(ConstraintViolation(
                constraint_name="second_law",
                constraint_type=ConstraintType.PHYSICAL,
                severity=Severity.INFO,
                description="Verify heat flow direction (hot to cold)",
                suggested_fix="Check temperature gradient"
            ))

        return violations

    @classmethod
    def check_speed_limit(cls, theory: Dict[str, Any]) -> List[ConstraintViolation]:
        """Check nothing exceeds speed of light"""
        violations = []

        if 'velocity' in theory:
            velocity = theory.get('velocity', 0)
            if abs(velocity) > cls.SPEED_LIMIT:
                violations.append(ConstraintViolation(
                    constraint_name="speed_limit",
                    constraint_type=ConstraintType.RELATIVISTIC,
                    severity=Severity.FATAL,
                    description=f"Velocity {velocity} cm/s exceeds speed of light",
                    suggested_fix="Use relativistic velocity addition or reduce velocity"
                ))

        return violations

    @classmethod
    def check_positivity_definiteness(cls, theory: Dict[str, Any]) -> List[ConstraintViolation]:
        """Check physical quantities are positive/definite where required"""
        violations = []

        positive_quantities = ['mass', 'density', 'pressure', 'energy_density']

        for quantity in positive_quantities:
            if quantity in theory:
                value = theory.get(quantity, 0)
                if isinstance(value, (int, float)) and value < 0:
                    violations.append(ConstraintViolation(
                        constraint_name=f"{quantity}_positivity",
                        constraint_type=ConstraintType.PHYSICAL,
                        severity=Severity.FATAL,
                        description=f"{quantity} is negative: {value}",
                        suggested_fix=f"{quantity} must be non-negative"
                    ))

        return violations


class QuantumConstraintsChecker:
    """Checks quantum mechanical constraints"""

    @staticmethod
    def check_uncertainty_principle(
        observables: Dict[str, float]
    ) -> List[ConstraintViolation]:
        """Check uncertainty principle constraints"""
        violations = []

        # Position-momentum uncertainty
        if 'position_uncertainty' in observables and 'momentum_uncertainty' in observables:
            delta_x = observables['position_uncertainty']
            delta_p = observables['momentum_uncertainty']

            h_bar = 1.055e-27  # erg*s
            product = delta_x * delta_p

            if product < h_bar / 2:
                violations.append(ConstraintViolation(
                    constraint_name="uncertainty_principle",
                    constraint_type=ConstraintType.QUANTUM,
                    severity=Severity.FATAL,
                    description=f"Uncertainty principle violated: Δx·Δp = {product:.3e} < ħ/2",
                    suggested_fix="Increase uncertainties or reconsider quantum state preparation"
                ))

        return violations

    @staticmethod
    def check_unitarity(theory: Dict[str, Any]) -> List[ConstraintViolation]:
        """Check unitarity (probability conservation)"""
        violations = []

        if 'total_probability' in theory:
            prob = theory['total_probability']

            if abs(prob - 1.0) > 0.01:  # Allow small numerical error
                violations.append(ConstraintViolation(
                    constraint_name="unitarity",
                    constraint_type=ConstraintType.QUANTUM,
                    severity=Severity.FATAL,
                    description=f"Unitarity violated: P = {prob} ≠ 1",
                    suggested_fix="Renormalize probabilities or check calculation"
                ))

        return violations


class RelativisticConstraintsChecker:
    """Checks relativistic constraints"""

    @staticmethod
    def check_causality(spacetime: Dict[str, Any]) -> List[ConstraintViolation]:
        """Check causality preservation"""
        violations = []

        # Check for closed timelike curves
        if 'metric_signature' in spacetime:
            signature = spacetime['metric_signature']
            if signature != '(1,3)' and signature != '(3,1)':
                violations.append(ConstraintViolation(
                    constraint_name="causality",
                    constraint_type=ConstraintType.RELATIVISTIC,
                    severity=Severity.SEVERE,
                    description=f"Unusual metric signature: {signature}",
                    suggested_fix="Verify metric signature or check for CTCs"
                ))

        return violations

    @staticmethod
    def check_energy_conditions(stress_energy: Dict[str, Any]) -> List[ConstraintViolation]:
        """Check energy conditions"""
        violations = []

        # Weak energy condition: T_μν u^μ u^ν ≥ 0 for timelike u
        if 'energy_density' in stress_energy:
            rho = stress_energy['energy_density']
            if rho < 0:
                violations.append(ConstraintViolation(
                    constraint_name="weak_energy_condition",
                    constraint_type=ConstraintType.RELATIVISTIC,
                    severity=Severity.SEVERE,
                    description=f"Negative energy density: {rho}",
                    suggested_fix="Check stress-energy tensor or consider exotic matter"
                ))

        return violations


class ObservationalConstraintsChecker:
    """Checks against observational data"""

    ASTROPHYSICAL_CONSTANTS = {
        'Hubble_constant': (70, 10),  # km/s/Mpc with uncertainty
        'matter_density': (0.3, 0.1),  # Omega_m
        'dark_energy_density': (0.7, 0.1),  # Omega_Lambda
        'CMB_temperature': (2.725, 0.001),  # K
    }

    @classmethod
    def check_constant_consistency(
        cls,
        theory_constants: Dict[str, float]
    ) -> List[ConstraintViolation]:
        """Check if theory constants match observations"""
        violations = []

        for const_name, (value, uncertainty) in cls.ASTROPHYSICAL_CONSTANTS.items():
            if const_name in theory_constants:
                theory_value = theory_constants[const_name]
                sigma = abs(theory_value - value) / uncertainty

                if sigma > 3:  # More than 3 sigma away
                    violations.append(ConstraintViolation(
                        constraint_name=f"{const_name}_consistency",
                        constraint_type=ConstraintType.OBSERVATIONAL,
                        severity=Severity.SEVERE,
                        description=f"{const_name} = {theory_value}, observed = {value} ± {uncertainty} ({sigma:.1f}σ)",
                        suggested_fix=f"Adjust {const_name} or explain discrepancy with new physics"
                    ))

        return violations


class TheoryRefutationEngine:
    """
    Main theory refutation engine.

    Tests theories against all known constraints simultaneously to rapidly
    identify unviable theories and suggest refinements.
    """

    def __init__(self):
        self.math_checker = MathematicalConsistencyChecker()
        self.physics_checker = PhysicalConstraintsChecker()
        self.quantum_checker = QuantumConstraintsChecker()
        self.relativistic_checker = RelativisticConstraintsChecker()
        self.observation_checker = ObservationalConstraintsChecker()

        self.test_history = []

    def identify_conflicts(
        self,
        theory: Dict[str, Any],
        theory_name: str = "Unknown Theory"
    ) -> TheoryTestResult:
        """
        Main method: identify all conflicts in a theory.

        Args:
            theory: Theory specification as dictionary
            theory_name: Name of the theory

        Returns:
            Comprehensive test results
        """
        print(f"\n[THEORY REFUTATION ENGINE] Testing: {theory_name}")

        all_violations = []

        # 1. Mathematical consistency
        print("  Checking mathematical consistency...")
        if 'equations' in theory:
            for eq in theory['equations']:
                all_violations.extend(self.math_checker.check_well_posedness(eq, theory.get('variables', [])))
                all_violations.extend(self.math_checker.check_dimensional_consistency(eq))

        if 'analysis' in theory:
            all_violations.extend(self.math_checker.check_stability(theory['analysis']))

        # 2. Physical constraints
        print("  Checking physical constraints...")
        all_violations.extend(self.physics_checker.check_conservation_laws(theory))
        all_violations.extend(self.physics_checker.check_thermodynamics(theory))
        all_violations.extend(self.physics_checker.check_speed_limit(theory))
        all_violations.extend(self.physics_checker.check_positivity_definiteness(theory))

        # 3. Quantum constraints
        if 'observables' in theory:
            all_violations.extend(self.quantum_checker.check_uncertainty_principle(theory['observables']))
        all_violations.extend(self.quantum_checker.check_unitarity(theory))

        # 4. Relativistic constraints
        if 'spacetime' in theory:
            all_violations.extend(self.relativistic_checker.check_causality(theory['spacetime']))
        if 'stress_energy' in theory:
            all_violations.extend(self.relativistic_checker.check_energy_conditions(theory['stress_energy']))

        # 5. Observational constraints
        if 'constants' in theory:
            all_violations.extend(self.observation_checker.check_constant_consistency(theory['constants']))

        # Categorize violations
        fatal_violations = [v for v in all_violations if v.severity == Severity.FATAL]
        severe_violations = [v for v in all_violations if v.severity == Severity.SEVERE]
        warnings = [v for v in all_violations if v.severity in [Severity.MODERATE, Severity.MILD, Severity.INFO]]

        # Calculate viability score
        n_constraints = 20  # Approximate number of constraints checked
        n_fatal = len(fatal_violations)
        n_severe = len(severe_violations)
        viability_score = max(0, 1.0 - (n_fatal * 1.0 + n_severe * 0.5) / n_constraints)

        is_viable = n_fatal == 0

        # Generate suggestions
        suggestions = self._generate_suggestions(all_violations, theory)

        result = TheoryTestResult(
            theory_name=theory_name,
            total_constraints_tested=n_constraints,
            violations=all_violations,
            is_viable=is_viable,
            viability_score=viability_score,
            fatal_violations=fatal_violations,
            warnings=warnings,
            suggestions=suggestions
        )

        # Print summary
        self._print_test_summary(result)

        self.test_history.append(result)

        return result

    def _generate_suggestions(
        self,
        violations: List[ConstraintViolation],
        theory: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions for fixing violations"""
        suggestions = []

        # Extract unique suggestions from violations
        for violation in violations:
            if violation.suggested_fix:
                suggestions.append(f"- Fix {violation.constraint_name}: {violation.suggested_fix}")

        # Add general suggestions based on violation types
        if violations:
            fatal_count = sum(1 for v in violations if v.severity == Severity.FATAL)
            if fatal_count > 0:
                suggestions.append(f"\nCRITICAL: {fatal_count} fatal violations found. Theory needs major revision.")

            # Check for common patterns
            conservation_violations = [v for v in violations
                                       if 'conservation' in v.constraint_name]
            if conservation_violations:
                suggestions.append("\nConsider whether conservation laws might be:\n"
                                  "- Avoided in this regime (e.g., open system)\n"
                                  "- Apparent due to simplification\n"
                                  "- Genuinely violated by new physics (provide evidence)")

        return suggestions

    def _print_test_summary(self, result: TheoryTestResult):
        """Print summary of test results"""
        print(f"\n  Test Summary for '{result.theory_name}':")
        print(f"  Viability: {result.is_viable}")
        print(f"  Score: {result.viability_score:.2f}/1.00")
        print(f"  Violations: {len(result.violations)}")

        if result.fatal_violations:
            print(f"\n  FATAL ({len(result.fatal_violations)}):")
            for v in result.fatal_violations[:3]:  # Show first 3
                print(f"    - {v.constraint_name}: {v.description}")
            if len(result.fatal_violations) > 3:
                print(f"    ... and {len(result.fatal_violations) - 3} more")

        if result.warnings:
            print(f"\n  WARNINGS ({len(result.warnings)}):")
            for v in result.warnings[:3]:
                print(f"    - {v.constraint_name}: {v.description}")

        if result.suggestions:
            print(f"\n  SUGGESTIONS:")
            for s in result.suggestions[:5]:
                print(f"    {s}")

    def batch_test_theories(
        self,
        theories: List[Dict[str, Any]]
    ) -> List[TheoryTestResult]:
        """
        Test multiple theories in batch.

        Args:
            theories: List of (theory_name, theory_dict) tuples

        Returns:
            List of test results
        """
        results = []

        for i, theory in enumerate(theories):
            if isinstance(theory, tuple):
                theory_name, theory_dict = theory
            else:
                theory_name = f"Theory_{i}"
                theory_dict = theory

            result = self.identify_conflicts(theory_dict, theory_name)
            results.append(result)

        # Rank by viability score
        results.sort(key=lambda r: r.viability_score, reverse=True)

        return results

    def compare_theories(
        self,
        theory_results: List[TheoryTestResult]
    ) -> Dict[str, Any]:
        """
        Compare multiple theories based on test results.

        Args:
            theory_results: Results from testing multiple theories

        Returns:
            Comparison summary
        """
        if not theory_results:
            return {'error': 'No theories to compare'}

        comparison = {
            'num_theories': len(theory_results),
            'viable_theories': [r.theory_name for r in theory_results if r.is_viable],
            'ranking': [(r.theory_name, r.viability_score) for r in theory_results],
            'best_theory': theory_results[0].theory_name,
            'most_violated_constraints': self._find_most_common_violations(theory_results)
        }

        return comparison

    def _find_most_common_violations(
        self,
        results: List[TheoryTestResult]
    ) -> List[Tuple[str, int]]:
        """Find which constraints are most commonly violated"""
        from collections import Counter

        all_violations = []
        for result in results:
            all_violations.extend([v.constraint_name for v in result.violations])

        counter = Counter(all_violations)
        return counter.most_common(5)

    def stress_test_theory(
        self,
        theory: Dict[str, Any],
        parameter_ranges: Dict[str, Tuple[float, float]]
    ) -> Dict[str, Any]:
        """
        Stress test a theory across parameter space.

        Args:
            theory: Theory to test
            parameter_ranges: Parameters to vary with (min, max) ranges

        Returns:
            Stress test results showing where theory breaks down
        """
        print(f"\n[STRESS TESTING] Across {len(parameter_ranges)} parameters")

        # Generate parameter grid (simplified - would use proper sampling)
        n_samples = 10
        stress_results = []

        for param, (min_val, max_val) in parameter_ranges.items():
            print(f"  Varying {param} from {min_val} to {max_val}")

            # Test at extremes and midpoints
            test_values = [min_val, (min_val + max_val) / 2, max_val]

            for value in test_values:
                test_theory = theory.copy()
                test_theory[param] = value

                result = self.identify_conflicts(
                    test_theory,
                    f"{theory.get('name', 'Theory')}_{param}={value:.2e}"
                )

                stress_results.append({
                    'parameter': param,
                    'value': value,
                    'viable': result.is_viable,
                    'score': result.viability_score
                })

        # Find regions where theory fails
        failures = [(r['parameter'], r['value'])
                    for r in stress_results if not r['viable']]

        return {
            'parameter_ranges': parameter_ranges,
            'test_results': stress_results,
            'failure_regions': failures,
            'robustness': len(failures) / len(stress_results) if stress_results else 0
        }


# Factory function
def create_theory_refutation_engine() -> TheoryRefutationEngine:
    """Factory function to create theory refutation engine"""
    return TheoryRefutationEngine()
