#!/usr/bin/env python

import os
import sys
import numpy as np
from casacore.tables import *
from askap.footprint import Skypos

if len(sys.argv) != 2:
    sys.exit("Usage %s <ms_file>" %(sys.argv[0]))

ms = sys.argv[1]

# Check that the observation wasn't in pol_fixed mode
ta = table("%s/ANTENNA" %(ms), readonly=True, ack=False)
ant_mount = ta.getcol("MOUNT", 0, 1)
if ant_mount[0] != 'equatorial':
    sys.exit("%s doesn't support pol_fixed mode" %(sys.argv[0]))
ta.close()

# Work out which beam is in this MS
t = table(ms, readonly=True, ack=False)
vis_feed = t.getcol('FEED1', 0, 1)
beam = vis_feed[0]

# Dump the FIELD table into a field file if it doesn't already exist.
# This ensures that there is a backup of the table in case it needs to be restored and
# also to ensure that if fix_dir.py is run again that it doesn't apply the wrong
# beam position (since the FIELD table is over-written the first time this is run).
field_file = ms.replace("ms", "field")
if os.path.exists(field_file) == False:
    tp = table("%s/FIELD" %(ms), readonly=True, ack=False)
    p_phase = tp.getcol('PHASE_DIR')
    p_phase.dump(ms.replace("ms", "field"))
    tp.close()
    print("Dumped field table for beam %d" %(beam))

# Load the FIELD table from the field file.
ms_phase = np.load(field_file, allow_pickle=True)
# Work out how many fields are in the MS.
n_fields = ms_phase.shape[0]
print("Found %d fields in FIELD table" %(n_fields))

# Open up the MS FIELD table so it can be updated.
tp = table("%s/FIELD" %(ms), readonly=False, ack=False)
# Open up the MS FEED table so we can work out what the offset is for the beam.
tf = table("%s/FEED" %(ms), readonly=True, ack=False)
# The offsets are assumed to be the same for all antennas so get a list of all
# the offsets for one antenna and for the current beam. This should return offsets
# required for each field.
t1 = taql("select from $tf where ANTENNA_ID==0 and FEED_ID==$beam")
n_offsets = t1.getcol("BEAM_OFFSET").shape[0]
offset_times = t1.getcol("TIME")
offset_intervals = t1.getcol("INTERVAL")
print("Found %d offsets in FEED table for beam %d" %(n_offsets, beam))
for offset_index in range(n_offsets):
    offset = t1.getcol("BEAM_OFFSET")[offset_index]
    print("Offset %d : t=%f-%f : (%fd,%fd)" %(offset_index, offset_times[offset_index]-offset_intervals[offset_index]/2.0,offset_times[offset_index]+offset_intervals[offset_index]/2.0, -offset[0][0]*180.0/np.pi, offset[0][1]*180.0/np.pi))

# Update the beam position for each field
for field in range(n_fields):
    t = table(ms, readonly=True, ack=False)
    tfdata = taql("select from $t where FIELD_ID==$field and FEED1==$beam and ANTENNA1=0 and ANTENNA2=1 and sumsqr(UVW[:2])>1.0")
    time_data = tfdata.getcol("TIME")
    offset_index = -1
    for offset in range(n_offsets):
        if (time_data[0] > offset_times[offset]-offset_intervals[offset]/2.0) and (time_data[0] < offset_times[offset]+offset_intervals[offset]/2.0):
            offset_index = offset
            break

#    print("Field %d : t=%f : offset=%d" %(field, time_data[0], offset_index))
    # Obtain the offset for the current field.
    offset = t1.getcol("BEAM_OFFSET")[offset_index]

    # Get the pointing direction for the field
    p_phase = ms_phase[field]

    # Shift the pointing centre by the beam offset
    phase = Skypos(p_phase[0][0], p_phase[0][1], 9, 9)
    new_pos = phase.shift(-offset[0][0], offset[0][1])
    new_pos.rn = 15
    new_pos.dn = 15
    new_pos_str = "%s" %(new_pos)
    print("Setting position of beam %d, field %d to %s (t=%f-%f, offset=%d)" %(beam, field, new_pos_str, time_data[0], time_data[-1], offset_index))
    # Update the FIELD table with the beam position
    new_ra = new_pos.ra
    if new_ra > np.pi:
        new_ra -= 2.0 * np.pi
    ms_phase[field][0][0] = new_ra
    ms_phase[field][0][1] = new_pos.dec

# Write the updated beam positions in to the MS.
tp.putcol("DELAY_DIR", ms_phase)
tp.putcol("PHASE_DIR", ms_phase)
tp.putcol("REFERENCE_DIR", ms_phase)
tp.close()
t.close()
