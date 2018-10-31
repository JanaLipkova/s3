#!/bin/sh

for file in APT/*
do
echo "Processing folder:" ${file}
python s3.py -i ${file}/MPR_reg.nii.gz -t -a
done
