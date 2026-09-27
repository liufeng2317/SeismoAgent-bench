# Seismic Operations

> **Relevant source files**
> * [gamma/seismic_ops.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py)

## Purpose and Scope

The `gamma.seismic_ops` module provides low-level seismological computations essential for earthquake event association and location. This module handles travel time calculations, event location optimization, magnitude estimation, and implements an eikonal solver for heterogeneous velocity models.

For the high-level association workflow that uses these operations, see [Core Association Functions](/AI4EPS/GaMMA/4.1-core-association-functions). For the statistical mixture model components that rely on these calculations, see [Mixture Model Classes](/AI4EPS/GaMMA/4.3-mixture-model-classes).

## System Architecture

The seismic operations module serves as the computational backbone for physical seismological calculations within GaMMA:

```mermaid
flowchart TD

A["event_loc<br>(x, y, z, t)"]
B["station_loc<br>(x, y, z)"]
C["phase_type<br>['p', 's']"]
D["phase_time<br>observations"]
E["vel<br>velocity_model"]
F["calc_time()<br>Travel Time"]
G["calc_loc()<br>Event Location"]
H["calc_mag()<br>Magnitude"]
I["calc_amp()<br>Amplitude"]
J["initialize_eikonal()<br>Setup"]
K["eikonal_solve()<br>Solver"]
L["traveltime()<br>Lookup"]
M["grad_traveltime()<br>Gradients"]
N["huber_loss_grad()<br>Loss Function"]
O["scipy.optimize<br>L-BFGS-B"]
P["newton_method()<br>Alternative"]

A --> F
B --> F
C --> F
E --> F
F --> L
D --> G
G --> N
A --> H
B --> H

subgraph Optimization ["Location Optimization"]
    N
    O
    P
    N --> O
end

subgraph Eikonal_System ["Eikonal Solver"]
    J
    K
    L
    M
    J --> K
    K --> L
    L --> M
end

subgraph Core_Functions ["Core Functions"]
    F
    G
    H
    I
    F --> G
    H --> I
end

subgraph Input_Data ["Input Data"]
    A
    B
    C
    D
    E
end
```

Sources: [gamma/seismic_ops.py L1-L486](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L1-L486)

## Travel Time Calculation

The module provides two approaches for calculating seismic travel times between event locations and stations:

### Simple Velocity Model

For homogeneous or simple layered models, travel times are calculated using direct distance and constant velocities:

```mermaid
flowchart TD

A["event_loc[:, :-1]<br>spatial_coordinates"]
B["np.linalg.norm()<br>euclidean_distance"]
C["vel={'p': 6.0, 's': 3.43}<br>velocity_dict"]
D["distance / velocity<br>travel_time"]
E["event_loc[:, -1:]<br>origin_time"]
F["travel_time + origin_time<br>arrival_time"]
G["v = np.array([vel[x] for x in phase_type])"]
H["tt = np.linalg.norm(ev_loc - station_loc) / v + ev_t"]

A --> G
C --> G

subgraph Implementation ["Code Implementation"]
    G
    H
    G --> H
end

subgraph calc_time_simple ["Simple Model (calc_time)"]
    A
    B
    C
    D
    E
    F
    A --> B
    C --> D
    B --> D
    E --> F
    D --> F
end
```

Sources: [gamma/seismic_ops.py L208-L218](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L208-L218)

### Eikonal-Based Travel Times

For complex 3D velocity structures, the module uses pre-computed travel time tables from an eikonal solver:

| Component | Function | Purpose |
| --- | --- | --- |
| **Solver Setup** | `initialize_eikonal()` | Creates 2D travel time grids for P and S waves |
| **Table Lookup** | `traveltime()` | Bilinear interpolation from pre-computed tables |
| **Gradient Calculation** | `grad_traveltime()` | Computes gradients for optimization |
| **Internal Interpolation** | `_interp()` | Numba-optimized bilinear interpolation |

Sources: [gamma/seismic_ops.py L154-L203](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L154-L203)

 [gamma/seismic_ops.py L315-L392](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L315-L392)

## Event Location Algorithm

The `calc_loc()` function implements robust event location using Huber loss optimization:

```mermaid
flowchart TD

A["phase_time<br>observed_arrivals"]
B["huber_loss_grad()<br>objective_function"]
C["station_loc<br>station_positions"]
D["event_loc0<br>initial_guess"]
E["phase_type<br>P_or_S_phases"]
F["scipy.optimize.minimize<br>L-BFGS-B"]
G["opt.x<br>optimized_location"]
H["opt.fun<br>final_loss"]
I["t_diff = predict_time - phase_time<br>residuals"]
J["abs(t_diff) > sigma<br>outlier_check"]
K["sigma * abs(t_diff) - 0.5 * sigma²<br>linear_loss"]
L["0.5 * t_diff²<br>quadratic_loss"]
M["weighted_sum<br>total_loss"]

B --> I

subgraph Loss_Function ["Huber Loss Details"]
    I
    J
    K
    L
    M
    J --> K
    J --> L
    K --> M
    L --> M
    I --> J
end

subgraph Location_Process ["Event Location Process"]
    A
    B
    C
    D
    E
    F
    G
    H
    A --> B
    C --> B
    D --> B
    E --> B
    B --> F
    F --> G
    F --> H
end
```

Sources: [gamma/seismic_ops.py L290-L313](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L290-L313)

 [gamma/seismic_ops.py L257-L287](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L257-L287)

## Magnitude Estimation

The module implements multiple magnitude scaling relationships for different seismological contexts:

### Primary Implementation (Picozzi et al., 2018)

The default magnitude calculation uses rapid response scaling:

```python
# Coefficients from Picozzi et al. (2018)
c0, c1, c2, c3 = 1.08, 0.93, -0.015, -1.68
mag_ = (data - c0 - c3 * np.log10(np.maximum(dist, 0.1))) / c1 + 3.5
```

### Robust Magnitude Calculation

The `calc_mag()` function includes outlier rejection:

```mermaid
flowchart TD

A["amplitude_data<br>log_amplitudes"]
B["mag_ = scaling_relation(data, dist)<br>individual_estimates"]
C["distance<br>hypocentral_distance"]
D["weight<br>pick_weights"]
E["mu = weighted_mean(mag_)<br>initial_estimate"]
F["std = weighted_std(mag_)<br>scatter_estimate"]
G["mask = abs(mag_ - mu) <= 2*std<br>outlier_rejection"]
H["final_mag = weighted_mean(mag_[mask])<br>robust_estimate"]
I["np.clip(mag, min=-2, max=8)<br>bounded_result"]

A --> B
C --> B
D --> B
B --> E
E --> F
F --> G
G --> H
H --> I
```

Sources: [gamma/seismic_ops.py L220-L237](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L220-L237)

 [gamma/seismic_ops.py L240-L252](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L240-L252)

## Eikonal Solver Implementation

The eikonal solver computes travel times in heterogeneous media by solving |∇u| = f, where u is travel time and f is slowness:

### Core Algorithm Components

| Function | Purpose | Implementation |
| --- | --- | --- |
| `sweeping()` | Fast sweeping method | Four-directional sweep pattern |
| `calculate_unique_solution()` | Local solver | Quadratic formula for travel time update |
| `sweeping_over_I_J_K()` | Grid traversal | Numba-optimized nested loops |
| `eikonal_solve()` | Main solver | Iterative convergence with error checking |

### Solver Workflow

```mermaid
flowchart TD

A["velocity_model<br>3D_or_layered"]
B["rgrid, zgrid<br>cylindrical_coordinates"]
C["config_bounds<br>xlim_ylim_zlim"]
D["u = 1000 * ones(nr, nz)<br>initialization"]
E["u[source] = 0<br>boundary_condition"]
F["sweeping(u, v, h)<br>four_directions"]
G["err < 1e-6<br>convergence_check"]
H["up, us<br>P_and_S_tables"]
I["grad_up, grad_us<br>gradient_tables"]
J["flattened_arrays<br>lookup_format"]

B --> D
G --> H

subgraph Output ["Result Processing"]
    H
    I
    J
    H --> I
    I --> J
end

subgraph Solver_Core ["Fast Sweeping"]
    D
    E
    F
    G
    D --> E
    E --> F
    F --> G
    G --> F
end

subgraph Setup ["Grid Setup"]
    A
    B
    C
    A --> B
    C --> B
end
```

Sources: [gamma/seismic_ops.py L77-L89](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L77-L89)

 [gamma/seismic_ops.py L54-L74](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L54-L74)

 [gamma/seismic_ops.py L15-L21](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L15-L21)

## Integration with Mixture Models

The seismic operations integrate with GaMMA's mixture models through the `initialize_centers()` function:

```mermaid
flowchart TD

A["centers_init<br>initial_event_locations"]
B["means = calc_time()<br>predicted_arrivals"]
C["station_locs<br>receiver_positions"]
D["phase_type<br>P_S_labels"]
E["dist = norm(means - X)<br>residual_calculation"]
F["X<br>observed_data"]
G["resp = exp(-dist²/2σ²)<br>responsibility_weights"]
H["resp = resp / sum(resp)<br>normalization"]
I["n_features<br>data_dimensions"]
J["time_only<br>calc_time()"]
K["time_amp<br>calc_time() + calc_mag()"]
L["updated_centers"]

H --> L

subgraph Feature_Handling ["Multi-Feature Support"]
    I
    J
    K
    L
    I --> J
    I --> K
    J --> L
    K --> L
end

subgraph Initialization_Process ["Center Initialization"]
    A
    B
    C
    D
    E
    F
    G
    H
    A --> B
    C --> B
    D --> B
    B --> E
    F --> E
    E --> G
    G --> H
end
```

Sources: [gamma/seismic_ops.py L394-L438](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L394-L438)

## Performance Optimization

The module uses several optimization strategies:

* **Numba JIT compilation** for eikonal solver inner loops: `@njit` decorators on performance-critical functions
* **Vectorized operations** with NumPy for batch processing of multiple events/stations
* **Scipy optimization** with L-BFGS-B for robust gradient-based event location
* **Pre-computed lookup tables** for complex velocity models to avoid repeated eikonal solving

Sources: [gamma/seismic_ops.py L15](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L15-L15)

 [gamma/seismic_ops.py L93](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L93-L93)

 [gamma/seismic_ops.py L117](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L117-L117)

 [gamma/seismic_ops.py L302-L312](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py#L302-L312)