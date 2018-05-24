"""
Performs skull stripping and tissue segmentations based on atlas registration
Employs ANTs for registration and the SRI24 atlas as template

Usage:
    Initialize an instance.
    skull_stripper = SkullStripper()

    Run skull stripping method:
    skull.stripper.strip_skull(input_path, output_path, want_tissues)

@author: jana lipkova
"""

import subprocess
#import shlex
import os
import src.helpers as utils
import numpy as np
import nibabel as nib
from nilearn.masking import apply_mask
from nilearn.image import load_img, math_img, threshold_img
import time

#import src.registration as reg

class SkullStripper():

    #Intialize the skull stripper class
    #@param input_path : Path to the input modality to skull strip
    #@param output_path : Path the to output folder.
    #@param want_tissue: Boolean for outputting the tissue registrations 
    def __init__(self, input_path, output_path, want_tissues):

        self.input_path = input_path
        self.output_path = output_path
        self.want_tissues = want_tissues

        self.name = os.path.splitext(os.path.splitext(os.path.basename(input_path))[0])[0]
        self.atlas = utils.get_relative_path("Atlas")

    # Compute non-deformable (translation -> rigid -> affine) registrations of moving to fixed image,
    # output is the base name for the computed registration
    # return name of the transformaiton file
    def compute_rigid_registration(self, moving_image, fixed_image, output):
    	imgs = fixed_image + ", " + moving_image 

        ants_call = ( " antsRegistration -d 3 -r [" + imgs + ", 1]" +
		  " -t translation[0.1]" +
		  " -m mattes[" + imgs + ", 1, 32, regular, 0.05]" +
		  " -c [1000, 1e-8, 20] -s 4vox -f 6 -l 1 " +
		  " -t rigid[0.1]" +
		  " -m mattes[" + imgs + ", 1, 32, regular, 0.1]" +
		  " -c [1000x1000, 1e-8, 20] -s 4x2vox -f 4x2 -l 1" +
		  " -t affine[0.1]" +
		  " -m mattes[" + imgs + " , 1 , 32, regular, 0.1 ]" +
		  " -c [10000x1111x5, 1e-8, 20] -s 4x2x1vox -f 3x2x1 -l 1" +
		  " -o " + output )

        subprocess.call(ants_call, shell=True, stdout=subprocess.PIPE) 
        output = output + "0GenericAffine.mat"
        return output

    	
    # Compute deformable (non-linear SyN) registration and output the transformation file
    def compute_non_rigid_registration(self, moving_image, fixed_image, mask, output):
	imgs = fixed_image + ", " + moving_image
        
	ants_call = (" antsRegistration -d 3 " +
                     " -m mattes[" + imgs + ", 1, 32, Regular, 0.25] " +
                     " -t SyN[ 0.1, 3, 0 ] " +
                     " -c [ 100x50x25, 1e-8, 20] " +
                     " -s 3x2x0vox -f 8x4x2 " +
		     " -w [0.25, 0.75] " +
		     " -x " + mask +
                     " -o " + output )

 	subprocess.call(ants_call, shell=True, stdout=subprocess.PIPE)
        output = output + "0Warp.nii.gz"
	return output

    # Apply computed transformation to register the moving image to the fixed image, store result in the output file
    def apply_transformation(self, moving_image, fixed_image, transform, output):   
	antstf_call = (" antsApplyTransforms -d 3" + 
		       " -i " + moving_image + 
		       " -r " + fixed_image + 
                       " -t " + transform + 
                       " -o " + output + ".nii.gz" 
                       + " --float 1")

        subprocess.call(antstf_call, shell=True, stdout=subprocess.PIPE)

    def strip_skull(self):
        
	""" Perform skull stripping"""
        print("Skull stripping started. \n --------------------------- \n")
        print("Input Modality: %s \n" % self.input_path)
        print("Output Folder : %s \n" % self.output_path)
      
        #1) Rigid registration: Atlas to Patient, apply the tranformation to get basic mask + tissue approximations
	print("Computing the basic mask: \n ---------------" )
        moving = self.atlas + "/atlas_t1.nii"
	#moving = self.atlas + "/atlas_pd.nii"
        fixed  = self.input_path
        output = self.output_path + "/" + self.name + "_atlas_reg"

        transform = self.compute_rigid_registration(moving, fixed, output)       
        self.apply_transformation(moving, fixed, transform, output) 

        #1.1) Apply the transformation to map atlas mask and tissue to patient space
  	for tissue in ["mask", "wm", "gm", "csf"]:
	    moving = self.atlas + "/atlas_" + tissue + ".nii"
	    output = self.output_path + "/" + self.name + "_" + tissue + ".nii.gz"
	    self.apply_transformation(moving, fixed, transform,output)

	# make the mask binary 
        mask = nib.load(self.output_path + "/" + self.name + "_mask.nii.gz")
        mask = math_img("img > 0.9", img=mask)
	nib.save(mask,self.output_path + "/" + self.name + "_mask.nii.gz")

 
	# 2) Refine by using deformable registration, with the above mask for masking
	print("Deformable registration \n")
        moving = self.output_path + "/" + self.name + "_atlas_reg.nii.gz"
	fixed  = self.input_path
	mask   = self.output_path + "/" + self.name + "_mask.nii.gz"
        output = self.output_path + "/atlas_def_reg.nii.gz"

        transform = self.compute_non_rigid_registration(moving, fixed, mask, output)
        self.apply_transformation(moving, fixed, transform, output)
	
        print("Tissue registration \n")
	for tissue in ["mask", "wm", "gm", "csf"]:
            moving = self.output_path + "/" + self.name + "_" + tissue + ".nii.gz"
            output = self.output_path + "/" + self.name + "_" + tissue + "_ref.nii.gz"
            self.apply_transformation(moving, fixed, transform,output)
  	
	# 3) Apply the basic and new mask
	mask_basic  = nib.load(os.path.join(self.output_path, self.name + "_mask.nii.gz"))
 	mask_refine = nib.load(os.path.join(self.output_path, self.name + "_mask_ref.nii.gz"))
	patient     = nib.load(self.input_path)
        
	masked_patient_basic   = np.multiply(patient.get_data(), mask_basic.get_data())
	masked_patient_refine  = np.multiply(patient.get_data(), mask_refine.get_data())

	masked_patient_basic   = nib.Nifti1Image( masked_patient_basic, patient.affine, patient.header)
	masked_patient_refine  = nib.Nifti1Image( masked_patient_refine, patient.affine, patient.header)
	nib.save(masked_patient_basic, os.path.join(self.output_path, self.name + "_masked_basic.nii.gz"))
        nib.save(masked_patient_refine, os.path.join(self.output_path, self.name + "_masked.nii.gz"))

        # 4) Clean-up
	os.rename(self.output_path + "/" + self.name + "_wm_ref.nii.gz", self.output_path + "/" + self.name + "_wm.nii.gz")
        os.rename(self.output_path + "/" + self.name + "_gm_ref.nii.gz", self.output_path + "/" + self.name + "_gm.nii.gz")
        os.rename(self.output_path + "/" + self.name + "_csf_ref.nii.gz",self.output_path + "/" + self.name + "_csf.nii.gz")
 	os.rename(self.output_path + "/" + self.name + "_mask.nii.gz",   self.output_path + "/" + self.name + "_mask_basic.nii.gz")    
        os.rename(self.output_path + "/" + self.name + "_mask_ref.nii.gz",   self.output_path + "/" + self.name + "_mask.nii.gz") 

	os.remove(os.path.join(self.output_path, self.name + "_atlas_reg.nii.gz"))
        os.remove(os.path.join(self.output_path, "atlas_def_reg.nii.gz"))
	os.remove(os.path.join(self.output_path, "atlas_def_reg.nii.gz0Warp.nii.gz"))
        os.remove(os.path.join(self.output_path, "atlas_def_reg.nii.gz0InverseWarp.nii.gz"))
	os.remove(os.path.join(self.output_path, self.name + "_atlas_reg0GenericAffine.mat"))
       
        print('---------------------------\nSkull Stripping Finished.') 
