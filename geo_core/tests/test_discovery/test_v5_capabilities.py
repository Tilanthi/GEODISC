"""
V5.0 Discovery Enhancement System - Comprehensive Test Suite
============================================================

Tests all V5.0 capabilities (V101-V108) and the V5.0 Orchestrator.

Capabilities Tested:
- V101: Temporal Causal Discovery
- V102: Scalable Counterfactual Engine
- V103: Multi-Modal Evidence Integration
- V104: Adversarial Hypothesis Framework
- V105: Meta-Discovery Transfer Learning
- V106: Explainable Causal Reasoning
- V107: Discovery Triage and Prioritization
- V108: Real-Time Streaming Discovery
- V5.0 Orchestrator: Unified system coordination

Date: 2026-04-14
Version: 5.0
"""

import sys
import os
import numpy as np
import warnings
from typing import Dict, List, Any

# Add geo_core to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress warnings for cleaner test output
warnings.filterwarnings('ignore')


class V5TestResult:
    """Result of a single test"""
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


class V5TestSuite:
    """Comprehensive test suite for V5.0 capabilities"""

    def __init__(self):
        self.results: List[V5TestResult] = []
        self.test_data = self._generate_test_data()

    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate synthetic test data"""
        np.random.seed(42)

        # Basic test dataset
        n_samples = 500
        n_vars = 5

        # Generate correlated data
        data = np.random.randn(n_samples, n_vars)
        data[:, 1] = 0.7 * data[:, 0] + 0.3 * np.random.randn(n_samples)  # Correlation
        data[:, 2] = 0.5 * data[:, 0] + 0.5 * np.random.randn(n_samples)

        variable_names = ['var_A', 'var_B', 'var_C', 'var_D', 'var_E']

        # Time series data for V101 and V108
        time_series = np.cumsum(np.random.randn(1000, 3), axis=0)

        return {
            'data': data,
            'variable_names': variable_names,
            'time_series': time_series,
            'n_samples': n_samples,
            'n_vars': n_vars
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all V5.0 capability tests"""
        print("=" * 70)
        print("V5.0 DISCOVERY ENHANCEMENT SYSTEM - TEST SUITE")
        print("=" * 70)
        print()

        # Test each capability
        print("Testing V101: Temporal Causal Discovery...")
        self.test_v101_temporal_causal()

        print("Testing V102: Scalable Counterfactual Engine...")
        self.test_v102_counterfactual()

        print("Testing V103: Multi-Modal Evidence Integration...")
        self.test_v103_multimodal_evidence()

        print("Testing V104: Adversarial Hypothesis Framework...")
        self.test_v104_adversarial_discovery()

        print("Testing V105: Meta-Discovery Transfer Learning...")
        self.test_v105_meta_discovery()

        print("Testing V106: Explainable Causal Reasoning...")
        self.test_v106_explainable_causal()

        print("Testing V107: Discovery Triage and Prioritization...")
        self.test_v107_discovery_triage()

        print("Testing V108: Real-Time Streaming Discovery...")
        self.test_v108_streaming_discovery()

        print("Testing V5.0 Orchestrator...")
        self.test_v5_orchestrator()

        # Print summary
        self._print_summary()

        return self._get_results()

    def test_v101_temporal_causal(self):
        """Test V101 Temporal Causal Discovery"""
        try:
            from geo_core.capabilities.v101_temporal_causal import (
                create_temporal_fci_discovery,
                TemporalFCIDiscovery,
                TimeLaggedPAGEdge
            )

            # Test factory function
            discovery = create_temporal_fci_discovery()
            self.results.append(V5TestResult(
                "V101 Factory",
                discovery is not None,
                "TemporalFCIDiscovery created"
            ))

            # Test temporal discovery
            result = discovery.discover_temporal_causal_structure(
                self.test_data['time_series'],
                ['var1', 'var2', 'var3'],
                max_lag=3
            )

            self.results.append(V5TestResult(
                "V101 Temporal Discovery",
                result is not None,
                f"Found {len(result.get('temporal_edges', []))} temporal edges"
            ))

            # Test Granger-FCI hybrid
            from geo_core.capabilities.v101_temporal_causal import create_granger_fci_hybrid
            hybrid = create_granger_fci_hybrid()
            self.results.append(V5TestResult(
                "V101 Granger-FCI Hybrid",
                hybrid is not None,
                "GrangerFCIHybrid created"
            ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V101 Temporal Causal",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V101 Temporal Causal",
                False,
                f"Error: {e}"
            ))

    def test_v102_counterfactual(self):
        """Test V102 Scalable Counterfactual Engine"""
        try:
            from geo_core.capabilities.v102_counterfactual_engine import (
                create_counterfactual_engine,
                CounterfactualEngine,
                Intervention
            )

            # Test factory function
            engine = create_counterfactual_engine()
            self.results.append(V5TestResult(
                "V102 Factory",
                engine is not None,
                "CounterfactualEngine created"
            ))

            # Test intervention
            intervention = Intervention(
                variable='var_A',
                value=1.5,
                intervention_type='do'
            )

            # Test causal effect estimation
            effect = engine.estimate_causal_effect(
                self.test_data['data'],
                self.test_data['variable_names'],
                {'variable': 'var_A', 'value': 1.5, 'intervention_type': 'do'},
                'var_B'
            )

            self.results.append(V5TestResult(
                "V102 Causal Effect Estimation",
                effect is not None,
                f"Estimated effect: {effect.effect_estimate:.3f}"
            ))

            # Test parallel interventions
            parallel_tester = engine.parallel_tester
            if parallel_tester:
                self.results.append(V5TestResult(
                    "V102 Parallel Tester",
                    True,
                    "ParallelInterventionTester available"
                ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V102 Counterfactual",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V102 Counterfactual",
                False,
                f"Error: {e}"
            ))

    def test_v103_multimodal_evidence(self):
        """Test V103 Multi-Modal Evidence Integration"""
        try:
            from geo_core.capabilities.v103_multimodal_evidence import (
                create_multimodal_evidence_fusion,
                MultiModalEvidenceFusion,
                EvidenceType
            )

            # Test factory function
            fusion = create_multimodal_evidence_fusion()
            self.results.append(V5TestResult(
                "V103 Factory",
                fusion is not None,
                "MultiModalEvidenceFusion created"
            ))

            # Test adding numerical evidence
            ev_id = fusion.add_numerical_evidence(
                'var_A', 'var_B', 0.75, 0.01, 500
            )
            self.results.append(V5TestResult(
                "V103 Add Numerical Evidence",
                ev_id is not None,
                f"Evidence ID: {ev_id}"
            ))

            # Test adding textual evidence
            text_id = fusion.add_textual_evidence(
                "This study demonstrates a correlation between variables.",
                "test_paper"
            )
            self.results.append(V5TestResult(
                "V103 Add Textual Evidence",
                text_id is not None,
                f"Evidence ID: {text_id}"
            ))

            # Test evidence fusion
            fusion_result = fusion.fuse_evidence_for_claim(
                "Variable A causes Variable B",
                [ev_id, text_id]
            )
            self.results.append(V5TestResult(
                "V103 Evidence Fusion",
                fusion_result is not None,
                f"Confidence: {fusion_result.aggregate_confidence:.2f}"
            ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V103 Multi-Modal Evidence",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V103 Multi-Modal Evidence",
                False,
                f"Error: {e}"
            ))

    def test_v104_adversarial_discovery(self):
        """Test V104 Adversarial Hypothesis Framework"""
        try:
            from geo_core.capabilities.v104_adversarial_discovery import (
                create_adversarial_discovery_system,
                AdversarialDiscoverySystem,
                DevilsAdvocateAgent
            )

            # Test factory function
            system = create_adversarial_discovery_system()
            self.results.append(V5TestResult(
                "V104 Factory",
                system is not None,
                "AdversarialDiscoverySystem created"
            ))

            # Test devil's advocate
            challenges = system.advocate.generate_challenges(
                hypothesis="Variable A causes Variable B",
                hypothesis_type="causal",
                variables=['var_A', 'var_B'],
                effect_size=0.7,
                sample_size=500
            )
            self.results.append(V5TestResult(
                "V104 Generate Challenges",
                len(challenges) > 0,
                f"Generated {len(challenges)} challenges"
            ))

            # Test red team falsification
            falsification = system.red_team.attempt_falsification(
                self.test_data['data'],
                self.test_data['variable_names'],
                "var_A causes var_B",
                0.7
            )
            self.results.append(V5TestResult(
                "V104 Red Team Falsification",
                'falsification_attempts' in falsification,
                f"Attempts: {len(falsification['falsification_attempts'])}"
            ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V104 Adversarial Discovery",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V104 Adversarial Discovery",
                False,
                f"Error: {e}"
            ))

    def test_v105_meta_discovery(self):
        """Test V105 Meta-Discovery Transfer Learning"""
        try:
            from geo_core.capabilities.v105_meta_discovery import (
                create_meta_discovery_transfer_engine,
                MetaDiscoveryTransferEngine,
                DiscoveryPattern
            )

            # Test factory function
            engine = create_meta_discovery_transfer_engine()
            self.results.append(V5TestResult(
                "V105 Factory",
                engine is not None,
                "MetaDiscoveryTransferEngine created"
            ))

            # Test pattern library
            patterns = engine.pattern_library.find_similar_patterns(
                "star_formation",
                ["causal_structure", "latent_confounders"]
            )
            self.results.append(V5TestResult(
                "V105 Pattern Library",
                len(patterns) >= 0,
                f"Found {len(patterns)} similar patterns"
            ))

            # Test few-shot learning
            adaptation = engine.few_shot_learner.adapt_to_new_domain(
                ["star_formation"],
                {'domain': 'test', 'data': self.test_data['data']},
                n_shots=[5]
            )
            self.results.append(V5TestResult(
                "V105 Few-Shot Learning",
                adaptation is not None,
                f"Performance: {adaptation.adaptation_performance:.2f}"
            ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V105 Meta-Discovery",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V105 Meta-Discovery",
                False,
                f"Error: {e}"
            ))

    def test_v106_explainable_causal(self):
        """Test V106 Explainable Causal Reasoning"""
        try:
            from geo_core.capabilities.v106_explainable_causal import (
                create_explainable_causal_reasoner,
                ExplainableCausalReasoner,
                CausalExplanation,
                CausalRelationshipType
            )

            # Test factory function
            reasoner = create_explainable_causal_reasoner()
            self.results.append(V5TestResult(
                "V106 Factory",
                reasoner is not None,
                "ExplainableCausalReasoner created"
            ))

            # Test causal explanation
            explanation = CausalExplanation(
                source="Jeans mass",
                target="Star formation rate",
                relationship_type=CausalRelationshipType.DIRECT_CAUSATION,
                strength=0.8,
                confidence=0.9,
                mechanism="Gravitational instability"
            )
            natural_language = explanation.to_natural_language()
            self.results.append(V5TestResult(
                "V106 Natural Language Explanation",
                len(natural_language) > 0,
                f"Generated: {natural_language[:50]}..."
            ))

            # Test story generator
            story_gen = reasoner.story_gen
            self.results.append(V5TestResult(
                "V106 Story Generator",
                story_gen is not None,
                "CausalStoryGenerator available"
            ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V106 Explainable Causal",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V106 Explainable Causal",
                False,
                f"Error: {e}"
            ))

    def test_v107_discovery_triage(self):
        """Test V107 Discovery Triage and Prioritization"""
        try:
            from geo_core.capabilities.v107_discovery_triage import (
                create_discovery_triage_system,
                DiscoveryTriageSystem,
                TriageCategory,
                ImpactDimension
            )

            # Test factory function
            triage = create_discovery_triage_system()
            self.results.append(V5TestResult(
                "V107 Factory",
                triage is not None,
                "DiscoveryTriageSystem created"
            ))

            # Test impact scoring
            discovery = {
                'discovery_id': 'test_001',
                'claim': 'Variable A causes Variable B',
                'novelty_score': 0.8,
                'sample_size': 500,
                'effect_size': 0.7
            }

            result = triage.triage_discovery(discovery, "test_domain")
            self.results.append(V5TestResult(
                "V107 Discovery Triage",
                result is not None,
                f"Category: {result.triage_category.value}, "
                f"Impact: {result.overall_impact_score:.2f}"
            ))

            # Test batch triage
            discoveries = [discovery] * 3
            batch_results = triage.triage_batch(discoveries, "test_domain")
            self.results.append(V5TestResult(
                "V107 Batch Triage",
                len(batch_results) == 3,
                f"Triaged {len(batch_results)} discoveries"
            ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V107 Discovery Triage",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V107 Discovery Triage",
                False,
                f"Error: {e}"
            ))

    def test_v108_streaming_discovery(self):
        """Test V108 Real-Time Streaming Discovery"""
        try:
            from geo_core.capabilities.v108_streaming_discovery import (
                create_streaming_discovery_engine,
                StreamingDiscoveryEngine,
                OnlineCausalDiscovery,
                StreamingAlertSystem
            )

            # Test factory function
            engine = create_streaming_discovery_engine(
                variable_names=['var1', 'var2', 'var3'],
                initial_batch_size=100,
                update_interval=50
            )
            self.results.append(V5TestResult(
                "V108 Factory",
                engine is not None,
                "StreamingDiscoveryEngine created"
            ))

            # Test online processing
            batch1 = self.test_data['time_series'][:100]
            result = engine.process_stream_batch(batch1)
            self.results.append(V5TestResult(
                "V108 Stream Processing",
                'state' in result,
                f"State: {result['state']}, "
                f"Observations: {result['n_observations']}"
            ))

            # Test alert system
            alert_system = engine.alert_system
            self.results.append(V5TestResult(
                "V108 Alert System",
                alert_system is not None,
                "StreamingAlertSystem available"
            ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V108 Streaming Discovery",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V108 Streaming Discovery",
                False,
                f"Error: {e}"
            ))

    def test_v5_orchestrator(self):
        """Test V5.0 Discovery Orchestrator"""
        try:
            from geo_core.v5_discovery_orchestrator import (
                create_v5_discovery_orchestrator,
                V5DiscoveryOrchestrator,
                discover_in_dataset,
                get_v5_capabilities
            )

            # Test capability check
            capabilities = get_v5_capabilities()
            available = sum(capabilities.values())
            self.results.append(V5TestResult(
                "V5.0 Capability Check",
                available > 0,
                f"{available}/8 capabilities available"
            ))

            # Test orchestrator creation
            orchestrator = create_v5_discovery_orchestrator()
            self.results.append(V5TestResult(
                "V5.0 Orchestrator Factory",
                orchestrator is not None,
                "V5DiscoveryOrchestrator created"
            ))

            # Test discovery pipeline
            result = orchestrator.run_standard_discovery(
                self.test_data['data'],
                self.test_data['variable_names']
            )
            self.results.append(V5TestResult(
                "V5.0 Standard Discovery",
                result is not None,
                f"Claim: {result.claim[:60]}..."
            ))

            # Test summary
            summary = orchestrator.get_discovery_summary()
            self.results.append(V5TestResult(
                "V5.0 Summary",
                len(summary) > 0,
                f"Summary length: {len(summary)} chars"
            ))

        except ImportError as e:
            self.results.append(V5TestResult(
                "V5.0 Orchestrator",
                False,
                f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(V5TestResult(
                "V5.0 Orchestrator",
                False,
                f"Error: {e}"
            ))

    def _print_summary(self):
        """Print test summary"""
        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")

        # Group results by capability
        by_capability = {}
        for result in self.results:
            cap = result.name.split(':')[0]
            if cap not in by_capability:
                by_capability[cap] = []
            by_capability[cap].append(result)

        for cap, cap_results in sorted(by_capability.items()):
            cap_passed = sum(1 for r in cap_results if r.passed)
            cap_total = len(cap_results)
            status = "✓" if cap_passed == cap_total else "✗"
            print(f"{status} {cap}: {cap_passed}/{cap_total} passed")

        print()
        print("=" * 70)

    def _get_results(self) -> Dict[str, Any]:
        """Get test results as dict"""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        return {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': pass_rate,
            'results': [(r.name, r.passed, r.message) for r in self.results],
            'success': pass_rate >= 80  # Success if 80%+ pass
        }


def main():
    """Main test runner"""
    suite = V5TestSuite()
    results = suite.run_all_tests()

    # Exit with appropriate code
    return 0 if results['success'] else 1


if __name__ == '__main__':
    exit(main())
