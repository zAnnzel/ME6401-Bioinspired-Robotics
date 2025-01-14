import numpy as np
import hebi
from functions import solveIK, rot, trans
from Hebi_TrajPlanner import TrajPlanner


class Grasper:
    def __init__(self, neutralPos):
        self.dutyfactor = 0.5
        self.period = 1.0
        self.dt = 1/100  # pybullet default
        self.eePos = neutralPos  # neutral position for the robot
        self.eeAng = np.array([0., 0., 0., 0., 0., 0.,])  # the diviation of each leg from neutral position, use 0. to initiate a float type array

    # 工作空间举起物体轨迹规划
    def front_leg_workspace_traj(self, step, leg_index):
        init_point = np.array([[0.85, 0.85, 0.23, 0.23, -0.4, -0.4],
                               [0.1, -0.1, 0.4, -0.4, 0.4, -0.4],
                               [0.1, 0.1, -0.12, -0.12, -0.12, -0.12]])
        # end_point = np.array([[0.2, 0.2, 0.23, 0.23, -0.4, -0.4],
        #                       [0.1, -0.1, 0.4, -0.4, 0.4, -0.4],
        #                       [0.5, 0.5, -0.12, -0.12, -0.12, -0.12]])
        dt = 2 / 100
        t = step * dt
        traj = init_point[:, leg_index] + [(1.414 / 4 * np.cos(t) - 1.414 / 4), 0, (1 / 4 * np.sin(t))]
        return traj

    # 关节空间举起物体轨迹规划
    def front_leg_jointspace_traj(self, init_pos, step, leg_index):
        # end_point = np.array([-0.49474198, -0.67771703, -4.46762366,  # leg 0
        #                       0.49474198, 0.67771703, 4.46762366,  # leg 1
        #                       -0.64025334, -0.32865358, -1.89880505,
        #                       0.64025296, 0.3286524, 1.89880162,
        #                       -0.27359199, -0.32446194, -1.80610188,
        #                       0.27359199, 0.32446194, 1.80610188])
        # deltapos = (end_point - init_point)[:, leg_index]
        dt = self.dt
        t = step * dt
        traj = init_pos[(leg_index * 3): (leg_index * 3 + 3)] + [(-1 + leg_index * 2) * 0.01 * t * 0,
                                                                   (-1 + leg_index * 2) * 0.75 * t * 0.4,
                                                                   (-1 + leg_index * 2) * 0.6 * t * 0.5]
        return traj

    # 关节空间调节俯仰
    def adjust_base_traj(self, init_pos, step, leg_index):
        dt = self.dt
        t = step * dt
        traj = init_pos[(leg_index * 3)] + ((-1) ** leg_index) * 0.1 * t
        return traj

    # 三次多项式插值轨迹规划
    def cubic_interpolation_traj(self, init_pos, step):
        dt = 1 / 800
        t = step * dt
        initial_v = np.array([0, 0, 0])
        end_v = np.array([0, 0, 0])
        initial_pos = init_pos[0: 3]
        end_pos = np.array([-0.46143309, -2.48169756, -2.7767164])
        t1 = 1
        a0 = initial_pos
        a1 = initial_v
        a2 = (3 / (t1 ** 2)) * (end_pos - initial_pos) - (1 / t1) * (2 * initial_v + end_v)
        a3 = (2 / (t1 ** 3)) * (initial_pos - end_pos) + (1 / (t1 ** 2)) * (initial_v + end_v)
        q = np.array(a0 + a1 * t + a2 * (t ** 2) + a3 * (t ** 3)).reshape(1, 3)
        traj = np.array(q).reshape(-1, 3)
        return traj

    # 五次多项式插值轨迹规划
    def polynomial_interpolation_path(self, init_pos, step):
        dt = 1 / 800
        t = step * dt
        t1 = 1
        initial_v = np.array([0, 0, 0])
        end_v = np.array([0, 0, 0])
        initial_a = np.array([0, 0, 0])
        end_a = np.array([0, 0, 0])
        initial_pos = init_pos[0: 3]
        end_pos = np.array([-0.46143309, -2.48169756, -2.7767164])
        a0 = initial_pos
        a1 = initial_v
        a2 = initial_a / 2
        a3 = ((20 * (end_pos - initial_pos) - (8 * end_v + 12 * initial_v) * t1 - (3 * initial_a - end_a) * (t1 ** 2)) /
              (2 * (t1 ** 3)))
        a4 = (30 * (initial_pos - end_pos) + (14 * end_v + 16 * initial_v) * t1 + (3 * initial_a - 2 * end_a) *
              (t1 ** 2)) / (2 * (t1 ** 4))
        a5 = ((12 * (end_pos - initial_pos) - (6 * (end_v + initial_v)) * t1 - (initial_a - end_a) * (t1 ** 2)) /
              (2 * (t1 ** 5)))
        q = a0 + a1 * t + a2 * t ** 2 + a3 * t ** 3 + a4 * t ** 4 + a5 * t ** 5
        traj = np.array(q).reshape(-1, 3)
        return traj

    def release_jointspace_traj(self, end_point, step, leg_index):
        dt = self.dt
        t = step * dt
        release_traj = end_point[(leg_index * 3): (leg_index * 3 + 3)] + [(-1 + leg_index * 2) * 0.15 * -t * 1.5,
                                                                          (-1 + leg_index * 2) * 0.7 * -t * 1.5,
                                                                          (-1 + leg_index * 2) * 0.2 * -t * 1.5]
        return release_traj


if __name__ == '__main__':
    import numpy as np
    import matplotlib.pyplot as plt

    init_point = np.array([-0.49188775, 0.12909448, -0.051144,
                           0.49188775, -0.12909448, 0.051144,
                           - 0.64025334, - 0.32865358, - 1.89880505,
                           0.64025296, 0.3286524, 1.89880162,
                           - 0.27359199, - 0.32446194, - 1.80610188,
                           0.27359199, 0.32446194, 1.80610188])

    g = Grasper(init_point)

    traj = g.front_leg_jointspace_traj(step=400 , leg_index=0)
    x = traj[0]
    y = traj[1]
    z = traj[2]
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    ax.scatter(x, y, z, s=1)
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    ax.set_aspect('equal', 'box')
    plt.show()
    pass