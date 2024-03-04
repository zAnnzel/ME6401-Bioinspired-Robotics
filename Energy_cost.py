import wandb
import numpy as np
from scipy.integrate import quad
from Hebi import Hebi
from Hebi_Env import HebiEnv
from Hebi_TrajPlanner import TrajPlanner

# Initialize wandb
wandb.init(project='Hebi-test', name='energy')

# Function to represent the trajectory (replace with your actual trajectory function)
def trajectory(t):
    x = np.cos(t)
    y = np.sin(t)
    z = 0.1 * t  # Example trajectory for the z-axis
    return x, y, z

# Function to calculate motor power based on joint torques and angular velocities
def calculate_motor_power(torque, angular_velocity):
    return torque * angular_velocity

# Function representing the torque profile for each joint (replace with your actual torques)
def joint_torque_profile(timestep):
    # Example torque profile, replace with your calculations
    # torque_x = Hebi.move_front_leg_jointspace(timestep)[:,3]
    # torque_y = Hebi.move_front_leg_jointspace(timestep)[:,4]
    # torque_z = Hebi.move_front_leg_jointspace(timestep)[:,5]
    torque_x = HebiEnv.step(TrajPlanner.front_leg_jointspace_traj(timestep, leg_index=0))[:,3]
    torque_y = HebiEnv.step(TrajPlanner.front_leg_jointspace_traj(timestep, leg_index=0))[:,4]
    torque_z = HebiEnv.step(TrajPlanner.front_leg_jointspace_traj(timestep, leg_index=0))[:,5]
    return torque_x, torque_y, torque_z

# Time parameters
start_time = 0.0
time_step = 0.1
step = 100
end_time = start_time + step * time_step

# Function to calculate the derivative of the trajectory
def trajectory_derivative(t):
    dt = 1e-6  # Small time step for numerical differentiation
    x, y, z = trajectory(t)
    x_dt, y_dt, z_dt = (trajectory(t + dt)[0] - x)/ dt, (trajectory(t + dt)[1] - y)/ dt, (trajectory(t + dt)[2] - z) / dt
    return x_dt, y_dt, z_dt

# Integration function for calculating energy consumption
def integrand(t):
    torques = joint_torque_profile(t)
    power = sum(calculate_motor_power(torque, angular_velocity) for torque, angular_velocity in zip(torques, trajectory_derivative(t)))
    return power

# Integrate the power over time to obtain energy consumption
result, _ = quad(integrand(t = 100), start_time, end_time)

print(f"Total energy consumption: {result} J")

# Log energy to wandb
wandb.log({
    "Force": 100,
    "Total energy consumption": result
})

# Finish the wandb run
wandb.finish()