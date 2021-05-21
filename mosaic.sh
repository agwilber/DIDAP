#! /bin/bash

set -e
set -x

# Inputs: original images; final template file
SHORT='t:j:o:'
LONG='template:,jobs:,output:'
OPTS=$(getopt --options $SHORT --longoptions $LONG --name "$0" -- "$@")
eval set -- "$OPTS"

jobs=1
while true; do
  case "$1" in
    -t | --template )
      template="$2"
      shift 2
      ;;
    -o | --output )
      output="$2"
      shift 2
      ;;
    -j | --jobs )
      jobs="$2"
      shift 2
      ;;
    -- )
      shift
      break
      ;;
    * )
      break
      ;;
  esac
done

if [[ -z $template ]]; then
  echo "-t | --template is required"
  exit 1
fi

if [[ -z $output ]]; then
  echo "-o | --output is required"
  exit 1
fi

if [[ $# == 0 ]]; then
  echo "At least one image must be provided"
  exit 1
fi
images=( "$@" )

# Generate beam power maps for each image
beamnames=()
for image in ${images[@]}; do
  prefix=$(dirname $image)/$(basename $image .fits)-beam.fits
  beamnames+=( $prefix )
done

parallel -j 1 -v -- ./askapbeam.py --template {1} --output {2} ::: ${images[@]} :::+ ${beamnames[@]}

# Create pb-corrected images
parallel -j 1 -v -- ./applybeam.py --image {1} --beam {2} ::: ${images[@]} :::+ ${beamnames[@]}

imagepbs=()
for image in ${images[@]}; do
  imagepb=$(dirname $image)/$(basename $image .fits)-pb.fits
  imagepbs+=( $imagepb )
done

# Regrid both pb-corrected image and beam-power maps
parallel -j 1 -v -- ./regrid.sh {1} $template ::: ${imagepbs[@]}
parallel -j 1 -v -- ./regrid.sh {1} $template ::: ${beamnames[@]}

# Rename regridded beams to format expected by myadd
for beamname in ${beamnames[@]}; do
  current=$(dirname $beamname)/$(basename $beamname .fits)-regridded.fits
  new=$(dirname $beamname)/$(basename $beamname -beam.fits)-pb-regridded-beam.fits
  mv $current $new
done

# Use myadd to grid
finals=()
for image in ${images[@]}; do
  final=$(dirname $image)/$(basename $image .fits)-pb-regridded.fits
  finals+=( $final )
done
./myadd.py --weight-suffix=-beam --output $output --beam-threshold 0.25 -- ${finals[@]}

