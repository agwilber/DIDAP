# DIrection Dependent Askap Pipeline (DIDAP)

Download visibilites from https://data.csiro.au/collections/domain/casdaObservation/search/ 

Preprocessing:

Use phaseshift.py to calculate and apply beam offsets to each beam.ms 

-- phaseshift.py requires askap_packages (https://bitbucket.csiro.au/projects/CASSSOFT/repos/askap-packages/browse)

Create mslist.txt with a list of all beam.ms files to process (example for SB8132 included)

Processing:

Use RunDIDAP.py to carry out DD cal and imaging on mslist.txt 
	
RunDIDAP.py requires kMS (https://github.com/cyriltasse/killMS) and DDF (https://github.com/cyriltasse/DDFacet)

Postprocessing: 

Use askapbeam.py on beam_m.AP_m.app.restored.fits to create a beam model which additonally corrects for Stoke's I defintion

askapbeam.py requires astrobits (pip install git+https://github.com/agwilber/astrobits.git)

Use applybeam.py on beam_m.AP_m.app.restored.fits to apply beam model 

Alternatively, use mosaic.sh to build a mosaic of all 36 DD beam images

mosaic.sh requires ASKAPsoft mosaic as template and requires miriad installation (https://www.atnf.csiro.au/computing/software/miriad/INSTALL.html) and path to $MIRBIN set (https://www.atnf.csiro.au/computing/software/miriad/INSTALL.html#post-install)
  
