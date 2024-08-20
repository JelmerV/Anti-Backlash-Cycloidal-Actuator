import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# setup latex style for plots exported to svg
plt.rcParams['svg.fonttype'] = 'none'
import matplotlib_inline.backend_inline
matplotlib_inline.backend_inline.set_matplotlib_formats('svg')


plt.rc('legend', fontsize=8.5)
plt.rc('grid', color='0.9')
plt.rcParams['axes.grid'] = True

rev_to_rad = 2 * np.pi

filename = 'test_data/2024-08-07__15-35-35_trajectory_700gr 32v.csv'
df = pd.read_csv(filename)
fig, axs = plt.subplots(3, 1, figsize=(7.5, 8.5), sharex=True)

axs[0].plot(df['TIME'], df['COMMAND_POSITION']*rev_to_rad, label='\\ld{Command Position}')
axs[0].plot(df['TIME'], df['CONTROL_POSITION']*rev_to_rad, label='\\ld{Control Position}')
axs[0].plot(df['TIME'], df['POSITION']*rev_to_rad, label='\\ld{Position}')
axs[0].set_ylabel('Position [rad]')
axs[0].legend(loc='upper left')

# axs[1].plot(df['TIME'], df['COMMAND_VELOCITY'], label='\\ld{Command Velocity [rad/s]}')
axs[1].plot(df['TIME'], df['CONTROL_VELOCITY']*rev_to_rad, label='\\ld{Control Velocity}')
axs[1].plot(df['TIME'], df['VELOCITY']*rev_to_rad, label='\\ld{Velocity}')
axs[1].set_ylabel('Velocity [rad/s]')
axs[1].legend(loc='upper left')

axs[2].plot(df['TIME'], df['CONTROL_TORQUE'], label='\\ld{Control Torque}')
axs[2].plot(df['TIME'], df['TORQUE'], label='\\ld{Torque}')
averaged_torque = df['TORQUE'].rolling(window=5, center=True).mean()
axs[2].plot(df['TIME'], averaged_torque, label='\\ld{Averaged Torque}')
axs[2].set_ylabel('Torque [Nm]')
axs[2].legend(loc='upper left')

# axs[3].plot(df['TIME'], df['Q_CURRENT'], label='\\ld{Q Current [A]}')
# axs[3].legend()

axs[0].set_xlim([15, 35])
axs[2].set_xlabel('Time [s]')

# fig.suptitle('Trajectory tracking test')
fig.tight_layout()

plt.savefig('figures/trajectory_700gr_32v.svg')

plt.show()