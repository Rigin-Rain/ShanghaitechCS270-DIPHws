import cv2
from scipy.fftpack import dct, idct
import scipy
import numpy as np
import os
import matplotlib.pyplot as plt
from collections import Counter, OrderedDict

Y_table = [[16, 11, 10, 16, 24, 40, 51, 61],
           [12, 12, 14, 19, 26, 58, 60, 55],
           [14, 13, 16, 24, 40, 57, 69, 56],
           [14, 17, 22, 29, 51, 87, 80, 62],
           [18, 22, 37, 56, 68 ,109 ,103 ,77],
           [24, 35, 55, 64, 81 ,104 ,113 ,92],
           [49, 64, 78, 87, 103, 121, 120, 101],
           [72, 92, 95, 98, 112, 100, 103, 99]]
# read the image and determine the row,col of the image (512x512)
img = cv2.imread("hw2_files\Q1\lena.tiff")
row, col, _ = img.shape
print("row: ",row, "col: ",col)

row_8,col_8 =row//8,col//8

cv2.imshow("Original Image",img)
cv2.waitKey(0)

ycbcr = cv2.cvtColor(img, cv2.COLOR_BGR2YCR_CB)
cv2.imshow("YCBCR Image",ycbcr.astype(np.uint8))
cv2.waitKey(0)

# test code to see if the image converting to YCRCB is broken
bgr = cv2.cvtColor(ycbcr, cv2.COLOR_YCrCb2BGR)
cv2.imshow("Restored RGB Image",bgr)
cv2.waitKey(0)
cv2.destroyAllWindows()

def Cut_64Blocks(img):
    blocks = np.zeros((row_8, col_8, 8, 8, 3),dtype = np.int16)
    for i in range (row_8):
        for j in range (col_8):
            blocks[i][j] = img[i*8:(i+1)*8,j*8:(j+1)*8]
    return np.asarray(blocks)

def DCTOnBlocks(blocks):
    dctBlocks = np.zeros((row_8,col_8,8,8,3))
    for i in range(row_8):
        for j in range(col_8):
            dct_b = np.zeros((8,8,3))
            for alpha in range(3):
               b = blocks[i][j][:,:,alpha]
               dct_b[:,:,alpha] = dct(dct(b.T, norm = 'ortho').T,norm = 'ortho')
            dctBlocks[i][j] = dct_b
    return dctBlocks

blocks = Cut_64Blocks(ycbcr)
print(blocks[0][0][:,:,1])
dctBlocks = DCTOnBlocks(blocks)

qDctBlocks = (dctBlocks[:,:,:,:,1]/Y_table).round().astype(np.int16)
################################################
def zigZag(block):
  lines=[[] for i in range(8+8-1)] 
  for y in range(8): 
    for x in range(8): 
      i=y+x 
      if(i%2 ==0): 
          lines[i].insert(0,block[y][x]) 
      else:  
          lines[i].append(block[y][x]) 
  return np.asarray([coefficient for line in lines for coefficient in line])
print(qDctBlocks[0][0])
testZigzag_00 = zigZag(qDctBlocks[0][0])

def TruncateEndZeros(zigzagAC):
    index = len(zigzagAC) - 1
    truncated = []
    while index >= 0:
        if zigzagAC[index] != 0:
            # print("FOUND: ",index)
            break
        index -= 1
    for i in range(index+1):
        truncated.append(zigzagAC[i])
    return truncated

# testTrun = TruncateEndZeros(zigZag(qDctBlocks[0][3]))
# print("Truncated :",testTrun)

def CollectSymbols(qDctBlocks):
    symbols = []
    for i in range(row_8):
        for j in range(col_8):
            symbols += TruncateEndZeros(zigZag(qDctBlocks[i][j])[1:])
    return symbols

symbols = CollectSymbols(qDctBlocks)
# print(symbols)
print("MIN",min(symbols))
min_symbols = min(symbols) - 1 if min(symbols) < 0 else min(symbols) + 1
print(min_symbols)

def CalculateProbabilities(symbols):
    counts = dict(Counter([str(s) for s in symbols]))
    probDict = dict(sorted(counts.items(), key=lambda item: item[1]))
    for key in probDict:
        probDict[key] /= float(len(symbols))
    return probDict

probDict = CalculateProbabilities(symbols)
print(probDict)
print(len(probDict))
print(sum(probDict.values()))

def GenHuffmanDict(p):
    '''Return a Huffman code for an ensemble with distribution p.'''
    # print(sum(p.values()))
    # print(p)

    # Base case of only two symbols, assign 0 or 1 arbitrarily
    if(len(p) == 2):
        return dict(zip(p.keys(), ['0', '1']))

    # Create a new distribution by merging lowest prob. pair
    p_prime = p.copy()
    a1, a2 = lowest_prob_pair(p)
    p1, p2 = p_prime.pop(a1), p_prime.pop(a2)
    p_prime[a1 + a2] = p1 + p2
    

    # Recurse and construct code on new distribution
    c = GenHuffmanDict(p_prime)
    ca1a2 = c.pop(a1 + a2)
    c[a1], c[a2] = ca1a2 + '0', ca1a2 + '1'

    return c

def lowest_prob_pair(p):
    '''Return pair of symbols from distribution p with lowest probabilities.'''
    assert(len(p) >= 2) # Ensure there are at least 2 symbols in the dist.

    sorted_p = sorted(p.items(), key=lambda item: item[1])
    return sorted_p[0][0], sorted_p[1][0]

huffmanCodeDict = GenHuffmanDict(probDict)
print(huffmanCodeDict)
print(len(huffmanCodeDict))

