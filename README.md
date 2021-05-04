# DIrection Dependent Askap Pipeline

Use phaseshift.py to calculate and apply beam offsets to each beam.ms 

Create mslist.txt with a list of all beam.ms to process

Use RunDIDAP.py to process mslist.txt

Use askapbeam.py on beam_m.AP_m.app.restored.fits to create a beam model

Use applybeam.py on beam_m.AP_m.app.restored.fits to apply beam model 
