import argparse
import numpy as np
from PIL import Image

def normalizeStaining(args):
    ''' Normalize staining appearence of H&E stained images
    
    Example use:
        see test.py
        
    Input:
        I: RGB input image
        Io: (optional) transmitted light intensity
        
    Output:
        Inorm: normalized image
        H: hematoxylin image
        E: eosin image
    
    Reference: 
        A method for normalizing histology slides for quantitative analysis. M.
        Macenko et al., ISBI 2009
    '''
         
    img = np.array(Image.open(args.imageFile))
    
    HERef = np.array([[0.5626, 0.2159],
                      [0.7201, 0.8012],
                      [0.4062, 0.5581]])
        
    maxCRef = np.array([1.9705, 1.0308])
    
    # define height and width of image
    h, w, c = img.shape
    
    # reshape image
    rimg = np.reshape(img.astype(np.float), (-1,3))
    
    # calculate optical density
    OD = -np.log((rimg+1)/args.Io)
    
    # remove transparent pixels
    ODhat = np.array([i for i in OD if not any(i<args.beta)])
        
    # compute eigenvectors (inverse transpose of )
    eigvals, eigvecs = np.linalg.eigh(np.cov(ODhat.T))
    eigvecs *= -1
    
    #project on the plane spanned by the eigenvectors corresponding to the two 
    # largest eigenvalues    
    That = ODhat.dot(eigvecs[:,1:3])
    
    phi = np.arctan2(That[:,1],That[:,0])
    
    minPhi = np.percentile(phi, args.alpha)
    maxPhi = np.percentile(phi, 100-args.alpha)
    
    vMin = eigvecs[:,1:3].dot(np.array([(np.cos(minPhi), np.sin(minPhi))]).T)
    vMax = eigvecs[:,1:3].dot(np.array([(np.cos(maxPhi), np.sin(maxPhi))]).T)
    
    # a heuristic to make the vector corresponding to hematoxylin first and the 
    # one corresponding to eosin second
    if vMin[0] > vMax[0]:
        HE = np.array((vMin[:,0], vMax[:,0])).T
    else:
        HE = np.array((vMax[:,0], vMin[:,0])).T
    
    # rows correspond to channels (RGB), columns to OD values
    Y = np.reshape(OD, (-1, 3)).T
    
    # determine concentrations of the individual stains
    C = np.linalg.lstsq(HE,Y)[0]
    
    # normalize stain concentrations
    maxC = np.array([np.percentile(C[0,:], 99), np.percentile(C[1,:],99)])
    C2 = np.array([C[:,i]/maxC*maxCRef for i in range(C.shape[1])]).T
    
    # recreate the image using reference mixing matrix
    
    Inorm = np.multiply(args.Io, np.exp(-HERef.dot(C2)))
    Inorm[Inorm>255] = 255
    Inorm = np.reshape(Inorm.T, (h, w, 3)).astype(np.uint8)    
    Image.fromarray(Inorm).save(args.saveFile)
    
    return Inorm
    
    
if __name__=='__main__':
    
    parser = argparse.ArgumentParser(description='train NEMO model')
    parser.add_argument('--imageFile', type=str, default='example1.tif', help='RGB image file')
    parser.add_argument('--saveFile', type=str, default='output.png', help='save file')
    parser.add_argument('--Io', type=int, default=240)
    parser.add_argument('--alpha', type=float, default=1)
    parser.add_argument('--beta', type=float, default=0.15)
    args = parser.parse_args()
    
    normalizeStaining(args)