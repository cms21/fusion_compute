import numpy as np
import matplotlib.pyplot as plt
import math

def plot_2Dhist(config_filename='ionorb_stl2d_boris.config'):
   
   print("Reading config file: %s ..." % config_filename)

   ## defaults:
   out_fname = "./out.hits.els.txt"
   dPhi = 0.0 ## radian shift of stl file coord system
   colormap = 'plasma'
   SignChange = 'F'
   beampower = 1.0

   with open(config_filename) as file:
      config = file.readlines()

   for line in config:
      words = line.split()
      if len(words) == 2:
         if words[0] == 'birth_fname':
            birth_fname = words[1].strip('\"')
         if words[0] == 'out_fname':
            out_fname = words[1].strip('\"')
         if words[0] == 'dPhi':
            dPhi = numpy.fromstring( words[1], dtype=float, sep=" " )
            dPhi = 0.0
         if words[0] == 'colormap':
            colormap = words[1]
         if words[0] == 'PhiSignChange':
            SignChange = words[1]
         if words[0] == 'beampower':
            beampower = np.fromstring( words[1], dtype=float, sep =" " )

   # radius in meters, outside of which are plotted
   # r_zero is 1.6955
   rcutoff = 1.5

   print('Loading birth file:',birth_fname)
   nheader = 6
   with open(birth_fname,"r") as f:
      nheader = 1
      line = f.readline()
      while line != "<start-of-data>\n":
         nheader += 1
         line = f.readline()

   birth = np.loadtxt( birth_fname, skiprows=nheader)
   Nbirth = len(birth)

   # NOTE that dPhi and the sign change are not acutally used,
   # There is no real reason to read the config file any more
   # except it can take a colormap input
   #
   #print " STL origin shift :", dPhi
   #print "Sign change between RHCS and Bt? :",SignChange
   print('Loading hit file  :',out_fname)
   hitdata = np.loadtxt(out_fname, skiprows=1)
   ##  columns are
   #   0 = ID ?
   #   1 = time [s]
   #   2 = calculation step
   #   3 = wall id [1 indexed]!
   #   4 = r
   #   5 = phi: -pi to pi
   #   6 = z
   #   7 = v_r
   #   8 = v_phi
   #   9 = v_z

   zmin = -1.4
   zmax = 1.4
   nparticles = 0

   for n in np.arange(hitdata.shape[0]):
      if hitdata[n,4] > rcutoff:
         nparticles += 1

   print(" particles that hit the wall r > %i: %i" % (rcutoff, nparticles))
   print(" Total particles in birth file     : %i" % (Nbirth))

   rbins= int(0.5*np.sqrt(nparticles))
   pbins= 4*rbins

   # phi - z projection
   #z = np.zeros(nparticles)
   #P = np.zeros(nparticles)
   #w = np.zeros(nparticles)

   z = []
   P = []

   for n in np.arange(nparticles):
      if hitdata[n,4] > rcutoff: #CMS: question: for particles below the cutoff, do we not care about them?
         z.append(hitdata[n,6])
         # account for the file being -pi to pi, AND origin angle of stl file
         #
         angle = hitdata[n,5]

         if angle < 0.0:
            angle = angle + 2.0*np.pi

         ## account for the origin angle of the stl file
         P.append(angle*180.0/np.pi)
         
   P = np.array(P)
   z = np.array(z)
   w = np.zeros_like(P)

   pmin = min(P)
   pmax = max(P)
   # estimating outerwall at 2.4m
   binarea = 2*np.pi*2.4 * (zmax -zmin) / (pbins*rbins)

   for i in np.arange(len(w)):
      w[i] = 1.0 * beampower / Nbirth / binarea
         
   flux = plt.hist2d(P, z, bins=[pbins,rbins], range=[[pmin,pmax],[zmin,zmax]], weights=w, norm=mpl.colors.LogNorm(), cmap=colormap)
   max_flux= np.amax(flux[0])
   index = np.where(flux[0] == max_flux)
   max_P_loc = flux[1][index[0][0]]
   max_z_loc = flux[2][index[1][0]]

   print(f"Max energy wall flux is {max_flux} at Phi={max_P_loc} z={max_z_loc}")
   plt.xlabel('RH degrees -- same as 3D wall output, NOT DIII-D coords')
   plt.ylabel('Tokamak z [meters]')
   plt.title('Approx. deposited power [MW/m^2]')
   plt.colorbar()


   plt.savefig("heatmap.png")
   return max_flux, max_P_loc, max_z_loc

def fullorb(fullorb_fname,dir="z"):
   plt.figure()
   oth_z = True
   oth_r = True

   if (dir=='p'):
      oth_z = False
      oth_r = True
   elif (dir=='z'):
      oth_z = True
      oth_r = True
   elif (dir=='w'):
      oth_z = True
      oth_r = False
   else:
      print("Usage:")
      print(" plot_fullorb.py [-p|-z|-w] <fname>")
      raise Exception("Usage: plot_fullorb.py [-p|-z|-w] <fname>")

   print("Processing file: %s"%fullorb_fname)

   try:
      with open(fullorb_fname) as f:
         lines = f.readlines()
   except Exception as e:
      print("ERROR: File not found: %s"%fullorb_fname)
      print("")
      print("Usage:")
      print(" plot_fullorb.py <fname>")
      raise Exception(e)

   if oth_z:
      if oth_r:
         print("Plotting R vs Z")
      else:
         print("Plotting Phi vs Z")
   else:
      print("Plotting R vs Phi")

   colors = np.zeros(len(lines)-1)

   r = np.zeros(len(lines)-1)
   oth =  np.zeros(len(lines)-1)

   maxrp = 0.0
   i = 0
   for line in lines:
      i = i+1
      if i==1:
         continue

      larr = line.split()
      r_f = float(larr[2])
      p_f = float(larr[3])
      z_f = float(larr[4])

      if (oth_z):
         colors[i-2] = i
         if oth_r:
            r[i-2] = r_f
         else:
            r[i-2] = p_f
         oth[i-2] = z_f
      else:
         colors[i-2] = z_f
         r[i-2] = r_f * math.sin(p_f)
         oth[i-2] = r_f * math.cos(p_f)
         maxrp=max(maxrp,abs(r[i-2]))
         maxrp=max(maxrp,abs(oth[i-2]))

   plt.scatter(r, oth,c=colors)
   if oth_z:
      if oth_r:
         plt.xlabel('R')
      else:
         plt.xlabel('Phi')
      plt.ylabel('Z')
   else:
      plt.xlabel('R * sin(Phi)')
      plt.ylabel('R * cos(Phi)')
      plt.xlim(maxrp*-1.05,maxrp*1.05)
      plt.ylim(maxrp*-1.05,maxrp*1.05)
   plt.savefig(f"fullorb_{dir}.png")


def hits(hits_fname,dir="z"):
   plt.figure()

   oth_z = True
   oth_r = True
   
   if (dir=='p'): 
      oth_z = False
      oth_r = True
   elif (dir=='z'):
      oth_z = True
      oth_r = True
   elif (dir=='w'):
      oth_z = True
      oth_r = False
   else:
      print("Usage:")
      print(" plot_hits.py [-p|-z|-w] <fname>")
      raise Exception("Usage: plot_hits.py [-p|-z|-w] <fname>")

   print("Processing file: %s"%hits_fname)

   try:
      with open(hits_fname) as f:
         lines = f.readlines()
   except Exception as e:
      print("ERROR: File not found: %s"%hits_fname)
      print("")
      print("Usage:")
      print(" plot_hits.py <fname>")
      raise Exception(e)

   if oth_z:
      if oth_r:
         print("Plotting R vs Z")
      else:
         print("Plotting Phi vs Z")
   else:
      print("Plotting R vs Phi")

   colors = np.zeros(len(lines)-1)

   r = np.zeros(len(lines)-1)
   oth =  np.zeros(len(lines)-1)

   i = 0
   for line in lines:
      i = i+1
      if i==1:
         continue

      larr = line.split()
      r_f = float(larr[4])
      p_f = float(larr[5])
      z_f = float(larr[6])

      if oth_z:
         colors[i-2] = i
      else:
         colors[i-2] = z_f


      if (oth_z):
         if oth_r:
            r[i-2] = r_f
         else:
            r[i-2] = p_f
         oth[i-2] = z_f
      else:
         r[i-2] = r_f * math.sin(p_f)
         oth[i-2] = r_f * math.cos(p_f)


   plt.scatter(r, oth,c=colors)
   if oth_z:
      if oth_r:
         plt.xlabel('R')
      else:
         plt.xlabel('Phi')
      plt.ylabel('Z')
   else:
      plt.xlabel('sin(Phi)')
      plt.ylabel('cos(Phi)')
   plt.savefig(f"hits_plot_{dir}.png")

def make_all_plots(fname): 
   try:
      for dir in ["p","z","w"]:
         hits(fname,dir=dir)
         fullorb(fname,dir=dir)
   except Exception as e:
      raise Exception(e)
      

try:
   make_all_plots("../test_compute/out.his.els.txt")
except Exception as e:
   print(e)