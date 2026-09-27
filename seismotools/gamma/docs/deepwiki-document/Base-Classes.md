# Base Classes

> **Relevant source files**
> * [docs/assets/diagram_gamma_annotated.png](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/assets/diagram_gamma_annotated.png)
> * [gamma/_base.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py)

This page documents the foundational `BaseMixture` class that provides the core EM (Expectation-Maximization) algorithm implementation for all mixture models in GaMMA. This abstract base class defines the interface and common functionality shared by the Gaussian mixture model variants.

For information about the specific mixture model implementations that inherit from this base class, see [Mixture Model Classes](/AI4EPS/GaMMA/4.3-mixture-model-classes).

## BaseMixture Class Architecture

The `BaseMixture` class serves as the abstract foundation for all mixture models in GaMMA, providing a standardized interface and common EM algorithm implementation. It inherits from scikit-learn's `BaseEstimator` and `DensityMixin` to ensure compatibility with the scikit-learn ecosystem.

```mermaid
classDiagram
    class BaseEstimator {
        «sklearn»
    }
    class DensityMixin {
        «sklearn»
    }
    class BaseMixture {
        «abstract»
        +n_components: int
        +tol: float
        +reg_covar: float
        +max_iter: int
        +n_init: int
        +init_params: str
        +random_state: RandomState
        +warm_start: bool
        +verbose: int
        +fit(X, y=None)
        +fit_predict(X, y=None)
        +predict(X)
        +predict_proba(X)
        +score(X, y=None)
        +score_samples(X)
        +sample(n_samples=1)
        +_e_step(X)
        +_m_step(X, log_resp)
        +_check_parameters(X)
        +_initialize(X, resp)
        +_estimate_log_prob(X)
        +_estimate_log_weights()
        +_get_parameters()
        +_set_parameters(params)
    }
    class GaussianMixture {
        +covariance_type: str
        +station_locs: array
        +vel: dict
        +phase_type: array
        +phase_weight: array
    }
    class BayesianGaussianMixture {
        +weight_concentration_prior: float
        +mean_precision_prior: float
        +covariance_prior: array
        +degrees_of_freedom_prior: float
    }
    BaseEstimator <|-- BaseMixture
    DensityMixin <|-- BaseMixture
    BaseMixture <|-- GaussianMixture
    BaseMixture <|-- BayesianGaussianMixture
```

**Sources:** [gamma/_base.py L40-L84](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L40-L84)

## EM Algorithm Implementation

The `BaseMixture` class implements the complete EM algorithm workflow, managing multiple initializations and convergence checking. The algorithm alternates between expectation and maximization steps until convergence or maximum iterations are reached.

```mermaid
flowchart TD

A["fit_predict(X)"]
B["validate_data(X)"]
C["_check_parameters(X)"]
D["warm_start enabled?"]
E["n_init iterations"]
F["Single iteration"]
G["_initialize_parameters(X, random_state)"]
H["EM Loop: max_iter iterations"]
I["_e_step(X)"]
J["_m_step(X, log_resp)"]
K["_compute_lower_bound(log_resp, log_prob_norm)"]
L["abs(change) < tol?"]
M["converged = True"]
N["Store best parameters"]
O["_set_parameters(best_params)"]
P["Final _e_step(X)"]
Q["Return component labels"]

A --> B
B --> C
C --> D
D --> E
D --> F
E --> G
F --> G
G --> H
H --> I
I --> J
J --> K
K --> L
L --> I
L --> M
M --> N
N --> O
O --> P
P --> Q
```

The EM algorithm tracks the lower bound of the log-likelihood at each iteration and selects the best performing initialization run. The process includes comprehensive logging and convergence monitoring.

**Sources:** [gamma/_base.py L189-L300](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L189-L300)

## Parameter Initialization Strategies

The `BaseMixture` class supports multiple initialization strategies for mixture model parameters, including seismic-specific initialization methods that leverage domain knowledge about travel times and station locations.

| Initialization Method | Description | Use Case |
| --- | --- | --- |
| `"kmeans"` | K-means clustering on time-space features | General purpose, fast initialization |
| `"random"` | Random uniform responsibilities | Exploration of parameter space |
| `"random_from_data"` | Random selection from data points | Data-driven initialization |
| `"k-means++"` | K-means++ algorithm | Improved cluster center selection |
| `"centers"` | Seismic-specific center initialization | Domain-specific initialization using travel times |

```mermaid
flowchart TD

A["_initialize_parameters(X, random_state)"]
B["Create feature matrix X_"]
C["X_ = [time, station_xy/vp]"]
D["init_params value?"]
E["KMeans clustering on X_"]
F["Random uniform responsibilities"]
G["Random data point selection"]
H["kmeans_plusplus on X_"]
I["initialize_centers from seismic_ops"]
J["_initialize(X, resp)"]
K["Set centers_init attribute"]

A --> B
B --> C
C --> D
D --> E
D --> F
D --> G
D --> H
D --> I
E --> J
F --> J
G --> J
H --> J
I --> K
K --> J
```

The seismic-specific `"centers"` initialization method calls `initialize_centers` from the `seismic_ops` module, which uses travel time calculations and station geometry to provide physically meaningful initial cluster centers.

**Sources:** [gamma/_base.py L98-L146](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L98-L146)

 [gamma/_base.py L19](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L19-L19)

## Abstract Methods Interface

The `BaseMixture` class defines several abstract methods that must be implemented by concrete subclasses. This interface ensures consistent behavior across different mixture model variants while allowing for specialized implementations.

```mermaid
classDiagram
    note "Abstract methods marked with *must be implemented by subclasses"
    class BaseMixture {
        «abstract»
        +_check_parameters(X) : "Validate subclass parameters"
        +_initialize(X, resp) : "Initialize model parameters"
        +_m_step(X, log_resp) : "Maximization step"
        +_get_parameters() : "Get current parameters"
        +_set_parameters(params) : "Set model parameters"
        +_estimate_log_weights() : "Calculate log weights"
        +_estimate_log_prob(X) : "Calculate log probabilities"
        +_compute_lower_bound(log_resp, log_prob_norm) : "Calculate lower bound"
    }
```

These abstract methods provide clear extension points for different mixture model types:

* **Parameter Management**: `_get_parameters()`, `_set_parameters()`, `_check_parameters()`
* **EM Algorithm Steps**: `_initialize()`, `_m_step()`, `_compute_lower_bound()`
* **Probability Estimation**: `_estimate_log_weights()`, `_estimate_log_prob()`

**Sources:** [gamma/_base.py L88-L96](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L88-L96)

 [gamma/_base.py L147-L157](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L147-L157)

 [gamma/_base.py L321-L333](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L321-L333)

 [gamma/_base.py L335-L341](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L335-L341)

 [gamma/_base.py L484-L508](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L484-L508)

## Parameter Validation and Constraints

The `BaseMixture` class includes comprehensive parameter validation using scikit-learn's constraint system. This ensures that all parameters are within valid ranges and of appropriate types before fitting begins.

| Parameter | Constraint | Description |
| --- | --- | --- |
| `n_components` | `Interval(Integral, 1, None)` | Number of mixture components ≥ 1 |
| `tol` | `Interval(Real, 0.0, None)` | Convergence tolerance ≥ 0 |
| `reg_covar` | `Interval(Real, 0.0, None)` | Covariance regularization ≥ 0 |
| `max_iter` | `Interval(Integral, 0, None)` | Maximum iterations ≥ 0 |
| `n_init` | `Interval(Integral, 1, None)` | Number of initializations ≥ 1 |
| `init_params` | `StrOptions({"kmeans", "random", ...})` | Initialization strategy |
| `verbose_interval` | `Interval(Integral, 1, None)` | Verbose output interval ≥ 1 |

The validation system automatically checks these constraints during the `@_fit_context` decorator execution, providing clear error messages for invalid parameter combinations.

**Sources:** [gamma/_base.py L47-L58](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L47-L58)

 [gamma/_base.py L217-L224](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L217-L224)

## Utility Methods and Functionality

The `BaseMixture` class provides several utility methods for model evaluation, sampling, and debugging:

### Model Evaluation Methods

```mermaid
flowchart TD

A["score_samples(X)"]
B["_estimate_weighted_log_prob(X)"]
C["logsumexp(weighted_log_prob, axis=1)"]
D["score(X, y=None)"]
E["Return per-sample log-likelihood"]
F["Return mean log-likelihood"]
G["predict(X)"]
H["argmax(weighted_log_prob, axis=1)"]
I["Return component labels"]
J["predict_proba(X)"]
K["_estimate_log_prob_resp(X)"]
L["exp(log_resp)"]
M["Return component probabilities"]

A --> B
B --> C
D --> A
A --> E
D --> F
G --> B
B --> H
H --> I
J --> K
K --> L
L --> M
```

### Sample Generation

The `sample()` method generates synthetic data points from the fitted mixture model, useful for model validation and data augmentation. It uses multinomial sampling to determine component membership and then generates samples from the appropriate component distributions.

**Sources:** [gamma/_base.py L343-L379](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L343-L379)

 [gamma/_base.py L381-L417](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L381-L417)

 [gamma/_base.py L418-L469](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py#L418-L469)