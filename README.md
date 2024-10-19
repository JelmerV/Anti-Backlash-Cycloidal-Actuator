# MSc Thesis - Cost-Effective and Torque-Dense Cycloidal Actuator with Anti-Backlash Mechanisms

Accompaning files for the thesis work "Anti-Backlash Mechanisms for Cost-Effective Cycloidal Drive Robotic Actuators: Design and Evaluation"

Results - Test scripts - CAD source - Step files - Documentation - Diagrams - Photos

## Abstract

3D-printing is a promising method for cost-effective actuator designs, but it often results in less precise tolerances, leading to increased play.
In this work, we propose two novel anti-backlash mechanisms for cycloidal reducers. One uses a conically shaped cycloidal disk, and the other uses a split non-pinwheel design. Both were integrated into a compact actuator design. Two prototypes were manufactured and extensively tested in comparison to a baseline model. Experimental results show that the proposed mechanisms reduce play at the cost of increased friction. Both mechanisms utilize an adjustable preload that can be configured for the intended application based on the trade-off between play and friction.
Furthermore, the designed actuator demonstrates performance that is competitive with recent works. Using 3D-printed components proves to be a viable manufacturing method for cost-efficient designs.

## Actuator design

<img src="Documentation/baseline cross-section - double.svg" alt="Baseline section views" height="300">

<p float="left">
  <img src="Documentation/printed-parts_annotated.svg" alt="Prototype parts" height="250">
  <img src="Documentation/Photos/prototypes assembled.jpg" alt="Three assembled prototypes and mounting and locking plates" height="250">
</p>

## Anti-Backlash mechanism

<p float="left">
    <img src="Documentation/split-pinwheel isolated parts.svg" alt="Split Non-pinwheel mechanism - modified parts" height="200">
    <img src="Documentation/conic isolated parts.svg" alt="Conic Cycloidal disk mechanism - modified parts" height="200">
</p>


## File overview


`Agendas` All meeting agendas

`CAD Export` Exported CAD files, such as STEP files of the assemblies and individuald STL or STEP parts for 3D-printing

`CAD Source` SOLIDWORKS files of all components for easy modification

`CAD Source/test setup` SOLIDWORKS files for parts related to the tests and test setup

`CAD Source/off-the-shelf` SOLIDWORKS files for sourced parts, such as bearings and hardware

`Cycloid and Non-Pinwheel Profile Generation` Jupyter notebook file with scripts for the generation of cycloidal and non-pinwheel profiles. Included function to export (part of) the profile to DXF.

`Documentation` Files for some of the tables and comparisons of the paper

`Documentation/diagrams` SVG files of all diagrams and annotated images

`Documentation/CAD Section Views` Screenshots of the CAD design

`Documentation/Cad animations` Videos of the motions and exploded views of the CAD design

`Documentation/All photos and videos` All pictures and photos from the timeline of the project. All files are timestamped, so recorded tests can e matched by video and raw data

`Test Scripts` More details about these scripts in [corresponding README](<Test Scripts/README.md>)

`Test Scripts/test_data` Resulting test data, all files have timestamps and short descriptions in the name. All of the used data is aready added in the analysing notebook files

`Test Scripts/figures` Resulting plots as SVG files from the analysis notebooks


## License

Shield: [![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

This work is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg
