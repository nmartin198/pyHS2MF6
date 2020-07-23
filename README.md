# pyHS2MF6: An Integrated Hydrologic Model 

pyHS2MF6 is a dynamic coupling of HSPF and MODFLOW 6 in Python. It is composed of three independent processes: HSPF, MODFLOW 6, and a coupled model controller and queue server that are linked with message passing queues. Dynamic coupling among the processes provides for information exchange in memory and process update during each simulation time step. To use pyHS2MF6, the user must specify the spatial mapping between the lumped parameter, stream reach and sub-watershed HSPF representation and the three-dimensional computational grid representation in MODFLOW 6. Mapping specification provides a means to focus infiltration, simulated in HSPF, to discrete zones of collections of cells, in MODFLOW 6, that could represent fractures, faults, or regions of enhanced secondary porosity to create focused areas of high transmissivity and storage if needed to match site conceptualization.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
