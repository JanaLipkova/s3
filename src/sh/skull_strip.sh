#!/bin/bash

# ANTS Registration
#-----------------------
m="$2"
out="$3"
f_in="$1"
m_in=${m}/atlas_t1.nii
name="$4"
out_this=${out}/${name}_atlas_reg.nii 
imgs=" $f_in, $m_in"
its=10000x1111x5
dim=3
antsRegistration -d $dim -r [ $imgs ,1] \
                         -m mattes[  $imgs , 1 , 32, regular, 0.05 ] \
                         -t translation[ 0.1 ] \
                         -c [1000,1.e-8,20]  \
                         -s 4vox  \
                         -f 6 -l 1 \
                         -m mattes[  $imgs , 1 , 32, regular, 0.1 ] \
                         -t rigid[ 0.1 ] \
                         -c [1000x1000,1.e-8,20]  \
                         -s 4x2vox  \
                         -f 4x2 -l 1 \
                         -m mattes[  $imgs , 1 , 32, regular, 0.1 ] \
                         -t affine[ 0.1 ] \
                         -c [$its,1.e-8,20]  \
                         -s 4x2x1vox  \
                         -f 3x2x1 -l 1 \
                         -o ${out_this}


antsApplyTransforms -d $dim -i $m_in -r $f_in -t ${out_this}0GenericAffine.mat -o ${out_this} --float 1 


# Apply transformation to the brain mask:
m_tmp=${m}/atlas_mask.nii
out_tmp=${out}/${name}_mask.nii
antsApplyTransforms -d $dim -i $m_tmp -r $f_in -t ${out_this}0GenericAffine.mat -o ${out_tmp}.gz --float 1
echo "Basic brain mask is saved to: ${out_tmp}.gz"

# Apply transformation to the brain tissue:
labels=(wm gm csf)
for label in ${labels[*]}
     do
     m_tmp=${m}/atlas_${label}.nii
     out_tmp=${out}/${name}_${label}.nii
     antsApplyTransforms -d $dim -i $m_tmp -r $f_in -t ${out_this}0GenericAffine.mat -o ${out_tmp}.gz --float 1
done


