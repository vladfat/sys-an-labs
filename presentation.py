from Solve import Solve
import basis_generator as b_gen
import numpy as np
import matplotlib.pyplot as plt

__author__ = 'vlad'


class PolynomialBuilder(object):
    def __init__(self, solution):
        assert isinstance(solution, Solve)
        self._solution = solution
        max_degree = max(solution.p) - 1
        if solution.poly_type == 'chebyshev':
            self.symbol = 'T'
            self.basis = b_gen.basis_sh_chebyshev(max_degree)
        elif solution.poly_type == 'legendre':
            self.symbol = 'P'
            self.basis = b_gen.basis_sh_legendre(max_degree)
        elif solution.poly_type == 'laguerre':
            self.symbol = 'L'
            self.basis = b_gen.basis_laguerre(max_degree)
        elif solution.poly_type == 'hermit':
            self.symbol = 'H'
            self.basis = b_gen.basis_hermite(max_degree)
        self.a = solution.a.T.tolist()
        self.c = solution.c.T.tolist()
        self.minX = [X.min(axis=0) for X in solution.X_]
        self.maxX = [X.max(axis=0) for X in solution.X_]
        self.minY = solution.Y_.min(axis=0)
        self.maxY = solution.Y_.max(axis=0)

    def _form_psi(self):
        """
        Generates specific basis coefficients for Psi functions
        """
        self.psi = list()
        for i in range(self._solution.Y.shape[1]):  # `i` is an index for Y
            psi_i = list()
            shift = 0
            for j in range(3):  # `j` is an index to choose vector from X
                psi_i_j = list()
                for k in range(self._solution.deg[j]):  # `k` is an index for vector component
                    psi_i_jk = self._solution.Lamb[shift:shift + self._solution.p[j], i].getA1()
                    shift += self._solution.p[j]
                    psi_i_j.append(psi_i_jk)
                psi_i.append(psi_i_j)
            self.psi.append(psi_i)

    def _transform_to_standard(self, coeffs: np.ndarray):
        """
        Transforms special polynomial to standard
        :param coeffs: coefficients of special polynomial
        :return: coefficients of standard polynomial
        """
        std_coeffs = np.zeros(coeffs.shape)
        for index in range(coeffs.shape[0]):
            cp = self.basis[index].coef.copy()
            cp.resize(coeffs.shape)
            std_coeffs += coeffs[index] * cp
        return std_coeffs

    def _print_psi_i_jk(self, i, j, k):
        """
        Returns string of Psi function in special polynomial form
        :param i: an index for Y
        :param j: an index to choose vector from X
        :param k: an index for vector component
        :return: result string
        """
        strings = list()
        for n in range(len(self.psi[i][j][k])):
            strings.append('{0:.6f}*{symbol}{deg}(x[{1},{2}])'.format(self.psi[i][j][k][n], j + 1, k + 1,
                                                                      symbol=self.symbol, deg=n))
        return ' + '.join(strings)

    def _print_phi_i_j(self, i, j):
        """
        Returns string of Phi function in special polynomial form
        :param i: an index for Y
        :param j: an index to choose vector from X
        :return: result string
        """
        strings = list()
        for k in range(len(self.psi[i][j])):
            shift = sum(self._solution.deg[:j]) + k
            for n in range(len(self.psi[i][j][k])):
                strings.append('{0:.6f}*{symbol}{deg}(x[{1},{2}])'.format(self.a[i][shift]*self.psi[i][j][k][n],
                                                                          j + 1, k + 1, symbol=self.symbol, deg=n))
        return ' + '.join(strings)

    def _print_F_i(self, i):
        """
        Returns string of F function in special polynomial form
        :param i: an index for Y
        :return: result string
        """
        strings = list()
        for j in range(3):
            for k in range(len(self.psi[i][j])):
                shift = sum(self._solution.deg[:j]) + k
                for n in range(len(self.psi[i][j][k])):
                    strings.append('{0:.6f}*{symbol}{deg}(x[{1},{2}])'.format(self.c[i][j] * self.a[i][shift] *
                                                                              self.psi[i][j][k][n],
                                                                              j + 1, k + 1, symbol=self.symbol, deg=n))
        return ' + '.join(strings)

    def _print_F_i_transformed(self, i):
        """
        Returns string of F function in special polynomial form
        :param i: an index for Y
        :return: result string
        """
        strings = list()
        constant = 0
        for j in range(3):
            for k in range(len(self.psi[i][j])):
                shift = sum(self._solution.deg[:j]) + k
                current_poly = np.poly1d(self._transform_to_standard(self.c[i][j] * self.a[i][shift] *
                                                                     self.psi[i][j][k]),
                                         variable='x[{0},{1}]'.format(j + 1, k + 1))
                constant += current_poly[current_poly.order]
                current_poly[current_poly.order] = 0
                strings.append(str(current_poly))
        strings.append('\n' + str(constant))
        return ' +\n'.join(strings)

    def _print_F_i_transformed_denormed(self, i):
        """
        Returns string of F function in special polynomial form
        :param i: an index for Y
        :return: result string
        """
        strings = list()
        constant = 0
        for j in range(3):
            for k in range(len(self.psi[i][j])):
                shift = sum(self._solution.deg[:j]) + k
                current_poly = np.poly1d(self._transform_to_standard(self.c[i][j] * self.a[i][shift] *
                                                                      self.psi[i][j][k]),
                                         variable='x[{0},{1}]'.format(j + 1, k + 1))
                constant += current_poly[current_poly.order]
                current_poly[current_poly.order] = 0
                strings.append(str(current_poly))
        strings.append('\n' + str(constant))
        return ' +\n'.join(strings)

    def get_results(self):
        """
        Generates results based on given solution
        :return: Results string
        """
        self._form_psi()
        psi_strings = ['Psi({0})([{1},{2}])={result}\n'.format(i + 1, j + 1, k + 1, result=self._print_psi_i_jk(i,j,k))
                       for i in range(self._solution.Y.shape[1])
                       for j in range(3)
                       for k in range(self._solution.deg[j])]
        phi_strings = ['Phi({0})([{1}])={result}\n'.format(i + 1,j + 1,result=self._print_phi_i_j(i,j))
                       for i in range(self._solution.Y.shape[1])
                       for j in range(3)]
        f_strings = ['F({0})={result}\n'.format(i + 1,result=self._print_F_i(i))
                       for i in range(self._solution.Y.shape[1])]
        f_strings_transformed = ['F({0}) transformed:\n{result}\n'.format(i + 1,result=self._print_F_i_transformed(i))
                       for i in range(self._solution.Y.shape[1])]
        f_strings_transformed_denormed = ['F({0}) transformed ' \
                                          'denormed:\n{result}\n'.format(i + 1,result=
        self._print_F_i_transformed_denormed(i))
                       for i in range(self._solution.Y.shape[1])]
        return '\n'.join(psi_strings + phi_strings + f_strings + f_strings_transformed + f_strings_transformed_denormed)

    def plot_graphs(self):
        fig, (ax1, ax2) = plt.subplots(1,2)
        ax1.set_xticks(np.arange(0,self._solution.n+1,5))
        ax1.plot(np.arange(1,self._solution.n+1),self._solution.Y_[:,0], 'r-', label='$Y_1$')
        ax1.plot(np.arange(1,self._solution.n+1),self._solution.F_[:,0], 'b-', label='$F_1$')
        ax1.legend(loc='upper right', fontsize=16)
        ax1.set_title('Coordinate 1')
        ax1.grid()

        ax2.set_xticks(np.arange(0,self._solution.n+1,5))
        ax2.plot(np.arange(1,self._solution.n+1),self._solution.Y_[:,1], 'r-', label='$Y_2$')
        ax2.plot(np.arange(1,self._solution.n+1),self._solution.F_[:,1], 'b-', label='$F_2$')
        ax2.legend(loc='upper right', fontsize=16)
        ax2.set_title('Coordinate 2')
        ax2.grid()
        
        manager = plt.get_current_fig_manager()
        manager.set_window_title('Graph')
        plt.show()


