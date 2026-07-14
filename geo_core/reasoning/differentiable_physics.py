"""
Differentiable Physics Engine for STAN V42

Implements automatic differentiation through physics forward models,
enabling gradient-based optimization for physics-based inference.

Key capabilities:
- Automatic differentiation through any physics model
- Gradient computation for parameter sensitivity analysis
- Hessian approximation for uncertainty estimation
- Integration with gradient-based samplers (HMC, NUTS)
- Physics-informed neural network components

All geochemistry models in SI units following STAN conventions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple, Union
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Physical Constants (SI, geochemistry-standard)
# ============================================================================

G_GRAV = 9.81            # Gravitational acceleration at Earth surface [m/s²]
R_GAS = 8.314            # Universal gas constant [J/mol/K]
K_BOLTZMANN = 1.381e-23  # Boltzmann constant [J/K]
M_H2O = 0.018015         # Molar mass of water [kg/mol]
M_CACO3 = 0.100086       # Molar mass of calcite [kg/mol]
M_CORG = 0.012011        # Molar mass of carbon [kg/mol]
M_FEO = 0.071844         # Molar mass of FeO [kg/mol]
M_PYRITE = 0.119975      # Molar mass of FeS2 [kg/mol]
RHO_WATER = 1000.0       # Density of water [kg/m³]
RHO_SEDIMENT = 2500.0    # Typical sediment grain density [kg/m³]
VISCOSITY_WATER = 1.0e-3 # Dynamic viscosity of water at 20 deg C [Pa*s]


# ============================================================================
# Dual Numbers for Automatic Differentiation
# ============================================================================

class DualNumber:
    """
    Dual number for forward-mode automatic differentiation.
    Represents value + epsilon * derivative
    """

    def __init__(self, value: float, derivative: float = 0.0):
        self.value = value
        self.derivative = derivative

    def __repr__(self) -> str:
        return f"Dual({self.value}, {self.derivative})"

    def __add__(self, other: Union['DualNumber', float]) -> 'DualNumber':
        if isinstance(other, DualNumber):
            return DualNumber(self.value + other.value,
                            self.derivative + other.derivative)
        return DualNumber(self.value + other, self.derivative)

    def __radd__(self, other: float) -> 'DualNumber':
        return self + other

    def __sub__(self, other: Union['DualNumber', float]) -> 'DualNumber':
        if isinstance(other, DualNumber):
            return DualNumber(self.value - other.value,
                            self.derivative - other.derivative)
        return DualNumber(self.value - other, self.derivative)

    def __rsub__(self, other: float) -> 'DualNumber':
        return DualNumber(other - self.value, -self.derivative)

    def __mul__(self, other: Union['DualNumber', float]) -> 'DualNumber':
        if isinstance(other, DualNumber):
            # Product rule: (f*g)' = f'*g + f*g'
            return DualNumber(self.value * other.value,
                            self.derivative * other.value + self.value * other.derivative)
        return DualNumber(self.value * other, self.derivative * other)

    def __rmul__(self, other: float) -> 'DualNumber':
        return self * other

    def __truediv__(self, other: Union['DualNumber', float]) -> 'DualNumber':
        if isinstance(other, DualNumber):
            # Quotient rule: (f/g)' = (f'*g - f*g') / g²
            return DualNumber(
                self.value / other.value,
                (self.derivative * other.value - self.value * other.derivative) / (other.value ** 2)
            )
        return DualNumber(self.value / other, self.derivative / other)

    def __rtruediv__(self, other: float) -> 'DualNumber':
        return DualNumber(other / self.value, -other * self.derivative / (self.value ** 2))

    def __pow__(self, n: Union[int, float, 'DualNumber']) -> 'DualNumber':
        if isinstance(n, DualNumber):
            # (f^g)' = f^g * (g' * ln(f) + g * f'/f)
            if self.value <= 0:
                return DualNumber(0.0, 0.0)
            val = self.value ** n.value
            deriv = val * (n.derivative * math.log(self.value) +
                          n.value * self.derivative / self.value)
            return DualNumber(val, deriv)
        # f^n: (f^n)' = n * f^(n-1) * f'
        return DualNumber(self.value ** n, n * (self.value ** (n - 1)) * self.derivative)

    def __neg__(self) -> 'DualNumber':
        return DualNumber(-self.value, -self.derivative)

    def __abs__(self) -> 'DualNumber':
        if self.value >= 0:
            return DualNumber(self.value, self.derivative)
        return DualNumber(-self.value, -self.derivative)

    def __lt__(self, other: Union['DualNumber', float]) -> bool:
        if isinstance(other, DualNumber):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: Union['DualNumber', float]) -> bool:
        if isinstance(other, DualNumber):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: Union['DualNumber', float]) -> bool:
        if isinstance(other, DualNumber):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: Union['DualNumber', float]) -> bool:
        if isinstance(other, DualNumber):
            return self.value >= other.value
        return self.value >= other


# Differentiable math functions
def dual_sqrt(x: DualNumber) -> DualNumber:
    """Square root for dual numbers."""
    val = math.sqrt(x.value)
    return DualNumber(val, x.derivative / (2 * val) if val != 0 else 0.0)


def dual_exp(x: DualNumber) -> DualNumber:
    """Exponential for dual numbers."""
    val = math.exp(x.value)
    return DualNumber(val, val * x.derivative)


def dual_log(x: DualNumber) -> DualNumber:
    """Natural log for dual numbers."""
    return DualNumber(math.log(x.value), x.derivative / x.value)


def dual_sin(x: DualNumber) -> DualNumber:
    """Sine for dual numbers."""
    return DualNumber(math.sin(x.value), math.cos(x.value) * x.derivative)


def dual_cos(x: DualNumber) -> DualNumber:
    """Cosine for dual numbers."""
    return DualNumber(math.cos(x.value), -math.sin(x.value) * x.derivative)


def dual_atan2(y: DualNumber, x: DualNumber) -> DualNumber:
    """Arctangent for dual numbers."""
    denom = x.value ** 2 + y.value ** 2
    return DualNumber(
        math.atan2(y.value, x.value),
        (x.value * y.derivative - y.value * x.derivative) / denom if denom != 0 else 0.0
    )


# ============================================================================
# Gradient Tape for Reverse-Mode AD
# ============================================================================

class GradientTape:
    """
    Gradient tape for reverse-mode automatic differentiation.
    Records operations for backward pass.
    """

    def __init__(self):
        self.operations: List[Tuple[str, Any, Any, Any]] = []
        self.values: Dict[int, float] = {}
        self.adjoints: Dict[int, float] = {}
        self._watching: Dict[str, int] = {}

    def watch(self, name: str, value: float) -> int:
        """Watch a variable for gradient computation."""
        var_id = id(value) if isinstance(value, object) else hash((name, value))
        self.values[var_id] = value
        self._watching[name] = var_id
        return var_id

    def record_op(self, op: str, inputs: List[int], output_id: int, output_val: float):
        """Record an operation."""
        self.operations.append((op, inputs, output_id, output_val))
        self.values[output_id] = output_val

    def gradient(self, output_id: int, var_names: List[str]) -> Dict[str, float]:
        """Compute gradients via reverse-mode AD."""
        # Initialize adjoints
        self.adjoints = {vid: 0.0 for vid in self.values}
        self.adjoints[output_id] = 1.0

        # Backward pass
        for op, inputs, out_id, out_val in reversed(self.operations):
            adj = self.adjoints.get(out_id, 0.0)

            if op == "add":
                for inp_id in inputs:
                    self.adjoints[inp_id] = self.adjoints.get(inp_id, 0.0) + adj
            elif op == "mul":
                # d(a*b) = a*db + b*da
                a_id, b_id = inputs
                a_val = self.values[a_id]
                b_val = self.values[b_id]
                self.adjoints[a_id] = self.adjoints.get(a_id, 0.0) + adj * b_val
                self.adjoints[b_id] = self.adjoints.get(b_id, 0.0) + adj * a_val
            elif op == "div":
                a_id, b_id = inputs
                a_val = self.values[a_id]
                b_val = self.values[b_id]
                self.adjoints[a_id] = self.adjoints.get(a_id, 0.0) + adj / b_val
                self.adjoints[b_id] = self.adjoints.get(b_id, 0.0) - adj * a_val / (b_val ** 2)
            elif op == "pow":
                base_id, exp_id = inputs
                base = self.values[base_id]
                exp = self.values[exp_id]
                if base > 0:
                    self.adjoints[base_id] = self.adjoints.get(base_id, 0.0) + adj * exp * (base ** (exp - 1))
                    self.adjoints[exp_id] = self.adjoints.get(exp_id, 0.0) + adj * out_val * math.log(base)
            elif op == "sqrt":
                inp_id = inputs[0]
                if out_val != 0:
                    self.adjoints[inp_id] = self.adjoints.get(inp_id, 0.0) + adj / (2 * out_val)
            elif op == "exp":
                inp_id = inputs[0]
                self.adjoints[inp_id] = self.adjoints.get(inp_id, 0.0) + adj * out_val
            elif op == "log":
                inp_id = inputs[0]
                inp_val = self.values[inp_id]
                if inp_val != 0:
                    self.adjoints[inp_id] = self.adjoints.get(inp_id, 0.0) + adj / inp_val

        # Extract requested gradients
        result = {}
        for name in var_names:
            var_id = self._watching.get(name)
            if var_id is not None:
                result[name] = self.adjoints.get(var_id, 0.0)
            else:
                result[name] = 0.0

        return result


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class GradientResult:
    """Result of gradient computation."""
    value: float
    gradients: Dict[str, float]
    parameters: Dict[str, float]


@dataclass
class HessianResult:
    """Result of Hessian computation."""
    value: float
    gradients: Dict[str, float]
    hessian: Dict[str, Dict[str, float]]
    parameters: Dict[str, float]


@dataclass
class SensitivityAnalysis:
    """Sensitivity analysis result."""
    parameter: str
    sensitivity: float  # |∂output/∂param| * param/output (elasticity)
    gradient: float
    relative_importance: float


# ============================================================================
# Differentiable Physics Models
# ============================================================================

class DifferentiablePhysicsEngine:
    """
    Main engine for differentiable physics computations.
    Supports both forward-mode and reverse-mode AD.
    """

    def __init__(self):
        self.models: Dict[str, Callable] = {}
        self._register_builtin_models()
        self._event_bus = None

    def _register_builtin_models(self):
        """Register built-in geochemistry models."""
        self.models["geothermal_gradient"] = self._geothermal_gradient
        self.models["compaction"] = self._compaction_model
        self.models["kerogen_maturation"] = self._kerogen_maturation
        self.models["toc_preservation"] = self._toc_preservation
        self.models["stokes_settling"] = self._stokes_settling
        self.models["pyritization"] = self._pyritization_rate
        self.models["sulfate_reduction"] = self._sulfate_reduction_rate
        self.models["carbon_isotope_fractionation"] = self._carbon_isotope_fractionation
        self.models["carbonate_saturation"] = self._carbonate_saturation
        self.models["silicification"] = self._silicification_rate

    def set_event_bus(self, event_bus):
        """Set event bus for integration."""
        self._event_bus = event_bus

    def register_model(self, name: str, model_fn: Callable):
        """Register a custom physics model."""
        self.models[name] = model_fn

    def compute_gradient(self,
                         model_name: str,
                         parameters: Dict[str, float],
                         diff_params: Optional[List[str]] = None) -> GradientResult:
        """
        Compute gradient of model output with respect to parameters.

        Uses forward-mode AD (efficient for few parameters).
        """
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        model = self.models[model_name]
        diff_params = diff_params or list(parameters.keys())

        gradients = {}

        # Compute gradient for each parameter
        for param_name in diff_params:
            # Create dual numbers with derivative wrt this parameter
            dual_params = {}
            for name, val in parameters.items():
                if name == param_name:
                    dual_params[name] = DualNumber(val, 1.0)
                else:
                    dual_params[name] = DualNumber(val, 0.0)

            # Evaluate model with dual numbers
            result = model(dual_params)

            if isinstance(result, DualNumber):
                gradients[param_name] = result.derivative
            else:
                gradients[param_name] = 0.0

        # Get scalar value
        scalar_params = {name: DualNumber(val, 0.0) for name, val in parameters.items()}
        result = model(scalar_params)
        value = result.value if isinstance(result, DualNumber) else result

        return GradientResult(
            value=value,
            gradients=gradients,
            parameters=parameters.copy()
        )

    def compute_hessian(self,
                        model_name: str,
                        parameters: Dict[str, float],
                        diff_params: Optional[List[str]] = None) -> HessianResult:
        """
        Compute Hessian matrix using finite differences on gradients.
        """
        diff_params = diff_params or list(parameters.keys())

        # Get gradient at current point
        grad_result = self.compute_gradient(model_name, parameters, diff_params)

        # Compute Hessian via finite differences
        epsilon = 1e-6
        hessian = {p1: {p2: 0.0 for p2 in diff_params} for p1 in diff_params}

        for p1 in diff_params:
            # Perturb parameter
            params_plus = parameters.copy()
            params_plus[p1] = parameters[p1] + epsilon

            grad_plus = self.compute_gradient(model_name, params_plus, diff_params)

            for p2 in diff_params:
                hessian[p1][p2] = (grad_plus.gradients[p2] - grad_result.gradients[p2]) / epsilon

        return HessianResult(
            value=grad_result.value,
            gradients=grad_result.gradients,
            hessian=hessian,
            parameters=parameters.copy()
        )

    def sensitivity_analysis(self,
                             model_name: str,
                             parameters: Dict[str, float]) -> List[SensitivityAnalysis]:
        """
        Perform sensitivity analysis on model parameters.
        """
        grad_result = self.compute_gradient(model_name, parameters)

        sensitivities = []
        total_sensitivity = 0.0

        for param, grad in grad_result.gradients.items():
            # Elasticity: percent change in output per percent change in input
            param_val = parameters[param]
            if grad_result.value != 0 and param_val != 0:
                elasticity = abs(grad * param_val / grad_result.value)
            else:
                elasticity = 0.0

            sensitivities.append(SensitivityAnalysis(
                parameter=param,
                sensitivity=elasticity,
                gradient=grad,
                relative_importance=0.0  # Computed below
            ))
            total_sensitivity += elasticity

        # Compute relative importance
        if total_sensitivity > 0:
            for s in sensitivities:
                s.relative_importance = s.sensitivity / total_sensitivity

        # Sort by importance
        sensitivities.sort(key=lambda s: s.relative_importance, reverse=True)

        return sensitivities

    # ========================================================================
    # Built-in Differentiable Physics Models
    # ========================================================================

    def _geothermal_gradient(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Geothermal temperature profile.
        T(z) = T_surface + gradient * z

        Parameters: T_surface (deg C), gradient (deg C/km), z (km)
        Returns: formation temperature [deg C]
        """
        T_surf = params.get("T_surface", DualNumber(20.0, 0.0))
        gradient = params.get("gradient", DualNumber(30.0, 0.0))
        z = params.get("z", DualNumber(2.0, 0.0))

        return T_surf + gradient * z

    def _compaction_model(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Athy's compaction law.
        phi(z) = phi0 * exp(-c * z)

        Parameters: phi0 (initial porosity), c (1/km), z (km)
        Returns: porosity at depth [fraction]
        """
        phi0 = params.get("phi0", DualNumber(0.6, 0.0))
        c = params.get("c", DualNumber(0.4, 0.0))
        z = params.get("z", DualNumber(1.0, 0.0))

        neg_one = DualNumber(-1.0, 0.0)
        exponent = neg_one * c * z

        return phi0 * dual_exp(exponent)

    def _kerogen_maturation(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Simplified Arrhenius kerogen maturation.
        X(T) = exp(-Ea / (R * T_K))

        Parameters: Ea (J/mol), T (deg C)
        Returns: transformation fraction [0-1]
        """
        Ea = params.get("Ea", DualNumber(200000.0, 0.0))
        T = params.get("T", DualNumber(150.0, 0.0))  # deg C

        R = DualNumber(R_GAS, 0.0)
        two_seventy_three = DualNumber(273.15, 0.0)
        T_K = T + two_seventy_three

        neg_one = DualNumber(-1.0, 0.0)
        exponent = neg_one * Ea / (R * T_K)

        return dual_exp(exponent)

    def _toc_preservation(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Organic carbon preservation model.
        TOC = flux * exp(-k * O2_exposure)

        Parameters: flux (wt%), O2_exposure (dimensionless), k (rate)
        Returns: preserved TOC [wt%]
        """
        flux = params.get("flux", DualNumber(5.0, 0.0))
        O2_exposure = params.get("O2_exposure", DualNumber(0.5, 0.0))
        k = params.get("k", DualNumber(2.0, 0.0))

        neg_one = DualNumber(-1.0, 0.0)
        exponent = neg_one * k * O2_exposure

        return flux * dual_exp(exponent)

    def _stokes_settling(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Stokes settling velocity.
        v_s = (rho_s - rho_w) * g * d^2 / (18 * mu)

        Parameters: d (grain diameter m), rho_s (kg/m^3), rho_w (kg/m^3)
        Returns: settling velocity [m/s]
        """
        d = params.get("d", DualNumber(1e-5, 0.0))
        rho_s = params.get("rho_s", DualNumber(RHO_SEDIMENT, 0.0))
        rho_w = params.get("rho_w", DualNumber(RHO_WATER, 0.0))

        g = DualNumber(G_GRAV, 0.0)
        mu = DualNumber(VISCOSITY_WATER, 0.0)
        eighteen = DualNumber(18.0, 0.0)

        return (rho_s - rho_w) * g * d * d / (eighteen * mu)

    def _pyritization_rate(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Pyritization rate (simplified).
        R = k * Fe_HR * H2S

        Parameters: Fe_HR (wt%), H2S (uM), k (rate constant)
        Returns: pyrite formation rate [relative]
        """
        Fe_HR = params.get("Fe_HR", DualNumber(1.0, 0.0))
        H2S = params.get("H2S", DualNumber(100.0, 0.0))
        k = params.get("k", DualNumber(1e-3, 0.0))

        return k * Fe_HR * H2S

    def _sulfate_reduction_rate(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Microbial sulfate reduction rate (simplified Michaelis-Menten).
        R = R_max * [SO4] / (Km + [SO4]) * [OC]

        Parameters: SO4 (mM), OC (wt%), R_max (mol/L/yr), Km (mM)
        Returns: sulfate reduction rate [mol/L/yr]
        """
        SO4 = params.get("SO4", DualNumber(10.0, 0.0))
        OC = params.get("OC", DualNumber(1.0, 0.0))
        R_max = params.get("R_max", DualNumber(1e-4, 0.0))
        Km = params.get("Km", DualNumber(5.0, 0.0))

        return R_max * SO4 / (Km + SO4) * OC

    def _carbon_isotope_fractionation(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Temperature-dependent carbon isotope fractionation.
        delta = a * 1e6 / T_K^2  (simplified)

        Parameters: T (deg C), a (fractionation coefficient)
        Returns: fractionation [per mil]
        """
        T = params.get("T", DualNumber(25.0, 0.0))
        a = params.get("a", DualNumber(1.0, 0.0))

        two_seventy_three = DualNumber(273.15, 0.0)
        T_K = T + two_seventy_three
        one_million = DualNumber(1e6, 0.0)

        return a * one_million / (T_K * T_K)

    def _carbonate_saturation(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Calcite saturation state.
        Omega = [Ca2+] * [CO3--] / Ksp

        Parameters: Ca (mM), CO3 (mM), Ksp (solubility product)
        Returns: saturation state Omega (Omega > 1 precipitates)
        """
        Ca = params.get("Ca", DualNumber(10.0, 0.0))
        CO3 = params.get("CO3", DualNumber(0.5, 0.0))
        Ksp = params.get("Ksp", DualNumber(3.3e-7, 0.0))

        # Convert mM to mol/L
        one_million = DualNumber(1e6, 0.0)
        return Ca * CO3 * one_million / (Ksp * DualNumber(1e6, 0.0))

    def _silicification_rate(self, params: Dict[str, DualNumber]) -> DualNumber:
        """
        Silica precipitation / silicification rate (simplified).
        R = k * (SiO2 - SiO2_eq)

        Parameters: SiO2 (ppm), SiO2_eq (equilibrium ppm), k (rate)
        Returns: silica precipitation rate [ppm/yr]
        """
        SiO2 = params.get("SiO2", DualNumber(120.0, 0.0))
        SiO2_eq = params.get("SiO2_eq", DualNumber(100.0, 0.0))
        k = params.get("k", DualNumber(0.01, 0.0))

        return k * (SiO2 - SiO2_eq)


# ============================================================================
# Gradient-Based Optimization
# ============================================================================

class GradientOptimizer:
    """
    Gradient-based optimizer for physics models.
    """

    def __init__(self, engine: DifferentiablePhysicsEngine):
        self.engine = engine

    def optimize(self,
                 model_name: str,
                 initial_params: Dict[str, float],
                 target_value: float,
                 bounds: Optional[Dict[str, Tuple[float, float]]] = None,
                 learning_rate: float = 0.01,
                 max_iterations: int = 1000,
                 tolerance: float = 1e-6) -> Tuple[Dict[str, float], List[float]]:
        """
        Optimize parameters to match target value using gradient descent.
        """
        params = initial_params.copy()
        losses = []

        for i in range(max_iterations):
            # Compute gradient
            result = self.engine.compute_gradient(model_name, params)

            # Loss = (value - target)²
            diff = result.value - target_value
            loss = diff * diff
            losses.append(loss)

            if loss < tolerance:
                break

            # Update parameters
            for name in params:
                grad = result.gradients.get(name, 0.0)
                # Gradient of loss wrt param: 2 * diff * dvalue/dparam
                grad_loss = 2 * diff * grad

                params[name] -= learning_rate * grad_loss

                # Apply bounds
                if bounds and name in bounds:
                    low, high = bounds[name]
                    params[name] = max(low, min(high, params[name]))

        return params, losses


# ============================================================================
# Fisher Information Matrix
# ============================================================================

class FisherInformationEstimator:
    """
    Estimates Fisher information matrix for parameter uncertainty.
    """

    def __init__(self, engine: DifferentiablePhysicsEngine):
        self.engine = engine

    def compute_fisher_matrix(self,
                              model_name: str,
                              parameters: Dict[str, float],
                              data_points: List[Dict[str, float]],
                              noise_variance: float) -> Dict[str, Dict[str, float]]:
        """
        Compute Fisher information matrix.
        F_ij = (1/σ²) Σ (∂μ/∂θ_i)(∂μ/∂θ_j)
        """
        param_names = list(parameters.keys())
        n_params = len(param_names)

        # Initialize Fisher matrix
        fisher = {p1: {p2: 0.0 for p2 in param_names} for p1 in param_names}

        # Sum over data points
        for data in data_points:
            # Merge data with parameters
            full_params = parameters.copy()
            full_params.update(data)

            # Compute gradient
            result = self.engine.compute_gradient(model_name, full_params, param_names)

            # Outer product of gradients
            for p1 in param_names:
                for p2 in param_names:
                    fisher[p1][p2] += (result.gradients[p1] * result.gradients[p2] /
                                      noise_variance)

        return fisher

    def parameter_uncertainties(self,
                                fisher_matrix: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Compute parameter uncertainties from Fisher matrix.
        σ_i = sqrt((F^-1)_ii)
        """
        param_names = list(fisher_matrix.keys())
        n = len(param_names)

        # Convert to list of lists for inversion
        matrix = [[fisher_matrix[p1][p2] for p2 in param_names] for p1 in param_names]

        # Simple matrix inversion (Gauss-Jordan)
        inv = self._invert_matrix(matrix)

        # Extract diagonal uncertainties
        uncertainties = {}
        for i, name in enumerate(param_names):
            if inv[i][i] > 0:
                uncertainties[name] = math.sqrt(inv[i][i])
            else:
                uncertainties[name] = float('inf')

        return uncertainties

    def _invert_matrix(self, matrix: List[List[float]]) -> List[List[float]]:
        """Gauss-Jordan matrix inversion."""
        n = len(matrix)

        # Augment with identity
        aug = [row + [1.0 if i == j else 0.0 for j in range(n)]
               for i, row in enumerate(matrix)]

        # Forward elimination
        for i in range(n):
            # Find pivot
            max_row = max(range(i, n), key=lambda r: abs(aug[r][i]))
            aug[i], aug[max_row] = aug[max_row], aug[i]

            if abs(aug[i][i]) < 1e-10:
                continue

            # Scale row
            scale = aug[i][i]
            aug[i] = [x / scale for x in aug[i]]

            # Eliminate column
            for j in range(n):
                if i != j:
                    factor = aug[j][i]
                    aug[j] = [aug[j][k] - factor * aug[i][k] for k in range(2 * n)]

        # Extract inverse
        return [row[n:] for row in aug]


# ============================================================================
# Singleton Access
# ============================================================================

_physics_engine: Optional[DifferentiablePhysicsEngine] = None


def get_differentiable_physics_engine() -> DifferentiablePhysicsEngine:
    """Get singleton physics engine instance."""
    global _physics_engine
    if _physics_engine is None:
        _physics_engine = DifferentiablePhysicsEngine()
    return _physics_engine


# ============================================================================
# Integration with STAN Event Bus
# ============================================================================

def setup_differentiable_physics_integration(event_bus) -> None:
    """Set up differentiable physics integration with STAN event bus."""
    engine = get_differentiable_physics_engine()
    engine.set_event_bus(event_bus)

    def on_gradient_request(event):
        """Handle gradient computation requests."""
        payload = event.get("payload", {})
        model_name = payload.get("model")
        parameters = payload.get("parameters", {})

        if model_name and parameters:
            result = engine.compute_gradient(model_name, parameters)

            event_bus.publish(
                "gradient_result",
                "differentiable_physics",
                {
                    "model": model_name,
                    "value": result.value,
                    "gradients": result.gradients
                }
            )

    def on_sensitivity_request(event):
        """Handle sensitivity analysis requests."""
        payload = event.get("payload", {})
        model_name = payload.get("model")
        parameters = payload.get("parameters", {})

        if model_name and parameters:
            sensitivities = engine.sensitivity_analysis(model_name, parameters)

            event_bus.publish(
                "sensitivity_result",
                "differentiable_physics",
                {
                    "model": model_name,
                    "sensitivities": [
                        {
                            "parameter": s.parameter,
                            "elasticity": s.sensitivity,
                            "gradient": s.gradient,
                            "importance": s.relative_importance
                        }
                        for s in sensitivities
                    ]
                }
            )

    event_bus.subscribe("gradient_request", on_gradient_request)
    event_bus.subscribe("sensitivity_request", on_sensitivity_request)
    logger.info("Differentiable physics integration configured")
