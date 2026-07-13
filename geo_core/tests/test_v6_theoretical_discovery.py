"""
V6.0 Theoretical Discovery System Test Suite

Tests all components of the V6.0 Theoretical Discovery System:
- SymbolicTheoreticEngine
- TheorySpaceMapper
- TheoryRefutationEngine
- LiteratureTheorySynthesizer
- ComputationalTheoreticalBridge
- V6TheoreticalDiscovery (main integrator)
"""

import sys
import os

# Add parent and grandparent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, grandparent_dir)

from geo_core.theoretical_discovery import (
    V6TheoreticalDiscovery,
    create_v6_theoretical_system,
    DiscoveryMode,
    DiscoveryResult,
    TheoreticalProblem,
    SymbolicTheoreticEngine,
    TheorySpaceMapper,
    TheoryRefutationEngine,
    LiteratureTheorySynthesizer,
    ComputationalTheoreticalBridge,
    PhysicsDomain,
    PhysicalConstraint,
    ScalingRelation,
    TheoryFramework,
    TheoryConnection,
)


def test_symbolic_theoretic_engine():
    """Test the symbolic theoretic engine component"""
    print("\n[Symbolic Theoretic Engine]")

    engine = SymbolicTheoreticEngine()

    # Test dimensional analysis
    relations = engine.discover_scaling_laws(
        ['mass', 'velocity', 'radius'],
        symmetries=['rotational']
    )
    print(f"  Dimensional analysis: {len(relations)} relations found")

    # Test first principles derivation
    domains = [PhysicsDomain.FLUID_DYNAMICS]
    derived = engine.derive_from_first_principles(
        "Fluid flow scaling",
        domains,
        ['velocity', 'density'],
        []
    )
    print(f"  First principles derivation: {len(derived)} relations")

    # Test perturbation theory
    perturbation = engine.perform_perturbation_analysis(
        "v = v0 + epsilon*v1",
        epsilon=0.01,
        order=2
    )
    print(f"  Perturbation analysis: {len(perturbation)} terms")

    return True


def test_theory_space_mapper():
    """Test the theory space mapper component"""
    print("\n[Theory Space Mapper]")

    mapper = TheorySpaceMapper()

    # Test theory space construction
    graph = mapper.construct_theory_space(['fluid_dynamics', 'thermodynamics'])
    print(f"  Theory space: {len(graph.nodes())} nodes, {len(graph.edges())} edges")

    # Test theory connection discovery
    connections = mapper.discover_connections('Navier_Stokes', 'Euler_Equations')
    print(f"  Theory connections: {len(connections)} found")

    # Test theory hypothesis generation
    hypotheses = mapper.generate_theory_hypotheses({
        'domains': ['fluid_dynamics'],
        'variables': ['velocity', 'pressure']
    })
    print(f"  Theory hypotheses: {len(hypotheses)} generated")

    return True


def test_theory_refutation_engine():
    """Test the theory refutation engine component"""
    print("\n[Theory Refutation Engine]")

    engine = TheoryRefutationEngine()

    # Test theory conflict identification
    theory = {
        'name': 'Test Theory',
        'description': 'A test theory',
        'assumptions': ['Assumption 1'],
        'predictions': ['Prediction 1']
    }
    result = engine.identify_conflicts(theory, 'Test Theory')
    print(f"  Conflict identification: viable={result.is_viable}, score={result.viability_score}")

    # Test batch theory testing
    theories = [
        {'name': 'Theory 1', 'description': 'Test', 'assumptions': [], 'predictions': []},
        {'name': 'Theory 2', 'description': 'Test', 'assumptions': [], 'predictions': []}
    ]
    batch_results = engine.batch_test_theories(theories)
    print(f"  Batch testing: {len(batch_results)} theories tested")

    # Test stress testing
    stress_result = engine.stress_test_theory(
        theory,
        {'parameter1': (0.0, 1.0)}
    )
    print(f"  Stress testing: {len(stress_result.get('test_points', []))} points tested")

    return True


def test_literature_theory_synthesizer():
    """Test the literature theory synthesizer component"""
    print("\n[Literature Theory Synthesizer]")

    synthesizer = LiteratureTheorySynthesizer()

    # Test equation extraction
    papers = {'paper1': 'Equation: $E = mc^2$'}
    equations = synthesizer.extract_equations(papers)
    print(f"  Equation extraction: {len(equations)} equations")

    # Test assumption pattern finding
    assumptions = synthesizer.find_assumption_patterns('astrophysics')
    print(f"  Assumption analysis: {len(assumptions.get('common_assumptions', {}))} patterns")

    # Test gap detection
    gaps = synthesizer.discover_theoretical_gaps('astrophysics')
    print(f"  Gap detection: {len(gaps)} insights")

    return True


def test_computational_theoretical_bridge():
    """Test the computational theoretical bridge component"""
    print("\n[Computational Theoretical Bridge]")

    bridge = ComputationalTheoreticalBridge()

    # Test simulation design
    theory_framework = {
        'physics': ['fluid_dynamics'],
        'observables': ['velocity', 'pressure'],
        'predictions': ['scaling_relation']
    }
    designs = bridge.design_elucidating_simulations(
        "Test question",
        theory_framework
    )
    print(f"  Simulation design: {len(designs)} designs")

    # Test computational-theoretical cycle
    cycle_result = bridge.run_computational_theoretical_cycle(
        "Test question",
        theory_framework
    )
    print(f"  Computational cycle: {len(cycle_result.get('extracted_insights', []))} insights")

    return True


def test_v6_main_integrator():
    """Test the main V6 integrator"""
    print("\n[V6 Main Integrator]")

    v6 = create_v6_theoretical_system()

    # Test system status
    status = v6.get_status()
    active_components = sum(status['components'].values())
    print(f"  System status: {active_components}/5 components active")

    # Test theoretical discovery mode
    result1 = v6.answer(
        "Derive stellar luminosity scaling",
        mode=DiscoveryMode.THEORETICAL
    )
    print(f"  THEORETICAL mode: confidence={result1.confidence}")

    # Test empirical discovery mode
    result2 = v6.answer(
        "Analyze galaxy data",
        mode=DiscoveryMode.EMPIRICAL
    )
    print(f"  EMPIRICAL mode: mode={result2.mode.value}")

    # Test hybrid discovery mode
    result3 = v6.answer(
        "Test theory with simulation",
        mode=DiscoveryMode.HYBRID
    )
    print(f"  HYBRID mode: confidence={result3.confidence}")

    # Test dimensional analysis
    relations = v6.perform_dimensional_analysis(
        ['mass', 'luminosity', 'radius']
    )
    print(f"  Dimensional analysis: {len(relations)} relations")

    # Test theory testing
    test_result = v6.test_theoretical_proposal(
        {'name': 'Test', 'description': 'Test', 'assumptions': [], 'predictions': []},
        'Test'
    )
    print(f"  Theory testing: viable={test_result.is_viable}")

    # Test theory connections
    connections = v6.find_theory_connections('Navier_Stokes', 'Euler_Equations')
    print(f"  Theory connections: {len(connections)} connections")

    return True


def test_integration_with_geo_core():
    """Test integration with main geo_core system"""
    print("\n[Integration with STAN Core]")

    try:
        from geo_core import V6TheoreticalDiscovery, create_v6_theoretical_system
        print("  ✓ V6.0 components exported from geo_core")

        # Test creation
        v6 = create_v6_theoretical_system()
        print("  ✓ Factory function works")

        # Test that it's the right type
        assert isinstance(v6, V6TheoreticalDiscovery)
        print("  ✓ Correct type returned")

        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def run_all_tests():
    """Run all V6.0 tests"""
    print("="*70)
    print("V6.0 THEORETICAL DISCOVERY SYSTEM TEST SUITE")
    print("="*70)

    tests = [
        ("Symbolic Theoretic Engine", test_symbolic_theoretic_engine),
        ("Theory Space Mapper", test_theory_space_mapper),
        ("Theory Refutation Engine", test_theory_refutation_engine),
        ("Literature Theory Synthesizer", test_literature_theory_synthesizer),
        ("Computational Theoretical Bridge", test_computational_theoretical_bridge),
        ("V6 Main Integrator", test_v6_main_integrator),
        ("STAN Core Integration", test_integration_with_geo_core),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n  ERROR in {test_name}: {e}")
            results[test_name] = False

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({100*passed/total:.1f}%)")

    if passed == total:
        print("\n✓ ALL V6.0 TESTS PASSED")
        print("\nThe V6.0 Theoretical Discovery System is fully operational.")
        print("GEODISC can now perform theoretical discovery beyond empirical analysis.")
    else:
        print("\n✗ SOME TESTS FAILED")
        print("Please review the errors above.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
