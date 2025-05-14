# pyHS2MF6: An Integrated Hydrologic Model 

**pyHS2MF6** is an open source, integrated hydrologic model. Integrated hydrologic modeling means simulating the full hydrologic cycle in terrestrial environments where both surface- and sub-surface water flow need to be represented. It is a dynamic coupling of two existing hydrologic models, [HSPF](https://www.epa.gov/ceam/hydrological-simulation-program-fortran-hspf) and [MODFLOW 6](https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model), in Python.

**pyHS2MF6** currently only supports water movement and storage processes. Snow, frozen ground, and fate and transport processes and representations are **not** currently supported.

It was developed for use in the Blanco River Aquifers Assessment Tool (BRAAT). Conceptualization of **pyHS2MF6** occurred during the conceptual model development phase of the BRAAT project. The [Conceptual Model Report](https://gato-docs.its.txstate.edu/jcr:3a5f9f4d-454d-4cf4-9d12-6cc643a64368) provides the requirements for **pyHS2MF6**. Drafts of reports for the second phase of the BRAAT project, which covered model implementation and application, are available in this repository in the [example models documentation](https://github.com/nmartin198/pyHS2MF6/tree/master/example_models/braat/docs).

## BRAAT Project Science

From the science perspective, **pyHS2MF6** is not new, and it (as with all integrated hydrological models) follows the blueprint from the 1960s provided in [Blueprint for a physically-based, digitally-simulated hydrologic response model](https://doi.org/10.1016/0022-1694(69)90020-1). Subsequent to development of this blueprint, there have been many implementations of integrated hydrological models that essentially follow this blueprint under different branding. Consequently, **pyHS2MF6** uses two mature and open source models (MODFLOW 6 and HSPF) and maintains the science and engineering calculations in these models, and there is nothing new in this model from a science- and civil engineering-perspective.  

Two scientific advances were made during implementation of this project using **pyHS2MF6**. These advances are related to data assimilation (DA) techniques and are identified below.

- Formal stream discharge observation error model development
    - [Flow Regime-Dependent, Discharge Uncertainty Envelope for Uncertainty Analysis with Ensemble Methods](https://doi.org/10.3390/w15061133)
- Development of a null space sensitivity analysis for ensemble methods
    - [A Null Space Sensitivity Analysis for Hydrological Data Assimilation with Ensemble Methods](https://doi.org/10.3390/hydrology12050106)


## Getting Started

A design goal for **pyHS2MF6** was to provide the capability to leverage existing HSPF watershed models and MODFLOW groundwater models. The desire to leverage these existing tools means that using pyHS2MF6 is complicated. The user needs to know how to use both building block programs before attempting an integrated simulation.

Code documentation, installation instructions, and a test case are provided on the associated [Pages](https://nmartin198.github.io/pyHS2MF6/) site.

## Contributing

The authors are happy to accept contributions to the project. It might be easiest to contact us prior to starting your contribution in case there are any initial suggestions or direction that we can provide.

The general procedure for contributing is as follows.

- Fork the project
- Make your changes
- Submit a pull request
    - It is important to have a conversation when opening a pull request. Describe your change and why it should be accepted.

## Authors

* **Nick Martin** nick.martin@alumni.stanford.edu

## License

This project is licensed under the GNU Affero General Public License v.3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

* A significant portion of pyHS2MF6 development was funded by [Southwest Research Institute](https://www.swri.org/groundwater-and-surface-water-analysis-and-modeling) internal research and development grant 15-R6015.
