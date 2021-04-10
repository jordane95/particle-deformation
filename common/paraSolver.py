import numpy as np
import matplotlib.pyplot as plt


class ParaSolver:
    def __init__(self, list_A, list_time):
        self.list_A = list_A
        self.list_time = list_time

        # assume equal-time space in list_time
        self.delta_t = list_time[1]-list_time[0]

        self.list_F = None
        self.list_eig_values = None
        self.list_eig_vectors = None
        self.list_ratios = None
        self.list_angles = None
        self.list_lengths = None

        self.list_S = None
        self.list_eig_values_s = None
        self.list_eig_vectors_s = None
        self.list_inner_product = None

        self.list_omega = None

    @staticmethod
    def _calc_F_next(A, delta_t, F_prec, dim=3):
        D = np.eye(dim) - (delta_t / 2) * A
        E = np.eye(dim) + (delta_t / 2) * A
        F = np.dot(np.dot(np.linalg.pinv(D), E), F_prec)
        return F

    def _calc_list_F(self, dim=3):
        # calculate transformation tensor at each time
        F = np.eye(dim)
        self.list_F = []
        for A in self.list_A:
            F = self._calc_F_next(A, self.delta_t, F, dim)
            self.list_F.append(F)
        return self.list_F

    @staticmethod
    def decompose(F, param_prev=None):
        # new algorithm to decompose F to get eigen parameters
        # in physical order
        F_inv = np.linalg.pinv(F)
        G = np.dot(F_inv.transpose(), F_inv)
        param_next = np.linalg.eig(G)
        if param_prev is not None:
            values_prev, vectors_prev = param_prev
            values_next, vectors_next = param_next
            sim = np.abs(vectors_prev.T @ vectors_next)
            sort_idx = np.argmax(sim, axis=1)
            # print('Before sort:\n', param_next)
            # print('sim:\n', sim)
            # print(sort_idx)
            values_next = values_next[sort_idx]
            vectors_next = vectors_next.T[sort_idx].T
            param_next = (values_next, vectors_next)
            # print("After sort:\n", param_next)
            # print()
        return param_next

    def calc_eig_para(self):
        # calculate the eig values and vectors at each time
        if self.list_F is None:
            self._calc_list_F()
        self.list_eig_values = []
        self.list_eig_vectors = []
        params = (np.array([1, 1, 1]), np.eye(3, dtype=float))
        for i, F in enumerate(self.list_F):
            # params = self.decompose(F, params) if i != 0 else self.decompose(F)
            params = self.decompose(F, params)
            eig_values, eig_vectors = params
            self.list_eig_values.append(eig_values)
            self.list_eig_vectors.append(eig_vectors)
        return self.list_eig_values, self.list_eig_vectors

    @staticmethod
    def calc_ratio(list_eig_values):
        list_ratios = []
        for eig_values in list_eig_values:
            ratio_xy = np.sqrt(eig_values[1]/eig_values[0])
            ratio_yz = np.sqrt(eig_values[2]/eig_values[0])
            ratio_xz = np.sqrt(eig_values[2]/eig_values[1])
            ratios = [ratio_xy, ratio_yz, ratio_xz]
            list_ratios.append(ratios)
        return np.array(list_ratios)

    @staticmethod
    def calc_angle(list_eig_vectors, normalize=False):
        list_angles = []
        for eig_vectors in list_eig_vectors:
            # inner product -> matrix product
            angles = np.arccos(eig_vectors)
            for i in range(len(angles)):
                for j in range(len(angles[i])):
                    if angles[i][j] > np.pi/2:
                        angles[i][j] -= np.pi
            if normalize:
                angles = np.abs(angles)
            list_angles.append(angles)
        return np.array(list_angles)

    def calc_geo_para(self, normalize=False):
        """

        :param sort:
        :param normalize:
        :return:
        """
        self.calc_eig_para()
        self.list_ratios = self.calc_ratio(self.list_eig_values)
        self.list_angles = self.calc_angle(self.list_eig_vectors, normalize)
        return self.list_ratios, self.list_angles

    def calc_length(self):
        self.list_lengths = np.sqrt(1/(np.array(self.list_eig_values)+1e-8))
        return self.list_lengths

    def plot_ratio(self, log=False):
        list_ratios = np.array(self.list_ratios)
        list_time = self.list_time
        if log:
            list_ratios = np.log(list_ratios)
        labels = ['a_1/a_0', 'a_2/a_0', 'a_2/a_1']
        for i in range(3):
            plt.subplot(1, 3, i+1)
            plt.plot(list_time, list_ratios[:, i], label=labels[i])
            plt.xlabel('t')
            plt.ylabel('ratio')
            plt.legend()
        plt.show()
        return None

    def plot_angle(self):
        list_angles = np.array(self.list_angles)
        num = 0
        for i in range(3):
            for j in range(3):
                num += 1
                plt.subplot(3, 3, num)
                plt.ylim(0, np.pi/2+0.1)
                plt.plot(self.list_time, list_angles[:, i, j],
                         label='angle(e_'+str(j+1)+', x_'+str(i+1)+')')
                plt.legend()
                plt.xlabel('t')
                plt.ylabel('theta')
        plt.show()
        return None

    def calc_strain_tensor(self):
        self.list_S = [(A+A.T)/2 for A in self.list_A]
        return self.list_S

    def decompose_S(self, S, params_prev=None):
        values_next, vectors_next = np.linalg.eig(S)
        if params_prev is not None:
            values_prev, vectors_prev = params_prev
            sim = np.abs(vectors_prev.T @ vectors_next)
            sort_idx = np.argmax(sim, axis=1)
            # print(vectors_prev)
            # print(vectors_next)
            # print(sim)
            # print(sort_idx)
            # print()
            values_next = values_next[sort_idx]
            vectors_next = vectors_next.T[sort_idx].T
        return values_next, vectors_next

    def calc_eig_strain(self):
        self.list_eig_values_s = []
        self.list_eig_vectors_s = []
        # print(self.list_S)
        params = (np.array([1, 1, 1]), np.eye(3))
        for i, S in enumerate(self.list_S):
            # params = self.decompose(S, params) if i != 0 else self.decompose(S)
            params = self.decompose_S(S, params)
            eig_value, eig_vector = params
            self.list_eig_values_s.append(eig_value)
            self.list_eig_vectors_s.append(eig_vector)
        return self.list_eig_values_s, self.list_eig_vectors_s

    def calc_coli(self, normalize=False):
        self.calc_strain_tensor()
        self.calc_eig_strain()
        list_eig_vectors_e = self.list_eig_vectors
        list_eig_vectors_s = self.list_eig_vectors_s
        list_inner_product = [np.dot(e.transpose(), s) for (e, s) in zip(list_eig_vectors_e, list_eig_vectors_s)]
        if normalize:
            list_inner_product = np.abs(list_inner_product)
        self.list_inner_product = list_inner_product
        return list_inner_product

    def plot_coli(self):
        list_time = self.list_time
        list_coli = self.list_inner_product
        # for coli in list_coli:
        #     print(coli)
        num = 0
        for i in range(3):
            for j in range(3):
                num += 1
                plt.subplot(3, 3, num)
                plt.ylim(0, 1)
                plt.plot(list_time, [coli[i, j] for coli in list_coli],
                         label='<e_'+str(i+1)+', s_'+str(j+1)+'>')
                plt.legend()
                plt.xlabel('t')
                plt.ylabel('inner product')
        plt.show()
        return None

    # calculate rot omega
    def calc_omega(self):
        list_W = np.array([(A-A.T)/2 for A in self.list_A])
        self.list_omega = [np.array([W[1, 0], W[2, 0], W[2, 1]]) for W in list_W]
        return self.list_omega

    def save_data(self):
        np.save("list_ratios.npy", self.list_ratios)
        np.save("list_angles.npy", self.list_angles)
        np.save("list_colis.npy", self.list_inner_product)

    def read_data(self):
        self.list_ratios = np.load("list_ratios.npy")
        self.list_angles = np.load("list_angles.npy")
        self.list_inner_product = np.load("list_colis.npy")


def make_grad_tensor(s_1, s_2, w_z):
    A = np.array([[s_1, -w_z, 0],
                  [w_z, s_2, 0],
                  [0, 0, -(s_1+s_2)]])
    return A


def test():
    A = make_grad_tensor(s_1=2, s_2=1, w_z=0.25)
    steps = 500
    list_A = [A for _ in range(steps)]
    para_solver = ParaSolver(list_A=list_A, list_time=np.linspace(0, 5, steps))
    import os
    if "list_ratios.npy" in os.listdir():
        para_solver.read_data()
    else:
        para_solver.calc_geo_para(normalize=True)
        para_solver.calc_coli(normalize=True)
        para_solver.save_data()
    para_solver.plot_ratio()
    para_solver.plot_angle()
    para_solver.plot_coli(normalize=True)


if __name__ == '__main__':
    test()
