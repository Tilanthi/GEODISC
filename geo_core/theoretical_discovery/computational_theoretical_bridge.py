"""
Computational-Theoretical Bridge

Connects numerical experiments with theoretical understanding, using
simulations to guide theory and theory to improve simulations.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class SimulationType(Enum):
    """Types of numerical simulations"""
    SPH = "SPH"  # Smoothed Particle Hydrodynamics
    GRID = "grid"  # Grid-based (finite difference/volume/element)
    PARTICLE_IN_CELL = "PIC"  # Particle-in-cell
    MONTE_CARLO = "monte_carlo"
    N_BODY = "n_body"
    RADIATIVE_TRANSFER = "radiative_transfer"


class InsightCategory(Enum):
    """Categories of insights from simulations"""
    SCALING_LAW = "scaling_law"
    INVARIANT = "invariant"
    APPROXIMATION = "approximation"
    INSTABILITY = "instability"
    PHASE_TRANSITION = "phase_transition"
    CRITICAL_POINT = "critical_point"


@dataclass
class SimulationDesign:
    """Design for a numerical simulation"""
    name: str
    physics_included: List[str]
    physics_excluded: List[str]
    parameters: Dict[str, Tuple[float, float]]  # (min, max)
    resolution_requirements: Dict[str, Any]
    boundary_conditions: Dict[str, str]
    initial_conditions: Dict[str, Any]
    output_observables: List[str]
    theoretical_questions: List[str]


@dataclass
class SimulationResult:
    """Results from running a simulation"""
    simulation_name: str
    parameters_used: Dict[str, float]
    data: Dict[str, np.ndarray]
    derived_quantities: Dict[str, float]
    insights: List[Dict[str, Any]]
    theoretical_implications: List[str]


@dataclass
class TheoreticalGuidance:
    """Guidance from theory for simulation design"""
    recommended_regime: str
    required_resolution: Dict[str, float]
    critical_parameters: List[str]
    expected_behaviors: List[str]
    warning_conditions: List[str]


@dataclass
class SimulationInsight:
    """Insight extracted from simulation results"""
    category: InsightCategory
    description: str
    mathematical_form: Optional[str]
    confidence: float
    conditions: List[str]
    theoretical_prediction: Optional[str] = None


class SimulationDesigner:
    """Design simulations to answer theoretical questions"""

    @staticmethod
    def design_for_theory_testing(
        theory_question: str,
        theory_framework: Dict[str, Any]
    ) -> SimulationDesign:
        """
        Design a simulation specifically to test a theoretical prediction.

        Args:
            theory_question: Question to investigate
            theory_framework: Theoretical framework being tested

        Returns:
            Simulation design
        """
        print(f"\n[SIMULATION DESIGN] For theory question: {theory_question}")

        # Extract relevant physics from theory
        physics = theory_framework.get('physics', ['fluid_dynamics'])
        observables = theory_framework.get('observables', [])

        # Determine what physics to include
        physics_included = []
        physics_excluded = []

        # Standard decision logic (simplified)
        for phys in ['self_gravity', 'radiation', 'magnetic_fields',
                    'viscosity', 'turbulence', 'relativity']:
            if phys in theory_framework.get('required_physics', []):
                physics_included.append(phys)
            else:
                physics_excluded.append(phys)

        # Determine parameter ranges
        parameters = {}
        for param, specs in theory_framework.get('parameters', {}).items():
            if isinstance(specs, tuple) and len(specs) == 2:
                parameters[param] = specs
            else:
                # Default range
                parameters[param] = (0.1, 10.0)

        design = SimulationDesign(
            name=f"test_{theory_question.replace(' ', '_')}",
            physics_included=physics_included,
            physics_excluded=physics_excluded,
            parameters=parameters,
            resolution_requirements=theory_framework.get('resolution', {}),
            boundary_conditions=theory_framework.get('boundary_conditions', {}),
            initial_conditions=theory_framework.get('initial_conditions', {}),
            output_observables=observables,
            theoretical_questions=[theory_question]
        )

        print(f"  Physics included: {physics_included}")
        print(f"  Physics excluded: {physics_excluded}")
        print(f"  Parameters: {list(parameters.keys())}")

        return design

    @staticmethod
    def isolate_physical_effects(
        base_simulation: SimulationDesign,
        effect_to_isolate: str
    ) -> SimulationDesign:
        """
        Create simulation variants to isolate specific physical effects.

        Args:
            base_simulation: Base simulation design
            effect_to_isolate: Which effect to isolate

        Returns:
            Modified simulation design
        """
        # Create variant with effect enabled
        variant_with = SimulationDesign(
            name=f"{base_simulation.name}_with_{effect_to_isolate}",
            physics_included=base_simulation.physics_included + [effect_to_isolate],
            physics_excluded=[e for e in base_simulation.physics_excluded
                             if e != effect_to_isolate],
            parameters=base_simulation.parameters,
            resolution_requirements=base_simulation.resolution_requirements,
            boundary_conditions=base_simulation.boundary_conditions,
            initial_conditions=base_simulation.initial_conditions,
            output_observables=base_simulation.output_observables,
            theoretical_questions=base_simulation.theoretical_questions
        )

        # Create variant with effect disabled
        variant_without = SimulationDesign(
            name=f"{base_simulation.name}_without_{effect_to_isolate}",
            physics_included=[p for p in base_simulation.physics_included
                               if p != effect_to_isolate],
            physics_excluded=base_simulation.physics_excluded + [effect_to_isolate],
            parameters=base_simulation.parameters,
            resolution_requirements=base_simulation.resolution_requirements,
            boundary_conditions=base_simulation.boundary_conditions,
            initial_conditions=base_simulation.initial_conditions,
            output_observables=base_simulation.output_observables,
            theoretical_questions=base_simulation.theoretical_questions
        )

        return variant_with, variant_without


class InsightExtractor:
    """Extract theoretical insights from simulation data"""

    @staticmethod
    def find_scaling_laws(
        data: Dict[str, np.ndarray],
        variables: List[str]
    ) -> List[SimulationInsight]:
        """
        Find scaling laws in simulation data.

        Args:
            data: Simulation output data
            variables: Variables to correlate

        Returns:
            List of scaling law insights
        """
        insights = []

        # Perform power-law fits between variable pairs
        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                if var1 in data and var2 in data:
                    x = data[var1]
                    y = data[var2]

                    if len(x) == len(y) and len(x) > 3:
                        # Log-transform for power law
                        log_x = np.log10(x[x > 0])
                        log_y = np.log10(y[y > 0])

                        if len(log_x) > 0 and len(log_y) > 0:
                            # Fit power law: y ∝ x^α
                            from scipy import stats
                            slope, intercept, r, p, std_err = stats.linregress(log_x, log_y)

                            if r > 0.8:  # Strong correlation
                                insights.append(SimulationInsight(
                                    category=InsightCategory.SCALING_LAW,
                                    description=f"{var2} ∝ {var1}^{slope:.2f}",
                                    mathematical_form=f"log({var2}) = {slope:.2f}*log({var1}) + {intercept:.2f}",
                                    confidence=abs(r),
                                    conditions=[f"r = {r:.3f}, p < {p:.3e}"]
                                ))

        return insights

    @staticmethod
    def find_invariants(
        data: Dict[str, np.ndarray],
        time_index: Optional[int] = None
    ) -> List[SimulationInsight]:
        """
        Find conserved or approximately conserved quantities.

        Args:
            data: Time-series simulation data
            time_index: Index of time dimension

        Returns:
            List of invariant insights
        """
        insights = []

        # Look for quantities that don't change much over time
        for var_name, values in data.items():
            if len(values) > 1:
                # Calculate relative variation
                mean_val = np.mean(values)
                std_val = np.std(values)
                rel_variation = std_val / abs(mean_val) if mean_val != 0 else float('inf')

                if rel_variation < 0.01:  # Less than 1% variation
                    insights.append(SimulationInsight(
                        category=InsightCategory.INVARIANT,
                        description=f"{var_name} is approximately conserved",
                        mathematical_form=f"d{var_name}/dt ≈ 0",
                        confidence=1.0 - rel_variation * 10,
                        conditions=[f"Relative variation: {rel_variation:.4f}"]
                    ))

        return insights

    @staticmethod
    def find_instabilities(
        data: Dict[str, np.ndarray],
        parameters: Dict[str, float]
    ) -> List[SimulationInsight]:
        """
        Find instabilities or critical points in simulation.

        Args:
            data: Simulation data potentially across parameter space
            parameters: Simulation parameters

        Returns:
            List of instability insights
        """
        insights = []

        # Look for rapid changes or divergences
        for var_name, values in data.items():
            if len(values) > 2:
                # Calculate derivatives (finite difference)
                derivatives = np.diff(values)

                # Look for large derivatives
                for i, deriv in enumerate(derivatives):
                    if abs(deriv) > 5 * np.std(derivatives):
                        insights.append(SimulationInsight(
                            category=InsightCategory.INSTABILITY,
                            description=f"Rapid change in {var_name} at index {i}",
                            mathematical_form=f"d{var_name}/dt = {deriv:.3e}",
                            confidence=0.7,
                            conditions=[f"Derivative exceeds 5σ"]
                        ))

        return insights

    @staticmethod
    def identify_approximation_regime(
        data: Dict[str, np.ndarray],
        theory_predictions: Dict[str, float]
    ) -> List[SimulationInsight]:
        """
        Identify where theoretical approximations are valid.

        Args:
            data: Simulation data
            theory_predictions: Theoretical predictions

        Returns:
            List of approximation validity insights
        """
        insights = []

        # Compare simulation to theory
        for var_name, sim_values in data.items():
            if var_name in theory_predictions:
                pred_value = theory_predictions[var_name]

                # Calculate relative error
                relative_errors = np.abs((sim_values - pred_value) / pred_value)

                # Find where approximation is good (< 10% error)
                good_regime = np.where(relative_errors < 0.1)[0]
                bad_regime = np.where(relative_errors > 0.5)[0]

                if len(good_regime) > 0 and len(bad_regime) > 0:
                    insights.append(SimulationInsight(
                        category=InsightCategory.APPROXIMATION,
                        description=f"{var_name} approximation valid in specific regime",
                        confidence=0.8,
                        conditions=[
                            f"Valid for {len(good_regime)}/{len(sim_values)} data points",
                            f"Breaks down in regime: {len(bad_regime)} points"
                        ]
                    ))

        return insights


class TheoryFromSimulation:
    """Derive theoretical insights from simulation results"""

    @staticmethod
    def suggest_analytic_approximation(
        simulation_results: Dict[str, np.ndarray],
        insight: SimulationInsight
    ) -> str:
        """
        Suggest analytic approximation based on simulation insight.

        Args:
            simulation_results: Simulation data
            insight: Discovered insight

        Returns:
            Suggested analytic approximation
        """
        if insight.category == InsightCategory.SCALING_LAW:
            return (
                f"Based on simulation: {insight.description}\n"
                f"Suggested analytic form: {insight.mathematical_form}\n"
                f"This power law should be derivable from dimensional analysis\n"
                f"and physical arguments."
            )

        elif insight.category == InsightCategory.INVARIANT:
            return (
                f"Simulation discovered: {insight.description}\n"
                f"Mathematical form: {insight.mathematical_form}\n"
                f"This suggests a conservation law or symmetry that should\n"
                f"be derivable from first principles."
            )

        else:
            return (
                f"Simulation insight: {insight.description}\n"
                f"This should be investigated theoretically to understand\n"
                f"the underlying physical mechanism."
            )

    @staticmethod
    def suggest_equation_form(
        scaling_relation: Dict[str, float]
    ) -> str:
        """
        Suggest complete equation form from scaling relation.

        Args:
            scaling_relation: Dictionary of variable -> exponent

        Returns:
            Suggested equation
        """
        # Build equation string
        lhs = list(scaling_relation.keys())[0]
        rhs_parts = []

        for var, exp in scaling_relation.items():
            if exp == 1:
                rhs_parts.append(var)
            elif exp != 0:
                rhs_parts.append(f"{var}^{exp:.2f}")

        rhs = " * ".join(rhs_parts)

        # Add dimensionless prefactor
        equation = f"{lhs} = C * {rhs}"
        note = "\nwhere C is a dimensionless constant determined by boundary conditions."

        return equation + note


class ComputationalTheoreticalBridge:
    """
    Main computational-theoretical bridge.

    Connects numerical experiments with theoretical understanding,
    enabling bidirectional flow of insights between computation and theory.
    """

    def __init__(self):
        self.simulation_designer = SimulationDesigner()
        self.insight_extractor = InsightExtractor()
        self.theory_from_sim = TheoryFromSimulation()

        self.simulation_history = []
        self.insight_database = []

    def design_elucidating_simulations(
        self,
        theory_question: str,
        theory_framework: Dict[str, Any]
    ) -> List[SimulationDesign]:
        """
        Design simulations specifically to illuminate theoretical questions.

        Args:
            theory_question: Theoretical question to investigate
            theory_framework: Relevant theoretical framework

        Returns:
            List of simulation designs
        """
        print(f"\n[COMPUTATIONAL-THEORETICAL BRIDGE]")
        print(f"Question: {theory_question}")

        designs = []

        # Primary simulation
        primary_design = self.simulation_designer.design_for_theory_testing(
            theory_question, theory_framework
        )
        designs.append(primary_design)

        # Isolation simulations
        for physics in theory_framework.get('physics', []):
            variant_with, variant_without = \
                self.simulation_designer.isolate_physical_effects(
                    primary_design, physics
                )
            designs.append(variant_with)
            designs.append(variant_without)

        # Parameter sweep design
        if 'parameters_to_sweep' in theory_framework:
            sweep_design = self._create_sweep_design(
                theory_question, theory_framework
            )
            designs.append(sweep_design)

        print(f"  Generated {len(designs)} simulation designs")

        return designs

    def _create_sweep_design(
        self,
        question: str,
        framework: Dict[str, Any]
    ) -> SimulationDesign:
        """Create parameter sweep simulation design"""
        sweep_params = framework.get('parameters_to_sweep', {})

        return SimulationDesign(
            name=f"sweep_{question.replace(' ', '_')}",
            physics_included=framework.get('physics', []),
            physics_excluded=[],
            parameters=sweep_params,
            resolution_requirements=framework.get('resolution', {}),
            boundary_conditions=framework.get('boundary_conditions', {}),
            initial_conditions=framework.get('initial_conditions', {}),
            output_observables=framework.get('observables', []),
            theoretical_questions=[f"How do results vary with {list(sweep_params.keys())}?"]
        )

    def extract_theoretical_insights(
        self,
        simulation_data: Dict[str, np.ndarray],
        variables_of_interest: List[str]
    ) -> List[SimulationInsight]:
        """
        Extract theoretical insights from simulation data.

        Args:
            simulation_data: Data from simulation
            variables_of_interest: Variables to analyze

        Returns:
            List of theoretical insights
        """
        print(f"\n[INSIGHT EXTRACTION] From {len(simulation_data)} data arrays")

        insights = []

        # Find scaling laws
        scaling_insights = self.insight_extractor.find_scaling_laws(
            simulation_data, variables_of_interest
        )
        insights.extend(scaling_insights)
        print(f"  Found {len(scaling_insights)} scaling laws")

        # Find invariants
        invariant_insights = self.insight_extractor.find_invariants(simulation_data)
        insights.extend(invariant_insights)
        print(f"  Found {len(invariant_insights)} invariants")

        # Find instabilities
        instability_insights = self.insight_extractor.find_instabilities(
            simulation_data, {}
        )
        insights.extend(instability_insights)
        print(f"  Found {len(instability_insights)} instabilities")

        # Store insights
        self.insight_database.extend(insights)

        return insights

    def refine_theory_from_insights(
        self,
        insights: List[SimulationInsight],
        original_theory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Refine theoretical framework based on simulation insights.

        Args:
            insights: Insights from simulation
            original_theory: Original theoretical framework

        Returns:
            Refined theoretical framework
        """
        print(f"\n[THEORY REFINEMENT] Based on {len(insights)} insights")

        refined_theory = original_theory.copy()

        # Add insights to theory
        refined_theory['simulation_insights'] = [
            {
                'category': insight.category.value,
                'description': insight.description,
                'mathematical_form': insight.mathematical_form,
                'confidence': insight.confidence
            }
            for insight in insights
        ]

        # Add suggested modifications
        modifications = []

        for insight in insights:
            suggestion = self.theory_from_sim.suggest_analytic_approximation(
                {}, insight
            )
            modifications.append(suggestion)

        refined_theory['suggested_modifications'] = modifications

        print(f"  Generated {len(modifications)} theory refinements")

        return refined_theory

    def guide_theory_development(
        self,
        findings: Dict[str, Any],
        original_theory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use simulation findings to guide theoretical development.

        Args:
            findings: Results and findings from simulations
            original_theory: Original theoretical framework

        Returns:
            Guidance for theoretical development
        """
        print(f"\n[THEORY GUIDANCE]")

        guidance = {
            'which_terms_important': [],
            'what_approximations_valid': [],
            'where_to_focus_effort': [],
            'suggested_analytic_approaches': []
        }

        # Analyze findings to extract guidance
        if 'scaling_relations' in findings:
            for scaling in findings['scaling_relations']:
                guidance['which_terms_important'].append(
                    f"Power law: {scaling['description']}"
                )

        if 'approximation_validity' in findings:
            guidance['what_approximations_valid'] = \
                findings['approximation_validity']

        # Generate suggested approaches
        guidance['suggested_analytic_approaches'] = [
            "1. Dimensional analysis on relevant variables",
            "2. Perturbation theory around known solutions",
            "3. Variational methods for approximate solutions",
            "4. Symmetry analysis to simplify equations",
            "5. Matched asymptotic expansions"
        ]

        print(f"  Generated {len(guidance['suggested_analytic_approaches'])} suggestions")

        return guidance

    def run_computational_theoretical_cycle(
        self,
        theory_question: str,
        theory_framework: Dict[str, Any],
        simulation_function: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run full cycle: design → simulate → extract insights → refine theory.

        Args:
            theory_question: Question to investigate
            theory_framework: Starting theoretical framework
            simulation_function: Optional function to run simulations

        Returns:
            Complete cycle results
        """
        print(f"\n" + "="*70)
        print(f"COMPUTATIONAL-THEORETICAL CYCLE")
        print(f"Question: {theory_question}")
        print("="*70)

        # Step 1: Design simulations
        designs = self.design_elucidating_simulations(
            theory_question, theory_framework
        )

        # Step 2: Run simulations (if function provided, otherwise mock)
        simulation_results = []
        for design in designs:
            if simulation_function:
                result = simulation_function(design)
                simulation_results.append(result)
            else:
                # Mock result for demonstration
                mock_result = self._mock_simulation_result(design)
                simulation_results.append(mock_result)

        # Step 3: Extract insights
        all_insights = []
        for result in simulation_results:
            insights = self.extract_theoretical_insights(
                result['data'],
                result.get('variables', [])
            )
            all_insights.extend(insights)

        # Step 4: Refine theory
        refined_theory = self.refine_theory_from_insights(
            all_insights, theory_framework
        )

        # Step 5: Generate guidance
        guidance = self.guide_theory_development(
            {'insights': all_insights},
            theory_framework
        )

        # Compile results
        cycle_results = {
            'theory_question': theory_question,
            'original_theory': theory_framework,
            'simulation_designs': designs,
            'simulation_results': simulation_results,
            'extracted_insights': all_insights,
            'refined_theory': refined_theory,
            'guidance': guidance,
            'next_steps': [
                "1. Validate refined theory against new simulations",
                "2. Compare predictions with observations",
                "3. Publish theoretical framework with computational validation"
            ]
        }

        return cycle_results

    def _mock_simulation_result(self, design: SimulationDesign) -> Dict[str, Any]:
        """Create mock simulation result for demonstration"""
        import numpy as np

        # Create mock data
        n_points = 100
        mock_data = {}

        for var in design.output_observables:
            mock_data[var] = np.random.randn(n_points)

        # Add time dimension
        mock_data['time'] = np.linspace(0, 1, n_points)

        # Add mock derived quantities
        mock_data['energy'] = np.cumsum(np.random.randn(n_points))

        return {
            'simulation_name': design.name,
            'parameters_used': {k: np.mean(v) for k, v in design.parameters.items()},
            'data': mock_data,
            'derived_quantities': {
                'total_energy': np.sum(mock_data.get('energy', [0])),
                'final_time': mock_data['time'][-1]
            },
            'insights': ['Mock insight 1', 'Mock insight 2'],
            'theoretical_implications': ['Mock implication']
        }


# Factory function
def create_computational_theoretical_bridge() -> ComputationalTheoreticalBridge:
    """Factory function to create computational-theoretical bridge"""
    return ComputationalTheoreticalBridge()
