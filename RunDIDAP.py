#!/usr/bin/env python
import os
from DDFacet.Other import logger
log=logger.getLogger("DDPipeASKAP")
from DDFacet.Other import ModColor

MaxFacetSize=1.
MinFacetSize=MaxFacetSize/10.

def os_exec(ss):
    print>>log,ModColor.Str("==========================================================")
    print>>log,ModColor.Str("Executing %s"%ss)
    print>>log,ModColor.Str("==========================================================")
    os.system(ss)

def RunDDF(MSName,
           OutBaseImageName,
           MaskName=None,
           SolsFile=None,SOLSDIR="SOLSDIR",
           InitDicoModel=None,NMajorIter=5,
           WeightColName=None,
           MaskAuto=True,
           FromLastResid=False,PeakFactor=0.003,Robust=-1.):
        
    ss="DDF.py --Data-MS %s --Image-Cell 2. --Image-NPix 12000 --Output-Mode Clean --Data-ColName DATA --Freq-NBand 2 --Freq-NDegridBand 10 --Facets-NFacet 7 --Weight-ColName None --Cache-Reset 0 --Deconv-Mode SSD --Output-RestoringBeam 11. --Output-Name %s --Deconv-CycleFactor 0. --Deconv-PeakFactor %s --Facets-DiamMin %f --Facets-DiamMax %f --Deconv-MaxMajorIter %i --Weight-Robust %f"%(MSName,OutBaseImageName,PeakFactor,MinFacetSize,MaxFacetSize,NMajorIter,Robust)

    if MaskAuto:
        ss+=" --Mask-Auto 1"
        
    
    if MaskName is not None:
        ss+=" --Mask-External %s"%MaskName
        
    if InitDicoModel is not None:
        ss+="  --Predict-InitDicoModel %s"%InitDicoModel

    if SolsFile is not None:
        ss+=" --DDESolutions-DDSols %s --DDESolutions-SolsDir %s"%(SolsFile,SOLSDIR)

    if WeightColName is not None:
         ss+=" --Weight-ColName %s"%WeightColName


    if FromLastResid:
        ss+=" --Cache-PSF force --Cache-Dirty forceresidual"
    OutName="%s.app.restored.fits"%OutBaseImageName
    if os.path.isfile(OutName):
        print>>log,ModColor.Str("%s exists, skippinf DDF step:"%OutName)
        print>>log,ModColor.Str("    %s"%ss)
        return
        
    os_exec(ss)

def RunKMS(MSName,BaseImageName,OutSolsName,SOLSDIR="SOLSDIR",NodesFile=None,DicoModel=None):
    ss="kMS.py --MSName %s --SolverType KAFCA --PolMode Scalar --BaseImageName %s --dt 5 --NCPU 40 --InCol DATA --UVMinMax=0.5,1000. --SolsDir=%s --NChanSols 10 --BeamMode None --DDFCacheDir=. --MinFacetSize %f --MaxFacetSize %f  --TChunk 2.1"%(MSName,BaseImageName,SOLSDIR,MinFacetSize,MaxFacetSize)

    if DicoModel is not None:
        ss+=" --DicoModel %s"%DicoModel
        
    if NodesFile is not None:
        ss+=" --NodesFile %s"%NodesFile

    if OutSolsName is not None:
        ss+=" --OutSolsName %s"%OutSolsName
        
    FilsSolsName="%s/%s/killMS.%s.sols.npz"%(SOLSDIR,MSName,OutSolsName)
    if os.path.isfile(FilsSolsName):
        print>>log,ModColor.Str("%s exists, skippinf kMS step:"%FilsSolsName)
        print>>log,ModColor.Str("    %s"%ss)
        return
    
    os_exec(ss)

def RunMakeMask(BaseImageName,Th=10,Box=(100,2)):
    ss="MakeMask.py --RestoredIm %s.app.restored.fits --Box %i,%i --Th %f"%(BaseImageName,Box[0],Box[1],Th)
    FileOutName="%s.app.restored.fits.mask.fits"%BaseImageName
    if os.path.isfile(FileOutName):
        print>>log,ModColor.Str("%s exists, skipping MakeMask step:"%FileOutName)
        print>>log,ModColor.Str("    %s"%ss)
        return FileOutName
    os_exec(ss)
    return FileOutName
    
def run(MSName):

    BaseImageName=os.path.abspath(MSName).split("_")[-3].split(".")[1]
    # ################################
    # Initial imaging
    RunDDF(MSName,BaseImageName,NMajorIter=2)

    # ################################
    # Make Mask
    MaskName=RunMakeMask(BaseImageName)

    # ################################
    # Deconvolve deeper
    DicoModel="%s.DicoModel"%BaseImageName
    BaseImageName="%s_m"%BaseImageName
    RunDDF(MSName,
           BaseImageName,
           MaskName=MaskName,
           NMajorIter=1,
           FromLastResid=True,
           InitDicoModel=DicoModel)
    
    # ################################
    # Cluster skymodel
    
    NodesFile="%s.app.restored.pybdsm.srl.fits.ClusterCat.npy"%BaseImageName
    if not os.path.isfile(NodesFile):
        ss="MakeCatalog.py --RestoredIm %s.app.restored.fits"%BaseImageName
        os_exec(ss)
        ss="ClusterCat.py --SourceCat %s.app.restored.pybdsm.srl.fits --DoPlot=1 --NGen 100 --NCPU 40 --FluxMin 0.001 --NCluster 6 --CentralRadius 0.7"%BaseImageName
        os_exec(ss)

    # ################################
    # DD calibration
    DicoModel="%s.DicoModel"%BaseImageName
    SOLSDIR="SOLS_%s"%MSName
    SolsFile="DDS0"
    RunKMS(MSName,BaseImageName,SolsFile,SOLSDIR=SOLSDIR,NodesFile=NodesFile,DicoModel=DicoModel)
    
    # ################################
    # DD imaging
    BaseImageName+=".AP"
    RunDDF(MSName,
           BaseImageName,
           MaskName=MaskName,
           SolsFile=SolsFile,SOLSDIR=SOLSDIR,
           InitDicoModel=DicoModel,
           NMajorIter=0,
           WeightColName="IMAGING_WEIGHT",
           Robust=-1.5)
    
    # ################################
    # Make Mask
    MaskName=RunMakeMask(BaseImageName,Th=5,Box=(50,2))

    # ################################
    # DD imaging deeper
    BaseImageName="%s_m"%BaseImageName
    RunDDF(MSName,
           BaseImageName,
           MaskName=MaskName,
           SolsFile=SolsFile,SOLSDIR=SOLSDIR,
           InitDicoModel=DicoModel,
           NMajorIter=1,
           PeakFactor=0.,
           FromLastResid=True,
           MaskAuto=False,
           WeightColName="IMAGING_WEIGHT",
           Robust=-1.5)
    

def run_all():
    ll=[l.strip() for l in file("mslist.txt","r").readlines()]
    for MSName in ll:
        run(MSName)

if __name__=="__main__":
    run_all()
