# NLLoc - Non-linear, earthquake location program

**NLLoc** performs earthquake locations in 3D models using non-linear
search techniques.

[Overview](#overview) - [Inversion Approach](#inversion-approach) -
[EDT Likelihood Function](#edt-likelihood-function) - [Oct-Tree Sampling](#oct-tree-sampling) - [Grid-Search](#grid-search) -
[Metropolis-Gibbs Sampling](#metropolis-gibbs-sampling) - [Running the Program - Input](#running-the-program---input) - [Output](#output) - [Processing and Display of Results](#processing-and-display-of-results) - [NonLinLoc Home](../index.md)

## Overview

The NLLoc program produces a **misfit function**, **"optimal"
hypocenters**, an estimate of the **posterior probability density
function** (PDF) for the spatial, *x,y,z* hypocenter location, and other
results using either a systematic **Grid-Search** or a stochastic,
**Metropolis-Gibbs sampling** approach.

The location algorithm used in NLLoc [(Lomax, et al., 2000)](./references.html) follows the inversion approach of
[Tarantola and Valette (1982)](references.html), and the earthquake
location methods of [Tarantola and Valette (1982)](references.html),
[Moser, van Eck and Nolet (1992)](references.html) and
[Wittlinger](references.html) et al. (1993). The errors in the
observations (phase time picks) and in the forward problem (travel-time
calculation) are assumed to be Gaussian. This assumption allows the
direct, analytic calculation of a maximum likelihood origin time given
the observed arrival times and the calculated travel times between the
observing stations and a point in xyz space. Thus the 4D problem of
hypocenter location reduces to a 3D search over *x,y,z* space.

To make the location program efficient for complicated, 3D models, the
travel-times between each station and all nodes of an *x,y,z* spatial
grid are calculated once using a 3D version ([Le Meur, 1994](references.html); [Le Meur, Virieux and Podvin, 1997](references.html)) of the Eikonal finite-difference scheme of
[Podvin and Lecomte (1991)](references.html) and then stored on disk
as travel-time grid files. This storage technique has been used by
[Wittlinger](references.html) et al. (1993), and in related
approaches by [Nelson and Vidale (1990)](references.html) and
[Shearer (1997)](references.html). The forward calculation during
location reduces to retrieving the travel-times from the grid files and
forming the misfit function *g* (**x**) in, equation (3).

In addition, to save disk space and for faster calculation, a constant
Vp/Vs ratio can be specified, and then only P travel-time grids are
required for each station.

The [Podvin and Lecomte (1991)](references.html) algorithm and
related methods use a finite-differences approximation of Huygen's
principle to find the first arriving, infinite frequency travel times at
all nodes of the grid. The algorithm of [Podvin and Lecomte (1991)](references.html) gives stable recovery of diffracted waves
near surfaces of strong velocity contrast and thus it accurately
produces travel times for diffracted and head waves. A limitation of the
current 3D version of the method is a restriction to cubic grids. This
may lead to excessively large travel-time grids if a relatively fine
cell spacing is required along one dimension since the same spacing must
be used for the other dimensions. This can be a problem for regional
studies where a fine node spacing in depth is necessary, but the
horizontal extent of the study volume can be much greater than the depth
extent. Thus a modification of the travel times calculation to allow use
of an irregular grid would be very useful.

After the travel times are calculated throughout the grid, the NonLinLoc
program uses the gradients of travel-time at the node to estimate the
take-off angles at each node. Two gradients are estimated for each axis
direction *x, y,* and *z* - one *G :sub:[low`* between the node and its preceding neighbour along the axis, and a second *G <sub>high</sub>* between the following neighbour and the node. The total gradient *G <sub>axis</sub>* along an axis is the mean of these two gradients; the total gradient along the three axes determines the vector gradient of travel-time. The direction opposite to the vector gradient of travel-time gives the ray take-off angles for ** dip and azimuth. An estimate of the quality of the angle determination is given by a comparison of the magnitudes and signs of *G <sub>low</sub>* and *G <sub>high</sub>*. If these two values are not similar, then there may be two rays which arrive nearly simultaneously at the station, and the take-off angle determination at the node may be unstable. The *x,y,z* volume used for grid-search or Metropolis-Gibbs location must be fully contained within the 3D travel-time grids. This limits the largest station distance that can be used for location since the 3D travel-time computation and the size of the output time-grid files grow rapidly with grid dimension. However, for location in flat-layered media, the travel times can be stored on very compact 2D grids, and readings for "regional" stations far from the search volume can be used. Except for TRANS GLOBAL mode, the NLLoc program uses a "flat earth", rectangular, left-handed, *x,y,z* coordinate system (positive X = East, positive Y = North, positive Z = down). Distance units are kilometers, and many input/output distance quantities can be expressed in rectangular or geographic (latitude and longitude) coordinates. In TRANS GLOBAL mode, the NLLoc program uses a "spherical earth", *longitude,latitude,depth* coordinate system (positive X = East, positive Y = North, positive Z = down). Longitude and latitude units are degrees, depth is in kilometers, and most input/output distance quantities are expressed in geographic (latitude and longitude) coordinates. See the book chapters **Probabilistic earthquake location in 3D and layered models: Introduction of a Metropolis-Gibbs method and comparison with linear locations [(Lomax,et al., 2000)](./references.html)** and **Earthquake Location, Direct, Global-Search Methods, in Complexity In Encyclopedia of Complexity and System Science `(Lomax, et al., 2009)](./references.html)** for further information on the NonLinLoc
location algorithms.

## Inversion Approach

The earthquake location algorithm implemented in the program NLLoc
[(Lomax, et al., 2000)](./references.html) follows the probabilistic
formulation of inversion presented in [Tarantola and Valette (1982)](references.html) and [Tarantola (1987)](references.html).
This formulation relies on the use of normalised and unnormalised
probability density functions to express our knowledge about the values
of parameters. Thus, given the normalised density function *f* (*x*)
for value of a parameter *x*, the probability that *x* has a value
between *X* and *X* +D *X* is

|image0|. (1)

In geophysical inversion we wish to constrain the values of a vector of
unknown parameters **p**, given a vector of observed data **d** and a
theoretical relationship q (**d**, **p**) relating **d** and **p**.
When the density functions giving the prior information on the model
parameters r :sub:[p` (**p**) and on the observations *r* **<sub>d</sub>** (**d**) are independent, and the theoretical relationship can be expressed as a conditional density function q (**d** \| **p**)m <sub>p</sub> (**p**), a complete, probabilistic solution can be expressed as a **posterior density function (PDF)** *s* <sub>p</sub> (**p**) (`Tarantola and Valette, 1982](references.html); [Tarantola, 1987](references.html))

|image1|, (2)

where m :sub:[p` (**p**) and m <sub>d</sub> (**d**) are null information density functions specifying the state of total ignorance. ### Gaussian Error Assumption - L2-RMS likelihood function For the case of earthquake location, the unknown parameters are the hypocentral coordinates x = (*x*, *y*, *z*) and the origin time *T*, the observed data is a set of arrival times t, and the theoretical relation gives predicted travel times h. `Tarantola and Valette (1982)](references.html) show that, if the theoretical relationship
and the observed arrival times are assumed to have gaussian
uncertainties with covariance matrices C *:sub:[T`* and C *<sub>t</sub>*, respectively, and if the prior information on *T* is taken as uniform, then it is possible to evaluate analytically the integral over d in (2) and an integral over origin time *T* to obtain the marginal PDF for the spatial location, *s* (**x**). This marginal PDF reduces to (`Tarantola and Valette, 1982](references.html); [Moser, van Eck and Nolet, 1992](references.html))

|image2| (3)

In this expression *K* is a normalisation factor, *r* (**x**) is a
density function of prior information on the model parameters, and
*g* (**x**) is an L2 misfit function.  |image3| is the vector of
observed arrival times **t** minus their weighted mean,  |image4| is
the vector of theoretical travel times **h** minus their weighted mean,
where the weights *w :sub:[i`* are given by |image5| (4) Furthermore, [Moser, van Eck and Nolet, 1992](references.html) show that the maximum likelihood origin time corresponding to a hypocentre at (*x*, *y*, *z*) is given by |image6| (5) The posterior density function (PDF) *s* (**x**) given by equation (3) represents a complete, probabilistic solution to the location problem, including information on uncertainty and resolution. This solution does not require a linearised theory, and the resulting PDF may be irregular and multi-modal because the forward calculation involves a non-linear relationship between hypocentre location and travel-times. This solution includes location uncertainties due to the spatial relation between the network and the event, measurement uncertainty in the observed arrival times, and errors in the calculation of theoretical travel times. However, realistic estimates of uncertainties in the observed and theoretical times must be available and specified in a gaussian form through **C** *<sub>t</sub>* and **C** *<sub>T</sub>*, respectively. Absolute location errors due to incorrect velocity structure could be included through **C** *<sub>T</sub>* if the resulting travel time errors can be estimated and described with a gaussian structure. Estimating these travel time errors is difficult and often not attempted. When the model used for location is a poor approximation to the "true" structure (as is often the case with layered model approximations), the absolute location uncertainties can be very large. ### Complete, Non-linear Location - PDF The NLLoc grid-search algotithm systematically determines the posterior probability density function *s* (**x**) or the "misfit" function *g* (**x**) over a 3D, *x,y,z* spacial grid. The NLLoc Metropolis-Gibbs sampling algorithm attempts to obtain a set of samples distributied according to the posterior probability density function *s* (**x**). The grid-search *s* (**x**) grid, samples drawn from this function, or the samples obtained by the Metropolis-Gibbs sampling, form the full, non-linear spatial solution to the earthquake location problem. This solution indicates the uncertainty in the spatial location due to picking errors, a simple estimate of travel-time calculation errors, the geometry of the observing stations and the incompatibility of the picks. The location uncertainty will in general be non-ellipsoidal (non-Gaussian) because the forward calculation involves a non-linear relationship between hypocenter location and travel-times. Because it is difficult or impossible to obtain, a more complete estimate of the travel-time errors (or, equivalently, a robust estimate of the errors in the velocity model) is not used. This is a serious limitation of this and most location algorithms, particularly for the study of absolute event locations. The PDF may be output to a [3D Grid](formats.html#_grid_) and a [binary Scatter file](formats.html#_location_scat_) (see [Output](#_output_) below). PDF values are also used for the determination of weighted average phase residuals (output to a `Phase Statistics](formats.html#_location_phsstat_) file), and for
calculating location confidence contour levels (see
[Output](#_output_) below), and "Traditional" Gaussian estimators
(see below).

### Maximum likelihood hypocentre

The maximum likelihood (or minimum misfit) point of the complete,
non-linear location PDF is selected as an "optimal" hypocentre. The
significance and uncertainty of this maximum likelihood hypocentre
cannot be assessed independently of the complete solution PDF. The
maximum likelihood hypocenter parameters are output to the NNLoc, ASCII
[Hypocenter-Phase File](formats.html#_location_hypphs_)
([`HYPOCENTER``, ``GEOGRAPHIC`` and ``QUALITY`` lines), and to the [quasi-HYPOELLIPSE format](formats.html#_location_qhypell_) and [HYPO71 format](formats.html#_location_hypo71_) files. The maximum likelihood hypocenter is also used for the determination of ray take-off angles (output to a `HypoInverse Archive](formats.html#_location_hypinv_) file), for the determination
of average phase residuals (output to a [Phase Statistics](formats.html#_location_phsstat_) file), and for magnitude
calculation. The ray take-off angles can be used for a first-motion
fault plane determination.

### Gaussian estimators

"Traditional" gaussian or normal estimators, such as the expectation
  *E* (**x**) and covariance matrix **C** may be obtained from the
  gridded values of the normalised location PDF or from samples of this
  function (e.g. [Tarantola and Valette, 1982](references.html); [Sen and Stoffa,1995](references.html)). For the grid case with nodes at
  **x** *:sub:[i,j,k`*, |image7|, (6) where D *V* *is the volume of a grid cell. For N samples drawn from the PDF with locations **x** <sub>n</sub>,* |image8|, (7) *where the PDF values* s( **x** *<sub>n</sub>*) are not required since the samples are assumed distributed according to the PDF. For both cases, the covariance matrix is then given by |image9|. (8) The Gaussian estimators are output to the NNLoc, ASCII `Hypocenter-Phase File](formats.html#_location_hypphs_) ([`STATISTICS`` line). ### Confidence Ellipsoid The 68% confidence ellipsoid can be obtained from singular value decomposition (SVD) of the covariance matrix **C**, following Press *et al*. (1992; their sec. 15.6 and eqs. 2.6.1 and 15.6.10). The SVD gives: |image10|, (9) where **U** = **V** are square, symmetric matrices and *w <sub>i</sub>* are singular values. The columns **V** *<sub>i</sub>* of **V** give the principle axes of the confidence ellipsoid. The corresponding semi-diameters for a 68% confidence ellipsoid are Ö (3.53*w <sub>i</sub>*), where 3.53 is the Dc <sup>2</sup> value for 68.3% confidence and 3 degrees of freedom. The gaussian estimators and resulting confidence ellipsoid will be good indicators of the uncertainties in the location only in the case where the complete, non-linear PDF has a single maximum and has an ellipsoidal form. ## The Equal Differential Time (EDT) likelihood function [EDT description page](../edt/edt.html) ## Oct-Tree Importance Sampling Algorithm [Oct-Tree description page](../octtree/OctTree.html) ## Grid-Search Algorithm The grid-search algorithm performs successively finer, systematic grid-searches within a spatial, *x,y,z* volume to obtain a misfit function, an optimal hypocenter and an estimate of the posterior probability density function ([PDF](core.NLLoc.md#_inversion_)) for hypocenter location. Advantages: #. Does not require partial derivatives, thus can be used with complicated, 3D velocity structures #. Systematic, deterministic coverage of search region #. Accurate recovery of very irregular (non-ellipsoidal) PDF's with multiple minima #. Efficiently reads into memory 2D planes of 3D travel-time grid files, thus can be used with large number of observations and large 3D travel-time grids #. Results can be used to obtain confidence contours Drawbacks: #. Very time consuming relative to stochastic and linear location techniques #. Relative to the size of the most significant region of the PDF, the final search grids may be too large (giving low resolution) or too small (giving truncation of the PDF) #. Requires careful selection of grid size and node spacing ### Procedure The Grid-Search location is based on a nested grid search using one or more location grids as specified by [LOCGRID](control.ControlFile.md#_NLLoc_locgrid_) statements in the Input Control File. The first LOCGRID statement specifies a specific initial search grid with fixed size, number of nodes and location. Subsequent LOCGRID statements specify the size and number of nodes for subsequent, nested grids; the location of these nested grids is usually set automatically in one or more of the *x,y,z* directions. |image11| For each location grid, the location quality (misfit or PDF value) at every node is obtained. For each node, the travel-times for each observation are obtained from the corresponding travel-time grid file and the PDF *s* (**x**), or misfit value *g* (**x**) is calculated using the equations given above in the `Inversion Approach](#_inversion_) section. These location quality values are
saved to a 3D grid file if requested. If there is a subsequent nested
grid, its position (for the directions with automatic positioning) is
set so that it is centered on the maximum PDF node (or, equivalently,
the minimum misfit node) of the current grid.

The initial location grid must be fully contained within the travel-time
grid files corresponding to a given observation for that observatoin to
be used in the location. Subsequent location grids, even if their
position is set automatically, must be fully contained within the
initial grid. The NLLoc program will attempt to translate a nested grid
that intersects a boundary of the initial grid so that it is contained
inside of the initial grid; if this is not possible the location will be
terminated prematurely.

For every node of each location grid, the grid-search algorithm must
obtain travel-times for every observation. These times are stored on
disk in 3D travel-time grid files which may be very large. It would be
extremely time consuming to read these times one by one directly from
the disk files, but there is also not enough space in general to fully
read all the relevant 3D grid files into memory. However, the grid
search is performed systematically throughout each location grid with
the *x* index varying last. Thus, it is adequate to have 2D planes or
"sheets" corressponding to the current *x* index available in memory at
any one time. This approach is used by the grid-search algorithm. Sheets
of data with a given *x* index are read from the 3D travel-time grid
files as large blocks of bytes, which is very fast in comparison to
reading the same number of data values individually.

## Metropolis-Gibbs Sampling Algorithm

The Metropolis-Gibbs algorithm performs a directed random walk within a
spatial, *x,y,z* volume to obtain a set of samples that follow the 3D
[PDF](core.NLLoc.md#_inversion_) for the earthquake location. The
samples give and estimate of the optimal hypocenter and an image of the
posterior probability density function (PDF) for hypocenter location.

Advantages:

#. Does not require partial derivatives, thus can be used with
   complicated, 3D velocity structures
#. Accurate recovery of moderately irregular (non-ellipsoidal) PDF's
   with a single minimum
#. Only only moderately slower (about 10 times slower) than linearised,
   iterative location techniques, and is much faster (about 100 times
   faster) than the grid-search
#. Results can be used to obtain confidence contours

Drawbacks:

#. Stochastic coverage of search region - may miss important features
#. Inconsistent recovery of very irregular (non-ellipsoidal) PDF's with
   multiple minima
#. Requires careful selection of sampling parameters
#. Attempts to read full 3D travel-time grid files into memory, thus may
   run very slowly with large number of observations and large 3D
   travel-time grids

### Procedure

The Metropolis-Gibbs search proceedure to obtain samples of a PDF is
based on the algorithm of [Metropolis et al. (1953)](references.html)
for the simulation of the distribution of a set of atoms at a given
temperature. The Metropolis-Gibbs algorithm used here is similar to the
"Metropolis" algorithm described in [Mosegaard and Tarantola (1995)](references.html) and the "Gibbs sampler" with temperature
*T* =1 described in [Sen and Stoffa (1995; sec 7.2)](references.html). It may be considered as a version of
Metropolis simulated annealing [Kirkpatrick et al. (1983)](references.html) where the temperature parameter is a
constant determined by the covariance matrix for the observational and
forward problem uncertainties. Thus the algorithm does not "anneal" or
converge to an optimal solution, but instead produces a set of samples
which follow the posterior PDF for the inverse problem.

The Metropolis-Gibbs sampler used in the program NonLinLoc for
earthquake location consists of a directed walk in the solution space
(*x*, *y*, *z*) which tends towards regions of high likelihood for the
location PDF, *s* (**x**) given by equation (3). At each step, the
current walk location **x** *:sub:[curr`* is perturbed by a vector *d* **x** of arbitrary direction and given length *l* to give a new location **x** *<sub>new</sub>*. The likelihood *s* (**x** *<sub>new</sub>*) is calculated for the new location and compared to the likelihood *s* (**x** *<sub>curr</sub>*) at the current location. If *s* (**x** *<sub>new</sub>*) ³ *s* (**x** *<sub>curr</sub>*), then the new location is accepted. If *s* (**x** *<sub>new</sub>*)](*s* (**x** *<sub>curr</sub>*), then the new location is accepted with
probability *P* = *s* (**x** *<sub>new</sub>*) /
*s* (**x** *<sub>curr</sub>*). When a new location is accepted it becomes
the current location and may be saved as a sample of the location PDF.

In earthquake location, the dimensions of the significant regions of the
location PDF can vary enormously and are not known a priori. It is
important to choose an initial step size large enough to allow global
exploration of the search volume, and to obtain a final step size that
gives good coverage of the location PDF while resolving details and
irregular structure of the PDF. The NonLinLoc Metropolis-Gibbs sampler
uses three distinct sampling stages to determine adaptively an optimal
step size *l* for the walk:

#. A **learning** stage where the step size is fixed and relatively
   large. The walk can explore globally the search volume and migrate
   towards regions of high likelihood. "Accepted" samples are not saved.
#. An **equilibration** stage where the step size *l* is adjusted in
   proportion to the standard deviations (*s <sub>x</sub>*, *s <sub>y</sub>*,
   *s <sub>z</sub>*) of the spatial distribution of all previously
   "accepted" samples obtained after the middle of the learning stage.
   After each new accepted sample, the standard deviations are updated
   and the step size *l* is set equal to *f <sub>s</sub>*
   (*s <sub>x</sub> s <sub>y</sub> s <sub>z</sub>/N<sub>s</sub>*) <sup>1/3</sup>,
   where *N <sub>s</sub>* is the number of previously "accepted" samples,
   and *f <sub>s</sub>* =8 is a step size scaling factor. This formula
   sets *l* in proportion to the cell size required to tile with
   *N <sub>s</sub>* cells the rectangular volume with sides *s <sub>x</sub>*,
   *s <sub>y</sub>* and *s <sub>z</sub>*. The walk can continue to migrate
   towards or may begin to explore regions of high likelihood.
   "Accepted" samples are not saved.
#. A **saving** stage where the step size *l* is fixed at its final
   value from the equilibration stage. The walk can continue to explore
   regions of high likelihood. "Accepted" samples are assumed to follow
   the location PDF and can be saved, but there may be a waiting time of
   several samples between saves to insure the independence of saved
   samples.

|image12|

It is important to set the parameters for the directed walk so that (1)
during the **learning** and **equilibration** stages the walk approaches
and reaches the high likelihood regions of the location PDF, and so that
(2) by the **saving** stage a suitable, relatively small, fixed step
size has been obtained to accurately explore and image the PDF.

|image13|

The NonLinLoc Metropolis-Gibbs sampling algorithm is initialised as
follows:

#. The walk location is set at the *x*, *y* position of the station
   with the earliest arrival time and non-zero weight, at the mean depth
   of the search region.
#. If the initial step *l* size is not specified, it is set to the cell
   size required to tile with *N <sub>s</sub>* cells the plane formed by
   the two longest sides of the initial search region. *N <sub>s</sub>* is
   the total number of samples to be accepted during the saving stage,
   including samples that are skipped between saves.

The rejection by the algorithm of new walk locations for a large number
of consecutive tries (the order of 1000 tries) may indicate that the
last "accepted" sample falls on a sharp likelihood maxima that is
narrower than the current step size. To allow the search to continue in
this case, the new location is accepted unconditionally and the step
size is reduced by a factor of two.

In the case that the size of the location PDF is very small relative to
the search region, the algorithm may fail to locate the region of high
likelihood or obtain an optimal step size. In this case the size of the
search region must be reduced or the size of the initial step size
adjusted. A more robust solution to this problem may be to add a
temperature parameter to the likelihood function, as with simulated
annealing. This variable parameter could be set to increase the
effective size of the PDF during the learning and equilibration stages
so that the region of high likelihood is located efficiently, and then
set to 1 during the saving stage so that the true PDF is imaged.

## Running the program - Input

Synopsis: ``NLLoc InputControlFile``

The NLLoc program takes a single argument *``InputControlFile``* which
specifies the complete path and filename for an `Input Control
File <control.ControlFile.md) with certain required and optional statements
specifying program parameters and input/output file names and locations.
See the [NLLoc Statements section](control.ControlFile.md#_NLLoc_) of the Input
Control File for more details. Note that to run NLLoc the [Generic Statements section](control.ControlFile.md#_generic_) of the Input Control File
must contain the [`CONTROL`` and ``TRANS`` (Geographic Transformation) statements. In addition, the NLLoc program requires: #. A file or files containing sets of seismic phase arrival times for each event. These arrival times can be can be specified in a number of [Phase formats](formats.html#_phase_), including those of the HYPO71/HYPOELLIPSE and SEISAN software, and the RéNaSS DEP format. #. Files containing a 2D or a 3D **Travel-time grid** created by the program [Grid2Time](core.Grid2Time.md) for each phase type at each station. If a constant Vp/Vs ratio is used, then only P travel-time grids are required for each station. The names, locations and other information for these files is specified in the [NLLoc Statements section](control.ControlFile.md#_NLLoc_) of the Input Control File. ## Output The location results can be output for **single event** and **summary** (all events) as: #. A [3D Grid](formats.html#_grid_) containing **misfit values** or **PDF <sup>\*</sup> (probability dentsity function)** values throughout the search volume (Grid-search only). #. An ASCII [Hypocenter-Phase File](formats.html#_location_hypphs_) containing **hypocentral coordinates and origin time** for the best **(minimum misfit / maximum likelihood)** point in the the search volume and an associated **phase list** <sup>!</sup> containing station and phase identifiers, phase times, residuals, take-off angles and other station/phase information. This file contains other information, including the **hypocentral coordinates and uncertainty** <sup>\*</sup> given by the traditional (Gaussian/Normal) **expectation** and **covariance matrix** measures of the PDF. #. A [binary Scatter file](formats.html#_location_scat_) <sup>\*!</sup> containing samples drawn from the PDF #. An ASCII `Confidence Levels](formats.html#_location_conf_) :sup:[\*!` giving the value of the PDF corresponding to confidence levels from 0.1 to 1.0 <sup>\*</sup> these output types are only generated for grids where the PDF is calculated. <sup>!</sup> these output types are only written to single event files The location results can also be output as **summary** (all events) files containing: #. A [3D Grid](formats.html#_grid_) header file describing the search volume #. ASCII [Phase Statistics](formats.html#_location_phsstat_) giving the mean residuals for P and S phases at each station #. An expanded, `quasi-HYPOELLIPSE format](formats.html#_location_qhypell_)
#. The [HypoInverse Archive](formats.html#_location_hypinv_) format
   which serves as input to the program [FPFIT (Reasenberg *et al.*, 1985)](references.html) for grid-search determination of focal
   mechanism solutions.

Single event and summary files are only saved for specific nested
search-grids as specified in the
[LOCGRID](control.ControlFile.md#_NLLoc_locgrid_) statement in the Input
Control File.

## Processing and Display of results

The location results for one or more events can be combined with the
program [LocSum](core.LocSum.md) to produce
[output](core.LocSum.md#_output_) such as a comprehensive, summary
[Hypocenter-Phase File](formats.html#_location_hypphs_), a binary
[Scatter File](formats.html#_location_), and a set of simple ASCII
format Scatter samples files.

The a comprehensive, summary [Hypocenter-Phase File](formats.html#_location_hypphs_) forms the input for the Java
applet [SeismicityViewer](SeismicityViewer.html) for interactive, 3D
display of event locations on an internet browser or appletviewer.

The location results for a single event or the output files produced by
the program [LocSum](core.LocSum.md) can be post-processed with the
program [Grid2GMT](core.Grid2GMT.md) to produce a GMT command script for
plotting misfit, PDF and location "cloud" results using the [GMT plotting package](http://gmt.soest.hawaii.edu%20target=_top).

Back to [the NonLinLoc site Home page](index.md).

*Anthony Lomax*

   :width: 212px
   :height: 44px
   :width: 206px
   :height: 42px
   :width: 258px
   :height: 49px
   :width: 16px
   :height: 26px
   :width: 13px
   :height: 21px
   :width: 221px
   :height: 34px
   :width: 182px
   :height: 65px
   :width: 186px
   :height: 37px
   :width: 120px
   :height: 44px
   :width: 209px
   :height: 24px
   :width: 132px
   :height: 25px
