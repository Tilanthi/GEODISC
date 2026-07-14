"""
Physical Process Library for STAN V43

Encyclopedia of geochemical mechanisms for reasoning about Proterozoic
geochemistry and sedimentary systems.  Provides a searchable database of
physical processes with equations, inputs/outputs, validity conditions,
and causal relationships.

Features:
- ~100 geochemical / sedimentological processes with full documentation
- Searchable by category, observable, timescale
- Causal chain building (A -> B -> C)
- Mechanism matching from observations
- Process validity checking

Author: STAN V43 Geochemistry Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Set, Callable, Any


class ProcessCategory(Enum):
    """Categories of physical processes."""
    RADIATIVE = auto()        # Emission/absorption processes
    DYNAMICAL = auto()        # Motion and forces
    THERMAL = auto()          # Heating and cooling
    CHEMICAL = auto()         # Chemical reactions
    MAGNETIC = auto()         # Magnetic field processes
    NUCLEAR = auto()          # Nuclear reactions
    GRAVITATIONAL = auto()    # Gravity-related
    TURBULENT = auto()        # Turbulence-related


class ProcessTimescale(Enum):
    """Characteristic timescales."""
    INSTANTANEOUS = auto()    # < 1 yr
    FAST = auto()             # 1 - 1000 yr
    INTERMEDIATE = auto()     # 1000 yr - 1 Myr
    SLOW = auto()             # 1 Myr - 100 Myr
    VERY_SLOW = auto()        # > 100 Myr


class EnergyScale(Enum):
    """Energy scales of processes."""
    THERMAL = auto()          # k_B * T ~ 1 meV - 1 eV
    CHEMICAL = auto()         # ~1 eV
    IONIZATION = auto()       # 1 - 100 eV
    X_RAY = auto()            # 0.1 - 10 keV
    GAMMA = auto()            # > 100 keV
    NUCLEAR = auto()          # MeV


@dataclass
class PhysicalQuantity:
    """A physical quantity with units."""
    name: str
    symbol: str
    units: str
    typical_range: Tuple[float, float]  # (min, max)
    description: str = ""


@dataclass
class ProcessEquation:
    """Mathematical representation of a process."""
    equation: str             # LaTeX-style equation
    python_form: str          # Python expression
    dependencies: List[str]   # Required input quantities
    output: str               # Output quantity name


@dataclass
class ValidityCondition:
    """Condition for process applicability."""
    parameter: str            # Parameter to check
    condition: str            # 'gt', 'lt', 'between', 'eq'
    value: float              # Threshold value
    value_max: Optional[float] = None  # For 'between'
    units: str = ""
    explanation: str = ""


@dataclass
class PhysicalProcess:
    """Complete specification of a physical process."""
    process_id: str           # Unique identifier
    name: str                 # Human-readable name
    category: ProcessCategory
    subcategory: str          # More specific classification
    description: str          # Full description

    # Physics
    equation: ProcessEquation
    rate_equation: Optional[ProcessEquation] = None  # For time-dependent

    # Inputs and outputs
    inputs: List[PhysicalQuantity] = field(default_factory=list)
    outputs: List[PhysicalQuantity] = field(default_factory=list)

    # Validity
    validity_conditions: List[ValidityCondition] = field(default_factory=list)
    domain: str = "sedimentary"       # Physical domain

    # Timescales
    timescale: ProcessTimescale = ProcessTimescale.INTERMEDIATE
    timescale_equation: Optional[str] = None  # Formula for timescale

    # Observables
    observational_signatures: List[str] = field(default_factory=list)
    tracer_molecules: List[str] = field(default_factory=list)

    # Connections
    causes: List[str] = field(default_factory=list)  # Process IDs this causes
    caused_by: List[str] = field(default_factory=list)  # Process IDs that cause this

    # Metadata
    references: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


class ProcessLibrary:
    """
    Searchable database of geochemical processes.
    """

    def __init__(self):
        """Initialize process library."""
        self.processes: Dict[str, PhysicalProcess] = {}
        self._build_library()

    def _build_library(self):
        """Build the complete process library."""
        self._add_radiative_processes()
        self._add_dynamical_processes()
        self._add_thermal_processes()
        self._add_chemical_processes()
        self._add_magnetic_processes()
        self._add_gravitational_processes()

    def _add_radiative_processes(self):
        """Add spectroscopic / analytical detection processes."""

        # X-ray fluorescence (XRF) element detection
        self.processes['xrf_element_detection'] = PhysicalProcess(
            process_id='xrf_element_detection',
            name='X-Ray Fluorescence (XRF) Element Detection',
            category=ProcessCategory.RADIATIVE,
            subcategory='spectroscopic',
            description='Characteristic X-ray emission from element-specific electron transitions, used for major/trace element quantification',
            equation=ProcessEquation(
                equation=r'I_XRF = k \cdot C_i \cdot \frac{1}{\mu_{in} + \mu_{out}}',
                python_form='k * C_i / (mu_in + mu_out)',
                dependencies=['element_concentration', 'matrix_absorption'],
                output='fluorescence_intensity'
            ),
            inputs=[
                PhysicalQuantity('element_concentration', 'C_i', 'ppm', (1, 10000), 'Element concentration'),
                PhysicalQuantity('matrix_absorption', 'mu', 'cm^2/g', (1, 1000), 'Matrix mass absorption'),
            ],
            outputs=[
                PhysicalQuantity('fluorescence_intensity', 'I_XRF', 'counts/s', (1, 1e6), 'XRF line intensity'),
            ],
            validity_conditions=[
                ValidityCondition('Z', 'gt', 11, units='', explanation='Na and heavier elements'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            observational_signatures=['elemental abundance', 'Fe/Al ratio', 'trace metal enrichment'],
            keywords=['XRF', 'major elements', 'trace elements', 'analytical']
        )

        # Raman spectroscopy of carbonaceous material
        self.processes['raman_cm_spectroscopy'] = PhysicalProcess(
            process_id='raman_cm_spectroscopy',
            name='Raman Spectroscopy of Carbonaceous Material',
            category=ProcessCategory.RADIATIVE,
            subcategory='spectroscopic',
            description='Inelastic (Raman) scattering from kerogen / carbonaceous material to assess thermal maturity',
            equation=ProcessEquation(
                equation=r'R_2 = A_{D1} / (A_{D1} + A_{G} + A_{D2})',
                python_form='A_D1 / (A_D1 + A_G + A_D2)',
                dependencies=['D1_band_area', 'G_band_area'],
                output='r2_ratio'
            ),
            inputs=[
                PhysicalQuantity('D1_band_area', 'A_D1', 'a.u.', (1, 10000), 'D1 defect band area'),
                PhysicalQuantity('G_band_area', 'A_G', 'a.u.', (1, 10000), 'G graphite band area'),
            ],
            outputs=[
                PhysicalQuantity('r2_ratio', 'R2', '', (0.0, 1.0), 'R2 Raman maturity ratio'),
            ],
            validity_conditions=[
                ValidityCondition('thermal_maturity', 'gt', 0.5, units='Ro %', explanation='Sufficient ordering for Raman'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            observational_signatures=['Raman D1-G bands', 'thermal maturity estimate'],
            keywords=['Raman', 'kerogen', 'thermal maturity', 'carbonaceous material']
        )

        # ICP-MS trace metal quantification
        self.processes['icpms_trace_metal'] = PhysicalProcess(
            process_id='icpms_trace_metal',
            name='ICP-MS Trace Metal Quantification',
            category=ProcessCategory.RADIATIVE,
            subcategory='spectroscopic',
            description='Mass-spectrometric detection of trace metals (Mo, U, V, Cr) from ionised aerosol',
            equation=ProcessEquation(
                equation=r'C_i = \frac{I_i / S_i - B_i}{M_{dilution}}',
                python_form='(I_i / S_i - B_i) / M_dilution',
                dependencies=['ion_signal', 'sensitivity_factor', 'blank'],
                output='trace_metal_concentration'
            ),
            inputs=[
                PhysicalQuantity('ion_signal', 'I_i', 'counts/s', (1, 1e8), 'Ion count rate'),
                PhysicalQuantity('sensitivity_factor', 'S_i', 'counts/s/ppb', (1e3, 1e9), 'Element sensitivity'),
            ],
            outputs=[
                PhysicalQuantity('trace_metal_concentration', 'C_i', 'ppb', (0.001, 10000), 'Trace metal concentration'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            observational_signatures=['Mo concentration', 'U concentration', 'redox proxy ratios'],
            keywords=['ICP-MS', 'trace metals', 'Mo', 'U', 'redox proxies', 'analytical']
        )

        # Isotope ratio mass spectrometry (IRMS)
        self.processes['irms_isotope_ratio'] = PhysicalProcess(
            process_id='irms_isotope_ratio',
            name='Isotope Ratio Mass Spectrometry (IRMS)',
            category=ProcessCategory.RADIATIVE,
            subcategory='spectroscopic',
            description='High-precision measurement of stable isotope ratios (d13C, d34S, d15N) via gas-source mass spectrometry',
            equation=ProcessEquation(
                equation=r'\delta = \left(\frac{R_{sample}}{R_{standard}} - 1\right) \times 1000',
                python_form='(R_sample / R_standard - 1) * 1000',
                dependencies=['sample_isotope_ratio', 'standard_isotope_ratio'],
                output='delta_value_permil'
            ),
            inputs=[
                PhysicalQuantity('sample_isotope_ratio', 'R_sample', '', (0.005, 0.015), 'Heavy/light isotope ratio'),
                PhysicalQuantity('standard_isotope_ratio', 'R_standard', '', (0.005, 0.015), 'Standard isotope ratio'),
            ],
            outputs=[
                PhysicalQuantity('delta_value_permil', 'delta', 'per mil', (-100, 100), 'Delta value (per mil)'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            observational_signatures=['d13C', 'd34S', 'd15N', 'isotope excursion'],
            keywords=['IRMS', 'stable isotopes', 'd13C', 'd34S', 'isotope fractionation']
        )

    def _add_dynamical_processes(self):
        """Add sedimentary dynamical processes."""

        # Sediment compaction
        self.processes['sediment_compaction'] = PhysicalProcess(
            process_id='sediment_compaction',
            name='Sediment Compaction (Athy\'s Law)',
            category=ProcessCategory.DYNAMICAL,
            subcategory='physical_compaction',
            description='Exponential porosity reduction with burial depth under overburden stress',
            equation=ProcessEquation(
                equation=r'\phi(z) = \phi_0 \, e^{-c \, z}',
                python_form='phi0 * exp(-c * z)',
                dependencies=['initial_porosity', 'compaction_coefficient', 'depth'],
                output='porosity'
            ),
            rate_equation=ProcessEquation(
                equation=r'\frac{d\phi}{dt} = -c \, \phi \, \frac{dz}{dt}',
                python_form='-c * phi * dz_dt',
                dependencies=['porosity', 'subsidence_rate'],
                output='porosity_change_rate'
            ),
            inputs=[
                PhysicalQuantity('initial_porosity', 'phi0', '', (0.3, 0.8), 'Depositional porosity'),
                PhysicalQuantity('compaction_coefficient', 'c', '1/km', (0.1, 1.0), 'Athy compaction constant'),
            ],
            outputs=[
                PhysicalQuantity('porosity', 'phi', '', (0.01, 0.8), 'Porosity at depth'),
                PhysicalQuantity('compacted_thickness', 'h', 'm', (0.1, 10000), 'Compacted stratigraphic thickness'),
            ],
            validity_conditions=[
                ValidityCondition('burial_depth', 'gt', 0.0, units='km', explanation='Requires burial'),
            ],
            timescale=ProcessTimescale.SLOW,
            causes=['porosity_loss', 'fluid_expulsion'],
            caused_by=['basin_subsidence', 'sediment_loading'],
            observational_signatures=['porosity-depth trend', 'compaction curve'],
            keywords=['compaction', 'porosity', 'burial', 'diagenesis']
        )

        # Fluid expulsion / dewatering
        self.processes['fluid_expulsion'] = PhysicalProcess(
            process_id='fluid_expulsion',
            name='Formation Fluid Expulsion',
            category=ProcessCategory.DYNAMICAL,
            subcategory='fluid_flow',
            description='Expulsion of pore fluids during compaction-driven dewatering',
            equation=ProcessEquation(
                equation=r'q_{fluid} = -\frac{k}{\mu} \nabla P_{excess}',
                python_form='-k / mu * grad_P_excess',
                dependencies=['permeability', 'fluid_viscosity', 'excess_pressure'],
                output='fluid_flux'
            ),
            inputs=[
                PhysicalQuantity('permeability', 'k', 'mD', (1e-6, 1000), 'Rock permeability'),
                PhysicalQuantity('excess_pressure', 'P_ex', 'MPa', (0.1, 50), 'Overpressure'),
            ],
            outputs=[
                PhysicalQuantity('fluid_flux', 'q', 'm/Myr', (1e-3, 1e4), 'Darcy fluid flux'),
            ],
            timescale=ProcessTimescale.SLOW,
            causes=['cementation', 'mass_transfer'],
            caused_by=['sediment_compaction', 'tectonic_loading'],
            observational_signatures=['vein networks', 'pressure solution', 'stylolites'],
            tracer_molecules=['d18O_fluid', '87Sr/86Sr'],
            keywords=['dewatering', 'fluid flow', 'compaction', 'diagenesis']
        )

        # Diagenetic mixing
        self.processes['diagenetic_mixing'] = PhysicalProcess(
            process_id='diagenetic_mixing',
            name='Diagenetic Fluid Mixing',
            category=ProcessCategory.TURBULENT,
            subcategory='mass_transfer',
            description='Dispersive mixing of formation waters with meteoric or basinal fluids during diagenesis',
            equation=ProcessEquation(
                equation=r'D_{mix} = \alpha_L \, v_{fluid}',
                python_form='alpha_L * v_fluid',
                dependencies=['dispersivity', 'fluid_velocity'],
                output='mixing_coefficient'
            ),
            inputs=[
                PhysicalQuantity('dispersivity', 'alpha_L', 'm', (0.1, 100), 'Longitudinal dispersivity'),
                PhysicalQuantity('fluid_velocity', 'v', 'm/Myr', (0.01, 1000), 'Pore-fluid velocity'),
            ],
            outputs=[
                PhysicalQuantity('mixing_coefficient', 'D_mix', 'm^2/Myr', (0.01, 1e5), 'Dispersion coefficient'),
            ],
            timescale=ProcessTimescale.SLOW,
            timescale_equation='t_mix = L^2 / D_mix',
            causes=['cement_precipitation', 'dissolution'],
            caused_by=['fluid_expulsion', 'meteoric_flushing', 'basin_dewatering'],
            observational_signatures=['d18O mixing trends', '87Sr/86Sr variation', 'cement zonation'],
            keywords=['mixing', 'diagenesis', 'dispersion', 'formation water']
        )

    def _add_thermal_processes(self):
        """Add geothermal heating and thermal maturation processes."""

        # Geothermal heating
        self.processes['geothermal_heating'] = PhysicalProcess(
            process_id='geothermal_heating',
            name='Geothermal Heating (Conductive)',
            category=ProcessCategory.THERMAL,
            subcategory='heating',
            description='Conductive heat flow from the mantle raising temperature along the geothermal gradient',
            equation=ProcessEquation(
                equation=r'T(z) = T_{surface} + \nabla T \cdot z',
                python_form='T_surface + grad_T * z',
                dependencies=['surface_temperature', 'geothermal_gradient', 'depth'],
                output='formation_temperature'
            ),
            inputs=[
                PhysicalQuantity('geothermal_gradient', 'grad_T', 'deg_C/km', (10, 80), 'Geothermal gradient'),
                PhysicalQuantity('burial_depth', 'z', 'km', (0.1, 10), 'Burial depth'),
            ],
            outputs=[
                PhysicalQuantity('formation_temperature', 'T', 'deg_C', (15, 400), 'Formation temperature'),
            ],
            timescale=ProcessTimescale.SLOW,
            causes=['kerogen_maturation', 'mineral_recrystallisation'],
            observational_signatures=['vitrinite reflectance trend', 'clay mineral illitisation'],
            keywords=['geothermal', 'burial', 'thermal history', 'maturation']
        )

        # Kerogen thermal maturation
        self.processes['kerogen_maturation'] = PhysicalProcess(
            process_id='kerogen_maturation',
            name='Kerogen Thermal Maturation (Arrhenius)',
            category=ProcessCategory.THERMAL,
            subcategory='transformation',
            description='Time-temperature dependent conversion of kerogen to hydrocarbon products following Arrhenius kinetics',
            equation=ProcessEquation(
                equation=r'X = 1 - \exp\left[-A \int_0^t e^{-E_a / RT(t)} dt\right]',
                python_form='1 - exp(-A * integral(exp(-Ea / (R * T(t))) * dt))',
                dependencies=['activation_energy', 'temperature_history', 'time'],
                output='transformation_ratio'
            ),
            inputs=[
                PhysicalQuantity('max_temperature', 'T_max', 'deg_C', (60, 300), 'Peak burial temperature'),
                PhysicalQuantity('heating_rate', 'dT/dt', 'deg_C/Myr', (0.1, 10), 'Geological heating rate'),
            ],
            outputs=[
                PhysicalQuantity('transformation_ratio', 'X', '', (0.0, 1.0), 'Fraction of kerogen converted'),
                PhysicalQuantity('vitrinite_reflectance', 'Ro', '%', (0.2, 5.0), 'Vitrinite reflectance'),
            ],
            validity_conditions=[
                ValidityCondition('temperature', 'gt', 60, units='deg_C', explanation='Onset of maturation'),
            ],
            timescale=ProcessTimescale.SLOW,
            causes=['hydrocarbon_generation', 'graphitisation'],
            caused_by=['geothermal_heating', 'burial'],
            observational_signatures=['Ro increase', 'Tmax increase', 'biomarker degradation'],
            tracer_molecules=['pristane/phytane', 'hopanes', 'steranes'],
            keywords=['maturation', 'kerogen', 'Arrhenius', 'thermal maturity', 'Ro']
        )

        # Hydrothermal alteration
        self.processes['hydrothermal_alteration'] = PhysicalProcess(
            process_id='hydrothermal_alteration',
            name='Hydrothermal Alteration',
            category=ProcessCategory.THERMAL,
            subcategory='mineral_reaction',
            description='Mineralogical and chemical alteration of host rock by hot circulating fluids',
            equation=ProcessEquation(
                equation=r'\frac{dC_{mineral}}{dt} = k_{rxn}(T) \cdot (C_{eq} - C_{fluid})',
                python_form='k_rxn(T) * (C_eq - C_fluid)',
                dependencies=['temperature', 'fluid_composition', 'equilibrium_concentration'],
                output='alteration_rate'
            ),
            inputs=[
                PhysicalQuantity('fluid_temperature', 'T_fluid', 'deg_C', (100, 500), 'Hydrothermal fluid temperature'),
                PhysicalQuantity('fluid_flux', 'q', 'm/yr', (1e-4, 100), 'Fluid mass flux'),
            ],
            outputs=[
                PhysicalQuantity('alteration_rate', 'R_alt', 'mol/m^3/yr', (1e-8, 1e-2), 'Mineral alteration rate'),
            ],
            validity_conditions=[
                ValidityCondition('fluid_temperature', 'gt', 100, units='deg_C', explanation='Hydrothermal regime'),
            ],
            timescale=ProcessTimescale.SLOW,
            causes=['silicification', 'carbonate_cementation', 'pyritization'],
            caused_by=['magmatic_intrusion', 'basin_dewatering', 'fault_valving'],
            observational_signatures=['silica flooding', 'sericitisation', 'pyrite alteration'],
            tracer_molecules=['d18O_whole_rock', 'd13C_carbonate'],
            keywords=['hydrothermal', 'alteration', 'silicification', 'metasomatism']
        )

    def _add_chemical_processes(self):
        """Add geochemical reaction processes."""

        # Microbial sulfate reduction
        self.processes['microbial_sulfate_reduction'] = PhysicalProcess(
            process_id='microbial_sulfate_reduction',
            name='Microbial Sulfate Reduction (MSR)',
            category=ProcessCategory.CHEMICAL,
            subcategory='redox',
            description='Anaerobic respiration in which sulfate-reducing bacteria oxidise organic matter using seawater sulfate as electron acceptor',
            equation=ProcessEquation(
                equation=r'2\mathrm{CH_2O} + \mathrm{SO_4^{2-}} \rightarrow 2\mathrm{HCO_3^-} + \mathrm{H_2S}',
                python_form='k_MSR * [SO4] * [OC]',
                dependencies=['sulfate_concentration', 'organic_carbon', 'temperature'],
                output='sulfide_production_rate'
            ),
            inputs=[
                PhysicalQuantity('sulfate_concentration', 'SO4', 'mM', (0.01, 30), 'Porewater sulfate'),
                PhysicalQuantity('organic_carbon', 'TOC', 'wt%', (0.01, 20), 'Total organic carbon'),
            ],
            outputs=[
                PhysicalQuantity('sulfide_production_rate', 'R_MSR', 'mol/L/yr', (1e-12, 1e-3), 'Sulfide production rate'),
            ],
            validity_conditions=[
                ValidityCondition('oxygen', 'lt', 0.01, units='mM', explanation='Anoxic conditions required'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            causes=['pyritization', 'sulfur_isotope_fractionation', 'carbon_isotope_shift'],
            caused_by=['organic_matter_burial', 'anoxia'],
            observational_signatures=['d34S_pyrite excursion', 'pyrite framboids', 'sulfurised organic matter'],
            tracer_molecules=['d34S_pyrite', 'pyrite-S', 'acid-volatile sulfide'],
            keywords=['MSR', 'sulfate reduction', 'redox', 'anoxia', 'pyrite']
        )

        # Pyritization
        self.processes['pyritization'] = PhysicalProcess(
            process_id='pyritization',
            name='Pyritization',
            category=ProcessCategory.CHEMICAL,
            subcategory='mineral_precipitation',
            description='Formation of pyrite (FeS2) from reactive iron and biogenic sulfide during early diagenesis',
            equation=ProcessEquation(
                equation=r'\mathrm{Fe^{2+}} + \mathrm{H_2S} \rightarrow \mathrm{FeS} \xrightarrow{S^0} \mathrm{FeS_2}',
                python_form='k_pyr * Fe_HR * H2S',
                dependencies=['reactive_iron', 'sulfide_concentration'],
                output='pyrite_flux'
            ),
            inputs=[
                PhysicalQuantity('reactive_iron', 'Fe_HR', 'wt%', (0.01, 5), 'Highly reactive iron'),
                PhysicalQuantity('sulfide_concentration', 'H2S', 'uM', (0.1, 10000), 'Porewater sulfide'),
            ],
            outputs=[
                PhysicalQuantity('pyrite_flux', 'F_pyr', 'mol/m^2/yr', (1e-6, 1), 'Pyrite burial flux'),
                PhysicalQuantity('fe_pyrite_ratio', 'FeHR/FeT', '', (0.0, 1.0), 'Reactive iron partitioning to pyrite'),
            ],
            validity_conditions=[
                ValidityCondition('sulfide_concentration', 'gt', 1.0, units='uM', explanation='Euxinic to sulfidic'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            causes=['pyrite_burial', 'iron_speciation_signal', 'sulfur_isotope_record'],
            caused_by=['microbial_sulfate_reduction', 'iron_reduction'],
            observational_signatures=['FeHR/FeT > 0.38', 'FePy/FeHR', 'pyrite framboids'],
            tracer_molecules=['d34S_pyrite', 'Fe/Al', 'DOP'],
            keywords=['pyrite', 'iron speciation', 'euxinia', 'redox proxy', 'diagenesis']
        )

        # Carbonate precipitation / dissolution
        self.processes['carbonate_precipitation'] = PhysicalProcess(
            process_id='carbonate_precipitation',
            name='Carbonate Precipitation and Dissolution',
            category=ProcessCategory.CHEMICAL,
            subcategory='mineral_reaction',
            description='Precipitation or dissolution of calcium carbonate controlled by saturation state, alkalinity, and pCO2',
            equation=ProcessEquation(
                equation=r'\Omega = \frac{[\mathrm{Ca^{2+}}][\mathrm{CO_3^{2-}}]}{K_{sp}}',
                python_form='[Ca2+] * [CO3--] / K_sp',
                dependencies=['calcium_ion', 'carbonate_ion', 'solubility_product'],
                output='saturation_state'
            ),
            inputs=[
                PhysicalQuantity('alkalinity', 'TA', 'meq/L', (0.1, 20), 'Total alkalinity'),
                PhysicalQuantity('pCO2', 'pCO2', 'ppmv', (10, 1e6), 'Partial pressure CO2'),
            ],
            outputs=[
                PhysicalQuantity('saturation_state', 'Omega', '', (0.01, 100), 'Calcite saturation state'),
                PhysicalQuantity('precipitation_rate', 'R_carb', 'mol/m^2/yr', (1e-5, 1e2), 'Carbonate precipitation rate'),
            ],
            validity_conditions=[
                ValidityCondition('Omega', 'gt', 1.0, explanation='Supersaturated for precipitation'),
            ],
            timescale=ProcessTimescale.SLOW,
            causes=['carbonate_burial', 'carbon_isotope_record', 'c_isotope_fractionation'],
            caused_by=['alkalinity_input', 'CO2_drawdown', 'evaporation'],
            observational_signatures=['d13C_carb', 'carbonate platform', 'stromatolite laminae'],
            tracer_molecules=['d13C_carb', 'd18O_carb', '87Sr/86Sr_carb'],
            keywords=['carbonate', 'precipitation', 'alkalinity', 'carbon cycle', 'stromatolite']
        )

    def _add_magnetic_processes(self):
        """Add paleomagnetic processes."""

        # Detrital remanent magnetization
        self.processes['detrital_remanent_magnetization'] = PhysicalProcess(
            process_id='detrital_remanent_magnetization',
            name='Detrital Remanent Magnetization (DRM)',
            category=ProcessCategory.MAGNETIC,
            subcategory='acquisition',
            description='Alignment of detrital magnetic grains with the ambient geomagnetic field during sediment deposition',
            equation=ProcessEquation(
                equation=r'\mathrm{DRM} = \chi \cdot B_{Earth} \cdot f_{align}',
                python_form='chi * B_Earth * f_align',
                dependencies=['magnetic_susceptibility', 'field_strength', 'alignment_efficiency'],
                output='remanent_magnetization'
            ),
            inputs=[
                PhysicalQuantity('magnetic_susceptibility', 'chi', 'm^3/kg', (1e-8, 1e-3), 'Magnetic susceptibility'),
                PhysicalQuantity('field_strength', 'B_E', 'uT', (1, 100), 'Geomagnetic field intensity'),
            ],
            outputs=[
                PhysicalQuantity('remanent_magnetization', 'DRM', 'A/m', (1e-5, 1), 'Detrital remanent magnetization'),
            ],
            validity_conditions=[
                ValidityCondition('grain_size', 'lt', 0.063, units='mm', explanation='Fine-grained for stable DRM'),
            ],
            timescale=ProcessTimescale.FAST,
            causes=['paleomagnetic_record', 'magnetic_stratigraphy'],
            caused_by=['sediment_deposition', 'magnetic_grain_supply'],
            observational_signatures=['NRM direction', 'paleopole position', 'magnetic polarity'],
            tracer_molecules=['magnetite', 'hematite', 'titano-magnetite'],
            keywords=['DRM', 'paleomagnetism', 'sediment', 'magnetic polarity']
        )

        # Chemical remanent magnetization
        self.processes['chemical_remanent_magnetization'] = PhysicalProcess(
            process_id='chemical_remanent_magnetization',
            name='Chemical Remanent Magnetization (CRM)',
            category=ProcessCategory.MAGNETIC,
            subcategory='acquisition',
            description='Magnetisation acquired when authigenic magnetic minerals grow through the critical blocking volume in a magnetic field',
            equation=ProcessEquation(
                equation=r'\mathrm{CRM} = M_s \cdot f_{growth} \cdot B_{Earth}',
                python_form='M_sat * f_growth * B_Earth',
                dependencies=['saturation_magnetisation', 'growth_fraction', 'field_strength'],
                output='remanent_magnetization'
            ),
            inputs=[
                PhysicalQuantity('saturation_magnetisation', 'M_s', 'A/m', (0.1, 500), 'Saturation magnetisation of authigenic phase'),
                PhysicalQuantity('field_strength', 'B_E', 'uT', (1, 100), 'Geomagnetic field intensity'),
            ],
            outputs=[
                PhysicalQuantity('remanent_magnetization', 'CRM', 'A/m', (1e-4, 10), 'Chemical remanent magnetization'),
            ],
            validity_conditions=[
                ValidityCondition('grain_diameter', 'between', 0.02, value_max=0.1, units='um', explanation='Single-domain blocking range'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            causes=['paleomagnetic_overprint', 'magnetic_mineral_authigenesis'],
            caused_by=['diagenesis', 'oxidation_front', 'fluid_flow'],
            observational_signatures=['CRM overprint', 'authigenic magnetite', 'goethite-hematite conversion'],
            tracer_molecules=['magnetite', 'hematite', 'goethite', 'pyrrhotite'],
            keywords=['CRM', 'paleomagnetism', 'authigenic', 'diagenesis', 'overprint']
        )

    def _add_gravitational_processes(self):
        """Add basin subsidence and sediment settling processes."""

        # Basin subsidence
        self.processes['basin_subsidence'] = PhysicalProcess(
            process_id='basin_subsidence',
            name='Basin Subsidence',
            category=ProcessCategory.GRAVITATIONAL,
            subcategory='tectonic',
            description='Downward motion of the basement driven by tectonic, thermal, and sediment-loading components',
            equation=ProcessEquation(
                equation=r'S(t) = S_{tect} + S_{thermal} + S_{load}',
                python_form='S_tect + S_thermal + S_load',
                dependencies=['tectonic_subsidence', 'thermal_subsidence', 'sediment_load'],
                output='total_subsidence'
            ),
            inputs=[
                PhysicalQuantity('tectonic_subsidence', 'S_tect', 'm', (10, 10000), 'Tectonically driven subsidence'),
                PhysicalQuantity('thermal_subsidence', 'S_therm', 'm', (10, 5000), 'Post-rift thermal subsidence'),
            ],
            outputs=[
                PhysicalQuantity('total_subsidence', 'S', 'm', (50, 15000), 'Total subsidence'),
                PhysicalQuantity('accommodation_space', 'V_accom', 'km^3', (1, 1e6), 'Accommodation volume'),
            ],
            timescale=ProcessTimescale.VERY_SLOW,
            causes=['sediment_accommodation', 'burial_depth_increase'],
            caused_by=['rifting', 'lithospheric_cooling', 'flexural_loading'],
            observational_signatures=['stratigraphic thickening', 'onlap/offlap', 'unconformities'],
            keywords=['subsidence', 'basin', 'accommodation', 'tectonics']
        )

        # Sediment settling and deposition
        self.processes['sediment_settling'] = PhysicalProcess(
            process_id='sediment_settling',
            name='Sediment Settling and Deposition',
            category=ProcessCategory.GRAVITATIONAL,
            subcategory='deposition',
            description='Gravitational settling of sediment particles through the water column to the basin floor',
            equation=ProcessEquation(
                equation=r'v_s = \frac{(\rho_s - \rho_w) \, g \, d^2}{18 \mu}',
                python_form='(rho_s - rho_w) * g * d**2 / (18 * mu)',
                dependencies=['grain_diameter', 'grain_density', 'fluid_viscosity'],
                output='settling_velocity'
            ),
            inputs=[
                PhysicalQuantity('grain_diameter', 'd', 'mm', (1e-5, 2), 'Particle diameter (Stokes regime)'),
                PhysicalQuantity('grain_density', 'rho_s', 'kg/m^3', (1500, 4500), 'Sediment grain density'),
            ],
            outputs=[
                PhysicalQuantity('settling_velocity', 'v_s', 'm/s', (1e-8, 0.5), 'Stokes settling velocity'),
                PhysicalQuantity('deposition_rate', 'R_dep', 'm/Myr', (1, 1e4), 'Accumulation rate'),
            ],
            validity_conditions=[
                ValidityCondition('Reynolds_number', 'lt', 1.0, explanation='Stokes (laminar) regime'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            causes=['sediment_accumulation', 'graded_bedding', 'sorting'],
            caused_by=['basin_subsidence', 'sediment_supply', 'sea_level_change'],
            observational_signatures=['fining-upward sequences', 'laminated sediments', 'bed thickness trends'],
            keywords=['settling', 'Stokes', 'deposition', 'sorting', 'graded bedding']
        )

    def get_process(self, process_id: str) -> Optional[PhysicalProcess]:
        """Get process by ID."""
        return self.processes.get(process_id)

    def search_by_category(self, category: ProcessCategory) -> List[PhysicalProcess]:
        """Find all processes in a category."""
        return [p for p in self.processes.values() if p.category == category]

    def search_by_keyword(self, keyword: str) -> List[PhysicalProcess]:
        """Find processes matching a keyword."""
        keyword_lower = keyword.lower()
        results = []
        for p in self.processes.values():
            if any(keyword_lower in kw.lower() for kw in p.keywords):
                results.append(p)
            elif keyword_lower in p.name.lower():
                results.append(p)
            elif keyword_lower in p.description.lower():
                results.append(p)
        return results

    def search_by_observable(self, observable: str) -> List[PhysicalProcess]:
        """Find processes that produce an observable."""
        obs_lower = observable.lower()
        return [p for p in self.processes.values()
                if any(obs_lower in sig.lower() for sig in p.observational_signatures)]

    def search_by_tracer(self, tracer: str) -> List[PhysicalProcess]:
        """Find processes traced by a molecule."""
        return [p for p in self.processes.values()
                if any(tracer.upper() in t.upper() for t in p.tracer_molecules)]

    def get_causes(self, process_id: str) -> List[PhysicalProcess]:
        """Get processes caused by this process."""
        process = self.get_process(process_id)
        if process is None:
            return []
        return [self.processes[pid] for pid in process.causes if pid in self.processes]

    def get_caused_by(self, process_id: str) -> List[PhysicalProcess]:
        """Get processes that cause this process."""
        process = self.get_process(process_id)
        if process is None:
            return []
        return [self.processes[pid] for pid in process.caused_by if pid in self.processes]


class MechanismMatcher:
    """
    Match observations to physical mechanisms.
    """

    def __init__(self, library: ProcessLibrary):
        """Initialize mechanism matcher."""
        self.library = library

    def match_observables(self, observables: List[str]) -> List[PhysicalProcess]:
        """
        Find processes that explain a set of observables.

        Args:
            observables: List of observed features

        Returns:
            Matching processes ranked by relevance
        """
        scores: Dict[str, int] = {}

        for obs in observables:
            matches = self.library.search_by_observable(obs)
            for proc in matches:
                scores[proc.process_id] = scores.get(proc.process_id, 0) + 1

        # Sort by score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [self.library.get_process(pid) for pid in sorted_ids if self.library.get_process(pid)]


class ProcessChainBuilder:
    """
    Build causal chains of physical processes.
    """

    def __init__(self, library: ProcessLibrary):
        """Initialize chain builder."""
        self.library = library

    def find_chain(self, start: str, end: str,
                   max_length: int = 5) -> List[List[str]]:
        """
        Find causal chains connecting two processes.

        Args:
            start: Starting process ID
            end: Target process ID
            max_length: Maximum chain length

        Returns:
            List of process ID chains
        """
        if start not in self.library.processes or end not in self.library.processes:
            return []

        chains = []
        self._dfs(start, end, [start], chains, max_length)
        return chains

    def _dfs(self, current: str, target: str, path: List[str],
             chains: List[List[str]], max_length: int):
        """Depth-first search for chains."""
        if len(path) > max_length:
            return

        if current == target:
            chains.append(list(path))
            return

        process = self.library.get_process(current)
        if process is None:
            return

        for next_id in process.causes:
            if next_id not in path:  # Avoid cycles
                path.append(next_id)
                self._dfs(next_id, target, path, chains, max_length)
                path.pop()

    def explain_observation_chain(self, observation: str,
                                  initial_condition: str) -> List[str]:
        """
        Build explanation chain from initial condition to observation.

        Args:
            observation: Observed feature
            initial_condition: Initial physical state

        Returns:
            List of process IDs forming the explanation
        """
        # Find processes that produce the observation
        end_processes = self.library.search_by_observable(observation)
        if not end_processes:
            return []

        # Find processes matching initial condition
        start_processes = self.library.search_by_keyword(initial_condition)
        if not start_processes:
            return []

        # Find shortest chain
        best_chain = None
        for start in start_processes:
            for end in end_processes:
                chains = self.find_chain(start.process_id, end.process_id)
                for chain in chains:
                    if best_chain is None or len(chain) < len(best_chain):
                        best_chain = chain

        return best_chain if best_chain else []


# Singleton instance
_process_library: Optional[ProcessLibrary] = None


def get_process_library() -> ProcessLibrary:
    """Get singleton process library."""
    global _process_library
    if _process_library is None:
        _process_library = ProcessLibrary()
    return _process_library


def get_mechanism_matcher() -> MechanismMatcher:
    """Get mechanism matcher."""
    return MechanismMatcher(get_process_library())


def get_chain_builder() -> ProcessChainBuilder:
    """Get chain builder."""
    return ProcessChainBuilder(get_process_library())


# Convenience functions

def find_process(keyword: str) -> List[PhysicalProcess]:
    """Search for processes by keyword."""
    return get_process_library().search_by_keyword(keyword)


def explain_observable(observable: str) -> List[PhysicalProcess]:
    """Find processes that can explain an observable."""
    return get_process_library().search_by_observable(observable)


def get_process_chain(start: str, end: str) -> List[List[str]]:
    """Find causal chains between processes."""
    return get_chain_builder().find_chain(start, end)
