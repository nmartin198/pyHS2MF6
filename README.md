# pyHS2MF6: An Integrated Hydrologic Model 

**pyHS2MF6** is an open source, integrated hydrologic model. Integrated hydrologic modeling means simulating the full hydrologic cycle in terrestrial environments where both surface- and sub-surface water flow need to be represented. It is a dynamic coupling of two existing hydrologic models, [HSPF](https://www.epa.gov/ceam/hydrological-simulation-program-fortran-hspf) and [MODFLOW 6](https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model), in Python.

**pyHS2MF6** currently only supports water movement and storage processes. Snow, frozen ground, and fate and transport processes and representations are **not** currently supported.

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
