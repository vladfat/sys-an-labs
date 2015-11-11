__author__ = 'strike'
from copy import deepcopy

from scipy import special
from openpyxl import Workbook

from lab_3.system_solve import *


class Solve(object):
    OFFSET = 1e-10

    def __init__(self,d):
        self.n = d['samples']
        self.dim = d['dimensions']
        self.filename_input = d['input_file']
        self.filename_output = d['output_file']
        self.deg = list(map(lambda x:x+1,d['degrees'])) # on 1 more because include 0
        self.weights = d['weights']
        self.poly_type = d['poly_type']
        self.splitted_lambdas = d['lambda_multiblock']
        self.norm_error = 0.0
        self.eps = 1E-8
        self.error = 0.0

    def define_data(self):
        f = open(self.filename_input, 'r')
        # all data from file_input in float
        self.datas = [list(map(lambda x:float(x),f.readline().split())) for i in range(self.n)]
        self.datas = np.matrix(self.datas)
        # list of sum degrees [ 3,1,2] -> [3,4,6]
        self.dim_integral = [sum(self.dim[:i + 1]) for i in range(len(self.dim))]

    def _minimize_equation(self, A, b, type='cjg'):
        """
        Finds such vector x that |Ax-b|->min.
        :param A: Matrix A
        :param b: Vector b
        :return: Vector x
        """
        if type == 'lsq':
            return np.linalg.lstsq(A,b)[0]
        elif type == 'cjg':
            return conjugate_gradient_method(A.T*A, A.T*b, self.eps)
        elif type == 'cjg2':
            return conjugate_gradient_method_v2(A.T*A, A.T*b, self.eps)
        elif type == 'cjg3':
            return conjugate_gradient_method_v3(A.T*A, A.T*b, self.eps)

    def norm_data(self):
        '''
        norm vectors value to value in [0,1]
        :return: float number in [0,1]
        '''
        n,m = self.datas.shape
        vec = np.ndarray(shape=(n,m),dtype=float)
        for j in range(m):
            minv = np.min(self.datas[:,j])
            maxv = np.max(self.datas[:,j])
            for i in range(n):
                vec[i,j] = (self.datas[i,j] - minv)/(maxv - minv)
        self.data = np.matrix(vec)

    def define_norm_vectors(self):
        '''
        buile matrix X and Y
        :return:
        '''
        X1 = self.data[:,:self.dim_integral[0]]
        X2 = self.data[:,self.dim_integral[0]:self.dim_integral[1]]
        X3 = self.data[:, self.dim_integral[1]:self.dim_integral[2]]
        #matrix of vectors i.e.X = [[X11,X12],[X21],...]
        self.X = [X1, X2, X3]
        #number columns in matrix X
        self.mX = self.dim_integral[2]
        # matrix, that consists of i.e. Y1,Y2
        self.Y = self.data[:, self.dim_integral[2]:self.dim_integral[3]]
        self.Y_ = self.datas[:, self.dim_integral[2]:self.dim_integral[3]]
        self.X_ = [self.datas[:,:self.dim_integral[0]], self.datas[:,self.dim_integral[0]:self.dim_integral[1]],
                   self.datas[:,self.dim_integral[1]:self.dim_integral[2]]]

    def built_B(self):
        def B_average():
            '''
            Vector B as average of max and min in Y. B[i] =max Y[i,:]
            :return:
            '''
            b = np.tile((self.Y.max(axis=1) + self.Y.min(axis=1))/2,(1,self.dim[3]))
            return b

        def B_scaled():
            '''
            Vector B  = Y
            :return:
            '''
            return deepcopy(self.Y)

        if self.weights == 'average':
            self.B = B_average()
        elif self.weights == 'scaled':
            self.B = B_scaled()
        else:
            exit('B not defined')
        self.B_log = np.log(self.B + 1 + self.OFFSET)

    def poly_func(self):
        '''
        Define function to polynomials
        :return: function
        '''
        if self.poly_type == 'sh_cheb_doubled':
            self.poly_f = special.eval_sh_chebyt
        elif self.poly_type == 'cheb':
            self.poly_f = special.eval_chebyt
        elif self.poly_type == 'sh_cheb_2':
            self.poly_f = lambda deg, x: special.eval_sh_chebyu(deg, x) / 2**deg

    def built_A(self):
        '''
        built matrix A on shifted polynomials Chebysheva
        :param self.p:mas of deg for vector X1,X2,X3 i.e.
        :param self.X: it is matrix that has vectors X1 - X3 for example
        :return: matrix A as ndarray
        '''

        def mA():
            '''
            :param X: [X1, X2, X3]
            :param p: [p1,p2,p3]
            :return: m = m1*p1+m2*p2+...
            '''
            m = 0
            for i in range(len(self.X)):
                m+= self.X[i].shape[1]*(self.deg[i]+1)
            return m

        def coordinate(v,deg):
            '''
            :param v: vector
            :param deg: chebyshev degree polynom
            :return:column with chebyshev value of coordiate vector
            '''
            c = np.ndarray(shape=(self.n,1), dtype = float)
            for i in range(self.n):
                c[i,0] = self.poly_f(deg, v[i])
            return c

        def vector(vec, p):
            '''
            :param vec: it is X that consist of X11, X12, ... vectors
            :param p: max degree for chebyshev polynom
            :return: part of matrix A for vector X1
            '''
            n, m = vec.shape
            a = np.ndarray(shape=(n,0),dtype = float)
            for j in range(m):
                for i in range(p):
                    ch = coordinate(vec[:,j],i)
                    a = np.append(a,ch,1)
            return a

        #k = mA()
        A = np.ndarray(shape = (self.n,0),dtype =float)
        for i in range(len(self.X)):
            vec = vector(self.X[i],self.deg[i])
            A = np.append(A, vec,1)
        self.A = np.matrix(A)
        self.A_log = np.log(self.A + 1 + self.OFFSET)

    def lamb(self):
        lamb = np.ndarray(shape = (self.A.shape[1],0), dtype = float)
        for i in range(self.dim[3]):
            if self.splitted_lambdas:
                boundary_1 = self.deg[0] * self.dim[0]
                boundary_2 = self.deg[1] * self.dim[1] + boundary_1
                lamb1 = self._minimize_equation(self.A_log[:, :boundary_1], self.B_log[:, i])
                lamb2 = self._minimize_equation(self.A_log[:, boundary_1:boundary_2], self.B_log[:, i])
                lamb3 = self._minimize_equation(self.A_log[:, boundary_2:], self.B_log[:, i])
                lamb = np.append(lamb, np.concatenate((lamb1, lamb2, lamb3)), axis=1)
            else:
                lamb = np.append(lamb, self._minimize_equation(self.A_log, self.B_log[:, i]), axis=1)
        self.Lamb = np.matrix(lamb) #Lamb in full events

    def psi(self):
        def built_psi(lamb):
            '''
            return matrix xi1 for b1 as matrix
            :param A:
            :param lamb:
            :param p:
            :return: matrix psi, for each Y
            '''
            psi = np.ndarray(shape=(self.n, self.mX), dtype = float)
            q = 0 #iterator in lamb and A
            l = 0 #iterator in columns psi
            for k in range(len(self.X)): # choose X1 or X2 or X3
                for s in range(self.X[k].shape[1]):# choose X11 or X12 or X13
                    for i in range(self.X[k].shape[0]):
                            psi[i,l] = self.A_log[i,q:q+self.deg[k]]*lamb[q:q+self.deg[k], 0]
                    q+=self.deg[k]
                    l+=1
            return np.matrix(psi)

        self.Psi_log = [] #as list because psi[i] is matrix(not vector)
        self.Psi = list()
        for i in range(self.dim[3]):
            self.Psi_log.append(built_psi(self.Lamb[:,i]))
            self.Psi.append(np.exp(self.Psi_log[i]) - 1)

    def built_a(self):
        self.a = np.ndarray(shape=(self.mX,0), dtype=float)
        for i in range(self.dim[3]):
            a1 = self._minimize_equation(self.Psi_log[i][:, :self.dim_integral[0]],
                                         np.log(self.Y[:, i] + 1 + self.OFFSET))
            a2 = self._minimize_equation(self.Psi_log[i][:, self.dim_integral[0]:self.dim_integral[1]],
                                         np.log(self.Y[:, i] + 1 + self.OFFSET))
            a3 = self._minimize_equation(self.Psi_log[i][:, self.dim_integral[1]:],
                                         np.log(self.Y[:, i] + 1 + self.OFFSET))
            # temp = self._minimize_equation(self.Psi[i], self.Y[:, i])
            # self.a = np.append(self.a, temp, axis=1)
            self.a = np.append(self.a, np.vstack((a1, a2, a3)), axis=1)

    def built_F1i(self, psi, a):
            '''
            not use; it used in next function
            :param psi: matrix psi (only one
            :param a: vector with shape = (6,1)
            :param degf:  = [3,4,6]//fibonachi of deg
            :return: matrix of (three) components with F1 F2 and F3
            '''
            m = len(self.X) # m  = 3
            F1i = np.ndarray(shape = (self.n,m),dtype = float)
            k = 0 # point of begining columnt to multipy
            for j in range(m): # 0 - 2
                for i in range(self.n): # 0 - 49
                    F1i[i,j] = psi[i,k:self.dim_integral[j]]*a[k:self.dim_integral[j],0]
                k = self.dim_integral[j]
            return np.matrix(F1i)

    def built_Fi(self):
        self.Fi_log = []
        self.Fi = list()
        for i in range(self.dim[3]):
            self.Fi_log.append(self.built_F1i(self.Psi_log[i],self.a[:,i]))
            self.Fi.append(np.exp(self.Fi_log[-1]) - 1)

    def built_c(self):
        self.c = np.ndarray(shape = (len(self.X),0),dtype = float)
        for i in range(self.dim[3]):
            self.c = np.append(self.c, self._minimize_equation(self.Fi_log[i], np.log(self.Y[:, i] + 1 + self.OFFSET))
                               ,axis=1)

    def built_F(self):
        F = np.ndarray(self.Y.shape, dtype = float)
        for j in range(F.shape[1]):#2
            for i in range(F.shape[0]): #50
                F[i,j] = self.Fi_log[j][i,:]*self.c[:,j]
        self.F_log = np.matrix(F)
        self.F = np.exp(self.F_log) - 1
        self.norm_error = []
        for i in range(self.Y.shape[1]):
            self.norm_error.append(np.linalg.norm(self.Y[:,i] - self.F[:,i],np.inf))

    def built_F_(self):
        minY = self.Y_.min(axis=0)
        maxY = self.Y_.max(axis=0)
        self.F_ = np.multiply(self.F,maxY - minY) + minY
        self.error = []
        for i in range(self.Y_.shape[1]):
            self.error.append(np.linalg.norm(self.Y_[:,i] - self.F_[:,i],np.inf))

    def save_to_file(self):
        wb = Workbook()
        #get active worksheet
        ws = wb.active

        l = [None]

        ws.append(['Input data: X'])
        for i in range(self.n):
             ws.append(l+self.datas[i,:self.dim_integral[3]].tolist()[0])
        ws.append([])

        ws.append(['Input data: Y'])
        for i in range(self.n):
             ws.append(l+self.datas[i,self.dim_integral[2]:self.dim_integral[3]].tolist()[0])
        ws.append([])

        ws.append(['X normalized:'])
        for i in range(self.n):
             ws.append(l+self.data[i,:self.dim_integral[2]].tolist()[0])
        ws.append([])

        ws.append(['Y normalized:'])
        for i in range(self.n):
             ws.append(l+self.data[i,self.dim_integral[2]:self.dim_integral[3]].tolist()[0])
        ws.append([])

        ws.append(['matrix B:'])
        for i in range(self.n):
             ws.append(l+self.B[i].tolist()[0])
        ws.append([])

        ws.append(['matrix A:'])
        for i in range(self.A.shape[0]):
             ws.append(l+self.A[i].tolist()[0])
        ws.append([])

        ws.append(['matrix Lambda:'])
        for i in range(self.Lamb.shape[0]):
             ws.append(l+self.Lamb[i].tolist()[0])
        ws.append([])

        for j in range(len(self.Psi)):
             s = 'matrix Psi%i:' %(j+1)
             ws.append([s])
             for i in range(self.n):
                  ws.append(l+self.Psi[j][i].tolist()[0])
             ws.append([])

        ws.append(['matrix a:'])
        for i in range(self.mX):
             ws.append(l+self.a[i].tolist()[0])
        ws.append([])

        for j in range(len(self.Fi)):
             s = 'matrix F%i:' %(j+1)
             ws.append([s])
             for i in range(self.Fi[j].shape[0]):
                  ws.append(l+self.Fi[j][i].tolist()[0])
             ws.append([])

        ws.append(['matrix c:'])
        for i in range(len(self.X)):
             ws.append(l+self.c[i].tolist()[0])
        ws.append([])

        ws.append(['Y rebuilt normalized :'])
        for i in range(self.n):
             ws.append(l+self.F[i].tolist()[0])
        ws.append([])

        ws.append(['Y rebuilt normalized :'])
        for i in range(self.n):
             ws.append(l+self.F_[i].tolist()[0])
        ws.append([])

        ws.append(['Error normalized (Y - F)'])
        ws.append(l + self.norm_error)

        ws.append(['Error (Y_ - F_))'])
        ws.append(l+self.error)

        wb.save(self.filename_output)
    
    def prepare(self):
        self.define_data()
        self.norm_data()
        self.define_norm_vectors()
        self.built_B()
        self.poly_func()
        self.built_A()
        self.lamb()
        self.psi()
        self.built_a()
        self.built_Fi()
        self.built_c()
        self.built_F()
        self.built_F_()
        self.save_to_file()