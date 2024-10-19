# Script details:

## Test scripts:

These scripts require the moteus python library, installed via `pip3 install moteus`. See the [python reference](https://github.com/mjbots/moteus/blob/main/lib/python/README.md) and the  [full Moteus reference](https://github.com/mjbots/moteus/blob/main/docs/reference.md) for details.

`actuator.py` Shared abstraction layer for the moteus motor controller using the USB to canFD interface. Used by all other test scripts

`record_max_torque.py` torque ramps with configurable duration and peak

`record_speedramp.py` Speed ramp with configurable duration and peak

`record_torque_constant.py` Torque ramp in combination with a mini40 loadcell (untested)

`record_torqueramp.py` Torque ramps for play and stiffness. multiple repetations at 2 different peaks. Used for play and stiffness estimation

`record_trajectory.py` For a trajectory of postions with configurable speed limit. Repeats trajectory at increasing accelerations.

`record-run-in.py`  Run actuator in alternating directions indefinetly while saving CSV data.

## Data processing scripts

These files are jupyter notebook files requiring the jupyter python library, or can be opened using vs-code. Furthermore, they require some libraries installed by `pip install numpy matplotlib pandas`

`analyse_anti-backlash.ipynb` jupyter notebook for the play, stiffness, and friction tests and all resulting plots. Saved plots as SVG are the ones used in the the paper.

`analyse_performance.ipynb` jupyter notebook for the maximum torque and velocity tests and plots, as well as the pendulum trajectory tracking tests and corresponding plots

## Directory

`./test_data` Resulting test data, all files have timestamps and short descriptions in the name. All of the used data is aready added in the analysing notebook files

`./figures` Resulting plots as SVG files from the analysis notebooks
