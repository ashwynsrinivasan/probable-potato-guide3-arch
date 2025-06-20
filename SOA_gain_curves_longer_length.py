#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 09:08:41 2025

@author: ayan
"""

''' this code is for using the OL SOA model for lengths greater
    than 900um, the SOA model from App notes is for SOA width of 2um
    and length of 900um (440 um + 460um) 
    
    
    
    From Molly: 
    
    To extrapolate to longer SOAs:

    Unsaturated Gain: for your wavelength, temperature, current density, 
    take 3 points that are valid, fit a straight line of G0 vs. length.  
    That is your new G0

    Ps: use the model in the app note for Psat (3dB point) to calculate Ps  
    for a 700um SOA.  Ps is theoretically length-independent, so you can use 
    this for saturated gain

   Wider:

   Multiply Ps by (NewWidth/OldWidth)*0.9

   The 0.9 is a fudge factor, we aren’t really sure if it’s the right number. 
   Theoretically, it should be 1.      '''


import numpy as np
import matplotlib.pyplot as plt

from SOA_model import SOA
from scipy.optimize import newton






''' Get g0 for 3 differnt SOA length and fit st. line '''

## for SOA length beyound 900um
def get_g0(Lsoa_, J_ , wl_, T_):

    # SOA_L = [350e-6, 450e-6, 550e-6, 650e-6, 750e-6, 850e-6] # in m
    SOA_L = [500e-6, 550e-6, 600e-6, 650e-6, 700e-6, 750e-6, 800e-6, 850e-6, 900e-6] # in m, model valid for 500um to 900um length
        
    g0_ = []
    for L in SOA_L:
        
        soa = SOA(T=T_,J=J_,L=L*1e6 - 460,wl=wl_*1e9)
        g0_.append(soa.g0)
        
    slope, intercept = np.polyfit(SOA_L, g0_, deg = 1)  # Returns [slope, intercept]
    g0_new_ = slope * Lsoa_ + intercept
    g0_dB_ = 10*np.log10(g0_)

    # ## plot g0 vs soa length and fit
    # soa_LL = np.linspace(300,900,num=20) *1e-6
    # fitted_g0 = [slope * LL + intercept for LL in soa_LL]
    # fitted_g0_dB = 10*np.log10(fitted_g0)
    
    # fig, a00 = plt.subplots(nrows =1, ncols=1)
    # a00.scatter(np.array(SOA_L)*1e6, g0_, label = 'model')
    # a00.plot(soa_LL*1e6, fitted_g0, color = 'r', label = 'fit')
    # # a00.scatter(np.array(SOA_L)*1e6, g0_dB_, label = 'model')
   
    # a00.set_xlabel('SOA Length (um)')
    # a00.set_ylabel('g0')
    # a00.set_title(f'slope:{slope/1e6 :0.2f}' )
    # a00.grid('True')
    # a00.legend()
        
    return g0_new_

 
## get the output saturation power for Lsoa = 700um
## the saturation power should be independent of length, theoretically

def get_Pos(J_ , wl_, T_ ):
    
    soa = SOA(T=T_, J=J_, L=700 - 460, wl=wl_*1e9)
    return soa.Pos_3dB
    
    


def get_Psat(Pos_3dB_, g0_, Wsoa_): #Calculates Ps on page 6 of tower's document
    # Ps_3dB is the output power 3dB saturation in dBm
    # g0 is the unsaturated gain, linear + unitless
    Pos_3dB_ = 10**(Pos_3dB_/10)  # in mW
    Psat_ = Pos_3dB_ * (g0_-2) / (g0_*np.log(2)) #in mW
    Psat_ = Psat_ * 1e-3 #Psat in W
    
    Psat_ = Psat_ * (Wsoa_/2e-6)*0.9 ## this is from Molly
    return Psat_


def get_gain(Pin_, g0_, Psat_):
    # g0 is unsaturated gain, linear and unitless
    # Pin is input laser power in W
    # Ps is the saturation power value, in W
   
    def f(g):
        return g - g0_ * np.exp( (1-g) * Pin_/Psat_)

    def fprime(g):
        z = Pin_/Psat_
        return 1 + g0_ * z * np.exp(z*(1-g))

    return newton(f, g0_, fprime=fprime, maxiter=10000)




    

# #############################################################################

Lsoa = 1250e-6
Wsoa = 2.7e-6
Tamb = 55
wl = 1310e-9 ## in meters
J_sweep = [3, 4, 5, 6, 7]



''' gain vs Pin for different current density '''

# # J_sweep = [3, 4, 5, 6, 7]
# # J_sweep = [2, 3, 4, 5, 6]
# Pin = np.linspace(-40, 20, 101)  # in dBm
# Pin_Watts  = 10**(Pin/10)*1e-3

# fig, a2 = plt.subplots(nrows =1, ncols=1)
# for J in J_sweep:
    
#     curr = J * 1e7 *  Wsoa * Lsoa
#     g0 = get_g0(Lsoa_ = Lsoa, J_ = J, wl_ = wl, T_ = Tamb)
#     Pos = get_Pos(J_ = J, wl_ = wl, T_ = Tamb )
#     Psat = get_Psat(Pos_3dB_ = Pos, g0_ = g0, Wsoa_ = Wsoa)
    
#     g = []
#     for x in Pin_Watts:
#         gg = get_gain(Pin_ = x, g0_ = g0, Psat_ = Psat)
#         g.append(gg)
    
#     g = np.array(g)
#     g_dB = 10*np.log10(g)
    
#     a2.set_title(f'L_soa = {Lsoa*1e6}um,  W_soa = {Wsoa*1e6}um, gain vs Pin' )
#     a2.plot(Pin, g_dB,label= f'J = {J}kA/cm^2, I = {curr*1e3:0.2f}mA')
#     a2.set_xlabel('Pin (dBm)')
#     a2.set_ylabel('gain (dB)')
#     a2.grid('True', which="both", ls="dashed", color='.7')
#     a2.legend(title = f'T = {Tamb}C')


''' gain vs Pout for different current density '''

# # J_sweep = [3, 4, 5, 6, 7]
# # J_sweep = [5]
# Pin = np.linspace(-40, 20, 101)  # in dBm
# Pin_Watts  = 10**(Pin/10)*1e-3

# fig, a3 = plt.subplots(nrows =1, ncols=1)
# for J in J_sweep:
    
#     curr = J * 1e7 *  Wsoa * Lsoa
#     g0 = get_g0(Lsoa_ = Lsoa, J_ = J, wl_ = wl, T_ = Tamb)
#     Pos = get_Pos(J_ = J, wl_ = wl, T_ = Tamb )
#     Psat = get_Psat(Pos_3dB_ = Pos, g0_ = g0, Wsoa_ = Wsoa)
    
#     g = []
#     Pout_Watts = []
#     for x in Pin_Watts:
#         gg = get_gain(Pin_ = x, g0_ = g0, Psat_ = Psat)
#         g.append(gg)
#         Pout_Watts.append(gg * x)
    
#     g = np.array(g)
#     g_dB = 10*np.log10(g)
#     Pout_mW = np.array(Pout_Watts)*1e3
#     Pout_dBm = 10*np.log10(Pout_mW)
    
#     a3.set_title(f'L_soa = {Lsoa*1e6}um,  W_soa = {Wsoa*1e6}um, gain vs Pin' )
#     a3.plot(Pout_dBm, g_dB,label= f'J = {J}kA/cm^2, I = {curr*1e3:0.2f}mA')
#     a3.set_xlabel('Pout (dBm)')
#     a3.set_ylabel('gain (dB)')
#     a3.grid('True', which="both", ls="dashed", color='.7')
#     a3.legend(title = f'T = {Tamb}C')









''' gain vs wl for different current density '''

# # J_sweep = [3, 4, 5, 6, 7]
# # J_sweep = [2, 3, 4, 5, 6]
# Pin = 0  # in dBm
# Pin_Watts  = 1e-6
# wl_sweep = np.linspace(1260e-9,1350e-9,num=1000)

# fig, a2 = plt.subplots(nrows =1, ncols=1)
# for J in J_sweep:
       
#     g = []
#     curr = J * 1e7 *  Wsoa * Lsoa
#     for wl in wl_sweep:
        
#         g0 = get_g0(Lsoa_ = Lsoa, J_ = J, wl_ = wl, T_ = Tamb)
#         Pos = get_Pos(J_ = J, wl_ = wl, T_ = Tamb )
#         Psat = get_Psat(Pos_3dB_ = Pos, g0_ = g0, Wsoa_ = Wsoa)
#         gg = get_gain(Pin_ = Pin_Watts, g0_ = g0, Psat_ = Psat)
#         g.append(gg)
    
#     g = np.array(g)
#     g_dB = 10*np.log10(g)
    
#     a2.set_title(f'L_soa = {Lsoa*1e6}um,  W_soa = {Wsoa*1e6}um, Unsaturated gain vs wvl' )
#     a2.plot(wl_sweep*1e6, g_dB,label= f'J = {J}kA/cm^2')
#     a2.set_xlabel('Wavelength (nm)')
#     a2.set_ylabel('g0 (dB)')
#     a2.grid('True', which="both", ls="dashed", color='.7')
#     a2.legend(title = f'T = {Tamb}C')





# # #################################### ''' TEMPERATURE SWEEP '''########################################################################


# T_sweep = [35, 55, 80]
# J = 5


''' gain vs wl for different current density '''

# # J_sweep = [3, 4, 5, 6, 7]
# # J_sweep = [2, 3, 4, 5, 6]
# Pin = 0  # in dBm
# Pin_Watts  = 1e-6
# wl_sweep = np.linspace(1260e-9,1350e-9,num=1000)

# fig, a2 = plt.subplots(nrows =1, ncols=1)
# for T in T_sweep:
       
#     g = []
#     curr = J * 1e7 *  Wsoa * Lsoa
#     for wl in wl_sweep:
        
#         g0 = get_g0(Lsoa_ = Lsoa, J_ = J, wl_ = wl, T_ = T)
#         Pos = get_Pos(J_ = J, wl_ = wl, T_ = T )
#         Psat = get_Psat(Pos_3dB_ = Pos, g0_ = g0, Wsoa_ = Wsoa)
#         gg = get_gain(Pin_ = Pin_Watts, g0_ = g0, Psat_ = Psat)
#         g.append(gg)
    
#     g = np.array(g)
#     g_dB = 10*np.log10(g)
    
#     a2.set_title(f'L_soa = {Lsoa*1e6}um,  W_soa = {Wsoa*1e6}um, J = 5kA/cm^2, g0 vs wvl' )
#     a2.plot(wl_sweep*1e6, g_dB,label= f'T = {T}C')
#     a2.set_xlabel('Wavelength (nm)')
#     a2.set_ylabel('g0 (dB)')
#     a2.grid('True', which="both", ls="dashed", color='.7')
#     a2.legend()




''' gain vs Pin for different current density '''

T_sweep = [35, 55, 80]
J = 7
wl = 1310e-9

Pin = np.linspace(-40, 20, 101)  # in dBm
Pin_Watts  = 10**(Pin/10)*1e-3

fig, a2 = plt.subplots(nrows =1, ncols=1)
for T in T_sweep:
    
    curr = J * 1e7 *  Wsoa * Lsoa
    g0 = get_g0(Lsoa_ = Lsoa, J_ = J, wl_ = wl, T_ = T)
    Pos = get_Pos(J_ = J, wl_ = wl, T_ = T )
    Psat = get_Psat(Pos_3dB_ = Pos, g0_ = g0, Wsoa_ = Wsoa)
    
    g = []
    for x in Pin_Watts:
        gg = get_gain(Pin_ = x, g0_ = g0, Psat_ = Psat)
        g.append(gg)
    
    g = np.array(g)
    g_dB = 10*np.log10(g)
    
    a2.set_title(f'L_soa = {Lsoa*1e6}um,  W_soa = {Wsoa*1e6}um, gain vs Pin' )
    a2.plot(Pin, g_dB,label= f'T = {T}C')
    a2.set_xlabel('Pin (dBm)')
    a2.set_ylabel('gain (dB)')
    a2.grid('True', which="both", ls="dashed", color='.7')
    a2.legend(title = f'J = {J}kA/cm^2, I = {curr*1e3:0.2f}mA')


''' gain vs Pout for different current density '''

# T_sweep = [35, 55, 80]
# J = 5
# wl = 1310e-9

# Pin = np.linspace(-40, 20, 101)  # in dBm
# Pin_Watts  = 10**(Pin/10)*1e-3

# fig, a3 = plt.subplots(nrows =1, ncols=1)
# for T in T_sweep:
    
#     curr = J * 1e7 *  Wsoa * Lsoa
#     g0 = get_g0(Lsoa_ = Lsoa, J_ = J, wl_ = wl, T_ = T)
#     Pos = get_Pos(J_ = J, wl_ = wl, T_ = T )
#     Psat = get_Psat(Pos_3dB_ = Pos, g0_ = g0, Wsoa_ = Wsoa)
    
#     g = []
#     Pout_Watts = []
#     for x in Pin_Watts:
#         gg = get_gain(Pin_ = x, g0_ = g0, Psat_ = Psat)
#         g.append(gg)
#         Pout_Watts.append(gg * x)
    
#     g = np.array(g)
#     g_dB = 10*np.log10(g)
#     Pout_mW = np.array(Pout_Watts)*1e3
#     Pout_dBm = 10*np.log10(Pout_mW)
    
#     a3.set_title(f'L_soa = {Lsoa*1e6}um,  W_soa = {Wsoa*1e6}um, J = 5kA/cm^2 gain vs Pin' )
#     a3.plot(Pout_dBm, g_dB,label= f'T = {T}C')
#     a3.set_xlabel('Pout (dBm)')
#     a3.set_ylabel('gain (dB)')
#     a3.grid('True', which="both", ls="dashed", color='.7')
#     a3.legend()







# ################################ New for Europa specs ##########################

# ''' gain vs Pin for different current density '''

# Lsoa = 1250e-6
# Wsoa = 2.7e-6
# Tamb = 55
# # wl = 1310e-9 ## in meters
# wl_sweep = np.array([1318.64,1317.48,1316.33,1315.17,1314.02,1312.87,1311.72,1310.57,1309.43,1308.28,1307.14,1306.01,1304.87,1303.73,1302.60,1301.47])*1e-9

# # wl_sweep = np.array([1310, 1311])*1e-9
 
# J = 7
# curr = J * 1e7 *  Wsoa * Lsoa
# Pin = -10.06  # in dBm
# Pin_Watts  = 10**(Pin/10)*1e-3 ## needs to be a list
# x = Pin_Watts

# fig, a7 = plt.subplots(nrows =1, ncols=1)
# T_sweep = [ 35, 55, 65]
# for Tamb in T_sweep:
    
#     g = []
    
#     for wl in wl_sweep:
        
        
#         g0 = get_g0(Lsoa_ = Lsoa, J_ = J, wl_ = wl, T_ = Tamb)
#         Pos = get_Pos(J_ = J, wl_ = wl, T_ = Tamb )
#         Psat = get_Psat(Pos_3dB_ = Pos, g0_ = g0, Wsoa_ = Wsoa)
        
#         # g = []
#         # for x in Pin_Watts:
#         gg = get_gain(Pin_ = x, g0_ = g0, Psat_ = Psat)
#         g.append(gg)
        
#     g = np.array(g)
#     g_dB = 10*np.log10(g)
    
#     print('Tamb:', Tamb, 'C')
#     print('SOA gain :', g_dB.T, 'dB')
        
#     a7.set_title(f'L_soa = {Lsoa*1e6}um,  W_soa = {Wsoa*1e6}um,Pin = {Pin}dBm' )
#     a7.plot(wl_sweep*1e9, g_dB,marker='o', linestyle='-', label= f'T = {Tamb}C')
#     a7.set_xlabel('Wavelength (dBm)')
#     a7.set_ylabel('gain (dB)')
#     a7.grid('True', which="both", ls="dashed", color='.7')
#     a7.legend(title = f'J = {J}kA/cm^2, I = {curr*1e3:0.2f}mA')





''' gain vs Pin for different current density '''

Lsoa = 1250e-6
Wsoa = 2.7e-6
Tamb = 55
# wl = 1310e-9 ## in meters
wl_sweep = np.array([1318.64,1317.48,1316.33,1315.17,1314.02,1312.87,1311.72,1310.57,1309.43,1308.28,1307.14,1306.01,1304.87,1303.73,1302.60,1301.47])*1e-9

# wl_sweep = np.array([1310, 1311])*1e-9
 


Pin = -5.087 # in dBm
Pin_Watts  = 10**(Pin/10)*1e-3 ## needs to be a list
x = Pin_Watts

fig, a7 = plt.subplots(nrows =1, ncols=1)
J_sweep = [3, 5, 7]
for J in J_sweep:
    
    curr = J * 1e7 *  Wsoa * Lsoa
    g = []
    
    for wl in wl_sweep:
        
        
        g0 = get_g0(Lsoa_ = Lsoa, J_ = J, wl_ = wl, T_ = Tamb)
        Pos = get_Pos(J_ = J, wl_ = wl, T_ = Tamb )
        Psat = get_Psat(Pos_3dB_ = Pos, g0_ = g0, Wsoa_ = Wsoa)
        
        # g = []
        # for x in Pin_Watts:
        gg = get_gain(Pin_ = x, g0_ = g0, Psat_ = Psat)
        g.append(gg)
        
    g = np.array(g)
    g_dB = 10*np.log10(g)
    
    print('Tamb:', Tamb, 'C')
    print('SOA gain :', g_dB.T, 'dB')
        
    a7.set_title(f'L_soa = {Lsoa*1e6}um,  W_soa = {Wsoa*1e6}um,Pin = {Pin}dBm' )
    a7.plot(wl_sweep*1e9, g_dB,marker='o', linestyle='-', label= f'J = {J}kA/cm^2, I = {curr*1e3:0.2f}mA')
    a7.set_xlabel('Wavelength (dBm)')
    a7.set_ylabel('gain (dB)')
    a7.grid('True', which="both", ls="dashed", color='.7')
    a7.legend(title = f'T = {Tamb}C')

