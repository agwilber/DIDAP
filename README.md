# DIrection Dependent Askap Pipeline

Use phaseshift.py to calculate and apply beam offsets to each beam.ms 
phaseshift.py requires askap_packages (https://bitbucket.csiro.au/projects/CASSSOFT/repos/askap-packages/browse)

Create mslist.txt with a list of all beam.ms files to process

Use RunDIDAP.py to carry out DD cal and imaging on mslist.txt
RunDIDAP.py requires kMS and DDF ()

Use askapbeam.py on beam_m.AP_m.app.restored.fits to create a beam model
askapbeam.py requires astrobits (pip install git+https://github.com/agwilber/astrobits.git)

Use applybeam.py on beam_m.AP_m.app.restored.fits to apply beam model and fix for stoke's I definition

Alternatively, use mosaic.sh to build a mosaic of all 36 beams
requires ASKAPsoft mosaic as template and requires miriad installation (https://www.atnf.csiro.au/computing/software/miriad/INSTALL.html) and path to $MIRBIN set (https://www.atnf.csiro.au/computing/software/miriad/INSTALL.html#post-install)
  
