import numpy as np
#定義Symbol名稱
WW = 0
C1 = 1
C2 = 2
C3 = 3
M1 = 4
M2 = 5
M3 = 6
M4 = 7
M5 = 8
M6 = 9
MY = 10
A = 11
K = 12
Q = 13
J = 14
TE = 15
NI = 16
WS = np.full((17,13),-1,np.int8)
#WW
WS[0][0] = WW
WS[0][1] = M1
WS[0][2] = M2
WS[0][3] = M3
WS[0][4] = M4
WS[0][5] = M5
WS[0][6] = M6
WS[0][7] = A
WS[0][8] = K
WS[0][9] = Q
WS[0][10] = J
WS[0][11] = TE
WS[0][12] = NI
#C1
WS[1][0] = C1
#C2
WS[2][0] = C2
#C3
WS[3][0] = C3
#M1
WS[4][0] = WW
WS[4][1] = M1
#M2
WS[5][0] = WW
WS[5][1] = M2
#M3
WS[6][0] = WW
WS[6][1] = M3
#M4
WS[7][0] = WW
WS[7][1] = M4
#M5
WS[8][0] = WW
WS[8][1] = M5
#M6
WS[9][0] = WW
WS[9][1] = M6
#MY
WS[10][0] = MY
#A
WS[11][0] = WW
WS[11][1] = A
#K
WS[12][0] = WW
WS[12][1] = K
#Q
WS[13][0] = WW
WS[13][1] = Q
#J
WS[14][0] = WW
WS[14][1] = J
#TE
WS[15][0] = WW
WS[15][1] = TE
#NI
WS[16][0] = WW
WS[16][1] = NI